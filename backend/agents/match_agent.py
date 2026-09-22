"""Agent 3：匹配评估 —— LangChain + 字段校验 + RAG

输入：jd_analysis, resume_analysis, resume, knowledge_context
"""
import json as _json

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda

_AGENT_NAME = "匹配评估Agent"

_REQUIRED_FIELDS = {
    "match_level": "dict",
    "analysis_basis": "list",
    "strengths": "list[str]",
    "weaknesses": "list[str]",
}
_MATCH_LEVEL_SUB_FIELDS = ["overall", "ability", "experience", "risk"]

_TEMPLATE = """你是简历与岗位匹配度评估专家。请基于以下信息评估候选人与岗位的匹配度。

【岗位JD分析结果】
{jd_analysis}

【简历分析结果】
{resume_analysis}

【简历原文】（用于引用真实原文，不得编造）
{resume}

【岗位知识库参考】
{knowledge}

【事实边界约束】
- analysis_basis / strengths / weaknesses 必须基于简历原文证据，逐项可追溯。
- 禁止升级措辞：不得把"参与"写成"主导/独立负责"，不得把"掌握/熟悉/了解"写成"精通"，除非原文明确支持。
- 禁止新增简历中不存在的数字、指标（性能提升、效率倍数、准确率等）或项目级别（生产级/工业级/高可用等）。
- 属于推断而非原文证据的内容，必须在句末标注"（推断）"。
- 简历未体现的 JD 要求技术，归入 weaknesses/gap 并表述为"当前简历未体现该技术实践"，不得写成已有经验。

【输出要求】
请严格返回如下JSON（用 ```json 代码块包裹，不要添加解释文字）：
{{
  "match_level": {{"overall": "较高/中等/较低", "ability": "较强/中等/较弱", "experience": "较强/中等/较弱", "risk": "需要优化/风险较低/风险较高"}},
  "analysis_basis": [{{"dimension": "维度名", "items": [{{"type": "match或gap", "content": "描述", "quote": "简历原文引用(仅match类型)", "match_degree": "高/中/低"}}]}}],
  "strengths": ["优势：具体描述"],
  "weaknesses": ["不足：具体描述"]
}}"""

_prompt = ChatPromptTemplate.from_template(_TEMPLATE)


def _dump_dict(obj):
    return _json.dumps(obj or {}, ensure_ascii=False, indent=2)


def _llm_call(prompt_val):
    from services import llm_service
    prompt = prompt_val.to_string() if hasattr(prompt_val, "to_string") else str(prompt_val)
    return llm_service.chat(prompt)


def _json_parse(text):
    from services import llm_service
    parsed = llm_service.parse_json_from_text(text)
    if parsed is None:
        raise RuntimeError(f"{_AGENT_NAME} 返回内容无法解析为JSON（长度 {len(text) if text else 0}）")
    return parsed


def _validate(result):
    if not isinstance(result, dict):
        raise RuntimeError(f"{_AGENT_NAME} 校验失败: 返回不是 JSON 对象")
    errors = []
    for field, expected_type in _REQUIRED_FIELDS.items():
        if field not in result:
            errors.append(f"必需字段 '{field}' 缺失")
            continue
        val = result[field]
        if expected_type == "dict":
            if not isinstance(val, dict):
                errors.append(f"字段 '{field}' 应为对象，实际 type={type(val).__name__}")
            elif field == "match_level":
                for sub in _MATCH_LEVEL_SUB_FIELDS:
                    if sub not in val or not isinstance(val[sub], str):
                        errors.append(f"match_level.{sub} 应为字符串")
        elif expected_type == "list":
            if not isinstance(val, list):
                errors.append(f"字段 '{field}' 应为数组，实际 type={type(val).__name__}")
        elif expected_type == "list[str]":
            if not isinstance(val, list):
                errors.append(f"字段 '{field}' 应为数组，实际 type={type(val).__name__}")
            else:
                non_str = [i for i, v in enumerate(val) if not isinstance(v, str)]
                if non_str:
                    errors.append(f"字段 '{field}' 数组内 {len(non_str)} 项不是字符串")
    if errors:
        raise RuntimeError(f"{_AGENT_NAME} 校验失败: " + "; ".join(errors))
    return result


chain = _prompt | RunnableLambda(_llm_call) | RunnableLambda(_json_parse) | RunnableLambda(_validate)


def run(jd_analysis, resume_analysis, resume, knowledge_context):
    return chain.invoke({
        "jd_analysis": _dump_dict(jd_analysis),
        "resume_analysis": _dump_dict(resume_analysis),
        "resume": resume,
        "knowledge": knowledge_context or "（无）",
    })


def build_prompt(jd_analysis, resume_analysis, resume, knowledge_context):
    return _prompt.invoke({
        "jd_analysis": _dump_dict(jd_analysis),
        "resume_analysis": _dump_dict(resume_analysis),
        "resume": resume,
        "knowledge": knowledge_context or "（无）",
    }).to_string()

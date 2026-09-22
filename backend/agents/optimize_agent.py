"""Agent 4：优化建议 —— LangChain + 字段校验 + RAG

输入：jd_analysis, match_result, resume, knowledge_context（四变量模板）
"""
import json as _json

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda

_AGENT_NAME = "优化建议Agent"

_REQUIRED_TOP = {
    "rewrite_suggestions": "list[dict]",
    "optimization_advice": "dict",
}
_SUGGESTION_REQUIRED = ["original", "revised", "basis", "evidence_grade"]
_OPTIMIZATION_ADVICE_REQUIRED = ["highlight", "supplement", "expression"]

_TEMPLATE = """你是简历优化建议专家。请基于匹配评估结果，生成简历改写与优化建议。

【最高原则】
在不改变、不新增、不虚构用户事实的前提下，最大化真实岗位匹配度。
宁可匹配度显得低，也不允许任何虚构。

【证据等级定义】（每条 rewrite_suggestion 必须标注 evidence_grade）
- A【已有事实】：简历中明确存在，可直接使用。
- B【基于事实的合理概括】：仅改变表达方式，不增加任何新事实。
- C【能力推断】：简历无直接证据、由你推测可能具备。禁止进入简历修改。
- D【当前缺口】：JD 要求但简历无证据。禁止进入简历修改。
- E【建议实践】：未来可学习/实践的方向。禁止进入简历修改。

【rewrite_suggestions 准入规则】
- 只允许 evidence_grade 为 "A" 或 "B" 的条目进入 rewrite_suggestions。
- C/D/E 类内容一律不得进入 rewrite_suggestions，只能写入 optimization_advice.supplement，
  并写成"当前简历未体现XX实践"或"建议后续学习/实践XX"的表述。

【禁止项】（revised 相对 original 而言）
1. 禁止新增技术栈：简历没写过的技术不得出现在 revised 中；JD 要求但简历未体现的技术，不得建议"写进简历"，只能写入 supplement。
2. 禁止新增职责、用户数量、项目级别。
3. 禁止新增任何数字与指标：性能提升比例、效率倍数、毫秒级、准确率、QPS 等，除非原文中真实存在。
4. 禁止把"参与"升级为"主导/独立负责"。
5. 禁止把"掌握/熟悉/了解"升级为"精通"，除非原文明确支持。
6. 禁止把个人项目包装成"生产级/工业级/高可用/大规模"。
7. 禁止把"理论可迁移"写成"具备实践经验"。
8. 禁止混淆技术概念：JSON Schema 不是 Tool Calling；RAG 本身不等于准确率提升。

【岗位知识库参考】（用于参考岗位能力标准、常见误区与表达规则）
{knowledge}

【输出要求】
1. original 必须摘录自简历原文，不得编造。
2. revised 只能在 original 的事实范围内重写：可调整语序与详略、突出原文已有事实、只使用原文已出现的技术词。
3. basis 必须包含三部分：原文依据（引用原文内容）+ 对应 JD 要求 + 改写逻辑说明。
4. JD 要求但简历未体现的能力：不生成改写条目，写入 supplement 并注明"当前简历未体现该技术实践"。

【岗位JD分析结果】
{jd_analysis}

【匹配评估结果】
{match_result}

【简历内容】
{resume}

请严格返回如下JSON（用 ```json 代码块包裹，不要添加解释文字）：
{{
  "rewrite_suggestions": [{{"original": "必须摘录自简历原文", "revised": "仅在原文事实范围内的优化表达", "basis": "依据：原文《XXX》；JD要求XXX；改写逻辑：XXX", "evidence_grade": "A或B"}}],
  "optimization_advice": {{"highlight": ["建议突出：具体说明（仅基于原文事实）"], "supplement": ["当前简历未体现XX技术实践" 或 "建议后续学习/实践XX"], "expression": ["建议优化表达：原表达→建议表达"]}}
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
    # 顶层字段
    for field, expected_type in _REQUIRED_TOP.items():
        if field not in result:
            errors.append(f"必需字段 '{field}' 缺失")
            continue
        val = result[field]
        if expected_type == "dict":
            if not isinstance(val, dict):
                errors.append(f"字段 '{field}' 应为对象，实际 type={type(val).__name__}")
            elif field == "optimization_advice":
                for sub in _OPTIMIZATION_ADVICE_REQUIRED:
                    if sub not in val or not isinstance(val[sub], list):
                        errors.append(f"optimization_advice.{sub} 应为数组")
                    elif val[sub] and not all(isinstance(x, str) for x in val[sub]):
                        errors.append(f"optimization_advice.{sub} 数组内存在非字符串项")
        elif expected_type == "list[dict]":
            if not isinstance(val, list):
                errors.append(f"字段 '{field}' 应为数组，实际 type={type(val).__name__}")
            else:
                for idx, sug in enumerate(val):
                    if not isinstance(sug, dict):
                        errors.append(f"rewrite_suggestions[{idx}] 应为对象")
                        continue
                    for req in _SUGGESTION_REQUIRED:
                        if req not in sug or not isinstance(sug[req], str):
                            errors.append(f"rewrite_suggestions[{idx}].{req} 应为字符串")
    if errors:
        raise RuntimeError(f"{_AGENT_NAME} 校验失败: " + "; ".join(errors))
    return result


chain = _prompt | RunnableLambda(_llm_call) | RunnableLambda(_json_parse) | RunnableLambda(_validate)


def run(jd_analysis, match_result, resume, knowledge_context):
    return chain.invoke({
        "jd_analysis": _dump_dict(jd_analysis),
        "match_result": _dump_dict(match_result),
        "resume": resume,
        "knowledge": knowledge_context or "（无）",
    })


def build_prompt(jd_analysis, match_result, resume, knowledge_context):
    return _prompt.invoke({
        "jd_analysis": _dump_dict(jd_analysis),
        "match_result": _dump_dict(match_result),
        "resume": resume,
        "knowledge": knowledge_context or "（无）",
    }).to_string()

"""Agent 2：简历分析 —— LangChain + 字段校验"""
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda

_AGENT_NAME = "简历分析Agent"

_REQUIRED_FIELDS = {
    "技术栈": "list[str]",
    "项目经历": "list[dict]",
    "优势": "list[str]",
    "不足": "list[str]",
}

_TEMPLATE = """你是简历分析专家。请分析以下简历，提取结构化信息。

【简历内容】
{resume}

【输出要求】
请严格返回如下JSON（用 ```json 代码块包裹，不要添加解释文字）：
{{
  "技术栈": ["技术1", "技术2"],
  "项目经历": [{{"项目名": "", "职责": "", "技术点": ""}}],
  "优势": ["优势1", "优势2"],
  "不足": ["不足1", "不足2"]
}}"""

_prompt = ChatPromptTemplate.from_template(_TEMPLATE)


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
        raise RuntimeError(f"{_AGENT_NAME} 校验失败: 返回不是 JSON 对象 (type={type(result).__name__})")
    errors = []
    for field, expected_type in _REQUIRED_FIELDS.items():
        if field not in result:
            errors.append(f"必需字段 '{field}' 缺失")
            continue
        val = result[field]
        if not isinstance(val, list):
            errors.append(f"字段 '{field}' 应为数组，实际 type={type(val).__name__}")
            continue
        if expected_type == "list[str]":
            non_str = [i for i, v in enumerate(val) if not isinstance(v, str)]
            if non_str:
                errors.append(f"字段 '{field}' 数组内 {len(non_str)} 项不是字符串")
        elif expected_type == "list[dict]":
            non_dict = [i for i, v in enumerate(val) if not isinstance(v, dict)]
            if non_dict:
                errors.append(f"字段 '{field}' 数组内 {len(non_dict)} 项不是对象")
    if errors:
        raise RuntimeError(f"{_AGENT_NAME} 校验失败: " + "; ".join(errors))
    return result


chain = _prompt | RunnableLambda(_llm_call) | RunnableLambda(_json_parse) | RunnableLambda(_validate)


def run(resume_text):
    return chain.invoke({"resume": resume_text})


def build_prompt(resume_text):
    return _prompt.invoke({"resume": resume_text}).to_string()

"""Agent 1：JD 分析 —— LangChain + 字段校验

链路：ChatPromptTemplate → _llm_call → _json_parse → _validate
"""
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda

_AGENT_NAME = "JD分析Agent"

_REQUIRED_FIELDS = {
    "岗位职责": "str",
    "核心技能": "list[str]",
    "技术要求": "list[str]",
    "岗位关键词": "list[str]",
}

_TEMPLATE = """你是岗位JD分析专家。请分析以下岗位JD，提取结构化信息。

【岗位JD】
{jd}

【输出要求】
请严格返回如下JSON（用 ```json 代码块包裹，不要添加解释文字）：
{{
  "岗位职责": "用一段话概括该岗位的核心职责",
  "核心技能": ["核心技能1", "核心技能2"],
  "技术要求": ["技术1", "技术2"],
  "岗位关键词": ["关键词1", "关键词2"]
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
    """服务端字段校验：必需字段存在 + 类型正确。"""
    if not isinstance(result, dict):
        raise RuntimeError(f"{_AGENT_NAME} 校验失败: 返回不是 JSON 对象 (type={type(result).__name__})")
    errors = []
    for field, expected_type in _REQUIRED_FIELDS.items():
        if field not in result:
            errors.append(f"必需字段 '{field}' 缺失")
            continue
        val = result[field]
        if expected_type == "str":
            if not isinstance(val, str):
                errors.append(f"字段 '{field}' 应为字符串，实际 type={type(val).__name__}")
        elif expected_type == "list[str]":
            if not isinstance(val, list):
                errors.append(f"字段 '{field}' 应为数组，实际 type={type(val).__name__}")
            else:
                non_str = [i for i, v in enumerate(val) if not isinstance(v, str)]
                if non_str:
                    errors.append(f"字段 '{field}' 数组内 {len(non_str)} 项不是字符串 (index={non_str[:3]})")
    if errors:
        raise RuntimeError(f"{_AGENT_NAME} 校验失败: " + "; ".join(errors))
    return result


chain = _prompt | RunnableLambda(_llm_call) | RunnableLambda(_json_parse) | RunnableLambda(_validate)


def run(jd_text):
    return chain.invoke({"jd": jd_text})


def build_prompt(jd_text):
    return _prompt.invoke({"jd": jd_text}).to_string()

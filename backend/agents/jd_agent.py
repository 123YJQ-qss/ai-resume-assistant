"""Agent 1：JD 分析 —— 结构化要求分类

链路：ChatPromptTemplate → _llm_call → _json_parse → _validate

v2 改动（2026-10-12）：
- 新增 requirements[] 数组，每条带 category（hard/core/preferred）
- 保留核心技能/技术要求/岗位关键词 三个旧字段（向后兼容）
- category 分类规则由 prompt 明确，不做写死
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

_TEMPLATE = """你是岗位JD分析专家。请分析以下岗位JD，提取结构化信息，并按要求重要性分类。

【岗位JD】
{jd}

【要求分类规则 —— 必须严格遵守】
将 JD 中的每一项明确要求归入以下三类之一：

🔴 hard（硬性门槛）—— 只有当 JD 中有明确、不可替代、无法用相近能力替代的准入条件时才归入此类。
  判断依据示例：
  - 明确写明"硕士及以上""本科及以上学历"（学历硬门槛）
  - 明确写明"3年以上 AI 相关工作经验"（工作年限硬门槛）
  - 特定法律/资格证书要求（如教师资格证、执业医师证）
  - 特定签证/工作许可要求
  注意：岗位名称是"Python 后端工程师"不自动等于 Python 是 hard。
  Python、Java、AI Agent 等技术经验通常归入 core 而非 hard，除非 JD 明确写"必须精通 XXX 且不可替代"。

🟠 core（核心岗位能力）—— 决定岗位适配度的主要能力要求。
  判断依据：
  - JD 岗位职责中明确承担的核心工作所需的技术和能力
  - 任职要求中列出的、不满足会直接影响岗位匹配的条件
  - 岗位名称暗示的核心技术栈（如"AI Agent 开发"→ Agent 工作流、RAG 是 core）
  - 可以是技术、经验、方法、流程等，不限于工具名

🟢 preferred（加分与扩展能力）—— JD 中以"优先/加分/有XX经验更好/了解XX"表述的条件。
  判断依据：
  - JD 明确写"XX 经验者优先"
  - 以"加分项""附加条件"形式出现
  - 特定工具/平台/框架经验（如 Coze、Dify、n8n、LlamaIndex）但不是核心工作内容
  - 行业特定经验（如"金融行业经验优先"）

【分类注意事项】
- 不允许因技术常见就自动升为 hard（Python/Java/Linux 都是技术，通常归入 core）
- 遇到 JD 表述含糊（如"熟悉某某技术"没说是必须还是优先），默认归入 core
- 遇到"必须"和"优先"同时出现的，以"优先"为准归入 preferred
- 同一能力下的多个相近工具（如 Coze、Dify、n8n）可以合并为一条 requirement，能力分组标注为"低代码 Agent 平台"
- 每条 requirement 要保留 JD 原文依据（jd_quote），不要凭空生成 JD 没有的要求
- requirement_id 用格式 req-001、req-002 ... 编号，后续 Agent 会引用这个 ID，必须保持唯一且不修改

【输出要求】
请严格返回如下JSON（用 ```json 代码块包裹，不要添加解释文字）：
{{
  "岗位职责": "用一段话概括该岗位的核心职责",
  "核心技能": ["核心技能1", "核心技能2（与 requirements 中 core 类对应）"],
  "技术要求": ["技术1", "技术2（与 requirements 中 core+preferred 类对应）"],
  "岗位关键词": ["关键词1", "关键词2（综合提取）"],
  "requirements": [
    {{
      "requirement_id": "req-001",
      "text": "具体要求文本（简洁描述）",
      "category": "hard/core/preferred",
      "category_reason": "为什么归为这一类的理由",
      "jd_quote": "JD 原文引用片段（不超过 50 字）",
      "capability_group": "能力分组标签（如：后端开发、Agent设计、学历门槛、RAG、工具经验等）",
      "confidence": "high/medium/low （JD 表述清晰度）"
    }}
  ]
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
    """服务端字段校验：必需字段存在 + 类型正确。requirements 为可选但如果存在则校验格式。"""
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

    # requirements 是可选字段，但如果存在则校验
    reqs = result.get("requirements")
    if reqs is not None:
        if not isinstance(reqs, list):
            errors.append(f"字段 'requirements' 应为数组，实际 type={type(reqs).__name__}")
        else:
            for idx, r in enumerate(reqs):
                if not isinstance(r, dict):
                    errors.append(f"requirements[{idx}] 应为对象")
                    continue
                for sub in ("requirement_id", "text", "category"):
                    if sub not in r or not isinstance(r.get(sub), str):
                        errors.append(f"requirements[{idx}].{sub} 应为字符串")
                cat = r.get("category", "")
                if cat and cat not in ("hard", "core", "preferred"):
                    errors.append(f"requirements[{idx}].category 值 '{cat}' 非法，应为 hard/core/preferred")

    if errors:
        raise RuntimeError(f"{_AGENT_NAME} 校验失败: " + "; ".join(errors))
    return result


chain = _prompt | RunnableLambda(_llm_call) | RunnableLambda(_json_parse) | RunnableLambda(_validate)


def run(jd_text):
    return chain.invoke({"jd": jd_text})


def build_prompt(jd_text):
    return _prompt.invoke({"jd": jd_text}).to_string()

"""Agent 3：匹配评估 v2 —— 基于 JD 要求分类的定性匹配

v2 改动（2026-10-12）：
- 核心改变：逐条读取 jd_analysis.requirements，每条独立匹配后综合判断
- 新增 requirement_matches 数组：每条 requirement 的匹配状态 + 证据 + 迁移说明
- 综合匹配等级改用定性规则（不用数字阈值），区分 hard/core/preferred 的权重
- 技术可迁移性只支持 partial_match，必须保留能力边界
- 保留旧的 analysis_basis/strengths/weaknesses 结构向后兼容
"""
import datetime as _dt
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

_TODAY = _dt.date.today()
_TODAY_STR = _TODAY.strftime("%Y-%m-%d")

_TEMPLATE = """你是简历与岗位匹配度评估专家。本次评估将基于 JD 结构化要求，逐条匹配简历证据，然后综合判断。

【当前日期】{today}

【岗位JD分析结果】
{jd_analysis}

【简历分析结果】
{resume_analysis}

【简历原文】（用于引用真实原文，不得编造）
{resume}

【岗位知识库参考】
{knowledge}

═══════════════════════════════════════
第一步：逐条匹配 JD requirements
═══════════════════════════════════════

对 JD 中的**每一条 requirement**（不管 category 是什么），都独立判断匹配状态。

每条 requirement 的匹配状态从以下四种中选一种：

✅ **direct_match（明确匹配）**
简历中有直接的技术、项目、工作职责、证书、学历或工作年限证据，能直接证明满足这条要求。
判断依据：简历原文有对应事实，不需要推测。

🟡 **partial_match（部分匹配）**
简历具有相似技术背景、相关项目经验或可迁移能力，但不能证明完整满足要求。
关键规则：
- 技术可迁移性**只能产生 partial_match，不能产生 direct_match**。
- 必须明确写出：迁移来源、共通能力是什么、**不能做什么**（能力边界）。
- 示例：
  - JD 要求 Coze/Dify 平台经验 → 简历有 LangChain Multi-Agent Workflow：可迁移的是 Agent 工作流设计能力，但 Dify 平台实际使用经验 = 未证明 → partial_match
  - JD 要求 LlamaIndex → 简历有 FAISS + Embedding + RAG：可迁移的是 RAG 原理与工程能力，但 LlamaIndex 框架本身 = 未证明 → partial_match
  - JD 要求 Python 后端开发 → 简历只有 Java 后端：Python = 未证明，只能算基础可迁移 → partial_match

❓ **unverified（待确认）**
简历**没有足够证据**，无法判断是否具有该能力。这不是否定，只是证据缺失。
判断依据：简历中没有出现相关关键词，或出现了但缺乏足够项目/职责细节。
注意：**没有提到 ≠ 不具备**，归为 unverified 而非 not_met。

❌ **not_met（明确不满足）**
现有资料能够**明确证明**候选人不满足某项要求。
判断依据示例：
- JD 要求"硕士学历"，简历明确写"本科" → not_met
- JD 要求"3年以上经验"，简历显示应届生 → not_met
- 简历中明确说"没有 XX 经验" → not_met
注意：只有**有反向证据**时才能判 not_met，仅仅"简历没提"不算。

═══════════════════════════════════════
第二步：综合判断匹配等级（定性规则，不使用数字阈值）
═══════════════════════════════════════

综合判断的优先级顺序：

1. **先检查 hard 门槛**：如果有任何 hard requirement 被判为 not_met → 直接整体风险"风险较高"，overall 不高于"中等"。
2. **再看 core 覆盖情况和证据强度**：
   - 绝大多数 core 是 direct_match，或至少 partial_match 且有可迁移证据 → 说明核心方向匹配。
   - 但要区分：direct_match 的证据强度（有完整项目 vs 只提了关键词）。
3. **preferred 类的影响很小**：
   - preferred 全部 unverified 不应该拖累 overall 到"较低"。
   - 只有当 preferred 类中存在极有价值的能力（如特定行业经验、特定生产级平台经验）且其他条件打平时，才可能影响判断。
4. **区分能力适配 vs 表达质量**：
   - 如果能力上基本满足（多数 core 有 direct/partial 证据），但简历表述不清晰 → match_level 不应给太低，
     而是应在 analysis_basis 和 weaknesses 中明确指出"表达质量问题"。

**定性判断参考**（不是阈值，是判断思路）：
- 「较高」：没有 hard 被 not_met；core 中绝大多数有 direct_match 证据；preferred 可以基本 unverified。
  即使简历表达较弱，能力事实充分也应该较高——表达问题在 analysis_basis 中指出即可。
- 「中等」：方向相关但有重要 core 能力处于 unverified；或 core 中不少只有 partial_match 证据；或存在一个 not_met 的 hard。
- 「较低」：有 hard 被判 not_met 且是关键阻断；或 core 中大量 unverified/not_met，整体方向偏离岗位。

═══════════════════════════════════════
第三步：生成结构化输出
═══════════════════════════════════════

【weaknesses/不足 分类标注 —— 用于前端区分展示】
每条 weakness 必须以以下三种标记之一开头：
- [表达优化]：候选人可能具备相关能力，但简历表述不清晰/不突出，可通过改写直接改善
- [事实待确认]：JD 要求某项能力，简历没有足够证据，需要候选人确认是否确实做过
- [能力缺口]：现有资料不能证明具备该技能，可能需要学习或实践补足

weaknesses 中的条目应从 requirement_matches 中推导：
- unverified + capability_group 属于 core → 归入 [事实待确认]
- unverified + capability_group 属于 preferred → 一般不放入 weaknesses（加分项，无需担忧）
- not_met + hard → 归入 [能力缺口] 并标注"硬性门槛"
- not_met + core → 归入 [能力缺口]
- partial_match 且匹配证据不足、需要简历更清晰表达 → 归入 [表达优化]

【Top3 关键差距排序】
analysis_basis 中 gap 条目的生成顺序应综合考虑：
- requirement 的 category（hard > core > preferred）
- match_status（not_met 最严重，其次 unverified）
- 实际招聘影响：这个缺口在真实筛选中影响多大
- 同 capability_group 的缺口应归并（如"没有 Coze"和"没有 Dify"合并为"低代码 Agent 平台经验待确认"）
不允许仅仅因为多个 preferred 类 unverified 就制造一串差距。

【日期与事实推断规则】
1. 毕业状态：简历明确写"已毕业"或毕业时间早于当前日期且无"预计"标注 → 已毕业。简历写的毕业时间已过但有"预计"标注未删除 → 不擅自判断，标"需确认"。简历没写 → 待确认。
2. 工作年限：用当前日期 {today} 减去简历最早工作/实习起始时间。简历没写 → 待确认。
3. 任何状态无法确认 → 一律标"待确认"，禁止无依据负面判断。

【事实边界约束】
- analysis_basis / strengths / weaknesses 必须基于简历原文证据，逐项可追溯。
- 禁止升级措辞：不得把"参与"写成"主导/独立负责"。
- 禁止新增数字/指标/项目级别。
- 属于推断而非原文证据的内容，必须标注"（推断）"。

【requirement_id 传递要求 —— 必须严格遵守】
- requirement_matches 中的 requirement_id **必须与 jd_analysis 输入中的 requirement_id 完全一致**，不允许修改或重新生成。
- jd_quote 也应直接引用输入中的 jd_quote，除非需要结合简历证据补充说明。

【输出要求】
请严格返回如下JSON（用 ```json 代码块包裹，不要添加解释文字）：
{{
  "match_level": {{
    "overall": "较高/中等/较低",
    "ability": "较强/中等/较弱",
    "experience": "较强/中等/较弱",
    "risk": "需要优化/风险较低/风险较高"
  }},
  "requirement_matches": [
    {{
      "requirement_id": "req-001（原样复制输入中的 ID）",
      "requirement_text": "需求简述",
      "category": "hard/core/preferred",
      "match_status": "direct_match/partial_match/unverified/not_met",
      "evidence": "简历原文引用（match 类型）或差距说明（gap 类型）",
      "confidence": "high/medium/low",
      "transferable_from": null,
      "transferable_boundary": null,
      "match_reason": "完整匹配判断理由"
    }}
  ],
  "analysis_basis": [{{
    "dimension": "能力维度名（如：Agent工作流设计能力、RAG知识检索能力、硬性门槛、表达质量）",
    "items": [{{
      "type": "match或gap",
      "content": "描述（gap 项请加 [类型标记]）",
      "quote": "简历原文引用(仅match类型)",
      "match_degree": "高/中/低",
      "requirement_id": "对应的 requirement_id（可选，方便溯源）"
    }}]
  }}],
  "strengths": ["优势：具体描述（必须有简历证据）"],
  "weaknesses": ["[类型标记]不足：具体描述（基于 requirement_matches）"]
}}

【重要提醒】
- 如果 jd_analysis 中没有 requirements 字段（JD Agent 未输出），请基于核心技能/技术要求/岗位关键词的扁平列表，用相同的匹配规则手动生成 requirement_matches。
- strengths 和 weaknesses 的数量应合理（各 3-6 条），不要硬凑或遗漏。
- 对同一能力的多个工具缺口进行归并（如 Coze/Dify/n8n 合并为"低代码 Agent 平台经验"）。"""

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

    # requirement_matches 是可选字段
    rms = result.get("requirement_matches")
    if rms is not None:
        if not isinstance(rms, list):
            errors.append(f"字段 'requirement_matches' 应为数组")
        else:
            for idx, rm in enumerate(rms):
                if not isinstance(rm, dict):
                    errors.append(f"requirement_matches[{idx}] 应为对象")
                    continue
                for sub in ("requirement_id", "match_status", "category"):
                    if rm.get(sub) and not isinstance(rm.get(sub), str):
                        errors.append(f"requirement_matches[{idx}].{sub} 应为字符串")
                ms = rm.get("match_status", "")
                if ms and ms not in ("direct_match", "partial_match", "unverified", "not_met"):
                    errors.append(f"requirement_matches[{idx}].match_status 值 '{ms}' 非法")
                cat = rm.get("category", "")
                if cat and cat not in ("hard", "core", "preferred"):
                    errors.append(f"requirement_matches[{idx}].category 值 '{cat}' 非法")

    if errors:
        raise RuntimeError(f"{_AGENT_NAME} 校验失败: " + "; ".join(errors))
    return result


chain = _prompt | RunnableLambda(_llm_call) | RunnableLambda(_json_parse) | RunnableLambda(_validate)


def run(jd_analysis, resume_analysis, resume, knowledge_context):
    return chain.invoke({
        "today": _TODAY_STR,
        "jd_analysis": _dump_dict(jd_analysis),
        "resume_analysis": _dump_dict(resume_analysis),
        "resume": resume,
        "knowledge": knowledge_context or "（无）",
    })


def build_prompt(jd_analysis, resume_analysis, resume, knowledge_context):
    return _prompt.invoke({
        "today": _TODAY_STR,
        "jd_analysis": _dump_dict(jd_analysis),
        "resume_analysis": _dump_dict(resume_analysis),
        "resume": resume,
        "knowledge": knowledge_context or "（无）",
    }).to_string()

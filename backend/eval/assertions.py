"""验收断言库 — 所有 HARD_ASSERT / LOGIC_CHECK / CROSS_TAB 的具体实现

注意：SEMANTIC 类检查不放在这里（需要人工判断，框架里一律返回 MANUAL_REVIEW）。
"""
from .__init__ import CheckResult, RESULT_PASS, RESULT_FAIL, RESULT_MANUAL, HARD_ASSERT, LOGIC_CHECK, CROSS_TAB


def _cr(name, result, category, details="", evidence=""):
    return CheckResult(name=name, result=result, category=category, details=details, evidence=evidence)


# ============ HARD_ASSERT ============

def check_data_source_is_workflow(data, raw):
    """必须走 Agent Workflow，不能是 mock_fallback 或 invalid_input"""
    ds = raw.get("data_source", "") or data.get("data_source", "")
    if ds == "mock_fallback":
        return _cr("data_source", RESULT_FAIL, HARD_ASSERT,
                   f"返回了 mock_fallback（LLM 不可用）", ds)
    if ds == "invalid_input":
        return _cr("data_source", RESULT_FAIL, HARD_ASSERT,
                   f"JD 质量校验未通过（不是长度问题就是关键词缺失）", ds)
    if "agent_workflow" not in ds and "llm_api" not in ds:
        return _cr("data_source", RESULT_FAIL, HARD_ASSERT,
                   f"data_source 不符合预期：{ds}", ds)
    return _cr("data_source", RESULT_PASS, HARD_ASSERT, f"data_source={ds}", ds)


def check_match_level_has_four_fields(data, raw):
    """match_level 必须有 overall/ability/experience/risk 四个字段"""
    ml = data.get("match_level") or {}
    expected = ["overall", "ability", "experience", "risk"]
    missing = [f for f in expected if not ml.get(f)]
    if missing:
        return _cr("match_level_fields", RESULT_FAIL, HARD_ASSERT,
                   f"缺失字段: {missing}", str(ml))
    return _cr("match_level_fields", RESULT_PASS, HARD_ASSERT, "四字段齐全")


def check_analysis_basis_is_list(data, raw):
    ab = data.get("analysis_basis")
    if not isinstance(ab, list):
        return _cr("analysis_basis_type", RESULT_FAIL, HARD_ASSERT,
                   f"应为 list, 实际 {type(ab).__name__}")
    return _cr("analysis_basis_type", RESULT_PASS, HARD_ASSERT, f"len={len(ab)}")


# ============ LOGIC_CHECK ============

def check_fact_check_no_violation(data, raw):
    """fact_check.flagged 必须为 0 —— 事实越界检测不通过则整条不合格"""
    fc = data.get("fact_check") or {}
    flagged = fc.get("flagged", 0)
    violations = fc.get("violations", 0)
    checked = fc.get("checked", 0)
    if flagged > 0:
        return _cr("fact_check_zero_violations", RESULT_FAIL, LOGIC_CHECK,
                   f"flagged={flagged}, violations={violations}, checked={checked}",
                   str(data.get("rewrite_suggestions", [])))
    return _cr("fact_check_zero_violations", RESULT_PASS, LOGIC_CHECK,
               f"flagged=0, checked={checked}")


def check_gaps_have_type_tag(data, raw):
    """analysis_basis 里的 gap 项，content 应以 [表达优化]/[事实待确认]/[能力缺口] 开头"""
    gaps_total = 0
    gaps_tagged = 0
    for dim in data.get("analysis_basis", []):
        for item in dim.get("items", []):
            if item.get("type") == "gap":
                gaps_total += 1
                if str(item.get("content", "")).startswith("["):
                    gaps_tagged += 1
    if gaps_total == 0:
        return _cr("gap_type_tags", RESULT_PASS, LOGIC_CHECK, "无 gap 项（不需要分类标记）")
    if gaps_tagged < gaps_total:
        return _cr("gap_type_tags", RESULT_FAIL, LOGIC_CHECK,
                   f"有 {gaps_total - gaps_tagged}/{gaps_total} 个 gap 缺类型标记")
    return _cr("gap_type_tags", RESULT_PASS, LOGIC_CHECK,
               f"全部 {gaps_total} 个 gap 带类型标记")


def check_rewrite_grade_is_ab(data, raw):
    """rewrite_suggestions 里每条 evidence_grade 必须是 A 或 B（Prompt 准入规则）"""
    rewrites = data.get("rewrite_suggestions") or []
    bad = []
    for i, r in enumerate(rewrites):
        g = r.get("evidence_grade", "")
        if g not in ("A", "B"):
            bad.append(f"#{i}={g}")
    if bad:
        return _cr("rewrite_grade_AB", RESULT_FAIL, LOGIC_CHECK,
                   f"不符合准入的 evidence_grade: {bad}", str(rewrites))
    return _cr("rewrite_grade_AB", RESULT_PASS, LOGIC_CHECK, f"全部 {len(rewrites)} 条 rewrite grade A/B")


def check_no_forbidden_fake_graduation(data, raw, forbidden_phrases=None):
    """已知真实毕业情况的简历，不允许出现'尚未毕业/在读'等错误判断"""
    if forbidden_phrases is None:
        forbidden_phrases = ["尚未毕业", "本科在读", "尚未完成学业", "仍在校"]
    blocks = []
    for dim in data.get("analysis_basis", []):
        for item in dim.get("items", []):
            blocks.append(item.get("content", ""))
    for w in data.get("weaknesses", []):
        blocks.append(w)
    all_text = " ".join(blocks)
    found = [p for p in forbidden_phrases if p in all_text]
    if found:
        return _cr("no_fake_graduation", RESULT_FAIL, LOGIC_CHECK,
                   f"检测到错误判断: {found}", all_text[:300])
    return _cr("no_fake_graduation", RESULT_PASS, LOGIC_CHECK,
               "无错误毕业状态判断")


# ============ CROSS_TAB ============

def check_match_level_consistent_with_basis(data, raw):
    """match_level.overall 和 analysis_basis 的 gap 比例不能严重矛盾"""
    ml_overall = data.get("match_level", {}).get("overall", "")
    total = 0
    gaps = 0
    for dim in data.get("analysis_basis", []):
        for item in dim.get("items", []):
            total += 1
            if item.get("type") == "gap":
                gaps += 1
    if total == 0:
        return _cr("cross_tab_consistency", RESULT_MANUAL, CROSS_TAB,
                   "analysis_basis 为空，无法检查一致性")

    gap_ratio = gaps / total

    # overall=较高 但 gap_ratio > 0.6 → 矛盾
    if ml_overall == "较高" and gap_ratio > 0.6:
        return _cr("cross_tab_consistency", RESULT_FAIL, CROSS_TAB,
                   f"overall={ml_overall} 但 gap_ratio={gap_ratio:.1%}（矛盾）")

    # overall=较低 但 gap_ratio < 0.2 → 矛盾
    if ml_overall == "较低" and gap_ratio < 0.2:
        return _cr("cross_tab_consistency", RESULT_FAIL, CROSS_TAB,
                   f"overall={ml_overall} 但 gap_ratio={gap_ratio:.1%}（矛盾）")

    return _cr("cross_tab_consistency", RESULT_PASS, CROSS_TAB,
               f"overall={ml_overall}, gap_ratio={gap_ratio:.1%} 一致")

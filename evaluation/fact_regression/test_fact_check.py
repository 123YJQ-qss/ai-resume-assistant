"""test_fact_check.py - fact_check.py v2 单元测试

覆盖 4 条用户要求 + TP/FP/FN 计算。
v2: original 必须是 RESUME 精确子串，避免混入 step 2 触发。
"""
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "backend"))
from services import fact_check

PASS = 0
FAIL = 0

def check(label, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  ✅ {label}")
    else:
        FAIL += 1
        print(f"  ❌ {label}  {detail}")


# =====================================================
# 简历原文（精确片段，测试用 original 必须是这个字符串的子串）
# =====================================================
RESUME = """
基于 FastAPI 和 LLM 构建智能简历分析系统，将传统单 Prompt 调用重构为多 Agent Workflow，设计 JD 分析、简历解析、匹配评估、优化建议四类 Agent。
基于 Paramiko 实现 SSH 远程连接与 SFTP 文件管理，支持服务器配置文件上传、修改以及备份。
熟悉 Linux 环境及服务部署流程，了解 SSH/SFTP 远程管理、服务器配置以及应用部署。
"""

RESUME_TECH = ["Python", "FastAPI", "LLM", "Agent Workflow", "Paramiko", "Linux", "SFTP", "SSH"]


def run_test_case(label, original, revised, jd_terms_raw, expected_violations):
    """original 必须是 RESUME 精确子串。

    jd_terms_raw 是 JD 分析 Agent 原始返回（含技术词+业务词），
    先过 extract_jd_terms 过滤（与 analyze.py 调用链一致），
    再传给 check_rewrite_suggestions。
    """
    opt = {"rewrite_suggestions": [{
        "original": original,
        "revised": revised,
        "basis": "测试",
        "evidence_grade": "A",
    }]}

    # 先过滤（与 analyze.py 真实调用一致）
    filtered_terms = fact_check.extract_jd_terms(
        {"核心技能": jd_terms_raw} if isinstance(jd_terms_raw, list) else jd_terms_raw
    )

    result, summary = fact_check.check_rewrite_suggestions(
        opt, RESUME, resume_tech=RESUME_TECH, jd_terms=filtered_terms
    )

    warnings = [s.get("fact_warning") for s in result["rewrite_suggestions"] if s.get("fact_warning")]
    actual_cats = set()
    for w in warnings:
        for segment in w.split("；"):
            seg = segment.strip()
            if not seg:
                continue
            if "疑似新增技术" in seg or "original未在简历原文中找到" in seg:
                actual_cats.add("fact_invention")
            elif "疑似新增数字" in seg or "疑似新增量化" in seg:
                actual_cats.add("fake_metric")
            elif "疑似措辞升级" in seg:
                actual_cats.add("skill_upgrade")
            elif "疑似未经证实的项目级描述" in seg:
                actual_cats.add("project_level_upgrade")
            elif "evidence_grade为C/D/E" in seg:
                actual_cats.add("theoretical_to_practical")

    expected = set(expected_violations)
    tp = len(expected & actual_cats)
    fp = len(actual_cats - expected)
    fn = len(expected - actual_cats)

    return {
        "label": label, "warnings": warnings,
        "actual_cats": actual_cats, "expected_cats": expected,
        "tp": tp, "fp": fp, "fn": fn,
        "pass": (fp == 0 and fn == 0),
    }


def main():
    print("=" * 60)
    print("fact_check v2 单元测试")
    print("=" * 60)

    # ---------------- 测试 1 ----------------
    print("\n[1] 业务词不应触发 fact_invention")
    jd_mixed = ["Python", "降本提效", "技术选型", "项目闭环", "API", "稳定性保障"]
    extracted = fact_check.extract_jd_terms({"核心技能": jd_mixed})
    check("业务词被过滤", "降本提效" not in extracted and "技术选型" not in extracted
          and "项目闭环" not in extracted and "稳定性保障" not in extracted,
          f"实际: {extracted}")
    check("技术词保留", "Python" in extracted, f"实际: {extracted}")

    # original = RESUME 里真实片段
    t1 = run_test_case(
        label="业务词不触发 fact_invention",
        original="基于 FastAPI 和 LLM 构建智能简历分析系统",
        revised="基于 FastAPI 和 LLM 构建智能简历分析系统，支撑降本提效和技术选型",
        jd_terms_raw=jd_mixed,
        expected_violations=set(),  # 零违规
    )
    check("预期零违规", t1["pass"], f"actual={t1['actual_cats']} warnings={t1['warnings']}")

    # ---------------- 测试 2 ----------------
    print("\n[2] 简历没有 Docker，改写新增 Docker → 应触发 fact_invention")
    jd_with_docker = ["Docker", "Kubernetes", "CI/CD", "自动化部署"]
    extracted2 = fact_check.extract_jd_terms({"核心技能": jd_with_docker})
    check("Docker 被识别为技术词", "Docker" in extracted2 and "Kubernetes" in extracted2,
          f"实际: {extracted2}")

    t2 = run_test_case(
        label="新增技术 Docker",
        original="基于 FastAPI 和 LLM 构建智能简历分析系统",
        revised="基于 Docker 容器化 FastAPI 微服务，支持 CI/CD 自动化部署",
        jd_terms_raw=jd_with_docker,
        expected_violations={"fact_invention"},
    )
    check("fact_invention 被触发", t2["pass"],
          f"actual={t2['actual_cats']} warnings={t2['warnings']}")

    # ---------------- 测试 3 ----------------
    print("\n[3] 简历已有 FastAPI → 改写提 FastAPI 不应触发 fact_invention")
    jd_with_fastapi = ["FastAPI", "Python", "MySQL"]
    t3 = run_test_case(
        label="已有技术不触发",
        original="基于 FastAPI 和 LLM 构建智能简历分析系统",
        revised="基于 FastAPI 实现高性能异步接口开发，重构原有架构",
        jd_terms_raw=jd_with_fastapi,
        expected_violations=set(),  # FastAPI 在简历里有 → 不触发
    )
    check("已有技术不触发 fact_invention", t3["pass"],
          f"actual={t3['actual_cats']} warnings={t3['warnings']}")

    # ---------------- 测试 4 ----------------
    print("\n[4] '生产级、高可用、显著提升' 分别按现有规则处理")
    t4a = run_test_case(
        label="生产级 → project_level_upgrade",
        original="基于 FastAPI 和 LLM 构建智能简历分析系统",
        revised="基于 FastAPI 和 LLM 构建生产级智能简历分析系统",
        jd_terms_raw=["FastAPI", "LLM"],
        expected_violations={"project_level_upgrade"},  # 只触发项目级包装，不触发 fact_invention
    )
    check("生产级 → project_level_upgrade (无 fact_invention)", t4a["pass"],
          f"actual={t4a['actual_cats']}")

    t4b = run_test_case(
        label="高可用 → project_level_upgrade",
        original="基于 Paramiko 实现 SSH 远程连接与 SFTP 文件管理",
        revised="基于 Paramiko 实现高可用 SSH 远程连接与 SFTP 文件管理",
        jd_terms_raw=["SSH", "SFTP"],
        expected_violations={"project_level_upgrade"},
    )
    check("高可用 → project_level_upgrade (无 fact_invention)", t4b["pass"],
          f"actual={t4b['actual_cats']}")

    t4c = run_test_case(
        label="显著提升 → fake_metric",
        original="基于 FastAPI 和 LLM 构建智能简历分析系统",
        revised="基于 FastAPI 和 LLM 构建智能简历分析系统，显著提升分析效率",
        jd_terms_raw=["FastAPI", "LLM"],
        expected_violations={"fake_metric"},
    )
    check("显著提升 → fake_metric (无 fact_invention)", t4c["pass"],
          f"actual={t4c['actual_cats']}")

    # ---------------- 汇总 TP/FP/FN ----------------
    print("\n" + "=" * 60)
    print("TP/FP/FN 汇总")
    print("=" * 60)

    all_tests = [t1, t2, t3, t4a, t4b, t4c]
    total_tp = total_fp = total_fn = 0
    for t in all_tests:
        total_tp += t["tp"]
        total_fp += t["fp"]
        total_fn += t["fn"]
        status = "✅" if t["pass"] else "❌"
        print(f"  {status} {t['label']}")
        print(f"       expected={t['expected_cats']} actual={t['actual_cats']} "
              f"TP={t['tp']} FP={t['fp']} FN={t['fn']}")

    print(f"\n  合计: TP={total_tp}  FP={total_fp}  FN={total_fn}")
    if total_tp + total_fp + total_fn > 0:
        precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) else 1.0
        recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) else 1.0
        print(f"  precision={precision:.2f}  recall={recall:.2f}")
    print(f"\n  断言通过: {PASS}  失败: {FAIL}")
    sys.exit(0 if FAIL == 0 else 1)


if __name__ == "__main__":
    main()

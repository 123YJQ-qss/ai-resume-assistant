import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "backend"))
from services import fact_check

# 用 dataset.json 里的完整简历
with open(os.path.join(HERE, "dataset.json"), "r", encoding="utf-8") as _f:
    _dataset = json.load(_f)
RESUME = _dataset["resume"]

# 简历技术栈（从真实简历提取的关键技术词）
RESUME_TECH = [
    "Python", "FastAPI", "Django", "LLM API", "大模型API", "Agent Workflow",
    "Paramiko", "Linux", "SFTP", "SSH", "MySQL", "SQLAlchemy",
    "openpyxl", "Vue2", "DeepSeek", "OpenAI", "Coze",
    "Prompt Engineering", "RAG", "Embedding", "FAISS", "sentence-transformers",
]

# JD 技术词（与真实 JD 分析 Agent 输出一致）
JD_TERMS = [
    "Python", "FastAPI", "SQL", "大模型", "LLM API", "Prompt Engineering",
    "Agent Workflow", "AI Agent", "系统架构设计", "API 开发", "Docker",
    "Kubernetes", "降本提效", "技术选型", "项目闭环", "稳定性保障",
]

def classify_warning(warn_text):
    cats = set()
    for seg in str(warn_text or "").split("；"):
        seg = seg.strip()
        if not seg:
            continue
        if "架构能力表述升级" in seg:
            cats.add("skill_upgrade")
        elif "疑似新增技术" in seg:
            cats.add("fact_invention")
        elif "original未在简历原文中找到" in seg:
            cats.add("fact_invention")
        elif "疑似措辞升级" in seg:
            cats.add("skill_upgrade")
        elif "疑似新增数字" in seg or "疑似新增量化" in seg:
            cats.add("fake_metric")
        elif "疑似未经证实的项目级" in seg:
            cats.add("project_level_upgrade")
        elif "evidence_grade为C/D/E" in seg:
            cats.add("theoretical_to_practical")
    return cats


def replay(golden_file):
    gs = json.load(open(golden_file, encoding="utf-8"))
    results = []
    all_tp = all_fp = all_fn = 0

    for i, g in enumerate(gs):
        expected = set(g.get("expected_types") or [])
        opt = {"rewrite_suggestions": [{
            "original": g.get("original") or "",
            "revised": g.get("revised") or "",
            "basis": "离线重放",
            "evidence_grade": "A",
        }]}

        result, summary = fact_check.check_rewrite_suggestions(
            opt, RESUME, resume_tech=RESUME_TECH, jd_terms=JD_TERMS
        )
        warnings = result["rewrite_suggestions"][0].get("fact_warning")
        actual = classify_warning(warnings) if warnings else set()

        tp_set = expected & actual
        fp_set = actual - expected
        fn_set = expected - actual
        all_tp += len(tp_set); all_fp += len(fp_set); all_fn += len(fn_set)

        status = "✅" if (not fp_set and not fn_set) else "❌"
        results.append({
            "idx": i, "case_id": g["case_id"], "status": status,
            "expected": sorted(expected), "actual": sorted(actual),
            "fp": sorted(fp_set), "fn": sorted(fn_set),
            "warning": warnings, "note": g.get("review_note", "")[:70],
        })

    print("=" * 90)
    print(f"离线重放: {len(gs)} 条 | TP={all_tp} FP={all_fp} FN={all_fn}")
    print("=" * 90)
    for r in results:
        print(f"{r['status']} [{r['idx']:02d}] {r['case_id']:15s} expected={r['expected']} actual={r['actual']}")
        if r['warning']: print(f"       warn: {r['warning'][:120]}")
        if r['fp']: print(f"       FP: {r['fp']}")
        if r['fn']: print(f"       FN: {r['fn']}")

    print("\n" + "=" * 90)
    print("按违规类型聚合")
    print("=" * 90)
    types = ["fact_invention", "fake_metric", "skill_upgrade",
             "project_level_upgrade", "theoretical_to_practical"]
    tstats = {t: {"tp": 0, "fp": 0, "fn": 0} for t in types}
    for r in results:
        for t in types:
            if t in set(r["expected"]) & set(r["actual"]): tstats[t]["tp"] += 1
            if t in set(r["actual"]) - set(r["expected"]): tstats[t]["fp"] += 1
            if t in set(r["expected"]) - set(r["actual"]): tstats[t]["fn"] += 1
    for t in types:
        s = tstats[t]
        p = s["tp"] / (s["tp"] + s["fp"]) if (s["tp"] + s["fp"]) else 1.0
        rc = s["tp"] / (s["tp"] + s["fn"]) if (s["tp"] + s["fn"]) else 1.0
        print(f"  {t:25s}: TP={s['tp']:2d} FP={s['fp']:2d} FN={s['fn']:2d}  P={p:.2f} R={rc:.2f}")

    p = all_tp / (all_tp + all_fp) if (all_tp + all_fp) else 1.0
    rc = all_tp / (all_tp + all_fn) if (all_tp + all_fn) else 1.0
    print(f"\n  总计 P={p:.2f} R={rc:.2f}  仅基于 {len(gs)} 条黄金集")


if __name__ == "__main__":
    replay(os.path.join(HERE, "golden_set.json"))

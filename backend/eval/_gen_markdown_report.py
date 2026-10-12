"""Task 5: 生成人工复核 Markdown 报告

从 full_evidence/*.json + eval_report.json 提取完整内容，
生成包含完整原文/改写（不截断）的 Markdown 报告。
不调用任何 LLM API。

用法：python backend/eval/_gen_markdown_report.py
输出：backend/eval/HUMAN_REVIEW_REPORT.md
"""
import json, os, glob
from datetime import datetime

EVIDENCE_DIR = os.path.join(os.path.dirname(__file__), "full_evidence")
REPORT_PATH = os.path.join(os.path.dirname(__file__), "eval_report.json")
OUTPUT = os.path.join(os.path.dirname(__file__), "HUMAN_REVIEW_REPORT.md")

with open(REPORT_PATH, encoding="utf-8") as f:
    eval_report = json.load(f)

md = []
m = eval_report["metadata"]
md.append(f"# AI Resume Assistant — 第四阶段人工复核报告\n")
md.append(f"- **生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
md.append(f"- **评测时间**: {m['timestamp']}")
md.append(f"- **Commit**: `{m['git_commit_short']}` ({m['git_commit_full']})")
md.append(f"- **模型**: {m['model_name']}")
md.append(f"- **框架版本**: {m['eval_framework_version']}")
md.append(f"- **受控 Case 数**: {len(eval_report['cases'])}")

total_pass = sum(1 for c in eval_report['cases'] for chk in c['checks'] if chk['result'] == 'PASS')
total_fail = sum(1 for c in eval_report['cases'] for chk in c['checks'] if chk['result'] == 'FAIL')
total_manual = sum(1 for c in eval_report['cases'] for chk in c['checks'] if chk['result'] == '待人工复核')
md.append(f"- **自动化**: PASS={total_pass} / FAIL={total_fail} / 待人工复核={total_manual}\n")

# 逐 case 自动汇总表
md.append("\n## 逐 Case 自动汇总\n")
md.append("| Case | PASS | FAIL | MANUAL | total |")
md.append("|------|------|------|--------|-------|")
for cr_case in eval_report['cases']:
    p = sum(1 for c in cr_case['checks'] if c['result'] == 'PASS')
    f = sum(1 for c in cr_case['checks'] if c['result'] == 'FAIL')
    man = sum(1 for c in cr_case['checks'] if c['result'] == '待人工复核')
    t = p + f + man
    md.append(f"| {cr_case['case_id']} | {p} | {f} | {man} | {t} |")
md.append(f"| **TOTAL** | **{total_pass}** | **{total_fail}** | **{total_manual}** | **{total_pass+total_fail+total_manual}** |")

md.append("\n---\n")
md.append("## 逐 Case 详细报告\n")

case_report_map = {c["case_id"]: c for c in eval_report["cases"]}
evidence_files = sorted(glob.glob(os.path.join(EVIDENCE_DIR, "*.json")))

for ef_path in evidence_files:
    with open(ef_path, encoding="utf-8") as f:
        ev = json.load(f)

    case_id = ev["case_id"]
    resume = ev.get("resume_text", "[截断]")
    jd = ev.get("job_description", "[截断]")
    resp = ev["raw_response"]
    data = resp.get("data", {})
    cr = case_report_map.get(case_id, {})

    md.append(f"## {case_id}\n")
    md.append(f"**测试目的**: {cr.get('description', '（见 cases.py human_expect）')}")
    md.append(f"**人工期望**: `{json.dumps(cr.get('human_expect', {}), ensure_ascii=False)}`\n")

    md.append("### 1. 输入（完整不截断）\n")
    md.append(f"**简历**:\n```\n{resume}\n```")
    md.append(f"\n**JD**:\n```\n{jd}\n```\n")

    md.append("### 2. AI 综合匹配结论\n")
    ml = data.get("match_level", {})
    md.append(f"- **overall**: {ml.get('overall', '?')}")
    md.append(f"- **ability**: {ml.get('ability', '?')}")
    md.append(f"- **experience**: {ml.get('experience', '?')}")
    md.append(f"- **risk**: {ml.get('risk', '?')}\n")

    md.append("### 3. 详细分析 (analysis_basis)\n")
    for dim in data.get("analysis_basis", []):
        dim_name = dim.get("dimension", "?")
        md.append(f"\n**维度: {dim_name}**")
        for item in dim.get("items", []):
            t = item.get("type", "")
            degree = item.get("match_degree", "")
            quote = item.get("quote", "")
            content = item.get("content", "")
            icon = "🔸" if t == "gap" else "✅" if t == "match" else "ℹ️"
            md.append(f"  - {icon} **{t}** ({degree}): {content}")
            if quote:
                md.append(f"    > 原文: {quote}")

    md.append("\n### 4. 改写建议 (rewrite_suggestions)\n")
    rewrites = data.get("rewrite_suggestions", [])
    if rewrites:
        for i, r in enumerate(rewrites):
            md.append(f"\n**改写 #{i+1}** (grade={r.get('evidence_grade','?')})")
            md.append(f"- **original**: `{r.get('original','')}`")
            md.append(f"- **revised**: `{r.get('revised','')}`")
            md.append(f"- **basis**: {r.get('basis','')}")
            fw = r.get("fact_warning", "")
            if fw:
                md.append(f"- ⚠️ **fact_warning**: `{fw}`")
    else:
        md.append("_（无改写建议）_")

    md.append("\n### 5. 事实校验 (fact_check)\n")
    fc = data.get("fact_check", {})
    md.append(f"- checked={fc.get('checked',0)}  flagged={fc.get('flagged',0)}  violations={fc.get('violations',0)}")
    if fc.get("flagged", 0) > 0:
        md.append("> ⚠️ **需要人工判断拦截是否合理**（flagged>0 不是自动 FAIL，保守误报和合理拦截都可能）")

    md.append("\n### 6. 优化任务 (optimization_advice)\n")
    oa = data.get("optimization_advice", {})
    for key in ["highlight", "supplement", "expression"]:
        items = oa.get(key, [])
        if items:
            md.append(f"\n**{key}** ({len(items)} 条):")
            for it in items:
                md.append(f"  - {it}")

    md.append("\n### 7. 分类汇总\n")
    strengths = data.get("strengths", [])
    weaknesses = data.get("weaknesses", [])
    md.append(f"- strengths: {len(strengths)} 条")
    md.append(f"- weaknesses: {len(weaknesses)} 条")
    if weaknesses:
        for w in weaknesses:
            md.append(f"  - {w}")

    md.append("\n### 8. 自动化检查结果\n")
    for chk in cr.get("checks", []):
        tag = "✅" if chk["result"] == "PASS" else "❌" if chk["result"] == "FAIL" else "👀"
        cat = chk["category"]
        details = chk.get("details", "")
        md.append(f"- {tag} [{cat}] {chk['name']}")
        if details and chk["result"] != "PASS":
            md.append(f"  > {details}")

    md.append("\n### 9. 需要人工审核的具体问题\n")
    md.append("请人工审查以下 7 项语义问题（自动化无法判定）：\n")
    for chk in cr.get("checks", []):
        if chk["result"] == "待人工复核":
            ev_text = chk.get("evidence", "")[:800]
            md.append(f"- 👀 **{chk['name'].replace('SEMANTIC: ', '')}**")
            if ev_text:
                md.append(f"  > 证据: {ev_text}")

    md.append("\n---\n")

with open(OUTPUT, "w", encoding="utf-8") as f:
    f.write("\n".join(md))

print(f"✅ 已生成: {OUTPUT}")
print(f"   大小: {os.path.getsize(OUTPUT):,} 字节")
print(f"   包含 Case 数: {len(evidence_files)}")

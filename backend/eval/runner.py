"""主评测 Runner — 严格区分自动化 PASS/FAIL 与人工复核

自动化检查 → 只有 HARD_ASSERT / LOGIC_CHECK / CROSS_TAB
语义质量检查 → 一律标记「待人工复核」，不自动 PASS

用法：
  python backend/eval/runner.py                    # 跑所有 10 个 case
  python backend/eval/runner.py --only CASE1       # 只跑一个
  python backend/eval/runner.py --local            # 跑本地单元测试
"""
import sys, os, json, time, argparse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import urllib.request
import subprocess

from eval import (
    CheckResult, TestCase,
    RESULT_PASS, RESULT_FAIL, RESULT_MANUAL, RESULT_SKIP,
)
from eval.cases import build_cases, standard_checks, SEMANTIC_CHECK_DESCRIPTIONS
from eval.assertions import check_no_forbidden_fake_graduation

API_URL = "https://ai-resume-assistant-so11.onrender.com/api/analyze"
TIMEOUT = 240

# Traceability: 从后端配置读模型信息
MODEL_NAME = "deepseek-chat"  # 从 backend/config.py 确认
AGENT_WORKFLOW_VERSION = "v1"  # Agent Workflow 版本号

def _get_git_head():
    try:
        head = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=os.path.join(os.path.dirname(__file__), "..", ".."),
            stderr=subprocess.DEVNULL,
        ).decode().strip()
        short = head[:8]
        return head, short
    except Exception:
        return "unknown", "unknown"


def call_api(resume_text, jd_text):
    body = json.dumps({
        "resume_text": resume_text,
        "job_description": jd_text,
    }, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(API_URL, data=body, headers={
        "Content-Type": "application/json; charset=utf-8"
    })
    t0 = time.time()
    try:
        resp = urllib.request.urlopen(req, timeout=TIMEOUT)
        r = json.loads(resp.read().decode("utf-8"))
        return {"ok": True, "elapsed": round(time.time() - t0, 2), "response": r}
    except Exception as e:
        return {"ok": False, "elapsed": round(time.time() - t0, 2), "error": str(e)}


def run_case(case):
    results = []

    # 1. 调 API
    api_result = call_api(case["resume_text"], case["job_description"])
    if not api_result["ok"]:
        results.append(CheckResult(
            name="api_call", result=RESULT_FAIL,
            category="HARD_ASSERT",
            details=f"API 调用失败: {api_result['error']}"
        ))
        return {"case_id": case["case_id"], "api": api_result, "checks": results, "_raw_response": {}}

    raw = api_result["response"]
    data = raw.get("data", {})
    results.append(CheckResult(
        name="api_call", result=RESULT_PASS,
        category="HARD_ASSERT",
        details=f"data_source={raw.get('data_source','')}, elapsed={api_result['elapsed']}s"
    ))

    # 2. 跑标准自动化断言
    for check_fn in standard_checks():
        try:
            cr = check_fn(data, raw)
            results.append(cr)
        except Exception as e:
            results.append(CheckResult(
                name=check_fn.__name__, result=RESULT_FAIL,
                category="HARD_ASSERT",
                details=f"断言函数抛异常: {type(e).__name__}: {str(e)[:80]}"
            ))

    # 3. 跑 case 专属自动化检查（基于 human_expect）
    he = case.get("human_expect", {})

    # 禁止词检查
    if "must_not_have_fake" in he:
        cr = check_no_forbidden_fake_graduation(data, raw, he["must_not_have_fake"])
        cr.name = "no_forbidden_content"
        results.append(cr)

    # match_level 下限（不能比指定等级低）
    if "min_match_overall" in he:
        overall = data.get("match_level", {}).get("overall", "")
        hierarchy = ["较低", "中等", "较高"]
        if overall:
            idx = hierarchy.index(overall) if overall in hierarchy else -1
            min_idx = hierarchy.index(he["min_match_overall"]) if he["min_match_overall"] in hierarchy else 0
            ok = idx >= min_idx
            results.append(CheckResult(
                name="match_overall_min",
                result=RESULT_PASS if ok else RESULT_FAIL,
                category="LOGIC_CHECK",
                details=f"overall={overall}, min_allowed={he['min_match_overall']}",
                evidence=json.dumps(data.get("match_level", {}), ensure_ascii=False),
            ))

    # match_level 上限
    if "max_match_overall" in he:
        overall = data.get("match_level", {}).get("overall", "")
        hierarchy = ["较低", "中等", "较高"]
        if overall:
            idx = hierarchy.index(overall) if overall in hierarchy else 99
            max_idx = hierarchy.index(he["max_match_overall"]) if he["max_match_overall"] in hierarchy else 2
            ok = idx <= max_idx
            results.append(CheckResult(
                name="match_overall_max",
                result=RESULT_PASS if ok else RESULT_FAIL,
                category="LOGIC_CHECK",
                details=f"overall={overall}, max_allowed={he['max_match_overall']}",
            ))

    # 4. 标记语义检查为「待人工复核」
    for desc in SEMANTIC_CHECK_DESCRIPTIONS:
        # 语义检查的上下文证据
        evidence = ""
        if "匹配等级" in desc:
            evidence = json.dumps(data.get("match_level", {}), ensure_ascii=False)
        elif "技术要求" in desc or "关键技术" in desc:
            dims = data.get("analysis_basis", [])
            evidence = json.dumps(dims[:2], ensure_ascii=False)
        elif "事实幻觉" in desc:
            evidence = json.dumps(data.get("rewrite_suggestions", [])[:2], ensure_ascii=False)
        elif "时间推断" in desc:
            all_text = " ".join(
                item.get("content", "")
                for dim in data.get("analysis_basis", [])
                for item in dim.get("items", [])
            )
            evidence = all_text[:500]

        results.append(CheckResult(
            name=f"SEMANTIC: {desc}",
            result=RESULT_MANUAL,
            category="SEMANTIC",
            details="自动化无法判定，需人工看证据",
            evidence=evidence,
        ))

    return {
        "case_id": case["case_id"],
        "description": case.get("description", ""),
        "human_expect": he,
        "api_elapsed": api_result["elapsed"],
        "checks": results,
        "_raw_response": raw,
        "evidence_summary": {
            "match_level": data.get("match_level"),
            "rewrite_count": len(data.get("rewrite_suggestions") or []),
            "gap_count": sum(
                1 for dim in data.get("analysis_basis", [])
                for item in dim.get("items", [])
                if item.get("type") == "gap"
            ),
            "fact_check": data.get("fact_check"),
        },
    }


def main():
    parser = argparse.ArgumentParser(description="AI Resume Assistant 回归评测")
    parser.add_argument("--only", default=None, help="只跑指定 case_id")
    parser.add_argument("--skip-api", action="store_true", help="跳过线上 API（只跑本地单元测试）")
    args = parser.parse_args()

    cases = build_cases()
    if args.only:
        cases = [c for c in cases if c["case_id"] == args.only]
        if not cases:
            print(f"⚠️ 找不到 case_id={args.only}")
            sys.exit(1)

    print("=" * 70)
    print(f"AI Resume Assistant 回归评测 Runner")
    print(f"目标: {API_URL}")
    print(f"时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Case 数: {len(cases)}")

    head_full, head_short = _get_git_head()
    print(f"Commit: {head_short}")
    print(f"模型: {MODEL_NAME}")
    print("=" * 70)

    report = {
        "metadata": {
            "timestamp": time.strftime('%Y-%m-%d %H:%M:%S'),
            "api_url": API_URL,
            "git_commit_full": head_full,
            "git_commit_short": head_short,
            "model_name": MODEL_NAME,
            "agent_workflow_version": AGENT_WORKFLOW_VERSION,
            "eval_framework_version": "v2",
        },
        "cases": [],
    }

    # 完整证据本地保存目录（不进 git，用于人工复核）
    full_evidence_dir = os.path.join(os.path.dirname(__file__), "full_evidence")
    os.makedirs(full_evidence_dir, exist_ok=True)

    # 汇总统计
    total_pass = 0
    total_fail = 0
    total_manual = 0
    cases_fail = 0

    for i, case in enumerate(cases):
        print(f"\n--- [{i+1}/{len(cases)}] {case['case_id']} ---")
        print(f"  描述: {case.get('description', '')}")

        if args.skip_api:
            print("  ⏭ 跳过 API 调用（--skip-api）")
            continue

        cr = run_case(case)
        report_case = {
            "case_id": cr["case_id"],
            "description": cr.get("description", ""),
            "human_expect": cr.get("human_expect", {}),
            "api_elapsed": cr.get("api_elapsed"),
            "checks": [chk.to_dict() for chk in cr["checks"]],  # 转 dict 以便 JSON 序列化
            "evidence_summary": cr.get("evidence_summary", {}),
        }
        report["cases"].append(report_case)

        # 完整脱敏证据保存（不进 git，用于人工复核时看完整 response）
        try:
            raw_resp = cr.get("_raw_response") or {}
            safe_id = case["case_id"].replace("/", "_")
            with open(os.path.join(full_evidence_dir, f"{safe_id}.json"), "w", encoding="utf-8") as fe:
                json.dump({
                    "case_id": case["case_id"],
                    "timestamp": report["metadata"]["timestamp"],
                    "git_commit": head_full,
                    "model": MODEL_NAME,
                    # 输入（脱敏：虚构姓名已脱敏，这里仅截断）
                    "resume_text": case["resume_text"][:500],
                    "job_description": case["job_description"][:500],
                    # 完整 response
                    "raw_response": raw_resp,
                }, fe, ensure_ascii=False, indent=2)
        except Exception:
            pass  # 证据保存失败不影响主流程

        has_fail = False
        for chk in cr["checks"]:
            tag = chk.result
            if tag == RESULT_PASS:
                total_pass += 1
            elif tag == RESULT_FAIL:
                total_fail += 1
                has_fail = True
            elif tag == RESULT_MANUAL:
                total_manual += 1
            print(f"  [{tag}] ({chk.category}) {chk.name}")
            if tag == RESULT_FAIL:
                print(f"         ❌ {chk.details}")
        if has_fail:
            cases_fail += 1

        # 证据摘要
        es = cr.get("evidence_summary", {})
        print(f"\n  摘要: overall={es.get('match_level', {}).get('overall', '?')}  "
              f"gaps={es.get('gap_count', '?')}  "
              f"rewrites={es.get('rewrite_count', '?')}  "
              f"fact_check={es.get('fact_check', {})}")

    print("\n" + "=" * 70)
    print(f"自动化通过: {total_pass}  |  自动化失败: {total_fail}  |  待人工复核: {total_manual}")
    print(f"有失败的 Case: {cases_fail}/{len(cases)}")
    print("=" * 70)

    # 保存报告（脱敏：不回显完整简历/JD）
    out_path = os.path.join(os.path.dirname(__file__), "eval_report.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"\n报告已保存: {out_path}")
    print("（报告中 check.evidence 字段包含敏感证据摘要，发布前请人工审核）")

    return 0 if total_fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

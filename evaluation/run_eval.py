"""run_eval.py - 三组消融对照评测（A/B/C）。

用法（在 backend 目录外运行均可，脚本会自行处理 sys.path）：
    python evaluation/run_eval.py --backend real --out evaluation/results/eval_ablation.json
    python evaluation/run_eval.py --backend mock     # 管道自检（token usage 为 N/A）

三组定义：
    A baseline      = 单 Prompt，无 RAG: build_single_prompt(resume, jd, "") + chat + parse
    B baseline_rag  = 单 Prompt + RAG:   _retrieve_knowledge(jd) 注入后再单次调用
    C improved      = Agent Workflow + RAG: analyze._run_workflow(resume, jd)（4 Agent 串行）

P0-4 token 统计：运行时包裹 LLMService._log_tokens 捕获真实 API usage
    （prompt_tokens / completion_tokens / total_tokens），不改任何业务代码；
    无真实 usage（mock 后端）时输出 None（报告显示 N/A）。
"""
import argparse
import json
import os
import sys
import time

BASE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE, "data")
BACKEND_DIR = os.path.join(BASE, "..", "backend")

sys.path.insert(0, DATA_DIR)
sys.path.insert(0, BACKEND_DIR)

import testset  # noqa: E402
import metrics as M  # noqa: E402
from api import analyze as analyze_mod  # noqa: E402
from services import llm_service  # noqa: E402
from agents import jd_agent, resume_agent, match_agent, optimize_agent  # noqa: E402

# ---------------- P0-4：真实 usage 采集（运行时包裹，不改业务文件） ----------------

USAGE = {"prompt": 0, "completion": 0, "total": 0, "calls": 0}
_orig_log_tokens = llm_service.LLMService._log_tokens


def _capturing_log_tokens(self, usage):
    _orig_log_tokens(usage)  # 原 _log_tokens 为 staticmethod，无需传 self；保留原打印行为
    if not usage:
        return
    if "prompt_tokens" in usage or "completion_tokens" in usage:  # OpenAI 兼容
        USAGE["prompt"] += usage.get("prompt_tokens") or 0
        USAGE["completion"] += usage.get("completion_tokens") or 0
        USAGE["total"] += usage.get("total_tokens") or 0
    else:  # Coze 格式
        USAGE["prompt"] += usage.get("input_count") or 0
        USAGE["completion"] += usage.get("output_count") or 0
        USAGE["total"] += usage.get("token_count") or 0
    USAGE["calls"] += 1


llm_service.LLMService._log_tokens = _capturing_log_tokens


def reset_usage():
    USAGE.update({"prompt": 0, "completion": 0, "total": 0, "calls": 0})


def accumulate_usage(dest):
    for k in ("prompt", "completion", "total", "calls"):
        dest[k] += USAGE[k]


def patch_llm(backend):
    """把评测后端挂到 services.llm_service，analyze.py 会通过同一模块对象引用它。"""
    capture = {"agent_outputs": {}, "prompt_chars": 0}

    def is_configured():
        return backend.is_configured()

    def get_provider():
        return backend.get_provider()

    def chat(prompt):
        return backend.chat(prompt)

    def run_agent(agent_name, prompt):
        capture["prompt_chars"] += len(prompt)
        out = backend.run_agent(agent_name, prompt)
        capture["agent_outputs"][agent_name] = out
        return out

    llm_service.is_configured = is_configured
    llm_service.get_provider = get_provider
    llm_service.chat = chat
    llm_service.run_agent = run_agent
    return capture


# ---------------- 三组运行流程 ----------------

def _run_single(case, backend, knowledge):
    """单 Prompt 公共实现（A/B 仅知识注入不同）。"""
    t0 = time.perf_counter()
    prompt = analyze_mod.build_single_prompt(case["resume"], case["jd"], knowledge)
    meta = {"prompt_chars": len(prompt), "parse_success": False, "workflow_success": True, "error": None}
    try:
        content = backend.chat(prompt)
        meta["parse_success"] = llm_service.parse_json_from_text(content) is not None
        result = analyze_mod._parse_ai_response(content)
    except Exception as e:
        meta["workflow_success"] = False
        meta["error"] = str(e)
        result = analyze_mod.get_mock_result()
        result["data_source"] = "mock_fallback"
        result["warning"] = "评测注入错误"
    meta["latency_ms"] = round((time.perf_counter() - t0) * 1000, 2)
    return result, meta


def run_baseline(case, backend):
    """A：单 Prompt，无 RAG。"""
    return _run_single(case, backend, knowledge="")


def run_baseline_rag(case, backend):
    """B：单 Prompt + RAG（与生产降级路径一致的注入方式）。"""
    knowledge = analyze_mod._retrieve_knowledge(case["jd"])
    return _run_single(case, backend, knowledge=knowledge)


def run_improved(case, backend):
    """C：Agent Workflow + RAG（RAG 注入 Match Agent）。"""
    t0 = time.perf_counter()
    meta = {"parse_success": True, "workflow_success": True, "error": None}
    try:
        result = analyze_mod._run_workflow(case["resume"], case["jd"])
    except Exception as e:
        meta["workflow_success"] = False
        meta["error"] = str(e)
        result = analyze_mod.get_mock_result()
        result["data_source"] = "mock_fallback"
        result["warning"] = "评测注入错误"
    meta["latency_ms"] = round((time.perf_counter() - t0) * 1000, 2)
    return result, meta


def run_improved_d(case, backend):
    """D：Agent Workflow，但 RAG 仅注入优化建议环节（不进 Match Agent，不参与 overall 判定）。

    评测侧实验变体：结构与 _run_workflow 一致，仅知识注入位置不同，不改业务代码。
    """
    t0 = time.perf_counter()
    meta = {"parse_success": True, "workflow_success": True, "error": None}
    try:
        knowledge_context = analyze_mod._retrieve_knowledge(case["jd"])

        jd_analysis = llm_service.run_agent("JD分析Agent", jd_agent.build_prompt(case["jd"]))
        resume_analysis = llm_service.run_agent("简历分析Agent", resume_agent.build_prompt(case["resume"]))

        # 差异点 1：Match Agent 不注入知识（空知识上下文）
        match_result = llm_service.run_agent(
            "匹配评估Agent",
            match_agent.build_prompt(jd_analysis, resume_analysis, case["resume"], ""),
        )

        # 差异点 2：RAG 仅注入优化建议环节，用于缺口识别与改写建议
        opt_prompt = optimize_agent.build_prompt(jd_analysis, match_result, case["resume"])
        if knowledge_context:
            opt_prompt += ("\n\n【岗位知识库参考】（仅用于缺口识别与改写建议，不参与匹配等级判断）\n"
                           + knowledge_context)
        opt_result = llm_service.run_agent("优化建议Agent", opt_prompt)

        result = analyze_mod.normalize_result({
            "match_level": match_result.get("match_level"),
            "analysis_basis": match_result.get("analysis_basis"),
            "strengths": match_result.get("strengths"),
            "weaknesses": match_result.get("weaknesses"),
            "rewrite_suggestions": opt_result.get("rewrite_suggestions"),
            "optimization_advice": opt_result.get("optimization_advice"),
        })
        result["data_source"] = analyze_mod.build_data_source("agent_workflow")
    except Exception as e:
        meta["workflow_success"] = False
        meta["error"] = str(e)
        result = analyze_mod.get_mock_result()
        result["data_source"] = "mock_fallback"
        result["warning"] = "评测注入错误"
    meta["latency_ms"] = round((time.perf_counter() - t0) * 1000, 2)
    return result, meta


RUNNERS = {
    "baseline": run_baseline,
    "baseline_rag": run_baseline_rag,
    "improved": run_improved,
    "improved_d": run_improved_d,
}


def compute_case_metrics(case, result, meta, jd_analysis):
    gap = M.gap_f1(M.extract_gap_texts(result), case.get("expected_gaps"))
    ml = result.get("match_level")
    row = {
        "id": case["id"],
        "category": case["category"],
        "workflow_success": meta["workflow_success"],
        "parse_success": meta["parse_success"],
        "field_completeness": M.field_completeness(result),
        "match_strict": M.match_level_accuracy(ml, case["expected_match_level"]) if meta["workflow_success"] else None,
        "match_graded": M.match_level_graded(ml, case["expected_match_level"]) if meta["workflow_success"] else None,
        "match_overall": M.match_level_overall(ml, case["expected_match_level"]) if meta["workflow_success"] else None,
        "gap_precision": gap["precision"],
        "gap_recall": gap["recall"],
        "gap_f1": gap["f1"],
        "suggestion_executability": M.suggestion_executability(result),
        "latency_ms": meta["latency_ms"],
        "prompt_chars": meta["prompt_chars"],
        # 留存原始输出片段，便于后续复算指标而无需重复调用 LLM
        "match_level_output": result.get("match_level") if isinstance(result, dict) else None,
        "gap_texts_output": M.extract_gap_texts(result),
    }
    if meta["workflow_success"] and jd_analysis is not None:
        skills = M.extract_skills_from_jd_analysis(jd_analysis)
        kw = M.set_f1(skills, case["expected_skills"])
        row["keyword_f1"] = kw["f1"]
        row["keyword_precision"] = kw["precision"]
        row["keyword_recall"] = kw["recall"]
    else:
        row["keyword_f1"] = None
        row["keyword_precision"] = None
        row["keyword_recall"] = None
    return row


def summarize(rows, key):
    vals = [r[key] for r in rows if r.get(key) is not None]
    return M.aggregate(vals)


def build_report_data(group_rows, n_cases, cfg, group_usage):
    def block(rows, usage):
        has_usage = usage["calls"] > 0
        return {
            "field_completeness": summarize(rows, "field_completeness")["mean"],
            "parse_success": summarize(rows, "parse_success")["mean"],
            "workflow_success": summarize(rows, "workflow_success")["mean"],
            "suggestion_executability": summarize(rows, "suggestion_executability")["mean"],
            "match_strict": summarize(rows, "match_strict")["mean"],
            "match_graded": summarize(rows, "match_graded")["mean"],
            "match_overall": summarize(rows, "match_overall")["mean"],
            "gap_precision": summarize(rows, "gap_precision")["mean"],
            "gap_recall": summarize(rows, "gap_recall")["mean"],
            "gap_f1": summarize(rows, "gap_f1")["mean"],
            "avg_latency_ms": summarize(rows, "latency_ms")["mean"],
            "avg_prompt_chars": summarize(rows, "prompt_chars")["mean"],
            # P0-4：真实 API usage（每次完整流程的平均值）；无真实 usage 时为 None（N/A）
            "real_prompt_tokens": round(usage["prompt"] / n_cases, 1) if has_usage else None,
            "real_completion_tokens": round(usage["completion"] / n_cases, 1) if has_usage else None,
            "real_total_tokens": round(usage["total"] / n_cases, 1) if has_usage else None,
        }

    return {
        "n_cases": n_cases,
        "config": cfg,
        "groups": {
            name: block(group_rows[name], group_usage[name])
            for name in group_rows
        },
        "rows": {name: group_rows[name] for name in group_rows},
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--backend", choices=["mock", "real"], default="mock")
    ap.add_argument("--fault-rate", type=float, default=0.0)
    ap.add_argument("--malformed-rate", type=float, default=0.0)
    ap.add_argument("--out", default=os.path.join(BASE, "results", "eval_ablation.json"))
    ap.add_argument("--groups", default="baseline,baseline_rag,improved",
                    help="逗号分隔的实验组（默认全部三组）")
    args = ap.parse_args()

    if args.backend == "real":
        from llm_backends import RealBackend
        backend = RealBackend()
    else:
        from llm_backends import MockBackend
        backend = MockBackend(fault_rate=args.fault_rate, malformed_rate=args.malformed_rate)

    groups = [g.strip() for g in args.groups.split(",") if g.strip()]
    for g in groups:
        if g not in RUNNERS:
            raise SystemExit(f"未知实验组: {g}（可选: {', '.join(RUNNERS)}）")

    capture = patch_llm(backend)

    group_rows = {g: [] for g in groups}
    group_usage = {g: {"prompt": 0, "completion": 0, "total": 0, "calls": 0} for g in groups}

    for idx, case in enumerate(testset.TEST_CASES):
        if hasattr(backend, "begin"):
            backend.begin(case, idx)

        for g in groups:
            capture["agent_outputs"] = {}
            capture["prompt_chars"] = 0
            reset_usage()

            res, meta = RUNNERS[g](case, backend)

            accumulate_usage(group_usage[g])
            if g in ("improved", "improved_d"):
                meta["prompt_chars"] = capture["prompt_chars"]
            jd_analysis = capture["agent_outputs"].get("JD分析Agent")
            row = compute_case_metrics(case, res, meta, jd_analysis)
            row["group"] = g
            group_rows[g].append(row)
            print(f"[{idx + 1}/{len(testset.TEST_CASES)}] {case['id']} {g} 完成 "
                  f"latency={meta['latency_ms']}ms")

    report = build_report_data(group_rows, len(testset.TEST_CASES), {
        "backend": args.backend,
        "fault_rate": args.fault_rate,
        "malformed_rate": args.malformed_rate,
        "groups": groups,
    }, group_usage)

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(json.dumps({k: report[k] for k in ("n_cases", "config", "groups")},
                     ensure_ascii=False, indent=2))
    print("\n结果已写入:", args.out)


if __name__ == "__main__":
    main()

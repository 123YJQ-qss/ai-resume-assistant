"""
backend/eval/compare_modes.py — Workflow vs Tool Agent A/B 对比脚本

离线脚本，一次性工具。不改业务逻辑、不加新依赖。
只调用 analyze.analyze_resume()（内部设置 AGENT_MODE 环境变量切换路径）。

用法：
    cd backend
    ..\.venv\Scripts\python.exe -m eval.compare_modes
    ..\.venv\Scripts\python.exe -m eval.compare_modes --limit 3 --mode workflow
    ..\.venv\Scripts\python.exe -m eval.compare_modes --limit 2 --mode both

输入：data/eval_cases.jsonl（不存在则生成 20 条空模板）
输出：results/compare_YYYYMMDD_HHMM.csv + 终端 markdown 汇总
"""
import argparse
import csv
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

# ---- 路径 ----
BACKEND_DIR = Path(__file__).resolve().parent.parent   # backend/
PROJECT_ROOT = BACKEND_DIR.parent                      # 项目根
DATA_DIR = PROJECT_ROOT / "data"
RESULTS_DIR = PROJECT_ROOT / "results"
CASES_FILE = DATA_DIR / "eval_cases.jsonl"

# 确保 data / results 目录存在
DATA_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def _load_dotenv():
    """加载 .env（从 analyze.py 复制过来，保持一致）。"""
    for env_file in (BACKEND_DIR / ".env", PROJECT_ROOT / ".env"):
        if not env_file.exists():
            continue
        for raw in env_file.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def _ensure_cases_file():
    """cases 文件不存在时，生成 20 条空模板让用户填。"""
    if CASES_FILE.exists():
        return

    print(f"📝 {CASES_FILE} 不存在，生成 20 条空模板...")
    print("   请填入真实 jd / resume / expected_level 后重跑脚本。\n")

    with open(CASES_FILE, "w", encoding="utf-8") as f:
        for i in range(1, 21):
            case = {
                "case_id": f"case_{i:02d}",
                "jd": "",
                "resume": "",
                "expected_level": "较高/中等/较低",
                "note": f"第 {i} 条用例：请在此填 jd、resume 和预期等级",
            }
            f.write(json.dumps(case, ensure_ascii=False) + "\n")

    print(f"✅ 模板已生成：{CASES_FILE}")
    print("   每一行是一个 JSON 对象，字段：case_id, jd, resume, expected_level")
    print("   expected_level 取值：较高 / 中等 / 较低\n")
    sys.exit(0)


def _load_cases():
    """从 JSONL 加载所有 case。"""
    cases = []
    with open(CASES_FILE, encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            try:
                cases.append(json.loads(line))
            except json.JSONDecodeError as e:
                print(f"⚠️  第 {line_no} 行 JSON 解析失败，跳过: {e}")
    return cases


def _resolve_level(match_level_dict):
    """从 match_level dict 提取 overall 等级。"""
    if not isinstance(match_level_dict, dict):
        return ""
    return match_level_dict.get("overall", "")


def _run_once(mode: str, jd: str, resume: str) -> dict:
    """跑一次分析，返回 {status, level, latency_ms, token_info...}。"""
    os.environ["AGENT_MODE"] = mode

    from services import llm_service
    llm_service.reset_token_accum()

    t0 = time.time()
    try:
        # 延迟导入：确保环境变量生效
        from api import analyze
        result = analyze.analyze_resume(resume, jd)
        latency_ms = int((time.time() - t0) * 1000)

        level = _resolve_level(result.get("match_level", {}))
        error = ""
        data_source = result.get("data_source", "")
        fc = result.get("fact_check", {})
        flagged = fc.get("flagged", 0) if isinstance(fc, dict) else 0

        accum = llm_service.get_token_accum()

        return {
            "status": "ok",
            "level": level,
            "latency_ms": latency_ms,
            "data_source": data_source,
            "fact_check_flagged": flagged,
            "tool_calls_count": "",
            "rounds": "",
            "prompt_tokens": accum["prompt_tokens"],
            "completion_tokens": accum["completion_tokens"],
            "error": error,
        }
    except Exception as e:
        latency_ms = int((time.time() - t0) * 1000)
        err_type = type(e).__name__
        err_msg = str(e)[:200]
        accum = llm_service.get_token_accum()
        return {
            "status": "error",
            "level": "",
            "latency_ms": latency_ms,
            "data_source": "",
            "fact_check_flagged": "",
            "tool_calls_count": "",
            "rounds": "",
            "prompt_tokens": accum["prompt_tokens"],
            "completion_tokens": accum["completion_tokens"],
            "error": f"{err_type}: {err_msg}",
        }


def main():
    parser = argparse.ArgumentParser(description="Workflow vs Tool Agent A/B 对比")
    parser.add_argument("--limit", type=int, default=0, help="只跑前 N 条（0=全部）")
    parser.add_argument("--mode", type=str, default="both",
                        choices=["both", "workflow", "tool_calling"],
                        help="跑哪种模式（default: both）")
    parser.add_argument("--sleep", type=float, default=2.0, help="每条之间 sleep 秒数（default: 2）")
    args = parser.parse_args()

    _load_dotenv()
    _ensure_cases_file()

    # 初始化 LLM 单例（避免 analyze_resume 内部首次 import 时机不同）
    from services import llm_service
    if not llm_service.is_configured():
        print("❌ LLM Provider 未配置（DEEPSEEK_API_KEY 或 OPENAI_API_KEY）")
        sys.exit(1)

    cases = _load_cases()
    if args.limit > 0:
        cases = cases[:args.limit]

    if not cases:
        print("❌ cases 文件为空，请先填入 jd/resume/expected_level")
        sys.exit(1)

    print(f"📋 加载 {len(cases)} 条用例，模式: {args.mode}")
    print(f"   输入: {CASES_FILE}")
    print(f"   每条之间 sleep: {args.sleep}s\n")

    # ---- 跑所有 case ----
    rows = []   # CSV 行
    modes_to_run = ["workflow", "tool_calling"] if args.mode == "both" else [args.mode]

    for idx, case in enumerate(cases, 1):
        case_id = case.get("case_id", f"case_{idx:02d}")
        jd = case.get("jd", "")
        resume = case.get("resume", "")
        expected = case.get("expected_level", "")

        if not jd.strip() or not resume.strip():
            print(f"[{idx}/{len(cases)}] {case_id} — ⚠️  跳过（jd 或 resume 为空）")
            # 跳过的也写一行 CSV（便于后续补跑时对齐）
            for mode in modes_to_run:
                rows.append({
                    "case_id": case_id, "mode": mode,
                    "output_level": "", "hit_expected": "",
                    "latency_ms": "", "prompt_tokens": "", "completion_tokens": "",
                    "tool_calls_count": "", "rounds": "", "error": "skipped_empty_input",
                })
            continue

        for mode in modes_to_run:
            label = "🔧 workflow" if mode == "workflow" else "🧪 tool_calling"
            print(f"[{idx}/{len(cases)}] {case_id} → {label} ...", end=" ", flush=True)

            result = _run_once(mode, jd, resume)

            hit = ""
            if result["status"] == "ok" and expected:
                hit = "✅" if result["level"] == expected else "❌"

            if result["status"] == "ok":
                print(f"{result['level']} {hit} ({result['latency_ms']}ms)")
            else:
                print(f"❌ ERROR: {result['error'][:60]}")

            rows.append({
                "case_id": case_id,
                "mode": mode,
                "output_level": result["level"],
                "hit_expected": hit,
                "latency_ms": result["latency_ms"],
                "prompt_tokens": result["prompt_tokens"],
                "completion_tokens": result["completion_tokens"],
                "tool_calls_count": result["tool_calls_count"],
                "rounds": result["rounds"],
                "error": result["error"],
            })

            # sleep（case 之间 + 同一个 case 两个模式之间）
            time.sleep(args.sleep)

    # ---- 写 CSV ----
    ts = datetime.now().strftime("%Y%m%d_%H%M")
    csv_path = RESULTS_DIR / f"compare_{ts}.csv"
    fieldnames = ["case_id", "mode", "output_level", "hit_expected",
                  "latency_ms", "prompt_tokens", "completion_tokens",
                  "tool_calls_count", "rounds", "error"]

    with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\n📄 CSV 已保存: {csv_path}")

    # ---- 汇总 markdown 表 ----
    print("\n" + "=" * 80)
    print("📊 汇总结果")
    print("=" * 80)

    # 按 mode 分组
    summary = {}
    for row in rows:
        mode = row["mode"]
        if row["error"] == "skipped_empty_input":
            continue
        summary.setdefault(mode, {"total": 0, "hit": 0, "errors": 0,
                                   "latencies": [], "rounds": []})
        s = summary[mode]
        s["total"] += 1
        if row["error"]:
            s["errors"] += 1
        else:
            # hit_expected 是 ✅ 时算命中
            if row["hit_expected"] == "✅":
                s["hit"] += 1
            if row["latency_ms"]:
                s["latencies"].append(int(row["latency_ms"]))
            if row["rounds"]:
                s["rounds"].append(int(row["rounds"]))

    # 打印 markdown 表
    print()
    header = "| 模式 | 条数 | 准确率 | 平均耗时s | 平均轮次 | 平均工具调用 | 失败数 |"
    sep =   "|------|------|--------|-----------|----------|-------------|--------|"
    print(header)
    print(sep)

    for mode, s in summary.items():
        total = s["total"]
        if total == 0:
            continue
        accuracy = f"{s['hit']}/{total - s['errors']}" if total - s['errors'] > 0 else "-"
        avg_latency = f"{sum(s['latencies']) / len(s['latencies']) / 1000:.1f}" if s["latencies"] else "-"
        avg_rounds = f"{sum(s['rounds']) / len(s['rounds']):.1f}" if s["rounds"] else "-"

        label = "Workflow" if mode == "workflow" else "Tool Calling"
        print(f"| {label} | {total} | {accuracy} | {avg_latency} | {avg_rounds} | - | {s['errors']} |")

    print(f"\n💡 说明：准确率 = output_level == expected_level 的比例")
    print(f"   CSV 中 hit_expected ✅/❌ 可逐行查看每个 case 的命中情况")


if __name__ == "__main__":
    main()

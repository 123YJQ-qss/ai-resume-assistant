"""test_run_evaluation.py - 评测器自身的最小自动化测试

验证 5 条验收标准：
  1. clean mock 不产生误报（policy_status=all_clear）
  2. adversarial mock 能检出预期类型（expectation_status=met）
  3. real 后端缺少配置时，不带 --allow-fallback 应失败（exit_code != 0）
  4. 显式 --allow-fallback 时正确标记 data_source=mock_fallback
  5. 输出 JSON 可读取且字段完整

运行：python evaluation/fact_regression/test_run_evaluation.py
"""
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "run_evaluation.py")

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


def run(cmd, env=None, cwd=None, capture_output=True):
    """subprocess.run 的薄封装，返回 (returncode, stdout, stderr)。"""
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    proc = subprocess.run(
        cmd,
        env=merged_env,
        cwd=cwd or os.path.dirname(SCRIPT),
        capture_output=capture_output,
        text=True,
        timeout=120,
    )
    return proc.returncode, proc.stdout or "", proc.stderr or ""


def main():
    print("=" * 60)
    print("评测器自检")
    print("=" * 60)

    # ---------- Test 1 & 2: mock 模式 ----------
    print("\n[1] mock backend：clean 不应误报，adversarial 应检出")
    out_json = os.path.join(HERE, "results", "_test_mock.json")
    rc, stdout, stderr = run(
        [sys.executable, "-u", SCRIPT, "--backend", "mock",
         "--out", out_json]
    )
    check("mock 模式退出码 = 0", rc == 0, f"got {rc}")
    with open(out_json, "r", encoding="utf-8") as f:
        report = json.load(f)

    # 1a. clean mock → all_clear
    clean_case = next(c for c in report["cases"] if c["mock_type"] == "clean")
    check("clean mock 无违规（policy_status=all_clear）",
          clean_case["policy_status"] == "all_clear",
          clean_case["fact_warnings"])

    # 2. adversarial mock → expectation 全 met
    adv_cases = [c for c in report["cases"] if c["mock_type"] == "adversarial"]
    check(f"adversarial mock {len(adv_cases)} 个用例全部 met",
          all(c["expectation_status"] == "met" for c in adv_cases),
          next((c["case_id"] for c in adv_cases if c["expectation_status"] != "met"), ""))

    # data_source 标记
    # mock backend 下 real case：Workflow 跑通 → data_source=mock_passthrough
    # （真实 Workflow 路径、真实 evidence 挂接、不调用真实 Provider）
    real_cases = [c for c in report["cases"] if c["mock_type"] == "real"]
    for c in real_cases:
        check(f"real 类 case data_source=mock_passthrough（Workflow 跑通）",
              c["data_source"] == "mock_passthrough",
              f"{c['case_id']}: {c['data_source']}")

    # mock_clean 必须有 rewrite_suggestions（至少一条）
    clean_cases = [c for c in report["cases"] if c["mock_type"] == "clean"]
    check("mock_clean 至少有一条 rewrite_suggestion",
          all(c["rewrite_suggestion_count"] >= 1 for c in clean_cases),
          f"clean_cases={[(c['case_id'], c['rewrite_suggestion_count']) for c in clean_cases]}")

    # mock_clean execution_status 必须 success
    check("mock_clean execution_status=success",
          all(c["execution_status"] == "success" for c in clean_cases))
    for c in adv_cases:
        check(f"adversarial case data_source=mock_adversarial",
              c["data_source"] == "mock_adversarial",
              c["case_id"])

    # ---------- Test 3: real backend 默认失败 ----------
    print("\n[2] real backend：Provider 未配置时不带 --allow-fallback 应失败")
    # 清空 DEEPSEEK_API_KEY + LLM_PROVIDER 环境变量
    env_no_key = os.environ.copy()
    for k in list(env_no_key.keys()):
        if k.upper() in ("DEEPSEEK_API_KEY", "OPENAI_API_KEY", "COZE_API_KEY",
                          "LLM_PROVIDER"):
            del env_no_key[k]
    # 还得清 .env 加载的影响：在子进程里 unset
    # 用 env 参数覆盖
    env_no_key["DEEPSEEK_API_KEY"] = ""
    env_no_key["LLM_PROVIDER"] = ""
    rc, stdout, stderr = run(
        [sys.executable, "-u", SCRIPT, "--backend", "real",
         "--out", os.path.join(HERE, "results", "_test_real_fail.json")],
        env=env_no_key,
    )
    check("real backend 无配置 → 非零退出码", rc != 0, f"got {rc}")
    combined = (stdout + stderr).lower()
    check("错误信息含 'Provider 未配置'", "provider 未配置" in combined,
          f"stdout={stdout.strip()[-200:]}")

    # ---------- Test 4: real backend + --allow-fallback → 正确降级 ----------
    print("\n[3] real backend + --allow-fallback：应执行并标记 mock_fallback")
    rc, stdout, stderr = run(
        [sys.executable, "-u", SCRIPT, "--backend", "real", "--allow-fallback",
         "--out", os.path.join(HERE, "results", "_test_real_fb.json")],
        env=env_no_key,  # 同样没 Key
    )
    check("带 --allow-fallback 退出码 = 0", rc == 0, f"got {rc}")
    with open(os.path.join(HERE, "results", "_test_real_fb.json"), "r", encoding="utf-8") as f:
        report_fb = json.load(f)
    real_cases_fb = [c for c in report_fb["cases"] if c["mock_type"] == "real"]
    for c in real_cases_fb:
        check(f"allow-fallback real case → data_source=mock_fallback",
              c["data_source"] == "mock_fallback",
              f"{c['case_id']}: {c['data_source']}")

    # ---------- Test 5: JSON 字段完整性 ----------
    print("\n[4] 输出 JSON 可读取且字段完整")
    required_top = ["summary", "cases", "generated_at", "backend"]
    for k in required_top:
        check(f"顶层字段 '{k}' 存在", k in report, f"missing {k}")

    req_case = ["case_id", "execution_status", "policy_status",
                "expectation_status", "data_source", "latency_ms",
                "fact_warning_count", "tokens", "error"]
    for c in report["cases"]:
        for k in req_case:
            check(f"case {c['case_id']} 字段 '{k}' 存在", k in c,
                  f"missing {k}")
        break  # 只查一条

    # concept_misuse 必须 supported=false, count=null
    vc = report["summary"]["violation_counts"]
    check("concept_misuse supported=false",
          vc.get("concept_misuse", {}).get("supported") is False)
    check("concept_misuse count=null",
          vc.get("concept_misuse", {}).get("count") is None)

    # summary 统计字段
    req_summary = ["total_cases", "execution_success", "execution_failed",
                   "violation_counts", "data_source_breakdown",
                   "init_warmup_ms"]
    for k in req_summary:
        check(f"summary 字段 '{k}' 存在", k in report["summary"],
              f"missing {k}")

    # ---------- 汇总 ----------
    print("\n" + "=" * 60)
    print(f"结果: {PASS} 通过 / {FAIL} 失败")
    print("=" * 60)
    sys.exit(0 if FAIL == 0 else 1)


if __name__ == "__main__":
    main()

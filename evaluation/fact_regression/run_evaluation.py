"""run_evaluation.py - 事实边界回归评测（可信度重构版）

设计目标：结果能区分"程序执行成功"、"质量规则通过"、"符合预期"三层含义，
并防止 Mock 结果冒充真实模型结果。

核心改进：
1. Mock 拆为 clean / adversarial 两类，分别用于验证"不误报"和"能检出"
2. 三状态 per case：execution_status / policy_status / expectation_status
3. data_source 明确标记 real / mock_clean / mock_adversarial / mock_fallback
4. --backend real 默认 Provider 未配置时失败；显式 --allow-fallback 才允许降级
5. concept_misuse 无检测器 → null + supported=false，不伪造 0
6. 首轮 warm-up 分离 RAG embedding 初始化耗时（约 26s）与真实 case 耗时

用法：
    python ...run_evaluation.py                               # 默认 real
    python ...run_evaluation.py --backend mock               # mock（含 clean + adversarial）
    python ...run_evaluation.py --backend real --allow-fallback
"""
import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone

# ------------------------------------------------------------------
# 路径
# ------------------------------------------------------------------
HERE = os.path.dirname(os.path.abspath(__file__))        # evaluation/fact_regression
EVAL_DIR = os.path.dirname(HERE)                         # evaluation/
PROJECT_ROOT = os.path.dirname(EVAL_DIR)                 # 项目根
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")      # 项目根/backend

# ------------------------------------------------------------------
# 加载 .env（必须在导入业务模块之前，否则 llm_service 读不到 Key）
# ------------------------------------------------------------------
def _load_dotenv():
    for env_file in (os.path.join(BACKEND_DIR, ".env"), os.path.join(PROJECT_ROOT, ".env")):
        if not os.path.isfile(env_file):
            continue
        for raw in open(env_file, encoding="utf-8").read().splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))

_load_dotenv()

sys.path.insert(0, BACKEND_DIR)
sys.path.insert(0, EVAL_DIR)

DATASET = os.path.join(HERE, "dataset.json")
RESULTS_DIR = os.path.join(HERE, "results")
LATEST_OUT = os.path.join(RESULTS_DIR, "latest.json")

# ------------------------------------------------------------------
# 业务模块
# ------------------------------------------------------------------
from api import analyze as analyze_mod  # noqa: E402
from services import llm_service        # noqa: E402
from services import fact_check         # noqa: E402

# ------------------------------------------------------------------
# Token 采集（运行时包裹，不改业务代码）
# ------------------------------------------------------------------
USAGE = {"prompt": 0, "completion": 0, "total": 0, "calls": 0}
_orig_log_tokens = llm_service.LLMService._log_tokens


def _capturing_log_tokens(self, usage):
    _orig_log_tokens(usage)
    if not usage:
        return
    if "prompt_tokens" in usage or "completion_tokens" in usage:
        USAGE["prompt"] += usage.get("prompt_tokens") or 0
        USAGE["completion"] += usage.get("completion_tokens") or 0
        USAGE["total"] += usage.get("total_tokens") or 0
    else:
        USAGE["prompt"] += usage.get("input_count") or 0
        USAGE["completion"] += usage.get("output_count") or 0
        USAGE["total"] += usage.get("token_count") or 0
    USAGE["calls"] += 1


llm_service.LLMService._log_tokens = _capturing_log_tokens


def reset_usage():
    USAGE.update({"prompt": 0, "completion": 0, "total": 0, "calls": 0})

# ------------------------------------------------------------------
# fact_warning 文本 → 6 类分类（仅覆盖有规则检测器的 5 类）
# ------------------------------------------------------------------
# concept_misuse 无规则检测器，不会出现在 fact_warning 中
# theoretical_to_practical 通过 evidence_grade C/D/E 触发
_WARN_TO_CATEGORY = [
    ("疑似新增技术", "fact_invention"),
    ("original未在简历原文中找到", "fact_invention"),
    ("疑似新增数字指标", "fake_metric"),
    ("疑似新增量化表述", "fake_metric"),
    ("疑似措辞升级", "skill_upgrade"),
    ("疑似未经证实的项目级描述", "project_level_upgrade"),
    ("evidence_grade为C/D/E", "theoretical_to_practical"),
]

# 有规则检测器的 5 类（concept_misuse 不在其中）
SUPPORTED_VIOLATION_TYPES = [
    "fact_invention",
    "fake_metric",
    "skill_upgrade",
    "project_level_upgrade",
    "theoretical_to_practical",
]

UNSUPPORTED_VIOLATION_TYPES = ["concept_misuse"]


def classify_warning(warn_text):
    """拆分 fact_warning 文本并分类。返回 list[category]。"""
    cats = []
    for segment in str(warn_text or "").split("；"):
        seg = segment.strip()
        if not seg:
            continue
        matched = None
        for keyword, cat in _WARN_TO_CATEGORY:
            if keyword in seg:
                matched = cat
                break
        cats.append(matched or "unknown")
    return cats

# ------------------------------------------------------------------
# Mock Backend（仅用于评测器内部测试，不依赖外部 MockBackend）
# 网络请求数 = 0（函数返回固定 JSON 字符串）
# ------------------------------------------------------------------
class FactRegressionMock:
    """为评测器内部测试提供 mock LLM 响应。

    根据 case["mock_type"] 和 case["_mock_scenario"] 返回对应 rewrite_suggestions，
    使 fact_check 能跑出预期结果。

    real / clean / adversarial 三种 mock_type 行为：
      - real: 返回基于真实简历片段的 suggestions（让 Workflow 跑通 + evidence 能挂接）
      - clean: 返回不触发 fact_check 的合法 suggestions
      - adversarial: 返回故意触发特定违规类型的 suggestions
    """

    # 从简历原文摘录的稳定片段（用于 real case 的默认 suggestion original）
    _RESUME_EXCERPT = None

    def __init__(self, provider="mock", resume_excerpt=None):
        self.provider = provider
        self.case = None
        self.idx = -1
        if resume_excerpt:
            FactRegressionMock._RESUME_EXCERPT = resume_excerpt

    def begin(self, case, idx):
        self.case = case
        self.idx = idx

    def is_configured(self):
        return True

    def get_provider(self):
        return self.provider

    def chat(self, prompt):
        """LLMService.chat 的 mock —— 从 prompt 内容识别当前调用场景，返回对应结构。

        必须按**更具体→更模糊**顺序判断，因为下游 prompt 会包含上游返回的 JSON 字段
        （如 match prompt 里包含 {"岗位职责": ...}，会误伤 JD 条件）。
        """
        mt = self.case.get("mock_type") if self.case else "real"
        p = str(prompt)

        # ---- 识别 LangChain agent（按具体度排序！）----
        # Optimize: 含 "rewrite_suggestions" 或 "优化建议专家"
        if "rewrite_suggestions" in p or "简历优化建议专家" in p:
            return self._mock_optimize(mt)

        # Match: "简历与岗位匹配度评估专家"（比 JD 多一个"与"字，区分开）
        if "简历与岗位匹配度评估专家" in p:
            return self._mock_match()

        # Resume: 只有简历分析有 "简历分析专家" + 简历内容（简历原文不出现"岗位职责"JSON）
        # 放在 JD 之前，因为 JD prompt 里没有 "简历分析专家"
        if "简历分析专家" in p:
            return self._mock_resume()

        # JD: 最模糊（被下游 prompt 引用，所以放最后）
        if "岗位JD分析专家" in p:
            return self._mock_jd()

        # ---- 单 Prompt 降级路径 ----
        if mt == "real":
            excerpt = FactRegressionMock._RESUME_EXCERPT or "基于 FastAPI 开发后台业务接口"
            return json.dumps({
                "match_level": {"overall": "中等", "ability": "中等",
                                "experience": "中等", "risk": "需要优化"},
                "analysis_basis": [{"dimension": "综合匹配度",
                                     "items": [{"type": "match", "content": "Python", "quote": "原文", "match_degree": "高"}]}],
                "strengths": ["AI应用开发经验"],
                "weaknesses": ["多模态经验缺失"],
                "rewrite_suggestions": [{
                    "original": excerpt,
                    "revised": excerpt,
                    "basis": "简历原文与 JD 要求结合，等价改写",
                    "evidence_grade": "A",
                }],
                "optimization_advice": {"highlight": ["突出技能"], "supplement": ["补充缺口"], "expression": ["优化表达"]},
            }, ensure_ascii=False)

        # 兜底：clean/adversarial 降级路径也返回完整结构
        return json.dumps({
            "match_level": {"overall": "中等", "ability": "中等",
                            "experience": "中等", "risk": "需要优化"},
            "analysis_basis": [],
            "strengths": [], "weaknesses": [],
            "rewrite_suggestions": [],
            "optimization_advice": {"highlight": [], "supplement": [], "expression": []},
        }, ensure_ascii=False)

    # ---- Agent-specific mock responses ----
    def _mock_jd(self):
        return json.dumps({
            "岗位职责": "岗位职责描述",
            "核心技能": ["Python"],
            "技术要求": ["Python", "Docker"],
            "岗位关键词": ["Python", "后端"],
        }, ensure_ascii=False)

    def _mock_resume(self):
        return json.dumps({
            "技术栈": ["Python", "FastAPI", "SQLAlchemy"],
            "项目经历": [{"项目名": "测试项目", "职责": "开发", "技术点": "Python"}],
            "优势": ["技术匹配"],
            "不足": ["经验有限"],
        }, ensure_ascii=False)

    def _mock_match(self):
        return json.dumps({
            "match_level": {
                "overall": "中等", "ability": "中等",
                "experience": "中等", "risk": "需要优化",
            },
            "analysis_basis": [{"dimension": "综合匹配度",
                                 "items": [{"type": "match", "content": "Python", "quote": "原文", "match_degree": "高"}]}],
            "strengths": ["Python 匹配"],
            "weaknesses": ["经验不足"],
        }, ensure_ascii=False)

    def _mock_optimize(self, mt):
        scenario = self.case.get("_mock_scenario", {}) if self.case else {}
        sug_list = scenario.get("rewrite_suggestions")
        if sug_list:
            suggestions = sug_list
        elif mt == "real":
            excerpt = FactRegressionMock._RESUME_EXCERPT or "基于 FastAPI 开发后台业务接口"
            suggestions = [{
                "original": excerpt, "revised": excerpt,
                "basis": "简历原文与 JD 要求结合", "evidence_grade": "A",
            }]
        elif mt == "clean":
            excerpt = FactRegressionMock._RESUME_EXCERPT or "基于 FastAPI 开发后台业务接口"
            suggestions = [{
                "original": excerpt, "revised": excerpt,
                "basis": "简历原文与 JD 要求结合，等价改写", "evidence_grade": "A",
            }]
        else:
            suggestions = []
        return json.dumps({
            "rewrite_suggestions": suggestions,
            "optimization_advice": {
                "highlight": ["突出技能"], "supplement": ["补充缺口"], "expression": ["优化表达"],
            },
        }, ensure_ascii=False)

    def run_agent(self, agent_name, prompt):
        """Workflow 路径 → 返回各 Agent 的 mock 输出。"""
        mt = self.case.get("mock_type") if self.case else "real"
        if "JD分析" in agent_name:
            return {
                "岗位职责": "岗位职责描述",
                "核心技能": ["Python"],
                "技术要求": ["Python"],
                "岗位关键词": ["Python"],
            }
        elif "简历分析" in agent_name:
            return {
                "技术栈": ["Python", "FastAPI"],
                "项目经历": [{"项目名": "测试项目", "职责": "开发", "技术点": "Python"}],
                "优势": ["技术匹配"],
                "不足": ["经验有限"],
            }
        elif "匹配评估" in agent_name:
            return {
                "match_level": {
                    "overall": "中等", "ability": "中等",
                    "experience": "中等", "risk": "需要优化",
                },
                "analysis_basis": [{"dimension": "综合匹配度",
                                     "items": [{"type": "match", "content": "Python", "quote": "原文", "match_degree": "高"}]}],
                "strengths": ["Python 匹配"],
                "weaknesses": ["经验不足"],
            }
        elif "优化建议" in agent_name:
            scenario = self.case.get("_mock_scenario", {}) if self.case else {}
            sug_list = scenario.get("rewrite_suggestions")
            if sug_list:
                suggestions = sug_list
            elif mt == "real":
                # real case 默认 suggestion：original 必须来自简历原文，让 evidence 能正确挂接
                excerpt = FactRegressionMock._RESUME_EXCERPT or "基于 FastAPI 开发后台业务接口"
                suggestions = [{
                    "original": excerpt,
                    "revised": excerpt,  # 等价改写
                    "basis": "简历原文与 JD 要求结合",
                    "evidence_grade": "A",
                }]
            else:
                suggestions = [{
                    "original": "原文片段",
                    "revised": "优化后表达",
                    "basis": "简历原文与 JD 要求结合",
                    "evidence_grade": "A",
                }]
            return {
                "rewrite_suggestions": suggestions,
                "optimization_advice": {
                    "highlight": ["突出技能"],
                    "supplement": ["补充缺口"],
                    "expression": ["优化表达"],
                },
            }
        return {}


# ------------------------------------------------------------------
# LLM Backend patch
# ------------------------------------------------------------------
def patch_for_mock(mock_backend):
    """把 mock backend 挂到 llm_service 模块级函数上。"""
    llm_service.is_configured = lambda: mock_backend.is_configured()
    llm_service.get_provider = lambda: mock_backend.get_provider()
    llm_service.chat = lambda prompt: mock_backend.chat(prompt)
    llm_service.run_agent = lambda name, prompt: mock_backend.run_agent(name, prompt)


def restore_real():
    """还原 llm_service 的真实模块级函数。"""
    from services import llm_service as _ls
    _orig = _ls.LLMService
    def _is_configured():
        return _orig().is_configured()
    def _get_provider():
        return _orig().provider
    def _chat(prompt):
        return _orig().chat(prompt)
    def _run_agent(name, prompt):
        return _orig().run_agent(name, prompt)
    llm_service.is_configured = _is_configured
    llm_service.get_provider = _get_provider
    llm_service.chat = _chat
    llm_service.run_agent = _run_agent

# ------------------------------------------------------------------
# Provider 检查（run 前调用）
# ------------------------------------------------------------------
def check_real_provider():
    """返回 (configured: bool, reason: str)。不改业务代码，只查 llm_service。"""
    try:
        configured = llm_service.is_configured()
    except Exception as e:
        return False, f"is_configured() 异常: {e}"
    if not configured:
        return False, "Provider 未配置（检查 .env 中的 LLM_PROVIDER 和对应 API Key）"
    try:
        provider = llm_service.get_provider()
    except Exception as e:
        return False, f"get_provider() 异常: {e}"
    return True, f"Provider={provider}"


# ------------------------------------------------------------------
# data_source 规范化
# ------------------------------------------------------------------
def normalize_data_source(raw_source, backend_type, mock_type):
    """把 result["data_source"] + backend_type + mock_type → 规范化 data_source。

    优先级：
      1. backend_type == "mock" 且 mock_type 是 clean/adversarial → 用 mock_clean / mock_adversarial
      2. backend_type == "mock" 且 mock_type 是 real：
         - result 里的 data_source 是 llm_api / agent_workflow → 说明 Workflow 跑通了（Mock 正确返回 schema）
           → 标记为 mock_passthrough（Mock backend 下通过了真实业务链路）
         - result 里的 data_source 是 mock_fallback → 真的降级了 → 标记 mock_fallback
      3. backend_type == "real" → 直接用 result 里的 data_source
    """
    if backend_type == "mock":
        if mock_type == "clean":
            return "mock_clean"
        if mock_type == "adversarial":
            return "mock_adversarial"
        # mock_type == "real"（真实 JD 用 Mock backend 跑）
        # 不应该一概当作 fallback，要看 result 里实际走了哪条链路
        if raw_source and raw_source != "mock_fallback":
            # Workflow 或单 Prompt 跑通了（Mock 返回了符合 schema 的数据）
            return "mock_passthrough"
        # 真的降级了
        return "mock_fallback"
    # backend_type == "real"
    return raw_source or "unknown"

# ------------------------------------------------------------------
# 主循环
# ------------------------------------------------------------------
def run_cases(backend_type, allow_fallback=False, verbose=False):
    with open(DATASET, "r", encoding="utf-8") as f:
        dataset = json.load(f)

    resume = dataset["resume"]
    cases = dataset["cases"]

    init_time_ms = 0.0
    mock_backend = None

    # ---------- 准备 mock ----------
    if backend_type == "mock":
        # 从简历原文提取一个稳定片段供 Mock 默认 suggestion 使用
        import re
        # 取第一段有效描述（优先项目经历里的长句）
        paragraphs = [p.strip() for p in re.split(r"\n\s*\n", resume) if len(p.strip()) >= 10]
        excerpt = None
        for p in paragraphs:
            for line in re.split(r"\n", p):
                if len(line.strip()) >= 20:
                    excerpt = line.strip()
                    break
            if excerpt:
                break
        if not excerpt:
            # fallback
            for line in [l.strip() for l in resume.split("\n") if len(l.strip()) >= 20]:
                excerpt = line
                break
        print(f"[mock] resume_excerpt: {excerpt[:60] if excerpt else '(none)'}...")
        mock_backend = FactRegressionMock(resume_excerpt=excerpt)
        patch_for_mock(mock_backend)
    else:
        # real：检查 provider
        configured, reason = check_real_provider()
        if not configured:
            if allow_fallback:
                print(f"[WARN] {reason} --allow-fallback 已开启，将继续执行并标记 data_source=mock_fallback")
            else:
                print(f"[FAIL] {reason}（未传 --allow-fallback，终止）")
                sys.exit(2)

    # ---------- Warm-up：一次 dummy 调用，分离 RAG 初始化耗时 ----------
    warm_up_result = None
    if backend_type == "mock" or check_real_provider()[0]:
        t_w0 = time.perf_counter()
        try:
            warm_up_result = analyze_mod.analyze_resume(resume, "这是一个仅用于初始化的测试 JD")
        except Exception as e:
            print(f"[WARN] warm-up 调用失败（不影响主流程）: {e}")
        init_time_ms = round((time.perf_counter() - t_w0) * 1000, 2)
        print(f"[init] warm-up 完成，耗时 {init_time_ms} ms（包含 RAG embedding 加载 + FAISS 索引构建）")

    # ---------- 主循环 ----------
    results = []
    per_case_latencies = []
    total_warnings = 0
    violation_case_count = 0
    expectation_pass_count = 0

    # 违规计数（仅有检测器的 5 类 + unknown）
    violation_counts = {t: 0 for t in SUPPORTED_VIOLATION_TYPES}
    violation_counts["unknown"] = 0
    # concept_misuse 单独标记 supported=false
    violation_support = {t: True for t in SUPPORTED_VIOLATION_TYPES}
    violation_support["concept_misuse"] = False

    for idx, case in enumerate(cases):
        case_id = case["id"]
        title = case["title"]
        mock_type = case.get("mock_type", "real")
        expected_violations = case.get("expected_violations")  # adversarial 有

        if mock_backend is not None:
            mock_backend.begin(case, idx)

        t0 = time.perf_counter()
        execution_ok = False
        policy_violated = False  # True = 检出违规
        expectation_met = None   # True/False/None（只对有 expected_violations 的 case 计算）
        data_source = "unknown"
        fact_check_result = None
        fact_warnings_list = []
        grade_dist = {"a": 0, "b": 0, "c": 0, "d": 0, "e": 0, "missing": 0}
        suggestion_count = 0
        err_msg = None
        tokens = None

        reset_usage()
        try:
            result = analyze_mod.analyze_resume(resume, case["jd"])

            if isinstance(result, dict):
                execution_ok = True
                raw_source = result.get("data_source") or "unknown"
                data_source = normalize_data_source(raw_source, backend_type, mock_type)
                fact_check_result = result.get("fact_check") or {"checked": 0, "flagged": 0, "violations": 0}

                suggestions = result.get("rewrite_suggestions") or []
                suggestion_count = len(suggestions) if isinstance(suggestions, list) else 0

                for sug in suggestions if isinstance(suggestions, list) else []:
                    if not isinstance(sug, dict):
                        continue
                    g = (sug.get("evidence_grade") or "missing").strip().lower()
                    if g not in grade_dist:
                        grade_dist[g] = 0
                    grade_dist[g] += 1
                    w = sug.get("fact_warning")
                    if w:
                        cats = classify_warning(w)
                        fact_warnings_list.append({
                            "original": sug.get("original"),
                            "revised": sug.get("revised"),
                            "evidence_grade": sug.get("evidence_grade"),
                            "fact_warning": w,
                            "categories": cats,
                        })
                        for c in cats:
                            if c in violation_counts:
                                violation_counts[c] += 1
                            elif c != "unknown":
                                violation_counts["unknown"] += 1
            else:
                err_msg = f"result 类型异常: {type(result).__name__}"

        except Exception as e:
            err_msg = f"{type(e).__name__}: {e}"

        latency_ms = round((time.perf_counter() - t0) * 1000, 2)
        per_case_latencies.append(latency_ms)

        if USAGE["calls"] > 0:
            tokens = {
                "prompt": USAGE["prompt"],
                "completion": USAGE["completion"],
                "total": USAGE["total"],
                "calls": USAGE["calls"],
            }

        # policy_status：有任何 fact_warning → 违规
        policy_violated = len(fact_warnings_list) > 0

        # expectation_status：仅对有 expected_violations 的 case 计算
        if expected_violations is not None:
            actual_violations = set()
            for fw in fact_warnings_list:
                for cat in fw["categories"]:
                    if cat in SUPPORTED_VIOLATION_TYPES:
                        actual_violations.add(cat)
            expected_set = set(expected_violations)
            expectation_met = (expected_set == actual_violations)

        # 构建三状态
        execution_status = "success" if execution_ok else "failed"
        policy_status = "violations_detected" if policy_violated else "all_clear"
        if expectation_met is True:
            expectation_status = "met"
        elif expectation_met is False:
            expectation_status = "not_met"
        else:
            expectation_status = "not_applicable"

        case_row = {
            "case_id": case_id,
            "title": title,
            "mock_type": mock_type,
            "execution_status": execution_status,
            "policy_status": policy_status,
            "expectation_status": expectation_status,
            "latency_ms": latency_ms,
            "data_source": data_source,
            "rewrite_suggestion_count": suggestion_count,
            "evidence_grade_distribution": grade_dist,
            "fact_check": fact_check_result,
            "fact_warnings": fact_warnings_list,
            "fact_warning_count": len(fact_warnings_list),
            "expected_violations": expected_violations,
            "tokens": tokens,
            "error": err_msg,
        }
        results.append(case_row)

        total_warnings += len(fact_warnings_list)
        if policy_violated:
            violation_case_count += 1
        if expectation_met is True:
            expectation_pass_count += 1

        print(f"[{idx + 1}/{len(cases)}] {case_id:20s} "
              f"exec={execution_status:6s} policy={policy_status:18s} "
              f"expect={expectation_status:14s} src={data_source:16s} "
              f"lat={latency_ms}ms")

    if mock_backend is not None:
        restore_real()

    # 构造 summary
    support_map = {}
    for t in SUPPORTED_VIOLATION_TYPES:
        support_map[t] = {"count": violation_counts[t], "supported": True}
    for t in UNSUPPORTED_VIOLATION_TYPES:
        support_map[t] = {"count": None, "supported": False}

    summary = {
        "total_cases": len(cases),
        "execution_success": sum(1 for r in results if r["execution_status"] == "success"),
        "execution_failed": sum(1 for r in results if r["execution_status"] == "failed"),
        "policy_violation_cases": violation_case_count,
        "policy_clean_cases": sum(1 for r in results if r["policy_status"] == "all_clear"),
        "expectation_met": expectation_pass_count,
        "expectation_total": sum(1 for r in results if r["expectation_status"] != "not_applicable"),
        "avg_latency_ms": round(sum(per_case_latencies) / len(per_case_latencies), 2) if per_case_latencies else 0,
        "min_latency_ms": round(min(per_case_latencies), 2) if per_case_latencies else 0,
        "max_latency_ms": round(max(per_case_latencies), 2) if per_case_latencies else 0,
        "init_warmup_ms": init_time_ms,
        "fact_warning_total": total_warnings,
        "data_source_breakdown": _count_field(results, "data_source"),
        "violation_counts": support_map,
    }

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "dataset": "evaluation/fact_regression/dataset.json",
        "dataset_version": dataset.get("version", "unknown"),
        "backend": backend_type,
        "allow_fallback": bool(allow_fallback),
        "note": "concept_misuse 无规则检测器（supported=false），不在本评测范围",
        "summary": summary,
        "cases": results,
    }


def _count_field(results, field):
    from collections import Counter
    c = Counter(r[field] for r in results)
    return dict(c)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--backend", choices=["mock", "real"], default="real")
    ap.add_argument("--allow-fallback", action="store_true",
                    help="real backend 在 Provider 未配置时允许降级到 mock_fallback（默认会终止）")
    ap.add_argument("--out", default=LATEST_OUT)
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args()

    os.makedirs(os.path.dirname(args.out), exist_ok=True)

    if args.backend == "real" and not args.allow_fallback:
        configured, reason = check_real_provider()
        if not configured:
            print(f"[FAIL] {reason}（未传 --allow-fallback，终止）")
            sys.exit(2)

    report = run_cases(args.backend, allow_fallback=args.allow_fallback, verbose=args.verbose)

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    s = report["summary"]
    print("\n" + "=" * 60)
    print(f"评测完成 | backend={args.backend} | allow-fallback={args.allow_fallback} | 输出={args.out}")
    print(f"  init:     warm-up {s['init_warmup_ms']} ms（首次 RAG embedding 加载 + FAISS 构建）")
    print(f"  cases:    {s['execution_success']}/{s['total_cases']} 执行成功")
    print(f"  policy:   {s['policy_clean_cases']} clean / {s['policy_violation_cases']} violations")
    print(f"  expect:   {s['expectation_met']}/{s['expectation_total']} 符合预期")
    print(f"  latency:  avg={s['avg_latency_ms']}ms  min={s['min_latency_ms']}ms  max={s['max_latency_ms']}ms")
    print(f"  data_src: {s['data_source_breakdown']}")
    vc = s["violation_counts"]
    print(f"  violations:")
    for t, info in vc.items():
        if info["supported"]:
            print(f"    {t}: {info['count']}")
        else:
            print(f"    {t}: (unsupported, 无规则检测器)")


if __name__ == "__main__":
    main()

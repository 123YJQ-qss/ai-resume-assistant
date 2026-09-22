"""metrics.py - 评测指标计算（纯函数，可复现）。

指标定义：
1. keyword_match     岗位关键词匹配准确性：模型识别的技能集合 vs 人工标注 expected_skills。
2. skill_recognition 技能识别准确性：同上（基于 JD 分析 Agent 输出的技术栈/关键词）。
   备注：二者都依赖"可结构化提取的技能列表"，仅在 Improved（JD 分析 Agent）侧可直接计算；
          Baseline（单 Prompt）无独立技能字段，计算时标记为 N/A。
3. field_completeness 输出字段完整率：必需字段是否齐全且非空。
4. json_parse_success JSON 解析成功率：解析器能否从文本中成功提取 JSON。
5. suggestion_executability 建议可执行性（结构代理）：改写建议是否同时具备 original/revised/basis。
6. workflow_success   Workflow 执行成功率：流程是否无异常完成。
7. avg_response_time  平均响应时间（ms）。
8. token_consumption  真实 API usage（prompt/completion/total tokens），由 LLM 响应 usage 字段采集；
   早期版本的 chars/2 估算已废弃。

补充指标（P0-1 / P0-2）：
- gap_precision / gap_recall / gap_f1   缺口识别：模型输出的不足/缺口 vs expected_gaps 集合比对。
- match_strict    match_level 4 字段严格字符串相等（保留原口径，未删除）。
- match_graded    match_level 分级得分：相同=1，相邻等级=0.5，相差两级=0，4 字段平均。
- match_overall   仅 overall 字段的严格一致（0/1）。
"""
import re

REQUIRED_TOP_FIELDS = [
    "match_level", "analysis_basis", "strengths",
    "weaknesses", "rewrite_suggestions", "optimization_advice",
]
MATCH_LEVEL_KEYS = ["overall", "ability", "experience", "risk"]
ADVICE_KEYS = ["highlight", "supplement", "expression"]

_RISKY_KEYS = {"ability", "experience", "risk"}


def _norm(s):
    return str(s or "").strip().lower()


def set_f1(predicted, expected):
    """预测集合 vs 期望集合的 precision/recall/F1。"""
    pred = set(_norm(x) for x in (predicted or []) if _norm(x))
    exp = set(_norm(x) for x in (expected or []) if _norm(x))
    if not exp:
        return {"precision": 0.0, "recall": 0.0, "f1": 0.0, "tp": 0, "fp": 0, "fn": 0}
    tp = len(pred & exp)
    fp = len(pred - exp)
    fn = len(exp - pred)
    precision = tp / len(pred) if pred else 0.0
    recall = tp / len(exp) if exp else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    return {"precision": precision, "recall": recall, "f1": f1, "tp": tp, "fp": fp, "fn": fn}


def extract_skills_from_jd_analysis(jd_analysis):
    """从 JD 分析 Agent 输出中提取技能/关键词列表。"""
    out = []
    if not isinstance(jd_analysis, dict):
        return out
    for key in ("核心技能", "技术要求", "岗位关键词"):
        v = jd_analysis.get(key)
        if isinstance(v, list):
            for item in v:
                if isinstance(item, str) and item.strip():
                    out.append(item.strip())
    return out


def field_completeness(result):
    """返回 0~1：必需字段齐全且非空的比例。"""
    if not isinstance(result, dict):
        return 0.0
    checks = []
    ml = result.get("match_level") or {}
    for k in MATCH_LEVEL_KEYS:
        checks.append(bool(_norm(ml.get(k))))

    for field in ("analysis_basis", "strengths", "weaknesses", "rewrite_suggestions"):
        v = result.get(field)
        checks.append(bool(isinstance(v, list) and len(v) > 0))

    advice = result.get("optimization_advice") or {}
    for k in ADVICE_KEYS:
        v = advice.get(k)
        checks.append(bool(isinstance(v, list) and len(v) > 0))

    return sum(checks) / len(checks) if checks else 0.0


def suggestion_executability(result):
    """结构代理：rewrite_suggestions 中 original/revised/basis 均非空的比例。"""
    items = result.get("rewrite_suggestions") if isinstance(result, dict) else None
    if not isinstance(items, list) or not items:
        return 0.0
    ok = 0
    for it in items:
        if not isinstance(it, dict):
            continue
        if it.get("original") and it.get("revised") and it.get("basis"):
            ok += 1
    return ok / len(items)


def match_level_accuracy(pred_match, exp_match):
    """预测 match_level 与人工标注在 4 个子字段上的精确一致率（strict，保留原口径）。"""
    if not isinstance(pred_match, dict) or not isinstance(exp_match, dict):
        return 0.0
    correct = 0
    for k in MATCH_LEVEL_KEYS:
        if _norm(pred_match.get(k)) == _norm(exp_match.get(k)):
            correct += 1
    return correct / len(MATCH_LEVEL_KEYS)


# ---------------- P0-2：match_level 分级评测（不覆盖 strict） ----------------

# 有序等级映射：数值越大越好
MATCH_LEVEL_ORDER = {
    "overall": {"较低": 0, "中等": 1, "较高": 2},
    "ability": {"较弱": 0, "中等": 1, "较强": 2},
    "experience": {"较弱": 0, "中等": 1, "较强": 2},
    "risk": {"风险较高": 0, "需要优化": 1, "风险较低": 2},
}


def match_level_graded(pred_match, exp_match):
    """分级得分：相同=1 分，相邻等级=0.5 分，相差两级=0 分；4 个字段取平均。

    - 标注取值不在有序表中的字段跳过（不计分母）；
    - 模型输出取值无法映射（如"待评估"）该字段记 0 分。
    """
    if not isinstance(pred_match, dict) or not isinstance(exp_match, dict):
        return 0.0
    total = 0.0
    denom = 0
    for k, order in MATCH_LEVEL_ORDER.items():
        ev = order.get(_norm(exp_match.get(k)))
        if ev is None:
            continue
        denom += 1
        pv = order.get(_norm(pred_match.get(k)))
        if pv is None:
            continue
        total += 1.0 if pv == ev else (0.5 if abs(pv - ev) == 1 else 0.0)
    return total / denom if denom else 0.0


def match_level_overall(pred_match, exp_match):
    """仅 overall 字段的严格一致（0/1）。"""
    if not isinstance(pred_match, dict) or not isinstance(exp_match, dict):
        return 0.0
    return 1.0 if _norm(pred_match.get("overall")) == _norm(exp_match.get("overall")) else 0.0


# ---------------- P0-1：gap 识别指标 ----------------

_PUNCT_RE = re.compile(r"[\s，。、；：,.;:()（）\[\]【】\"'`~!？?！·—\-_]")


def _norm_text(s):
    """基础归一化：小写 + 去空白与常见中英文标点。"""
    return _PUNCT_RE.sub("", str(s or "").strip().lower())


def extract_gap_texts(result):
    """从模型输出中收集"缺口/不足"描述文本：
    weaknesses 列表 + analysis_basis 中 type=gap 的 content。
    """
    texts = []
    if not isinstance(result, dict):
        return texts
    for w in result.get("weaknesses") or []:
        if isinstance(w, str) and w.strip():
            texts.append(w)
    for dim in result.get("analysis_basis") or []:
        if not isinstance(dim, dict):
            continue
        for item in dim.get("items") or []:
            if isinstance(item, dict) and _norm(item.get("type")) == "gap":
                c = item.get("content")
                if isinstance(c, str) and c.strip():
                    texts.append(c)
    return texts


def gap_f1(predicted_texts, expected_gaps):
    """缺口识别 precision / recall / F1。

    匹配规则（归一化后双向包含）：
    - 预测文本与期望 gap 归一化后相等或互为子串 → 该预测"命中"该 gap；
    - TP = 命中至少一个期望 gap 的预测文本数
    - FP = 未命中任何期望 gap 的预测文本数
    - FN = 未被任何预测文本命中的期望 gap 数
    无真实可比数据时返回 None（聚合时自动剔除，报告中显示 N/A）。
    """
    pred = [_norm_text(t) for t in (predicted_texts or []) if _norm_text(t)]
    exp = [_norm_text(g) for g in (expected_gaps or []) if _norm_text(g)]

    if not exp and not pred:
        return {"precision": None, "recall": None, "f1": None}
    if not exp:  # 不应有缺口，却预测了缺口 → 全部为 FP
        return {"precision": 0.0, "recall": None, "f1": None}

    hits_exp = set()
    tp = 0
    for p in pred:
        matched = False
        for j, e in enumerate(exp):
            if p == e or p in e or e in p:
                matched = True
                hits_exp.add(j)
        if matched:
            tp += 1
    fp = len(pred) - tp
    fn = len(exp) - len(hits_exp)

    precision = tp / len(pred) if pred else None
    recall = len(hits_exp) / len(exp)  # 被覆盖的期望gap数 / 期望gap总数（保证 ≤ 1）
    if precision is None or (precision + recall) == 0:
        f1 = None if precision is None else 0.0
    else:
        f1 = 2 * precision * recall / (precision + recall)
    return {"precision": precision, "recall": recall, "f1": f1}


def aggregate(numbers):
    arr = [float(x) for x in numbers if x is not None]
    if not arr:
        return {"mean": 0.0, "count": 0}
    return {"mean": round(sum(arr) / len(arr), 4), "count": len(arr)}
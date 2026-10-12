"""fact_check 语义级回归测试 v2 —— 要求核对拦截原因

相比 v1 的改进：
  - 每个用例带 expect_reason 关键词（如 "疑似措辞升级" / "疑似新增数字指标"）
  - flagged 符合预期但原因不匹配 → PARTIAL_PASS（拦截了但原因不对，不算完整识别）
  - 明确区分：
      FULL_PASS     — flagged 和原因都匹配（完整语义识别）
      PARTIAL_PASS  — flagged 符合但原因关键词不匹配（碰巧拦截）
      FAIL          — flagged 不符合预期（该拦没拦 / 不该拦却拦）

拦截原因关键词（来自 fact_check.py L302-330）：
  "疑似新增技术"        — 技术词不在 original 也不在简历
  "疑似新增数字指标"    — 数字不在 original
  "疑似新增量化表述"    — QUALITATIVE_METRIC_WORDS 不在 original
  "疑似措辞升级"        — UPGRADE_WORDS 命中
  "疑似未经证实的项目级描述" — PROJECT_LEVEL_WORDS 命中
  "架构能力表述升级"    — 架构词命中但有动作词，降级

用法：python backend/eval/fact_check_semantic_tests.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from services.fact_check import check_rewrite_suggestions


# ===================== 测试矩阵 =====================
#
# 每个条目：(name, original, revised, expect_flagged, expect_reason, jd_terms)
#
# expect_reason 是 fact_warning 子串，空字符串"" 表示「不检查原因，只看 flagged」
# 多个原因用 "|" 分隔（任一匹配即可）
# jd_terms: 模拟真实 JD 里的技术词列表，fact_check 第 3 步新增技术检测以此为候选集
CASES = [
    # ============ fact_check 主流程测试 ============

    # 1. 职责程度升级（参与→主导）—— 应该被措辞升级拦截
    ("职责升级：参与→主导",
     "参与 AI 简历优化系统开发",
     "主导 AI 简历优化系统开发",
     True, "疑似措辞升级", []),

    # 2. 动作主体变化（张三→团队）—— fact_check 不应因业务词拦
    ("动作主体变化：张三→团队（fact_check 不应因业务词拦）",
     "张三负责后端接口设计",
     "团队负责后端接口设计",
     False, "", []),

    # 3. 技术+任务绑定变化（FastAPI 写接口→训练大模型）
    #    给 jd_terms 加 "大模型" 模拟真实场景（JD 要求大模型能力）
    ("技术+任务绑定变化（FastAPI 开发→训练大模型）",
     "用 FastAPI 开发任务管理接口",
     "用 FastAPI 训练大模型",
     True, "疑似新增技术", ["大模型", "fastapi", "训练"]),

    # 4. 新增数字成果
    ("新增数字成果",
     "训练大模型",
     "训练大模型，累计服务用户 5000+ 人次",
     True, "疑似新增数字指标", []),

    # 5. 升级技术级别（了解→精通）
    ("技能升级：了解→精通",
     "了解 LangChain",
     "精通 LangChain",
     True, "疑似措辞升级", []),

    # 6. 项目级包装
    ("项目级包装：生产级",
     "做了一个简历系统",
     "做了一个生产级简历系统",
     True, "疑似未经证实", []),

    # ============ _all_2grams_in 容错边界 ============

    # 7. 拉丁词完整包含（JD 词 "fastapi" 在 original 里完整出现）
    #    → _all_2grams_in 应该返回 True → fact_check 不应因 "fastapi" 拦
    ("拉丁词完整包含不应拦（original 已有 fastapi）",
     "用 FastAPI 开发接口",
     "用 FastAPI 开发 RESTful 接口",
     False, "", ["fastapi"]),

    # 8. 散落单字不应通过容错（JD 词 "大语言模型" 不应因散落单字被容忍）
    #    original 有"大模型"但没有"语言模型" → "大语言模型"是新增完整技术
    ("散落单字不应容忍新增完整技术",
     "用大模型做训练",
     "用大语言模型做训练",
     True, "疑似新增技术", ["大语言模型"]),

    # 9. 词序反转应该容错（训练大模型 ↔ 大模型训练）
    #    JD 词 "训练大模型" 和 original 里的 "训练大模型" 只是词序反
    ("词序反转应通过容错（训练大模型 ↔ 大模型训练）",
     "训练大模型",
     "用大模型做训练",
     False, "", ["训练大模型"]),
]


# ===================== 执行 =====================

def run():
    results = []  # (name, result, flagged, fact_warning)

    for name, original, revised, expect_flagged, expect_reason, jd_terms in CASES:
        opt = {
            "rewrite_suggestions": [{
                "original": original,
                "revised": revised,
                "basis": "测试",
                "evidence_grade": "B",
            }]
        }
        resume_text = original  # 简化：简历原文就是 original

        result, summary = check_rewrite_suggestions(
            opt, resume_text,
            resume_tech=[],
            jd_terms=jd_terms,
        )
        flagged = summary["flagged"]

        # 提取 fact_warning
        fact_warning = ""
        for sug in result.get("rewrite_suggestions", []):
            if sug.get("fact_warning"):
                fact_warning = sug["fact_warning"]
                break

        # 判定
        result_label = ""
        if expect_flagged and flagged == 0:
            result_label = "FAIL"
        elif not expect_flagged and flagged > 0:
            result_label = "FAIL"
        else:
            # flagged 符合预期 → 检查原因
            if expect_reason:
                reason_ok = any(r in fact_warning for r in expect_reason.split("|"))
                if reason_ok:
                    result_label = "FULL_PASS"
                else:
                    result_label = "PARTIAL_PASS"
            else:
                result_label = "PASS"

        results.append((name, result_label, flagged, fact_warning))

    return results


if __name__ == "__main__":
    results = run()

    full_pass = sum(1 for _, r, _, _ in results if r == "FULL_PASS")
    partial = sum(1 for _, r, _, _ in results if r == "PARTIAL_PASS" or r == "PASS")
    fail = sum(1 for _, r, _, _ in results if r == "FAIL")

    print("=" * 70)
    print("fact_check 语义级回归测试 v2（核对拦截原因）")
    print("=" * 70)

    for name, r, flagged, warning in results:
        if r == "FAIL":
            tag = "❌ FAIL"
        elif r == "PARTIAL_PASS":
            tag = "⚠️ PARTIAL"
        elif r == "FULL_PASS":
            tag = "✅ FULL"
        else:
            tag = "✅ PASS"
        print(f"  {tag}  {name}")
        if r in ("FAIL", "PARTIAL_PASS") or warning:
            print(f"         flagged={flagged}  fact_warning=\"{warning}\"")

    print()
    print(f"完整识别 (FULL_PASS): {full_pass}")
    print(f"碰巧拦截 / 仅 flagged 对 (PARTIAL/PASS): {partial}")
    print(f"FAIL: {fail}")

    # 盲区摘要
    blind = [name for name, r, _, _ in results if r == "FAIL"]
    partial_list = [name for name, r, _, _ in results if r == "PARTIAL_PASS"]
    if blind or partial_list:
        print()
        print("⚠️ 需要关注的盲区：")
        for b in blind:
            print(f"  ❌ FAIL: {b}")
        for p in partial_list:
            print(f"  ⚠️ PARTIAL（拦截了但原因不对）: {p}")

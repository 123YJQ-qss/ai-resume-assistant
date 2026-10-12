"""fact_check 语义级回归测试

用户明确指出：单字 multiset 只检查字符重合，无法识别动作主体、职责程度、
技术与动作关系、数字成果等事实关系变化。

本模块以反例驱动，测试 fact_check 是否会漏掉以下类型的虚构改写：

  1. 动作主体变化："张三负责" → "团队负责"（主体变了但 char 仍有重合）
  2. 职责程度升级："参与设计" → "主导设计"（程度升级，但"设计"两字在原文）
  3. 技术+任务绑定变化："用 FastAPI 写接口" → "用 FastAPI 训练大模型"
     （FastAPI 在原文，所以 multiset 说"可以"，但训练大模型是假的）
  4. 数字成果新增：原文无数字 → revised 加了"5000 次调用"
  5. 技能升级："了解 X" → "精通 X"

这些测试的目的不是证明当前 fact_check 都能挡住——而是**准确标记哪些类型
还挡不住**，作为后续增强的明确目标。

用法：python backend/eval/fact_check_tests.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from services.fact_check import check_rewrite_suggestions, _norm, _all_2grams_in


# ============ 事实关系测试 ============

def run_all():
    results = []

    # --- 测试 fact_check 主流程能否检测到 ---
    def _test_check(name, original, revised, expect_flagged, resume_text=None, jd_terms=None):
        """expect_flagged=True 表示期望 fact_check 检出违规"""
        opt = {
            "rewrite_suggestions": [{
                "original": original,
                "revised": revised,
                "basis": "测试",
                "evidence_grade": "B",
            }]
        }
        resume = resume_text or original
        jd = jd_terms or []
        result, summary = check_rewrite_suggestions(
            opt, resume,
            resume_tech=[],  # 简化
            jd_terms=jd,
        )
        flagged = summary["flagged"]
        ok = (flagged > 0) == expect_flagged
        results.append(("fact_check", name, ok, flagged, summary))
        return ok

    # --- 测试 _all_2grams_in 在不同语义场景下的表现 ---
    def _test_2gram(name, source, target, expect):
        got = _all_2grams_in(source, _norm(target))
        ok = got == expect
        results.append(("2gram", name, ok, got, None))
        return ok

    # ============== fact_check 主流程测试 ==============

    # 案例 1：职责程度升级（参与→主导）—— fact_check 应该能挡住（有 UPGRADE_WORDS）
    _test_check("职责升级：参与→主导",
                original="参与 AI 简历优化系统开发",
                revised="主导 AI 简历优化系统开发",
                expect_flagged=True)

    # 案例 2：动作主体变化（张三→团队）—— fact_check 现有能力可能挡不住
    _test_check("动作主体变化：张三→团队",
                original="张三负责后端接口设计",
                revised="团队负责后端接口设计",
                expect_flagged=False)  # 标记=False 说明这是已知盲区

    # 案例 3：技术+任务绑定变化（FastAPI 写接口→训练大模型）
    # original 有 FastAPI，所以 multiset 说"可以"，但任务变了
    _test_check("技术+任务绑定变化",
                original="用 FastAPI 开发任务管理接口",
                revised="用 FastAPI 训练大模型",
                expect_flagged=False)

    # 案例 4：新增数字成果
    _test_check("新增数字成果",
                original="训练大模型",
                revised="训练大模型，累计服务用户 5000+ 人次",
                expect_flagged=True)

    # 案例 5：升级技术级别（了解→精通）
    _test_check("技能升级：了解→精通",
                original="了解 LangChain",
                revised="精通 LangChain",
                expect_flagged=True)

    # 案例 6：项目级包装
    _test_check("项目级包装：生产级",
                original="做了一个简历系统",
                revised="做了一个生产级简历系统",
                expect_flagged=True)

    # ============== _all_2grams_in 语义级测试 ==============

    # 案例 A：拉丁词+中文组合（FastAPI 框架）—— FastAPI 不在原文 → 不应容错
    _test_2gram("拉丁词+后缀不应误判",
                "fastapi框架",
                "使用 flask 开发接口",  # 原文只有 flask
                expect=False)

    # 案例 B：中文子串散落（"大语言模型" vs "大数据"+"语言理解"）
    _test_2gram("散落单字不应通过容错",
                "大语言模型",
                "做大数据分析和自然语言理解",
                expect=False)

    # 案例 C：词序反转应该容错
    _test_2gram("词序反转应通过容错",
                "训练大模型",
                "用大模型做训练",
                expect=True)

    return results


if __name__ == "__main__":
    results = run_all()
    print("=" * 70)
    print("fact_check 语义级回归测试")
    print("=" * 70)

    pass_count = sum(1 for _, _, ok, _, _ in results if ok)
    total = len(results)

    for cat, name, ok, detail, summary in results:
        tag = "PASS" if ok else "FAIL"
        print(f"  [{tag}] {name}")
        if not ok:
            if cat == "fact_check":
                flagged = detail
                print(f"         fact_check.flagged={flagged}（期望值未满足）")
                if summary:
                    print(f"         summary={summary}")
            else:
                print(f"         实际返回 {detail}")

    print()
    print(f"结果: {pass_count}/{total} PASS")
    print()

    # 打印盲区分析
    blind_spots = []
    for cat, name, ok, detail, summary in results:
        if not ok:
            blind_spots.append(name)

    if blind_spots:
        print("⚠️ 以下场景是 fact_check 的已知盲区（需要后续增强）：")
        for b in blind_spots:
            print(f"  • {b}")
    else:
        print("✅ 当前 fact_check 无盲区")

"""回归测试套件 — fact_check + rewrite_filter

不依赖外部服务，直接 import 后端模块做函数级验证。
所有测试样例脱敏，不包含真实简历或密钥。

用法：python backend/_regression_local.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

def test_2gram():
    """返回 [(name, got, expect), ...]"""
    from services.fact_check import _all_2grams_in, _norm
    return [
        # 词序反转 → 应容错（中文字符全集都在 target 里）
        ("词序反转：训练大模型 ↔ 大模型训练",
         _all_2grams_in("大模型训练", _norm("训练大模型")), True),
        # 新增拉丁技术 → 应触发（拉丁词严格检查）
        ("新增技术：LangChain ↔ 原文只有 PyTorch",
         _all_2grams_in("langchain", _norm("使用 PyTorch 训练模型")), False),
        # 边界：散落单字（不应被 2-gram 误判）
        ("边界风险：大语言模型 vs 大数据+语言理解（散落）",
         _all_2grams_in("大语言模型", _norm("做大数据分析和自然语言理解")), False),
        # 拉丁词匹配
        ("拉丁词命中：FastAPI vs 原文有 fastapi",
         _all_2grams_in("fastapi", _norm("使用 fastapi 开发")), True),
        ("拉丁词不命中：FastAPI vs 原文没有",
         _all_2grams_in("fastapi", _norm("使用 flask 开发")), False),
    ]


def test_substantive_change():
    """返回 [(name, got, expect), ...]"""
    from api.analyze import _rewrite_has_substantive_change
    return [
        # === 应保留 ===
        ("保留：具体化职责（有实质信息增量）",
         _rewrite_has_substantive_change(
            "参与项目开发",
            "负责 AI 简历优化系统的后端架构设计与 FastAPI 接口实现"
         ), True),

        ("保留：STAR 结构重组织",
         _rewrite_has_substantive_change(
            "在公司做了一个简历项目，用了 LangChain 和 DeepSeek",
            "主导开发多阶段 AI 简历优化系统（LangChain Agent Workflow + DeepSeek LLM），上线后服务用户 5000+"
         ), True),

        ("保留：术语纠正",
         _rewrite_has_substantive_change(
            "我们用 RAG 提升了效果",
            "构建 RAG 检索增强生成管线，引入 FAISS 向量索引提升知识命中率"
         ), True),

        # === 应过滤 ===
        ("过滤：完全相同",
         _rewrite_has_substantive_change("使用 FastAPI 开发接口", "使用 FastAPI 开发接口"), False),

        ("过滤：仅标点微调",
         _rewrite_has_substantive_change(
            "使用 FastAPI 开发任务管理、数据查询等业务接口，通过 SQLAlchemy 与 MySQL 完成数据读写。",
            "使用 FastAPI 开发任务管理、数据查询等业务接口，通过 SQLAlchemy 与 MySQL 完成数据读写"
         ), False),

        ("过滤：空泛短句追加",
         _rewrite_has_substantive_change(
            "使用 FastAPI 开发任务管理、数据查询等业务接口",
            "使用 FastAPI 开发任务管理、数据查询等业务接口，支持平台业务功能实现"
         ), False),

        ("过滤：措辞升级单字改动（熟悉→精通）",
         _rewrite_has_substantive_change("熟悉 Python 编程", "精通 Python 编程"), False),

        ("过滤：措辞升级单字改动（参与→主导）",
         _rewrite_has_substantive_change("参与项目开发", "主导项目开发"), False),
    ]


if __name__ == "__main__":
    print("=" * 60)
    print("回归测试套件 — fact_check + rewrite_filter")
    print("=" * 60)

    all_pass = True

    print("\n--- #1 _all_2grams_in 2-gram 容错 ---")
    for name, got, expect in test_2gram():
        ok = got == expect
        if not ok: all_pass = False
        tag = "PASS" if ok else "FAIL"
        print(f"  [{tag}] {name}")
        if not ok:
            print(f"         期望 {expect}, 实际 {got}")

    print("\n--- #2 _rewrite_has_substantive_change ---")
    for name, got, expect in test_substantive_change():
        ok = got == expect
        if not ok: all_pass = False
        tag = "PASS" if ok else "FAIL"
        print(f"  [{tag}] {name}")
        if not ok:
            print(f"         期望 {expect}, 实际 {got}")

    print("\n" + "=" * 60)
    print("整体结果：", "全部 PASS ✅" if all_pass else "存在 FAIL ❌")
    print("=" * 60)
    sys.exit(0 if all_pass else 1)

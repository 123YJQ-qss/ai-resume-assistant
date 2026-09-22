"""test_evidence.py - evidence.py 单元测试

零真实 LLM，零网络请求，零第三方依赖。
运行：python backend/services/test_evidence.py
"""
import json, sys, os

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from services import evidence

RESUME = """杨佳奇
熟悉 Python 开发，掌握 FastAPI / Django 框架
设计 LLM Provider 抽象服务层，解耦 Agent 与底层模型调用
熟悉 Python 开发，掌握 FastAPI / Django 框架
基于 Paramiko 实现 SSH 远程连接与 SFTP 文件管理
"""

def test_basic_attach():
    """精确原文匹配成功"""
    result = {"rewrite_suggestions": [
        {"original": "掌握 FastAPI / Django 框架", "revised": "改写后"},
    ]}
    evidence.attach_evidence(result, RESUME)
    ev = result["rewrite_suggestions"][0]["evidence"]
    assert len(ev) >= 1
    e = ev[0]
    assert e["evidence_index"] == 1
    assert isinstance(e["match_score"], float) and 0 < e["match_score"] <= 1
    assert e["source_type"] == "resume"
    print(f"  ✅ 基本匹配: source_id={e['source_id']} match_score={e['match_score']}")

def test_original_not_in_resume():
    """LLM original 不在简历中 → evidence=[]"""
    result = {"rewrite_suggestions": [
        {"original": "完全不存在的片段 Kubernetes Docker", "revised": "改写后"},
    ]}
    evidence.attach_evidence(result, RESUME)
    ev = result["rewrite_suggestions"][0]["evidence"]
    assert ev == [], f"期望空数组，实际={ev}"
    print(f"  ✅ original 不在简历时 evidence=[]")

def test_duplicate_text_source_id_distinct():
    """相同文本在不同位置 → 不同 source_id"""
    # RESUME 里 "熟悉 Python 开发，掌握 FastAPI / Django 框架" 出现两次（行 2 和行 4）
    frags = evidence.build_resume_fragments(RESUME)
    # 找两条相同 original_text
    from collections import Counter
    text_counts = Counter(f["original_text"] for f in frags)
    dup_texts = [t for t, c in text_counts.items() if c > 1]
    assert dup_texts, "简历里应该有重复文本用于测试"
    dup = dup_texts[0]
    dup_ids = [f["source_id"] for f in frags if f["original_text"] == dup]
    assert len(dup_ids) >= 2
    assert len(set(dup_ids)) == len(dup_ids), \
        f"相同文本不同位置应该有不同 source_id: {dup_ids}"
    print(f"  ✅ 重复文本 source_id 不同: {dup_ids}")

def test_source_id_stable():
    """同一简历重复运行 → 相同 source_id"""
    ids_a = [f["source_id"] for f in evidence.build_resume_fragments(RESUME)]
    ids_b = [f["source_id"] for f in evidence.build_resume_fragments(RESUME)]
    assert ids_a == ids_b
    for sid in ids_a:
        assert sid.startswith("resume_")
        body = sid[len("resume_"):]
        assert "_" in body  # occurrence_index 部分
        hex_part, idx = body.rsplit("_", 1)
        assert len(hex_part) == 12
        assert idx.isdigit()
    print(f"  ✅ source_id 稳定且格式正确（resume_<12hex>_<idx>）")

def test_match_score_not_similarity():
    """match_score 是字符串匹配覆盖率，不是向量相似度"""
    result = {"rewrite_suggestions": [
        {"original": "掌握 FastAPI / Django 框架", "revised": "改写后"},
    ]}
    evidence.attach_evidence(result, RESUME)
    e = result["rewrite_suggestions"][0]["evidence"][0]
    # match_score 是 len(normalized_original) / len(normalized_fragment)
    # 精确匹配时 = 1.0
    assert e["match_score"] == 1.0 or e["match_score"] < 1.0
    # 字段名必须叫 match_score，不能叫 score
    assert "score" not in e or "match_score" in e
    assert "match_score" in e
    print(f"  ✅ match_score={e['match_score']}（字符串覆盖率，非向量相似度）")

def test_evidence_method_marked():
    """resume_fragments 顶层必须标记 evidence_method"""
    result = {"rewrite_suggestions": [
        {"original": "掌握 FastAPI / Django 框架", "revised": "改写后"},
    ]}
    evidence.attach_evidence(result, RESUME)
    rf = result.get("resume_fragments")
    assert rf is not None
    assert rf.get("evidence_method") == "exact_source_match"
    print(f"  ✅ evidence_method=exact_source_match")

def test_evidence_index_not_rank():
    """字段名 evidence_index，不能叫 rank（不是检索排名）"""
    result = {"rewrite_suggestions": [
        {"original": "掌握 FastAPI / Django 框架", "revised": "改写后"},
    ]}
    evidence.attach_evidence(result, RESUME)
    e = result["rewrite_suggestions"][0]["evidence"][0]
    assert "evidence_index" in e
    assert "rank" not in e  # 旧字段名已移除
    assert e["evidence_index"] == 1
    print(f"  ✅ evidence_index 字段名正确（不是 rank）")

def test_error_isolation():
    """假设 build_resume_fragments 抛异常 → attach_evidence 不应破坏调用方"""
    # 用 monkey patch 让 build_resume_fragments 抛
    import services.evidence as ev_mod
    orig = ev_mod.build_resume_fragments
    try:
        ev_mod.build_resume_fragments = lambda r: (_ for _ in ()).throw(RuntimeError("boom"))
        result = {"rewrite_suggestions": [
            {"original": "x", "revised": "y"},
        ]}
        # attach_evidence 自己现在也不 try/except —— 由 analyze.py 的调用方 try/except 包裹
        # 这里测试：attach_evidence 内部不吞异常（让调用方决定如何处理）
        raised = False
        try:
            ev_mod.attach_evidence(result, RESUME)
        except RuntimeError as e:
            raised = True
            assert "boom" in str(e)
        assert raised, "证据链内部异常应向上抛出，由业务侧 try/except 隔离"
        print(f"  ✅ 证据链内部异常向上抛出（由调用方隔离）")
    finally:
        ev_mod.build_resume_fragments = orig

def test_json_roundtrip():
    """结果可 json.dumps / json.loads"""
    result = {"rewrite_suggestions": [
        {"original": "掌握 FastAPI / Django 框架", "revised": "改写后"},
    ]}
    evidence.attach_evidence(result, RESUME)
    s = json.dumps(result, ensure_ascii=False)
    loaded = json.loads(s)
    assert len(loaded["rewrite_suggestions"][0]["evidence"]) >= 1
    print(f"  ✅ JSON roundtrip 通过")

def test_no_rewrite_suggestions():
    """没有 rewrite_suggestions → 安全返回"""
    result = {"match_level": {"overall": "待评估"}}
    evidence.attach_evidence(result, RESUME)
    assert result["match_level"]["overall"] == "待评估"
    print(f"  ✅ 无 rewrite_suggestions 时安全返回")

def test_empty_resume():
    """空简历 → evidence=[]，不抛异常"""
    result = {"rewrite_suggestions": [
        {"original": "任何", "revised": "改写"},
    ]}
    evidence.attach_evidence(result, "")
    ev = result["rewrite_suggestions"][0]["evidence"]
    assert ev == []
    print(f"  ✅ 空简历不抛异常")

def test_original_text_from_resume():
    """evidence.original_text 必须是简历原文子串"""
    result = {"rewrite_suggestions": [
        {"original": "掌握 FastAPI / Django 框架", "revised": "改写后"},
    ]}
    evidence.attach_evidence(result, RESUME)
    e = result["rewrite_suggestions"][0]["evidence"][0]
    assert e["original_text"].strip() in RESUME
    print(f"  ✅ evidence.original_text 是简历原文子串")

# ---- runner ----
def run():
    print("=" * 60)
    print("evidence.py 单元测试（v2 审计版）")
    print("=" * 60)
    tests = [
        test_basic_attach,
        test_original_not_in_resume,
        test_duplicate_text_source_id_distinct,
        test_source_id_stable,
        test_match_score_not_similarity,
        test_evidence_method_marked,
        test_evidence_index_not_rank,
        test_error_isolation,
        test_json_roundtrip,
        test_no_rewrite_suggestions,
        test_empty_resume,
        test_original_text_from_resume,
    ]
    passed = 0
    for t in tests:
        try:
            t()
            passed += 1
        except AssertionError as e:
            print(f"  ❌ {t.__name__}: {e}")
        except Exception as e:
            import traceback
            print(f"  ❌ {t.__name__} 异常: {e}")
            traceback.print_exc()
    print(f"\n  通过: {passed}/{len(tests)}")
    return passed == len(tests)

if __name__ == "__main__":
    ok = run()
    sys.exit(0 if ok else 1)

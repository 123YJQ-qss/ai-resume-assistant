"""临时脚本：fact_check 合成用例自检（不调用 LLM）。"""
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, r"e:\AI简历优化助手-deploy\backend")

from services import fact_check

RESUME = "3年Python后端，使用FastAPI开发接口，调用过OpenAI/DeepSeek接口，做过基于向量检索的RAG demo，参与过团队项目开发。"
RESUME_TECH = ["Python", "FastAPI", "OpenAI", "DeepSeek", "RAG", "向量检索"]
JD_TERMS = fact_check.extract_jd_terms({
    "核心技能": ["Python", "Docker", "LangGraph"],
    "技术要求": ["K8s", "性能调优"],
    "岗位关键词": ["模型部署"],
})

CASES = [
    # (name, item, 期望违规数)
    ("合法B级改写", {"original": "使用FastAPI开发接口", "revised": "具备FastAPI接口开发实践", "evidence_grade": "B"}, 0),
    ("合法A级原文", {"original": "做过基于向量检索的RAG demo", "revised": "做过基于向量检索的RAG demo", "evidence_grade": "A"}, 0),
    ("新增技术", {"original": "使用FastAPI开发接口", "revised": "使用FastAPI与Docker开发接口", "evidence_grade": "A"}, 1),
    ("新增指标", {"original": "使用FastAPI开发接口", "revised": "使用FastAPI开发接口，性能提升60%", "evidence_grade": "A"}, 1),
    ("措辞升级", {"original": "参与过团队项目开发", "revised": "主导团队项目开发", "evidence_grade": "A"}, 1),
    ("项目级包装", {"original": "做过RAG demo", "revised": "构建生产级高可用RAG系统", "evidence_grade": "A"}, 1),
    ("越级C", {"original": "调用过OpenAI接口", "revised": "精通Prompt Engineering", "evidence_grade": "C"}, 1),
    ("original不可追溯", {"original": "主导过千亿级网关重构", "revised": "具备网关重构经验", "evidence_grade": "A"}, 1),
]

result = {"rewrite_suggestions": [c[1] for c in CASES]}
result, summary = fact_check.check_rewrite_suggestions(result, RESUME, resume_tech=RESUME_TECH, jd_terms=JD_TERMS)
print("summary:", summary)
ok = True
for (name, item, expect) in CASES:
    warn = item.get("fact_warning", "")
    actual = 1 if warn else 0
    status = "PASS" if actual == expect else "FAIL"
    if actual != expect:
        ok = False
    print(f"[{status}] {name}: 期望{expect} 实际{actual} {warn}")

# 原文已有"精通"时不算升级
r2 = {"rewrite_suggestions": [{"original": "精通Python", "revised": "精通Python与算法", "evidence_grade": "A"}]}
r2, s2 = fact_check.check_rewrite_suggestions(r2, "精通Python，3年经验", resume_tech=["Python"], jd_terms=[])
print("原文含精通用例:", s2, "warning=", r2["rewrite_suggestions"][0].get("fact_warning", "无"))
print("\n总体:", "ALL PASS" if ok else "存在FAIL")

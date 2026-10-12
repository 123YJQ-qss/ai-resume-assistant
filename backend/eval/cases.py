"""10 个真实 JD 回归评测用例（脱敏样例）

每个 Case 包含：
  - case_id / description
  - resume_text（脱敏：用虚构姓名，真实结构）
  - job_description（脱敏：真实 JD 关键词，脱敏公司/人名）
  - human_expect（人工期望：必须达成的质量标准）
  - 验收检查函数列表

所有用例都是为了覆盖不同风险模式，不是真实简历（虚构姓名、虚构公司）。
"""
from .assertions import (
    check_data_source_is_workflow,
    check_match_level_has_four_fields,
    check_analysis_basis_is_list,
    check_fact_check_no_violation,
    check_gaps_have_type_tag,
    check_rewrite_grade_is_ab,
    check_no_forbidden_fake_graduation,
    check_match_level_consistent_with_basis,
)


def build_cases():
    cases = []

    # ====== CASE1：正常匹配 — AI 应用开发 ======
    # 背景：候选人技术栈与 JD 高度匹配，有明确项目经验
    cases.append({
        "case_id": "CASE1_正常匹配_AI应用开发",
        "description": "技术栈高度匹配 + 有真实项目经验，期望整体匹配度偏高，有 1-3 条改写",
        "resume_text": (
            "张三，2022.09-2025.06 软件工程 本科（已毕业）。"
            "2025.07 至今 在字节跳动担任 AI 应用开发工程师，使用 Python、FastAPI、"
            "LangChain 构建多阶段 Agent Workflow，集成 DeepSeek 大模型实现简历智能分析，"
            "服务用户超过 5000 人次。"
        ),
        "job_description": (
            "AI 应用开发工程师。职责：负责 AI 大模型应用的后端架构设计与开发；"
            "基于 LangChain 等框架构建智能 Agent 工作流；集成 DeepSeek、GPT 等主流大模型 API。"
            "要求：本科及以上学历计算机相关专业；熟练 Python 和 FastAPI；"
            "有 LLM 应用开发经验，了解 LangChain；具备工程化意识。"
        ),
        "human_expect": {
            "min_match_overall": "中等",  # 至少中等，不能偏低
            "expected_gaps": ["Django 经验", "GPT API 实践"],  # 这些应该在 gap 里出现
            "must_not_have_fake": ["尚未毕业", "本科在读"],
            "min_rewrite_count": 0,  # 可 0 条（原文已好），不强制
        },
    })

    # ====== CASE2：核心能力缺失 — 文学 vs 后端 ======
    # 背景：候选人专业方向完全不匹配，JD 核心技能一个没有
    cases.append({
        "case_id": "CASE2_核心能力缺失",
        "description": "汉语言文学背景申请后端工程师，无任何计算机经验，期望匹配度偏低且明确列出能力缺口",
        "resume_text": (
            "李四，2020-2024 汉语言文学 本科。"
            "曾在出版社担任编辑 2 年，负责内容审核、校对、选题策划。"
            "熟悉 Word、Excel、Adobe InDesign。"
        ),
        "job_description": (
            "后端工程师。要求：本科及以上学历计算机相关专业；熟练 Python、Java 或 Go；"
            "熟悉 MySQL、Redis、Docker；有高并发系统开发经验；了解分布式架构。"
        ),
        "human_expect": {
            "max_match_overall": "中等",  # 不能判较高
            "must_have_gap_types": ["能力缺口"],
            "gap_should_include": ["Python", "MySQL", "Docker"],
        },
    })

    # ====== CASE3：跨岗位匹配 — 工业设计 PM → AI PM ======
    # 背景：产品经验相关但方向不同，AI 经验待确认
    cases.append({
        "case_id": "CASE3_跨岗位匹配",
        "description": "工业设计背景的产品经理应聘 AI 产品经理，产品经验相关但 AI 方向是新领域",
        "resume_text": (
            "王五，2021-2025 工业设计 本科。"
            "曾在智能家居公司担任产品经理 2 年，负责硬件产品定义、用户研究、"
            "PRD 撰写、与设计/供应链团队协调。"
        ),
        "job_description": (
            "产品经理（AI 方向）。要求：本科及以上学历；2-5 年产品经理经验；"
            "熟悉用户研究、PRD 撰写、产品迭代方法；"
            "有 AI/智能硬件/数据产品经验优先。"
        ),
        "human_expect": {
            "must_have_gap_types": ["事实待确认"],  # AI 产品经验待确认，不是"能力缺口"
            "should_not_have_gap_types": ["能力缺口"],  # 产品基础能力不是缺口
        },
    })

    # ====== CASE4：经历不足 — 在读学生 ======
    # 背景：计算机在读，无任何工作经验，申请需要工作经验的岗位
    cases.append({
        "case_id": "CASE4_经历不足_在读无经验",
        "description": "计算机本科在读，无任何工作/实习经历，期望匹配度低但不能判'能力缺口'",
        "resume_text": (
            "赵六，2025.09 至今 计算机科学与技术 本科在读。"
            "已修课程：Python 程序设计、数据结构、操作系统。"
            "自学过 LangChain、FastAPI 基础框架。"
        ),
        "job_description": (
            "Python 后端工程师。要求：本科及以上学历计算机相关专业；"
            "1-3 年 Python 开发经验；熟悉 Web 框架（FastAPI/Django）；"
            "有实际项目部署经历。"
        ),
        "human_expect": {
            "must_not_have_fake": ["已毕业"],  # 在读不能判已毕业
            "must_have_gap_types": ["事实待确认"],  # 工作经验待确认
            "max_match_overall": "中等",
        },
    })

    # ====== CASE5：已毕业确认 — 禁止判在读 ======
    # 背景：明确写"2024 年 6 月已毕业"，AI 不能无依据判在读
    cases.append({
        "case_id": "CASE5_已毕业确认",
        "description": "简历明确写'已毕业'，AI 不能出现'尚未毕业'判断",
        "resume_text": (
            "孙七，2020.09-2024.06 计算机科学 本科（2024 年 6 月已毕业）。"
            "2024.07 至今 在某互联网公司担任后端开发工程师，使用 Go 和 MySQL。"
        ),
        "job_description": (
            "后端工程师。要求：本科及以上学历计算机相关专业；"
            "熟悉 Go 或 Python；有微服务开发经验。"
        ),
        "human_expect": {
            "must_not_have_fake": ["尚未毕业", "本科在读", "仍在校"],
        },
    })

    # ====== CASE6：表达充分 → 改写应为空 ======
    # 背景：简历描述已经足够清晰专业，测试 AI 是否"不硬凑改写"
    cases.append({
        "case_id": "CASE6_表达充分不应硬凑改写",
        "description": "简历描述已清晰专业，rewrite_suggestions 应该为空或很少",
        "resume_text": (
            "周八，负责开发 AI Agent Workflow 系统，采用 LangChain 编排四阶段 Agent，"
            "集成 DeepSeek V3 大模型作为推理引擎，通过 FAISS 向量索引检索岗位知识库，"
            "实现智能简历分析与改写建议生成，服务用户 5000+。"
        ),
        "job_description": (
            "AI 应用开发工程师。职责：负责 AI Agent 系统架构设计与开发；"
            "基于 LangChain 等框架构建智能工作流；集成主流大模型 API；"
            "要求：熟悉 LangChain、Python、FastAPI、DeepSeek。"
        ),
        "human_expect": {
            "rewrite_count_zero_or_few": True,  # 允许 0-1 条，不应该硬凑
        },
    })

    # ====== CASE7：事实冲突 — 时间推算 ======
    # 背景：简历写"2020-2023 本科"但没写"已毕业"，AI 应该判"待确认"而非强断言
    cases.append({
        "case_id": "CASE7_时间推算应待确认",
        "description": "2020-2023 时间段无'已毕业'标注，AI 不能仅凭时间断言状态",
        "resume_text": (
            "吴九，教育经历：2020.09-2023.06 软件工程。"
            "目前在一家 AI 公司做后端开发。"
        ),
        "job_description": (
            "后端开发工程师。要求：计算机相关专业；1-3 年开发经验；熟悉 Python。"
        ),
        "human_expect": {
            "should_not_assert_graduate_state": True,  # 不能硬说已毕业或在读
        },
    })

    return cases


# 统一的自动化检查函数（所有 case 共享）
def standard_checks():
    """每个 case 都要跑的 HARD_ASSERT / LOGIC_CHECK"""
    return [
        check_data_source_is_workflow,
        check_match_level_has_four_fields,
        check_analysis_basis_is_list,
        check_fact_check_no_violation,
        check_gaps_have_type_tag,
        check_rewrite_grade_is_ab,
        check_match_level_consistent_with_basis,
    ]


# 语义质量检查（自动化无法判定，一律 MANUAL_REVIEW）
# 每个 case 跑完后自动标记这些需要人工看
SEMANTIC_CHECK_DESCRIPTIONS = [
    "匹配等级是否符合人工期望（看 overall/ability/experience/risk 四个值）",
    "关键技术要求是否遗漏（对比 JD 核心关键词与 analysis_basis）",
    "事实幻觉检测（rewrite 新增技术/数字/项目级别）",
    "空泛改写检测（rewrite 是否只是加评价短句）",
    "跨 Tab 一致性（match_level 与 analysis_basis.overall_gap_ratio 一致）",
    "教育经历/时间推断正确性",
    "weaknesses 或 supplement 的分类标记是否准确（[表达优化]/[事实待确认]/[能力缺口]）",
]

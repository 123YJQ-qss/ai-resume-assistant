# AI Resume Assistant — 第四阶段人工复核报告

- **生成时间**: 2026-10-12 20:20:20
- **评测时间**: 2026-10-12 20:07:46
- **Commit**: `3d14c57c` (3d14c57cb7282121a8e99f8bab2eddd58bd33b52)
- **模型**: deepseek-chat
- **框架版本**: v2
- **受控 Case 数**: 10
- **自动化**: PASS=84 / FAIL=0 / 待人工复核=73


## 逐 Case 自动汇总

| Case | PASS | FAIL | MANUAL | total |
|------|------|------|--------|-------|
| CASE1_正常匹配_AI应用开发 | 10 | 0 | 7 | 17 |
| CASE2_核心能力缺失 | 9 | 0 | 7 | 16 |
| CASE3_跨岗位匹配 | 8 | 0 | 7 | 15 |
| CASE4_经历不足_在读无经验 | 9 | 0 | 8 | 17 |
| CASE5_已毕业确认 | 9 | 0 | 7 | 16 |
| CASE6_表达充分不应硬凑改写 | 7 | 0 | 8 | 15 |
| CASE7_时间推算应待确认 | 8 | 0 | 7 | 15 |
| CASE8_事实冲突_技术栈 | 7 | 0 | 8 | 15 |
| CASE9_数字成果虚构不应出现 | 8 | 0 | 7 | 15 |
| CASE10_技术能力夸大_隐蔽措辞 | 9 | 0 | 7 | 16 |
| **TOTAL** | **84** | **0** | **73** | **157** |

---

## 逐 Case 详细报告

## CASE10_技术能力夸大_隐蔽措辞

**测试目的**: 简历写'了解 Docker'，rewrite 写成'深入掌握 Docker / Kubernetes'，检查是否被拦截
**人工期望**: `{"should_not_have_grade_upgrade": true, "min_match_overall": "较低"}`

### 1. 输入（完整不截断）

**简历**:
```
陈十二，2022.09-2026.06 计算机科学（预计毕业）。自学 Python、FastAPI、LangChain；了解 Docker 和 Linux。曾做过一个简历分析的个人项目。
```

**JD**:
```
AI 应用开发工程师。岗位职责：负责 AI 大模型应用的后端架构设计与开发，基于 LangChain 等框架构建智能 Agent 工作流。任职要求：本科及以上学历计算机相关专业；熟练掌握 Python 和 FastAPI；有 LLM 应用开发经验；了解 LangChain；熟悉 Docker / Kubernetes；具备良好的工程化意识。
```

### 2. AI 综合匹配结论

- **overall**: 中等
- **ability**: 中等
- **experience**: 较弱
- **risk**: 需要优化

### 3. 详细分析 (analysis_basis)


**维度: 技术栈匹配**
  - ✅ **match** (高): 简历体现掌握 Python，与 JD 技术要求一致
    > 原文: 自学 Python、FastAPI、LangChain
  - ✅ **match** (高): 简历体现掌握 FastAPI，与 JD 技术要求一致
    > 原文: 自学 Python、FastAPI、LangChain
  - ✅ **match** (中): 简历体现掌握 LangChain，与 JD 核心技能（智能 Agent 工作流构建）方向一致
    > 原文: 自学 Python、FastAPI、LangChain
  - ✅ **match** (低): 简历体现了解 Docker，与 JD 技术要求方向一致，但原文措辞为“了解”，深度有限
    > 原文: 了解 Docker 和 Linux
  - 🔸 **gap** (低): [能力缺口] 当前简历未体现 Kubernetes 技术实践，JD 明确要求该技术

**维度: 项目经历匹配**
  - ✅ **match** (中): 简历体现有一个简历分析个人项目，技术点涉及 Python、FastAPI、LangChain，与 JD 的 AI 应用开发方向相关
    > 原文: 曾做过一个简历分析的个人项目
  - 🔸 **gap** (低): [事实待确认] 当前简历未体现项目是否涉及大模型应用的后端架构设计或智能 Agent 工作流构建，需确认项目具体实现内容
  - 🔸 **gap** (低): [能力缺口] 当前简历未体现项目复杂度、规模或工程化实践（如部署、容器编排等），JD 要求工程化意识

**维度: 工作经验匹配**
  - 🔸 **gap** (低): [事实待确认] 简历未提及任何正式工作或实习经历，工作年限待确认；JD 为后端架构设计与开发岗位，通常需要一定工程经验

**维度: 教育背景匹配**
  - ✅ **match** (高): 简历体现计算机科学专业背景，与 JD 技术方向对口
    > 原文: 2022.09-2026.06 计算机科学（预计毕业）
  - 🔸 **gap** (低): [事实待确认] 简历标注“预计毕业 2026.06”，当前日期为 2026-10-12，该预计毕业时间已过，需确认候选人实际是否已毕业

### 4. 改写建议 (rewrite_suggestions)


**改写 #1** (grade=B)
- **original**: `自学 Python、FastAPI、LangChain；了解 Docker 和 Linux。`
- **revised**: `技术栈：Python、FastAPI、LangChain（自学）；Docker、Linux（了解）。`
- **basis**: 依据：原文《自学 Python、FastAPI、LangChain；了解 Docker 和 Linux》；JD 要求 Python、FastAPI、LangChain、Docker 等技术栈；改写逻辑：将原文技术栈按“掌握程度”分组归类，使技术能力层次更清晰，便于招聘方快速定位与 JD 匹配的关键技能，不新增任何技术词或改变掌握程度。

**改写 #2** (grade=B)
- **original**: `曾做过一个简历分析的个人项目。`
- **revised**: `个人项目：基于 Python、FastAPI、LangChain 实现简历分析功能。`
- **basis**: 依据：原文《曾做过一个简历分析的个人项目》及前文《自学 Python、FastAPI、LangChain》；JD 要求 AI 大模型应用开发、LLM 应用开发、LangChain；改写逻辑：将原文中分散的技术栈信息与项目描述合并，明确该项目使用了 Python、FastAPI、LangChain，使项目与 JD 的 AI 应用开发方向关联更直观，不新增任何原文未出现的技术或职责。

### 5. 事实校验 (fact_check)

- checked=2  flagged=0  violations=0

### 6. 优化任务 (optimization_advice)


**highlight** (3 条):
  - 建议突出：计算机科学专业背景与岗位技术方向对口（原文：2022.09-2026.06 计算机科学（预计毕业）），可将教育背景置于简历顶部显眼位置。
  - 建议突出：自学掌握的 Python、FastAPI、LangChain 与 JD 核心技术要求高度重合（原文：自学 Python、FastAPI、LangChain），建议在技能栏中优先展示这三项。
  - 建议突出：个人项目使用了 Python、FastAPI、LangChain（原文：曾做过一个简历分析的个人项目），建议在项目描述中明确点出技术栈，强化与 AI 应用开发方向的关联。

**expression** (2 条):
  - 建议优化表达：原表达“自学 Python、FastAPI、LangChain；了解 Docker 和 Linux。”→ 建议表达“技术栈：Python、FastAPI、LangChain（自学）；Docker、Linux（了解）。”，按掌握程度分组，层次更清晰。
  - 建议优化表达：原表达“曾做过一个简历分析的个人项目。”→ 建议表达“个人项目：基于 Python、FastAPI、LangChain 实现简历分析功能。”，将技术栈与项目关联，突出与 JD 的匹配度。

### 7. 分类汇总

- strengths: 4 条
- weaknesses: 0 条

### 8. 自动化检查结果

- ✅ [HARD_ASSERT] api_call
- ✅ [HARD_ASSERT] data_source
- ✅ [HARD_ASSERT] match_level_fields
- ✅ [HARD_ASSERT] analysis_basis_type
- ✅ [LOGIC_CHECK] fact_check_flagged
- ✅ [LOGIC_CHECK] gap_type_tags
- ✅ [LOGIC_CHECK] rewrite_grade_AB
- ✅ [CROSS_TAB] cross_tab_consistency
- ✅ [LOGIC_CHECK] match_overall_min
- 👀 [SEMANTIC] SEMANTIC: 匹配等级是否符合人工期望（看 overall/ability/experience/risk 四个值）
  > 自动化无法判定，需人工看证据
- 👀 [SEMANTIC] SEMANTIC: 关键技术要求是否遗漏（对比 JD 核心关键词与 analysis_basis）
  > 自动化无法判定，需人工看证据
- 👀 [SEMANTIC] SEMANTIC: 事实幻觉检测（rewrite 新增技术/数字/项目级别）
  > 自动化无法判定，需人工看证据
- 👀 [SEMANTIC] SEMANTIC: 空泛改写检测（rewrite 是否只是加评价短句）
  > 自动化无法判定，需人工看证据
- 👀 [SEMANTIC] SEMANTIC: 跨 Tab 一致性（match_level 与 analysis_basis.overall_gap_ratio 一致）
  > 自动化无法判定，需人工看证据
- 👀 [SEMANTIC] SEMANTIC: 教育经历/时间推断正确性
  > 自动化无法判定，需人工看证据
- 👀 [SEMANTIC] SEMANTIC: weaknesses 或 supplement 的分类标记是否准确（[表达优化]/[事实待确认]/[能力缺口]）
  > 自动化无法判定，需人工看证据

### 9. 需要人工审核的具体问题

请人工审查以下 7 项语义问题（自动化无法判定）：

- 👀 **匹配等级是否符合人工期望（看 overall/ability/experience/risk 四个值）**
  > 证据: {"overall": "中等", "ability": "中等", "experience": "较弱", "risk": "需要优化"}
- 👀 **关键技术要求是否遗漏（对比 JD 核心关键词与 analysis_basis）**
  > 证据: [{"dimension": "技术栈匹配", "items": [{"type": "match", "content": "简历体现掌握 Python，与 JD 技术要求一致", "quote": "自学 Python、FastAPI、LangChain", "match_degree": "高"}, {"type": "match", "content": "简历体现掌握 FastAPI，与 JD 技术要求一致", "quote": "自学 Python、FastAPI、LangChain", "match_degree": "高"}, {"type": "match", "content": "简历体现掌握 LangChain，与 JD 核心技能（智能 Agent 工作流构建）方向一致", "quote": "自学 Python、FastAPI、LangChain", "match_degree": "中"}, {"type": "match", "content": "简历体现了解 Docker，与 JD 技术要求方向一致，但原文措辞为“了解”，深度有限", "quote":
- 👀 **事实幻觉检测（rewrite 新增技术/数字/项目级别）**
  > 证据: [{"original": "自学 Python、FastAPI、LangChain；了解 Docker 和 Linux。", "revised": "技术栈：Python、FastAPI、LangChain（自学）；Docker、Linux（了解）。", "basis": "依据：原文《自学 Python、FastAPI、LangChain；了解 Docker 和 Linux》；JD 要求 Python、FastAPI、LangChain、Docker 等技术栈；改写逻辑：将原文技术栈按“掌握程度”分组归类，使技术能力层次更清晰，便于招聘方快速定位与 JD 匹配的关键技能，不新增任何技术词或改变掌握程度。", "evidence_grade": "B", "evidence": [{"source_id": "resume_7c2bc61b8e00_0", "original_text": "自学 Python、FastAPI、LangChain；", "evidence_index": 1, "match_score": 0.2222, "source_type": "resume
- 👀 **空泛改写检测（rewrite 是否只是加评价短句）**
- 👀 **跨 Tab 一致性（match_level 与 analysis_basis.overall_gap_ratio 一致）**
- 👀 **教育经历/时间推断正确性**
  > 证据: 简历体现掌握 Python，与 JD 技术要求一致 简历体现掌握 FastAPI，与 JD 技术要求一致 简历体现掌握 LangChain，与 JD 核心技能（智能 Agent 工作流构建）方向一致 简历体现了解 Docker，与 JD 技术要求方向一致，但原文措辞为“了解”，深度有限 [能力缺口] 当前简历未体现 Kubernetes 技术实践，JD 明确要求该技术 简历体现有一个简历分析个人项目，技术点涉及 Python、FastAPI、LangChain，与 JD 的 AI 应用开发方向相关 [事实待确认] 当前简历未体现项目是否涉及大模型应用的后端架构设计或智能 Agent 工作流构建，需确认项目具体实现内容 [能力缺口] 当前简历未体现项目复杂度、规模或工程化实践（如部署、容器编排等），JD 要求工程化意识 [事实待确认] 简历未提及任何正式工作或实习经历，工作年限待确认；JD 为后端架构设计与开发岗位，通常需要一定工程经验 简历体现计算机科学专业背景，与 JD 技术方向对口 [事实待确认] 简历标注“预计毕业 2026.06”，当前日期为 2026-10-12，该预计毕业时
- 👀 **weaknesses 或 supplement 的分类标记是否准确（[表达优化]/[事实待确认]/[能力缺口]）**

---

## CASE1_正常匹配_AI应用开发

**测试目的**: 技术栈高度匹配 + 有真实项目经验，期望整体匹配度偏高，有 1-3 条改写
**人工期望**: `{"min_match_overall": "中等", "expected_gaps": ["Django 经验", "GPT API 实践"], "must_not_have_fake": ["尚未毕业", "本科在读"], "min_rewrite_count": 0}`

### 1. 输入（完整不截断）

**简历**:
```
张三，2022.09-2025.06 软件工程 本科（已毕业）。2025.07 至今 在字节跳动担任 AI 应用开发工程师，使用 Python、FastAPI、LangChain 构建多阶段 Agent Workflow，集成 DeepSeek 大模型实现简历智能分析，服务用户超过 5000 人次。
```

**JD**:
```
AI 应用开发工程师。职责：负责 AI 大模型应用的后端架构设计与开发；基于 LangChain 等框架构建智能 Agent 工作流；集成 DeepSeek、GPT 等主流大模型 API。要求：本科及以上学历计算机相关专业；熟练 Python 和 FastAPI；有 LLM 应用开发经验，了解 LangChain；具备工程化意识。
```

### 2. AI 综合匹配结论

- **overall**: 较高
- **ability**: 较强
- **experience**: 较弱
- **risk**: 需要优化

### 3. 详细分析 (analysis_basis)


**维度: 技术栈匹配**
  - ✅ **match** (高): 候选人技术栈与岗位要求高度重合，具备 Python、FastAPI、LangChain、DeepSeek 大模型、Agent Workflow 等核心技能
    > 原文: 使用 Python、FastAPI、LangChain 构建多阶段 Agent Workflow，集成 DeepSeek 大模型实现简历智能分析
  - ✅ **match** (高): 具备 AI 大模型应用开发经验，与岗位职责中'AI 大模型应用的后端架构设计与开发'方向一致
    > 原文: 在字节跳动担任 AI 应用开发工程师
  - ✅ **match** (高): 具备智能 Agent 工作流构建经验，与岗位核心技能'智能 Agent 工作流构建'匹配
    > 原文: 构建多阶段 Agent Workflow
  - ✅ **match** (高): 具备大模型 API 集成经验，与岗位核心技能'大模型 API 集成'匹配
    > 原文: 集成 DeepSeek 大模型实现简历智能分析
  - 🔸 **gap** (低): [事实待确认] 岗位关键词包含 GPT，当前简历未体现 GPT 大模型 API 集成实践

**维度: 项目经历匹配**
  - ✅ **match** (高): 项目'简历智能分析系统'与岗位 AI 应用开发方向高度相关，涉及多阶段 Agent Workflow 与 DeepSeek 大模型集成
    > 原文: 集成 DeepSeek 大模型实现简历智能分析
  - ✅ **match** (中): 项目已落地并服务超过 5000 人次用户，具备实际业务交付能力
    > 原文: 服务用户超过 5000 人次
  - 🔸 **gap** (中): [表达优化] 简历项目描述较为简略，缺少后端架构设计的具体细节、成果量化指标及团队协作经历

**维度: 工作经验**
  - 🔸 **gap** (中): [事实待确认] 工作年限较短，2025.07 至今约 1 年 3 个月工作经验（按当前日期 2026-10-12 计算），岗位未明确要求年限但经验积累有限

**维度: 教育背景**
  - ✅ **match** (高): 软件工程本科背景，专业对口，与岗位技术方向一致
    > 原文: 2022.09-2025.06 软件工程 本科（已毕业）

**维度: 工程化意识**
  - 🔸 **gap** (中): [表达优化] 岗位要求工程化意识，简历未体现架构设计、代码规范、测试、部署等工程化实践细节

### 4. 改写建议 (rewrite_suggestions)


**改写 #1** (grade=B)
- **original**: `使用 Python、FastAPI、LangChain 构建多阶段 Agent Workflow，集成 DeepSeek 大模型实现简历智能分析，服务用户超过 5000 人次。`
- **revised**: `基于 Python、FastAPI、LangChain 构建多阶段 Agent Workflow，集成 DeepSeek 大模型 API 实现简历智能分析，服务用户超过 5000 人次。`
- **basis**: 依据：原文《使用 Python、FastAPI、LangChain 构建多阶段 Agent Workflow，集成 DeepSeek 大模型实现简历智能分析，服务用户超过 5000 人次。》；JD要求「大模型 API 集成」「LangChain」「Agent 工作流构建」；改写逻辑：将「集成 DeepSeek 大模型」明确为「集成 DeepSeek 大模型 API」，更准确对应 JD 中「大模型 API 集成」的表述，未新增任何技术栈或事实。

### 5. 事实校验 (fact_check)

- checked=1  flagged=0  violations=0

### 6. 优化任务 (optimization_advice)


**highlight** (5 条):
  - 建议突出：Python、FastAPI、LangChain 技术栈与岗位核心技能高度重合，可在简历中作为核心技术能力前置展示。
  - 建议突出：多阶段 Agent Workflow 构建经验，直接对应岗位「智能 Agent 工作流构建」职责。
  - 建议突出：DeepSeek 大模型集成与简历智能分析落地项目，体现大模型 API 集成能力。
  - 建议突出：项目服务用户超过 5000 人次，体现实际业务交付能力。
  - 建议突出：软件工程本科背景，专业与岗位技术方向一致。

**expression** (2 条):
  - 建议优化表达：原表达「集成 DeepSeek 大模型实现简历智能分析」→ 建议表达「集成 DeepSeek 大模型 API 实现简历智能分析」，更准确对应 JD 中「大模型 API 集成」的表述。
  - 建议优化表达：原表达「使用 Python、FastAPI、LangChain 构建多阶段 Agent Workflow」→ 建议表达「基于 Python、FastAPI、LangChain 构建多阶段 Agent Workflow」，「基于」比「使用」更符合技术简历的专业表达习惯。

### 7. 分类汇总

- strengths: 4 条
- weaknesses: 0 条

### 8. 自动化检查结果

- ✅ [HARD_ASSERT] api_call
- ✅ [HARD_ASSERT] data_source
- ✅ [HARD_ASSERT] match_level_fields
- ✅ [HARD_ASSERT] analysis_basis_type
- ✅ [LOGIC_CHECK] fact_check_flagged
- ✅ [LOGIC_CHECK] gap_type_tags
- ✅ [LOGIC_CHECK] rewrite_grade_AB
- ✅ [CROSS_TAB] cross_tab_consistency
- ✅ [LOGIC_CHECK] no_forbidden_content
- ✅ [LOGIC_CHECK] match_overall_min
- 👀 [SEMANTIC] SEMANTIC: 匹配等级是否符合人工期望（看 overall/ability/experience/risk 四个值）
  > 自动化无法判定，需人工看证据
- 👀 [SEMANTIC] SEMANTIC: 关键技术要求是否遗漏（对比 JD 核心关键词与 analysis_basis）
  > 自动化无法判定，需人工看证据
- 👀 [SEMANTIC] SEMANTIC: 事实幻觉检测（rewrite 新增技术/数字/项目级别）
  > 自动化无法判定，需人工看证据
- 👀 [SEMANTIC] SEMANTIC: 空泛改写检测（rewrite 是否只是加评价短句）
  > 自动化无法判定，需人工看证据
- 👀 [SEMANTIC] SEMANTIC: 跨 Tab 一致性（match_level 与 analysis_basis.overall_gap_ratio 一致）
  > 自动化无法判定，需人工看证据
- 👀 [SEMANTIC] SEMANTIC: 教育经历/时间推断正确性
  > 自动化无法判定，需人工看证据
- 👀 [SEMANTIC] SEMANTIC: weaknesses 或 supplement 的分类标记是否准确（[表达优化]/[事实待确认]/[能力缺口]）
  > 自动化无法判定，需人工看证据

### 9. 需要人工审核的具体问题

请人工审查以下 7 项语义问题（自动化无法判定）：

- 👀 **匹配等级是否符合人工期望（看 overall/ability/experience/risk 四个值）**
  > 证据: {"overall": "较高", "ability": "较强", "experience": "较弱", "risk": "需要优化"}
- 👀 **关键技术要求是否遗漏（对比 JD 核心关键词与 analysis_basis）**
  > 证据: [{"dimension": "技术栈匹配", "items": [{"type": "match", "content": "候选人技术栈与岗位要求高度重合，具备 Python、FastAPI、LangChain、DeepSeek 大模型、Agent Workflow 等核心技能", "quote": "使用 Python、FastAPI、LangChain 构建多阶段 Agent Workflow，集成 DeepSeek 大模型实现简历智能分析", "match_degree": "高"}, {"type": "match", "content": "具备 AI 大模型应用开发经验，与岗位职责中'AI 大模型应用的后端架构设计与开发'方向一致", "quote": "在字节跳动担任 AI 应用开发工程师", "match_degree": "高"}, {"type": "match", "content": "具备智能 Agent 工作流构建经验，与岗位核心技能'智能 Agent 工作流构建'匹配", "quote": "构建多阶段 Agent Workflow", "match_
- 👀 **事实幻觉检测（rewrite 新增技术/数字/项目级别）**
  > 证据: [{"original": "使用 Python、FastAPI、LangChain 构建多阶段 Agent Workflow，集成 DeepSeek 大模型实现简历智能分析，服务用户超过 5000 人次。", "revised": "基于 Python、FastAPI、LangChain 构建多阶段 Agent Workflow，集成 DeepSeek 大模型 API 实现简历智能分析，服务用户超过 5000 人次。", "basis": "依据：原文《使用 Python、FastAPI、LangChain 构建多阶段 Agent Workflow，集成 DeepSeek 大模型实现简历智能分析，服务用户超过 5000 人次。》；JD要求「大模型 API 集成」「LangChain」「Agent 工作流构建」；改写逻辑：将「集成 DeepSeek 大模型」明确为「集成 DeepSeek 大模型 API」，更准确对应 JD 中「大模型 API 集成」的表述，未新增任何技术栈或事实。", "evidence_grade": "B", "evidence": [{"source_id": 
- 👀 **空泛改写检测（rewrite 是否只是加评价短句）**
- 👀 **跨 Tab 一致性（match_level 与 analysis_basis.overall_gap_ratio 一致）**
- 👀 **教育经历/时间推断正确性**
  > 证据: 候选人技术栈与岗位要求高度重合，具备 Python、FastAPI、LangChain、DeepSeek 大模型、Agent Workflow 等核心技能 具备 AI 大模型应用开发经验，与岗位职责中'AI 大模型应用的后端架构设计与开发'方向一致 具备智能 Agent 工作流构建经验，与岗位核心技能'智能 Agent 工作流构建'匹配 具备大模型 API 集成经验，与岗位核心技能'大模型 API 集成'匹配 [事实待确认] 岗位关键词包含 GPT，当前简历未体现 GPT 大模型 API 集成实践 项目'简历智能分析系统'与岗位 AI 应用开发方向高度相关，涉及多阶段 Agent Workflow 与 DeepSeek 大模型集成 项目已落地并服务超过 5000 人次用户，具备实际业务交付能力 [表达优化] 简历项目描述较为简略，缺少后端架构设计的具体细节、成果量化指标及团队协作经历 [事实待确认] 工作年限较短，2025.07 至今约 1 年 3 个月工作经验（按当前日期 2026-10-12 计算），岗位未明确要求年限但经验积累有限 软件工程本科背景，专业对口，与岗位技术方向一致 
- 👀 **weaknesses 或 supplement 的分类标记是否准确（[表达优化]/[事实待确认]/[能力缺口]）**

---

## CASE2_核心能力缺失

**测试目的**: 汉语言文学背景申请后端工程师，无任何计算机经验，期望匹配度偏低且明确列出能力缺口
**人工期望**: `{"max_match_overall": "中等", "must_have_gap_types": ["能力缺口"], "gap_should_include": ["Python", "MySQL", "Docker"]}`

### 1. 输入（完整不截断）

**简历**:
```
李四，2020-2024 汉语言文学 本科。曾在出版社担任编辑 2 年，负责内容审核、校对、选题策划。熟悉 Word、Excel、Adobe InDesign。
```

**JD**:
```
后端工程师。要求：本科及以上学历计算机相关专业；熟练 Python、Java 或 Go；熟悉 MySQL、Redis、Docker；有高并发系统开发经验；了解分布式架构。
```

### 2. AI 综合匹配结论

- **overall**: 较低
- **ability**: 较弱
- **experience**: 较弱
- **risk**: 风险较高

### 3. 详细分析 (analysis_basis)


**维度: 后端开发能力**
  - 🔸 **gap** (低): [能力缺口] 岗位要求负责后端系统设计与开发，简历未体现任何后端开发相关经历或技能。

**维度: 高并发系统开发**
  - 🔸 **gap** (低): [能力缺口] 岗位核心技能要求高并发系统开发，当前简历未体现该技术实践。

**维度: 分布式架构设计**
  - 🔸 **gap** (低): [能力缺口] 岗位核心技能要求分布式架构设计，当前简历未体现该技术实践。

**维度: 编程语言（Python/Java/Go）**
  - 🔸 **gap** (低): [能力缺口] 岗位技术要求 Python、Java、Go，当前简历未体现上述任一语言的实践。

**维度: 数据库与中间件（MySQL/Redis）**
  - 🔸 **gap** (低): [能力缺口] 岗位技术要求 MySQL、Redis，当前简历未体现该技术实践。

**维度: 容器化（Docker）**
  - 🔸 **gap** (低): [能力缺口] 岗位技术要求 Docker，当前简历未体现该技术实践。

**维度: 学历与专业**
  - ✅ **match** (中): 岗位要求本科及以上、计算机相关专业。候选人具备本科学历，但专业为汉语言文学，非计算机相关专业。
    > 原文: 李四，2020-2024 汉语言文学 本科。

**维度: 工作经历**
  - ✅ **match** (低): 候选人具备出版社编辑工作经历，与岗位后端开发职责无直接关联。
    > 原文: 曾在出版社担任编辑 2 年，负责内容审核、校对、选题策划。

**维度: 工具技能**
  - ✅ **match** (低): 候选人熟悉办公与排版工具，与岗位技术要求无关联。
    > 原文: 熟悉 Word、Excel、Adobe InDesign。

### 4. 改写建议 (rewrite_suggestions)

_（无改写建议）_

### 5. 事实校验 (fact_check)

- checked=0  flagged=0  violations=0

### 6. 优化任务 (optimization_advice)


**highlight** (3 条):
  - 建议突出：本科学历（2020-2024 汉语言文学 本科），满足岗位'本科及以上'的学历门槛要求。
  - 建议突出：2 年出版社编辑工作经验，体现职场稳定性与内容审核、校对、选题策划的流程化工作能力。
  - 建议突出：熟练使用 Word、Excel、Adobe InDesign 等工具，体现文档处理与工具学习能力。

**expression** (2 条):
  - 建议优化表达：'曾在出版社担任编辑 2 年，负责内容审核、校对、选题策划'→'拥有 2 年出版社编辑工作经验，负责内容审核、校对及选题策划，熟悉出版流程全环节'（仅调整语序与补充原文已有职责的概括性表述，不新增事实）。
  - 建议优化表达：'熟悉 Word、Excel、Adobe InDesign'→'熟练使用 Word、Excel 进行文档处理，掌握 Adobe InDesign 排版工具'（仅细化原文已有工具的使用场景，不新增技术栈）。

### 7. 分类汇总

- strengths: 3 条
- weaknesses: 0 条

### 8. 自动化检查结果

- ✅ [HARD_ASSERT] api_call
- ✅ [HARD_ASSERT] data_source
- ✅ [HARD_ASSERT] match_level_fields
- ✅ [HARD_ASSERT] analysis_basis_type
- ✅ [LOGIC_CHECK] fact_check_flagged
- ✅ [LOGIC_CHECK] gap_type_tags
- ✅ [LOGIC_CHECK] rewrite_grade_AB
- ✅ [CROSS_TAB] cross_tab_consistency
- ✅ [LOGIC_CHECK] match_overall_max
- 👀 [SEMANTIC] SEMANTIC: 匹配等级是否符合人工期望（看 overall/ability/experience/risk 四个值）
  > 自动化无法判定，需人工看证据
- 👀 [SEMANTIC] SEMANTIC: 关键技术要求是否遗漏（对比 JD 核心关键词与 analysis_basis）
  > 自动化无法判定，需人工看证据
- 👀 [SEMANTIC] SEMANTIC: 事实幻觉检测（rewrite 新增技术/数字/项目级别）
  > 自动化无法判定，需人工看证据
- 👀 [SEMANTIC] SEMANTIC: 空泛改写检测（rewrite 是否只是加评价短句）
  > 自动化无法判定，需人工看证据
- 👀 [SEMANTIC] SEMANTIC: 跨 Tab 一致性（match_level 与 analysis_basis.overall_gap_ratio 一致）
  > 自动化无法判定，需人工看证据
- 👀 [SEMANTIC] SEMANTIC: 教育经历/时间推断正确性
  > 自动化无法判定，需人工看证据
- 👀 [SEMANTIC] SEMANTIC: weaknesses 或 supplement 的分类标记是否准确（[表达优化]/[事实待确认]/[能力缺口]）
  > 自动化无法判定，需人工看证据

### 9. 需要人工审核的具体问题

请人工审查以下 7 项语义问题（自动化无法判定）：

- 👀 **匹配等级是否符合人工期望（看 overall/ability/experience/risk 四个值）**
  > 证据: {"overall": "较低", "ability": "较弱", "experience": "较弱", "risk": "风险较高"}
- 👀 **关键技术要求是否遗漏（对比 JD 核心关键词与 analysis_basis）**
  > 证据: [{"dimension": "后端开发能力", "items": [{"type": "gap", "content": "[能力缺口] 岗位要求负责后端系统设计与开发，简历未体现任何后端开发相关经历或技能。", "match_degree": "低"}]}, {"dimension": "高并发系统开发", "items": [{"type": "gap", "content": "[能力缺口] 岗位核心技能要求高并发系统开发，当前简历未体现该技术实践。", "match_degree": "低"}]}]
- 👀 **事实幻觉检测（rewrite 新增技术/数字/项目级别）**
  > 证据: []
- 👀 **空泛改写检测（rewrite 是否只是加评价短句）**
- 👀 **跨 Tab 一致性（match_level 与 analysis_basis.overall_gap_ratio 一致）**
- 👀 **教育经历/时间推断正确性**
  > 证据: [能力缺口] 岗位要求负责后端系统设计与开发，简历未体现任何后端开发相关经历或技能。 [能力缺口] 岗位核心技能要求高并发系统开发，当前简历未体现该技术实践。 [能力缺口] 岗位核心技能要求分布式架构设计，当前简历未体现该技术实践。 [能力缺口] 岗位技术要求 Python、Java、Go，当前简历未体现上述任一语言的实践。 [能力缺口] 岗位技术要求 MySQL、Redis，当前简历未体现该技术实践。 [能力缺口] 岗位技术要求 Docker，当前简历未体现该技术实践。 岗位要求本科及以上、计算机相关专业。候选人具备本科学历，但专业为汉语言文学，非计算机相关专业。 候选人具备出版社编辑工作经历，与岗位后端开发职责无直接关联。 候选人熟悉办公与排版工具，与岗位技术要求无关联。
- 👀 **weaknesses 或 supplement 的分类标记是否准确（[表达优化]/[事实待确认]/[能力缺口]）**

---

## CASE3_跨岗位匹配

**测试目的**: 工业设计背景的产品经理应聘 AI 产品经理，产品经验相关但 AI 方向是新领域
**人工期望**: `{"must_have_gap_types": ["事实待确认"], "should_not_have_gap_types": ["能力缺口"]}`

### 1. 输入（完整不截断）

**简历**:
```
王五，2021-2025 工业设计 本科。曾在智能家居公司担任产品经理 2 年，负责硬件产品定义、用户研究、PRD 撰写、与设计/供应链团队协调。
```

**JD**:
```
产品经理（AI 方向）。要求：本科及以上学历；2-5 年产品经理经验；熟悉用户研究、PRD 撰写、产品迭代方法；有 AI/智能硬件/数据产品经验优先。
```

### 2. AI 综合匹配结论

- **overall**: 中等
- **ability**: 中等
- **experience**: 中等
- **risk**: 需要优化

### 3. 详细分析 (analysis_basis)


**维度: 岗位职责匹配**
  - ✅ **match** (中): 简历体现用户研究、PRD撰写、产品迭代相关职责，与JD核心职责方向一致
    > 原文: 负责硬件产品定义、用户研究、PRD 撰写、与设计/供应链团队协调
  - 🔸 **gap** (低): [事实待确认] JD要求负责AI方向产品的规划与迭代，当前简历未体现AI产品规划与迭代的具体实践

**维度: 核心技能匹配**
  - ✅ **match** (高): 简历明确体现用户研究技能
    > 原文: 用户研究
  - ✅ **match** (高): 简历明确体现PRD撰写技能
    > 原文: PRD 撰写
  - 🔸 **gap** (低): [事实待确认] JD要求产品迭代方法，当前简历未体现具体产品迭代方法的实践描述

**维度: 技术要求匹配**
  - 🔸 **gap** (低): [能力缺口] JD要求AI技术方向，当前简历未体现该技术实践
  - ✅ **match** (中): 简历体现智能家居硬件产品经验，与智能硬件方向匹配
    > 原文: 曾在智能家居公司担任产品经理 2 年，负责硬件产品定义
  - 🔸 **gap** (低): [能力缺口] JD要求数据产品经验，当前简历未体现该技术实践

**维度: 经验年限与学历**
  - ✅ **match** (高): 简历体现2年产品经理经验，符合JD 2-5年经验要求
    > 原文: 曾在智能家居公司担任产品经理 2 年
  - ✅ **match** (高): 简历体现本科学历，符合JD本科及以上要求
    > 原文: 2021-2025 工业设计 本科
  - 🔸 **gap** (低): [事实待确认] 简历教育时间线为2021-2025，工作经历为2年产品经理，时间线存在重叠，需确认实际工作起始时间与毕业状态

### 4. 改写建议 (rewrite_suggestions)


**改写 #1** (grade=B)
- **original**: `曾在智能家居公司担任产品经理 2 年，负责硬件产品定义、用户研究、PRD 撰写、与设计/供应链团队协调。`
- **revised**: `智能家居公司 | 产品经理（2年）：负责硬件产品定义、用户研究与PRD撰写，协调设计/供应链团队推进产品落地。`
- **basis**: 依据：原文《曾在智能家居公司担任产品经理 2 年，负责硬件产品定义、用户研究、PRD 撰写、与设计/供应链团队协调》；JD要求用户研究、PRD撰写、产品迭代方法，以及智能硬件方向；改写逻辑：将原文信息按'公司-岗位-职责'结构重新组织，用分点式表达提升可读性，并将'与设计/供应链团队协调'调整为'协调设计/供应链团队推进产品落地'，使职责逻辑更清晰，未新增任何事实。

### 5. 事实校验 (fact_check)

- checked=1  flagged=0  violations=0

### 6. 优化任务 (optimization_advice)


**highlight** (3 条):
  - 建议突出：智能家居硬件产品经理2年经验，与JD智能硬件方向直接匹配，建议在简历开头或摘要中优先呈现。
  - 建议突出：用户研究与PRD撰写两项核心技能已在原文中明确体现，建议在技能栏或工作经历中单独列出，便于HR快速识别。
  - 建议突出：工业设计本科背景与硬件产品方向相关，建议保留并说明其与产品经理岗位的关联性。

**expression** (2 条):
  - 建议优化表达：'负责硬件产品定义、用户研究、PRD 撰写、与设计/供应链团队协调' → '负责硬件产品定义、用户研究与PRD撰写，协调设计/供应链团队推进产品落地'（提升职责逻辑与专业度）
  - 建议优化表达：'曾在智能家居公司担任产品经理 2 年' → '智能家居公司 | 产品经理（2年）'（更符合简历标准格式，便于快速识别）

### 7. 分类汇总

- strengths: 3 条
- weaknesses: 0 条

### 8. 自动化检查结果

- ✅ [HARD_ASSERT] api_call
- ✅ [HARD_ASSERT] data_source
- ✅ [HARD_ASSERT] match_level_fields
- ✅ [HARD_ASSERT] analysis_basis_type
- ✅ [LOGIC_CHECK] fact_check_flagged
- ✅ [LOGIC_CHECK] gap_type_tags
- ✅ [LOGIC_CHECK] rewrite_grade_AB
- ✅ [CROSS_TAB] cross_tab_consistency
- 👀 [SEMANTIC] SEMANTIC: 匹配等级是否符合人工期望（看 overall/ability/experience/risk 四个值）
  > 自动化无法判定，需人工看证据
- 👀 [SEMANTIC] SEMANTIC: 关键技术要求是否遗漏（对比 JD 核心关键词与 analysis_basis）
  > 自动化无法判定，需人工看证据
- 👀 [SEMANTIC] SEMANTIC: 事实幻觉检测（rewrite 新增技术/数字/项目级别）
  > 自动化无法判定，需人工看证据
- 👀 [SEMANTIC] SEMANTIC: 空泛改写检测（rewrite 是否只是加评价短句）
  > 自动化无法判定，需人工看证据
- 👀 [SEMANTIC] SEMANTIC: 跨 Tab 一致性（match_level 与 analysis_basis.overall_gap_ratio 一致）
  > 自动化无法判定，需人工看证据
- 👀 [SEMANTIC] SEMANTIC: 教育经历/时间推断正确性
  > 自动化无法判定，需人工看证据
- 👀 [SEMANTIC] SEMANTIC: weaknesses 或 supplement 的分类标记是否准确（[表达优化]/[事实待确认]/[能力缺口]）
  > 自动化无法判定，需人工看证据

### 9. 需要人工审核的具体问题

请人工审查以下 7 项语义问题（自动化无法判定）：

- 👀 **匹配等级是否符合人工期望（看 overall/ability/experience/risk 四个值）**
  > 证据: {"overall": "中等", "ability": "中等", "experience": "中等", "risk": "需要优化"}
- 👀 **关键技术要求是否遗漏（对比 JD 核心关键词与 analysis_basis）**
  > 证据: [{"dimension": "岗位职责匹配", "items": [{"type": "match", "content": "简历体现用户研究、PRD撰写、产品迭代相关职责，与JD核心职责方向一致", "quote": "负责硬件产品定义、用户研究、PRD 撰写、与设计/供应链团队协调", "match_degree": "中"}, {"type": "gap", "content": "[事实待确认] JD要求负责AI方向产品的规划与迭代，当前简历未体现AI产品规划与迭代的具体实践", "match_degree": "低"}]}, {"dimension": "核心技能匹配", "items": [{"type": "match", "content": "简历明确体现用户研究技能", "quote": "用户研究", "match_degree": "高"}, {"type": "match", "content": "简历明确体现PRD撰写技能", "quote": "PRD 撰写", "match_degree": "高"}, {"type": "gap", "conte
- 👀 **事实幻觉检测（rewrite 新增技术/数字/项目级别）**
  > 证据: [{"original": "曾在智能家居公司担任产品经理 2 年，负责硬件产品定义、用户研究、PRD 撰写、与设计/供应链团队协调。", "revised": "智能家居公司 | 产品经理（2年）：负责硬件产品定义、用户研究与PRD撰写，协调设计/供应链团队推进产品落地。", "basis": "依据：原文《曾在智能家居公司担任产品经理 2 年，负责硬件产品定义、用户研究、PRD 撰写、与设计/供应链团队协调》；JD要求用户研究、PRD撰写、产品迭代方法，以及智能硬件方向；改写逻辑：将原文信息按'公司-岗位-职责'结构重新组织，用分点式表达提升可读性，并将'与设计/供应链团队协调'调整为'协调设计/供应链团队推进产品落地'，使职责逻辑更清晰，未新增任何事实。", "evidence_grade": "B", "evidence": [{"source_id": "resume_b4ff9bcf968e_0", "original_text": "王五，2021-2025 工业设计 本科。曾在智能家居公司担任产品经理 2 年，负责硬件产品定义、用户研究、PRD 撰写、与设计/供应链团队
- 👀 **空泛改写检测（rewrite 是否只是加评价短句）**
- 👀 **跨 Tab 一致性（match_level 与 analysis_basis.overall_gap_ratio 一致）**
- 👀 **教育经历/时间推断正确性**
  > 证据: 简历体现用户研究、PRD撰写、产品迭代相关职责，与JD核心职责方向一致 [事实待确认] JD要求负责AI方向产品的规划与迭代，当前简历未体现AI产品规划与迭代的具体实践 简历明确体现用户研究技能 简历明确体现PRD撰写技能 [事实待确认] JD要求产品迭代方法，当前简历未体现具体产品迭代方法的实践描述 [能力缺口] JD要求AI技术方向，当前简历未体现该技术实践 简历体现智能家居硬件产品经验，与智能硬件方向匹配 [能力缺口] JD要求数据产品经验，当前简历未体现该技术实践 简历体现2年产品经理经验，符合JD 2-5年经验要求 简历体现本科学历，符合JD本科及以上要求 [事实待确认] 简历教育时间线为2021-2025，工作经历为2年产品经理，时间线存在重叠，需确认实际工作起始时间与毕业状态
- 👀 **weaknesses 或 supplement 的分类标记是否准确（[表达优化]/[事实待确认]/[能力缺口]）**

---

## CASE4_经历不足_在读无经验

**测试目的**: 计算机本科在读，无任何工作/实习经历，期望匹配度低但不能判'能力缺口'
**人工期望**: `{"must_not_have_fake": ["已毕业"], "must_have_gap_types": ["事实待确认"], "max_match_overall": "中等"}`

### 1. 输入（完整不截断）

**简历**:
```
赵六，2025.09 至今 计算机科学与技术 本科在读。已修课程：Python 程序设计、数据结构、操作系统。自学过 LangChain、FastAPI 基础框架。
```

**JD**:
```
Python 后端工程师。要求：本科及以上学历计算机相关专业；1-3 年 Python 开发经验；熟悉 Web 框架（FastAPI/Django）；有实际项目部署经历。
```

### 2. AI 综合匹配结论

- **overall**: 较低
- **ability**: 较弱
- **experience**: 较弱
- **risk**: 风险较高

### 3. 详细分析 (analysis_basis)


**维度: 技术栈匹配**
  - ✅ **match** (中): 简历体现 Python 技术栈，与 JD 要求的 Python 后端开发方向一致
    > 原文: 已修课程：Python 程序设计、数据结构、操作系统。自学过 LangChain、FastAPI 基础框架。
  - ✅ **match** (低): 简历体现 FastAPI 学习经历，与 JD 要求的 Web 框架应用部分吻合
    > 原文: 自学过 LangChain、FastAPI 基础框架。
  - 🔸 **gap** (低): [能力缺口] 当前简历未体现 Django 实践，JD 明确要求 FastAPI 或 Django 等 Web 框架应用能力
  - 🔸 **gap** (低): [能力缺口] 当前简历未体现项目部署相关实践，JD 要求参与实际项目的部署与上线工作

**维度: 项目与工程经验**
  - 🔸 **gap** (低): [能力缺口] 简历项目经历为空，无法证明具备后端开发的实际工程经验
  - 🔸 **gap** (低): [事实待确认] JD 要求 1-3 年经验，简历未体现任何实习或工作起始时间，工作年限待确认

**维度: 教育背景**
  - ✅ **match** (中): 计算机科学与技术专业本科在读，与 JD 要求的计算机相关专业、本科及以上学历方向一致
    > 原文: 赵六，2025.09 至今 计算机科学与技术 本科在读。
  - 🔸 **gap** (低): [事实待确认] 简历标注 2025.09 至今本科在读，未给出预计毕业时间，毕业状态与可到岗时间待确认

### 4. 改写建议 (rewrite_suggestions)


**改写 #1** (grade=B)
- **original**: `已修课程：Python 程序设计、数据结构、操作系统。`
- **revised**: `已修课程：Python 程序设计、数据结构、操作系统（与 Python 后端开发方向相关的计算机核心课程）。`
- **basis**: 依据：原文《已修课程：Python 程序设计、数据结构、操作系统。》；JD要求：Python 后端开发、计算机相关专业；改写逻辑：在不新增事实的前提下，将课程与岗位方向建立明确关联，帮助招聘方快速识别课程与后端开发的相关性，提升信息组织清晰度。
- ⚠️ **fact_warning**: `疑似新增技术: python后端开发`

**改写 #2** (grade=B)
- **original**: `自学过 LangChain、FastAPI 基础框架。`
- **revised**: `自学过 FastAPI 基础框架，了解 Python Web 框架的基本使用；同时自学过 LangChain。`
- **basis**: 依据：原文《自学过 LangChain、FastAPI 基础框架。》；JD要求：FastAPI、Django、Web 框架应用；改写逻辑：将 FastAPI 前置并明确其属于 Python Web 框架，使与 JD 核心关键词的对应关系更直接，同时保留 LangChain 的原有信息，不新增任何技术栈或事实。
- ⚠️ **fact_warning**: `疑似新增技术: web框架`

### 5. 事实校验 (fact_check)

- checked=2  flagged=2  violations=2
> ⚠️ **需要人工判断拦截是否合理**（flagged>0 不是自动 FAIL，保守误报和合理拦截都可能）

### 6. 优化任务 (optimization_advice)


**highlight** (3 条):
  - 建议突出：计算机科学与技术本科在读，专业方向与 JD 要求的计算机相关专业一致（原文：赵六，2025.09 至今 计算机科学与技术 本科在读）。
  - 建议突出：已修 Python 程序设计、数据结构、操作系统等核心课程，具备 Python 与计算机基础（原文：已修课程：Python 程序设计、数据结构、操作系统）。
  - 建议突出：主动自学 FastAPI 基础框架，与 JD 要求的 Python Web 框架方向有重合（原文：自学过 LangChain、FastAPI 基础框架）。

**expression** (2 条):
  - 建议优化表达：原表达“自学过 LangChain、FastAPI 基础框架。”→建议表达“自学过 FastAPI 基础框架，了解 Python Web 框架的基本使用；同时自学过 LangChain。”
  - 建议优化表达：原表达“已修课程：Python 程序设计、数据结构、操作系统。”→建议表达“已修课程：Python 程序设计、数据结构、操作系统（与 Python 后端开发方向相关的计算机核心课程）。”

### 7. 分类汇总

- strengths: 3 条
- weaknesses: 0 条

### 8. 自动化检查结果

- ✅ [HARD_ASSERT] api_call
- ✅ [HARD_ASSERT] data_source
- ✅ [HARD_ASSERT] match_level_fields
- ✅ [HARD_ASSERT] analysis_basis_type
- 👀 [LOGIC_CHECK] fact_check_flagged
  > flagged=2, violations=2, checked=2 — 人工判断拦截是否合理
- ✅ [LOGIC_CHECK] gap_type_tags
- ✅ [LOGIC_CHECK] rewrite_grade_AB
- ✅ [CROSS_TAB] cross_tab_consistency
- ✅ [LOGIC_CHECK] no_forbidden_content
- ✅ [LOGIC_CHECK] match_overall_max
- 👀 [SEMANTIC] SEMANTIC: 匹配等级是否符合人工期望（看 overall/ability/experience/risk 四个值）
  > 自动化无法判定，需人工看证据
- 👀 [SEMANTIC] SEMANTIC: 关键技术要求是否遗漏（对比 JD 核心关键词与 analysis_basis）
  > 自动化无法判定，需人工看证据
- 👀 [SEMANTIC] SEMANTIC: 事实幻觉检测（rewrite 新增技术/数字/项目级别）
  > 自动化无法判定，需人工看证据
- 👀 [SEMANTIC] SEMANTIC: 空泛改写检测（rewrite 是否只是加评价短句）
  > 自动化无法判定，需人工看证据
- 👀 [SEMANTIC] SEMANTIC: 跨 Tab 一致性（match_level 与 analysis_basis.overall_gap_ratio 一致）
  > 自动化无法判定，需人工看证据
- 👀 [SEMANTIC] SEMANTIC: 教育经历/时间推断正确性
  > 自动化无法判定，需人工看证据
- 👀 [SEMANTIC] SEMANTIC: weaknesses 或 supplement 的分类标记是否准确（[表达优化]/[事实待确认]/[能力缺口]）
  > 自动化无法判定，需人工看证据

### 9. 需要人工审核的具体问题

请人工审查以下 7 项语义问题（自动化无法判定）：

- 👀 **fact_check_flagged**
  > 证据: 疑似新增技术: python后端开发; 疑似新增技术: web框架
- 👀 **匹配等级是否符合人工期望（看 overall/ability/experience/risk 四个值）**
  > 证据: {"overall": "较低", "ability": "较弱", "experience": "较弱", "risk": "风险较高"}
- 👀 **关键技术要求是否遗漏（对比 JD 核心关键词与 analysis_basis）**
  > 证据: [{"dimension": "技术栈匹配", "items": [{"type": "match", "content": "简历体现 Python 技术栈，与 JD 要求的 Python 后端开发方向一致", "quote": "已修课程：Python 程序设计、数据结构、操作系统。自学过 LangChain、FastAPI 基础框架。", "match_degree": "中"}, {"type": "match", "content": "简历体现 FastAPI 学习经历，与 JD 要求的 Web 框架应用部分吻合", "quote": "自学过 LangChain、FastAPI 基础框架。", "match_degree": "低"}, {"type": "gap", "content": "[能力缺口] 当前简历未体现 Django 实践，JD 明确要求 FastAPI 或 Django 等 Web 框架应用能力", "match_degree": "低"}, {"type": "gap", "content": "[能力缺口] 当前简历未体现项目部署相关实践，JD 要
- 👀 **事实幻觉检测（rewrite 新增技术/数字/项目级别）**
  > 证据: [{"original": "已修课程：Python 程序设计、数据结构、操作系统。", "revised": "已修课程：Python 程序设计、数据结构、操作系统（与 Python 后端开发方向相关的计算机核心课程）。", "basis": "依据：原文《已修课程：Python 程序设计、数据结构、操作系统。》；JD要求：Python 后端开发、计算机相关专业；改写逻辑：在不新增事实的前提下，将课程与岗位方向建立明确关联，帮助招聘方快速识别课程与后端开发的相关性，提升信息组织清晰度。", "evidence_grade": "B", "fact_warning": "疑似新增技术: python后端开发", "evidence": [{"source_id": "resume_51cc6a191187_0", "original_text": "Python 程序设计、数据结构、操作系统。", "evidence_index": 1, "match_score": 0.2857, "source_type": "resume"}]}, {"original": "自学过 LangC
- 👀 **空泛改写检测（rewrite 是否只是加评价短句）**
- 👀 **跨 Tab 一致性（match_level 与 analysis_basis.overall_gap_ratio 一致）**
- 👀 **教育经历/时间推断正确性**
  > 证据: 简历体现 Python 技术栈，与 JD 要求的 Python 后端开发方向一致 简历体现 FastAPI 学习经历，与 JD 要求的 Web 框架应用部分吻合 [能力缺口] 当前简历未体现 Django 实践，JD 明确要求 FastAPI 或 Django 等 Web 框架应用能力 [能力缺口] 当前简历未体现项目部署相关实践，JD 要求参与实际项目的部署与上线工作 [能力缺口] 简历项目经历为空，无法证明具备后端开发的实际工程经验 [事实待确认] JD 要求 1-3 年经验，简历未体现任何实习或工作起始时间，工作年限待确认 计算机科学与技术专业本科在读，与 JD 要求的计算机相关专业、本科及以上学历方向一致 [事实待确认] 简历标注 2025.09 至今本科在读，未给出预计毕业时间，毕业状态与可到岗时间待确认
- 👀 **weaknesses 或 supplement 的分类标记是否准确（[表达优化]/[事实待确认]/[能力缺口]）**

---

## CASE5_已毕业确认

**测试目的**: 简历明确写'已毕业'，AI 不能出现'尚未毕业'判断
**人工期望**: `{"must_not_have_fake": ["尚未毕业", "本科在读", "仍在校"]}`

### 1. 输入（完整不截断）

**简历**:
```
孙七，2020.09-2024.06 计算机科学 本科（2024 年 6 月已毕业）。2024.07 至今 在某互联网公司担任后端开发工程师，使用 Go 和 MySQL。
```

**JD**:
```
后端工程师。要求：本科及以上学历计算机相关专业；熟悉 Go 或 Python；有微服务开发经验。
```

### 2. AI 综合匹配结论

- **overall**: 中等
- **ability**: 中等
- **experience**: 中等
- **risk**: 需要优化

### 3. 详细分析 (analysis_basis)


**维度: 技术栈匹配**
  - ✅ **match** (高): 候选人掌握 Go 语言，与 JD 技术要求中的 Go 匹配。
    > 原文: 使用 Go 和 MySQL
  - 🔸 **gap** (低): [能力缺口] JD 技术要求中的 Python，当前简历未体现该技术实践。
  - 🔸 **gap** (低): [事实待确认] JD 核心技能与技术要求中的微服务开发，当前简历未体现该技术实践。

**维度: 岗位职责匹配**
  - ✅ **match** (中): 候选人拥有互联网公司后端开发工程师工作经历，与 JD 岗位职责中后端系统设计开发方向相关。
    > 原文: 在某互联网公司担任后端开发工程师
  - 🔸 **gap** (低): [事实待确认] JD 岗位职责中参与微服务架构的构建与维护，当前简历未体现该技术实践。

**维度: 学历与专业**
  - ✅ **match** (高): 候选人学历为本科，专业为计算机科学，与 JD 岗位关键词中本科及以上、计算机相关专业匹配。
    > 原文: 2020.09-2024.06 计算机科学 本科

**维度: 毕业与到岗状态**
  - ✅ **match** (高): 简历明确标注 2024 年 6 月已毕业，可立即全职到岗。
    > 原文: 2024 年 6 月已毕业

**维度: 工作年限**
  - ✅ **match** (中): 简历显示 2024.07 至今从事后端开发工作，按当前日期 2026-10-12 计算约 2 年 3 个月工作经验。
    > 原文: 2024.07 至今 在某互联网公司担任后端开发工程师

**维度: 项目经历**
  - 🔸 **gap** (低): [表达优化] 简历缺少具体项目经历描述，无法评估候选人在后端系统设计与微服务方面的实际项目经验。

### 4. 改写建议 (rewrite_suggestions)


**改写 #1** (grade=B)
- **original**: `2024.07 至今 在某互联网公司担任后端开发工程师，使用 Go 和 MySQL。`
- **revised**: `2024.07 至今 在某互联网公司担任后端开发工程师，负责后端开发工作，技术栈为 Go 和 MySQL。`
- **basis**: 依据：原文《2024.07 至今 在某互联网公司担任后端开发工程师，使用 Go 和 MySQL》；JD要求：后端开发、Go；改写逻辑：将原文中隐含的岗位职责（后端开发）显性化，使技术栈与岗位职责的关联更清晰，未新增任何事实。

### 5. 事实校验 (fact_check)

- checked=1  flagged=0  violations=0

### 6. 优化任务 (optimization_advice)


**highlight** (3 条):
  - 建议突出：Go 语言与 JD 技术要求直接匹配，可在简历中明确标注掌握 Go 语言。
  - 建议突出：2024 年 6 月已毕业，可立即全职到岗，建议在简历中保留该信息。
  - 建议突出：本科为计算机科学专业，符合 JD 对本科及以上、计算机相关专业的要求。

**expression** (1 条):
  - 建议优化表达：使用 Go 和 MySQL → 负责后端开发工作，技术栈为 Go 和 MySQL（使职责与技术栈关联更清晰）

### 7. 分类汇总

- strengths: 4 条
- weaknesses: 0 条

### 8. 自动化检查结果

- ✅ [HARD_ASSERT] api_call
- ✅ [HARD_ASSERT] data_source
- ✅ [HARD_ASSERT] match_level_fields
- ✅ [HARD_ASSERT] analysis_basis_type
- ✅ [LOGIC_CHECK] fact_check_flagged
- ✅ [LOGIC_CHECK] gap_type_tags
- ✅ [LOGIC_CHECK] rewrite_grade_AB
- ✅ [CROSS_TAB] cross_tab_consistency
- ✅ [LOGIC_CHECK] no_forbidden_content
- 👀 [SEMANTIC] SEMANTIC: 匹配等级是否符合人工期望（看 overall/ability/experience/risk 四个值）
  > 自动化无法判定，需人工看证据
- 👀 [SEMANTIC] SEMANTIC: 关键技术要求是否遗漏（对比 JD 核心关键词与 analysis_basis）
  > 自动化无法判定，需人工看证据
- 👀 [SEMANTIC] SEMANTIC: 事实幻觉检测（rewrite 新增技术/数字/项目级别）
  > 自动化无法判定，需人工看证据
- 👀 [SEMANTIC] SEMANTIC: 空泛改写检测（rewrite 是否只是加评价短句）
  > 自动化无法判定，需人工看证据
- 👀 [SEMANTIC] SEMANTIC: 跨 Tab 一致性（match_level 与 analysis_basis.overall_gap_ratio 一致）
  > 自动化无法判定，需人工看证据
- 👀 [SEMANTIC] SEMANTIC: 教育经历/时间推断正确性
  > 自动化无法判定，需人工看证据
- 👀 [SEMANTIC] SEMANTIC: weaknesses 或 supplement 的分类标记是否准确（[表达优化]/[事实待确认]/[能力缺口]）
  > 自动化无法判定，需人工看证据

### 9. 需要人工审核的具体问题

请人工审查以下 7 项语义问题（自动化无法判定）：

- 👀 **匹配等级是否符合人工期望（看 overall/ability/experience/risk 四个值）**
  > 证据: {"overall": "中等", "ability": "中等", "experience": "中等", "risk": "需要优化"}
- 👀 **关键技术要求是否遗漏（对比 JD 核心关键词与 analysis_basis）**
  > 证据: [{"dimension": "技术栈匹配", "items": [{"type": "match", "content": "候选人掌握 Go 语言，与 JD 技术要求中的 Go 匹配。", "quote": "使用 Go 和 MySQL", "match_degree": "高"}, {"type": "gap", "content": "[能力缺口] JD 技术要求中的 Python，当前简历未体现该技术实践。", "match_degree": "低"}, {"type": "gap", "content": "[事实待确认] JD 核心技能与技术要求中的微服务开发，当前简历未体现该技术实践。", "match_degree": "低"}]}, {"dimension": "岗位职责匹配", "items": [{"type": "match", "content": "候选人拥有互联网公司后端开发工程师工作经历，与 JD 岗位职责中后端系统设计开发方向相关。", "quote": "在某互联网公司担任后端开发工程师", "match_degree": "中"}, {"type
- 👀 **事实幻觉检测（rewrite 新增技术/数字/项目级别）**
  > 证据: [{"original": "2024.07 至今 在某互联网公司担任后端开发工程师，使用 Go 和 MySQL。", "revised": "2024.07 至今 在某互联网公司担任后端开发工程师，负责后端开发工作，技术栈为 Go 和 MySQL。", "basis": "依据：原文《2024.07 至今 在某互联网公司担任后端开发工程师，使用 Go 和 MySQL》；JD要求：后端开发、Go；改写逻辑：将原文中隐含的岗位职责（后端开发）显性化，使技术栈与岗位职责的关联更清晰，未新增任何事实。", "evidence_grade": "B", "evidence": [{"source_id": "resume_ef7b3b8a7e39_0", "original_text": "2024.07 至今 在某互联网公司担任后端开发工程师，使用 Go 和 MySQL。", "evidence_index": 1, "match_score": 1.0, "source_type": "resume"}]}]
- 👀 **空泛改写检测（rewrite 是否只是加评价短句）**
- 👀 **跨 Tab 一致性（match_level 与 analysis_basis.overall_gap_ratio 一致）**
- 👀 **教育经历/时间推断正确性**
  > 证据: 候选人掌握 Go 语言，与 JD 技术要求中的 Go 匹配。 [能力缺口] JD 技术要求中的 Python，当前简历未体现该技术实践。 [事实待确认] JD 核心技能与技术要求中的微服务开发，当前简历未体现该技术实践。 候选人拥有互联网公司后端开发工程师工作经历，与 JD 岗位职责中后端系统设计开发方向相关。 [事实待确认] JD 岗位职责中参与微服务架构的构建与维护，当前简历未体现该技术实践。 候选人学历为本科，专业为计算机科学，与 JD 岗位关键词中本科及以上、计算机相关专业匹配。 简历明确标注 2024 年 6 月已毕业，可立即全职到岗。 简历显示 2024.07 至今从事后端开发工作，按当前日期 2026-10-12 计算约 2 年 3 个月工作经验。 [表达优化] 简历缺少具体项目经历描述，无法评估候选人在后端系统设计与微服务方面的实际项目经验。
- 👀 **weaknesses 或 supplement 的分类标记是否准确（[表达优化]/[事实待确认]/[能力缺口]）**

---

## CASE6_表达充分不应硬凑改写

**测试目的**: 简历描述已清晰专业，rewrite_suggestions 应该为空或很少
**人工期望**: `{"rewrite_count_zero_or_few": true}`

### 1. 输入（完整不截断）

**简历**:
```
周八，负责开发 AI Agent Workflow 系统，采用 LangChain 编排四阶段 Agent，集成 DeepSeek V3 大模型作为推理引擎，通过 FAISS 向量索引检索岗位知识库，实现智能简历分析与改写建议生成，服务用户 5000+。
```

**JD**:
```
AI 应用开发工程师。职责：负责 AI Agent 系统架构设计与开发；基于 LangChain 等框架构建智能工作流；集成主流大模型 API；要求：熟悉 LangChain、Python、FastAPI、DeepSeek。
```

### 2. AI 综合匹配结论

- **overall**: 中等
- **ability**: 较强
- **experience**: 待确认
- **risk**: 需要优化

### 3. 详细分析 (analysis_basis)


**维度: AI Agent 系统架构设计**
  - ✅ **match** (高): 简历体现候选人负责开发 AI Agent Workflow 系统，采用 LangChain 编排四阶段 Agent，具备 AI Agent 系统编排与开发的直接经验，与岗位核心职责高度吻合。
    > 原文: 负责开发 AI Agent Workflow 系统，采用 LangChain 编排四阶段 Agent

**维度: 智能工作流构建**
  - ✅ **match** (高): 简历体现候选人通过 LangChain 编排四阶段 Agent 实现智能简历分析与改写建议生成，具备智能工作流构建的实践经验。
    > 原文: 采用 LangChain 编排四阶段 Agent……实现智能简历分析与改写建议生成

**维度: 大模型 API 集成**
  - ✅ **match** (高): 简历体现候选人集成 DeepSeek V3 大模型作为推理引擎，具备大模型集成经验，且与岗位技术栈中 DeepSeek 要求直接对应。
    > 原文: 集成 DeepSeek V3 大模型作为推理引擎

**维度: LangChain**
  - ✅ **match** (高): 简历明确体现 LangChain 使用经验，与岗位技术要求直接匹配。
    > 原文: 采用 LangChain 编排四阶段 Agent

**维度: Python**
  - 🔸 **gap** (低): [事实待确认] 岗位技术要求 Python，简历技术栈与项目描述中未明确提及 Python，当前简历未体现该技术实践，需候选人确认。

**维度: FastAPI**
  - 🔸 **gap** (低): [能力缺口] 岗位技术要求 FastAPI，简历技术栈与项目描述中均未体现，当前简历未体现该技术实践。

**维度: DeepSeek**
  - ✅ **match** (高): 简历明确体现 DeepSeek V3 集成经验，与岗位技术要求匹配。
    > 原文: 集成 DeepSeek V3 大模型作为推理引擎

**维度: 项目成果与量化指标**
  - 🔸 **gap** (中): [表达优化] 简历仅提及服务用户 5000+，未体现性能提升、准确率等具体工作成果指标，成果表述可进一步量化以增强说服力。

**维度: 教育背景与工作年限**
  - 🔸 **gap** (低): [事实待确认] 简历未提供教育背景、毕业时间及工作起始时间，毕业状态与工作年限均待确认，无法评估经验积累程度。

### 4. 改写建议 (rewrite_suggestions)


**改写 #1** (grade=B)
- **original**: `负责开发 AI Agent Workflow 系统，采用 LangChain 编排四阶段 Agent，集成 DeepSeek V3 大模型作为推理引擎，通过 FAISS 向量索引检索岗位知识库，实现智能简历分析与改写建议生成，服务用户 5000+。`
- **revised**: `负责开发 AI Agent Workflow 系统：基于 LangChain 编排四阶段 Agent 智能工作流，集成 DeepSeek V3 大模型作为推理引擎，通过 FAISS 向量索引检索岗位知识库，实现智能简历分析与改写建议生成，服务用户 5000+。`
- **basis**: 依据：原文《负责开发 AI Agent Workflow 系统，采用 LangChain 编排四阶段 Agent，集成 DeepSeek V3 大模型作为推理引擎，通过 FAISS 向量索引检索岗位知识库，实现智能简历分析与改写建议生成，服务用户 5000+。》；JD要求：AI Agent 系统架构设计、智能工作流构建、LangChain、DeepSeek；改写逻辑：将原文一句话拆分为“系统名称 + 冒号 + 技术实现链路”的结构，使“AI Agent Workflow 系统”作为核心项目名前置突出，同时将“编排四阶段 Agent”明确为“编排四阶段 Agent 智能工作流”，自然融入 JD 关键词“智能工作流”，不新增任何技术栈或事实。
- ⚠️ **fact_warning**: `疑似新增技术: aiagent系统架构设计`

### 5. 事实校验 (fact_check)

- checked=1  flagged=1  violations=1
> ⚠️ **需要人工判断拦截是否合理**（flagged>0 不是自动 FAIL，保守误报和合理拦截都可能）

### 6. 优化任务 (optimization_advice)


**highlight** (5 条):
  - 建议突出：AI Agent Workflow 系统开发经验，明确写出“负责开发 AI Agent Workflow 系统”，与岗位核心职责“AI Agent 系统架构设计与开发”直接对应。
  - 建议突出：LangChain 编排四阶段 Agent 的智能工作流构建经验，与岗位核心技能“智能工作流构建”直接对应。
  - 建议突出：DeepSeek V3 大模型集成经验，与岗位技术要求“DeepSeek”及“大模型 API 集成”直接对应。
  - 建议突出：FAISS 向量索引检索岗位知识库的技术实现，体现 RAG/检索增强相关工程能力。
  - 建议突出：服务用户 5000+ 的规模数据，体现项目实际落地经验。

**expression** (1 条):
  - 原表达：负责开发 AI Agent Workflow 系统，采用 LangChain 编排四阶段 Agent，集成 DeepSeek V3 大模型作为推理引擎，通过 FAISS 向量索引检索岗位知识库，实现智能简历分析与改写建议生成，服务用户 5000+。→ 建议表达：负责开发 AI Agent Workflow 系统：基于 LangChain 编排四阶段 Agent 智能工作流，集成 DeepSeek V3 大模型作为推理引擎，通过 FAISS 向量索引检索岗位知识库，实现智能简历分析与改写建议生成，服务用户 5000+。

### 7. 分类汇总

- strengths: 4 条
- weaknesses: 0 条

### 8. 自动化检查结果

- ✅ [HARD_ASSERT] api_call
- ✅ [HARD_ASSERT] data_source
- ✅ [HARD_ASSERT] match_level_fields
- ✅ [HARD_ASSERT] analysis_basis_type
- 👀 [LOGIC_CHECK] fact_check_flagged
  > flagged=1, violations=1, checked=1 — 人工判断拦截是否合理
- ✅ [LOGIC_CHECK] gap_type_tags
- ✅ [LOGIC_CHECK] rewrite_grade_AB
- ✅ [CROSS_TAB] cross_tab_consistency
- 👀 [SEMANTIC] SEMANTIC: 匹配等级是否符合人工期望（看 overall/ability/experience/risk 四个值）
  > 自动化无法判定，需人工看证据
- 👀 [SEMANTIC] SEMANTIC: 关键技术要求是否遗漏（对比 JD 核心关键词与 analysis_basis）
  > 自动化无法判定，需人工看证据
- 👀 [SEMANTIC] SEMANTIC: 事实幻觉检测（rewrite 新增技术/数字/项目级别）
  > 自动化无法判定，需人工看证据
- 👀 [SEMANTIC] SEMANTIC: 空泛改写检测（rewrite 是否只是加评价短句）
  > 自动化无法判定，需人工看证据
- 👀 [SEMANTIC] SEMANTIC: 跨 Tab 一致性（match_level 与 analysis_basis.overall_gap_ratio 一致）
  > 自动化无法判定，需人工看证据
- 👀 [SEMANTIC] SEMANTIC: 教育经历/时间推断正确性
  > 自动化无法判定，需人工看证据
- 👀 [SEMANTIC] SEMANTIC: weaknesses 或 supplement 的分类标记是否准确（[表达优化]/[事实待确认]/[能力缺口]）
  > 自动化无法判定，需人工看证据

### 9. 需要人工审核的具体问题

请人工审查以下 7 项语义问题（自动化无法判定）：

- 👀 **fact_check_flagged**
  > 证据: 疑似新增技术: aiagent系统架构设计
- 👀 **匹配等级是否符合人工期望（看 overall/ability/experience/risk 四个值）**
  > 证据: {"overall": "中等", "ability": "较强", "experience": "待确认", "risk": "需要优化"}
- 👀 **关键技术要求是否遗漏（对比 JD 核心关键词与 analysis_basis）**
  > 证据: [{"dimension": "AI Agent 系统架构设计", "items": [{"type": "match", "content": "简历体现候选人负责开发 AI Agent Workflow 系统，采用 LangChain 编排四阶段 Agent，具备 AI Agent 系统编排与开发的直接经验，与岗位核心职责高度吻合。", "quote": "负责开发 AI Agent Workflow 系统，采用 LangChain 编排四阶段 Agent", "match_degree": "高"}]}, {"dimension": "智能工作流构建", "items": [{"type": "match", "content": "简历体现候选人通过 LangChain 编排四阶段 Agent 实现智能简历分析与改写建议生成，具备智能工作流构建的实践经验。", "quote": "采用 LangChain 编排四阶段 Agent……实现智能简历分析与改写建议生成", "match_degree": "高"}]}]
- 👀 **事实幻觉检测（rewrite 新增技术/数字/项目级别）**
  > 证据: [{"original": "负责开发 AI Agent Workflow 系统，采用 LangChain 编排四阶段 Agent，集成 DeepSeek V3 大模型作为推理引擎，通过 FAISS 向量索引检索岗位知识库，实现智能简历分析与改写建议生成，服务用户 5000+。", "revised": "负责开发 AI Agent Workflow 系统：基于 LangChain 编排四阶段 Agent 智能工作流，集成 DeepSeek V3 大模型作为推理引擎，通过 FAISS 向量索引检索岗位知识库，实现智能简历分析与改写建议生成，服务用户 5000+。", "basis": "依据：原文《负责开发 AI Agent Workflow 系统，采用 LangChain 编排四阶段 Agent，集成 DeepSeek V3 大模型作为推理引擎，通过 FAISS 向量索引检索岗位知识库，实现智能简历分析与改写建议生成，服务用户 5000+。》；JD要求：AI Agent 系统架构设计、智能工作流构建、LangChain、DeepSeek；改写逻辑：将原文一句话拆分为“系统名称 + 冒
- 👀 **空泛改写检测（rewrite 是否只是加评价短句）**
- 👀 **跨 Tab 一致性（match_level 与 analysis_basis.overall_gap_ratio 一致）**
- 👀 **教育经历/时间推断正确性**
  > 证据: 简历体现候选人负责开发 AI Agent Workflow 系统，采用 LangChain 编排四阶段 Agent，具备 AI Agent 系统编排与开发的直接经验，与岗位核心职责高度吻合。 简历体现候选人通过 LangChain 编排四阶段 Agent 实现智能简历分析与改写建议生成，具备智能工作流构建的实践经验。 简历体现候选人集成 DeepSeek V3 大模型作为推理引擎，具备大模型集成经验，且与岗位技术栈中 DeepSeek 要求直接对应。 简历明确体现 LangChain 使用经验，与岗位技术要求直接匹配。 [事实待确认] 岗位技术要求 Python，简历技术栈与项目描述中未明确提及 Python，当前简历未体现该技术实践，需候选人确认。 [能力缺口] 岗位技术要求 FastAPI，简历技术栈与项目描述中均未体现，当前简历未体现该技术实践。 简历明确体现 DeepSeek V3 集成经验，与岗位技术要求匹配。 [表达优化] 简历仅提及服务用户 5000+，未体现性能提升、准确率等具体工作成果指标，成果表述可进一步量化以增强说服力。 [事实待确认] 简历未提供教育背景、毕业时
- 👀 **weaknesses 或 supplement 的分类标记是否准确（[表达优化]/[事实待确认]/[能力缺口]）**

---

## CASE7_时间推算应待确认

**测试目的**: 2020-2023 时间段无'已毕业'标注，AI 不能仅凭时间断言状态
**人工期望**: `{"should_not_assert_graduate_state": true}`

### 1. 输入（完整不截断）

**简历**:
```
吴九，教育经历：2020.09-2023.06 软件工程。目前在一家 AI 公司做后端开发。
```

**JD**:
```
后端开发工程师。要求：计算机相关专业；1-3 年开发经验；熟悉 Python。
```

### 2. AI 综合匹配结论

- **overall**: 中等
- **ability**: 中等
- **experience**: 较弱
- **risk**: 需要优化

### 3. 详细分析 (analysis_basis)


**维度: 教育背景**
  - ✅ **match** (高): 具有软件工程专业教育背景，与岗位要求的计算机相关专业匹配
    > 原文: 教育经历：2020.09-2023.06 软件工程
  - 🔸 **gap** (低): [事实待确认]简历未说明学历层次（本科/硕士等），无法确认是否满足岗位对学历的要求

**维度: 工作经历**
  - ✅ **match** (中): 目前从事后端开发工作，与岗位核心职责方向一致
    > 原文: 目前在一家 AI 公司做后端开发
  - 🔸 **gap** (低): [事实待确认]简历未写明后端开发工作的起始时间，无法核算实际工作年限是否落在岗位要求的1-3年区间

**维度: 技术栈**
  - 🔸 **gap** (低): [事实待确认]岗位核心要求Python编程能力，当前简历未体现该技术实践
  - 🔸 **gap** (低): [表达优化]简历未列出任何具体技术栈，无法判断后端开发相关技术掌握情况

**维度: 项目与系统设计**
  - 🔸 **gap** (低): [事实待确认]岗位要求参与服务端功能设计与系统设计，当前简历未体现相关项目经历或设计实践

### 4. 改写建议 (rewrite_suggestions)


**改写 #1** (grade=B)
- **original**: `目前在一家 AI 公司做后端开发`
- **revised**: `目前在一家 AI 公司从事后端开发工作`
- **basis**: 依据：原文《目前在一家 AI 公司做后端开发》；JD要求：负责后端系统的开发与维护，参与服务端功能设计与实现；改写逻辑：将口语化表达“做后端开发”调整为更专业的书面表达“从事后端开发工作”，提升简历专业度，不改变任何事实内容。

### 5. 事实校验 (fact_check)

- checked=1  flagged=0  violations=0

### 6. 优化任务 (optimization_advice)


**highlight** (2 条):
  - 建议突出：软件工程专业教育背景与岗位要求的计算机相关专业方向一致，可在简历中明确标注学历层次（如本科）以增强匹配度（仅基于原文已有事实补充）
  - 建议突出：当前在AI公司从事后端开发的工作经历与岗位核心职责方向一致，可补充具体工作起止时间以体现工作年限

**expression** (1 条):
  - 建议优化表达：原表达“目前在一家 AI 公司做后端开发”→建议表达“目前在一家 AI 公司从事后端开发工作”，将口语化表达调整为更专业的书面表达

### 7. 分类汇总

- strengths: 2 条
- weaknesses: 0 条

### 8. 自动化检查结果

- ✅ [HARD_ASSERT] api_call
- ✅ [HARD_ASSERT] data_source
- ✅ [HARD_ASSERT] match_level_fields
- ✅ [HARD_ASSERT] analysis_basis_type
- ✅ [LOGIC_CHECK] fact_check_flagged
- ✅ [LOGIC_CHECK] gap_type_tags
- ✅ [LOGIC_CHECK] rewrite_grade_AB
- ✅ [CROSS_TAB] cross_tab_consistency
- 👀 [SEMANTIC] SEMANTIC: 匹配等级是否符合人工期望（看 overall/ability/experience/risk 四个值）
  > 自动化无法判定，需人工看证据
- 👀 [SEMANTIC] SEMANTIC: 关键技术要求是否遗漏（对比 JD 核心关键词与 analysis_basis）
  > 自动化无法判定，需人工看证据
- 👀 [SEMANTIC] SEMANTIC: 事实幻觉检测（rewrite 新增技术/数字/项目级别）
  > 自动化无法判定，需人工看证据
- 👀 [SEMANTIC] SEMANTIC: 空泛改写检测（rewrite 是否只是加评价短句）
  > 自动化无法判定，需人工看证据
- 👀 [SEMANTIC] SEMANTIC: 跨 Tab 一致性（match_level 与 analysis_basis.overall_gap_ratio 一致）
  > 自动化无法判定，需人工看证据
- 👀 [SEMANTIC] SEMANTIC: 教育经历/时间推断正确性
  > 自动化无法判定，需人工看证据
- 👀 [SEMANTIC] SEMANTIC: weaknesses 或 supplement 的分类标记是否准确（[表达优化]/[事实待确认]/[能力缺口]）
  > 自动化无法判定，需人工看证据

### 9. 需要人工审核的具体问题

请人工审查以下 7 项语义问题（自动化无法判定）：

- 👀 **匹配等级是否符合人工期望（看 overall/ability/experience/risk 四个值）**
  > 证据: {"overall": "中等", "ability": "中等", "experience": "较弱", "risk": "需要优化"}
- 👀 **关键技术要求是否遗漏（对比 JD 核心关键词与 analysis_basis）**
  > 证据: [{"dimension": "教育背景", "items": [{"type": "match", "content": "具有软件工程专业教育背景，与岗位要求的计算机相关专业匹配", "quote": "教育经历：2020.09-2023.06 软件工程", "match_degree": "高"}, {"type": "gap", "content": "[事实待确认]简历未说明学历层次（本科/硕士等），无法确认是否满足岗位对学历的要求", "match_degree": "低"}]}, {"dimension": "工作经历", "items": [{"type": "match", "content": "目前从事后端开发工作，与岗位核心职责方向一致", "quote": "目前在一家 AI 公司做后端开发", "match_degree": "中"}, {"type": "gap", "content": "[事实待确认]简历未写明后端开发工作的起始时间，无法核算实际工作年限是否落在岗位要求的1-3年区间", "match_degree": "低"}]}]
- 👀 **事实幻觉检测（rewrite 新增技术/数字/项目级别）**
  > 证据: [{"original": "目前在一家 AI 公司做后端开发", "revised": "目前在一家 AI 公司从事后端开发工作", "basis": "依据：原文《目前在一家 AI 公司做后端开发》；JD要求：负责后端系统的开发与维护，参与服务端功能设计与实现；改写逻辑：将口语化表达“做后端开发”调整为更专业的书面表达“从事后端开发工作”，提升简历专业度，不改变任何事实内容。", "evidence_grade": "B", "evidence": [{"source_id": "resume_13326b9e3b92_0", "original_text": "吴九，教育经历：2020.09-2023.06 软件工程。目前在一家 AI 公司做后端开发。", "evidence_index": 1, "match_score": 0.3256, "source_type": "resume"}]}]
- 👀 **空泛改写检测（rewrite 是否只是加评价短句）**
- 👀 **跨 Tab 一致性（match_level 与 analysis_basis.overall_gap_ratio 一致）**
- 👀 **教育经历/时间推断正确性**
  > 证据: 具有软件工程专业教育背景，与岗位要求的计算机相关专业匹配 [事实待确认]简历未说明学历层次（本科/硕士等），无法确认是否满足岗位对学历的要求 目前从事后端开发工作，与岗位核心职责方向一致 [事实待确认]简历未写明后端开发工作的起始时间，无法核算实际工作年限是否落在岗位要求的1-3年区间 [事实待确认]岗位核心要求Python编程能力，当前简历未体现该技术实践 [表达优化]简历未列出任何具体技术栈，无法判断后端开发相关技术掌握情况 [事实待确认]岗位要求参与服务端功能设计与系统设计，当前简历未体现相关项目经历或设计实践
- 👀 **weaknesses 或 supplement 的分类标记是否准确（[表达优化]/[事实待确认]/[能力缺口]）**

---

## CASE8_事实冲突_技术栈

**测试目的**: 简历明确 Python+Go 经验，JD 要 Java，AI 不能篡改成 Java 或 Spring Boot
**人工期望**: `{"must_not_have_fake_rewrite": ["Java", "Spring Boot", "Spring Cloud"], "must_have_gap_types": ["能力缺口"]}`

### 1. 输入（完整不截断）

**简历**:
```
郑十，2020-2024 计算机科学 本科。后端开发工程师，3 年经验，主要技术栈 Python（FastAPI/Django）和 Go。曾用 Go 开发微服务网关，用 Python 做数据处理管道。
```

**JD**:
```
高级后端工程师（Java 方向）。岗位职责：负责公司核心业务系统的后端架构设计与开发，参与系统性能优化。任职要求：本科及以上学历计算机相关专业；3-5 年 Java 开发经验；熟悉 Spring Boot、Spring Cloud 等主流框架；熟悉 MySQL、Redis、Kafka；有微服务架构和分布式系统开发经验者优先。
```

### 2. AI 综合匹配结论

- **overall**: 较低
- **ability**: 中等
- **experience**: 中等
- **risk**: 风险较高

### 3. 详细分析 (analysis_basis)


**维度: 技术栈匹配度**
  - 🔸 **gap** (低): [能力缺口]岗位核心技术要求为 Java、Spring Boot、Spring Cloud、MySQL、Redis、Kafka，当前简历未体现上述任何技术的实践经历。
  - ✅ **match** (低): 候选人具备后端开发技术栈，但为 Python 与 Go 方向，与岗位要求的 Java 方向不一致。
    > 原文: 主要技术栈 Python（FastAPI/Django）和 Go

**维度: 岗位职责匹配度**
  - 🔸 **gap** (低): [能力缺口]岗位要求负责核心业务系统的后端架构设计与开发，当前简历未体现架构设计相关职责实践。
  - 🔸 **gap** (低): [能力缺口]岗位要求参与系统性能优化，当前简历未体现性能优化相关工作内容。
  - ✅ **match** (中): 候选人具备后端开发经验，与岗位的后端开发方向存在一定基础重合。
    > 原文: 后端开发工程师，3 年经验

**维度: 微服务与分布式经验**
  - ✅ **match** (中): 候选人具备微服务网关开发经历，与岗位微服务架构方向存在部分关联。
    > 原文: 曾用 Go 开发微服务网关
  - 🔸 **gap** (低): [事实待确认]岗位要求分布式系统开发能力，简历仅体现微服务网关与数据处理管道，未体现分布式系统相关实践（如分布式事务、服务治理、分布式缓存等）。

**维度: 项目经历深度**
  - 🔸 **gap** (低): [表达优化]简历项目描述较为简略，缺少具体项目成果与量化数据，难以评估项目复杂度与个人贡献。
  - 🔸 **gap** (低): [表达优化]简历未提及框架之外的工程实践细节（如部署、监控、调优等），无法判断工程能力深度。

**维度: 教育背景与工作年限**
  - ✅ **match** (高): 候选人具备计算机科学本科学历，专业方向与岗位相关。
    > 原文: 2020-2024 计算机科学 本科
  - ✅ **match** (中): 候选人自述具备 3 年后端开发经验，与高级后端工程师岗位的经验要求存在一定匹配。
    > 原文: 后端开发工程师，3 年经验
  - 🔸 **gap** (低): [事实待确认]简历未写明工作起始时间，无法独立核实 3 年经验的实际起止区间，工作年限待确认。

### 4. 改写建议 (rewrite_suggestions)


**改写 #1** (grade=B)
- **original**: `后端开发工程师，3 年经验，主要技术栈 Python（FastAPI/Django）和 Go。`
- **revised**: `后端开发工程师，3 年经验，主要技术栈为 Python（FastAPI/Django）与 Go，具备多语言后端开发能力。`
- **basis**: 依据：原文《后端开发工程师，3 年经验，主要技术栈 Python（FastAPI/Django）和 Go》；JD要求后端开发能力与多语言技术栈基础；改写逻辑：将原文技术栈信息以更专业的书面表达重新组织，突出多语言后端开发这一原文已有事实，不新增任何技术或经验。

**改写 #2** (grade=B)
- **original**: `曾用 Go 开发微服务网关，用 Python 做数据处理管道。`
- **revised**: `曾使用 Go 开发微服务网关，具备微服务架构方向的开发经历；使用 Python 构建数据处理管道，具备数据处理相关工程经验。`
- **basis**: 依据：原文《曾用 Go 开发微服务网关，用 Python 做数据处理管道》；JD要求微服务架构与后端开发经验；改写逻辑：将原文两项经历分点展开，明确技术方向与工程属性，使微服务网关与数据处理管道两项事实与岗位微服务方向形成更清晰的对应，不新增职责或技术。
- ⚠️ **fact_warning**: `疑似新增技术: 微服务架构`

### 5. 事实校验 (fact_check)

- checked=2  flagged=1  violations=1
> ⚠️ **需要人工判断拦截是否合理**（flagged>0 不是自动 FAIL，保守误报和合理拦截都可能）

### 6. 优化任务 (optimization_advice)


**highlight** (5 条):
  - 建议突出：3 年后端开发经验，与岗位后端开发方向存在基础重合，可在简历开头明确标注工作年限与后端开发定位。
  - 建议突出：掌握 Python 与 Go 双技术栈，具备多语言后端开发能力，体现技术学习与迁移潜力。
  - 建议突出：曾用 Go 开发微服务网关，与岗位微服务架构方向存在部分关联，应作为重点经历前置展示。
  - 建议突出：有数据处理管道开发经历，具备数据处理相关工程经验，可体现工程实践广度。
  - 建议突出：2020-2024 计算机科学本科学历，专业背景与岗位高度相关。

**expression** (2 条):
  - 建议优化表达：原表达「后端开发工程师，3 年经验，主要技术栈 Python（FastAPI/Django）和 Go。」→ 建议表达「后端开发工程师，3 年经验，主要技术栈为 Python（FastAPI/Django）与 Go，具备多语言后端开发能力。」
  - 建议优化表达：原表达「曾用 Go 开发微服务网关，用 Python 做数据处理管道。」→ 建议表达「曾使用 Go 开发微服务网关，具备微服务架构方向的开发经历；使用 Python 构建数据处理管道，具备数据处理相关工程经验。」

### 7. 分类汇总

- strengths: 5 条
- weaknesses: 0 条

### 8. 自动化检查结果

- ✅ [HARD_ASSERT] api_call
- ✅ [HARD_ASSERT] data_source
- ✅ [HARD_ASSERT] match_level_fields
- ✅ [HARD_ASSERT] analysis_basis_type
- 👀 [LOGIC_CHECK] fact_check_flagged
  > flagged=1, violations=1, checked=2 — 人工判断拦截是否合理
- ✅ [LOGIC_CHECK] gap_type_tags
- ✅ [LOGIC_CHECK] rewrite_grade_AB
- ✅ [CROSS_TAB] cross_tab_consistency
- 👀 [SEMANTIC] SEMANTIC: 匹配等级是否符合人工期望（看 overall/ability/experience/risk 四个值）
  > 自动化无法判定，需人工看证据
- 👀 [SEMANTIC] SEMANTIC: 关键技术要求是否遗漏（对比 JD 核心关键词与 analysis_basis）
  > 自动化无法判定，需人工看证据
- 👀 [SEMANTIC] SEMANTIC: 事实幻觉检测（rewrite 新增技术/数字/项目级别）
  > 自动化无法判定，需人工看证据
- 👀 [SEMANTIC] SEMANTIC: 空泛改写检测（rewrite 是否只是加评价短句）
  > 自动化无法判定，需人工看证据
- 👀 [SEMANTIC] SEMANTIC: 跨 Tab 一致性（match_level 与 analysis_basis.overall_gap_ratio 一致）
  > 自动化无法判定，需人工看证据
- 👀 [SEMANTIC] SEMANTIC: 教育经历/时间推断正确性
  > 自动化无法判定，需人工看证据
- 👀 [SEMANTIC] SEMANTIC: weaknesses 或 supplement 的分类标记是否准确（[表达优化]/[事实待确认]/[能力缺口]）
  > 自动化无法判定，需人工看证据

### 9. 需要人工审核的具体问题

请人工审查以下 7 项语义问题（自动化无法判定）：

- 👀 **fact_check_flagged**
  > 证据: 疑似新增技术: 微服务架构
- 👀 **匹配等级是否符合人工期望（看 overall/ability/experience/risk 四个值）**
  > 证据: {"overall": "较低", "ability": "中等", "experience": "中等", "risk": "风险较高"}
- 👀 **关键技术要求是否遗漏（对比 JD 核心关键词与 analysis_basis）**
  > 证据: [{"dimension": "技术栈匹配度", "items": [{"type": "gap", "content": "[能力缺口]岗位核心技术要求为 Java、Spring Boot、Spring Cloud、MySQL、Redis、Kafka，当前简历未体现上述任何技术的实践经历。", "match_degree": "低"}, {"type": "match", "content": "候选人具备后端开发技术栈，但为 Python 与 Go 方向，与岗位要求的 Java 方向不一致。", "quote": "主要技术栈 Python（FastAPI/Django）和 Go", "match_degree": "低"}]}, {"dimension": "岗位职责匹配度", "items": [{"type": "gap", "content": "[能力缺口]岗位要求负责核心业务系统的后端架构设计与开发，当前简历未体现架构设计相关职责实践。", "match_degree": "低"}, {"type": "gap", "content": "[能力缺口]岗位要求参与系统性
- 👀 **事实幻觉检测（rewrite 新增技术/数字/项目级别）**
  > 证据: [{"original": "后端开发工程师，3 年经验，主要技术栈 Python（FastAPI/Django）和 Go。", "revised": "后端开发工程师，3 年经验，主要技术栈为 Python（FastAPI/Django）与 Go，具备多语言后端开发能力。", "basis": "依据：原文《后端开发工程师，3 年经验，主要技术栈 Python（FastAPI/Django）和 Go》；JD要求后端开发能力与多语言技术栈基础；改写逻辑：将原文技术栈信息以更专业的书面表达重新组织，突出多语言后端开发这一原文已有事实，不新增任何技术或经验。", "evidence_grade": "B", "evidence": [{"source_id": "resume_ea9211a276e7_0", "original_text": "后端开发工程师，3 年经验，主要技术栈 Python（FastAPI/Django）和 Go。", "evidence_index": 1, "match_score": 1.0, "source_type": "resume"}]}, {"ori
- 👀 **空泛改写检测（rewrite 是否只是加评价短句）**
- 👀 **跨 Tab 一致性（match_level 与 analysis_basis.overall_gap_ratio 一致）**
- 👀 **教育经历/时间推断正确性**
  > 证据: [能力缺口]岗位核心技术要求为 Java、Spring Boot、Spring Cloud、MySQL、Redis、Kafka，当前简历未体现上述任何技术的实践经历。 候选人具备后端开发技术栈，但为 Python 与 Go 方向，与岗位要求的 Java 方向不一致。 [能力缺口]岗位要求负责核心业务系统的后端架构设计与开发，当前简历未体现架构设计相关职责实践。 [能力缺口]岗位要求参与系统性能优化，当前简历未体现性能优化相关工作内容。 候选人具备后端开发经验，与岗位的后端开发方向存在一定基础重合。 候选人具备微服务网关开发经历，与岗位微服务架构方向存在部分关联。 [事实待确认]岗位要求分布式系统开发能力，简历仅体现微服务网关与数据处理管道，未体现分布式系统相关实践（如分布式事务、服务治理、分布式缓存等）。 [表达优化]简历项目描述较为简略，缺少具体项目成果与量化数据，难以评估项目复杂度与个人贡献。 [表达优化]简历未提及框架之外的工程实践细节（如部署、监控、调优等），无法判断工程能力深度。 候选人具备计算机科学本科学历，专业方向与岗位相关。 候选人自述具备 3 年后端开发经验，与高级后
- 👀 **weaknesses 或 supplement 的分类标记是否准确（[表达优化]/[事实待确认]/[能力缺口]）**

---

## CASE9_数字成果虚构不应出现

**测试目的**: 简历无量化成果，rewrite 不应凭空加'5000+ 用户'等数字
**人工期望**: `{"rewrite_should_not_have_fake_metrics": true}`

### 1. 输入（完整不截断）

**简历**:
```
冯十一，负责开发企业内部管理系统，使用 Vue 和 Element Plus 做前端，Java Spring Boot 做后端，参与需求分析、接口设计、编码实现、测试部署全过程。
```

**JD**:
```
全栈开发工程师。要求：Vue + Spring Boot 经验；有企业管理系统开发经验；熟悉 MySQL、Redis。
```

### 2. AI 综合匹配结论

- **overall**: 中等
- **ability**: 中等
- **experience**: 较弱
- **risk**: 需要优化

### 3. 详细分析 (analysis_basis)


**维度: 技术栈匹配**
  - ✅ **match** (高): 简历体现 Vue 前端开发实践，与 JD 要求的 Vue 技术一致
    > 原文: 使用 Vue 和 Element Plus 做前端
  - ✅ **match** (高): 简历体现 Spring Boot 后端开发实践，与 JD 要求的 Spring Boot 技术一致
    > 原文: Java Spring Boot 做后端
  - 🔸 **gap** (低): [事实待确认] JD 要求 MySQL，当前简历未体现该技术实践
  - 🔸 **gap** (低): [事实待确认] JD 要求 Redis，当前简历未体现该技术实践

**维度: 岗位职责匹配**
  - ✅ **match** (高): 简历体现全栈开发实践，前端 Vue、后端 Java Spring Boot，与 JD 全栈开发职责方向一致
    > 原文: 使用 Vue 和 Element Plus 做前端，Java Spring Boot 做后端
  - ✅ **match** (高): 简历项目为企业内部管理系统，与 JD 企业管理系统开发方向一致
    > 原文: 负责开发企业内部管理系统
  - ✅ **match** (中): 简历体现参与完整开发流程，覆盖需求分析、接口设计、编码实现、测试部署
    > 原文: 参与需求分析、接口设计、编码实现、测试部署全过程

**维度: 经验与背景**
  - 🔸 **gap** (低): [事实待确认] 简历未提供工作年限、起始时间，无法计算实际工作年限，工作年限待确认
  - 🔸 **gap** (低): [事实待确认] 简历未提供学历、毕业时间信息，毕业状态待确认
  - 🔸 **gap** (低): [事实待确认] 简历未体现团队协作、项目规模等背景信息

**维度: 成果与量化**
  - 🔸 **gap** (低): [表达优化] 简历未提供具体项目成果与量化数据，项目贡献度难以评估

### 4. 改写建议 (rewrite_suggestions)


**改写 #1** (grade=B)
- **original**: `负责开发企业内部管理系统，使用 Vue 和 Element Plus 做前端，Java Spring Boot 做后端`
- **revised**: `负责企业内部管理系统的全栈开发：前端使用 Vue + Element Plus，后端使用 Java Spring Boot`
- **basis**: 依据：原文《负责开发企业内部管理系统，使用 Vue 和 Element Plus 做前端，Java Spring Boot 做后端》；JD要求全栈开发、Vue、Spring Boot、企业管理系统开发；改写逻辑：将原文中分散的前后端技术描述整合为'全栈开发'结构，用冒号分点呈现技术栈归属，使'全栈'这一JD核心关键词与原文已有事实自然对应，提升信息组织清晰度与岗位相关性，未新增任何技术或职责。

**改写 #2** (grade=B)
- **original**: `参与需求分析、接口设计、编码实现、测试部署全过程`
- **revised**: `参与企业内部管理系统开发全过程，覆盖需求分析、接口设计、编码实现、测试部署各阶段`
- **basis**: 依据：原文《参与需求分析、接口设计、编码实现、测试部署全过程》；JD要求参与企业管理系统开发；改写逻辑：将'全过程'具体化为'覆盖……各阶段'，并补充'企业内部管理系统开发'作为上下文，使流程描述与JD'企业管理系统开发'职责直接关联，表达更专业清晰，未改变'参与'的职责程度，未新增任何事实。

### 5. 事实校验 (fact_check)

- checked=2  flagged=0  violations=0

### 6. 优化任务 (optimization_advice)


**highlight** (3 条):
  - 建议突出：全栈开发能力——原文已明确前端 Vue + Element Plus、后端 Java Spring Boot，建议在简历开头或项目描述首句直接点明'全栈开发'定位，与JD核心技能'全栈开发'形成第一眼匹配。
  - 建议突出：企业管理系统项目背景——原文已写明'企业内部管理系统'，与JD'企业管理系统开发'高度一致，建议将该关键词前置，避免被技术细节淹没。
  - 建议突出：完整开发流程参与——原文已列出需求分析、接口设计、编码实现、测试部署五个阶段，建议保留并作为独立要点呈现，体现对项目全流程的熟悉度。

**expression** (2 条):
  - 建议优化表达：'使用 Vue 和 Element Plus 做前端，Java Spring Boot 做后端' → '负责企业内部管理系统的全栈开发：前端使用 Vue + Element Plus，后端使用 Java Spring Boot'（将口语化'做前端/做后端'改为'全栈开发'结构，突出JD核心关键词'全栈开发'，同时保留原文全部技术事实）。
  - 建议优化表达：'参与需求分析、接口设计、编码实现、测试部署全过程' → '参与企业内部管理系统开发全过程，覆盖需求分析、接口设计、编码实现、测试部署各阶段'（补充项目上下文，使流程描述与JD'企业管理系统开发'职责直接挂钩，表达更完整专业）。

### 7. 分类汇总

- strengths: 3 条
- weaknesses: 0 条

### 8. 自动化检查结果

- ✅ [HARD_ASSERT] api_call
- ✅ [HARD_ASSERT] data_source
- ✅ [HARD_ASSERT] match_level_fields
- ✅ [HARD_ASSERT] analysis_basis_type
- ✅ [LOGIC_CHECK] fact_check_flagged
- ✅ [LOGIC_CHECK] gap_type_tags
- ✅ [LOGIC_CHECK] rewrite_grade_AB
- ✅ [CROSS_TAB] cross_tab_consistency
- 👀 [SEMANTIC] SEMANTIC: 匹配等级是否符合人工期望（看 overall/ability/experience/risk 四个值）
  > 自动化无法判定，需人工看证据
- 👀 [SEMANTIC] SEMANTIC: 关键技术要求是否遗漏（对比 JD 核心关键词与 analysis_basis）
  > 自动化无法判定，需人工看证据
- 👀 [SEMANTIC] SEMANTIC: 事实幻觉检测（rewrite 新增技术/数字/项目级别）
  > 自动化无法判定，需人工看证据
- 👀 [SEMANTIC] SEMANTIC: 空泛改写检测（rewrite 是否只是加评价短句）
  > 自动化无法判定，需人工看证据
- 👀 [SEMANTIC] SEMANTIC: 跨 Tab 一致性（match_level 与 analysis_basis.overall_gap_ratio 一致）
  > 自动化无法判定，需人工看证据
- 👀 [SEMANTIC] SEMANTIC: 教育经历/时间推断正确性
  > 自动化无法判定，需人工看证据
- 👀 [SEMANTIC] SEMANTIC: weaknesses 或 supplement 的分类标记是否准确（[表达优化]/[事实待确认]/[能力缺口]）
  > 自动化无法判定，需人工看证据

### 9. 需要人工审核的具体问题

请人工审查以下 7 项语义问题（自动化无法判定）：

- 👀 **匹配等级是否符合人工期望（看 overall/ability/experience/risk 四个值）**
  > 证据: {"overall": "中等", "ability": "中等", "experience": "较弱", "risk": "需要优化"}
- 👀 **关键技术要求是否遗漏（对比 JD 核心关键词与 analysis_basis）**
  > 证据: [{"dimension": "技术栈匹配", "items": [{"type": "match", "content": "简历体现 Vue 前端开发实践，与 JD 要求的 Vue 技术一致", "quote": "使用 Vue 和 Element Plus 做前端", "match_degree": "高"}, {"type": "match", "content": "简历体现 Spring Boot 后端开发实践，与 JD 要求的 Spring Boot 技术一致", "quote": "Java Spring Boot 做后端", "match_degree": "高"}, {"type": "gap", "content": "[事实待确认] JD 要求 MySQL，当前简历未体现该技术实践", "match_degree": "低"}, {"type": "gap", "content": "[事实待确认] JD 要求 Redis，当前简历未体现该技术实践", "match_degree": "低"}]}, {"dimension": "岗位职责匹配", "items"
- 👀 **事实幻觉检测（rewrite 新增技术/数字/项目级别）**
  > 证据: [{"original": "负责开发企业内部管理系统，使用 Vue 和 Element Plus 做前端，Java Spring Boot 做后端", "revised": "负责企业内部管理系统的全栈开发：前端使用 Vue + Element Plus，后端使用 Java Spring Boot", "basis": "依据：原文《负责开发企业内部管理系统，使用 Vue 和 Element Plus 做前端，Java Spring Boot 做后端》；JD要求全栈开发、Vue、Spring Boot、企业管理系统开发；改写逻辑：将原文中分散的前后端技术描述整合为'全栈开发'结构，用冒号分点呈现技术栈归属，使'全栈'这一JD核心关键词与原文已有事实自然对应，提升信息组织清晰度与岗位相关性，未新增任何技术或职责。", "evidence_grade": "B", "evidence": [{"source_id": "resume_c71e0d381f16_0", "original_text": "冯十一，负责开发企业内部管理系统，使用 Vue 和 Element Plus 做前端，
- 👀 **空泛改写检测（rewrite 是否只是加评价短句）**
- 👀 **跨 Tab 一致性（match_level 与 analysis_basis.overall_gap_ratio 一致）**
- 👀 **教育经历/时间推断正确性**
  > 证据: 简历体现 Vue 前端开发实践，与 JD 要求的 Vue 技术一致 简历体现 Spring Boot 后端开发实践，与 JD 要求的 Spring Boot 技术一致 [事实待确认] JD 要求 MySQL，当前简历未体现该技术实践 [事实待确认] JD 要求 Redis，当前简历未体现该技术实践 简历体现全栈开发实践，前端 Vue、后端 Java Spring Boot，与 JD 全栈开发职责方向一致 简历项目为企业内部管理系统，与 JD 企业管理系统开发方向一致 简历体现参与完整开发流程，覆盖需求分析、接口设计、编码实现、测试部署 [事实待确认] 简历未提供工作年限、起始时间，无法计算实际工作年限，工作年限待确认 [事实待确认] 简历未提供学历、毕业时间信息，毕业状态待确认 [事实待确认] 简历未体现团队协作、项目规模等背景信息 [表达优化] 简历未提供具体项目成果与量化数据，项目贡献度难以评估
- 👀 **weaknesses 或 supplement 的分类标记是否准确（[表达优化]/[事实待确认]/[能力缺口]）**

---

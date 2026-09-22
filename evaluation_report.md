# AI 简历优化助手 — 评测报告（Evaluation Report）

> **诚实声明（务必先读）**
>
> 本报告核心数据为 **真实 LLM 三组消融评测**（A/B/C，DeepSeek `deepseek-chat`，24 组标注样本，共 72 次真实调用），
> 数据源：`evaluation/results/eval_ablation.json`。
>
> 核心结论一句话：
> **RAG 独立贡献为负**（单 Prompt 注入当前知识库后，匹配与缺口识别指标全部下降）；
> **Workflow 独立贡献在 overall 匹配上为正**（+0.125），但在分级得分与缺口识别上不成立，且带来约 1.9× 延迟、3.1× 输入 token；
> **所有指标中没有任何一项支持"准确率大幅提升"的简历表述**。
> 未提升/下降的指标全部如实记录，不做粉饰。

---

## 0. 结论速览（TL;DR）

| 问题 | 结论 |
|------|------|
| 三组消融是否来自真实 LLM | ✅ 是（DeepSeek，24 组 × 3 组，真实 usage 采集） |
| RAG 是否有效 | ❌ 独立看为负贡献（B−A：match 与 gap 指标全部下降，成本+延迟上升） |
| Agent Workflow 是否有效 | ⚠️ 部分有效（overall 匹配 +0.125、strict +0.073；graded 持平；gap F1 略降；代价高） |
| 两者组合 vs 纯单 Prompt | ⚠️ overall +0.083，其余基本持平，成本/延迟显著上升 |
| 技能/关键词 F1（Improved） | 0.4574（本次运行；上一次运行为 0.4605，LLM 非确定性波动） |
| 接口可用性 99.2% | ❌ 仍无长期依据（仅短时快照 100%） |

---

## 1. 评测目录结构

```
evaluation/
├── README.md                # 使用说明
├── data/
│   └── testset.py           # 24 组标注测试数据（未修改）
├── metrics.py               # 指标计算（本次新增 gap_f1 / match_graded / match_overall）
├── llm_backends.py          # RealBackend / MockBackend（未修改）
├── run_eval.py              # 三组消融对照（A/B/C）+ 真实 usage 采集
├── availability_test.py     # 接口可用性 / 故障注入测量
└── results/
    ├── eval_ablation.json   # ★ 三组消融真实结果（本报告主数据源）
    ├── eval_ablation.log    # 三组消融运行日志（含逐次真实 token 统计）
    ├── eval_real.json       # 早前两版本评测结果（Baseline vs Improved）
    ├── eval_result.json     # Mock 干净运行
    ├── fault.json           # 故障注入(25%)
    └── malformed.json       # 畸形 JSON(25%)
```

## 2. 三组实验定义（消融设计）

| 组 | 名称 | 定义 | 目的 |
|----|------|------|------|
| **A** | `baseline` | 单 Prompt，**无 RAG**（`build_single_prompt(resume, jd, "")`） | 纯模型能力基线 |
| **B** | `baseline_rag` | 单 Prompt **+ RAG**（`_retrieve_knowledge(jd)` 注入后单次调用，与生产降级路径一致） | **RAG 独立贡献 = B − A** |
| **C** | `improved` | Agent Workflow + RAG（4 Agent 串行） | **Workflow 独立贡献 = C − B**；组合贡献 = C − A |

- 同一批 24 组测试数据，未做任何修改；`expected_*` 标签未动。
- 评测通过运行时 monkeypatch 挂接 LLM 层，**未修改任何业务代码文件**。

## 3. 指标计算方法

| 指标 | 计算规则 | 说明 |
|------|----------|------|
| match_strict | match_level 4 字段字符串逐一相等取均值 | 原口径，**保留未删** |
| match_graded（新增） | 有序等级：相同=1 分，相邻=0.5 分，差两级=0 分；4 字段平均（overall: 较低<中等<较高；ability/experience: 较弱<中等<较强；risk: 风险较高<需要优化<风险较低） | 对有序标签更公平 |
| match_overall（新增） | 仅 overall 字段严格一致（0/1） | 单字段主指标 |
| gap_precision/recall/F1（新增） | 模型输出的 `weaknesses` + `analysis_basis(type=gap)` 文本，与 `expected_gaps` 集合比对：基础归一化（小写、去空白标点）后**双向包含**视为命中；precision = 命中至少一个期望 gap 的预测文本数/预测文本总数；recall = 被覆盖的期望 gap 数/期望 gap 总数 | expected_gaps 为空的样本不计入对应分母 |
| field_completeness / parse_success / workflow_success / suggestion_executability | 同前一版定义 | 结构指标 |
| real_prompt/completion/total_tokens | **直接读取 LLM API 响应的 usage 字段**（运行时包裹 `LLMService._log_tokens` 捕获），取每完整流程平均值 | 已废弃 chars/2 估算 |

> 说明：gap 匹配为"双向包含"规则，模型输出多条不足文本命中同一 gap 会同时计入 precision 的 TP，
> 因此 gap_precision 读数偏保守（大量描述性不足文本不计为命中），recall 上限 1.0。
> 每样本的 `match_level_output` 与 `gap_texts_output` 已留存于结果 JSON，可离线复算，无需重复调用。

## 4. 实际测试结果（真实 LLM，24 组 × 3 组）

### 4.1 三组指标总表

| 指标 | A 单Prompt | B 单Prompt+RAG | C Workflow+RAG |
|------|-----------|----------------|----------------|
| match_strict | 0.4479 | 0.4062 | **0.4792** |
| match_graded | **0.7188** | 0.6910 | **0.7188** |
| match_overall | 0.5417 | 0.5000 | **0.6250** |
| gap_precision | **0.2914** | 0.2514 | 0.2629 |
| gap_recall | **0.9706** | **0.9706** | 0.8922 |
| gap_f1 | **0.5604** | 0.4992 | 0.4987 |
| 字段完整率 | 1.0 | 1.0 | 1.0 |
| JSON 解析成功率 | 1.0 | 1.0 | 1.0 |
| Workflow 成功率 | 1.0 | 1.0 | 1.0 |
| 建议可执行性(代理) | 1.0 | 1.0 | 1.0 |
| 平均响应时间(ms) | **10406** | 11231 | 19381 |
| 平均 prompt tokens | **586.3** | 681.5 | 1874.7 |
| 平均 completion tokens | **1190.2** | 1299.2 | 1704.1 |
| 平均 total tokens | **1776.5** | 1980.7 | 3578.8 |
| 关键词 F1（仅 C 有结构化字段） | N/A | N/A | 0.4574 |

> N/A 说明：A/B（单 Prompt）无独立技能/关键词字段，keyword F1 结构上不可计算，如实标 N/A，不视作 0 分。
> 上一版本两组成评测（eval_real.json）测得 match 平 0.4688 / keyword F1 0.4605 / 延迟 11.5s vs 23.6s；
> 本次同口径重测数值有小幅波动（LLM temperature=0.2 的非确定性），两次结果均在报告中保留，结论方向一致。

### 4.2 消融贡献分解

**RAG 独立贡献（B − A）**：

| 指标 | 变化 | 判定 |
|------|------|------|
| match_strict | −0.0417 | ❌ 下降 |
| match_graded | −0.0278 | ❌ 下降 |
| match_overall | −0.0417 | ❌ 下降 |
| gap_f1 | −0.0612 | ❌ 下降 |
| 延迟 | +825 ms | ❌ 上升 |
| total tokens | +204.2 | ❌ 上升 |

→ **当前知识库对"匹配判断"的独立贡献为负**。原因（基于代码事实）：知识库 52 条中仅 21 条 AI 应用开发 + 14 条泛化"后端开发"，**无 Python开发/Java后端/普通后端专属条目**，18/24 样本召回的是泛化/错配知识；且检索无相似度阈值，低相关知识无条件注入。

**Workflow 独立贡献（C − B）**：

| 指标 | 变化 | 判定 |
|------|------|------|
| match_strict | **+0.0730** | ✅ 上升 |
| match_graded | +0.0278 | ≈ 持平 |
| match_overall | **+0.1250** | ✅ 上升 |
| gap_f1 | −0.0005 | ≈ 持平 |
| 延迟 | **+8150 ms（1.73×）** | ❌ 明显变慢 |
| total tokens | **+1598.1（1.81×）** | ❌ 明显增加 |

→ Workflow 带来了**总体匹配判断上的真实改善**（overall +0.125 是本次最大的单项增益），
但改善没有延伸到分级得分与缺口识别；代价是延迟与 token 接近翻倍。

**组合贡献（C − A）**：overall +0.0833、strict +0.0313、graded 0、gap_f1 −0.0617、延迟 +8.97s、total tokens +1802.3。

## 5. 回答三个核心问题

1. **Agent Workflow 是否有效？** —— 部分有效。对 `overall` 匹配有可复现的正贡献（C−B=+0.125，C−A=+0.083），并对结构化评测（技能字段、可评估性）是必要前提；但在 graded 得分、gap 识别上无贡献，且成本/延迟接近翻倍。
2. **RAG 是否有效？** —— 以当前知识库，**无效且为负**。B−A 全部内容指标下降，仅增加了 16% prompt token 与 825ms 延迟。
3. **哪些改进来自 Workflow、哪些来自 RAG？** —— overall/strict 匹配改善来自 **Workflow**；RAG 在当前形态下没有带来任何正向内容指标。

## 6. 下一步应该优化什么（按优先级）

1. **P1（最高优先）：重建知识库相关性** —— 为 Python开发/Java后端/普通后端补充专属条目；检索加相似度阈值（低分不注入）。在 RAG 由负转正之前，任何"RAG 提升准确率"的说法都不成立。
2. **P1：上下文去重 + Agent 1/2 并行** —— 简历原文被传 3 次、JD 分析传 2 次，中间 JSON 带 `indent=2`；去重 + 并行预计可显著压缩 C 组 19.4s / 1874.7 prompt tokens 的成本。
3. **P2：Match Agent prompt 注入评级 rubric**（各档位判定标准），对齐标注尺度，可能改善 graded 得分。
4. **P2：评测扩充** —— 单标注标签 + 24 样本的统计功效有限；overall +0.125 需更多样本/交叉标注确认后再写进简历。

## 7. 接口可用性（维持原结论）

**「99.2%」无长期依据，不能写。** 已实测（`availability_test.py`，短时快照）：350 次请求 100% 2xx、0 个 5xx、平均 1.57ms、P95 1.75ms。
可作为可复现描述："短时 350 次请求 0 个 5xx"，不可写 99.2% SLA。

## 8. 哪些指标可以写进简历 / 哪些不能写

### ✅ 可以写（已实测、措辞准确）

1. 多 Agent Workflow（4 Agent）、RAG（Embedding+FAISS 52 条）、LLM Provider 抽象与三级降级。
2. 建立了**三组消融评测框架**（单Prompt / 单Prompt+RAG / Workflow+RAG），24 组标注样本，真实 usage 采集。
3. Workflow 使**总体匹配一致率提升 0.125**（0.500→0.625，4 档标签严格口径，需注明样本规模 24）。
4. 技能/关键词结构化识别 F1 ≈ 0.46（24 组标注样本，仅 Workflow 架构可产出该字段）。
5. 成本/延迟实测：Workflow 较单 Prompt 延迟 1.86×、total tokens 2.02×（架构权衡的量化认知）。
6. 故障注入 25% 下无 5xx；350 次请求短时快照 100% 2xx。

### ❌ 不能写

1. ❌ RAG 提升了准确率（实测为负贡献）
2. ❌ 匹配准确率大幅提升 X%（graded 持平，strict 仅 +0.03）
3. ❌ 响应稳定性提升 25% / 接口可用性 99.2%（无基线 / 无长期证据）
4. ❌ 真实 API 计费成本金额（仅测得 token 数）

## 9. 复现方法

```powershell
# 重要：run_eval.py 直接导入 analyze 模块，不经过 main.py，因此不会自动加载 .env，
# 需在命令行注入环境变量（主业务服务 uvicorn 启动则正常读取配置）。
$env:LLM_PROVIDER='deepseek'
$env:DEEPSEEK_API_KEY='sk-xxxx'

# 三组消融真实评测（约 15-20 分钟，72 次真实调用）
python evaluation/run_eval.py --backend real --out evaluation/results/eval_ablation.json

# 只跑某一组
python evaluation/run_eval.py --backend real --groups improved

# Mock 管道自检（token usage 为 N/A）
python evaluation/run_eval.py --backend mock

# 接口可用性（先启动服务）
cd backend && python -m uvicorn main:app --port 8007
python evaluation/availability_test.py --base http://127.0.0.1:8007 --n 200
```

完整说明见 [evaluation/README.md](evaluation/README.md)。

---

## 10. RAG 优化轮（v2）：知识库判别性规则 + 相似度阈值

### 10.1 本轮修改（未动 Agent 数量、主业务流程、测试集与评分规则）

| 修改 | 内容 |
|------|------|
| 知识库扩充 | [knowledge_base.json](backend/rag/knowledge_base.json) 52 → **70 条**：新增 18 条**判别性岗位能力规则**（AI应用开发 4 / Python开发 6 / Java后端 4 / 普通后端 4），规则形式为"核心栈组合 → 等级判定边界"（如：微服务 JD 且简历仅单体经验 → overall 至多中等、risk 需要优化），而非泛化描述 |
| 相似度阈值 | [rag_knowledge.py](backend/rag/rag_knowledge.py) 增加 `RAG_MIN_SCORE`（默认 **0.875**，可环境变量覆盖）。校准依据：域内 24 组 JD 的 top-3 最低分 **0.8835**，域外查询（UI设计/销售/新媒体）最高分 **0.869**，阈值取分离边界 |
| 检索日志 | 每次检索输出：query、top_k、阈值、逐条 score 与"通过/低于阈值(不注入)"、最终注入清单。验证：域外查询 0/3 注入 |
| Top-K | 保持 **3** 不变 |

### 10.2 v2 评测结果（真实 LLM）

> ⚠️ **运行完整性说明**：本次运行中途 DeepSeek 账户余额耗尽（**402 Payment Required**），样本 19–24（be_01~be_06）三组均失败（走降级），其余 18 个样本三组全部真实成功。以下对比采用**三组共同有效的 18 个样本**口径，保证可比性。数据源：`evaluation/results/eval_ablation_v2.json`。

| 指标 | A 单Prompt | B 单Prompt+RAG | C Workflow+RAG |
|------|-----------|----------------|----------------|
| match_strict | 0.4861 | 0.4306 | **0.5139** |
| match_graded | 0.7361 | 0.7176 | **0.7407** |
| match_overall | 0.5556 | 0.4444 | 0.5556 |
| gap_precision | 0.3203 | 0.3293 | 0.3218 |
| gap_recall | 0.9231 | **0.9615** | 0.8462 |
| gap_f1 | 0.5775 | **0.6015** | 0.5484 |
| 平均响应时间(ms) | 11247 | 11492 | 21367 |
| 真实 tokens (in/out/total)* | 589/1196/1786 | 743/1212/1956 | 1843/1589/3432 |

\* token 为各自有效样本均值口径（A n=19 / B,C n=18；失败调用不产生 usage）。

### 10.3 v2 消融贡献（与 v1 对比）

| 贡献 | 指标 | v1（52条库，无阈值，24样本） | v2（70条库+阈值，18样本） |
|------|------|------|------|
| **RAG（B−A）** | match_strict | −0.0417 | −0.0555（仍为负） |
| | match_overall | −0.0417 | −0.1112（仍为负） |
| | gap_f1 | −0.0612 | **+0.0240（首次转正）** |
| | gap_recall | ≈持平 | +0.0384（注入规则帮助模型覆盖期望缺口） |
| **Workflow（C−B）** | match_strict | +0.0730 | +0.0833 |
| | match_overall | +0.1250 | +0.1112 |
| | gap_f1 | −0.0005 | −0.0531 |

### 10.4 v2 诚实结论

1. **RAG 未完全转正**：判别性规则 + 阈值使**缺口识别（gap_f1）首次由负转正**（+0.024，且 recall 提升），但 **match_level 各口径仍为负贡献**（strict −0.056、overall −0.111）。"RAG 提升匹配准确率"依然不成立。
2. **Workflow 贡献稳定**：在两轮评测中对 match_strict（+0.07~+0.08）与 match_overall（+0.11~+0.13）均为正，结论跨运行可复现。
3. **未完成 24 样本全量验证**：余额不足导致 6 个普通后端样本缺失；需充值后重跑完整 24 样本才能给出最终结论。
4. 评分规则、测试集、expected 标签未做任何修改；本轮仅改知识库内容与 RAG 检索层。

---

## 11. RAG 定位实验（D 组设计）：账户余额耗尽，实测未完成

### 11.1 D 组定义（已实现，待余额恢复后一键运行）

| 组 | 定义 | 验证目标 |
|----|------|----------|
| D `improved_d` | Agent Workflow，**RAG 从 Match Agent 移出，仅注入优化建议 Agent**（用于缺口识别与改写建议），不参与 overall 等级判断 | 验证 RAG 应服务"gap识别/优化建议"还是"overall 判断" |

- 实现方式：评测侧实验变体（[run_eval.py](evaluation/run_eval.py) 的 `run_improved_d`），**未修改任何业务代码**。
- 运行命令：`python evaluation/run_eval.py --backend real --groups improved_d --out evaluation/results/eval_group_d.json`
- 保持不变：测试集、评分规则、Embedding 模型、Top-K=3、阈值 0.875。

### 11.2 实测状态（诚实记录）

**D 组未能获得任何真实数据。** 运行时 DeepSeek 账户余额已为零，24/24 次调用全部返回 `402 Payment Required`（日志：`eval_group_d.log`），全部样本走降级路径。**不伪造 D 组结果，D 组所有内容指标记为 N/A。**

本次运行唯一的有效产出是 RAG 检索日志：24 组 JD 全部命中 3/3 条判别性规则条目（如 py_03 → `py_rule_crawler`、java_01 → `java_rule_core/java_rule_micro`），检索层行为符合设计预期。

### 11.3 四组对比表（当前状态）

| 指标（18 共同样本） | A 单Prompt | B 单Prompt+RAG | C Workflow+RAG(Match注入) | D Workflow+RAG(仅优化建议) |
|------|-----------|----------------|----------------|----------------|
| match_strict | 0.4861 | 0.4306 | 0.5139 | **N/A（未运行）** |
| match_graded | 0.7361 | 0.7176 | 0.7407 | **N/A** |
| match_overall | 0.5556 | 0.4444 | 0.5556 | **N/A** |
| gap_f1 | 0.5775 | 0.6015 | 0.5484 | **N/A** |
| 延迟(ms) | 11247 | 11492 | 21367 | **N/A** |
| tokens(total) | 1786 | 1956 | 3432 | **N/A** |

### 11.4 基于现有证据的定位分析（待 D 组实测确认）

**已有证据支持的判断：**

1. **RAG 对 gap 识别有正贡献**（v2：B−A gap_f1 +0.024，recall +0.038）——判别性规则帮助模型覆盖期望缺口。
2. **RAG 注入 Match Agent 对 match_level 为负**（v2：B−A overall −0.111、strict −0.056）——长规则文本进入匹配上下文反而干扰等级判断。
3. **Workflow 本身对 match 有稳定正贡献**（两轮：overall +0.11~+0.13）。

**倾向性结论（非实测）**：RAG 的证据指向"更适合服务 gap 识别/优化建议"，D 组的预期是保留 gap 收益、消除 match 干扰；但该结论在 D 组实测前**属于假设，不可写进任何报告或简历**。余额恢复后运行第 11.1 节命令即可完成验证。

# 职途AI — 基于 LLM Workflow 的智能求职辅助应用

## 项目介绍

职途AI 是一个面向求职者的智能简历分析工具，解决用户在投递简历前缺少专业反馈的问题。

用户上传简历并输入目标岗位 JD，系统通过 4 阶段 LLM Workflow 逐维度分析匹配度，输出结构化优化建议，帮助用户明确简历改进方向。

**核心能力：**

- **岗位分析** — 从 JD 中提取结构化要求（维度、硬性条件、软技能、关键词）
- **简历匹配** — 对照 JD 逐维度评估简历匹配程度（综合 / 技能 / 经历 / 风险）
- **AI 优化建议** — 生成改写建议、补充方向和表达优化，并提供修改前后对比
- **引用校验** — 回查简历原文，验证 AI 生成的引用是否真实存在，降低模型幻觉

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | HTML + CSS + JavaScript（无框架，纯原生） |
| 后端 | Node.js + Express.js |
| LLM | DeepSeek API（OpenAI 兼容接口，JSON Mode） |
| 文件解析 | pdf-parse（PDF 文本提取） |
| Prompt 管理 | 独立 Prompt 模板文件，版本控制 |
| 部署 | Render（render.yaml 一键部署） |

## 系统流程

```
用户输入（简历 + JD）
    │
    ▼
┌─────────────────────────────────────┐
│ Phase 1: 并行提取                    │
│  jdParser  解析 JD  → 结构化要求     │
│  resumeParser 解析简历 → 结构化信息  │
└──────────────┬──────────────────────┘
               ▼
┌─────────────────────────────────────┐
│ Phase 2: 匹配分析                    │
│  matchEngine 逐维度对照 → 匹配度 +   │
│  判断依据 + 引用校验（verifyQuotes） │
└──────────────┬──────────────────────┘
               ▼
┌─────────────────────────────────────┐
│ Phase 3: 建议生成                    │
│  suggestionEngine 基于匹配结果 →     │
│  改写建议 + 优化建议（分类输出）     │
└──────────────┬──────────────────────┘
               ▼
┌─────────────────────────────────────┐
│ Phase 4: 结果聚合                    │
│  组装为前端展示格式 → 返回 JSON      │
└─────────────────────────────────────┘
```

## 核心功能

### 1. JD 岗位解析
从原始 JD 文本中提取维度（如技术能力、产品能力）、硬性要求、软技能和关键词，不做任何推测。

### 2. 简历内容分析
从简历中提取教育背景、工作经历、项目经历、技能标签，每条经历附带原文引用（quote），确保可追溯。

### 3. 岗位匹配评估
逐维度对比 JD 要求与简历内容，输出：
- 综合匹配度（高 / 中 / 低）
- 技能匹配度
- 经历匹配度
- 风险提示
- 逐维度判断依据（match 项 + gap 项）

### 4. AI 优化建议
基于匹配缺陷生成分类建议：
- 建议突出哪些经历
- 建议补充哪些信息
- 建议优化哪些表达
- 修改前后对比（原文 → 改写建议）

### 5. 引用真实性校验
matchEngine 输出后，`verifyQuotes()` 回查简历原文验证 AI 生成的引用是否真实存在。校验基准为结构化简历字段（work_experience / project_experience / education / skills）和原始文本，采用标准化文本比对（去空格、去标点、统一小写）。引用不实则清除，前端显示「原文已核验」或「引用未通过核验」标签。

## 项目结构

```
e:\AI简历优化助手
├── index.html              # 前端页面（首页 / 输入页 / 加载页 / 结果页）
├── style.css               # 全局样式
├── script.js               # 前端交互逻辑 + API 调用 + 结果渲染
├── server.js               # 后端入口（Express 路由 + PDF 解析 + JD 校验）
├── config/
│   └── llm.js              # LLM 配置（模型、温度、超时）
├── prompts/                # Prompt 模板（版本控制）
│   ├── jdParser.js         # JD 解析 Prompt
│   ├── resumeParser.js     # 简历解析 Prompt
│   ├── matchEngine.js      # 匹配分析 Prompt
│   └── suggestionEngine.js # 建议生成 Prompt
├── services/
│   ├── analyzeService.js   # 分析服务入口（薄封装）
│   ├── llmService.js       # LLM 调用层（DeepSeek chat + structuredChat）
│   ├── workflow/
│   │   └── orchestrator.js # Pipeline 编排器（4 阶段流程控制）
│   ├── chains/             # 业务链（每个模块独立调用 LLM）
│   │   ├── jdParser.js
│   │   ├── resumeParser.js
│   │   ├── matchEngine.js
│   │   └── suggestionEngine.js
│   └── evaluation/
│       └── evaluator.js    # 效果评估（批量测试 Pipeline）
├── test-cases/
│   └── cases.json          # 测试案例
├── test-resume.pdf         # 测试用简历
├── package.json
├── render.yaml             # Render 部署配置
└── .env                    # 环境变量（LLM_API_KEY 等）
```

## 项目亮点

### Workflow 任务拆解
将分析任务拆解为 4 个独立节点（JD 解析 → 简历解析 → 匹配分析 → 建议生成），每个节点独立输入输出，支持并行执行（Phase 1 中 JD 解析和简历解析并行），失败时自动降级，便于调试和效果追踪。

### Prompt 模块化管理
4 个 Prompt 模板独立存放在 `prompts/` 目录，通过版本控制管理。每个 Prompt 包含 System Prompt 和 `buildUserMessage()` 函数，通过 JSON Mode 约束输出格式。

### 输出结构化设计
所有 LLM 输出通过 `structuredChat()` 的 JSON Mode 强制返回结构化 JSON，配合 `normalizeResult()` 补全缺失字段和 `cleanArrayField()` 清洗脏数据（过滤 JSON 片段、代码块、高特殊字符内容），确保前端可稳定渲染。

### 引用校验降低模型幻觉
`verifyQuotes()` 在匹配引擎输出后，对照简历原始文本验证 AI 引用的真实性。不实引用被清除并在前端标注「引用未通过核验」，避免向用户展示 AI 编造的内容。

## 项目运行方式

### 1. 安装依赖

```bash
npm install
```

### 2. 配置环境变量

在项目根目录创建 `.env` 文件：

```env
LLM_API_KEY=你的DeepSeek API Key
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-chat
```

### 3. 启动服务

```bash
npm start
```

服务启动后访问：**http://localhost:3000**

### 4. 其他命令

```bash
npm run clean      # 清理端口占用
npm run restart    # 重启服务
```

## 评估测试

项目包含效果评估模块，可批量测试 Pipeline 在不同 JD + 简历案例下的输出效果：

```bash
node services/evaluation/evaluator.js              # 运行全部案例
node services/evaluation/evaluator.js --case 0     # 运行指定案例
```

测试案例位于 `test-cases/cases.json`。

## API 接口

### POST /api/analyze

简历分析接口，支持两种格式：

**multipart/form-data:**
- `file` — PDF 简历文件
- `job_description` — 岗位 JD 文本

**application/json:**
- `resume_text` — 简历文本
- `job_description` — 岗位 JD 文本

### GET /api/health

健康检查接口，返回服务状态和 LLM 配置状态。

## 项目截图

<!-- 截图占位，部署后替换为实际截图 -->

- 首页 Hero 区域
- 输入页（步骤引导 + 上传 + JD 输入）
- 加载页（实时状态展示）
- 结果页（匹配度卡片 + 判断依据 + 建议）

## License

MIT
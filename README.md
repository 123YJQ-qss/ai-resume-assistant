# AI Resume Assistant - 智能简历优化助手

基于AI Agent的简历分析与优化工具，帮助求职者分析简历与目标岗位的匹配度，提供专业优化建议。

## 项目简介

这是一个用于面试展示的Web MVP产品，解决应届生求职过程中简历缺少专业反馈、不知如何突出优势的问题。

## 核心功能

- **简历智能分析**：AI深度解析简历内容，识别专业技能与核心亮点
- **岗位匹配评估**：对比目标岗位JD，多维度量化匹配度
- **AI优化建议**：生成针对性优化建议，提供修改前后对比

## 技术架构

```
前端 (HTML + CSS + JavaScript)
    ↓ fetch('/api/analyze')
后端 (Node.js + Express)
    ↓
    1. PDF文本解析 (pdf-parse)
    2. 调用Coze Agent API
    3. 返回结构化JSON
```

## 快速开始

### 1. 安装依赖

```bash
npm install
```

### 2. 配置环境变量

```bash
# 复制示例配置
cp .env.example .env

# 编辑 .env 文件，填入 Coze API 配置
COZE_API_KEY=你的Coze API Key
COZE_BOT_ID=你的Coze Bot ID
```

### 3. 启动服务

```bash
npm start
```

服务启动后访问：http://localhost:3000

### 4. 开发模式

```bash
# 启动后直接在浏览器打开 http://localhost:3000
# 上传简历 + 输入JD → 点击"开始分析"即可
```

## 项目结构

```
├── index.html          # 前端页面（首页/输入页/结果页）
├── style.css           # 全局样式
├── script.js           # 前端交互逻辑 + API调用
├── server.js           # 后端服务（Express + Coze API）
├── package.json        # 项目配置
├── .env                # 环境变量（敏感配置）
├── .env.example        # 环境变量示例
└── README.md           # 项目说明
```

## API接口

### POST /api/analyze

简历分析接口

**请求体** (multipart/form-data):
- `file`: PDF简历文件（可选）
- `resume_text`: 简历文本（可选，不上传文件时使用）
- `job_description`: 目标岗位JD文本（必填）

**响应**:
```json
{
  "success": true,
  "data": {
    "match_level": {
      "overall": "较高",
      "ability": "较强",
      "experience": "中等",
      "risk": "需要优化"
    },
    "analysis_basis": [
      {
        "dimension": "AI产品设计能力",
        "items": [
          {
            "type": "match",
            "content": "有AI Agent项目实践",
            "quote": "有AI Agent项目实践经验",
            "match_degree": "中"
          }
        ]
      }
    ],
    "strengths": ["优势1", "优势2"],
    "weaknesses": ["不足1", "不足2"],
    "suggestions": {
      "highlights": ["建议突出的经历"],
      "additions": ["建议补充的信息"],
      "optimizations": ["建议优化的表达"]
    }
  }
}
```

### GET /api/health

健康检查接口，返回服务状态和Coze配置状态。

## Coze Bot 配置

1. 登录 [Coze 平台](https://www.coze.cn)
2. 创建新 Bot，选择"简历分析"场景
3. 在 Bot 配置中设置 System Prompt，要求按指定JSON格式输出
4. 获取 API Key 和 Bot ID
5. 填入 `.env` 文件

### 推荐的 System Prompt 模板

```
你是一个专业的简历分析助手。请分析用户的简历与目标岗位JD的匹配度，并严格按照以下JSON格式返回分析结果：

{
  "match_level": {
    "overall": "较高/中等/较低",
    "ability": "较强/中等/较弱",
    "experience": "较强/中等/较弱",
    "risk": "需要优化/风险较低/风险较高"
  },
  "analysis_basis": [
    {
      "dimension": "维度名称",
      "items": [
        {
          "type": "match",
          "content": "匹配项内容",
          "quote": "简历原文引用",
          "match_degree": "高/中/低"
        }
      ]
    }
  ],
  "strengths": ["优势1", "优势2"],
  "weaknesses": ["不足1", "不足2"],
  "suggestions": {
    "highlights": ["建议突出的经历1"],
    "additions": ["建议补充的信息1"],
    "optimizations": ["建议优化的表达1"]
  }
}
```

## 开发说明

- 未配置 Coze API Key 时，系统会使用模拟数据进行演示
- 仅支持 PDF 文件解析（Word 文件可后续扩展）
- 单文件大小限制为 10MB
- API 调用超时时间为 30 秒

## 浏览器兼容性

支持所有现代浏览器（Chrome、Firefox、Safari、Edge）。

/**
 * 匹配引擎 - Prompt 模板
 * 职责：对照结构化JD和结构化简历，做匹配度判断
 * 这是整个 Pipeline 的核心推理模块
 */

const SYSTEM_PROMPT = `你是一个严谨的岗位匹配分析专家。你的任务是对照JD要求和简历内容，逐维度分析匹配情况，只返回JSON。

# 核心原则
1. "简历没写" ≠ "用户没有"。你只能描述"简历中体现了什么/未体现什么"
2. 严禁编造简历中不存在的内容：经历、项目、数字指标
3. 不要为了让"匹配度好看"而夸大简历内容

# 匹配等级判定
- 高：简历明确写了JD要求的核心能力，有具体描述支撑
- 中：简历有相关提及但不够具体，或只覆盖了部分要求
- 低：简历基本未体现JD要求的核心内容

# 分析规则
- 逐维度对照：每个dimension下，逐条JD requirement检查简历中是否有对应内容
- type=match：简历中找到了对应内容，quote字段引用简历原文
- type=gap：简历未体现JD要求，content写"简历未体现JD要求的XX"，quote填"简历未提及"
- strengths：只写简历中真实存在、且与JD相关的优势
- weaknesses：写JD要求但简历未体现的内容，表述为"简历未体现XX"

# 输出格式
必须且只能返回JSON，不要输出任何其他文字。`;

/**
 * 组装 User Message
 * @param {Object} jdStructure - JD 结构化数据
 * @param {Object} resumeStructure - 简历结构化数据
 * @returns {string}
 */
function buildUserMessage(jdStructure, resumeStructure) {
    return `请对照以下JD要求与简历内容，逐维度分析匹配情况，返回JSON。

【JD结构化要求】
${JSON.stringify(jdStructure, null, 2)}

【简历结构化内容】
${JSON.stringify(resumeStructure, null, 2)}

返回格式：
{
  "match_level": {
    "overall": "高/中/低",
    "ability": "高/中/低",
    "experience": "高/中/低",
    "risk": "高/中/低"
  },
  "analysis_basis": [
    {
      "dimension": "维度名称",
      "items": [
        {
          "type": "match",
          "jd_requirement": "对应的JD要求",
          "content": "匹配说明",
          "quote": "简历原文引用",
          "match_degree": "高/中/低"
        },
        {
          "type": "gap",
          "jd_requirement": "对应的JD要求",
          "content": "简历未体现JD要求的XX",
          "quote": "简历未提及",
          "match_degree": "低"
        }
      ]
    }
  ],
  "strengths": ["基于简历真实内容的优势"],
  "weaknesses": ["JD要求但简历未体现的内容，表述为'简历未体现XX'"]
}`;
}

module.exports = { SYSTEM_PROMPT, buildUserMessage };
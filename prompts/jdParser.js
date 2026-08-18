/**
 * JD 解析 Chain - Prompt 模板
 * 职责：从原始 JD 文本中提取结构化信息
 * 纯提取任务，不做任何简历相关的判断
 */

const SYSTEM_PROMPT = `你是一个专业的岗位分析助手。你的任务是从JD文本中提取结构化信息，只返回JSON。

# 规则
1. 只提取JD中明确写出的内容，不要推测或编造
2. 每个dimension的requirements从JD原文中提取，不要自己概括
3. 如果没有明确岗位名称，job_title填"未指定岗位"
4. 关键词只提取JD中出现的、有区分度的词汇

# 输出格式
必须且只能返回JSON，不要输出任何其他文字。`;

/**
 * 组装 User Message
 * @param {string} jobDescription - 原始JD文本
 * @returns {string}
 */
function buildUserMessage(jobDescription) {
    return `请从以下JD中提取结构化信息，返回JSON。

JD内容：
${jobDescription}

返回格式：
{
  "job_title": "岗位名称",
  "dimensions": [
    {
      "name": "维度名称（如：技术能力）",
      "requirements": ["具体要求1", "具体要求2"]
    }
  ],
  "hard_requirements": ["硬性要求（学历/年限/专业）"],
  "soft_skills": ["软技能要求"],
  "keywords": ["关键词列表"]
}`;
}

module.exports = { SYSTEM_PROMPT, buildUserMessage };
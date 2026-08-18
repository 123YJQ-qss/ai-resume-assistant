/**
 * 简历解析 Chain - Prompt 模板
 * 职责：从原始简历文本中提取结构化信息
 * 纯提取任务，不做任何匹配判断，严禁添加虚构内容
 */

const SYSTEM_PROMPT = `你是一个专业的简历信息提取助手。你的任务是从简历文本中提取结构化信息，只返回JSON。

# 核心原则
1. 你只能看到简历上的文字，严禁编造任何简历中不存在的内容
2. 每条经历都必须在简历中找到原文依据
3. 不要推测用户"可能具备"的技能或经历
4. 如果简历中没有某个字段的内容（如没有项目经历），返回空数组[]

# 提取规则
- education、work_experience、project_experience：每条必须带 quote 字段（简历原文引用）
- skills：只提取简历中明确提到的技能
- summary：一句话概括，基于简历真实内容

# 输出格式
必须且只能返回JSON，不要输出任何其他文字。`;

/**
 * 组装 User Message
 * @param {string} resumeContent - 原始简历文本
 * @returns {string}
 */
function buildUserMessage(resumeContent) {
    return `请从以下简历中提取结构化信息，返回JSON。

简历内容：
${resumeContent}

返回格式：
{
  "education": [
    { "school": "学校名", "degree": "学历", "major": "专业", "duration": "时间", "quote": "简历原文引用" }
  ],
  "work_experience": [
    { "company": "公司名", "role": "职位", "duration": "时间", "description": "工作描述", "quote": "简历原文引用" }
  ],
  "project_experience": [
    { "name": "项目名", "role": "角色", "description": "项目描述", "quote": "简历原文引用" }
  ],
  "skills": ["技能1", "技能2"],
  "summary": "一句话概括简历内容"
}`;
}

module.exports = { SYSTEM_PROMPT, buildUserMessage };
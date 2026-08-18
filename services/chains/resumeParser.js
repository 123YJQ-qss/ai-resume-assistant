/**
 * 简历解析 Chain
 * 职责：从原始简历文本中提取结构化信息
 * 输入：resumeContent (string)
 * 输出：{ education, work_experience, project_experience, skills, summary }
 */

const llmService = require('../llmService');
const { SYSTEM_PROMPT, buildUserMessage } = require('../../prompts/resumeParser');

/**
 * 解析简历，提取结构化信息
 * @param {string} resumeContent - 原始简历文本
 * @returns {Promise<Object>} 结构化简历
 */
async function parse(resumeContent) {
    const userMessage = buildUserMessage(resumeContent);

    const raw = await llmService.structuredChat({
        system: SYSTEM_PROMPT,
        user: userMessage
    });

    return normalizeResume(raw);
}

/**
 * 规范化简历结构，补全缺失字段
 */
function normalizeResume(data) {
    return {
        education: Array.isArray(data.education) ? data.education : [],
        work_experience: Array.isArray(data.work_experience) ? data.work_experience : [],
        project_experience: Array.isArray(data.project_experience) ? data.project_experience : [],
        skills: Array.isArray(data.skills) ? data.skills : [],
        summary: data.summary || ''
    };
}

module.exports = { parse, normalizeResume };
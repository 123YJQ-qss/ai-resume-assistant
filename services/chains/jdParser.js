/**
 * JD 解析 Chain
 * 职责：从原始 JD 文本中提取结构化信息
 * 输入：jobDescription (string)
 * 输出：{ job_title, dimensions, hard_requirements, soft_skills, keywords }
 */

const llmService = require('../llmService');
const { SYSTEM_PROMPT, buildUserMessage } = require('../../prompts/jdParser');

/**
 * 解析 JD，提取结构化信息
 * @param {string} jobDescription - 原始 JD 文本
 * @returns {Promise<Object>} 结构化 JD
 */
async function parse(jobDescription) {
    const userMessage = buildUserMessage(jobDescription);

    const raw = await llmService.structuredChat({
        system: SYSTEM_PROMPT,
        user: userMessage
    });

    return normalizeJD(raw);
}

/**
 * 规范化 JD 结构，补全缺失字段
 */
function normalizeJD(data) {
    return {
        job_title: data.job_title || '未指定岗位',
        dimensions: Array.isArray(data.dimensions) ? data.dimensions.filter(d => d.name) : [],
        hard_requirements: Array.isArray(data.hard_requirements) ? data.hard_requirements : [],
        soft_skills: Array.isArray(data.soft_skills) ? data.soft_skills : [],
        keywords: Array.isArray(data.keywords) ? data.keywords : []
    };
}

module.exports = { parse, normalizeJD };
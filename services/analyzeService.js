/**
 * AI 分析服务层（薄封装）
 * 职责：作为 server.js 与 Workflow Orchestrator 之间的适配层
 * 
 * 注意：所有 LLM 调用和业务编排逻辑已下沉到 services/workflow/orchestrator.js，
 * 此文件仅保留入口函数，保持对外接口稳定。
 */

const orchestrator = require('./workflow/orchestrator');

/**
 * 简历分析主入口
 * @param {string} resumeContent - 简历文本
 * @param {string} jobDescription - 岗位JD
 * @param {Object} [options] - 可选配置（如 context 用于 RAG）
 * @returns {Promise<Object>} 分析结果（与前端格式兼容）
 */
async function analyzeResume(resumeContent, jobDescription, options = {}) {
    return orchestrator.run(resumeContent, jobDescription, options);
}

module.exports = {
    analyzeResume
};
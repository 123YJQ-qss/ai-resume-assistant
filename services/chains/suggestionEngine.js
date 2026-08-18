/**
 * 建议引擎
 * 职责：基于简历结构和匹配结果，生成可执行的优化建议
 * 输入：resumeStructure (Object) + matchResult (Object) + [context] (Object, 预留RAG)
 * 输出：{ rewrite_suggestions, optimization_advice }
 * 
 * context 参数预留：后续接入 RAG 知识库时，可传入行业最佳实践、简历模板等
 */

const llmService = require('../llmService');
const { SYSTEM_PROMPT, buildUserMessage } = require('../../prompts/suggestionEngine');

/**
 * 生成优化建议
 * @param {Object} resumeStructure - 简历结构化数据
 * @param {Object} matchResult - 匹配分析结果
 * @param {Object} [context=null] - 预留：RAG 知识库上下文
 *   context 结构示例：
 *   {
 *     industry: { bestPractices: [...], templates: [...] },
 *     keywords: { required: [...], recommended: [...] },
 *     standards: { format: "...", structure: "..." }
 *   }
 * @returns {Promise<Object>} 建议结果
 */
async function generate(resumeStructure, matchResult, context = null) {
    const userMessage = buildUserMessage(resumeStructure, matchResult, context);

    const raw = await llmService.structuredChat({
        system: SYSTEM_PROMPT,
        user: userMessage
    });

    return normalizeSuggestions(raw);
}

/**
 * 规范化建议结果，补全缺失字段
 */
function normalizeSuggestions(data) {
    return {
        rewrite_suggestions: cleanArrayField(data.rewrite_suggestions),
        optimization_advice: {
            highlight: cleanArrayField(data.optimization_advice?.highlight),
            supplement: cleanArrayField(data.optimization_advice?.supplement),
            expression: cleanArrayField(data.optimization_advice?.expression)
        }
    };
}

/**
 * 清洗数组字段
 */
function cleanArrayField(field) {
    if (!Array.isArray(field)) return [];

    return field.filter(item => {
        if (typeof item === 'string') {
            if (item.trim().length < 3) return false;
            const trimmed = item.trim();
            if (trimmed.startsWith('{') || trimmed.startsWith('[')) return false;
            if (trimmed.startsWith('```')) return false;
            return true;
        }

        if (typeof item === 'object' && item !== null) {
            if ('original' in item || 'revised' in item) {
                return !!(item.original && item.revised);
            }
            return true;
        }

        return false;
    });
}

module.exports = { generate, normalizeSuggestions, cleanArrayField };
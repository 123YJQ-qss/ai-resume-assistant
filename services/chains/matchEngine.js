/**
 * 匹配引擎
 * 职责：对照结构化 JD 和结构化简历，做匹配度判断
 * 输入：jdStructure (Object) + resumeStructure (Object) + originalResume (string)
 * 输出：{ match_level, analysis_basis, strengths, weaknesses }
 * 
 * 包含防虚构机制：verifyQuotes 回查原文引用
 */

const llmService = require('../llmService');
const { SYSTEM_PROMPT, buildUserMessage } = require('../../prompts/matchEngine');

/**
 * 执行岗位匹配分析
 * @param {Object} jdStructure - JD 结构化数据（来自 jdParser）
 * @param {Object} resumeStructure - 简历结构化数据（来自 resumeParser）
 * @param {string} originalResume - 原始简历文本（用于引用回查）
 * @returns {Promise<Object>} 匹配结果
 */
async function match(jdStructure, resumeStructure, originalResume) {
    const userMessage = buildUserMessage(jdStructure, resumeStructure);

    const raw = await llmService.structuredChat({
        system: SYSTEM_PROMPT,
        user: userMessage
    });

    // 规范化
    const result = normalizeResult(raw);

    // 防虚构：回查简历真实来源引用
    verifyQuotes(result, resumeStructure, originalResume);

    return result;
}

/**
 * 规范化结果：补全缺失字段 + 清洗脏数据
 */
function normalizeResult(data) {
    return {
        match_level: {
            overall: data.match_level?.overall || '待评估',
            ability: data.match_level?.ability || '待评估',
            experience: data.match_level?.experience || '待评估',
            risk: data.match_level?.risk || '待评估'
        },
        analysis_basis: cleanArrayField(data.analysis_basis),
        strengths: cleanArrayField(data.strengths),
        weaknesses: cleanArrayField(data.weaknesses)
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
            const jsonChars = (trimmed.match(/[{}[\]":]/g) || []).length;
            if (jsonChars > Math.max(3, trimmed.length * 0.3)) return false;
            return true;
        }

        if (typeof item === 'object' && item !== null) {
            if ('dimension' in item) {
                if (!item.dimension) return false;
                if (item.items && Array.isArray(item.items)) {
                    item.items = cleanArrayField(item.items);
                }
                return true;
            }
            return true;
        }

        return false;
    });
}

/**
 * 简历真实来源引用回查（防虚构）
 * 校验 analysis_basis 中所有 type=match 的 quote 是否来自用户真实简历信息。
 * 校验基准的优先级：
 *   1. resumeStructure（结构化简历：work/education/project/skills 等真实字段）
 *   2. originalResume（原始简历文本，作为兜底）
 * 匹配采用标准化文本比对：去空格、去换行、忽略标点差异。
 * 若引用不实，清除 quote（避免展示编造内容）。
 */
function verifyQuotes(result, resumeStructure, originalResume) {
    if (!result.analysis_basis || !Array.isArray(result.analysis_basis)) return;

    const trustedSnippets = extractTrustedSnippets(resumeStructure).map(normalizeText);
    const normalizedResume = normalizeText(originalResume);

    for (const dimension of result.analysis_basis) {
        if (!dimension.items || !Array.isArray(dimension.items)) continue;

        for (const item of dimension.items) {
            if (item.type !== 'match' || !item.quote || item.quote === '简历未提及') continue;

            const normalizedQuote = normalizeText(item.quote);
            // 过短的引用不做匹配，避免误杀
            if (normalizedQuote.length < 2) continue;

            // 1. 优先：结构化来源池匹配（含双向包含，容忍 AI 少量扩写/摘录）
            let exists = trustedSnippets.some(snippet =>
                snippet.includes(normalizedQuote) || normalizedQuote.includes(snippet)
            );

            // 2. 兜底：原始文本匹配
            if (!exists && normalizedResume) {
                exists = normalizedResume.includes(normalizedQuote);
            }

            if (!exists) {
                console.warn(`[quote-verify] 检测到引用不实，已清除: "${item.quote.substring(0, 50)}..."`);
                item.quote = '';
                item.quote_unverified = true;
            }
        }
    }
}

/**
 * 从结构化简历中提取真实来源片段池
 * 覆盖：work_experience / project_experience / education 的所有字符串字段 + skills 数组
 */
function extractTrustedSnippets(resumeStructure) {
    if (!resumeStructure || typeof resumeStructure !== 'object') return [];

    const snippets = [];

    // skills：字符串数组
    if (Array.isArray(resumeStructure.skills)) {
        for (const skill of resumeStructure.skills) {
            if (typeof skill === 'string' && skill.trim()) snippets.push(skill);
        }
    }

    // education / work_experience / project_experience：对象数组，收集其所有字符串字段
    const objectFields = ['education', 'work_experience', 'project_experience'];
    for (const field of objectFields) {
        if (!Array.isArray(resumeStructure[field])) continue;
        for (const entry of resumeStructure[field]) {
            if (!entry || typeof entry !== 'object') continue;
            for (const value of Object.values(entry)) {
                if (typeof value === 'string' && value.trim()) snippets.push(value);
            }
        }
    }

    return snippets;
}

/**
 * 标准化文本：去除空格、换行、所有中英文标点，并统一小写
 * 用于忽略格式差异的模糊匹配
 */
function normalizeText(text) {
    if (typeof text !== 'string') return '';
    return text
        .replace(/[\s\p{P}]+/gu, '')
        .toLowerCase();
}

module.exports = { match, normalizeResult, cleanArrayField, verifyQuotes };
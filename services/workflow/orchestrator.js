/**
 * Workflow Orchestrator
 * 职责：编排简历分析 Pipeline，控制执行顺序、传递中间结果、处理异常
 * 
 * Pipeline:
 *   Phase 1 (并行): jdParser.parse(JD)  +  resumeParser.parse(Resume)
 *   Phase 2:        matchEngine.match(jdStructure, resumeStructure, originalResume)
 *   Phase 3:        suggestionEngine.generate(resumeStructure, matchResult [, context])
 *   Phase 4:        结果聚合（保持前端格式不变）
 */

const jdParser = require('../chains/jdParser');
const resumeParser = require('../chains/resumeParser');
const matchEngine = require('../chains/matchEngine');
const suggestionEngine = require('../chains/suggestionEngine');

/**
 * 运行完整的简历分析 Pipeline
 * @param {string} resumeContent - 原始简历文本
 * @param {string} jobDescription - 原始 JD 文本
 * @param {Object} [options] - 可选配置
 * @param {Object} [options.context] - RAG 上下文（传入 suggestionEngine）
 * @param {number} [options.maxRetries=2] - 每步最大重试次数
 * @returns {Promise<Object>} 最终分析结果（与前端格式兼容）
 */
async function run(resumeContent, jobDescription, options = {}) {
    const { context = null, maxRetries = 2 } = options;

    const startTime = Date.now();
    console.log('🚀 [Pipeline] 开始执行...');

    // ============================================================
    // Phase 1: 并行提取（JD + 简历）
    // ============================================================
    console.log('📋 [Pipeline] Phase 1: 并行提取 JD 和简历...');
    const phase1Start = Date.now();

    let jdStructure, resumeStructure;
    try {
        [jdStructure, resumeStructure] = await Promise.all([
            executeWithRetry(() => jdParser.parse(jobDescription), maxRetries, 'jdParser'),
            executeWithRetry(() => resumeParser.parse(resumeContent), maxRetries, 'resumeParser')
        ]);
    } catch (error) {
        throw new PipelineError('Phase1', 'JD或简历解析失败，请检查输入内容', error);
    }

    console.log(`  ✅ JD解析完成: ${jdStructure.dimensions.length}个维度, ${jdStructure.keywords.length}个关键词`);
    console.log(`  ✅ 简历解析完成: ${resumeStructure.skills.length}个技能, ${resumeStructure.work_experience.length}段工作经历`);
    console.log(`  ⏱ Phase 1 耗时: ${Date.now() - phase1Start}ms`);

    // ============================================================
    // Phase 2: 匹配分析
    // ============================================================
    console.log('🔍 [Pipeline] Phase 2: 岗位匹配分析...');
    const phase2Start = Date.now();

    let matchResult;
    try {
        matchResult = await executeWithRetry(
            () => matchEngine.match(jdStructure, resumeStructure, resumeContent),
            maxRetries,
            'matchEngine'
        );
    } catch (error) {
        console.error('  ⚠️ 匹配分析失败，返回待评估状态');
        matchResult = getFallbackMatchResult();
    }

    console.log(`  ✅ 匹配度: overall=${matchResult.match_level.overall}, ability=${matchResult.match_level.ability}, experience=${matchResult.match_level.experience}`);
    console.log(`  ⏱ Phase 2 耗时: ${Date.now() - phase2Start}ms`);

    // ============================================================
    // Phase 3: 建议生成
    // ============================================================
    console.log('💡 [Pipeline] Phase 3: 生成优化建议...');
    const phase3Start = Date.now();

    let suggestions;
    try {
        suggestions = await executeWithRetry(
            () => suggestionEngine.generate(resumeStructure, matchResult, context),
            maxRetries,
            'suggestionEngine'
        );
    } catch (error) {
        console.error('  ⚠️ 建议生成失败，返回空建议');
        suggestions = getFallbackSuggestions();
    }

    console.log(`  ✅ 改写建议: ${suggestions.rewrite_suggestions.length}条`);
    console.log(`  ⏱ Phase 3 耗时: ${Date.now() - phase3Start}ms`);

    // ============================================================
    // Phase 4: 结果聚合
    // ============================================================
    const finalResult = assembleResult(matchResult, suggestions);

    console.log(`🏁 [Pipeline] 完成，总耗时: ${Date.now() - startTime}ms`);
    return finalResult;
}

/**
 * 带重试的执行器
 * @param {Function} fn - 异步函数
 * @param {number} maxRetries - 最大重试次数
 * @param {string} stepName - 步骤名称（日志用）
 * @returns {Promise<any>}
 */
async function executeWithRetry(fn, maxRetries, stepName) {
    let lastError;

    for (let attempt = 0; attempt <= maxRetries; attempt++) {
        try {
            if (attempt > 0) {
                console.log(`  🔄 [${stepName}] 重试第 ${attempt} 次...`);
            }
            return await fn();
        } catch (error) {
            lastError = error;
            console.warn(`  ⚠️ [${stepName}] 第 ${attempt + 1} 次尝试失败: ${error.message}`);
        }
    }

    throw lastError;
}

/**
 * 聚合最终结果（保持前端格式不变）
 */
function assembleResult(matchResult, suggestions) {
    return {
        match_level: matchResult.match_level || {
            overall: '待评估',
            ability: '待评估',
            experience: '待评估',
            risk: '待评估'
        },
        analysis_basis: matchResult.analysis_basis || [],
        strengths: matchResult.strengths || [],
        weaknesses: matchResult.weaknesses || [],
        rewrite_suggestions: suggestions.rewrite_suggestions || [],
        optimization_advice: suggestions.optimization_advice || {
            highlight: [],
            supplement: [],
            expression: []
        }
    };
}

/**
 * 匹配结果降级（当匹配引擎失败时）
 */
function getFallbackMatchResult() {
    return {
        match_level: {
            overall: '待评估',
            ability: '待评估',
            experience: '待评估',
            risk: '待评估'
        },
        analysis_basis: [],
        strengths: [],
        weaknesses: []
    };
}

/**
 * 建议结果降级（当建议引擎失败时）
 */
function getFallbackSuggestions() {
    return {
        rewrite_suggestions: [],
        optimization_advice: {
            highlight: [],
            supplement: [],
            expression: []
        }
    };
}

/**
 * Pipeline 错误类
 */
class PipelineError extends Error {
    constructor(phase, message, cause) {
        super(`[${phase}] ${message}`);
        this.name = 'PipelineError';
        this.phase = phase;
        this.cause = cause;
    }
}

module.exports = { run, PipelineError };
/**
 * 评估模块
 * 用于测试 Pipeline 各模块在不同 JD + 简历案例下的输出效果
 * 
 * 用法：
 *   node services/evaluation/evaluator.js              # 运行全部案例
 *   node services/evaluation/evaluator.js --case 0     # 运行指定案例
 */

const path = require('path');
const fs = require('fs');
const orchestrator = require('../workflow/orchestrator');
const jdParser = require('../chains/jdParser');
const resumeParser = require('../chains/resumeParser');
const matchEngine = require('../chains/matchEngine');
const suggestionEngine = require('../chains/suggestionEngine');

/**
 * 加载测试案例
 */
function loadCases() {
    const casesPath = path.join(__dirname, '..', '..', 'test-cases', 'cases.json');
    if (!fs.existsSync(casesPath)) {
        console.warn('⚠️ 未找到测试案例文件 test-cases/cases.json');
        return [];
    }
    return JSON.parse(fs.readFileSync(casesPath, 'utf-8'));
}

/**
 * 运行单个案例
 * @param {Object} testCase - { name, jd, resume, expectedHighlights? }
 * @returns {Promise<Object>} { name, success, result, timing, errors }
 */
async function runCase(testCase) {
    const timing = { start: Date.now() };
    const errors = [];

    console.log(`\n📋 测试案例: ${testCase.name}`);
    console.log('─'.repeat(60));

    try {
        // 运行完整 Pipeline
        const result = await orchestrator.run(testCase.resume, testCase.jd);
        timing.total = Date.now() - timing.start;

        // 基础质量检查
        const checks = {
            hasMatchLevel: !!result.match_level?.overall && result.match_level.overall !== '待评估',
            hasAnalysisBasis: result.analysis_basis?.length > 0,
            hasStrengths: result.strengths?.length > 0,
            hasWeaknesses: result.weaknesses?.length > 0,
            hasRewriteSuggestions: result.rewrite_suggestions?.length > 0,
            hasOptimizationAdvice: (
                result.optimization_advice?.highlight?.length > 0 ||
                result.optimization_advice?.supplement?.length > 0 ||
                result.optimization_advice?.expression?.length > 0
            )
        };

        const passedChecks = Object.values(checks).filter(Boolean).length;
        const totalChecks = Object.keys(checks).length;

        console.log(`  匹配度: ${result.match_level.overall}/${result.match_level.ability}/${result.match_level.experience}/${result.match_level.risk}`);
        console.log(`  分析维度: ${result.analysis_basis.length}个`);
        console.log(`  优势: ${result.strengths.length}条 | 不足: ${result.weaknesses.length}条`);
        console.log(`  改写建议: ${result.rewrite_suggestions.length}条`);
        console.log(`  质量检查: ${passedChecks}/${totalChecks} 通过`);
        console.log(`  耗时: ${timing.total}ms`);

        return {
            name: testCase.name,
            success: true,
            result,
            timing,
            checks: { passed: passedChecks, total: totalChecks, details: checks }
        };

    } catch (error) {
        timing.total = Date.now() - timing.start;
        errors.push(error.message);

        console.log(`  ❌ 失败: ${error.message}`);
        console.log(`  耗时: ${timing.total}ms`);

        return {
            name: testCase.name,
            success: false,
            result: null,
            timing,
            errors
        };
    }
}

/**
 * 单模块测试：分别测试 JD 解析、简历解析、匹配、建议
 * @param {Object} testCase
 */
async function runModuleTests(testCase) {
    console.log(`\n🔬 模块级测试: ${testCase.name}`);
    console.log('─'.repeat(60));

    const results = {};

    // 测试 JD 解析
    try {
        const jd = await jdParser.parse(testCase.jd);
        results.jdParser = { success: true, dimensions: jd.dimensions.length, keywords: jd.keywords.length };
        console.log(`  ✅ jdParser: ${jd.dimensions.length}维度, ${jd.keywords.length}关键词`);
    } catch (e) {
        results.jdParser = { success: false, error: e.message };
        console.log(`  ❌ jdParser: ${e.message}`);
    }

    // 测试简历解析
    try {
        const resume = await resumeParser.parse(testCase.resume);
        results.resumeParser = { success: true, skills: resume.skills.length, experiences: resume.work_experience.length };
        console.log(`  ✅ resumeParser: ${resume.skills.length}技能, ${resume.work_experience.length}段经历`);
    } catch (e) {
        results.resumeParser = { success: false, error: e.message };
        console.log(`  ❌ resumeParser: ${e.message}`);
    }

    return results;
}

/**
 * 打印汇总报告
 */
function printSummary(allResults) {
    console.log('\n' + '='.repeat(60));
    console.log('📊 评估汇总');
    console.log('='.repeat(60));

    const total = allResults.length;
    const success = allResults.filter(r => r.success).length;
    const fail = total - success;

    console.log(`  总案例: ${total} | 成功: ${success} | 失败: ${fail}`);
    console.log(`  平均耗时: ${Math.round(allResults.reduce((s, r) => s + r.timing.total, 0) / total)}ms`);

    if (success > 0) {
        const avgChecks = allResults
            .filter(r => r.success && r.checks)
            .reduce((s, r) => s + r.checks.passed, 0) / success;
        console.log(`  平均质量检查通过率: ${(avgChecks / 6 * 100).toFixed(1)}%`);
    }

    console.log('');
}

// ============================================================
// CLI 入口
// ============================================================
if (require.main === module) {
    const args = process.argv.slice(2);
    const caseIndex = args.includes('--case') ? parseInt(args[args.indexOf('--case') + 1]) : null;

    const llmConfig = require('../../config/llm');
    if (!llmConfig.apiKey) {
        console.error('❌ 未配置 LLM_API_KEY，无法运行评估');
        console.error('   请在 .env 文件中添加 LLM_API_KEY');
        process.exit(1);
    }

    (async () => {
        const allCases = loadCases();

        if (allCases.length === 0) {
            console.log('请在 test-cases/cases.json 中添加测试案例');
            console.log('示例格式: [{"name": "案例1", "jd": "...", "resume": "..."}]');
            process.exit(0);
        }

        const casesToRun = caseIndex !== null
            ? [allCases[caseIndex]].filter(Boolean)
            : allCases;

        console.log(`🧪 开始评估，共 ${casesToRun.length} 个案例\n`);

        const allResults = [];
        for (const testCase of casesToRun) {
            const result = await runCase(testCase);
            allResults.push(result);
        }

        printSummary(allResults);
        process.exit(0);
    })();
}

module.exports = { runCase, runModuleTests, loadCases };
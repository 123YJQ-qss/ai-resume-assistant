/* ============================================================
   AI Resume Assistant - 交互逻辑
   功能：页面导航、文件上传、API调用、结果渲染
   ============================================================ */

// ==================== API配置 ====================
// 部署时修改此处为你的后端公网地址
// 本地开发: 'http://localhost:3000'
// 部署后:   'https://your-backend.onrender.com' 或 'https://your-backend.railway.app'
const API_BASE_URL = '';  // 留空表示使用当前域名（推荐部署模式）
// const API_BASE_URL = 'http://localhost:3000';  // 本地开发模式

const API_BASE = API_BASE_URL || window.location.origin;

// -------------------- 全局状态 --------------------
let uploadedFile = null;

// -------------------- 页面导航 --------------------

/**
 * 切换页面（section）
 */
function navigateTo(pageId) {
    document.querySelectorAll('.page').forEach(page => {
        page.classList.remove('active');
    });
    const targetPage = document.getElementById(pageId);
    if (targetPage) {
        targetPage.classList.add('active');
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }
}

// -------------------- 文件上传 --------------------

const uploadArea = document.getElementById('uploadArea');
const fileInput = document.getElementById('fileInput');
const uploadSuccess = document.getElementById('uploadSuccess');
const fileName = document.getElementById('fileName');

uploadArea.addEventListener('click', (e) => {
    if (e.target.closest('.upload-success')) {
        fileInput.click();
    } else {
        fileInput.click();
    }
});

uploadArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadArea.classList.add('dragover');
});

uploadArea.addEventListener('dragleave', () => {
    uploadArea.classList.remove('dragover');
});

uploadArea.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadArea.classList.remove('dragover');
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        handleFile(files[0]);
    }
});

fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        handleFile(e.target.files[0]);
    }
});

/**
 * 处理上传的文件 - 保存文件引用供后续API调用
 */
function handleFile(file) {
    const allowedTypes = [
        'application/pdf',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    ];

    if (!allowedTypes.includes(file.type)) {
        alert('请上传 PDF 或 Word 格式的文件');
        return;
    }

    // 保存文件引用
    uploadedFile = file;

    // 显示上传成功
    uploadArea.classList.add('uploaded');
    fileName.textContent = file.name;
}

// -------------------- 示例JD填充 --------------------

const jdExamples = {
    pm: `AI产品经理岗位：

【岗位职责】
1. 负责AI产品的需求分析、用户研究和产品规划，推动产品从0到1落地
2. 深入理解AI技术能力边界，设计合理的产品方案，平衡技术实现与用户体验
3. 与算法、工程团队紧密协作，推进产品迭代，确保产品按时高质量交付
4. 通过数据分析、用户反馈等方式持续优化产品，提升核心指标

【任职要求】
1. 本科及以上学历，计算机、软件工程、人工智能等相关专业优先
2. 具备产品需求分析、PRD撰写、原型设计等基本功
3. 对AI技术有基本理解，了解Prompt Engineering、Agent等概念
4. 具备良好的逻辑思维和沟通表达能力`,
    dev: `前端开发工程师岗位：

【岗位职责】
1. 负责公司核心产品的前端架构设计与开发
2. 与UI/UX设计师配合，实现高质量的用户界面
3. 优化前端性能，提升用户体验
4. 参与前端工程化建设，包括组件库、脚手架等

【任职要求】
1. 本科及以上学历，计算机相关专业
2. 熟练掌握HTML、CSS、JavaScript，熟悉ES6+规范
3. 熟悉React或Vue框架，有实际项目经验
4. 了解前端工程化工具（Webpack、Vite等）`,
    data: `数据分析师岗位：

【岗位职责】
1. 负责业务数据的采集、清洗和分析，为业务决策提供数据支持
2. 搭建数据指标体系，监控关键业务指标变化
3. 通过数据挖掘发现业务增长点，推动业务优化
4. 撰写数据分析报告，向管理层汇报分析结果

【任职要求】
1. 本科及以上学历，统计学、数学、计算机等相关专业
2. 熟练使用SQL，掌握Python或R进行数据分析
3. 熟悉常用的数据可视化工具（Tableau、PowerBI等）
4. 具备良好的数据敏感度和逻辑分析能力`
};

function fillExample(type) {
    const jdInput = document.getElementById('jdInput');
    if (jdExamples[type]) {
        jdInput.value = jdExamples[type];
        jdInput.style.transition = 'none';
        jdInput.style.borderColor = 'var(--accent)';
        setTimeout(() => {
            jdInput.style.transition = 'var(--transition)';
            jdInput.style.borderColor = 'var(--border)';
        }, 600);
    }
}

// -------------------- AI分析流程 --------------------

/**
 * 校验JD内容质量（与后端validateJDQuality保持一致）
 */
function validateJDQuality(jdText) {
    const text = jdText.trim();
    
    if (text.length < 10) {
        return { valid: false, reason: '岗位JD内容过短，请提供更详细的职位描述' };
    }
    
    const chineseChars = (text.match(/[\u4e00-\u9fa5]/g) || []).length;
    const totalChars = text.length;
    const chineseRatio = chineseChars / totalChars;
    
    if (chineseRatio < 0.3) {
        return { valid: false, reason: '岗位JD中文字符过少（不足30%），请输入真实的中文岗位描述' };
    }
    
    const digitChars = (text.match(/[0-9]/g) || []).length;
    const digitRatio = digitChars / totalChars;
    if (digitRatio > 0.7) {
        return { valid: false, reason: '岗位JD数字过多（超过70%），请输入包含具体职责要求的文字描述' };
    }
    
    const jobKeywords = ['岗位', '职责', '要求', '经验', '学历', '专业', '负责', '能力', '任职', '岗位描述', '技能', '技术', '产品', '开发', '设计', '运营', '市场', '管理', '分析', '研究', '客户', '用户', '团队', '项目', '规划', '组织', '沟通', '协调', '推动', '建立', '制定'];
    const hasKeyword = jobKeywords.some(kw => text.includes(kw));
    if (!hasKeyword) {
        return { valid: false, reason: '岗位JD缺少有效的岗位描述关键词（如"职责""要求""经验"等），请输入更完整的岗位信息' };
    }
    
    return { valid: true, reason: '' };
}

/**
 * 开始分析 - 调用后端API
 */
async function startAnalysis() {
    const jdInput = document.getElementById('jdInput');
    const jdFilled = jdInput.value.trim().length > 0;

    // 校验
    if (!uploadedFile && !jdFilled) {
        alert('请先上传简历并填写目标岗位JD');
        return;
    }
    if (!uploadedFile) {
        alert('请先上传简历文件');
        return;
    }
    if (!jdFilled) {
        alert('请填写目标岗位JD');
        return;
    }
    
    // JD质量校验
    const jdValidation = validateJDQuality(jdInput.value);
    if (!jdValidation.valid) {
        alert(jdValidation.reason);
        return;
    }

    // 禁用按钮
    const analyzeBtn = document.getElementById('analyzeBtn');
    analyzeBtn.disabled = true;
    analyzeBtn.innerHTML = '<span class="btn-icon">⏳</span> 分析中...';

    // 跳转到Loading页面
    navigateTo('loading');
    resetLoadingSteps();

    try {
        // 步骤1：解析简历（立即完成）
        setLoadingStep(1, 'active');
        const formData = new FormData();
        formData.append('file', uploadedFile);
        formData.append('job_description', jdInput.value);
        
        // 用微任务模拟步骤1完成（简历解析是本地操作，很快）
        await new Promise(r => setTimeout(r, 300));
        setLoadingStep(1, 'done');
        setLoadingStep(2, 'active');
        
        // 步骤2：解析JD（立即完成）
        await new Promise(r => setTimeout(r, 200));
        setLoadingStep(2, 'done');
        setLoadingStep(3, 'active');
        
        // 步骤3：AI深度分析（等待API返回，带计时器显示）
        const startTime = Date.now();
        const timerInterval = setInterval(() => {
            const elapsed = Math.floor((Date.now() - startTime) / 1000);
            const step3 = document.getElementById('loadingStep3');
            if (step3) {
                const label = step3.querySelector('.step-text');
                if (label) {
                    label.textContent = `正在匹配与生成分析建议（已用时${elapsed}秒）`;
                }
            }
        }, 1000);

        const response = await fetch(`${API_BASE}/api/analyze`, {
            method: 'POST',
            body: formData
        });
        
        clearInterval(timerInterval);

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.error || '分析服务暂时不可用');
        }

        const result = await response.json();
        
        // 步骤3完成，进入步骤4
        setLoadingStep(3, 'done');
        setLoadingStep(4, 'active');
        
        // 步骤4：渲染结果
        await new Promise(r => setTimeout(r, 300));
        setLoadingStep(4, 'done');
        
        if (result.success && result.data) {
            const validatedData = validateAndNormalizeData(result.data);
            renderAnalysisResult(validatedData, result.data_source, result.warning);
        } else {
            throw new Error('返回数据格式异常，请稍后重试');
        }

        analyzeBtn.disabled = false;
        analyzeBtn.innerHTML = '<span class="btn-icon">🔍</span> 开始分析';
        navigateTo('result');

    } catch (error) {
        console.error('分析失败:', error);
        clearInterval(window._loadingTimer);
        
        analyzeBtn.disabled = false;
        analyzeBtn.innerHTML = '<span class="btn-icon">🔍</span> 开始分析';
        showLoadingError(error.message);
    }
}

/**
 * 校验并规范化返回数据
 * 确保即使AI返回的数据不完整，页面也能正常展示
 */
function validateAndNormalizeData(data) {
    const normalized = {
        match_level: data.match_level || {
            overall: '待评估',
            ability: '待评估',
            experience: '待评估',
            risk: '待评估'
        },
        analysis_basis: data.analysis_basis || [],
        strengths: data.strengths || [],
        weaknesses: data.weaknesses || [],
        rewrite_suggestions: data.rewrite_suggestions || [],
        optimization_advice: data.optimization_advice || {
            highlight: [],
            supplement: [],
            expression: []
        }
    };

    // 确保 match_level 子字段存在
    normalized.match_level = {
        overall: normalized.match_level.overall || '待评估',
        ability: normalized.match_level.ability || '待评估',
        experience: normalized.match_level.experience || '待评估',
        risk: normalized.match_level.risk || '待评估'
    };

    return normalized;
}

/**
 * 在Loading页面显示错误信息
 */
function showLoadingError(errorMessage) {
    const loadingPage = document.getElementById('loading');
    if (!loadingPage) {
        // 如果找不到loading页面，直接跳转回输入页
        alert('分析失败：' + errorMessage);
        navigateTo('input');
        return;
    }

    // 创建错误提示HTML
    const errorHtml = `
        <div class="loading-error">
            <div class="error-icon">⚠️</div>
            <h3>分析遇到问题</h3>
            <p class="error-message">${errorMessage}</p>
            <div class="error-actions">
                <button class="btn btn-primary" onclick="navigateTo('input')">返回修改</button>
                <button class="btn btn-secondary" onclick="location.reload()">刷新页面</button>
            </div>
        </div>
    `;

    // 插入错误信息到loading页面
    const loadingContent = loadingPage.querySelector('.loading-content');
    if (loadingContent) {
        loadingContent.innerHTML = errorHtml;
    } else {
        alert('分析失败：' + errorMessage);
        navigateTo('input');
    }
}

// -------------------- Loading控制 --------------------

function resetLoadingSteps() {
    for (let i = 1; i <= 4; i++) {
        const step = document.getElementById('loadingStep' + i);
        if (step) {
            step.classList.remove('active', 'done');
        }
    }
}

function setLoadingStep(stepNum, status) {
    const step = document.getElementById('loadingStep' + stepNum);
    if (step) {
        step.classList.remove('active', 'done');
        step.classList.add(status);
    }
}

// -------------------- 动态渲染分析结果 --------------------

/**
 * 渲染AI分析结果到结果页
 * @param {Object} data - 后端返回的分析结果
 * @param {string} dataSource - 数据来源标识
 * @param {string} warning - 警告信息
 */
function renderAnalysisResult(data, dataSource, warning) {
    // 清空所有静态占位内容，确保动态渲染
    clearResultPage();

    // 显示数据来源标识
    showDataSourceBadge(dataSource, warning);

    // 1. 渲染岗位匹配分析
    renderMatchLevel(data.match_level);
    
    // 2. 渲染AI判断依据
    renderAnalysisBasis(data.analysis_basis);
    
    // 3. 渲染简历优势
    renderStrengths(data.strengths);
    
    // 4. 渲染存在不足
    renderWeaknesses(data.weaknesses);
    
    // 5. 渲染修改前后对比（基于 rewrite_suggestions）
    renderComparison(data);
    
    // 6. 渲染AI优化建议（基于 optimization_advice）
    renderSuggestions(data);
}

/**
 * 清空结果页面所有容器
 */
function clearResultPage() {
    const containers = [
        '.match-content-verbal',
        '#analysisBasisContent',
        '#strengthsList',
        '#weaknessesList',
        '#comparisonContent',
        '#suggestionsContent'
    ];
    
    containers.forEach(selector => {
        const el = document.querySelector(selector);
        if (el) el.innerHTML = '';
    });
    
    // 清除通用容器（兜底）
    const basisBody = document.querySelectorAll('.result-card')[1]?.querySelector('.card-body');
    if (basisBody && basisBody.id !== 'analysisBasisContent') {
        // 已经通过ID处理，跳过
    }
}

/**
 * 显示数据来源标识
 */
function showDataSourceBadge(dataSource, warning) {
    const existing = document.querySelector('.data-source-badge');
    if (existing) existing.remove();
    
    const badge = document.createElement('div');
    badge.className = 'data-source-badge';
    
    if (dataSource === 'coze_api') {
        badge.innerHTML = '<span class="badge-real">● AI实时分析结果</span>';
    } else if (dataSource === 'coze_api_partial') {
        badge.innerHTML = '<span class="badge-partial">⚠ 部分分析结果</span><span class="badge-msg">' + (warning || '') + '</span>';
    } else if (dataSource === 'coze_api_idle') {
        badge.innerHTML = '<span class="badge-real">● AI分析结果</span>';
    } else if (dataSource === 'invalid_input') {
        badge.innerHTML = '<span class="badge-mock">⚠ 输入无效</span><span class="badge-msg">' + (warning || '请检查输入内容') + '</span>';
    } else if (dataSource === 'mock_fallback') {
        badge.innerHTML = '<span class="badge-mock">⚠ 示例数据</span><span class="badge-msg">' + (warning || 'AI分析服务暂不可用，当前显示示例数据') + '</span>';
    } else {
        badge.innerHTML = '<span class="badge-real">● AI分析结果</span>';
    }
    
    const pageHeader = document.querySelector('#result .page-header');
    if (pageHeader) {
        pageHeader.appendChild(badge);
    }
}

/**
 * 渲染岗位匹配程度
 */
function renderMatchLevel(matchLevel) {
    const container = document.querySelector('.match-content-verbal');
    if (!container || !matchLevel) return;

    container.innerHTML = `
        <div class="verbal-item overall">
            <span class="verbal-label">综合匹配程度</span>
            <span class="verbal-value high">${matchLevel.overall || '待评估'}</span>
        </div>
        <div class="verbal-items">
            <div class="verbal-item">
                <span class="verbal-label">能力匹配</span>
                <span class="verbal-value strong">${matchLevel.ability || '待评估'}</span>
            </div>
            <div class="verbal-item">
                <span class="verbal-label">经历匹配</span>
                <span class="verbal-value medium">${matchLevel.experience || '待评估'}</span>
            </div>
            <div class="verbal-item">
                <span class="verbal-label">岗位风险</span>
                <span class="verbal-value warn">${matchLevel.risk || '待评估'}</span>
            </div>
        </div>
    `;
}

/**
 * 渲染AI判断依据（按维度分组）
 */
function renderAnalysisBasis(analysisBasis) {
    const container = document.querySelector('.ai-reason') || 
                      document.querySelector('.result-card .card-body');
    if (!container || !analysisBasis || analysisBasis.length === 0) return;

    // 找到AI判断依据的card-body
    const basisCard = document.querySelectorAll('.result-card')[1];
    const basisBody = basisCard ? basisCard.querySelector('.card-body') : null;
    if (!basisBody) return;

    basisBody.innerHTML = analysisBasis.map(dimension => `
        <div class="dimension-block">
            <h4 class="dimension-title">【维度：${dimension.dimension}】</h4>
            <div class="dimension-items">
                ${dimension.items.map(item => `
                    <div class="dimension-item ${item.type === 'match' ? 'match' : 'gap'}">
                        <span class="dim-icon">${item.type === 'match' ? '✓' : '⚠'}</span>
                        <span class="dim-label">${item.type === 'match' ? '匹配项：' : '待补充项：'}</span>
                        <span class="dim-content">${item.content}</span>
                        ${item.quote ? `<span class="dim-quote">（简历原文："${item.quote}"）</span>` : ''}
                        <span class="dim-badge ${item.match_degree === '高' ? 'high' : item.match_degree === '中' ? 'medium' : 'low'}">
                            匹配度：${item.match_degree || '待评估'}
                        </span>
                    </div>
                `).join('')}
            </div>
        </div>
    `).join('');
}

/**
 * 渲染简历优势
 */
function renderStrengths(strengths) {
    const cards = document.querySelectorAll('.result-card');
    const advantageCard = cards[2];
    if (!advantageCard) return;

    const list = advantageCard.querySelector('.result-list') || 
                 document.getElementById('strengthsList');
    if (!list) return;

    if (!strengths || strengths.length === 0) {
        list.innerHTML = '<li class="placeholder-text">暂无数据</li>';
        return;
    }

    list.innerHTML = strengths.map((item, index) => `
        <li class="result-item advantage">
            <span class="item-marker">▸</span>
            <span>${item}</span>
            <span class="dim-tag">优势${index + 1}</span>
        </li>
    `).join('');
}

/**
 * 渲染存在不足
 */
function renderWeaknesses(weaknesses) {
    const cards = document.querySelectorAll('.result-card');
    const weaknessCard = cards[3];
    if (!weaknessCard) return;

    const list = weaknessCard.querySelector('.result-list') ||
                 document.getElementById('weaknessesList');
    if (!list) return;

    if (!weaknesses || weaknesses.length === 0) {
        list.innerHTML = '<li class="placeholder-text">暂无数据</li>';
        return;
    }

    list.innerHTML = weaknesses.map((item, index) => `
        <li class="result-item weakness">
            <span class="item-marker">▸</span>
            <span>${item}</span>
            <span class="dim-tag">不足${index + 1}</span>
        </li>
    `).join('');
}

/**
 * 渲染修改前后对比（使用后端返回的 rewrite_suggestions）
 */
function renderComparison(data) {
    const cards = document.querySelectorAll('.result-card');
    const compareCard = cards[4];
    if (!compareCard) return;

    const body = compareCard.querySelector('.card-body');
    if (!body) return;

    // 使用后端返回的 rewrite_suggestions
    const rewriteSuggestions = data.rewrite_suggestions || [];

    if (rewriteSuggestions.length === 0) {
        body.innerHTML = '<p style="color: var(--text-secondary); text-align: center; padding: 20px;">暂无改写建议</p>';
        return;
    }

    body.innerHTML = rewriteSuggestions.map((item, index) => `
        <div class="compare-block">
            <div class="compare-grid">
                <div class="compare-col before">
                    <div class="compare-label">修改前</div>
                    <div class="compare-content">
                        <p>${item.original || '原文'}</p>
                    </div>
                </div>
                <div class="compare-arrow">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <line x1="5" y1="12" x2="19" y2="12"/>
                        <polyline points="12 5 19 12 12 19"/>
                    </svg>
                </div>
                <div class="compare-col after">
                    <div class="compare-label">修改后</div>
                    <div class="compare-content">
                        <p>${item.revised || '建议改写'}</p>
                    </div>
                </div>
            </div>
            ${item.basis ? `<p class="compare-reason">改写依据：${item.basis}</p>` : ''}
        </div>
    `).join('');
}

/**
 * 渲染AI优化建议（使用后端返回的 optimization_advice）
 */
function renderSuggestions(data) {
    const cards = document.querySelectorAll('.result-card');
    const suggestionCard = cards[5];
    if (!suggestionCard) return;

    const body = suggestionCard.querySelector('.card-body');
    if (!body) return;

    // 使用后端返回的 optimization_advice
    const advice = data.optimization_advice || {};

    body.innerHTML = `
        <div class="ai-suggestions">
            ${advice.highlight && advice.highlight.length > 0 ? `
                <div class="suggestion-group">
                    <h4 class="suggestion-group-title">💡 建议突出哪些经历</h4>
                    <ul class="suggestion-list">
                        ${advice.highlight.map(item => `<li>${item}</li>`).join('')}
                    </ul>
                </div>
            ` : ''}
            ${advice.supplement && advice.supplement.length > 0 ? `
                <div class="suggestion-group">
                    <h4 class="suggestion-group-title">📝 建议补充哪些信息</h4>
                    <ul class="suggestion-list">
                        ${advice.supplement.map(item => `<li>${item}</li>`).join('')}
                    </ul>
                </div>
            ` : ''}
            ${advice.expression && advice.expression.length > 0 ? `
                <div class="suggestion-group">
                    <h4 class="suggestion-group-title">✨ 建议优化哪些表达</h4>
                    <ul class="suggestion-list">
                        ${advice.expression.map(item => `<li>${item}</li>`).join('')}
                    </ul>
                </div>
            ` : ''}
            ${(!advice.highlight || advice.highlight.length === 0) && 
              (!advice.supplement || advice.supplement.length === 0) && 
              (!advice.expression || advice.expression.length === 0) ? `
                <p style="color: var(--text-secondary); text-align: center; padding: 20px;">暂无优化建议</p>
            ` : ''}
        </div>
    `;
}

// -------------------- 初始化 --------------------

document.addEventListener('DOMContentLoaded', () => {
    navigateTo('landing');
});

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

    // 重置 Tab 到匹配概览
    document.querySelectorAll('.result-tab').forEach(t => t.classList.remove('active'));
    const firstTab = document.querySelector('.result-tab[data-tab="overview"]');
    if (firstTab) firstTab.classList.add('active');
    document.querySelectorAll('.result-tab-pane').forEach(p => p.classList.remove('active'));
    const firstPane = document.getElementById('tab-overview');
    if (firstPane) firstPane.classList.add('active');

    // 显示数据来源标识
    showDataSourceBadge(dataSource, warning);

    // 1. 渲染岗位匹配分析
    renderMatchLevel(data.match_level);
    renderKeyGaps(data);
    
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
    const ids = [
        'analysisBasisContent',
        'strengthsList',
        'weaknessesList',
        'comparisonContent',
        'suggestionsContent'
    ];
    ids.forEach(id => {
        const el = document.getElementById(id);
        if (el) el.innerHTML = '';
    });
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

    // 匹配总结文字
    const summaryMap = {
        '较高': '核心技术栈与岗位高度匹配，建议重点突出项目成果和 AI 落地经验。',
        '中等': '技术方向基本对口，但缺少一些关键经历或量化成果，建议补充项目细节。',
        '较低': '方向有偏差，需要在简历中重点强化岗位相关的技术栈和项目经历。',
        '需要优化': '岗位风险较高，建议先做针对性优化再投递。',
        '待评估': '正在评估中...'
    };
    const overall = matchLevel.overall || '待评估';
    const summary = summaryMap[overall] || '基于 JD 核心要求与简历内容的综合判断。';

    // 更新总结
    const summaryEl = document.getElementById('matchSummary');
    if (summaryEl) summaryEl.textContent = summary;

    // 更新四个匹配标签（只改文字，不改 DOM 结构）
    const overallVal = container.querySelector('.verbal-item.overall .verbal-value');
    if (overallVal) overallVal.textContent = overall;

    const subItems = container.querySelectorAll('.verbal-items .verbal-item');
    const subKeys = ['ability', 'experience', 'risk'];
    subItems.forEach((item, i) => {
        const key = subKeys[i];
        const val = matchLevel[key] || '待评估';
        const valEl = item.querySelector('.verbal-value');
        if (valEl) valEl.textContent = val;
    });
}

/**
 * 解析文本开头的 [类型标记]，返回 { type, text }
 * 支持的类型：表达优化 / 事实待确认 / 能力缺口 / 需补充真实信息
 */
function parseTypeTag(raw) {
    if (!raw || typeof raw !== 'string') return { type: null, text: '' };
    const m = raw.match(/^\s*\[([^\]]+)\]\s*/);
    if (m) {
        return { type: m[1].trim(), text: raw.slice(m[0].length).trim() };
    }
    return { type: null, text: raw.trim() };
}

/**
 * 把类型映射为 UI 显示用的 key 和样式 class
 */
function typeTagStyle(type) {
    if (!type) return { key: 'unknown', cls: 'tag-unknown', label: '待分类' };
    if (type.includes('表达')) return { key: 'expr', cls: 'tag-expr', label: '表达优化' };
    if (type.includes('事实')) return { key: 'confirm', cls: 'tag-confirm', label: '事实待确认' };
    if (type.includes('能力')) return { key: 'gap', cls: 'tag-gap', label: '能力缺口' };
    if (type.includes('补充')) return { key: 'info', cls: 'tag-info', label: '需真实信息' };
    return { key: 'other', cls: 'tag-other', label: type };
}

/**
 * 全局切换 Tab（用于 onclick 跳转）
 */
function switchTab(tabName) {
    document.querySelectorAll('.result-tab').forEach(t => t.classList.remove('active'));
    const tab = document.querySelector('.result-tab[data-tab="' + tabName + '"]');
    if (tab) tab.classList.add('active');
    document.querySelectorAll('.result-tab-pane').forEach(p => p.classList.remove('active'));
    const pane = document.getElementById('tab-' + tabName);
    if (pane) {
        pane.classList.add('active');
        const tabs = document.querySelector('.result-tabs');
        if (tabs) tabs.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
}
window.switchTab = switchTab;

/**
 * 渲染关键差距 Top3
 */
function renderKeyGaps(data) {
    const body = document.getElementById('gapContent');
    if (!body) return;

    const allGaps = [];
    (data.analysis_basis || []).forEach(dim => {
        (dim.items || []).forEach(item => {
            if (item.type === 'gap') {
                allGaps.push({
                    content: item.content,
                    degree: item.match_degree || '低',
                    dimension: dim.dimension || ''
                });
            }
        });
    });

    const degreePriority = { '低': 0, '中': 1, '高': 2 };
    allGaps.sort((a, b) => (degreePriority[a.degree] || 0) - (degreePriority[b.degree] || 0));

    const topGaps = allGaps.slice(0, 3);

    if (topGaps.length === 0) {
        body.innerHTML = '<p class="placeholder-text">暂未发现关键差距 ✨</p>';
        return;
    }

    body.innerHTML = topGaps.map((gap, idx) => {
        const parsed = parseTypeTag(gap.content);
        const tag = typeTagStyle(parsed.type);
        return `
        <div class="gap-item">
            <span class="gap-num">${idx + 1}</span>
            <div class="gap-info">
                <div class="gap-content">${parsed.text || gap.content}</div>
                <div class="gap-meta">
                    ${parsed.type ? `<span class="gap-type ${tag.cls}">${tag.label}</span>` : ''}
                    <span class="gap-dim">${gap.dimension}</span>
                    <span class="gap-level">匹配度：${gap.degree}</span>
                </div>
            </div>
        </div>
    `;
    }).join('');
}

/**
 * 渲染AI判断依据（按维度分组，可折叠）
 */
function renderAnalysisBasis(analysisBasis) {
    const body = document.getElementById('analysisBasisContent');
    if (!body) return;

    if (!analysisBasis || analysisBasis.length === 0) {
        body.innerHTML = '<p class="placeholder-text">暂无判断依据</p>';
        return;
    }

    body.innerHTML = analysisBasis.map((dim, dimIdx) => {
        const matchItems = dim.items.filter(i => i.type === 'match');
        const gapItems = dim.items.filter(i => i.type === 'gap');
        const hasMatch = matchItems.length > 0;
        const hasGap = gapItems.length > 0;

        return `
        <div class="dimension-block ${dimIdx === 0 ? 'dim-open' : ''}">
            <div class="dimension-header ${dimIdx === 0 ? 'dim-open' : ''}" data-dim="${dimIdx}">
                <span class="dimension-arrow">▶</span>
                <h4 class="dimension-title">${dim.dimension}</h4>
                <div class="dimension-badges">
                    ${hasMatch ? `<span class="dim-count match">✓ ${matchItems.length}</span>` : ''}
                    ${hasGap ? `<span class="dim-count gap">⚠ ${gapItems.length}</span>` : ''}
                </div>
            </div>
            <div class="dimension-body">
                ${dim.items.map(item => {
                    const type = item.type === 'match' ? 'match' : 'gap';
                    const icon = type === 'match' ? '✓' : '⚠';
                    const label = type === 'match' ? '匹配' : '待补充';
                    return `
                    <div class="dimension-item ${type}">
                        <div class="dim-row">
                            <span class="dim-icon">${icon}</span>
                            <span class="dim-content">${item.content}</span>
                        </div>
                        ${item.quote ? `<span class="dim-quote">简历原文："${item.quote}"</span>` : ''}
                    </div>`;
                }).join('')}
            </div>
        </div>`;
    }).join('');

    // 绑定折叠点击事件
    body.querySelectorAll('.dimension-header').forEach(header => {
        header.addEventListener('click', () => {
            header.classList.toggle('dim-open');
            const block = header.parentElement;
            block.classList.toggle('dim-open');
        });
    });
}

/**
 * 渲染简历优势
 */
function renderStrengths(strengths) {
    const list = document.getElementById('strengthsList');
    if (!list) return;

    if (!strengths || strengths.length === 0) {
        list.innerHTML = '<li class="placeholder-text">暂无数据</li>';
        return;
    }

    list.innerHTML = strengths.map(item => `
        <li class="result-item advantage">
            <span class="item-marker">▸</span>
            <span>${item}</span>
        </li>
    `).join('');
}

/**
 * 渲染存在不足
 */
function renderWeaknesses(weaknesses) {
    const list = document.getElementById('weaknessesList');
    if (!list) return;

    if (!weaknesses || weaknesses.length === 0) {
        list.innerHTML = '<li class="placeholder-text">暂无数据</li>';
        return;
    }

    list.innerHTML = weaknesses.map(item => `
        <li class="result-item weakness">
            <span class="item-marker">▸</span>
            <span>${item}</span>
        </li>
    `).join('');
}

/**
 * 简易字符级 Diff：返回 {text, type: 'keep'|'del'|'add'} 数组
 * 基于 LCS（最长公共子序列）
 *
 * 长文本保护：original 或 revised 长度 > 300 字符时，退化为"整段标记"
 * （LCS 是 O(m×n)，长文本会卡死主线程）
 */
function diffChars(orig, rev) {
    if (!orig) return rev ? [{ text: rev, type: 'add' }] : [];
    if (!rev) return [{ text: orig, type: 'del' }];

    // 长文本保护：退化为简单的"整体对比"
    const MAX_CHAR_DIFF_LEN = 300;
    if (orig.length > MAX_CHAR_DIFF_LEN || rev.length > MAX_CHAR_DIFF_LEN) {
        if (orig === rev) return [{ text: orig, type: 'keep' }];
        // 粗略：前 80% 相同的部分算 keep，后面算 add
        const minLen = Math.min(orig.length, rev.length);
        let sameEnd = 0;
        for (let i = 0; i < minLen; i++) {
            if (orig[i] === rev[i]) sameEnd = i + 1;
            else break;
        }
        const result = [];
        if (sameEnd > 0) result.push({ text: orig.slice(0, sameEnd), type: 'keep' });
        if (orig.slice(sameEnd)) result.push({ text: orig.slice(sameEnd), type: 'del' });
        if (rev.slice(sameEnd)) result.push({ text: rev.slice(sameEnd), type: 'add' });
        return result;
    }

    const m = orig.length, n = rev.length;
    // 构建 LCS 矩阵
    const dp = Array.from({ length: m + 1 }, () => Array(n + 1).fill(0));
    for (let i = 1; i <= m; i++) {
        for (let j = 1; j <= n; j++) {
            if (orig[i - 1] === rev[j - 1]) dp[i][j] = dp[i - 1][j - 1] + 1;
            else dp[i][j] = Math.max(dp[i - 1][j], dp[i][j - 1]);
        }
    }
    // 回溯
    const result = [];
    let i = m, j = n;
    while (i > 0 || j > 0) {
        if (i > 0 && j > 0 && orig[i - 1] === rev[j - 1]) {
            result.unshift({ text: orig[i - 1], type: 'keep' });
            i--; j--;
        } else if (j > 0 && (i === 0 || dp[i][j - 1] >= dp[i - 1][j])) {
            result.unshift({ text: rev[j - 1], type: 'add' });
            j--;
        } else {
            result.unshift({ text: orig[i - 1], type: 'del' });
            i--;
        }
    }
    // 合并连续同类型
    const merged = [];
    for (const seg of result) {
        const last = merged[merged.length - 1];
        if (last && last.type === seg.type) last.text += seg.text;
        else merged.push({ ...seg });
    }
    return merged;
}

/**
 * 渲染修改前后对比（带 Diff + 操作按钮）
 */
function renderComparison(data) {
    const body = document.getElementById('comparisonContent');
    if (!body) return;

    const suggestions = data.rewrite_suggestions || [];

    if (suggestions.length === 0) {
        body.innerHTML = '<p class="placeholder-text">暂无改写建议</p>';
        return;
    }

    body.innerHTML = suggestions.map((item, idx) => {
        const diff = diffChars(item.original || '', item.revised || '');
        const gradeBadge = item.evidence_grade
            ? `<span class="evidence-grade grade-${item.evidence_grade}">证据等级 ${item.evidence_grade}</span>`
            : '';
        const basisId = 'basis-' + idx;

        return `
        <div class="compare-block" data-idx="${idx}">
            <div class="compare-block-header">
                <span class="compare-index">#${idx + 1}</span>
                ${gradeBadge}
            </div>
            <div class="compare-grid">
                <div class="compare-col before">
                    <div class="compare-label">原文</div>
                    <div class="compare-content diff-original">
                        ${diff.filter(s => s.type !== 'add').map(s =>
                            s.type === 'del'
                                ? `<span class="diff-del">${s.text}</span>`
                                : `<span class="diff-keep">${s.text}</span>`
                        ).join('') || '<em class="diff-empty">（空）</em>'}
                    </div>
                </div>
                <div class="compare-arrow">→</div>
                <div class="compare-col after">
                    <div class="compare-label">AI 改写</div>
                    <div class="compare-content diff-revised">
                        ${diff.filter(s => s.type !== 'del').map(s =>
                            s.type === 'add'
                                ? `<span class="diff-add">${s.text}</span>`
                                : `<span class="diff-keep">${s.text}</span>`
                        ).join('') || '<em class="diff-empty">（空）</em>'}
                    </div>
                </div>
            </div>
            ${item.basis ? `
                <button class="basis-toggle" onclick="toggleBasis('${basisId}', this)">
                    <span>▼</span> 修改依据
                </button>
                <div class="compare-reason" id="${basisId}" style="display:none">${item.basis}</div>
            ` : ''}
            <div class="compare-actions">
                <button class="action-btn copy" onclick="copyRewrite(this, ${idx})">📋 复制改写</button>
                <button class="action-btn accept" onclick="acceptRewrite(this, ${idx})">✅ 采纳</button>
                <button class="action-btn reject" onclick="rejectRewrite(this, ${idx})">❌ 不采纳</button>
            </div>
        </div>`;
    }).join('');

    // 保存 rewrite 数据供 copy 使用
    window._rewriteSuggestions = suggestions;
}

/** 折叠/展开修改依据 */
function toggleBasis(id, btn) {
    const el = document.getElementById(id);
    if (!el) return;
    const hidden = el.style.display === 'none';
    el.style.display = hidden ? 'block' : 'none';
    btn.querySelector('span').textContent = hidden ? '▲' : '▼';
}
window.toggleBasis = toggleBasis;

/** 复制改写文本 */
function copyRewrite(btn, idx) {
    const item = window._rewriteSuggestions && window._rewriteSuggestions[idx];
    if (!item) return;
    navigator.clipboard.writeText(item.revised || '').then(() => {
        const orig = btn.textContent;
        btn.textContent = '✓ 已复制';
        btn.classList.add('copied');
        setTimeout(() => { btn.textContent = orig; btn.classList.remove('copied'); }, 1500);
    });
}
window.copyRewrite = copyRewrite;

/** 本地持久化 key */
const _LS_REWRITE_STATE = 'ai_resume_rewrite_state';

function _loadRewriteState() {
    try { return JSON.parse(localStorage.getItem(_LS_REWRITE_STATE)) || {}; }
    catch { return {}; }
}
function _saveRewriteState(state) {
    try { localStorage.setItem(_LS_REWRITE_STATE, JSON.stringify(state)); } catch {}
}

/** 采纳改写（本地持久化） */
function acceptRewrite(btn, idx) {
    const block = btn.closest('.compare-block');
    if (!block) return;
    block.classList.toggle('accepted');
    block.classList.remove('rejected');
    btn.classList.toggle('active');
    const accepted = block.classList.contains('accepted');
    btn.textContent = accepted ? '✓ 已采纳' : '✅ 采纳';
    const rejectBtn = block.querySelector('.action-btn.reject');
    if (rejectBtn) rejectBtn.classList.remove('active');
    // 持久化
    const state = _loadRewriteState();
    state[idx] = accepted ? 'accepted' : null;
    _saveRewriteState(state);
}
window.acceptRewrite = acceptRewrite;

/** 不采纳（本地持久化） */
function rejectRewrite(btn, idx) {
    const block = btn.closest('.compare-block');
    if (!block) return;
    block.classList.toggle('rejected');
    block.classList.remove('accepted');
    btn.classList.toggle('active');
    const rejected = block.classList.contains('rejected');
    btn.textContent = rejected ? '✓ 已标记' : '❌ 不采纳';
    const acceptBtn = block.querySelector('.action-btn.accept');
    if (acceptBtn) acceptBtn.classList.remove('active');
    // 持久化
    const state = _loadRewriteState();
    state[idx] = rejected ? 'rejected' : null;
    _saveRewriteState(state);
}
window.rejectRewrite = rejectRewrite;

/**
 * 从优化建议文本中提取核心内容 + 判断优先级 + 是否需要补充真实信息
 */
function parseAdviceItem(text, source) {
    // 先用 parseTypeTag 提取 [类型标记]
    const parsed = parseTypeTag(text);
    let content = parsed.text || text;
    let explicitType = parsed.type; // 后端 Prompt 指定的类型

    // 去掉通用前缀（如果 parseTypeTag 没处理掉）
    content = content.replace(/^建议[突出补充优化表达]*[:：]\s*/, '');
    content = content.replace(/^建议优化表达[：:]\s*/, '');

    let priority = '中';
    let needRealInfo = false;
    let sourceLabel = '';

    // 如果后端给了明确类型标记，优先使用
    if (explicitType) {
        const tag = typeTagStyle(explicitType);
        if (tag.key === 'expr') {
            priority = '中';
            sourceLabel = '表达优化';
        } else if (tag.key === 'confirm') {
            priority = '高';
            sourceLabel = '事实待确认';
        } else if (tag.key === 'gap') {
            priority = '高';
            sourceLabel = '能力缺口';
        } else if (tag.key === 'info') {
            priority = '高';
            needRealInfo = true;
            sourceLabel = '需真实信息';
        }
    } else {
        // 没有显式标记 → 按 source 推断
        if (source === 'supplement') {
            priority = '高';
            sourceLabel = '需补充';
            const realInfoKeywords = ['学历', '毕业', '学位', '教育背景', '工作经历', '实习', '证书', '语言'];
            if (realInfoKeywords.some(k => content.includes(k))) {
                needRealInfo = true;
            }
            // 检查是否明确说"学习/实践" → 能力缺口
            if (/学习|实践|掌握/.test(content)) {
                sourceLabel = '能力缺口';
            }
        } else if (source === 'expression') {
            priority = '中';
            sourceLabel = '表达优化';
        } else {
            priority = '低';
            sourceLabel = '突出优势';
        }
    }

    return { content, priority, needRealInfo, sourceLabel, original: text, explicitType };
}

/**
 * 渲染AI优化建议 → 任务清单
 */
function renderSuggestions(data) {
    const body = document.getElementById('suggestionsContent');
    if (!body) return;

    const advice = data.optimization_advice || {};
    const all = [];

    (advice.supplement || []).forEach(t => all.push(parseAdviceItem(t, 'supplement')));
    (advice.expression || []).forEach(t => all.push(parseAdviceItem(t, 'expression')));
    (advice.highlight || []).forEach(t => all.push(parseAdviceItem(t, 'highlight')));

    if (all.length === 0) {
        body.innerHTML = '<p class="placeholder-text">暂无优化建议 ✨</p>';
        return;
    }

    // 按优先级排序（高→低）
    const priOrder = { '高': 0, '中': 1, '低': 2 };
    all.sort((a, b) => priOrder[a.priority] - priOrder[b.priority]);

    body.innerHTML = `
        <div class="task-list">
            ${all.map((item, idx) => `
                <div class="task-item" data-idx="${idx}">
                    <label class="task-check">
                        <input type="checkbox" onchange="toggleTask(this)">
                        <span class="check-box"></span>
                    </label>
                    <div class="task-body">
                        <div class="task-content">${item.content}</div>
                        <div class="task-tags">
                            <span class="pri-tag pri-${item.priority === '高' ? 'high' : item.priority === '中' ? 'mid' : 'low'}">
                                ${item.priority}优先级
                            </span>
                            <span class="src-tag src-${item.sourceLabel === '需补充' ? 'supplement' : item.sourceLabel === '表达优化' ? 'expr' : 'highlight'}">
                                ${item.sourceLabel}
                            </span>
                            ${item.needRealInfo ? '<span class="real-tag">需真实信息</span>' : ''}
                        </div>
                    </div>
                </div>
            `).join('')}
        </div>
    `;
}

/** 切换任务完成状态 */
function toggleTask(cb) {
    const item = cb.closest('.task-item');
    if (!item) return;
    if (cb.checked) item.classList.add('done');
    else item.classList.remove('done');
}
window.toggleTask = toggleTask;

// -------------------- 初始化 --------------------

document.addEventListener('DOMContentLoaded', () => {
    navigateTo('landing');

    // Tab 切换
    document.querySelectorAll('.result-tab').forEach(tab => {
        tab.addEventListener('click', () => {
            const tabName = tab.dataset.tab;
            // 切换按钮激活态
            document.querySelectorAll('.result-tab').forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            // 切换面板
            document.querySelectorAll('.result-tab-pane').forEach(p => p.classList.remove('active'));
            const pane = document.getElementById('tab-' + tabName);
            if (pane) pane.classList.add('active');
        });
    });
});

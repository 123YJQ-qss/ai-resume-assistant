/**
 * AI Resume Assistant - 后端服务
 * 功能：
 * 1. 提供静态文件服务（前端HTML/CSS/JS）
 * 2. 接收简历文件上传并解析PDF文本
 * 3. 调用 AI 服务层进行简历分析（DeepSeek LLM）
 * 4. 返回结构化分析结果
 */

const path = require('path');
require('dotenv').config({ path: path.resolve(__dirname, '.env') });

// 调试：检查环境变量是否加载成功
console.log('========================================');
console.log('环境变量加载状态：');
console.log('  PORT:', process.env.PORT || '(默认3000)');
console.log('  LLM_API_KEY:', process.env.LLM_API_KEY ? '✓ 已配置' : '✗ 未配置');
console.log('  LLM_MODEL:', process.env.LLM_MODEL || '(默认 deepseek-chat)');
console.log('  LLM_BASE_URL:', process.env.LLM_BASE_URL || '(默认 https://api.deepseek.com)');
console.log('  .env文件路径:', path.resolve(__dirname, '.env'));
console.log('========================================');

const express = require('express');
const cors = require('cors');
const multer = require('multer');
const pdfParse = require('pdf-parse');

const analyzeService = require('./services/analyzeService');

const app = express();
const PORT = process.env.PORT || 3000;

// 中间件
app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname)));

// 显式根路由：返回 index.html
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'index.html'));
});

// 文件上传配置（内存存储，用于PDF解析）
const upload = multer({ storage: multer.memoryStorage() });

// ============================================================
// API路由
// ============================================================

/**
 * POST /api/analyze
 * 简历分析接口
 * 
 * 支持两种输入方式：
 * 1. multipart/form-data: file (PDF) + job_description
 * 2. application/json: resume_text + job_description
 */
app.post('/api/analyze', (req, res) => {
    // 判断请求格式
    const contentType = req.headers['content-type'] || '';
    
    if (contentType.includes('application/json')) {
        // JSON 格式：直接使用 resume_text
        handleJsonRequest(req, res);
    } else {
        // multipart/form-data 格式：使用文件上传
        const uploadMiddleware = upload.single('file');
        uploadMiddleware(req, res, (err) => {
            if (err) {
                return res.status(400).json({ error: err.message });
            }
            handleMultipartRequest(req, res);
        });
    }
});

/**
 * 校验JD内容质量
 * 拒绝纯数字、纯符号、纯无意义内容，确保AI分析有实际意义
 * @returns {{valid: boolean, reason: string}}
 */
function validateJDQuality(jdText) {
    const text = jdText.trim();
    
    if (text.length < 10) {
        return { valid: false, reason: '岗位JD内容过短，请提供更详细的职位描述' };
    }
    
    // 统计字符类型占比
    const chineseChars = (text.match(/[\u4e00-\u9fa5]/g) || []).length;
    const totalChars = text.length;
    const chineseRatio = chineseChars / totalChars;
    
    // 数字占比
    const digitChars = (text.match(/[0-9]/g) || []).length;
    const digitRatio = digitChars / totalChars;
    
    // 检查：中文字符占比
    if (chineseRatio < 0.3) {
        return { valid: false, reason: '岗位JD中文字符过少（不足30%），请输入真实的中文岗位描述' };
    }
    
    // 检查：纯数字/符号
    if (digitRatio > 0.7) {
        return { valid: false, reason: '岗位JD数字过多（超过70%），请输入包含具体职责要求的文字描述' };
    }
    
    // 检查：至少包含一个岗位相关关键词
    const jobKeywords = ['岗位', '职责', '要求', '经验', '学历', '专业', '负责', '能力', '任职', '岗位描述', '技能', '技术', '产品', '开发', '设计', '运营', '市场', '管理', '分析', '研究', '客户', '用户', '团队', '项目', '规划', '组织', '沟通', '协调', '推动', '建立', '制定'];
    const hasKeyword = jobKeywords.some(kw => text.includes(kw));
    if (!hasKeyword) {
        return { valid: false, reason: '岗位JD缺少有效的岗位描述关键词（如"职责""要求""经验"等），请输入更完整的岗位信息' };
    }
    
    return { valid: true, reason: '' };
}

/**
 * 处理 JSON 格式请求
 */
async function handleJsonRequest(req, res) {
    try {
        const { job_description, resume_text } = req.body;

        // 参数校验
        if (!job_description || job_description.trim().length === 0) {
            return res.status(400).json({ error: '请提供岗位JD描述' });
        }

        // JD内容质量校验
        const jdValidation = validateJDQuality(job_description);
        if (!jdValidation.valid) {
            const result = getMockAnalysisResult();
            result.data_source = 'invalid_input';
            result.warning = jdValidation.reason;
            return res.json({
                success: true,
                data: result,
                data_source: 'invalid_input',
                warning: jdValidation.reason
            });
        }

        if (!resume_text || resume_text.trim().length === 0) {
            return res.status(400).json({ error: '请提供简历文本内容' });
        }

        console.log(`收到JSON分析请求：简历${resume_text.length}字，JD${job_description.length}字`);

        // 调用 AI 服务层
        const analysisResult = await analyzeService.analyzeResume(resume_text.trim(), job_description.trim());

        // 返回分析结果（含数据来源标识）
        res.json({
            success: true,
            data: analysisResult,
            data_source: 'llm',
            warning: null
        });

    } catch (error) {
        console.error('分析失败:', error.message);
        res.status(500).json({ 
            error: 'AI分析服务暂时不可用，请稍后重试',
            detail: error.message 
        });
    }
}

/**
 * 处理 multipart/form-data 格式请求
 */
async function handleMultipartRequest(req, res) {
    try {
        const { job_description, resume_text } = req.body;

        // 参数校验
        if (!job_description || job_description.trim().length === 0) {
            return res.status(400).json({ error: '请提供岗位JD描述' });
        }

        // JD内容质量校验
        const jdValidation = validateJDQuality(job_description);
        if (!jdValidation.valid) {
            const result = getMockAnalysisResult();
            result.data_source = 'invalid_input';
            result.warning = jdValidation.reason;
            return res.json({
                success: true,
                data: result,
                data_source: 'invalid_input',
                warning: jdValidation.reason
            });
        }

        // 获取简历文本：优先使用上传的PDF文件
        let resumeContent = '';
        
        if (req.file) {
            try {
                const data = await pdfParse(req.file.buffer);
                resumeContent = data.text;
            } catch (parseErr) {
                return res.status(400).json({ error: 'PDF文件解析失败，请确保上传的是有效的PDF文件' });
            }
        } else if (resume_text && resume_text.trim().length > 0) {
            resumeContent = resume_text;
        } else {
            return res.status(400).json({ error: '请上传简历文件或输入简历文本' });
        }

        if (resumeContent.trim().length === 0) {
            return res.status(400).json({ error: '简历内容为空，请检查文件或文本' });
        }

        console.log(`收到文件分析请求：简历${resumeContent.length}字，JD${job_description.length}字`);

        // 调用 AI 服务层
        const analysisResult = await analyzeService.analyzeResume(resumeContent.trim(), job_description.trim());

        // 返回分析结果（含数据来源标识）
        res.json({
            success: true,
            data: analysisResult,
            data_source: 'llm',
            warning: null
        });

    } catch (error) {
        console.error('分析失败:', error.message);
        res.status(500).json({ 
            error: 'AI分析服务暂时不可用，请稍后重试',
            detail: error.message 
        });
    }
}

/**
 * 模拟分析结果（仅用于输入无效时的占位，且会在前端显示"输入无效"标识）
 */
function getMockAnalysisResult() {
    return {
        match_level: {
            overall: "待评估",
            ability: "待评估",
            experience: "待评估",
            risk: "待评估"
        },
        analysis_basis: [],
        strengths: [],
        weaknesses: [],
        rewrite_suggestions: [],
        optimization_advice: {
            highlight: [],
            supplement: [],
            expression: []
        }
    };
}

/**
 * GET /api/health
 * 健康检查接口
 */
app.get('/api/health', (req, res) => {
    res.json({ 
        status: 'ok', 
        message: 'AI Resume Assistant API is running',
        llm_configured: !!process.env.LLM_API_KEY
    });
});

// 启动服务（自动处理端口占用）
const server = app.listen(PORT, () => {
    console.log(`
╔══════════════════════════════════════════╗
║     AI Resume Assistant 后端服务已启动     ║
╠══════════════════════════════════════════╣
║  本地访问:  http://localhost:${PORT}
║  API接口:  http://localhost:${PORT}/api/analyze
║  健康检查:  http://localhost:${PORT}/api/health
╚══════════════════════════════════════════╝
    `);
    
    if (!process.env.LLM_API_KEY) {
        console.log('⚠️  警告: 未配置LLM_API_KEY，将无法调用AI分析');
        console.log('   请在.env文件中添加 LLM_API_KEY 配置');
    }
});

// 处理端口占用错误：给出清晰提示而不是崩溃
server.on('error', (error) => {
    if (error.code === 'EADDRINUSE') {
        console.error(`
╔══════════════════════════════════════════════════════╗
║              ❌ 端口 ${PORT} 已被占用                  ║
╠══════════════════════════════════════════════════════╣
║  可能是之前的server.js进程没有正常关闭                  ║
║                                                        ║
║  解决方法（任选其一）：                                  ║
║                                                        ║
║  方法1：在当前终端按 Ctrl+C 停止旧进程                   ║
║                                                        ║
║  方法2：新开一个 PowerShell 终端，执行：                 ║
║    Stop-Process -Name node -Force                      ║
║  然后重新运行: node server.js                           ║
║                                                        ║
║  方法3：运行自动清理脚本:                                ║
║    npm run clean                                       ║
╚══════════════════════════════════════════════════════╝
        `);
    } else {
        console.error('服务器启动错误:', error.message);
    }
    process.exit(1);
});
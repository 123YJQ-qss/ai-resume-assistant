/**
 * AI Resume Assistant - 后端服务
 * 功能：
 * 1. 提供静态文件服务（前端HTML/CSS/JS）
 * 2. 接收简历文件上传并解析PDF文本
 * 3. 调用Coze Agent API (V3 流式响应) 进行简历分析
 * 4. 返回结构化分析结果
 */

const path = require('path');
require('dotenv').config({ path: path.resolve(__dirname, '.env') });

// 调试：检查环境变量是否加载成功
console.log('========================================');
console.log('环境变量加载状态：');
console.log('  PORT:', process.env.PORT || '(默认3000)');
console.log('  COZE_API_KEY:', process.env.COZE_API_KEY ? '✓ 已配置' : '✗ 未配置');
console.log('  COZE_BOT_ID:', process.env.COZE_BOT_ID ? '✓ 已配置' : '✗ 未配置');
console.log('  COZEZE_API_URL:', process.env.COZEZE_API_URL || '(使用默认)');
console.log('  .env文件路径:', path.resolve(__dirname, '.env'));
console.log('========================================');

const express = require('express');
const cors = require('cors');
const multer = require('multer');
const pdfParse = require('pdf-parse');
const axios = require('axios');

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

        // 调用Coze Agent API
        const analysisResult = await callCozeAgent(resume_text, job_description);

        // 返回分析结果（含数据来源标识）
        res.json({
            success: true,
            data: analysisResult,
            data_source: analysisResult.data_source || 'coze_api',
            warning: analysisResult.warning || null
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

        // 调用Coze Agent API
        const analysisResult = await callCozeAgent(resumeContent, job_description);

        // 返回分析结果（含数据来源标识）
        res.json({
            success: true,
            data: analysisResult,
            data_source: analysisResult.data_source || 'coze_api',
            warning: analysisResult.warning || null
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
 * 调用Coze Agent API (V3版本 - 流式响应)
 * 
 * 使用流式响应方式，直接获取AI回复，避免查询状态接口的权限问题
 */
async function callCozeAgent(resumeContent, jobDescription) {
    const baseUrl = process.env.COZEZE_API_URL || 'https://api.coze.cn';
    const apiKey = process.env.COZE_API_KEY;
    const botId = process.env.COZE_BOT_ID;

    if (!apiKey || !botId) {
        console.warn('Coze API配置缺失，返回模拟数据');
        return getMockAnalysisResult();
    }

    // 构建完整的分析提示词
    const analysisPrompt = `请分析以下简历与岗位的匹配度，并返回结构化分析结果。

【岗位JD】
${jobDescription}

【简历内容】
${resumeContent}

【输出要求】
1. 严格按照下面的JSON格式返回，不要添加任何解释文字
2. 所有字符串值中不要包含双引号、大括号等特殊字符，如需引用原文请用书名号《》或单引号
3. rewrite_suggestions 中的 original 字段必须是从上方【简历内容】中摘录的真实原文，不得编造
4. basis 字段必须说明改写依据：引用简历原文 + 对应JD要求 + 改写逻辑
5. 用 \`\`\`json 代码块包裹整个JSON返回

【返回格式示例】
\`\`\`json
{
  "match_level": {
    "overall": "较高/中等/较低",
    "ability": "较强/中等/较弱",
    "experience": "较强/中等/较弱",
    "risk": "需要优化/风险较低/风险较高"
  },
  "analysis_basis": [
    {
      "dimension": "维度名称（如：AI产品设计能力）",
      "items": [
        {
          "type": "match",
          "content": "匹配项内容描述",
          "quote": "简历原文引用",
          "match_degree": "高/中/低"
        },
        {
          "type": "gap",
          "content": "待补充项内容描述",
          "match_degree": "高/中/低"
        }
      ]
    }
  ],
  "strengths": ["优势1：具体描述", "优势2：具体描述"],
  "weaknesses": ["不足1：具体描述", "不足2：具体描述"],
  "rewrite_suggestions": [
    {
      "original": "必须摘录自简历原文",
      "revised": "优化后的表达",
      "basis": "依据说明：简历原文为《XXX》，JD要求XXX，因此改写为XXX"
    }
  ],
  "optimization_advice": {
    "highlight": ["建议突出经历1：具体说明", "建议突出经历2：具体说明"],
    "supplement": ["建议补充信息1：具体说明", "建议补充信息2：具体说明"],
    "expression": ["建议优化表达1：原表达→建议表达", "建议优化表达2：原表达→建议表达"]
  }
}
\`\`\`

请开始分析并返回结果：`;

    const headers = {
        'Authorization': `Bearer ${apiKey}`,
        'Content-Type': 'application/json',
        'Accept': 'text/event-stream'
    };

    try {
        console.log('Step 1: 发起Coze对话（流式响应）...');
        
        // 使用 axios 发送流式请求
        const response = await axios.post(`${baseUrl}/v3/chat`, {
            bot_id: botId,
            user_id: 'resume_analyzer_user',
            stream: true,
            auto_save_history: true,
            additional_messages: [
                {
                    role: 'user',
                    content: analysisPrompt,
                    content_type: 'text'
                }
            ]
        }, { 
            headers, 
            timeout: 60000,  // 60秒超时
            responseType: 'stream'
        });

        console.log('Step 2: 接收AI流式响应...');
        console.log('响应状态码:', response.status);

        // 处理流式响应
        return new Promise((resolve, reject) => {
            let fullContent = '';
            let streamEnded = false;
            let lastChunkTime = Date.now();
            let chunkCount = 0;

            // 流式接收处理
            response.data.on('data', (chunk) => {
                chunkCount++;
                lastChunkTime = Date.now();
                const chunkStr = chunk.toString();
                
                // 解析 SSE 数据
                const lines = chunkStr.split('\n');
                for (const line of lines) {
                    if (line.startsWith('data:')) {
                        const data = line.substring(5).trim();
                        
                        if (!data || data === '[DONE]') continue;
                        
                        try {
                            const parsed = JSON.parse(data);
                            
                            // 收集 answer 类型内容
                            if (parsed.type === 'answer' && parsed.content) {
                                fullContent += parsed.content;
                            }
                            
                            // 处理 completed 事件 - 用完整内容替换
                            if (parsed.event === 'conversation.message.completed') {
                                const msgData = parsed.data;
                                if (msgData?.type === 'answer' && msgData.content) {
                                    fullContent = msgData.content;
                                }
                            }
                        } catch (e) {
                            // 忽略非JSON行
                        }
                    }
                }
            });

            response.data.on('end', () => {
                streamEnded = true;
                console.log(`Step 4: 流式接收完成，共 ${chunkCount} 个数据块，${fullContent.length} 字符`);
                
                if (fullContent.length > 100) {
                    const result = parseAIResponse(fullContent);
                    result.data_source = 'coze_api';
                    resolve(result);
                } else {
                    console.warn('AI返回内容过少，可能API响应不完整');
                    const result = getMockAnalysisResult();
                    result.data_source = 'mock_fallback';
                    result.warning = 'AI分析响应不完整，当前显示示例数据，请稍后重试';
                    resolve(result);
                }
            });

            response.data.on('error', (err) => {
                console.error('流式响应错误:', err.message);
                if (!streamEnded) {
                    reject(err);
                }
            });

            // 超时保护：给足时间让AI完成回复
            setTimeout(() => {
                if (!streamEnded) {
                    console.warn(`流式响应超时(90秒)，已接收 ${fullContent.length} 字符`);
                    streamEnded = true;
                    
                    if (fullContent.length > 100) {
                        // 尝试解析已接收的内容
                        const result = parseAIResponse(fullContent);
                        result.data_source = 'coze_api_partial';
                        result.warning = 'AI响应尚未完成，当前显示部分分析结果';
                        resolve(result);
                    } else {
                        const result = getMockAnalysisResult();
                        result.data_source = 'mock_fallback';
                        result.warning = 'AI分析超时，当前显示示例数据，请稍后重试';
                        resolve(result);
                    }
                }
            }, 90000);

            // 空闲检测：如果15秒没有新数据，认为流已结束
            const idleCheck = setInterval(() => {
                if (streamEnded) {
                    clearInterval(idleCheck);
                    return;
                }
                if (Date.now() - lastChunkTime > 15000 && fullContent.length > 100) {
                    streamEnded = true;
                    clearInterval(idleCheck);
                    console.log(`流空闲15秒，判定接收完成，共 ${fullContent.length} 字符`);
                    
                    const result = parseAIResponse(fullContent);
                    result.data_source = 'coze_api_idle';
                    resolve(result);
                }
            }, 3000);
        });

    } catch (apiError) {
        console.error('Coze API调用失败:', apiError.message);
        
        if (apiError.response) {
            console.error('状态码:', apiError.response.status);
            console.error('错误详情:', JSON.stringify(apiError.response.data));
        }
        
        return getMockAnalysisResult();
    }
}

/**
 * 解析AI返回的响应内容
 * 解析策略（按优先级）：
 * 1. 提取 ```json ... ``` 代码块（最可靠）
 * 2. 直接 JSON.parse 完整内容
 * 3. 用 extractJSON 提取（fallback，可能截断）
 * 4. 返回默认结构
 */
function parseAIResponse(content) {
    if (!content) return getMockAnalysisResult();

    console.log('parseAIResponse 输入内容长度:', content.length);

    let parsed = null;

    // 策略1：提取 ```json 代码块（最可靠，避免特殊字符干扰）
    const codeBlockMatch = content.match(/```json\s*([\s\S]*?)```/);
    if (codeBlockMatch) {
        const jsonStr = codeBlockMatch[1].trim();
        console.log('策略1: 提取到json代码块, 长度:', jsonStr.length);
        try {
            parsed = JSON.parse(jsonStr);
            console.log('策略1: 代码块JSON解析成功');
        } catch (e) {
            console.log('策略1: 代码块JSON解析失败:', e.message);
        }
    }

    // 策略2：直接解析完整内容
    if (!parsed) {
        try {
            parsed = JSON.parse(content.trim());
            console.log('策略2: 直接JSON解析成功');
        } catch (e) {
            console.log('策略2: 直接JSON解析失败:', e.message);
        }
    }

    // 策略3：用 extractJSON 提取（可能截断，作为最后手段）
    if (!parsed) {
        const jsonContent = extractJSON(content);
        console.log('策略3: extractJSON提取长度:', jsonContent.length);
        try {
            parsed = JSON.parse(jsonContent);
            console.log('策略3: 提取后JSON解析成功（注意：数据可能不完整）');
        } catch (e) {
            console.log('策略3: 提取后JSON解析失败:', e.message);
        }
    }

    // 如果所有策略都失败，返回默认结构
    if (!parsed) {
        console.warn('所有JSON解析策略均失败，返回默认结构');
        return formatTextResult(content);
    }

    // 关键：补全缺失字段，确保前端不会因为字段缺失而显示空白
    const result = normalizeResult(parsed);
    console.log('解析完成，字段检查:', {
        has_match_level: !!result.match_level.overall && result.match_level.overall !== '待评估',
        analysis_basis_count: result.analysis_basis.length,
        strengths_count: result.strengths.length,
        weaknesses_count: result.weaknesses.length,
        rewrite_count: result.rewrite_suggestions.length,
        has_advice: result.optimization_advice.highlight.length + 
                     result.optimization_advice.supplement.length + 
                     result.optimization_advice.expression.length
    });
    return result;
}

/**
 * 规范化解析结果，补全缺失字段
 * 同时清洗脏数据：过滤掉原始JSON字符串等异常值
 */
function normalizeResult(data) {
    const result = {
        match_level: {
            overall: data.match_level?.overall || '待评估',
            ability: data.match_level?.ability || '待评估',
            experience: data.match_level?.experience || '待评估',
            risk: data.match_level?.risk || '待评估'
        },
        analysis_basis: cleanArrayField(data.analysis_basis),
        strengths: cleanArrayField(data.strengths),
        weaknesses: cleanArrayField(data.weaknesses),
        rewrite_suggestions: cleanArrayField(data.rewrite_suggestions),
        optimization_advice: {
            highlight: cleanArrayField(data.optimization_advice?.highlight),
            supplement: cleanArrayField(data.optimization_advice?.supplement),
            expression: cleanArrayField(data.optimization_advice?.expression)
        }
    };

    // 兼容旧格式
    if (data.suggestions && !data.optimization_advice) {
        result.optimization_advice = {
            highlight: cleanArrayField(data.suggestions.highlights),
            supplement: cleanArrayField(data.suggestions.additions),
            expression: cleanArrayField(data.suggestions.optimizations)
        };
    }

    return result;
}

/**
 * 清洗数组字段
 * 对字符串数组：过滤原始JSON字符串、空值等异常数据
 * 对对象数组：仅验证对象结构是否完整
 */
function cleanArrayField(field) {
    if (!Array.isArray(field)) return [];
    
    return field.filter(item => {
        // 字符串类型：过滤异常值
        if (typeof item === 'string') {
            if (item.trim().length < 3) return false;
            
            const trimmed = item.trim();
            if (trimmed.startsWith('{') || trimmed.startsWith('[')) return false;
            if (trimmed.startsWith('```')) return false;
            const jsonChars = (trimmed.match(/[{}[\]":]/g) || []).length;
            if (jsonChars > Math.max(3, trimmed.length * 0.3)) return false;
            
            return true;
        }
        
        // 对象类型：验证基本结构
        if (typeof item === 'object' && item !== null) {
            // analysis_basis 对象：清洗嵌套的 items 数组
            if ('dimension' in item) {
                if (!item.dimension) return false;
                if (item.items && Array.isArray(item.items)) {
                    item.items = cleanArrayField(item.items);
                }
                return true;
            }
            // rewrite_suggestions 对象
            if ('original' in item || 'revised' in item) {
                return item.original && item.revised;
            }
            return true;
        }
        
        return false;
    });
}

/**
 * 从文本中提取JSON
 * 使用更智能的方式找到第一个完整的 JSON 对象
 */
function extractJSON(text) {
    // 找到第一个 { 的位置
    const jsonStart = text.indexOf('{');
    
    if (jsonStart === -1) return text;
    
    // 从 { 开始，逐个字符匹配大括号
    let braceCount = 0;
    let inString = false;
    let escapeNext = false;
    
    for (let i = jsonStart; i < text.length; i++) {
        const char = text[i];
        
        // 处理字符串内的字符
        if (escapeNext) {
            escapeNext = false;
            continue;
        }
        
        if (char === '\\') {
            escapeNext = true;
            continue;
        }
        
        if (char === '"') {
            inString = !inString;
            continue;
        }
        
        // 跳过字符串内的字符
        if (inString) continue;
        
        // 处理大括号
        if (char === '{') {
            braceCount++;
        } else if (char === '}') {
            braceCount--;
            // 当 braceCount 回到 0，说明找到了完整的 JSON 对象
            if (braceCount === 0) {
                return text.substring(jsonStart, i + 1);
            }
        }
    }
    
    // 如果没有找到完整的 JSON，返回从 { 开始到结尾的内容
    return text.substring(jsonStart);
}

/**
 * 将非JSON文本包装成标准格式
 */
function formatTextResult(text) {
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
            expression: [text]
        }
    };
}

/**
 * 模拟分析结果（仅用于API不可用时的fallback，且会在前端显示"示例数据"标识）
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
        coze_configured: !!process.env.COZE_API_KEY && !!process.env.COZE_BOT_ID
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
    
    if (!process.env.COZE_API_KEY) {
        console.log('⚠️  警告: 未配置COZE_API_KEY，将使用模拟数据');
        console.log('   请在.env文件中添加Coze API配置');
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

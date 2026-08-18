/**
 * LLM 配置模块
 * 第一阶段：使用 DeepSeek（OpenAI 兼容接口）
 * API Key 通过环境变量注入，不写死在代码中
 */

const path = require('path');
// 自包含加载 .env：确保任何入口（server.js / evaluator.js）require 本模块时环境变量已就绪
require('dotenv').config({ path: path.resolve(__dirname, '..', '.env') });

module.exports = {
    // DeepSeek API 基础地址
    baseURL: process.env.LLM_BASE_URL || 'https://api.deepseek.com',
    
    // DeepSeek API Key（在 .env 中配置 LLM_API_KEY）
    apiKey: process.env.LLM_API_KEY,
    
    // 模型名称
    model: process.env.LLM_MODEL || 'deepseek-chat',
    
    // 低温度保证分析结果稳定一致
    temperature: 0.3,
    
    // 最大输出 token 数
    maxTokens: 4000,
    
    // 请求超时（毫秒）
    timeout: 60000
};
/**
 * LLM 调用服务层
 * 封装 DeepSeek（OpenAI 兼容接口）的 chat completions 调用
 * 职责：发送请求 → 处理响应 → 错误处理
 */

const axios = require('axios');
const llmConfig = require('../config/llm');

/**
 * 调用 LLM chat completions
 * @param {Object} options
 * @param {string} options.system - System Prompt
 * @param {string} options.user - User Message
 * @param {boolean} [options.jsonMode=false] - 是否启用 JSON 模式
 * @returns {Promise<string>} LLM 返回的文本内容
 */
async function chat(options) {
    const { system, user, jsonMode = false } = options;

    const messages = [];
    if (system) {
        messages.push({ role: 'system', content: system });
    }
    messages.push({ role: 'user', content: user });

    const requestBody = {
        model: llmConfig.model,
        messages,
        temperature: llmConfig.temperature,
        max_tokens: llmConfig.maxTokens,
        stream: false
    };

    // DeepSeek JSON 模式：在 system prompt 中开头加 "You must respond in valid JSON format."
    // 同时设置 response_format
    if (jsonMode) {
        requestBody.response_format = { type: 'json_object' };
    }

    const startTime = Date.now();

    const response = await axios.post(`${llmConfig.baseURL}/v1/chat/completions`, requestBody, {
        headers: {
            'Authorization': `Bearer ${llmConfig.apiKey}`,
            'Content-Type': 'application/json'
        },
        timeout: llmConfig.timeout
    });

    const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
    const content = response.data?.choices?.[0]?.message?.content;

    if (!content) {
        throw new Error('LLM 返回内容为空');
    }

    const usage = response.data?.usage;
    if (usage) {
        console.log(`[LLM] 耗时 ${elapsed}s | prompt ${usage.prompt_tokens} tokens | completion ${usage.completion_tokens} tokens`);
    }

    return content;
}

/**
 * 结构化调用：启用 JSON Mode + 自动解析
 * @param {Object} options
 * @param {string} options.system - System Prompt
 * @param {string} options.user - User Message
 * @returns {Promise<Object>} 解析后的 JSON 对象
 */
async function structuredChat(options) {
    let content = await chat({ ...options, jsonMode: true });

    // 尝试直接解析
    try {
        return JSON.parse(content);
    } catch (e) {
        // 如果直接解析失败，尝试提取代码块中的 JSON
        const codeBlockMatch = content.match(/```json\s*([\s\S]*?)```/);
        if (codeBlockMatch) {
            try {
                return JSON.parse(codeBlockMatch[1].trim());
            } catch (e2) {
                // 仍然失败
            }
        }
        // 最后尝试：从第一个 { 到最后一个 }
        const firstBrace = content.indexOf('{');
        const lastBrace = content.lastIndexOf('}');
        if (firstBrace !== -1 && lastBrace > firstBrace) {
            try {
                return JSON.parse(content.substring(firstBrace, lastBrace + 1));
            } catch (e3) {
                // 彻底失败
            }
        }
        console.error('[LLM] JSON 解析失败，原始内容:', content.substring(0, 200));
        throw new Error('LLM 返回内容无法解析为 JSON');
    }
}

module.exports = { chat, structuredChat };
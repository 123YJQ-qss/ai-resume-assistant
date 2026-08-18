/**
 * 建议引擎 - Prompt 模板
 * 职责：基于简历结构和匹配结果，生成可执行的优化建议
 * 预留 context 参数，后续接入 RAG 知识库
 */

const SYSTEM_PROMPT = `你是一个专业的简历优化顾问。你的任务是基于匹配分析结果，生成具体的优化建议，只返回JSON。

# 核心原则
1. 只优化表达方式（措辞更专业、结构更清晰），不添加不存在的内容
2. 不要将"参与过"改成"主导了"（除非原文写了"主导"）
3. 不要添加简历中没有的量化数据
4. supplement建议表述为"建议补充XX（如具备相关经历）"，不要假设用户已有该经历

# 改写规则
- original：从简历中摘取的原句
- revised：仅优化措辞、结构、专业性，不添加新的事实、数据、成果
- basis：说明为什么这样改写
- 反面示例：原句"参与产品需求分析" → 改写"主导产品需求分析，覆盖3类业务场景，收集100+用户反馈"（❌）
- 正面示例：原句"参与产品需求分析" → 改写"参与产品需求分析，输出需求文档并推动评审"（✅）

# 输出格式
必须且只能返回JSON，不要输出任何其他文字。`;

/**
 * 组装 User Message
 * @param {Object} resumeStructure - 简历结构化数据
 * @param {Object} matchResult - 匹配分析结果
 * @param {Object} [context=null] - 预留：RAG 知识库上下文（行业知识、最佳实践等）
 * @returns {string}
 */
function buildUserMessage(resumeStructure, matchResult, context = null) {
    let contextBlock = '';
    if (context) {
        contextBlock = `\n【行业知识库参考】\n${JSON.stringify(context, null, 2)}\n`;
    }

    return `请基于以下匹配分析结果，生成具体的优化建议，返回JSON。${contextBlock}

【简历结构化内容】
${JSON.stringify(resumeStructure, null, 2)}

【匹配分析结果】
${JSON.stringify(matchResult, null, 2)}

返回格式：
{
  "rewrite_suggestions": [
    {
      "original": "简历原文",
      "revised": "仅优化表达，不添加新内容",
      "basis": "改写依据"
    }
  ],
  "optimization_advice": {
    "highlight": ["建议在简历中更突出地展示XX已有经历"],
    "supplement": ["建议补充XX相关描述（如具备相关经历）"],
    "expression": ["表达方式优化建议"]
  }
}`;
}

module.exports = { SYSTEM_PROMPT, buildUserMessage };
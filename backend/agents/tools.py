"""
agents/tools.py — 三个 LangChain Tool 包装

复用现有能力模块（rag_knowledge / fact_check / jd_agent），
不引入新依赖。Tool schema 手动定义（OpenAI 兼容 JSON）。
"""
import json as _json


def _search_knowledge(query, top_k=3):
    """FAISS 岗位知识检索（内部实现）。"""
    try:
        from rag import rag_knowledge
        results = rag_knowledge.search(query, top_k=top_k)
        return results
    except Exception as e:
        return [{"error": f"知识库检索失败: {type(e).__name__}: {str(e)[:200]}"}]


def _check_facts(original_text, proposed_rewrite, jd_terms=None):
    """事实边界校验（内部实现）。"""
    try:
        from services import fact_check
        # fact_check 需要完整 opt_result dict（含 rewrite_suggestions 数组）
        opt_result = {
            "rewrite_suggestions": [
                {
                    "original": original_text,
                    "revised": proposed_rewrite,
                    "evidence_grade": "A",
                }
            ]
        }
        result = fact_check.check_rewrite_suggestions(
            opt_result, original_text,
            resume_tech=None, jd_terms=jd_terms or []
        )
        # 提取检查结果
        safe = all(not rw.get("fact_warning") for rw in result.get("rewrite_suggestions", []))
        warnings = [rw.get("fact_warning", "") for rw in result.get("rewrite_suggestions", [])
                    if rw.get("fact_warning")]
        return {"safe": safe, "violations": warnings}
    except Exception as e:
        return {"safe": False, "violations": [f"校验异常: {type(e).__name__}: {str(e)[:200]}"]}


def _parse_jd(jd_text):
    """JD 结构化解析（内部实现，调用 jd_agent）。"""
    try:
        from agents import jd_agent
        result = jd_agent.run(jd_text)
        # 只返回核心字段，去掉冗余
        return {
            "岗位职责": result.get("岗位职责", ""),
            "requirements": result.get("requirements", []),
            "核心技能": result.get("核心技能", []),
            "技术要求": result.get("技术要求", []),
            "岗位关键词": result.get("岗位关键词", []),
        }
    except Exception as e:
        return {"error": f"JD 解析失败: {type(e).__name__}: {str(e)[:200]}"}


# 三个 Tool 的 OpenAI 兼容 schema（传给 LLM 的描述）
TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "parse_jd",
            "description": "将岗位 JD 解析为结构化的三级分类要求（hard/core/preferred）。返回 requirements 数组，每条带 category 字段。这是分析的第一步。",
            "parameters": {
                "type": "object",
                "properties": {
                    "jd_text": {
                        "type": "string",
                        "description": "原始岗位 JD 完整文本"
                    }
                },
                "required": ["jd_text"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_knowledge",
            "description": "从岗位知识库检索相关技术栈、行业标准和常见模式。用于回答 'Agent 工作流通常怎么设计？' 或 'AI 应用开发需要哪些技术？'",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "检索关键词（如 'Agent 工作流设计模式'）"
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "返回结果数量，默认 3",
                        "default": 3
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_facts",
            "description": "对一段改写做事实边界校验，检查是否新增了原文不存在的技术词、数字、升级措辞。在输出改写建议前必须先调用此工具。",
            "parameters": {
                "type": "object",
                "properties": {
                    "original_text": {
                        "type": "string",
                        "description": "简历原文片段"
                    },
                    "proposed_rewrite": {
                        "type": "string",
                        "description": "AI 建议的改写版本"
                    },
                    "jd_terms": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "JD 中出现的技术词列表（用于判断新增词是否来自 JD 合理映射）"
                    }
                },
                "required": ["original_text", "proposed_rewrite", "jd_terms"]
            }
        }
    }
]


# Tool dispatch：根据 name 路由到内部实现
def execute_tool(name, arguments):
    """执行指定 tool，返回 string（喂回给 LLM 的 role=tool 消息）。

    最外层 try-except 兜底，任何异常都返回错误 JSON 字符串，
    保证 tool 调用不会 500，错误信息作为 tool_result 喂回 LLM 继续循环。
    """
    try:
        args = _json.loads(arguments) if isinstance(arguments, str) else arguments
    except Exception:
        args = {}

    try:
        if name == "parse_jd":
            result = _parse_jd(args.get("jd_text", ""))
        elif name == "search_knowledge":
            result = _search_knowledge(
                args.get("query", ""),
                args.get("top_k", 3),
            )
        elif name == "check_facts":
            result = _check_facts(
                args.get("original_text", ""),
                args.get("proposed_rewrite", ""),
                args.get("jd_terms", []),
            )
        else:
            result = {"error": f"未知工具: {name}"}
    except Exception as e:
        result = {"error": f"tool 执行异常[{name}]: {type(e).__name__}: {str(e)[:200]}"}

    # 返回 JSON 字符串（LLM 的 tool 消息 content 必须是 string）
    try:
        return _json.dumps(result, ensure_ascii=False, default=str)
    except Exception:
        return _json.dumps({"error": "tool 结果序列化失败"}, ensure_ascii=False)

"""
api/analyze.py - POST /api/analyze 接口 + Agent Workflow 编排
"""
import re

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from agents import jd_agent, resume_agent, match_agent, optimize_agent
from rag import rag_knowledge
from services import evidence, fact_check, llm_service, parser

router = APIRouter()

# 结构化 logger（request_id 由中间件写入 ContextVar，logger 自动携带）
from logging_config import get_logger
_logger = get_logger("analyze")

# 岗位相关关键词（用于 JD 质量校验）
_JOB_KEYWORDS = [
    "岗位", "职责", "要求", "经验", "学历", "专业", "负责", "能力", "任职",
    "岗位描述", "技能", "技术", "产品", "开发", "设计", "运营", "市场", "管理",
    "分析", "研究", "客户", "用户", "团队", "项目", "规划", "组织", "沟通",
    "协调", "推动", "建立", "制定",
]

# 单 Prompt 降级流程模板（Agent Workflow 失败时的兜底单次调用）
_SINGLE_PROMPT_TEMPLATE = """请分析以下简历与岗位的匹配度，并返回结构化分析结果。

【岗位JD】
__JD__

【岗位知识库参考】(用于提升匹配准确性与改写质量)
__KNOWLEDGE__

【简历内容】
__RESUME__

【最高原则】
在不改变、不新增、不虚构用户事实的前提下，最大化真实岗位匹配度。宁可匹配度显得低，也不允许虚构。

【证据等级与准入】
rewrite_suggestions 只允许基于简历原文事实的条目（A 已有事实 / B 基于事实的合理概括）。
能力推断（C）、当前缺口（D）、建议实践（E）禁止进入 rewrite_suggestions，只能写入 optimization_advice.supplement。

【禁止项】（相对简历原文而言）
1. 禁止新增简历中不存在的技术栈、职责、用户数量、项目级别
2. 禁止新增任何数字与指标（性能提升比例、效率倍数、毫秒级、准确率等），除非原文真实存在
3. 禁止把"参与"升级为"主导/独立负责"，禁止把"掌握/熟悉/了解"升级为"精通"（除非原文明确支持）
4. 禁止把个人项目包装成"生产级/工业级/高可用/大规模"
5. 禁止把"理论可迁移"写成"具备实践经验"
6. 禁止混淆技术概念（JSON Schema≠Tool Calling，RAG≠准确率提升）
7. JD 要求但简历未体现的技术：不得建议写进简历，写入 supplement 并注明"当前简历未体现该技术实践"

【输出要求】
1. 严格按照下面的JSON格式返回，不要添加任何解释文字
2. 所有字符串值中不要包含双引号、大括号等特殊字符，如需引用原文请用书名号《》或单引号
3. rewrite_suggestions 中的 original 字段必须是从上方【简历内容】中摘录的真实原文，不得编造
4. basis 字段必须说明改写依据：引用简历原文 + 对应JD要求 + 改写逻辑
5. revised 只能在 original 的事实范围内重写，只使用原文已出现的技术词
6. 用 ```json 代码块包裹整个JSON返回

【返回格式示例】
```json
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
      "revised": "仅在原文事实范围内的优化表达",
      "evidence_grade": "A或B",
      "basis": "依据说明：简历原文为《XXX》，JD要求XXX，因此改写为XXX"
    }
  ],
  "optimization_advice": {
    "highlight": ["建议突出经历1：具体说明", "建议突出经历2：具体说明"],
    "supplement": ["建议补充信息1：具体说明", "建议补充信息2：具体说明"],
    "expression": ["建议优化表达1：原表达→建议表达", "建议优化表达2：原表达→建议表达"]
  }
}
```

请开始分析并返回结果："""


def validate_jd_quality(jd_text):
    """校验 JD 内容质量，返回 (valid, reason)"""
    text = jd_text.strip()
    if len(text) < 10:
        return False, "岗位JD内容过短，请提供更详细的职位描述"

    total = len(text)
    chinese_ratio = len(re.findall(r"[\u4e00-\u9fa5]", text)) / total
    digit_ratio = len(re.findall(r"[0-9]", text)) / total

    if chinese_ratio < 0.3:
        return False, "岗位JD中文字符过少（不足30%），请输入真实的中文岗位描述"
    if digit_ratio > 0.7:
        return False, "岗位JD数字过多（超过70%），请输入包含具体职责要求的文字描述"

    if not any(kw in text for kw in _JOB_KEYWORDS):
        return False, "岗位JD缺少有效的岗位描述关键词（如\"职责\"\"要求\"\"经验\"等），请输入更完整的岗位信息"

    return True, ""


def clean_array_field(field):
    """清洗数组字段，过滤原始 JSON 字符串等异常值"""
    if not isinstance(field, list):
        return []
    result = []
    for item in field:
        if isinstance(item, str):
            if len(item.strip()) < 3:
                continue
            trimmed = item.strip()
            if trimmed.startswith("{") or trimmed.startswith("["):
                continue
            if trimmed.startswith("```"):
                continue
            json_chars = len(re.findall(r"[{}\[\]\":]", trimmed))
            if json_chars > max(3, len(trimmed) * 0.3):
                continue
            result.append(item)
        elif isinstance(item, dict):
            if "dimension" in item:
                if not item.get("dimension"):
                    continue
                if isinstance(item.get("items"), list):
                    item["items"] = clean_array_field(item["items"])
                result.append(item)
            elif "original" in item or "revised" in item:
                if item.get("original") and item.get("revised"):
                    result.append(item)
            else:
                result.append(item)
    return result


def normalize_result(data):
    """规范化结果，补全缺失字段"""
    data = data or {}
    ml = data.get("match_level") or {}
    advice = data.get("optimization_advice") or {}
    result = {
        "match_level": {
            "overall": ml.get("overall") or "待评估",
            "ability": ml.get("ability") or "待评估",
            "experience": ml.get("experience") or "待评估",
            "risk": ml.get("risk") or "待评估",
        },
        "analysis_basis": clean_array_field(data.get("analysis_basis")),
        "strengths": clean_array_field(data.get("strengths")),
        "weaknesses": clean_array_field(data.get("weaknesses")),
        "rewrite_suggestions": clean_array_field(data.get("rewrite_suggestions")),
        "optimization_advice": {
            "highlight": clean_array_field(advice.get("highlight")),
            "supplement": clean_array_field(advice.get("supplement")),
            "expression": clean_array_field(advice.get("expression")),
        },
    }
    # 兼容旧格式
    if data.get("suggestions") and not data.get("optimization_advice"):
        s = data["suggestions"]
        result["optimization_advice"] = {
            "highlight": clean_array_field(s.get("highlights")),
            "supplement": clean_array_field(s.get("additions")),
            "expression": clean_array_field(s.get("optimizations")),
        }
    return result


def get_mock_result():
    """模拟结果（API 不可用时的 fallback，前端会显示示例数据标识）"""
    return {
        "match_level": {"overall": "待评估", "ability": "待评估", "experience": "待评估", "risk": "待评估"},
        "analysis_basis": [],
        "strengths": [],
        "weaknesses": [],
        "rewrite_suggestions": [],
        "optimization_advice": {"highlight": [], "supplement": [], "expression": []},
    }


def _format_text_result(text):
    result = get_mock_result()
    result["optimization_advice"]["expression"] = [text]
    return result


def build_single_prompt(resume, jd, knowledge):
    return (_SINGLE_PROMPT_TEMPLATE
            .replace("__JD__", jd)
            .replace("__KNOWLEDGE__", knowledge or "（未匹配到相关岗位知识）")
            .replace("__RESUME__", resume))


def _parse_ai_response(content):
    if not content:
        return get_mock_result()
    parsed = llm_service.parse_json_from_text(content)
    if parsed is None:
        return _format_text_result(content)
    return normalize_result(parsed)


def _retrieve_knowledge(job_description):
    """RAG 检索岗位知识，返回人类可读的知识上下文"""
    hits = rag_knowledge.search_knowledge(job_description, top_k=3)
    if not hits:
        _logger.info("event=rag_retrieve  hits=0")
        return ""
    text = "\n".join(f"- 【{h['category']}】{h['content']}" for h in hits)
    _logger.info(f"event=rag_retrieve  hits={len(hits)}")
    return text


def build_data_source(kind):
    """动态生成 data_source 标识：{provider}_{kind}

    kind 取值：
    - "llm_api"        普通 LLM 调用
    - "agent_workflow" Agent Workflow 调用

    例如：deepseek_agent_workflow、openai_agent_workflow。
    """
    return f"{llm_service.get_provider()}_{kind}"


def _run_workflow(resume_content, job_description):
    """多 Agent Workflow 主流程 —— LangChain Runnable 编排

    LangChain 真实参与链路：
      ChatPromptTemplate → RunnableLambda(LLMService.chat) → RunnableLambda(JSON解析)
    四个 Agent 通过 RunnablePassthrough + assign 串联，fact_check 和 evidence 作为末端节点。
    Provider/LLMService 完全不动，仅通过 RunnableLambda 嵌入。
    """
    if not llm_service.is_configured():
        raise RuntimeError("LLM Provider 未配置")

    from langchain_core.runnables import RunnablePassthrough, RunnableLambda

    # 前置：RAG 检索岗位知识
    knowledge_context = ""
    try:
        knowledge_context = _retrieve_knowledge(job_description)
    except Exception as e:
        _logger.warning(f"event=rag_retrieve_failed  exc_type={type(e).__name__}")

    # ---- LangChain Runnable 工作流 ----
    # 输入 ctx = {"job_description", "resume_content", "knowledge_context"}
    # 输出 = 最终 merged dict
    def _step1_jd(ctx):
        _logger.info("event=workflow_step  step=1/4  agent=JD分析Agent")
        return jd_agent.run(ctx["job_description"])

    def _step2_resume(ctx):
        _logger.info("event=workflow_step  step=2/4  agent=简历分析Agent")
        return resume_agent.run(ctx["resume_content"])

    def _step3_match(ctx):
        _logger.info("event=workflow_step  step=3/4  agent=匹配评估Agent")
        return match_agent.run(
            ctx["jd_analysis"], ctx["resume_analysis"],
            ctx["resume_content"], ctx.get("knowledge_context", ""),
        )

    def _step4_optimize(ctx):
        _logger.info("event=workflow_step  step=4/4  agent=优化建议Agent")
        return optimize_agent.run(
            ctx["jd_analysis"], ctx["match_result"],
            ctx["resume_content"], ctx.get("knowledge_context", ""),
        )

    def _step5_merge(ctx):
        """fact_check → normalize → evidence → 返回"""
        opt_result = ctx["opt_result"]
        match_result = ctx["match_result"]
        jd_analysis = ctx["jd_analysis"]
        resume_analysis = ctx["resume_analysis"]
        resume_text = ctx["resume_content"]

        # fact_check：规则式越界检测
        opt_result, fact_summary = fact_check.check_rewrite_suggestions(
            opt_result, resume_text,
            resume_tech=resume_analysis.get("技术栈"),
            jd_terms=fact_check.extract_jd_terms(jd_analysis),
        )
        _logger.info(
            f"event=fact_check  checked={fact_summary['checked']}  "
            f"flagged={fact_summary['flagged']}  violations={fact_summary['violations']}"
        )

        merged = normalize_result({
            "match_level": match_result.get("match_level"),
            "analysis_basis": match_result.get("analysis_basis"),
            "strengths": match_result.get("strengths"),
            "weaknesses": match_result.get("weaknesses"),
            "rewrite_suggestions": opt_result.get("rewrite_suggestions"),
            "optimization_advice": opt_result.get("optimization_advice"),
        })
        merged["fact_check"] = fact_summary
        merged["data_source"] = build_data_source("agent_workflow")

        # evidence：挂简历原文证据（try/except 防阻断）
        try:
            merged = evidence.attach_evidence(merged, resume_text)
        except Exception as e:
            _logger.warning(f"event=evidence_failed  exc_type={type(e).__name__}")

        _logger.info(f"event=workflow_done  data_source={merged['data_source']}  "
                     f"rewrite_suggestions={len(merged.get('rewrite_suggestions') or [])}")
        return merged

    # LangChain Runnable 链：通过 RunnablePassthrough.assign 逐步注入字段
    workflow = (
        RunnablePassthrough.assign(
            jd_analysis=_step1_jd,
            resume_analysis=_step2_resume,
        )
        | RunnablePassthrough.assign(match_result=_step3_match)
        | RunnablePassthrough.assign(opt_result=_step4_optimize)
        | RunnableLambda(_step5_merge)
    )

    # 入口 ctx
    ctx = {
        "job_description": job_description,
        "resume_content": resume_content,
        "knowledge_context": knowledge_context,
    }
    return workflow.invoke(ctx)


def _run_single_prompt(resume_content, job_description):
    """单 Prompt 降级流程（Agent Workflow 失败时的兜底）"""
    if not llm_service.is_configured():
        _logger.warning("event=single_prompt_fallback  reason=LLM未配置")
        result = get_mock_result()
        result["data_source"] = "mock_fallback"
        result["warning"] = "LLM服务未配置，当前显示示例数据"
        return result

    knowledge_context = ""
    try:
        knowledge_context = _retrieve_knowledge(job_description)
    except Exception as e:
        _logger.warning(f"event=rag_retrieve_failed  exc_type={type(e).__name__}")

    prompt = build_single_prompt(resume_content, job_description, knowledge_context)
    try:
        content = llm_service.chat(prompt)
        if content and len(content) > 100:
            result = _parse_ai_response(content)
            result, fact_summary = fact_check.check_rewrite_suggestions(result, resume_content)
            result["fact_check"] = fact_summary
            result["data_source"] = build_data_source("llm_api")
            try:
                result = evidence.attach_evidence(result, resume_content)
            except Exception as e:
                _logger.warning(f"event=evidence_failed  exc_type={type(e).__name__}")
            _logger.info(f"event=single_prompt_done  data_source={result['data_source']}")
            return result
        _logger.warning("event=single_prompt_incomplete_response  reason=LLM响应过短")
        result = get_mock_result()
        result["data_source"] = "mock_fallback"
        result["warning"] = "AI分析响应不完整，当前显示示例数据，请稍后重试"
        return result
    except Exception as e:
        _logger.warning(f"event=single_prompt_failed  exc_type={type(e).__name__}")
        result = get_mock_result()
        result["data_source"] = "mock_fallback"
        result["warning"] = "AI分析服务暂时不可用，当前显示示例数据"
        return result


def analyze_resume(resume_content, job_description):
    """简历分析入口：优先走多 Agent Workflow，失败自动降级到单 Prompt 流程"""
    try:
        _logger.info("event=analyze_start  path=workflow")
        return _run_workflow(resume_content, job_description)
    except Exception as e:
        _logger.warning(f"event=workflow_failed  exc_type={type(e).__name__}  "
                        f"exc={str(e)[:200]}  path=fallback_to_single_prompt")
        return _run_single_prompt(resume_content, job_description)


@router.post("/api/analyze")
async def analyze(request: Request):
    """POST /api/analyze：支持 application/json 与 multipart/form-data 两种输入"""
    try:
        content_type = request.headers.get("content-type", "")
        if "application/json" in content_type:
            try:
                body = await request.json()
            except Exception as e:
                # 客户端传了非法 JSON → 明确返回 400
                _logger.warning(f"event=invalid_json  exc_type={type(e).__name__}")
                return JSONResponse(status_code=400, content={
                    "error": "请求体不是合法的 JSON 格式",
                })
            job_description = (body.get("job_description") or "").strip()
            resume_text = body.get("resume_text") or ""
        else:
            form = await request.form()
            job_description = (form.get("job_description") or "").strip()
            resume_text = form.get("resume_text") or ""
            file = form.get("file")
            if file is not None:
                filename = getattr(file, "filename", "") or ""
                content = await file.read()
                try:
                    resume_text = parser.parse_file(filename, content)
                except ValueError as e:
                    _logger.warning(f"event=parse_file_failed  filename={filename[:32]}")
                    return JSONResponse(status_code=400, content={"error": str(e)})
            resume_text = resume_text or ""

        # 参数校验
        if not job_description:
            return JSONResponse(status_code=400, content={"error": "请提供岗位JD描述"})

        valid, reason = validate_jd_quality(job_description)
        if not valid:
            result = get_mock_result()
            result["data_source"] = "invalid_input"
            result["warning"] = reason
            _logger.warning(f"event=jd_invalid  reason={reason[:60]}")
            return {"success": True, "data": result, "data_source": "invalid_input", "warning": reason}

        if not resume_text or not resume_text.strip():
            return JSONResponse(status_code=400, content={"error": "请上传简历文件或输入简历文本"})

        _logger.info(f"event=request_received  resume_chars={len(resume_text)}  "
                     f"jd_chars={len(job_description)}")

        result = await run_in_threadpool(analyze_resume, resume_text, job_description)

        _logger.info(f"event=request_success  data_source={result.get('data_source')}")
        return {
            "success": True,
            "data": result,
            "data_source": result.get("data_source") or "mock_fallback",
            "warning": result.get("warning"),
        }
    except Exception as e:
        _logger.error(
            f"event=request_failed  exc_type={type(e).__name__}  exc={str(e)[:200]}",
            exc_info=(type(e), e, e.__traceback__),
        )
        return JSONResponse(status_code=500, content={
            "error": "AI分析服务暂时不可用，请稍后重试",
        })

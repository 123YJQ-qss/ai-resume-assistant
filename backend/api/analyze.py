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

【JD 要求分类 —— 先分类，再匹配】
hard（硬性门槛）：只有 JD 明确写明、不可替代的准入条件（学历硬门槛、工作年限硬门槛、法律/资格证书、签证要求）。注意：Python/Java/Agent 等技术经验通常归入 core，不因岗位名是 Python 工程师就自动成 hard。
core（核心岗位能力）：岗位核心工作所需的技术和能力，决定适配度的主要依据。
preferred（加分）：JD 以"优先/加分"表述的条件。preferred 未满足不应拖累核心匹配度。

【每条要求的匹配状态】
direct_match：简历有直接证据。
partial_match：有相似技术/可迁移能力但不完整。技术迁移**只能支持 partial_match**，不能等同于 direct_match。必须保留能力边界。
unverified：简历没足够证据（没提到≠不具备）。
not_met：有反向证据明确不满足（如 JD 要求硕士，简历明确本科）。

【综合匹配等级（定性，不用数字阈值）】
先看 hard：如果有 hard 被判 not_met → 风险"风险较高"，overall 不高于"中等"。
再看 core：绝大多数 core 有 direct_match 或有可迁移 partial_match → 方向匹配。
preferred 全部 unverified 不应拖累到"较低"。
区分能力适配 vs 表达质量：能力基本满足但简历表达弱 → 不应给太低，而是指出表达问题。
- 较高：无 hard not_met，core 绝大多数有 direct_match 证据。即使表达弱也应较高（表达问题单独指出）。
- 中等：方向相关但有重要 core 处于 unverified，或有 hard not_met。
- 较低：有 hard not_met 且关键阻断，或 core 大量 unverified。

【禁止项】（相对简历原文而言）
1. 禁止新增简历中不存在的技术栈、职责、用户数量、项目级别
2. 禁止新增任何数字与指标（性能提升比例、效率倍数、毫秒级、准确率等），除非原文真实存在
3. 禁止把"参与"升级为"主导/独立负责"，禁止把"掌握/熟悉/了解"升级为"精通"（除非原文明确支持）
4. 禁止把个人项目包装成"生产级/工业级/高可用/大规模"
5. 禁止把"理论可迁移"写成"具备实践经验"
6. 禁止混淆技术概念（JSON Schema≠Tool Calling，RAG≠准确率提升）
7. JD 要求但简历未体现的技术：不得建议写进简历，写入 supplement 并注明"当前简历未体现该技术实践"

【weaknesses 分类标注】
- [表达优化]：可能具备但表述不清晰，可改写改善
- [事实待确认]：JD 要求但简历无足够证据，需候选人自己确认
- [能力缺口]：不能证明具备该技能，需学习/实践

【Top3 关键差距排序】：综合考虑 category（hard>core>preferred）、match_status、招聘影响。同组工具缺口归并（Coze/Dify 合并为"低代码 Agent 平台"）。

【rewrite_suggestions 准入】：只允许 evidence_grade A/B。C/D/E 进入 supplement。

【输出要求】
1. 严格按照下面的JSON格式返回，不要添加任何解释文字
2. 所有字符串值中不要包含双引号、大括号等特殊字符，如需引用原文请用书名号《》或单引号
3. 用 ```json 代码块包裹整个JSON返回

【返回格式示例】
```json
{
  "match_level": {
    "overall": "较高/中等/较低",
    "ability": "较强/中等/较弱",
    "experience": "较强/中等/较弱",
    "risk": "需要优化/风险较低/风险较高"
  },
  "requirement_matches": [
    {
      "requirement_id": "req-001",
      "requirement_text": "要求简述",
      "category": "hard/core/preferred",
      "match_status": "direct_match/partial_match/unverified/not_met",
      "evidence": "简历原文引用",
      "confidence": "high/medium/low",
      "transferable_from": null,
      "transferable_boundary": null,
      "match_reason": "判断理由"
    }
  ],
  "analysis_basis": [
    {
      "dimension": "能力维度名",
      "items": [
        {
          "type": "match",
          "content": "匹配描述",
          "quote": "简历原文引用",
          "match_degree": "高/中/低"
        },
        {
          "type": "gap",
          "content": "[类型标记]差距描述",
          "match_degree": "高/中/低"
        }
      ]
    }
  ],
  "strengths": ["优势1：具体描述"],
  "weaknesses": ["[类型标记]不足1：具体描述"],
  "rewrite_suggestions": [
    {
      "original": "必须摘录自简历原文",
      "revised": "仅在原文事实范围内的优化表达",
      "evidence_grade": "A或B",
      "basis": "依据说明"
    }
  ],
  "optimization_advice": {
    "highlight": ["建议突出：说明"],
    "supplement": ["[类型标记]建议内容"],
    "expression": ["原表达→建议表达"]
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


def _rewrite_has_substantive_change(original, revised):
    """判断改写是否有实质性变化（过滤微改动/空泛追加）。

    返回 False 表示应丢弃这条改写。

    检测规则（v2：放宽阈值，让更多实质性改写通过）：
    1. 完全相同 → 丢弃
    2. 只有标点/空格微调（差异率 < 5%） → 丢弃
    3. 尾部纯追加空泛评价短句（如"体现了优秀能力"） → 丢弃
    4. 措辞升级 + 有其他实质内容变化 → 保留（交给 evidence_grade 判断安全度）
    
    核心原则：evidence_grade 分级已在 prompt 层保证了事实安全，
    本函数只过滤无意义的改写（完全相同、纯标点、纯空泛追加）。
    """
    if not original or not revised:
        return False
    o = original.strip()
    r = revised.strip()
    if o == r:
        return False

    longer = max(len(o), len(r))
    shorter = min(len(o), len(r))
    if longer == 0:
        return False

    # 规则1：包含关系 + 差异极小（<12%）→ 纯标点/空格微调，丢弃
    # 1个字符变化在 8 字符里就是 12.5%，所以 0.12 刚好兜住大部分纯标点场景
    if (r in o or o in r) and (longer - shorter) / longer < 0.12:
        return False

    # 规则2：尾部纯追加空泛评价短句
    if len(r) > len(o) * 1.3:
        remaining = r.replace(o, "").strip()
        _EMPTY_PHRASES = [
            "体现了", "保障了", "有利于", "支持", "有助于",
            "具备较强", "具有较好", "展现了", "展示了",
            "提升了", "优化了", "完善了",
        ]
        if len(remaining) < 20 and any(p in remaining for p in _EMPTY_PHRASES):
            return False

    # 其余情况：保留（让 evidence_grade 来控制事实安全）
    return True


def normalize_result(data):
    """规范化结果，补全缺失字段 + 过滤低质量 rewrite"""
    data = data or {}
    ml = data.get("match_level") or {}
    advice = data.get("optimization_advice") or {}

    # 过滤低质量 rewrite_suggestions
    raw_rewrites = data.get("rewrite_suggestions")
    if isinstance(raw_rewrites, list):
        filtered = []
        for item in raw_rewrites:
            if not isinstance(item, dict):
                continue
            if _rewrite_has_substantive_change(
                item.get("original", ""), item.get("revised", "")
            ):
                filtered.append(item)
        rewrite_suggestions = filtered
        _rewrite_debug = {"raw": len(raw_rewrites), "kept": len(filtered), "dropped": len(raw_rewrites) - len(filtered)}
        _logger.info(f"rewrite_filter: raw={len(raw_rewrites)} kept={len(filtered)} dropped={len(raw_rewrites)-len(filtered)}")
    else:
        rewrite_suggestions = []
        _rewrite_debug = {"raw": 0, "kept": 0, "dropped": 0}

    # requirement_matches：来自 Match Agent 的逐条匹配结果（可选字段，向后兼容）
    requirement_matches = clean_array_field(data.get("requirement_matches"))

    result = {
        "match_level": {
            "overall": ml.get("overall") or "待评估",
            "ability": ml.get("ability") or "待评估",
            "experience": ml.get("experience") or "待评估",
            "risk": ml.get("risk") or "待评估",
        },
        "requirement_matches": requirement_matches,
        "analysis_basis": clean_array_field(data.get("analysis_basis")),
        "strengths": clean_array_field(data.get("strengths")),
        "weaknesses": clean_array_field(data.get("weaknesses")),
        "rewrite_suggestions": rewrite_suggestions,
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
    result["debug"] = {"rewrite_filter": _rewrite_debug}
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
            "requirement_matches": match_result.get("requirement_matches"),
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
        result = _run_single_prompt(resume_content, job_description)
        # 把原始异常挂上去，便于前端/调用方排查
        if result.get("data_source") == "mock_fallback":
            result.setdefault("debug", {})["workflow_error"] = f"{type(e).__name__}: {str(e)[:200]}"
        return result


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

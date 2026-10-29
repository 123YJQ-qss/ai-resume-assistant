"""
agents/tool_agent.py — Tool Calling Agent 主入口

LLM 自主决定 tool 调用顺序，最多 5 轮强制收敛。
输出 JSON schema 与 workflow 模式完全一致，前端无感知。

v2 修复（2026-10-29）：
- 强制收敛：max_rounds 后追加一次无 tools 重试（带"必须输出 JSON"指令）
- 返回附带 _jd_analysis，供后处理 fact_check 提取 jd_terms
- AGENT_META_LOG=1 时输出 [AGENT_META] 埋点日志
"""
import json as _json
import os
import time

from services import llm_service
from logging_config import get_logger
from .tools import TOOLS_SCHEMA, execute_tool

_logger = get_logger("tool_agent")

SYSTEM_PROMPT = """你是 AI 简历匹配分析专家。你可以使用以下三个工具：

1. parse_jd — 将岗位 JD 解析为三级分类要求（hard/core/preferred），返回 requirements[]
2. search_knowledge — 从岗位知识库检索技术栈、行业标准（可选使用）
3. check_facts — 对改写做事实边界校验（输出改写建议前必须先调用）

工作流程（自主决定调用顺序）：
1. 先调用 parse_jd 解析 JD 的三级分类要求
2. （可选）用 search_knowledge 查相关技术栈或行业模式
3. 基于 JD 解析结果 + 简历原文内容，做匹配评估，输出 requirement_matches[]（每条带 category 和 match_status）
4. 生成改写建议时，先用 check_facts 校验再输出
5. 最终必须输出一个完整的 JSON 对象，包含以下字段（字段名和结构不要改）：

{
  "match_level": {"overall": "较高/中等/较低", "ability": "较强/中等/较弱", 
                  "experience": "充足/中等/不足", "risk": "较低风险/需要优化/风险较高"},
  "requirement_matches": [{"requirement_id":"req-001","requirement_text":"...",
                           "category":"hard/core/preferred","match_status":"direct_match/partial_match/unverified/not_met",
                           "evidence":"...","match_reason":"...",
                           "transferable_from":"...（如有）","transferable_boundary":"...（如有）"}],
  "analysis_basis": [{"dimension":"...","items":[{"type":"match/gap","content":"...","match_degree":"高/中/低"}]}],
  "strengths": ["...","..."],
  "weaknesses": ["..."],
  "rewrite_suggestions": [{"original":"...","revised":"...","evidence_grade":"A/B"}],
  "optimization_advice": {
    "highlight": ["建议突出：具体说明（仅基于原文事实）"],
    "supplement": ["[类型标记]具体建议内容（类型标记：表达优化/事实待确认/能力缺口）"],
    "expression": ["建议优化表达：原表达→建议表达"]
  }
}

重要规则：
- 技术迁移只能产生 partial_match，不能等同于满足指定工具经验，必须保留能力边界
- 不要把"简历未提及"直接等同于"明确不具备"
- 硬性门槛（hard）用 JD 明确表述判断，不因岗位名称自动升级
- 加分项（preferred）不应拖累核心匹配度
- 改写完必须先 check_facts，发现违规就回退改写建议或降低 evidence_grade
"""

MAX_ROUNDS = 5
_FORCE_JSON_RETRY = True   # max_rounds 后强制收敛再请求一次


def _should_log_meta():
    return os.getenv("AGENT_META_LOG", "0").strip() in ("1", "true", "TRUE")


def run(job_description: str, resume_content: str) -> dict:
    """Tool Calling Agent 主循环。"""
    if not llm_service.is_configured():
        raise RuntimeError("LLM Provider 未配置")

    meta_enabled = _should_log_meta()
    meta = {
        "rounds": 0,
        "tool_calls": [],
        "prompt_tokens": 0,
        "completion_tokens": 0,
    }
    t_start = time.time()

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": (
            "请对以下简历与岗位 JD 进行完整分析，并按 JSON schema 输出。\n\n"
            f"【岗位 JD】\n{job_description}\n\n"
            f"【简历内容】\n{resume_content}"
        )},
    ]

    _logger.info(f"event=tool_agent_start  max_rounds={MAX_ROUNDS}")

    # 从 parse_jd tool 结果中提取（供后处理 fact_check 用）
    jd_analysis = None

    parsed_result = None

    for round_idx in range(1, MAX_ROUNDS + 1):
        meta["rounds"] = round_idx
        _logger.info(f"event=tool_agent_round  round={round_idx}/{MAX_ROUNDS}")

        # 最后一轮强制收敛：不给 tools，强制 JSON
        is_last_round = round_idx >= MAX_ROUNDS
        use_tools = None if is_last_round else TOOLS_SCHEMA

        response = llm_service.chat_with_tools(
            messages, tools=use_tools,
            tool_choice="auto" if use_tools else "none",
        )

        content = response.get("content") or ""
        tool_calls = response.get("tool_calls")

        # ---- 最后一轮但 LLM 还想调 tool → 丢掉 tool_calls，强制走 JSON 解析 ----
        if is_last_round and tool_calls:
            _logger.warning(f"event=tool_agent_forced_converge  round={round_idx}")
            tool_calls = None

        # ---- 分支 1：LLM 输出了 tool_calls，执行后继续 ----
        if tool_calls:
            messages.append({
                "role": "assistant",
                "content": content,
                "tool_calls": tool_calls,
            })

            for tc in tool_calls:
                tc_id = tc.get("id", "")
                tc_name = tc.get("function", {}).get("name", "")
                tc_args = tc.get("function", {}).get("arguments", "{}")

                _logger.info(f"event=tool_call  round={round_idx}  tool={tc_name}")
                tool_t0 = time.time()
                tool_result = execute_tool(tc_name, tc_args)
                tool_ok = "error" not in (tool_result or "").lower()[:50]
                tool_latency = int((time.time() - tool_t0) * 1000)

                if meta_enabled:
                    meta["tool_calls"].append({
                        "name": tc_name, "ok": tool_ok, "latency_ms": tool_latency,
                    })

                # parse_jd 结果 → 缓存 jd_analysis 供后处理用
                if tc_name == "parse_jd":
                    try:
                        parsed_jd = _json.loads(tool_result)
                        if "requirements" in parsed_jd or "核心技能" in parsed_jd:
                            jd_analysis = parsed_jd
                    except Exception:
                        pass

                messages.append({
                    "role": "tool",
                    "name": tc_name,
                    "tool_call_id": tc_id,
                    "content": tool_result,
                })

            continue

        # ---- 分支 2：LLM 输出了文本，尝试解析 JSON ----
        if content:
            parsed = llm_service.parse_json_from_text(content)
            if parsed:
                _logger.info(f"event=tool_agent_converge  round={round_idx}  ok")
                parsed_result = parsed
                break

            # 解析失败
            if is_last_round:
                # ---- 最后一轮还没解析成功 → 强制收敛重试 ----
                if _FORCE_JSON_RETRY:
                    _logger.warning("event=tool_agent_force_json_retry")
                    messages.append({"role": "assistant", "content": content})
                    messages.append({
                        "role": "user",
                        "content": (
                            "现在必须输出最终 JSON 对象。不要调用任何工具。"
                            "直接输出完整的 JSON（不要加 ```json 代码块标记），"
                            "字段必须包含 match_level、requirement_matches、"
                            "analysis_basis、strengths、rewrite_suggestions、"
                            "optimization_advice。"
                        ),
                    })
                    # 再请求一次（无 tools）
                    response2 = llm_service.chat_with_tools(messages, tools=None, tool_choice="none")
                    content2 = response2.get("content") or ""
                    parsed2 = llm_service.parse_json_from_text(content2)
                    if parsed2:
                        _logger.info("event=tool_agent_converge  force_json_retry  ok")
                        parsed_result = parsed2
                        break
                    raise RuntimeError(
                        f"Tool Agent {MAX_ROUNDS} 轮 + 强制收敛重试后仍无法解析 JSON。"
                        f"最后回复前 200 字符: {content2[:200]}"
                    )
                else:
                    raise RuntimeError(
                        f"Tool Agent {MAX_ROUNDS} 轮后无法解析 JSON。"
                        f"最后回复前 200 字符: {content[:200]}"
                    )

            # 非最后一轮解析失败 → 提示 LLM 修正
            _logger.warning(f"event=tool_agent_json_parse_fail  round={round_idx}")
            messages.append({"role": "assistant", "content": content})
            messages.append({
                "role": "user",
                "content": "上一个回复无法解析为 JSON，请重新输出完整的 JSON 对象（不要加 ```json 代码块标记）。",
            })
            continue

        # content 和 tool_calls 都没有 → 异常
        raise RuntimeError(f"Tool Agent round {round_idx}: LLM 未返回 content 也未返回 tool_calls")

    # ---- 收敛成功 ----
    if parsed_result is None:
        raise RuntimeError("Tool Agent 异常：循环内未收敛")

    # 附带 jd_analysis（供后处理 fact_check 提取 jd_terms）
    if jd_analysis:
        parsed_result["_jd_analysis"] = jd_analysis

    # 埋点日志
    total_ms = int((time.time() - t_start) * 1000)
    if meta_enabled:
        meta["latency_ms"] = total_ms
        _logger.info(f"[AGENT_META] {_json.dumps(meta, ensure_ascii=False)}")

    _logger.info(f"event=tool_agent_done  rounds={meta['rounds']}  latency_ms={total_ms}")
    return parsed_result

"""
evidence.py - 简历原文 source grounding（证据回查）

**真实性质（必须如实声明）**：
  本模块不是 RAG / FAISS 检索。项目中的 RAG/FAISS 服务于岗位知识库
  （knowledge_base.json），不服务于简历原文。
  本模块做的是：LLM 输出 rewrite_suggestions 之后，**用精确字符串匹配**
  从简历原文中回查支撑片段。这是 post-hoc source grounding，
  不是 retrieval evidence。

职责：
  1. 把简历原文切成若干证据片段（按段落/换行/句号切分）
  2. 为每个片段生成稳定 source_id（内容 SHA-1 + 位置 occurrence_index）
  3. 对 rewrite_suggestions 每条建议，从片段库中回查支撑原文
  4. 生成结构化 evidence 数组，挂到每条 suggestion 上

零第三方依赖，纯标准库。
"""
import re
import hashlib

# ---- 归一化：供字符串匹配使用 ----
def _norm(s):
    """去空白+小写，用于中文包含匹配。"""
    return re.sub(r"\s+", "", str(s or "")).lower()

# ---- 简历片段切分（稳定可复现）----
def _split_resume(resume_text):
    """把简历原文切成证据片段。

    切分规则（优先级从高到低）：
    1. 双换行段落 → 强边界
    2. 单换行 → 次边界
    3. 中文句号/分号/冒号 → 弱边界
    4. 英文句号 → 弱边界

    过短片段（< 6 字）会被合并到相邻片段。
    """
    if not resume_text or not resume_text.strip():
        return []

    # 第一步：按双换行切段落
    paragraphs = re.split(r"\n\s*\n", resume_text)
    # 第二步：段落内按单换行切行
    lines = []
    for p in paragraphs:
        for line in re.split(r"\n", p):
            line = line.strip()
            if line:
                lines.append(line)

    # 第三步：过长行按句号/分号切分（句子级片段）
    fragments = []
    for line in lines:
        if len(line) > 80:
            parts = re.split(r"(?<=[。；；：;])", line)
            for part in parts:
                part = part.strip()
                if part:
                    fragments.append(part)
        else:
            fragments.append(line)

    # 第四步：过短片段合并（< 6 字）
    merged = []
    for frag in fragments:
        if not merged:
            merged.append(frag)
            continue
        if len(frag) < 6:
            merged[-1] = merged[-1] + frag
        else:
            merged.append(frag)
    return merged

# ---- 稳定 source_id（含 occurrence_index 处理重复文本）----
def _make_source_id(text, occurrence_index):
    """基于内容+位置的稳定 source_id。

    同一份简历重复运行、相同文本出现在相同位置 → source_id 相同。
    相同文本出现在不同位置（不同 occurrence_index）→ source_id 不同。

    格式：resume_<SHA-1前12位>_<occurrence_index>
    """
    digest = hashlib.sha1(text.encode("utf-8")).hexdigest()
    return f"resume_{digest[:12]}_{occurrence_index}"

# ---- 片段库构建 ----
def build_resume_fragments(resume_text):
    """从简历原文构建片段库，返回 list[{source_id, original_text}]。

    顺序稳定：按原文出现顺序。
    相同文本出现在不同位置 → 不同 source_id（occurrence_index 递增）。
    """
    frags = _split_resume(resume_text)
    result = []
    # 追踪每种唯一文本的出现次数
    seen_counts = {}
    for f in frags:
        key = _norm(f)
        idx = seen_counts.get(key, 0)
        result.append({
            "source_id": _make_source_id(f, idx),
            "original_text": f,
        })
        seen_counts[key] = idx + 1
    return result

# ---- 查找支撑片段 ----
def _find_supporting_fragments(fragments, suggestion):
    """从片段库中回查支撑 suggestion 的原文片段（精确字符串匹配）。

    匹配优先级：
    1. suggestion["original"] → 精确包含（归一化后）
    2. original 找不到 → 用 suggestion["basis"] 里引号/书名号包裹的片段尝试
    3. 都找不到 → 用 suggestion["revised"] 里的拉丁关键词尝试

    返回 list[{source_id, original_text, evidence_index, match_score, source_type}]。
    match_score = 查找串归一化长度 / 命中片段归一化长度（0~1，不代表向量相似度）。
    evidence_index 从 1 开始，表示 evidence 数组中的序号（不是检索排名）。
    """
    if not fragments:
        return []

    norm_frags = [(f, _norm(f["original_text"])) for f in fragments]

    search_strings = []
    orig = suggestion.get("original") or ""
    basis = suggestion.get("basis") or ""
    revised = suggestion.get("revised") or ""
    if orig.strip():
        search_strings.append(orig)
    basis_quotes = re.findall(r"[《「]([^」》]{4,})[」》]", basis)
    for q in basis_quotes:
        if q.strip():
            search_strings.append(q)

    hits = []   # (frag_idx, match_score, frag_dict)
    seen = set()

    for s in search_strings:
        sn = _norm(s)
        if len(sn) < 4:
            continue
        for idx, (f, fn) in enumerate(norm_frags):
            if idx in seen:
                continue
            if sn in fn:
                match_score = round(len(sn) / max(len(fn), 1), 4)
                hits.append((idx, match_score, f))
                seen.add(idx)
                break  # 每个 suggestion 只取第一个命中的片段

    if not hits and revised.strip():
        rn = _norm(revised)
        kws = re.findall(r"[a-z]{3,}", rn)
        for kw in kws[:3]:
            for idx, (f, fn) in enumerate(norm_frags):
                if idx in seen:
                    continue
                if kw in fn:
                    match_score = round(len(kw) / max(len(fn), 1), 4)
                    hits.append((idx, match_score, f))
                    seen.add(idx)
                    break
            if hits:
                break

    evidence = []
    for evidence_index, (idx, match_score, f) in enumerate(hits, start=1):
        evidence.append({
            "source_id": f["source_id"],
            "original_text": f["original_text"],
            "evidence_index": evidence_index,
            "match_score": match_score,
            "source_type": "resume",
        })
    return evidence

# ---- 公共入口 ----
def attach_evidence(result, resume_text):
    """给 result 里每条 rewrite_suggestions 挂 evidence 字段。

    **真实性质**：post-hoc source grounding，不是 RAG/FAISS 检索。
    evidence_method 标记为 "exact_source_match"。

    修改是增量的：只新增 evidence 键，不动其他字段。
    向后兼容：没有 rewrite_suggestions 时返回原 result。
    JSON 可序列化：evidence 里全是 str / int / float，无复杂对象。
    不抛异常：调用方应 wrap in try/except，此处也做防御。

    返回 result（就地修改）。
    """
    suggestions = (result or {}).get("rewrite_suggestions")
    if not isinstance(suggestions, list) or not suggestions:
        return result

    fragments = build_resume_fragments(resume_text)
    if not fragments:
        for s in suggestions:
            if isinstance(s, dict):
                s["evidence"] = []
        return result

    for s in suggestions:
        if not isinstance(s, dict):
            continue
        evidence_list = _find_supporting_fragments(fragments, s)
        s["evidence"] = evidence_list

    if "resume_fragments" not in result:
        result["resume_fragments"] = {
            "count": len(fragments),
            "source_type": "resume",
            "evidence_method": "exact_source_match",
        }

    return result

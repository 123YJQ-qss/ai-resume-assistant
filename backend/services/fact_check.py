"""fact_check.py - 轻量事实校验（纯规则，无第三方依赖）

职责：对 rewrite_suggestions 做"相对简历原文"的事实越界检测，违规项打标记（不改写、不删除内容）。
检测范围（可模式化的部分）：
1. evidence_grade 越级：C/D/E 出现在 rewrite_suggestions（只允许 A/B）
2. original 可追溯性：original 是否能在简历原文中找到
3. 新增技术词：JD 技术词表中出现在 revised、但简历原文与技术栈都没有的词
4. 新增数字/指标：revised 中出现 original 里没有的数字、百分比、倍数量词
5. 措辞升级：精通/主导/独立负责 等（原文无则违规）
6. 项目级包装：生产级/工业级/高可用/毫秒级 等（原文无则违规）

语义级越界（如"理论迁移写成实践"的变体表述）无法用规则完全覆盖，主要依赖 Prompt 约束，
本模块只做确定性兜底。

v2 修改（2026-09-14）：extract_jd_terms 新增技术/业务分类器
------------------------------------------------------------
之前 extract_jd_terms 把 JD 分析里"核心技能/技术要求/岗位关键词"的所有字符串
都当作技术词。但 JD 分析 Agent 会混入业务词（降本提效、技术选型、项目闭环等），
这些词不该触发 fact_invention（它们不是"技术名词"）。

现在只将以下特征的 term 归入 technical：
  (a) 含 3+ 连续拉丁字符，且长度 ≤ 15（避免 LLM 幻觉长串）
      e.g. Python / Docker / FAISS / Kubernetes / openai / api
  (b) 含中文技术后缀：框架/数据库/中间件/引擎/协议/算法/模型/容器/部署/
      服务/接口/语言/系统/库/组件/工具/架构

业务词（降本提效、技术选型、项目闭环、稳定性保障、独立交付...）不满足 (a)(b)，
被排除在 technical 列表外，不再触发 fact_invention。

本修改只影响 extract_jd_terms 的输出集合大小，函数签名和
check_rewrite_suggestions 的返回格式完全不变。
"""
import re

# 升级类措辞（revised 出现且原文没有 → 违规）
UPGRADE_WORDS = [
    "精通", "主导", "独立负责", "独立完成", "独立设计", "独立开发",
    "资深", "专家级", "顶尖",
]

# 项目级/规模类包装词（revised 出现且原文没有 → 违规）
PROJECT_LEVEL_WORDS = [
    "生产级", "工业级", "商业级", "企业级", "生产环境",
    "高可用", "高并发", "毫秒级", "秒级响应",
    "千万级", "亿级", "海量用户", "大规模生产", "千万用户", "亿级用户",
]

# 定性量化表述（revised 出现且原文没有 → 违规）
QUALITATIVE_METRIC_WORDS = [
    "显著提升", "大幅提升", "明显提升", "成倍", "数倍", "数十倍",
    "效率倍增", "准确率大幅",
]

_NUM_RE = re.compile(r"\d+(?:\.\d+)?\s*(?:%|％|倍|万|亿|ms|毫秒|qps|ms秒)?", re.IGNORECASE)

# 版本号模式：版本 v1.0 / v1 / v1.0.3 / version 2
_VERSION_NUM_RE = re.compile(r"(?:版本|version|v)\s*\d+(?:\.\d+){0,3}", re.IGNORECASE)

# 章节/阶段模式：第 N 章/模块/阶段、Phase N、Stage N
_SECTION_NUM_RE = re.compile(r"(?:第\s*\d+[章节模块阶段步骤部分]|(?:phase|stage|step|chapter|part)\s*\d+)", re.IGNORECASE)

# 技术别名归一化：用于比较 JD 技术词与简历技术栈
# key = 规范化后目标, value = 匹配正则（在 _norm 后的小写文本上匹配）
_TECH_ALIAS_MAP = [
    (re.compile(r"ai[-_\s]*agent"), "agent"),        # AI Agent / AI-Agent / aiagent / ai agent → agent
    (re.compile(r"agent[-_\s]*workflow"), "agent"),   # Agent Workflow → agent（归一化后比较时等价）
]

# 架构相关技术词（命中此集合时，如果 original 含架构动作词，降级为 skill_upgrade）
_ARCHITECTURE_TERMS = {
    "系统架构设计", "架构设计", "总体架构设计", "技术架构设计",
    "系统架构", "技术架构", "总体架构", "完整架构",
}

# 架构动作词（出现在 original / 简历原文里时，表示已有架构设计能力）
_ARCHITECTURE_ACTION_WORDS = {
    "设计", "封装", "解耦", "抽象", "抽象层", "provider层",
    "统一封装", "统一接口", "请求调用",
}

# 中文技术后缀：term 含任意一个 → 视为技术词
_CHINESE_TECH_SUFFIXES = [
    "框架", "数据库", "中间件", "引擎", "协议", "算法", "模型",
    "容器", "部署", "服务", "接口", "语言", "系统", "库",
    "组件", "工具", "架构",
]

# 拉丁序列正则：匹配 3+ 连续拉丁字母/数字（含大小写混合）
_LATIN_RUN_RE = re.compile(r"[a-zA-Z][a-zA-Z0-9._\-]{2,}")


def _is_technical_term(term):
    """判断 JD 分析产出的一个 term 是否应该视为"技术名词"。

    分类规则（文档中的 (a)(b) 两条）：
      (a) 含 3+ 连续拉丁字符，串长度 ≤ 15（排除 LLM 幻觉长串）
      (b) 含中文技术后缀（_CHINESE_TECH_SUFFIXES 之一）

    两条都不满足 → 视为业务词，排除。
    """
    if not term or not isinstance(term, str):
        return False
    # (a) 拉丁序列
    for m in _LATIN_RUN_RE.finditer(term):
        run = m.group()
        if 3 <= len(run) <= 15:
            return True
    # (b) 中文技术后缀
    for suffix in _CHINESE_TECH_SUFFIXES:
        if suffix in term:
            return True
    return False


def _norm(s):
    """去空白 + 小写，用于中文包含匹配。"""
    return re.sub(r"\s+", "", str(s or "")).lower()


def _normalize_tech_term(term):
    """对技术名词做有限别名归一化（仅处理格式差异）。

    AI Agent / AI-Agent / aiagent → agent
    Agent Workflow → agent

    不做宽泛同义词映射（如"容器"→"Docker"）。
    """
    n = _norm(term)
    for pat, canon in _TECH_ALIAS_MAP:
        if pat.search(n):
            return canon
    return n


def _is_fake_metric_candidate(num_str, full_text):
    """判断 _NUM_RE 捕获到的数字串是否应触发 fake_metric。

    排除项：
      (a) 裸 0 或裸 1（不是指标，是项目阶段/计数）
          e.g. "从 0 到 1" 的 "0"、"1"
      (b) 版本号模式（v1、v2.0、version 1.0.3）
      (c) 章节/阶段模式（第 3 模块、Phase 2）

    保留项：
      - 带修饰符（%/倍/万/亿/ms/qps/毫秒）的任何数字
      - 裸数字 ≥ 10（如 "500+"、"2025" 不行但 "20ms" 带修饰符）
      - 裸数字 2-9 但紧邻业务动词（实际上这种场景极少）
    """
    s = num_str.strip()
    # (a) 排除纯 0 / 纯 1（不带修饰符的裸数字）
    if s in ("0", "1"):
        return False
    # (b) 版本号
    if _VERSION_NUM_RE.search(full_text):
        # 进一步确认：捕获的数字是否就是版本号的一部分
        if s.replace(".", "").isdigit() or s in ("v1", "v2", "v3"):
            return False
    # (c) 章节/阶段
    if _SECTION_NUM_RE.search(full_text):
        return False
    return True


def extract_jd_terms(jd_analysis):
    """从 JD 分析结果中提取"技术名词"候选。

    先收集核心技能/技术要求/岗位关键词下的所有字符串，
    再通过 _is_technical_term 过滤掉业务词。
    """
    terms = []
    if not isinstance(jd_analysis, dict):
        return terms
    for key in ("核心技能", "技术要求", "岗位关键词"):
        v = jd_analysis.get(key)
        if isinstance(v, list):
            for item in v:
                if isinstance(item, str) and item.strip() and _is_technical_term(item.strip()):
                    terms.append(item.strip())
    return terms


def _resume_tech_set(resume_tech):
    return {_norm(t) for t in (resume_tech or []) if _norm(t)}


def check_rewrite_suggestions(opt_result, resume_text, resume_tech=None, jd_terms=None):
    """校验 opt_result["rewrite_suggestions"]，违规项追加 fact_warning 字段。

    参数：
        opt_result: 含 rewrite_suggestions 的结果 dict（原地修改）
        resume_text: 简历原文
        resume_tech: 简历分析产出的技术栈列表（可空）
        jd_terms: JD 技术词候选列表（可空）

    返回：(opt_result, summary)；summary = {"checked": n, "flagged": n, "violations": n}

    v3 修改（2026-09-14）：
      - 新增技术词比较前做 _normalize_tech_term（AI Agent/aiagent → agent）
      - 架构词（系统架构设计等）如果 original/简历有架构动作词，降级为 skill_upgrade 而非 fact_invention
      - fake_metric 排除裸 0/1、版本号、章节号
    """
    items = opt_result.get("rewrite_suggestions") if isinstance(opt_result, dict) else None
    if not isinstance(items, list):
        return opt_result, {"checked": 0, "flagged": 0, "violations": 0}

    resume_norm = _norm(resume_text)
    tech_set = _resume_tech_set(resume_tech)
    # 简历技术栈也做别名归一化
    tech_set_norm = {_normalize_tech_term(t) for t in (resume_tech or [])}
    jd_norm_terms = [_norm(t) for t in (jd_terms or []) if _norm(t)]
    # JD 技术词也做别名归一化
    jd_norm_terms_aliased = [_normalize_tech_term(t) for t in (jd_terms or []) if _norm(t)]

    checked = 0
    flagged = 0
    violations_total = 0
    for it in items:
        if not isinstance(it, dict):
            continue
        checked += 1
        warnings = []
        original = it.get("original") or ""
        revised = it.get("revised") or ""
        o_norm = _norm(original)
        r_norm = _norm(revised)

        # 1. evidence_grade 准入：rewrite_suggestions 只允许 A/B
        grade = _norm(it.get("evidence_grade"))
        if grade in ("c", "d", "e"):
            warnings.append("evidence_grade为C/D/E（推断/缺口/建议实践），不得作为简历修改结果")

        # 2. original 可追溯性
        if o_norm and o_norm not in resume_norm:
            warnings.append("original未在简历原文中找到，无法追溯事实依据")

        # 3. 新增技术词（以 JD 词表为候选集，保守判定）
        fact_invention_triggered = False
        if r_norm:
            for t_raw, t_aliased in zip(jd_norm_terms, jd_norm_terms_aliased):
                # 用归一化前的词做包含判断（保留原始字符串），但用别名归一化后的值做集合比较
                t_in_revised = (t_raw in r_norm) or (t_aliased in r_norm and len(t_aliased) >= 3)
                if not t_in_revised:
                    continue
                # 别名归一化后检查是否在简历里已有
                in_resume_original = (t_raw in o_norm) or (t_raw in resume_norm)
                in_resume_aliased = t_aliased in tech_set_norm
                if in_resume_original or in_resume_aliased:
                    continue

                # 命中！但先检查是否是架构词 + original 有架构动作词 → 降级
                is_architecture_term = any(at in t_raw or at in t_aliased for at in _ARCHITECTURE_TERMS)
                if is_architecture_term:
                    # original 或简历原文里有没有架构动作词？
                    has_action = any(
                        aw in o_norm or aw in resume_norm
                        for aw in _ARCHITECTURE_ACTION_WORDS
                    )
                    if has_action:
                        # 降级为 skill_upgrade
                        warnings.append(f"疑似措辞升级: {t_raw}（架构能力表述升级，非技术虚构）")
                        fact_invention_triggered = "ARCH_DOWNGRADED"
                        continue

                warnings.append(f"疑似新增技术: {t_raw}")
                fact_invention_triggered = True
                break

        # 4. 新增数字/指标（排除裸 0/1、版本号、章节号）
        if r_norm:
            o_nums = {x.strip() for x in _NUM_RE.findall(o_norm)}
            for n in _NUM_RE.findall(r_norm):
                n_stripped = n.strip()
                if n_stripped not in o_nums and _is_fake_metric_candidate(n_stripped, r_norm):
                    warnings.append(f"疑似新增数字指标: {n_stripped}")
                    break
            else:
                for qw in QUALITATIVE_METRIC_WORDS:
                    if qw in r_norm and qw not in o_norm:
                        warnings.append(f"疑似新增量化表述: {qw}")
                        break

        # 5. 措辞升级
        for w in UPGRADE_WORDS:
            if w in r_norm and w not in o_norm and w not in resume_norm:
                warnings.append(f"疑似措辞升级: {w}")
                break

        # 6. 项目级包装
        for w in PROJECT_LEVEL_WORDS:
            if w in r_norm and w not in o_norm and w not in resume_norm:
                warnings.append(f"疑似未经证实的项目级描述: {w}")
                break

        if warnings:
            it["fact_warning"] = "；".join(warnings)
            flagged += 1
            violations_total += len(warnings)

    summary = {"checked": checked, "flagged": flagged, "violations": violations_total}
    return opt_result, summary

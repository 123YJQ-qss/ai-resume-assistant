"""验收标准定义

定义三类检查结果：
  PASS        — 自动化断言通过（格式/字段/可程序化判定）
  FAIL        — 自动化断言明确失败
  MANUAL_REVIEW — 自动化无法判定，标记为"待人工复核"

定义四类检查：
  HARD_ASSERT   — 硬断言（格式、字段、类型），失败=FAIL
  LOGIC_CHECK   — 逻辑检查（非空、有结构、fact_check 违规数=0）
  SEMANTIC      — 语义质量（自动化无法判断，一律 MANUAL_REVIEW）
  CROSS_TAB     — 跨 Tab 一致性（match_level.overall 和 analysis_basis 维度数是否矛盾）
"""

from dataclasses import dataclass, field
from typing import List, Callable, Dict, Any

RESULT_PASS = "PASS"
RESULT_FAIL = "FAIL"
RESULT_MANUAL = "待人工复核"
RESULT_SKIP = "SKIP"

# 检查类型分类常量（用于 CheckResult.category）
HARD_ASSERT = "HARD_ASSERT"   # 硬断言（格式、字段、类型），失败=FAIL
LOGIC_CHECK = "LOGIC_CHECK"   # 逻辑检查（非空、有结构、fact_check 违规数=0）
SEMANTIC = "SEMANTIC"         # 语义质量（自动化无法判断，一律 MANUAL_REVIEW）
CROSS_TAB = "CROSS_TAB"       # 跨 Tab 一致性


@dataclass
class CheckResult:
    name: str
    result: str  # PASS/FAIL/待人工复核
    category: str  # HARD_ASSERT / LOGIC_CHECK / SEMANTIC / CROSS_TAB
    details: str = ""
    evidence: str = ""  # 原始输出片段，便于人工复核

    def to_dict(self):
        return {
            "name": self.name,
            "result": self.result,
            "category": self.category,
            "details": self.details,
            "evidence": self.evidence[:500] if self.evidence else "",
        }


@dataclass
class TestCase:
    case_id: str
    description: str
    resume_text: str
    job_description: str
    # 人工期望（自动化参考，不直接 PASS/FAIL）
    human_expect: Dict[str, Any] = field(default_factory=dict)
    # 检查函数列表，每个函数签名 (data_dict, raw_response) -> CheckResult
    checks: List[Callable] = field(default_factory=list)

    def to_dict(self):
        return {
            "case_id": self.case_id,
            "description": self.description,
            "human_expect": self.human_expect,
            # resume_text / job_description 只在内部使用，报告里不回显完整文本（脱敏）
            "resume_text": "[REDACTED]",
            "job_description": "[REDACTED]",
        }


def is_pass(cr: CheckResult) -> bool:
    return cr.result == RESULT_PASS


def is_fail(cr: CheckResult) -> bool:
    return cr.result == RESULT_FAIL


def is_manual(cr: CheckResult) -> bool:
    return cr.result == RESULT_MANUAL

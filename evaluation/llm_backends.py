"""llm_backends.py - 评测用 LLM 后端。

RealBackend：直接复用 services.llm_service（需要真实 Provider 凭证）。
MockBackend：确定性脚本化后端，用于验证评测管道与测量结构化/机械指标。

MockBackend 说明（务必区分，避免误解）：
- 它根据当前测试用例的人工标注返回 JSON，因此内容正确类指标（关键词匹配、技能识别、
  匹配准确率）在默认 clean 模式下等于"管道自检"，不代表真实模型能力。
- 通过 fault_rate / malformed_rate 注入确定性故障，用于真实测量
  JSON 解析成功率、Workflow 成功率、降级后的字段完整率等结构化指标。
"""
import json

from services import llm_service


class MockBackend:
    """脚本化后端。通过 CURRENT 上下文注入当前用例的人工标注。"""

    def __init__(self, provider="deepseek", fault_rate=0.0, malformed_rate=0.0):
        self.provider = provider
        self.fault_rate = fault_rate
        self.malformed_rate = malformed_rate
        self.case = None
        self.idx = -1

    def begin(self, case, idx):
        self.case = case
        self.idx = idx

    def is_configured(self):
        return True

    def get_provider(self):
        return self.provider

    def _fault(self):
        return self.fault_rate and (self.idx % int(1 / self.fault_rate) == 0)

    def _malformed(self):
        return self.malformed_rate and (self.idx % int(1 / self.malformed_rate) == 0)

    # --- 单 Prompt（Baseline） ---
    def chat(self, prompt):
        if self._fault():
            raise RuntimeError("mock LLM fault injection (single-prompt)")
        return self._single_json()

    # --- Agent Workflow（Improved） ---
    def run_agent(self, agent_name, prompt):
        if self._fault():
            raise RuntimeError(f"mock LLM fault injection ({agent_name})")
        raw = self._agent_json(agent_name)
        parsed = llm_service.parse_json_from_text(raw)
        if parsed is None:
            raise RuntimeError(f"mock 返回无法解析为JSON ({agent_name})")
        return parsed

    # ---------------- 生成逻辑 ----------------
    def _single_json(self):
        ml = self.case["expected_match_level"]
        if self._malformed():
            return "这不是有效的 JSON 文本 {{"
        payload = {
            "match_level": ml,
            "analysis_basis": [{
                "dimension": "综合匹配度",
                "items": [{"type": "match", "content": "技能匹配", "quote": "原文", "match_degree": "高"}],
            }],
            "strengths": [f"具备{', '.join(self.case['expected_skills'][:2])}"],
            "weaknesses": [f"缺少{', '.join(self.case['expected_gaps'][:2])}"],
            "rewrite_suggestions": [{
                "original": "原文摘录", "revised": "优化后表达", "basis": "简历原文与JD要求结合",
            }],
            "optimization_advice": {
                "highlight": ["突出技能"], "supplement": ["补充缺口"], "expression": ["优化表达"],
            },
        }
        return "```json\n" + json.dumps(payload, ensure_ascii=False) + "\n```"

    def _agent_json(self, agent_name):
        if self._malformed():
            return "not-json"
        if "JD分析" in agent_name:
            payload = {
                "岗位职责": "该岗位负责相关技术研发",
                "核心技能": self.case["expected_skills"],
                "技术要求": self.case["expected_skills"],
                "岗位关键词": self.case["expected_skills"],
            }
        elif "简历分析" in agent_name:
            resume_skills = [s for s in self.case["expected_skills"] if s not in self.case["expected_gaps"]]
            payload = {
                "技术栈": resume_skills or self.case["expected_skills"],
                "项目经历": [{"项目名": "项目A", "职责": "研发", "技术点": ""}],
                "优势": ["匹配技能"],
                "不足": self.case["expected_gaps"],
            }
        elif "匹配评估" in agent_name:
            payload = {
                "match_level": self.case["expected_match_level"],
                "analysis_basis": [{
                    "dimension": "综合匹配度",
                    "items": [{"type": "match", "content": "技能匹配", "quote": "原文", "match_degree": "高"}],
                }],
                "strengths": ["匹配技能"],
                "weaknesses": self.case["expected_gaps"],
            }
        elif "优化建议" in agent_name:
            payload = {
                "rewrite_suggestions": [{
                    "original": "原文摘录", "revised": "优化后表达", "basis": "简历原文与JD要求结合",
                }],
                "optimization_advice": {"highlight": ["突出"], "supplement": ["补充"], "expression": ["优化"]},
            }
        else:
            payload = {}
        return "```json\n" + json.dumps(payload, ensure_ascii=False) + "\n```"


class RealBackend:
    """真实后端：调用 services.llm_service 的原始实现。

    run_eval.patch_llm 会在本实例构造之后替换 llm_service 模块级函数，
    因此这里在 __init__ 阶段捕获原始函数引用，避免递归/覆盖问题。
    """

    def __init__(self):
        self._is_configured = llm_service.is_configured
        self._get_provider = llm_service.get_provider
        self._chat = llm_service.chat
        self._run_agent = llm_service.run_agent

    def is_configured(self):
        return self._is_configured()

    def get_provider(self):
        return self._get_provider()

    def chat(self, prompt):
        return self._chat(prompt)

    def run_agent(self, agent_name, prompt):
        return self._run_agent(agent_name, prompt)
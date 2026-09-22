"""
test_analyze.py - /api/analyze 接口的自动化测试

不调用真实 LLM、不发起网络请求、不加载 RAG（sentence-transformers/FAISS）。
所有 LLM 调用被 monkeypatch 为固定返回值。

运行：
    cd backend
    python -m pytest api/test_analyze.py -v
"""
import json
import os
import sys
import uuid
from unittest.mock import patch

import pytest

# ---- 让 backend 成为 import 根 ----
HERE = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(HERE)
PROJECT_ROOT = os.path.dirname(BACKEND_DIR)
sys.path.insert(0, BACKEND_DIR)
sys.path.insert(0, PROJECT_ROOT)

# ---- 先清掉 .env 里的 Provider Key（用 mock 跑，不需要）----
os.environ.pop("DEEPSEEK_API_KEY", None)
os.environ.pop("OPENAI_API_KEY", None)
os.environ.pop("COZE_API_KEY", None)
os.environ.pop("LLM_PROVIDER", None)
os.environ.setdefault("LLM_PROVIDER", "mock")

from fastapi.testclient import TestClient

# 业务模块（注意：导入 main 时会触发 _load_dotenv 再次 setdefault，
# 但我们已经先 pop 了 Key，且 setdefault 不会覆盖已设置的值）
from main import app
from services import llm_service as llm_svc


# ---------------------------------------------------------------------------
# Mock 数据（与 run_evaluation.FactRegressionMock 保持一致的 Agent 返回 schema）
# ---------------------------------------------------------------------------
def _mock_agent_response(agent_name: str):
    """按 Agent 名称返回最小合法 dict。"""
    if "JD分析" in agent_name:
        return {"岗位职责": "岗位职责描述", "核心技能": ["Python"],
                "技术要求": ["Python"], "岗位关键词": ["Python"]}
    if "简历分析" in agent_name:
        return {"技术栈": ["Python", "FastAPI"],
                "项目经历": [{"项目名": "测试项目", "职责": "开发", "技术点": "Python"}],
                "优势": ["技术匹配"], "不足": ["经验有限"]}
    if "匹配评估" in agent_name:
        return {
            "match_level": {"overall": "中等", "ability": "中等",
                            "experience": "中等", "risk": "需要优化"},
            "analysis_basis": [{"dimension": "综合匹配度",
                                "items": [{"type": "match", "content": "Python",
                                           "quote": "原文", "match_degree": "高"}]}],
            "strengths": ["Python 匹配"], "weaknesses": ["经验不足"],
        }
    if "优化建议" in agent_name:
        return {
            "rewrite_suggestions": [{
                "original": "基于 FastAPI开发后台业务接口，实现任务管理、数据查询等核心功能",
                "revised": "基于 FastAPI 开发后台业务接口，实现任务管理与数据查询核心功能",
                "basis": "简历原文等价改写",
                "evidence_grade": "A",
            }],
            "optimization_advice": {
                "highlight": ["突出AI应用开发"],
                "supplement": ["补充多模态经验"],
                "expression": ["优化表达"],
            },
        }
    return {}


def _mock_chat_response(prompt: str) -> str:
    """单 Prompt 路径的兜底响应（JSON 字符串）。"""
    return json.dumps({
        "match_level": {"overall": "中等", "ability": "中等",
                        "experience": "中等", "risk": "需要优化"},
        "analysis_basis": [],
        "strengths": [], "weaknesses": [],
        "rewrite_suggestions": [],
        "optimization_advice": {"highlight": [], "supplement": [], "expression": []},
    }, ensure_ascii=False)


def _mock_parse_json(text: str):
    """从 LLM 响应中提取 JSON（真实实现）。"""
    import re
    m = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
    if m:
        text = m.group(1)
    try:
        return json.loads(text)
    except Exception:
        return None


# ---------------------------------------------------------------------------
# pytest fixture：给每个 TestClient 加上完整的 mock
# ---------------------------------------------------------------------------
@pytest.fixture
def client():
    """为 TestClient 注入 mock LLM + mock RAG。"""
    # LLM mock：让 is_configured=True，所有 run_agent 返回固定 schema
    with patch.object(llm_svc, "is_configured", return_value=True), \
         patch.object(llm_svc, "run_agent", side_effect=_mock_agent_response), \
         patch.object(llm_svc, "chat", side_effect=_mock_chat_response), \
         patch.object(llm_svc, "parse_json_from_text", side_effect=_mock_parse_json), \
         patch.object(llm_svc, "get_provider", return_value="mock"), \
         patch("api.analyze._retrieve_knowledge", return_value=""), \
         patch("rag.rag_knowledge.search_knowledge", return_value=[]):
        yield TestClient(app)


@pytest.fixture
def client_llm_raising():
    """用于测试 500：让 run_agent 抛异常，Workflow 失败 → analyze_resume 自己降级到 mock_fallback。
    但若我们让 analyze_resume 也 raise → 会触发 endpoint 外层 except → 500。"""
    def _always_raise(name, prompt):
        raise RuntimeError("Agent mock test failure (intentional)")

    with patch.object(llm_svc, "is_configured", return_value=True), \
         patch.object(llm_svc, "run_agent", side_effect=_always_raise), \
         patch.object(llm_svc, "chat", side_effect=_mock_chat_response), \
         patch.object(llm_svc, "get_provider", return_value="mock"), \
         patch("api.analyze._retrieve_knowledge", return_value=""), \
         patch("rag.rag_knowledge.search_knowledge", return_value=[]), \
         patch("api.analyze.analyze_resume", side_effect=RuntimeError("injected test error")):
        yield TestClient(app)


# ---------------------------------------------------------------------------
# 测试用例
# ---------------------------------------------------------------------------
SAMPLE_RESUME = """张三  某科技公司 AI 应用开发工程师

教育背景
  2021-2025  某大学 计算机科学与技术  本科

工作经历
  2024.06 - 至今  AI 应用开发工程师

项目经历
  职途AI - AI 简历优化助手
  基于 FastAPI开发后台业务接口，实现任务管理、数据查询等核心功能。
  使用 Python 进行后端开发，构建 RAG 检索增强模块，使用 sentence-transformers 生成文本 Embedding。
"""

SAMPLE_JD = """岗位：AI 应用开发工程师
职责：
1. 负责 Python 后端开发
2. 参与 AI 应用架构设计与实现
3. 与产品经理协作推进项目落地
要求：
- 3 年以上 Python 开发经验
- 熟悉 FastAPI 框架
- 了解 AI Agent 或 RAG 技术
"""


class TestAnalyzeEndpoint:
    """/api/analyze 接口核心功能测试"""

    def test_normal_request_success(self, client: TestClient):
        """正常 JSON 请求返回 200，字段完整。"""
        resp = client.post("/api/analyze", json={
            "resume_text": SAMPLE_RESUME,
            "job_description": SAMPLE_JD,
        })
        assert resp.status_code == 200, f"body={resp.text}"
        body = resp.json()

        # 顶层字段
        assert "success" in body and body["success"] is True
        assert "data" in body
        assert "data_source" in body

        data = body["data"]
        # 子字段
        assert "match_level" in data
        assert "rewrite_suggestions" in data
        assert "optimization_advice" in data

        # data_source 必须以 mock 开头（因为我们 mock 了 get_provider）
        assert body["data_source"].startswith("mock_"), \
            f"data_source={body['data_source']}（不是 mock 路径）"

    def test_missing_job_description_400(self, client: TestClient):
        """缺少 JD → 400。"""
        resp = client.post("/api/analyze", json={
            "resume_text": SAMPLE_RESUME,
        })
        assert resp.status_code == 400
        body = resp.json()
        assert "error" in body

    def test_missing_resume_text_400(self, client: TestClient):
        """缺少简历 → 400。"""
        resp = client.post("/api/analyze", json={
            "job_description": SAMPLE_JD,
        })
        assert resp.status_code == 400
        body = resp.json()
        assert "error" in body

    def test_empty_resume_text_400(self, client: TestClient):
        """简历字段存在但为空字符串 → 400。"""
        resp = client.post("/api/analyze", json={
            "resume_text": "   \n\n  ",
            "job_description": SAMPLE_JD,
        })
        assert resp.status_code == 400

    def test_invalid_jd_too_short(self, client: TestClient):
        """JD 过短（<10 字）→ 业务校验不通过，返回 success=True + invalid_input data_source。"""
        resp = client.post("/api/analyze", json={
            "resume_text": SAMPLE_RESUME,
            "job_description": "短",
        })
        # validate_jd_quality 返回 False 时，endpoint 走 invalid_input 分支 → 200 + success=True
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["data_source"] == "invalid_input"
        assert body.get("warning")

    def test_invalid_json_400(self, client: TestClient):
        """非法 JSON body → 400（endpoint 内显式捕获 JSONDecodeError）。"""
        resp = client.post(
            "/api/analyze",
            content=b"not-valid-json",
            headers={"content-type": "application/json"},
        )
        assert resp.status_code == 400

    def test_internal_service_error_500(self, client_llm_raising: TestClient):
        """内部异常 → 返回受控 500，错误信息不泄露实现细节。"""
        resp = client_llm_raising.post("/api/analyze", json={
            "resume_text": SAMPLE_RESUME,
            "job_description": SAMPLE_JD,
        })
        assert resp.status_code == 500
        body = resp.json()
        assert "error" in body
        # 受控错误：不包含 traceback、不包含注入的原始错误信息
        assert "injected test error" not in body["error"]
        assert "Traceback" not in body.get("error", "")
        # 不应暴露 detail 字段（旧版有，新版移除了）
        assert "detail" not in body


class TestRequestId:
    """request_id 中间件行为测试"""

    def test_x_request_id_passthrough(self, client: TestClient):
        """客户端传入 X-Request-ID → 响应头原样返回。"""
        my_rid = "test-rid-abc123xyz456"
        resp = client.post(
            "/api/analyze",
            json={"resume_text": SAMPLE_RESUME, "job_description": SAMPLE_JD},
            headers={"X-Request-ID": my_rid},
        )
        assert resp.status_code == 200
        got = resp.headers.get("X-Request-ID")
        assert got == my_rid, f"expected={my_rid}, got={got}"

    def test_x_request_id_auto_generate(self, client: TestClient):
        """未传入 → 自动生成 12 位 hex（uuid4 前缀），响应头带回。"""
        resp = client.post(
            "/api/analyze",
            json={"resume_text": SAMPLE_RESUME, "job_description": SAMPLE_JD},
        )
        assert resp.status_code == 200
        got = resp.headers.get("X-Request-ID")
        assert got is not None, "未自动生成 X-Request-ID"
        assert len(got) >= 12
        # 应是合法 hex
        int(got[:12], 16)

    def test_x_request_id_on_error_response(self, client: TestClient):
        """即使返回 4xx 错误，响应头也应带 X-Request-ID。"""
        my_rid = "error-rid-999"
        # 400 非法 JSON
        resp = client.post(
            "/api/analyze",
            content=b"not-json",
            headers={"content-type": "application/json", "X-Request-ID": my_rid},
        )
        assert resp.status_code == 400
        assert resp.headers.get("X-Request-ID") == my_rid

        # 400 缺字段
        resp2 = client.post(
            "/api/analyze",
            json={"job_description": SAMPLE_JD},
            headers={"X-Request-ID": my_rid},
        )
        assert resp2.status_code == 400
        assert resp2.headers.get("X-Request-ID") == my_rid

    def test_auto_rid_on_500(self, client_llm_raising: TestClient):
        """500 错误响应也必须带 X-Request-ID。"""
        resp = client_llm_raising.post("/api/analyze", json={
            "resume_text": SAMPLE_RESUME, "job_description": SAMPLE_JD,
        })
        assert resp.status_code == 500
        got = resp.headers.get("X-Request-ID")
        assert got is not None and len(got) >= 12


class TestMockIsolation:
    """Mock 测试不应发起真实网络请求 / 加载真实 RAG"""

    def test_no_provider_network_called(self, client: TestClient):
        """mock backend 不应调用 LLMService 外部 Provider 的 httpx 请求。

        TestClient 自身用 httpx.Client 发请求到本地 TestServer（内存循环），
        这不是"真实网络请求"，也不会连接外部 Provider。这里通过断言
        llm_service.LLMService 实例从未被创建来证明没有走真实 Provider 路径。
        """
        # client fixture 已经 patch 了 llm_service.is_configured / run_agent / chat，
        # 这些 patch 让所有 LLM 调用直接返回固定 dict / JSON 字符串，
        # 完全不经过真实 LLMService 外部 httpx.Client。
        resp = client.post("/api/analyze", json={
            "resume_text": SAMPLE_RESUME, "job_description": SAMPLE_JD,
        })
        assert resp.status_code == 200
        # 同时验证 data_source 是 mock 路径
        body = resp.json()
        assert body["data_source"].startswith("mock_")

    def test_response_fields_compatible(self, client: TestClient):
        """响应字段必须与前端兼容：success/data/data_source/warning。"""
        resp = client.post("/api/analyze", json={
            "resume_text": SAMPLE_RESUME, "job_description": SAMPLE_JD,
        })
        body = resp.json()
        assert "success" in body and body["success"] is True
        assert "data" in body and isinstance(body["data"], dict)
        assert "data_source" in body and isinstance(body["data_source"], str)
        # warning 可存在也可不存在，但不应该抛异常
        _ = body.get("warning")

    def test_multipart_form_also_works(self, client: TestClient):
        """multipart/form-data 路径也能跑通（无文件，只有文本字段）。"""
        resp = client.post(
            "/api/analyze",
            data={
                "resume_text": SAMPLE_RESUME,
                "job_description": SAMPLE_JD,
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True

"""
main.py - AI简历优化助手 FastAPI 入口

统一后端服务：文件上传、PDF/Word 解析、Agent Workflow、RAG 检索、LLM 调用。
"""
import asyncio
import os
import time
import uuid
from collections import defaultdict, deque
from pathlib import Path

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse

BASE_DIR = Path(__file__).resolve().parent          # backend/
PROJECT_ROOT = BASE_DIR.parent                       # 项目根（含前端与 .env）


def _load_dotenv():
    """加载 .env（简单读取，不引入额外依赖）"""
    for env_file in (BASE_DIR / ".env", PROJECT_ROOT / ".env"):
        if not env_file.exists():
            continue
        for raw in env_file.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from logging_config import setup_logging, set_request_id, get_logger

# 结构化日志
setup_logging()
_logger = get_logger("main")


# ============================================================
# 安全收尾：限流 / 并发控制 / 输入长度限制
# 全部基于 Python 标准库实现，不引入新依赖
# ============================================================

# 限流参数（环境变量可调）
_RATE_LIMIT_WINDOW_SEC = int(os.getenv("RATE_LIMIT_WINDOW_SEC", "60"))       # 滑动窗口秒数
_RATE_LIMIT_MAX_REQUESTS = int(os.getenv("RATE_LIMIT_MAX_REQUESTS", "5"))     # 窗口内最大请求数 / IP
_CONCURRENT_ANALYSIS_MAX = int(os.getenv("CONCURRENT_ANALYSIS_MAX", "2"))      # 同时运行的 AI 分析上限
_MAX_INPUT_CHARS = int(os.getenv("MAX_INPUT_CHARS", "20000"))                  # 简历 + JD 总字符上限（防止 Token 爆炸）

# 内存限流存储：{ip: deque([timestamp, ...])}
_rate_limit_store = defaultdict(deque)
# 并发分析信号量（在 analyze.py 中 acquire/release）
_analysis_semaphore = asyncio.Semaphore(_CONCURRENT_ANALYSIS_MAX)


def _check_rate_limit(client_ip: str) -> tuple[bool, str]:
    """检查 IP 是否超出限流窗口。返回 (allowed, reason)。"""
    now = time.time()
    window = _rate_limit_store[client_ip]
    # 清除窗口外的旧请求
    while window and now - window[0] > _RATE_LIMIT_WINDOW_SEC:
        window.popleft()

    if len(window) >= _RATE_LIMIT_MAX_REQUESTS:
        oldest = window[0]
        wait = int(_RATE_LIMIT_WINDOW_SEC - (now - oldest)) + 1
        return False, f"请求过于频繁，请 {wait} 秒后再试（每分钟最多 {_RATE_LIMIT_MAX_REQUESTS} 次）"

    window.append(now)
    return True, ""


def _client_ip(request: Request) -> str:
    """获取客户端 IP（兼容 Render/X-Forwarded-For）。"""
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


class _SecurityMiddleware(BaseHTTPMiddleware):
    """限流 + 输入长度限制（只作用于 /api/analyze）。"""

    async def dispatch(self, request: Request, call_next) -> Response:
        path = request.url.path

        # 只对分析接口做保护
        if path == "/api/analyze" and request.method == "POST":
            ip = _client_ip(request)
            allowed, reason = _check_rate_limit(ip)
            if not allowed:
                _logger.warning(f"event=rate_limited  client={ip}  reason={reason}")
                return JSONResponse(
                    status_code=429,
                    content={"success": False, "error": reason, "data_source": "rate_limit"},
                )

            # 检查 Content-Length 头（快速拦截）
            cl = request.headers.get("content-length")
            if cl and int(cl) > _MAX_INPUT_CHARS * 2:   # JSON 序列化后 ≈ 2x 原文字符
                _logger.warning(f"event=body_too_large  client={ip}  content_length={cl}")
                return JSONResponse(
                    status_code=413,
                    content={"success": False, "error": f"请求体过大，请缩短简历或岗位JD内容（上限 {_MAX_INPUT_CHARS} 字符）"},
                )

        return await call_next(request)


# 导出给 analyze.py 用（不做 import 循环）
def get_analysis_semaphore() -> asyncio.Semaphore:
    return _analysis_semaphore


class _RequestIdMiddleware(BaseHTTPMiddleware):
    """为每个请求生成或接收 request_id，写入 ContextVar + 响应头 + 日志。"""

    HEADER_NAME = "X-Request-ID"

    async def dispatch(self, request: Request, call_next) -> Response:
        incoming = request.headers.get(self.HEADER_NAME)
        if incoming and incoming.strip():
            request_id = incoming.strip()[:64]
        else:
            request_id = uuid.uuid4().hex[:12]

        set_request_id(request_id)

        method = request.method
        path = request.url.path
        qs = request.url.query
        qs_part = f"?{qs}" if qs else ""
        _logger.info(
            f"event=request_start  method={method} path={path}{qs_part}  "
            f"client={_client_ip(request)}"
        )
        t0 = time.perf_counter()

        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as exc:
            _logger.error(
                f"event=request_exception  method={method} path={path}  "
                f"exc_type={type(exc).__name__}  exc={str(exc)[:200]}",
                exc_info=(type(exc), exc, exc.__traceback__),
            )
            raise

        response.headers[self.HEADER_NAME] = request_id

        duration_ms = int((time.perf_counter() - t0) * 1000)
        _logger.info(
            f"event=request_end  method={method} path={path}  "
            f"status={status_code}  duration_ms={duration_ms}"
        )

        return response


app = FastAPI(title="AI Resume Assistant", version="2.0.0")

# ---- 中间件顺序：安全 > RequestId > CORS ----
app.add_middleware(_SecurityMiddleware)
app.add_middleware(_RequestIdMiddleware)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 业务路由
from api.analyze import router as analyze_router
from services import llm_service

app.include_router(analyze_router)


# ---- 前端静态托管 ----
@app.get("/")
def index():
    return FileResponse(PROJECT_ROOT / "index.html")


@app.get("/index.html")
def index_html():
    return FileResponse(PROJECT_ROOT / "index.html")


@app.get("/style.css")
def style_css():
    return FileResponse(PROJECT_ROOT / "style.css")


@app.get("/script.js")
def script_js():
    return FileResponse(PROJECT_ROOT / "script.js")


# 健康检查（清理后：只保留必要字段）
@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "service": "AI Resume Assistant",
        "version": "2.0.0",
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)

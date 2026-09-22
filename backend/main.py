"""
main.py - AI简历优化助手 FastAPI 入口

统一后端服务：文件上传、PDF/Word 解析、Agent Workflow、RAG 检索、LLM 调用。
"""
import os
import time
import uuid
from pathlib import Path

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

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


class _RequestIdMiddleware(BaseHTTPMiddleware):
    """为每个请求生成或接收 request_id，写入 ContextVar + 响应头 + 日志。"""

    HEADER_NAME = "X-Request-ID"

    async def dispatch(self, request: Request, call_next) -> Response:
        # 1) 优先接受客户端传入的 X-Request-ID
        incoming = request.headers.get(self.HEADER_NAME)
        if incoming and incoming.strip():
            request_id = incoming.strip()[:64]   # 防止过长
        else:
            # 2) 未提供 → 自动生成（uuid4 hex 前 12 位，去分隔符）
            request_id = uuid.uuid4().hex[:12]

        # 3) 写入 ContextVar（业务代码通过 get_request_id() 可读取）
        set_request_id(request_id)

        # 4) 记录请求开始（不记录 body 内容，脱敏）
        method = request.method
        path = request.url.path
        qs = request.url.query
        qs_part = f"?{qs}" if qs else ""
        _logger.info(
            f"event=request_start  method={method} path={path}{qs_part}  "
            f"client={request.client.host if request.client else '-'}"
        )
        t0 = time.perf_counter()

        # 5) 执行业务
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as exc:
            # 异常路径：记录但必须 re-raise，让 FastAPI 的异常处理器接管
            _logger.error(
                f"event=request_exception  method={method} path={path}  "
                f"exc_type={type(exc).__name__}  exc={str(exc)[:200]}",
                exc_info=(type(exc), exc, exc.__traceback__),
            )
            raise

        # 6) 无论成功/失败都在响应头带回 request_id
        response.headers[self.HEADER_NAME] = request_id

        # 7) 记录请求结束
        duration_ms = int((time.perf_counter() - t0) * 1000)
        _logger.info(
            f"event=request_end  method={method} path={path}  "
            f"status={status_code}  duration_ms={duration_ms}"
        )

        return response


app = FastAPI(title="AI Resume Assistant", version="2.0.0")

# ---- 中间件顺序：RequestId 在前（确保 preflight 和异常也能拿到 request_id）----
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


# 健康检查
@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "message": "AI Resume Assistant API is running",
        "provider": llm_service.get_provider(),
        "llm_configured": llm_service.is_configured(),
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)

"""
logging_config.py - 结构化日志 + request_id 上下文

使用 stdlib logging（无第三方依赖），通过 ContextVar 传递 request_id，
输出格式为 key=value（单行，便于 grep 与 ELK/Loki 解析）。

不记录：API Key、完整简历、完整 JD、模型原始响应。
"""
import json
import logging
import sys
from contextvars import ContextVar

# 请求级上下文变量（每个请求独立，线程/协程安全）
request_id_var: ContextVar[str] = ContextVar("request_id", default="-")

_LOGGER_INITIALIZED = False


class _KeyValueFormatter(logging.Formatter):
    """key=value 格式，每条日志一行，携带 level 和 request_id。

    输出示例：
      2025-01-15 10:30:00 INFO  request_id=abc123  event=request_start  method=POST path=/api/analyze
    """

    def format(self, record: logging.LogRecord) -> str:
        parts = [self.formatTime(record, "%Y-%m-%d %H:%M:%S")]
        parts.append(f"{record.levelname:5s}")

        # request_id 来自 ContextVar
        rid = request_id_var.get()
        parts.append(f"request_id={rid}")

        # 消息体：期望是 "event=xxx key=val key=val" 或纯文本
        msg = record.getMessage()
        parts.append(msg)

        # 异常堆栈（只在 error 级别带）
        if record.exc_info and record.exc_info[0] is not None:
            parts.append(f"exc_info={record.exc_info[0].__name__}")

        return "  ".join(parts)


def setup_logging(level: int = logging.INFO) -> None:
    """配置根 logger：key=value 格式、stdout、一次性。"""
    global _LOGGER_INITIALIZED
    if _LOGGER_INITIALIZED:
        return

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(_KeyValueFormatter())

    root = logging.getLogger()
    root.addHandler(handler)
    root.setLevel(level)

    # 第三方库降级（httpx/uvicorn/transformers 等）
    for name in ("httpx", "uvicorn", "transformers", "sentence_transformers", "faiss"):
        logging.getLogger(name).setLevel(logging.WARNING)

    _LOGGER_INITIALIZED = True


def get_logger(name: str) -> logging.Logger:
    """获取命名 logger（调用 setup_logging 保证配置生效）。"""
    if not _LOGGER_INITIALIZED:
        setup_logging()
    return logging.getLogger(name)


def set_request_id(rid: str) -> None:
    """中间件调用：将 request_id 写入 ContextVar。"""
    request_id_var.set(rid)


def get_request_id() -> str:
    """业务代码调用：获取当前请求的 request_id（没有则返回 '-'）。"""
    return request_id_var.get()

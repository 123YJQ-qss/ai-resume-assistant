"""
llm_service.py - 统一 LLM 调用层

支持通用 OpenAI 兼容接口，并保留 Coze 作为备用 Provider。

Provider 路由（由环境变量 LLM_PROVIDER 决定）：
- deepseek  -> OpenAI 兼容 /v1/chat/completions（默认）
- openai    -> OpenAI 兼容 /v1/chat/completions
- coze      -> Coze v3 chat 流式接口（保留）

本层职责：请求发送、timeout、retry、JSON 解析、token 统计。
Agent 层只需调用 chat(prompt)，不关心具体模型与供应商。
"""
import os
import re
import json
import time

import httpx

DEFAULT_MODEL = "deepseek-chat"

# OpenAI 兼容接口的默认地址
_DEFAULT_BASE_URL = {
    "deepseek": "https://api.deepseek.com",
    "openai": "https://api.openai.com/v1",
}


def get_provider():
    """读取当前 Provider（默认 deepseek）。"""
    return (os.getenv("LLM_PROVIDER") or "deepseek").strip().lower()


class LLMService:
    """LLM Provider 抽象：统一 chat() 入口，内部按 provider 路由。"""

    TIMEOUT = 120.0
    MAX_RETRIES = 3

    def __init__(self):
        self.timeout = self.TIMEOUT
        self.max_retries = self.MAX_RETRIES

    # ---------------- 配置 ----------------

    @property
    def provider(self):
        return get_provider()

    def _api_key(self):
        if self.provider == "coze":
            return os.getenv("COZE_API_KEY", "")
        if self.provider == "openai":
            return os.getenv("OPENAI_API_KEY", "")
        return os.getenv("DEEPSEEK_API_KEY", "")

    def _model(self):
        if self.provider == "openai":
            return os.getenv("MODEL_NAME") or "gpt-4o-mini"
        return os.getenv("MODEL_NAME") or DEFAULT_MODEL

    def is_configured(self):
        if self.provider == "coze":
            return bool(os.getenv("COZE_API_KEY") and os.getenv("COZE_BOT_ID"))
        return bool(self._api_key())

    # ---------------- 统一入口 ----------------

    def chat(self, prompt):
        """统一 LLM 调用入口，返回完整回复文本。失败向上抛出异常。"""
        if self.provider == "coze":
            return self._chat_coze(prompt)
        return self._chat_openai_compatible(prompt)

    # ---------------- OpenAI 兼容实现 ----------------

    def _openai_url(self):
        base = os.getenv(
            "OPENAI_BASE_URL" if self.provider == "openai" else "DEEPSEEK_BASE_URL",
            _DEFAULT_BASE_URL.get(self.provider, "https://api.deepseek.com"),
        ).rstrip("/")
        if base.endswith("/chat/completions"):
            return base
        if base.endswith("/v1"):
            return base + "/chat/completions"
        return base + "/v1/chat/completions"

    def _chat_openai_compatible(self, prompt):
        url = self._openai_url()
        headers = {
            "Authorization": "Bearer " + self._api_key(),
            "Content-Type": "application/json",
        }
        body = {
            "model": self._model(),
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
        }
        last_err = None
        for attempt in range(self.max_retries + 1):
            try:
                with httpx.Client(timeout=self.timeout) as client:
                    resp = client.post(url, headers=headers, json=body)
                    resp.raise_for_status()
                    data = resp.json()
                content = ((data.get("choices") or [{}])[0]
                           .get("message", {}).get("content", ""))
                self._log_tokens(data.get("usage"))
                return content or ""
            except Exception as e:  # 网络 / 超时 / HTTP 错误等
                last_err = e
                if attempt < self.max_retries:
                    wait = min(2 ** attempt, 8)
                    print(f"[LLM] {self.provider} 调用失败（第{attempt + 1}次），{wait}s后重试：{e}")
                    time.sleep(wait)
        raise RuntimeError(f"{self.provider} 调用失败（已重试{self.max_retries}次）：{last_err}")

    # ---------------- Coze 实现（保留作为备用 Provider） ----------------

    def _coze_base_url(self):
        return os.getenv("COZEZE_API_URL", "https://api.coze.cn")

    def _chat_coze(self, prompt):
        url = self._coze_base_url() + "/v3/chat"
        headers = {
            "Authorization": "Bearer " + os.getenv("COZE_API_KEY", ""),
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
        }
        body = {
            "bot_id": os.getenv("COZE_BOT_ID", ""),
            "user_id": "resume_analyzer_user",
            "stream": True,
            "auto_save_history": True,
            "additional_messages": [
                {"role": "user", "content": prompt, "content_type": "text"}
            ],
        }

        full_content = ""
        usage = None
        with httpx.Client(timeout=self.timeout) as client:
            with client.stream("POST", url, headers=headers, json=body) as resp:
                resp.raise_for_status()
                for line in resp.iter_lines():
                    if not line.startswith("data:"):
                        continue
                    data = line[5:].strip()
                    if not data or data == "[DONE]":
                        continue
                    try:
                        parsed = json.loads(data)
                    except (json.JSONDecodeError, ValueError):
                        continue
                    if parsed.get("type") == "answer" and parsed.get("content"):
                        full_content += parsed["content"]
                    if parsed.get("event") == "conversation.message.completed":
                        msg = parsed.get("data") or {}
                        if msg.get("type") == "answer" and msg.get("content"):
                            full_content = msg["content"]
                    if parsed.get("event") == "conversation.chat.completed":
                        usage = (parsed.get("data") or {}).get("usage")
        self._log_tokens(usage)
        return full_content

    # ---------------- JSON 解析 ----------------

    def parse_json_from_text(self, content):
        """从 LLM 返回文本中提取并解析 JSON（代码块 / 直接解析 / 首个大括号提取）。"""
        if not content:
            return None
        m = re.search(r"```json\s*([\s\S]*?)```", content)
        s = m.group(1).strip() if m else content.strip()
        try:
            return json.loads(s)
        except (json.JSONDecodeError, ValueError):
            pass
        try:
            return json.loads(self._extract_json(s))
        except (json.JSONDecodeError, ValueError):
            pass
        return None

    @staticmethod
    def _extract_json(text):
        """提取第一个完整 JSON 对象。"""
        start = text.find("{")
        if start == -1:
            return text
        brace_count = 0
        in_string = False
        escape_next = False
        for i in range(start, len(text)):
            ch = text[i]
            if escape_next:
                escape_next = False
                continue
            if ch == "\\":
                escape_next = True
                continue
            if ch == '"':
                in_string = not in_string
                continue
            if in_string:
                continue
            if ch == "{":
                brace_count += 1
            elif ch == "}":
                brace_count -= 1
                if brace_count == 0:
                    return text[start:i + 1]
        return text[start:]

    # ---------------- Agent 调用封装 ----------------

    def run_agent(self, agent_name, prompt):
        """chat + JSON 解析；解析失败抛异常，触发上层降级。"""
        content = self.chat(prompt)
        parsed = self.parse_json_from_text(content)
        if not parsed:
            raise RuntimeError(
                f"{agent_name} 返回内容无法解析为JSON（长度 {len(content) if content else 0}）"
            )
        return parsed

    # ---------------- token 统计 ----------------

    @staticmethod
    def _log_tokens(usage):
        if not usage:
            return
        if "prompt_tokens" in usage or "completion_tokens" in usage:  # OpenAI 兼容
            print(
                "[LLM] token统计: "
                f"prompt={usage.get('prompt_tokens')}, "
                f"completion={usage.get('completion_tokens')}, "
                f"total={usage.get('total_tokens')}"
            )
            return
        # Coze 格式
        print(
            "[LLM] token统计: "
            f"input={usage.get('input_count')}, "
            f"output={usage.get('output_count')}, "
            f"total={usage.get('token_count')}"
        )


# 单例
LLM_SERVICE = LLMService()


# ---------------- 模块级兼容接口（供 api/analyze.py、main.py 调用） ----------------

def is_configured():
    return LLM_SERVICE.is_configured()


def chat(prompt):
    return LLM_SERVICE.chat(prompt)


def run_agent(agent_name, prompt):
    return LLM_SERVICE.run_agent(agent_name, prompt)


def parse_json_from_text(content):
    return LLM_SERVICE.parse_json_from_text(content)
"""构造带连接池与传输层重试的 ChatOpenAI，避免偶发 TLS ConnectError。

传输层重试（httpx AsyncHTTPTransport retries）在 socket/TLS 层自动重连，
比应用层 astream_agent_with_retry 响应更快，两层同时存在互补不冲突。
"""

from __future__ import annotations

import httpx
from langchain_openai import ChatOpenAI

from app.core.config import get_settings

settings = get_settings()

# 连接池配置：保持长连接、限制最大并发，减少每次握手开销
_LIMITS = httpx.Limits(
    max_keepalive_connections=10,
    max_connections=20,
    keepalive_expiry=30,
)


def _make_http_client() -> httpx.AsyncClient:
    """返回配置了传输层重试与连接池的 httpx 客户端。"""
    transport = httpx.AsyncHTTPTransport(
        retries=2,          # socket 层自动重连（ConnectError / EOF），每次间隔极短
        limits=_LIMITS,
    )
    timeout = httpx.Timeout(
        connect=15.0,       # TLS 握手最多等 15s，超时立刻抛错给应用层重试
        read=float(settings.AGENT_LLM_TIMEOUT_SEC),
        write=30.0,
        pool=10.0,
    )
    return httpx.AsyncClient(transport=transport, timeout=timeout)


def build_llm(*, streaming: bool | None = None, temperature: float = 0.7) -> ChatOpenAI:
    """
    带连接池重试的 ChatOpenAI。
    - http_async_client：自定义 httpx client，传输层自动重连 2 次
    - max_retries=0：禁用 openai SDK 自身重试，由外层 astream_agent_with_retry 控制
    """
    use_stream = settings.CHAT_STREAM_LLM if streaming is None else streaming
    return ChatOpenAI(
        model=settings.DEFAULT_MODEL,
        api_key=settings.API_302_KEY,
        base_url=f"{settings.API_302_BASE_URL}",
        temperature=temperature,
        streaming=use_stream,
        max_retries=0,
        http_async_client=_make_http_client(),
    )

"""SSE / astream_events 辅助：避免工具输出序列化失败拖垮整条智能体流。"""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from langgraph.graph.graph import CompiledGraph

logger = logging.getLogger(__name__)

# 可重试的网络/连接类异常（模块级延迟导入以避免强依赖顺序）
def _is_retryable_conn_error(exc: BaseException) -> bool:
    """返回 True 表示该异常是瞬时连接错误，可以重试。"""
    cls_name = type(exc).__name__
    module = type(exc).__module__ or ""
    # openai.APIConnectionError / openai.APITimeoutError
    if "openai" in module and cls_name in ("APIConnectionError", "APITimeoutError"):
        return True
    # httpx.ConnectError / ConnectTimeout / ReadTimeout
    if "httpx" in module and cls_name in ("ConnectError", "ConnectTimeout", "ReadTimeout"):
        return True
    # httpcore.ConnectError
    if "httpcore" in module and "ConnectError" in cls_name:
        return True
    return False


def _append_content_parts(content: Any, out: list[str]) -> None:
    if isinstance(content, str) and content:
        out.append(content)
    elif isinstance(content, list):
        for p in content:
            if isinstance(p, dict) and p.get("type") == "text":
                t = p.get("text", "")
                if isinstance(t, str) and t:
                    out.append(t)


def iter_llm_text_chunks_from_astream_event(event_type: str, event: dict[str, Any]) -> list[str]:
    """
    从 LangChain astream_events v2 的 LLM 事件中取出宜下发的文本片段。
    - on_chat_model_stream: chunk.content
    - on_chat_model_end: output.content（非流式 / 部分图用）
    """
    data = event.get("data") or {}
    chunks: list[str] = []
    if event_type == "on_chat_model_stream":
        chunk = data.get("chunk")
        if chunk is not None:
            _append_content_parts(getattr(chunk, "content", None), chunks)
        return chunks
    if event_type == "on_chat_model_end":
        msg = data.get("output")
        if msg is not None:
            _append_content_parts(getattr(msg, "content", None), chunks)
        return chunks
    return chunks


def llm_text_pieces_for_sse(evt: str, event: dict[str, Any], *, stream_llm: bool) -> list[str]:
    """
    stream_llm=True：只消费 on_chat_model_stream（逐字）。
    stream_llm=False：优先整段 on_chat_model_end；若无则回退 stream（兼容不同 LC/LangGraph 版本）。
    """
    if stream_llm:
        if evt != "on_chat_model_stream":
            return []
        return iter_llm_text_chunks_from_astream_event("on_chat_model_stream", event)
    if evt == "on_chat_model_end":
        return iter_llm_text_chunks_from_astream_event("on_chat_model_end", event)
    if evt == "on_chat_model_stream":
        return iter_llm_text_chunks_from_astream_event("on_chat_model_stream", event)
    return []


async def astream_agent_with_retry(
    agent: "CompiledGraph",
    inputs: dict[str, Any],
    *,
    max_retries: int = 3,
    base_delay: float = 1.5,
):
    """
    带网络重试的 astream_events 包装器（async generator）。

    规则：
    - 仅对 LLM 层连接/超时类错误重试。
    - 一旦已产出 LLM 文本事件（on_chat_model_stream/end），不再重试，直接上抛。
    - 重试间隔：base_delay * 2^(attempt-1)，即 1.5s → 3s → 6s。
    """
    last_exc: BaseException | None = None
    for attempt in range(max_retries):
        if attempt > 0:
            delay = base_delay * (2 ** (attempt - 1))
            logger.warning(
                "LLM connection error, retry %d/%d in %.1fs: %s",
                attempt,
                max_retries - 1,
                delay,
                last_exc,
            )
            await asyncio.sleep(delay)

        text_started = False
        try:
            async for event in agent.astream_events(inputs, version="v2"):
                evt = event.get("event")
                if evt in ("on_chat_model_stream", "on_chat_model_end"):
                    text_started = True
                yield event
            return
        except BaseException as exc:
            last_exc = exc
            if not _is_retryable_conn_error(exc):
                raise
            if text_started:
                # 已有部分文字输出，重试会造成重复，直接上抛
                raise
            # 连接错误且没有文字输出：继续重试

    if last_exc is not None:
        raise last_exc


def safe_tool_output_preview(out: Any, *, max_len: int = 800) -> str:
    if out is None:
        return ""
    if isinstance(out, str):
        s = out
    else:
        try:
            s = str(out)
        except Exception:
            return "（工具输出无法预览）"
    if len(s) > max_len:
        return s[:max_len] + "…"
    return s

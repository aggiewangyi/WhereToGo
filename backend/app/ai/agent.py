"""LangGraph ReAct agent: real tool execution loop + streaming events."""

from __future__ import annotations

import logging
from functools import lru_cache

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langgraph.prebuilt import create_react_agent

from app.ai.llm_client import build_llm
from app.ai.prompts.planner import SYSTEM_PROMPT_01
from app.ai.streaming_utils import astream_agent_with_retry, llm_text_pieces_for_sse, safe_tool_output_preview
from app.ai.tools import ALL_TOOLS
from app.ai.tools.tool_timeout import wrap_tools_with_timeout
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

_MAX_HISTORY_MESSAGES = 40


@lru_cache(maxsize=1)
def get_react_graph():
    """Singleton compiled graph (tools + model bound inside create_react_agent)."""
    llm = build_llm()
    tools = wrap_tools_with_timeout(list(ALL_TOOLS), get_settings().AGENT_TOOL_TIMEOUT_SEC)
    return create_react_agent(llm, tools, prompt=SYSTEM_PROMPT_01)


def build_message_list(message: str, history: list[BaseMessage] | None) -> list[BaseMessage]:
    prior = list(history or [])[-_MAX_HISTORY_MESSAGES:]
    return [*prior, HumanMessage(content=message)]


async def chat_completion(message: str, history: list[BaseMessage] | None = None):
    """
    Multi-turn chat with executed tools. Yields (event_type, data) for SSE.

    event_type: text | tool_start | tool_end | error | done
    """
    graph = get_react_graph()
    messages = build_message_list(message, history)

    try:
        async for event in astream_agent_with_retry(
            graph,
            {"messages": messages},
            max_retries=get_settings().AGENT_LLM_RETRY,
        ):
            try:
                evt = event.get("event")
                for piece in llm_text_pieces_for_sse(evt, event, stream_llm=settings.CHAT_STREAM_LLM):
                    if piece:
                        yield ("text", piece)
                if evt == "on_tool_start":
                    data = event.get("data") or {}
                    name = event.get("name") or data.get("name") or ""
                    yield ("tool_start", {"name": name, "input": data.get("input")})
                elif evt == "on_tool_end":
                    data = event.get("data") or {}
                    name = event.get("name") or data.get("name") or ""
                    out = data.get("output")
                    preview = safe_tool_output_preview(out)
                    yield ("tool_end", {"name": name, "output": preview})
            except Exception:
                logger.exception("chat_completion stream event failed")
                continue
    except Exception:
        logger.exception("chat_completion stream failed")
        yield ("error", {"message": "对话服务暂时不可用，请稍后重试。"})
    yield ("done", None)


def extract_final_text(messages: list[BaseMessage]) -> str:
    for msg in reversed(messages):
        if isinstance(msg, AIMessage):
            c = msg.content
            if isinstance(c, str):
                return c
            if isinstance(c, list):
                parts: list[str] = []
                for p in c:
                    if isinstance(p, dict) and p.get("type") == "text":
                        parts.append(str(p.get("text", "")))
                return "".join(parts)
    return ""


async def chat_invoke_blocking(message: str, history: list[BaseMessage] | None = None) -> str:
    """Non-streaming: full agent run, return final assistant text."""
    graph = get_react_graph()
    messages = build_message_list(message, history)
    try:
        result = await graph.ainvoke({"messages": messages})
        final_messages = result.get("messages", [])
        return extract_final_text(list(final_messages))
    except Exception:
        logger.exception("chat_invoke_blocking failed")
        return "对话服务暂时不可用，请稍后重试。"

"""工具超时/异常时返回简短说明：不中断 ReAct，由模型用常识与上文继续答。"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from langchain_core.tools import BaseTool, StructuredTool
from pydantic import BaseModel, ConfigDict

logger = logging.getLogger(__name__)


def _filtered_tool_kwargs(inner: BaseTool, kwargs: dict[str, Any]) -> dict[str, Any]:
    """只向内层工具传 schema 声明的字段，避免 LangGraph 注入字段导致校验/调用异常。"""
    schema = getattr(inner, "args_schema", None)
    if schema is None:
        return dict(kwargs)
    try:
        names = set(schema.model_fields.keys())
    except AttributeError:
        return dict(kwargs)
    return {k: v for k, v in kwargs.items() if k in names}


def _args_schema_ignore_extra(schema: type[BaseModel]) -> type[BaseModel]:
    """子类 schema：忽略 tool_call_id 等多余入参，避免包装工具在调用前就校验失败。"""

    class _IgnoreExtra(schema):
        model_config = ConfigDict(extra="ignore")

    _IgnoreExtra.__name__ = f"{schema.__name__}IgnoreExtra"
    return _IgnoreExtra


def wrap_tool_with_timeout(tool: BaseTool, timeout_sec: float) -> BaseTool:
    """超时/失败时返回中性文案：等价于本条无工具结果，模型照常往下推理。"""

    async def _arun(**kwargs: Any) -> str:
        payload = _filtered_tool_kwargs(tool, kwargs)
        try:
            return await asyncio.wait_for(tool.ainvoke(payload), timeout=timeout_sec)
        except asyncio.TimeoutError:
            logger.warning(
                "agent tool timeout name=%s timeout_sec=%s",
                tool.name,
                timeout_sec,
            )
            return (
                f"「{tool.name}」本次超时（>{int(timeout_sec)}s），无工具返回，已跳过。"
                "请结合对话上文与你自身知识直接回答，不必再等同一条工具结果。"
            )
        except Exception:
            logger.exception("agent tool failed name=%s", tool.name)
            return (
                f"「{tool.name}」暂不可用，无工具返回，已跳过。"
                "请结合对话上文与你自身知识直接回答即可。"
            )

    schema = getattr(tool, "args_schema", None)
    if schema is None:
        return tool

    try:
        if isinstance(schema, type) and issubclass(schema, BaseModel):
            wrap_schema = _args_schema_ignore_extra(schema)
        else:
            wrap_schema = schema
    except Exception:
        logger.warning("tool_timeout: could not relax args_schema for %s", tool.name)
        wrap_schema = schema

    return StructuredTool.from_function(
        coroutine=_arun,
        name=tool.name,
        description=tool.description or "",
        args_schema=wrap_schema,
    )


def wrap_tools_with_timeout(tools: list[BaseTool], timeout_sec: float) -> list[BaseTool]:
    if timeout_sec <= 0:
        return tools
    return [wrap_tool_with_timeout(t, timeout_sec) for t in tools]

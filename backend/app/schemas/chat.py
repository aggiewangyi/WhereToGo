from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.base import SchemaBase


class ChatHistoryItem(BaseModel):
    """Prior turns only; latest user message is sent in `message`."""

    role: Literal["user", "assistant"]
    content: str = Field(default="", max_length=32000)


class ChatRequest(BaseModel):
    session_id: str | None = None
    message: str = Field(..., min_length=1)
    # 会话级交互：verbose 播报/提示更细；quiet 少打扰（话术更短）；图内移交规则一致，均需用户确认草案后再行前
    interaction_mode: Literal["verbose", "quiet"] | None = None
    trip_id: int | None = None
    stream: bool = True
    history: list[ChatHistoryItem] | None = Field(
        default=None,
        description="Earlier conversation turns (Layer-1 client cache); capped server-side.",
    )


class ChatToolCall(BaseModel):
    name: str
    arguments: dict


class ChatDelta(BaseModel):
    type: str  # "text" | "tool_call" | "tool_result" | "done"
    content: str | None = None
    tool_call: ChatToolCall | None = None
    tool_result: dict | None = None


class ChatSessionListItem(SchemaBase):
    id: str
    title: str | None
    updated_at: datetime


class ChatTurnOut(SchemaBase):
    role: str
    content: str
    created_at: datetime


class ChatHistoryPayload(BaseModel):
    session_id: str
    messages: list[ChatTurnOut]

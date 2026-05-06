"""从用户本轮输入中抽取对行程/服务的满意与不满点，写入持久旅行记忆。"""

from __future__ import annotations

import logging

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from app.ai.llm_client import build_llm

logger = logging.getLogger(__name__)


class _FeedbackDelta(BaseModel):
    satisfied: list[str] = Field(default_factory=list, description="用户满意、喜欢、想保留的要点，短句")
    unsatisfied: list[str] = Field(default_factory=list, description="不满意、太累、太贵、不想去等，短句")
    implicit_note: str | None = Field(default=None, description="推断的隐藏需求或约束，一句中文")


_EXTRACT_SYSTEM = """你是旅行对话反馈抽取器。根据「用户最新一句」判断是否在评价上一轮助手输出。
- 若用户在提新问题、改目的地、闲聊与评价无关，三列表输出空数组、implicit_note 为 null。
- satisfied：明确褒义、想保留、「就按这个」「不错」等可映射的具体点（简短）。
- unsatisfied：明确批评、拒绝、太累、太贵、太远、不要某类安排等（简短）。
- implicit_note：仅当能推断隐藏偏好/禁忌时给一句，否则 null。
只输出结构化结果，不要 Markdown。"""


async def extract_feedback_delta(user_message: str, assistant_reply_tail: str) -> _FeedbackDelta:
    """assistant_reply_tail 传末尾 4000 字即可，降本。"""
    u = (user_message or "").strip()
    if not u or len(u) > 800:
        return _FeedbackDelta()
    tail = (assistant_reply_tail or "")[-4000:]
    llm = build_llm(streaming=False, temperature=0.2).with_structured_output(_FeedbackDelta)
    try:
        out = await llm.ainvoke(
            [
                SystemMessage(content=_EXTRACT_SYSTEM),
                HumanMessage(
                    content=f"【用户最新一句】\n{u}\n\n【助手回复片段】\n{tail}",
                ),
            ],
        )
        if isinstance(out, _FeedbackDelta):
            return out
        return _FeedbackDelta.model_validate(out)
    except Exception:
        logger.exception("extract_feedback_delta failed")
        return _FeedbackDelta()

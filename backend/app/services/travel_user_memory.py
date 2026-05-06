"""跨会话旅行记忆：对话结束后合并用户反馈。"""

from __future__ import annotations

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.multi_agent.feedback_extract import extract_feedback_delta
from app.ai.schemas.persistent_travel_memory import PersistentTravelMemory
from app.crud.travel_memory import get_persistent_travel_memory, save_persistent_travel_memory

logger = logging.getLogger(__name__)


async def persist_user_interaction_mode_default(db: AsyncSession, user_id: int, mode: str) -> None:
    """将用户显式选择的交互模式写入跨会话记忆，供后续新会话默认继承。"""
    if mode not in ("verbose", "quiet"):
        return
    try:
        mem = await get_persistent_travel_memory(db, user_id)
        merged = mem.merge_delta(
            satisfied=[],
            unsatisfied=[],
            implicit_note=None,
            destination_hint=None,
            mode_default=mode,
        )
        await save_persistent_travel_memory(db, user_id, merged)
        await db.flush()
    except Exception:
        logger.exception("persist_user_interaction_mode_default failed for user %s", user_id)


async def merge_feedback_after_turn(
    db: AsyncSession,
    user_id: int,
    user_message: str,
    assistant_reply: str,
) -> None:
    """将本轮对话中可解析的满意/不满点写入 users.travel_memory。"""
    delta = await extract_feedback_delta(user_message, assistant_reply)
    if not delta.satisfied and not delta.unsatisfied and not delta.implicit_note:
        return
    try:
        mem = await get_persistent_travel_memory(db, user_id)
        merged = mem.merge_delta(
            satisfied=delta.satisfied,
            unsatisfied=delta.unsatisfied,
            implicit_note=delta.implicit_note,
            destination_hint=None,
            mode_default=None,
        )
        await save_persistent_travel_memory(db, user_id, merged)
        await db.flush()
    except Exception:
        logger.exception("merge_feedback_after_turn failed for user %s", user_id)

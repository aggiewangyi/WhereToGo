"""users.travel_memory 读写（跨会话旅行记忆）。"""

from __future__ import annotations

import json
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.schemas.persistent_travel_memory import PersistentTravelMemory
from app.models.user import User

logger = logging.getLogger(__name__)


async def get_persistent_travel_memory(db: AsyncSession, user_id: int) -> PersistentTravelMemory:
    result = await db.execute(select(User.travel_memory).where(User.id == user_id))
    raw = result.scalar_one_or_none()
    if not raw or not str(raw).strip():
        return PersistentTravelMemory()
    try:
        data = json.loads(raw)
        return PersistentTravelMemory.model_validate(data)
    except Exception:
        logger.warning("invalid travel_memory json for user %s, resetting", user_id)
        return PersistentTravelMemory()


async def save_persistent_travel_memory(db: AsyncSession, user_id: int, mem: PersistentTravelMemory) -> None:
    u = await db.get(User, user_id)
    if u is None:
        return
    u.travel_memory = mem.model_dump_json(ensure_ascii=False)
    await db.flush()

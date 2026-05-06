import uuid
from datetime import datetime, timezone

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chat import ChatMessage, ChatSession


async def get_session_by_id(db: AsyncSession, session_id: str, user_id: int) -> ChatSession | None:
    stmt = select(ChatSession).where(ChatSession.id == session_id, ChatSession.user_id == user_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def create_session(
    db: AsyncSession,
    user_id: int,
    *,
    trip_id: int | None = None,
    title: str | None = None,
) -> ChatSession:
    sid = str(uuid.uuid4())
    obj = ChatSession(id=sid, user_id=user_id, trip_id=trip_id, title=title)
    db.add(obj)
    await db.flush()
    await db.refresh(obj)
    return obj


async def list_messages_for_llm(db: AsyncSession, session_id: str, limit: int = 50) -> list[ChatMessage]:
    """Return the last `limit` messages in chronological order."""
    stmt = (
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    rows = list(result.scalars().all())
    rows.reverse()
    return rows


async def append_message(db: AsyncSession, session_id: str, role: str, content: str) -> ChatMessage:
    msg = ChatMessage(session_id=session_id, role=role, content=content)
    db.add(msg)
    await db.flush()
    await db.refresh(msg)
    await touch_session_updated(db, session_id)
    return msg


async def touch_session_updated(db: AsyncSession, session_id: str) -> None:
    sess = await db.get(ChatSession, session_id)
    if sess is None:
        return
    sess.updated_at = datetime.now(timezone.utc)
    await db.flush()


async def list_sessions_for_user(db: AsyncSession, user_id: int, *, limit: int = 50) -> list[ChatSession]:
    stmt = (
        select(ChatSession)
        .where(ChatSession.user_id == user_id)
        .order_by(desc(ChatSession.updated_at))
        .limit(limit)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def list_messages_for_ui(db: AsyncSession, session_id: str, *, limit: int = 400) -> list[ChatMessage]:
    stmt = (
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_pending_prep_payload(db: AsyncSession, session_id: str) -> str | None:
    stmt = select(ChatSession.pending_prep_payload).where(ChatSession.id == session_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def set_pending_prep_payload(db: AsyncSession, session_id: str, payload_json: str) -> None:
    sess = await db.get(ChatSession, session_id)
    if sess is None:
        return
    sess.pending_prep_payload = payload_json
    await db.flush()


async def clear_pending_prep_payload(db: AsyncSession, session_id: str) -> None:
    sess = await db.get(ChatSession, session_id)
    if sess is None:
        return
    sess.pending_prep_payload = None
    await db.flush()


async def get_session_interaction_mode(db: AsyncSession, session_id: str) -> str | None:
    stmt = select(ChatSession.interaction_mode).where(ChatSession.id == session_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def set_session_interaction_mode(db: AsyncSession, session_id: str, mode: str) -> None:
    sess = await db.get(ChatSession, session_id)
    if sess is None:
        return
    sess.interaction_mode = mode
    await db.flush()


async def get_langgraph_thread_id(db: AsyncSession, session_id: str) -> str | None:
    stmt = select(ChatSession.langgraph_thread_id).where(ChatSession.id == session_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def set_langgraph_thread_id(db: AsyncSession, session_id: str, thread_id: str) -> None:
    sess = await db.get(ChatSession, session_id)
    if sess is None:
        return
    sess.langgraph_thread_id = thread_id
    await db.flush()


async def clear_langgraph_thread_id(db: AsyncSession, session_id: str) -> None:
    sess = await db.get(ChatSession, session_id)
    if sess is None:
        return
    sess.langgraph_thread_id = None
    await db.flush()

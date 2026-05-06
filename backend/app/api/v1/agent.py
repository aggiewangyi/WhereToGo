"""旅行 Agent：对话（SSE）、会话列表与历史恢复（按登录用户隔离）。"""

import json
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.api.deps_agent import get_agent_principal
from app.core.config import get_settings
from app.crud import chat as chat_crud
from app.models.user import User
from app.schemas.chat import ChatHistoryPayload, ChatRequest, ChatSessionListItem, ChatTurnOut
from app.services import chat_service
from app.services.travel_user_memory import merge_feedback_after_turn, persist_user_interaction_mode_default

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/agent", tags=["agent"])
settings = get_settings()


async def _sse_generator(
    body: ChatRequest,
    session_id: str,
    prior: list,
    db: AsyncSession,
    user_id: int,
):
    try:
        sess_payload = json.dumps({"type": "session", "data": {"session_id": session_id}}, ensure_ascii=False)
        yield f"event: session\ndata: {sess_payload}\n\n"

        if body.interaction_mode in ("verbose", "quiet"):
            await chat_crud.set_session_interaction_mode(db, session_id, body.interaction_mode)
            await persist_user_interaction_mode_default(db, user_id, body.interaction_mode)

        parts: list[str] = []
        db_arg = db if settings.CHAT_MULTI_AGENT else None
        stream = chat_service.stream_chat_events(
            body.message,
            prior,
            db_arg,
            session_id=session_id if db_arg else None,
            user_id=user_id if db_arg else None,
            interaction_mode=body.interaction_mode,
        )
        async for event_type, data in stream:
            if event_type == "text" and data:
                parts.append(str(data))
            payload = json.dumps({"type": event_type, "data": data}, ensure_ascii=False)
            yield f"event: {event_type}\ndata: {payload}\n\n"

        assistant_text = "".join(parts)
        await chat_service.persist_user_and_assistant(db, session_id, body.message, assistant_text)
        if settings.CHAT_MULTI_AGENT and settings.CHAT_FEEDBACK_MEMORY:
            await merge_feedback_after_turn(db, user_id, body.message, assistant_text)
    except Exception:
        logger.exception("agent sse pipeline failed")
        err = json.dumps(
            {"type": "error", "data": {"message": "Agent 处理失败，请稍后重试。"}},
            ensure_ascii=False,
        )
        yield f"event: error\ndata: {err}\n\n"
        done = json.dumps({"type": "done", "data": None}, ensure_ascii=False)
        yield f"event: done\ndata: {done}\n\n"


@router.get("/sessions", response_model=list[ChatSessionListItem])
async def list_chat_sessions(
    user: User = Depends(get_agent_principal),
    db: AsyncSession = Depends(get_session),
):
    rows = await chat_crud.list_sessions_for_user(db, user.id, limit=50)
    return [ChatSessionListItem.model_validate(r) for r in rows]


@router.get("/sessions/{session_id}/messages", response_model=ChatHistoryPayload)
async def get_session_messages(
    session_id: str,
    user: User = Depends(get_agent_principal),
    db: AsyncSession = Depends(get_session),
):
    sess = await chat_crud.get_session_by_id(db, session_id, user.id)
    if sess is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="会话不存在或无权访问")
    rows = await chat_crud.list_messages_for_ui(db, session_id)
    turns = [ChatTurnOut.model_validate(m) for m in rows]
    return ChatHistoryPayload(session_id=session_id, messages=turns)


@router.post("/chat")
async def agent_chat(
    body: ChatRequest,
    user: User = Depends(get_agent_principal),
    db: AsyncSession = Depends(get_session),
):
    uid = user.id
    session_id, prior = await chat_service.resolve_session_and_prior_messages(db, uid, body)

    if body.stream:
        return StreamingResponse(
            _sse_generator(body, session_id, prior, db, uid),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    if body.interaction_mode in ("verbose", "quiet"):
        await chat_crud.set_session_interaction_mode(db, session_id, body.interaction_mode)
        await persist_user_interaction_mode_default(db, uid, body.interaction_mode)

    db_arg = db if settings.CHAT_MULTI_AGENT else None
    text = await chat_service.collect_blocking_reply(
        body.message,
        prior,
        db_arg,
        session_id=session_id if db_arg else None,
        user_id=uid if db_arg else None,
        interaction_mode=body.interaction_mode,
    )
    await chat_service.persist_user_and_assistant(db, session_id, body.message, text)
    if settings.CHAT_MULTI_AGENT and settings.CHAT_FEEDBACK_MEMORY:
        await merge_feedback_after_turn(db, uid, body.message, text)
    return {"type": "text", "content": text, "session_id": session_id}

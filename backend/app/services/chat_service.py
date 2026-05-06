"""Chat session resolution, history merge, and persistence."""

from collections.abc import Sequence

from fastapi import HTTPException, status
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.agent import chat_completion as single_agent_completion, chat_invoke_blocking
from app.ai.multi_agent import multi_agent_completion
from app.core.config import get_settings
from app.crud import chat as chat_crud
from app.schemas.chat import ChatHistoryItem, ChatRequest

settings = get_settings()

# 解析会话和先前消息
async def resolve_session_and_prior_messages(
    db: AsyncSession,
    user_id: int,
    body: ChatRequest,
) -> tuple[str, list[BaseMessage]]:
    """
    Returns (session_id, prior_turns_as_langchain_messages).
    Current user utterance is NOT included.
    """
    if body.session_id:
        sess = await chat_crud.get_session_by_id(db, body.session_id, user_id)
        if sess is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="会话不存在或无权访问")
        sid = sess.id
        rows = await chat_crud.list_messages_for_llm(db, sid, limit=80)
        prior: list[BaseMessage] = []
        for r in rows:
            if r.role == "user":
                prior.append(HumanMessage(content=r.content))
            elif r.role == "assistant":
                prior.append(AIMessage(content=r.content))
        return sid, prior

    sess = await chat_crud.create_session(db, user_id, trip_id=body.trip_id)
    sid = sess.id
    if body.history:
        for h in body.history[-40:]:
            await chat_crud.append_message(db, sid, h.role, h.content)
        rows = await chat_crud.list_messages_for_llm(db, sid, limit=80)
    else:
        rows = []
    prior = []
    for r in rows:
        if r.role == "user":
            prior.append(HumanMessage(content=r.content))
        elif r.role == "assistant":
            prior.append(AIMessage(content=r.content))
    return sid, prior

# 持久化用户和助手对话
async def persist_user_and_assistant(
    db: AsyncSession,
    session_id: str,
    user_text: str,
    assistant_text: str,
) -> None:
    await chat_crud.append_message(db, session_id, "user", user_text)
    await chat_crud.append_message(db, session_id, "assistant", assistant_text)

# 流式返回对话事件
def stream_chat_events(
    message: str,
    prior: Sequence[BaseMessage],
    db: AsyncSession | None,
    *,
    session_id: str | None = None,
    user_id: int | None = None,
    interaction_mode: str | None = None,
):
    if settings.CHAT_MULTI_AGENT and db is not None:
        return multi_agent_completion(
            message,
            list(prior),
            db,
            session_id=session_id,
            user_id=user_id,
            interaction_mode=interaction_mode,
        )
    return single_agent_completion(message, list(prior))


async def collect_blocking_reply(
    message: str,
    prior: list[BaseMessage],
    db: AsyncSession | None,
    *,
    session_id: str | None = None,
    user_id: int | None = None,
    interaction_mode: str | None = None,
) -> str:
    if settings.CHAT_MULTI_AGENT and db is not None:
        parts: list[str] = []
        async for event_type, data in multi_agent_completion(
            message,
            prior,
            db,
            session_id=session_id,
            user_id=user_id,
            interaction_mode=interaction_mode,
        ):
            if event_type == "text" and data:
                parts.append(str(data))
        return "".join(parts)
    return await chat_invoke_blocking(message, prior)

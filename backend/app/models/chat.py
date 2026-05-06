from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[str | None] = mapped_column(String(200), default=None)
    trip_id: Mapped[int | None] = mapped_column(ForeignKey("trips.id"), default=None, index=True)
    # JSON: 行程已定稿、待用户确认后再跑 Agent3（行前）
    pending_prep_payload: Mapped[str | None] = mapped_column(Text, default=None)
    # verbose: 播报更细；quiet: 少打扰；二者不改变 LangGraph 在行程确认处的挂起逻辑
    interaction_mode: Mapped[str | None] = mapped_column(String(16), default=None)
    # LangGraph SqliteSaver / MemorySaver 的 thread_id，用于 interrupt 恢复
    langgraph_thread_id: Mapped[str | None] = mapped_column(String(40), default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    messages: Mapped[list["ChatMessage"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
    )


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String(36), ForeignKey("chat_sessions.id"), index=True)
    role: Mapped[str] = mapped_column(String(20))
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    session: Mapped["ChatSession"] = relationship(back_populates="messages")

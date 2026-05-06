from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    phone: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    nickname: Mapped[str] = mapped_column(String(50))
    avatar: Mapped[str | None] = mapped_column(String(500), default=None)
    hashed_password: Mapped[str] = mapped_column(String(200))
    preferences: Mapped[str | None] = mapped_column(Text, default=None, comment="JSON: travel preferences")
    travel_memory: Mapped[str | None] = mapped_column(
        Text, default=None, comment="JSON: cross-session travel memory (likes, dislikes, implicit needs)"
    )
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

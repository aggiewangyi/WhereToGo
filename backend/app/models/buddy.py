from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class BuddyPost(Base):
    __tablename__ = "buddy_posts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    destination: Mapped[str] = mapped_column(String(100))
    date_start: Mapped[date | None] = mapped_column(Date, default=None)
    date_end: Mapped[date | None] = mapped_column(Date, default=None)
    budget_min: Mapped[float | None] = mapped_column(Float, default=None)
    budget_max: Mapped[float | None] = mapped_column(Float, default=None)
    people_wanted: Mapped[int] = mapped_column(Integer, default=1)
    tags: Mapped[str | None] = mapped_column(String(500), comment="comma separated: 摄影,AA,女生结伴")
    description: Mapped[str | None] = mapped_column(Text, default=None)
    status: Mapped[str] = mapped_column(
        Enum("open", "closed", "full", name="buddy_post_status"),
        default="open",
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    applications: Mapped[list["BuddyApplication"]] = relationship(back_populates="post")


class BuddyApplication(Base):
    __tablename__ = "buddy_applications"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    post_id: Mapped[int] = mapped_column(ForeignKey("buddy_posts.id"), index=True)
    applicant_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    self_intro: Mapped[str | None] = mapped_column(Text, default=None, comment="申请者简介")
    message: Mapped[str | None] = mapped_column(Text, default=None)
    status: Mapped[str] = mapped_column(
        Enum("pending", "accepted", "rejected", name="buddy_app_status"),
        default="pending",
    )
    match_score: Mapped[float | None] = mapped_column(Float, default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    post: Mapped["BuddyPost"] = relationship(back_populates="applications")

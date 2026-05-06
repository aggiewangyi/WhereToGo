from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Destination(Base):
    __tablename__ = "destinations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), index=True)
    country: Mapped[str] = mapped_column(String(100))
    province: Mapped[str | None] = mapped_column(String(100), default=None)
    city: Mapped[str | None] = mapped_column(String(100), default=None)
    tags: Mapped[str | None] = mapped_column(Text, default=None, comment="JSON array: ['海岛','小众']")
    best_seasons: Mapped[str | None] = mapped_column(String(100), comment="e.g. '3,4,5,9,10'")
    avg_cost_per_day: Mapped[float | None] = mapped_column(Float, default=None, comment="CNY")
    visa_required: Mapped[int] = mapped_column(Integer, default=0, comment="0=免签 1=落地签 2=需办签")
    safety_level: Mapped[int] = mapped_column(Integer, default=5, comment="1-5, 5=safest")
    knowledge_card: Mapped[str | None] = mapped_column(Text, default=None, comment="JSON: laws/customs/tips")
    cover_image: Mapped[str | None] = mapped_column(String(500), default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

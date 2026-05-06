"""Structured travel intent extracted from conversation (Agent 1 output signal for downstream agents)."""

from pydantic import BaseModel, Field


class TravelProfile(BaseModel):
    destination: str | None = Field(default=None, description="确定或最可能的目的地")
    days: int | None = Field(default=None, ge=1, le=90, description="出行天数")
    budget_level: str | None = Field(default=None, description="如：穷游/舒适/豪华/不限")
    traveler_type: str | None = Field(default=None, description="如：情侣/亲子/独行/朋友")
    preferences: list[str] = Field(default_factory=list, description="偏好标签")
    departure_city: str | None = None
    people_count: int | None = Field(default=None, ge=1)
    notes: str | None = Field(default=None, description="其他约束或原话摘要")

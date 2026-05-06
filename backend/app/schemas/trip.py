from datetime import date, datetime

from pydantic import BaseModel, Field

from app.schemas.base import SchemaBase


# ---------- Request ----------
class TripCreate(BaseModel):
    title: str = Field(..., max_length=200)
    destination_id: int | None = None
    start_date: date | None = None
    end_date: date | None = None
    people_count: int = Field(1, ge=1)


class TripUpdate(BaseModel):
    title: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    people_count: int | None = None
    status: str | None = None


class TripGenerateRequest(BaseModel):
    """AI 一键生成行程的请求体"""
    destination: str = Field(..., description="目的地名称或关键词")
    days: int = Field(..., ge=1, le=30)
    people_count: int = Field(1, ge=1)
    budget: float | None = Field(None, ge=0)
    preferences: list[str] | None = Field(None, description="偏好标签: 美食/自然/人文...")


# ---------- Response ----------
class ItineraryOut(SchemaBase):
    id: int
    trip_id: int
    days: str | None = None
    generated_by_ai: bool
    updated_at: datetime


class BudgetOut(SchemaBase):
    id: int
    trip_id: int
    total: float
    currency: str
    categories: str | None = None


class TripOut(SchemaBase):
    id: int
    user_id: int
    destination_id: int | None = None
    title: str
    start_date: date | None = None
    end_date: date | None = None
    people_count: int
    status: str
    created_at: datetime
    itinerary: ItineraryOut | None = None
    budget: BudgetOut | None = None

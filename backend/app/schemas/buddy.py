from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.base import SchemaBase


# ---------- Request ----------
class BuddyPostCreate(BaseModel):
    destination: str = Field(..., max_length=100)
    date_start: date | None = None
    date_end: date | None = None
    budget_min: float | None = None
    budget_max: float | None = None
    people_wanted: int = Field(1, ge=1)
    tags: list[str] | None = None
    description: str | None = None


class BuddyApplyRequest(BaseModel):
    """申请加入：简介与留言会展示在发布者「我的招募」中。"""

    self_intro: str | None = Field(default=None, max_length=2000)
    message: str | None = Field(default=None, max_length=2000)


class BuddyApplicationReviewRequest(BaseModel):
    action: Literal["accept", "reject"]


# ---------- Response ----------
class BuddyPostOut(SchemaBase):
    id: int
    user_id: int
    destination: str
    date_start: date | None = None
    date_end: date | None = None
    budget_min: float | None = None
    budget_max: float | None = None
    people_wanted: int
    tags: str | None = None
    description: str | None = None
    status: str
    created_at: datetime


class BuddyApplicationOut(SchemaBase):
    id: int
    post_id: int
    applicant_id: int
    self_intro: str | None = None
    message: str | None = None
    status: str
    match_score: float | None = None
    created_at: datetime


class BuddyApplicationPublisherOut(SchemaBase):
    """发布者查看的申请列表（含申请人昵称）。"""

    id: int
    post_id: int
    applicant_id: int
    applicant_nickname: str
    self_intro: str | None = None
    message: str | None = None
    status: str
    created_at: datetime

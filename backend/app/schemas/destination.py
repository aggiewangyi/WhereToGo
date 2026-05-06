from pydantic import BaseModel, Field

from app.schemas.base import SchemaBase


class DestinationRecommendRequest(BaseModel):
    keyword: str | None = Field(None, description="关键词: 海边/古镇/小众...")
    budget_per_day: float | None = None
    season: int | None = Field(None, ge=1, le=12, description="月份")
    tags: list[str] | None = None
    limit: int = Field(10, ge=1, le=50)


class DestinationOut(SchemaBase):
    id: int
    name: str
    country: str
    province: str | None = None
    city: str | None = None
    tags: str | None = None
    best_seasons: str | None = None
    avg_cost_per_day: float | None = None
    visa_required: int
    safety_level: int
    cover_image: str | None = None


class DestinationWikiOut(SchemaBase):
    id: int
    name: str
    knowledge_card: str | None = None

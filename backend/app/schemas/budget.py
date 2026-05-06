from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.base import SchemaBase


class BudgetCreate(BaseModel):
    trip_id: int
    total: float = Field(..., ge=0)
    currency: str = "CNY"
    categories: dict | None = None


class ExpenseCreate(BaseModel):
    amount: float = Field(..., gt=0)
    category: str = Field(..., max_length=50)
    note: str | None = None


class ExpenseOut(SchemaBase):
    id: int
    budget_id: int
    amount: float
    category: str
    note: str | None = None
    created_at: datetime


class BudgetSummary(SchemaBase):
    total_planned: float
    total_spent: float
    remaining: float
    currency: str
    by_category: dict

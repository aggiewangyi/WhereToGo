import json

from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.trip import crud_budget
from app.models.trip import Budget, Expense
from app.schemas.budget import BudgetCreate, BudgetSummary, ExpenseCreate


async def create_budget(db: AsyncSession, data: BudgetCreate) -> Budget:
    budget = Budget(
        trip_id=data.trip_id,
        total=data.total,
        currency=data.currency,
        categories=json.dumps(data.categories, ensure_ascii=False) if data.categories else None,
    )
    db.add(budget)
    await db.flush()
    await db.refresh(budget)
    return budget


async def add_expense(db: AsyncSession, budget_id: int, data: ExpenseCreate):
    return await crud_budget.add_expense(db, budget_id, data.amount, data.category, data.note)


async def list_expenses(db: AsyncSession, budget_id: int) -> list[Expense]:
    return await crud_budget.get_expenses(db, budget_id)


async def get_summary(db: AsyncSession, budget_id: int) -> BudgetSummary:
    budget = await crud_budget.get(db, budget_id)
    expenses = await crud_budget.get_expenses(db, budget_id)

    total_spent = sum(e.amount for e in expenses)
    by_category: dict[str, float] = {}
    for e in expenses:
        by_category[e.category] = by_category.get(e.category, 0) + e.amount

    return BudgetSummary(
        total_planned=budget.total,
        total_spent=total_spent,
        remaining=budget.total - total_spent,
        currency=budget.currency,
        by_category=by_category,
    )

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.crud.base import CRUDBase
from app.models.trip import Budget, Expense, Itinerary, Trip
from app.schemas.trip import TripCreate, TripUpdate


class CRUDTrip(CRUDBase[Trip, TripCreate, TripUpdate]):
    async def get_with_details(self, db: AsyncSession, trip_id: int) -> Trip | None:
        stmt = (
            select(Trip)
            .options(selectinload(Trip.itinerary), selectinload(Trip.budget))
            .where(Trip.id == trip_id)
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_trips(self, db: AsyncSession, user_id: int, skip: int = 0, limit: int = 20) -> list[Trip]:
        """Eager-load itinerary & budget so async session can serialize TripOut without lazy IO."""
        stmt = (
            select(Trip)
            .options(selectinload(Trip.itinerary), selectinload(Trip.budget))
            .where(Trip.user_id == user_id)
            .order_by(Trip.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())


class CRUDItinerary(CRUDBase[Itinerary, None, None]):
    async def get_by_trip(self, db: AsyncSession, trip_id: int) -> Itinerary | None:
        result = await db.execute(select(Itinerary).where(Itinerary.trip_id == trip_id))
        return result.scalar_one_or_none()

    async def upsert(self, db: AsyncSession, trip_id: int, days_json: str, by_ai: bool = True) -> Itinerary:
        existing = await self.get_by_trip(db, trip_id)
        if existing:
            existing.days = days_json
            existing.generated_by_ai = by_ai
            await db.flush()
            await db.refresh(existing)
            return existing
        obj = Itinerary(trip_id=trip_id, days=days_json, generated_by_ai=by_ai)
        db.add(obj)
        await db.flush()
        await db.refresh(obj)
        return obj


class CRUDBudget(CRUDBase[Budget, None, None]):
    async def get_by_trip(self, db: AsyncSession, trip_id: int) -> Budget | None:
        result = await db.execute(select(Budget).where(Budget.trip_id == trip_id))
        return result.scalar_one_or_none()

    async def add_expense(self, db: AsyncSession, budget_id: int, amount: float, category: str, note: str | None = None) -> Expense:
        expense = Expense(budget_id=budget_id, amount=amount, category=category, note=note)
        db.add(expense)
        await db.flush()
        await db.refresh(expense)
        return expense

    async def get_expenses(self, db: AsyncSession, budget_id: int) -> list[Expense]:
        result = await db.execute(select(Expense).where(Expense.budget_id == budget_id))
        return list(result.scalars().all())


crud_trip = CRUDTrip(Trip)
crud_itinerary = CRUDItinerary(Itinerary)
crud_budget = CRUDBudget(Budget)

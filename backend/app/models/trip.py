from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Trip(Base):
    __tablename__ = "trips"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    destination_id: Mapped[int | None] = mapped_column(ForeignKey("destinations.id"), default=None)
    title: Mapped[str] = mapped_column(String(200))
    start_date: Mapped[date | None] = mapped_column(Date, default=None)
    end_date: Mapped[date | None] = mapped_column(Date, default=None)
    people_count: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(
        Enum("draft", "planned", "ongoing", "completed", "cancelled", name="trip_status"),
        default="draft",
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    itinerary: Mapped["Itinerary | None"] = relationship(back_populates="trip", uselist=False)
    budget: Mapped["Budget | None"] = relationship(back_populates="trip", uselist=False)


class Itinerary(Base):
    __tablename__ = "itineraries"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    trip_id: Mapped[int] = mapped_column(ForeignKey("trips.id"), unique=True)
    days: Mapped[str | None] = mapped_column(Text, comment="JSON: structured day-by-day plan")
    generated_by_ai: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    trip: Mapped["Trip"] = relationship(back_populates="itinerary")


class Budget(Base):
    __tablename__ = "budgets"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    trip_id: Mapped[int] = mapped_column(ForeignKey("trips.id"), unique=True)
    total: Mapped[float] = mapped_column(Float, default=0)
    currency: Mapped[str] = mapped_column(String(10), default="CNY")
    categories: Mapped[str | None] = mapped_column(Text, comment="JSON: planned per category")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    trip: Mapped["Trip"] = relationship(back_populates="budget")
    expenses: Mapped[list["Expense"]] = relationship(back_populates="budget")


class Expense(Base):
    __tablename__ = "expenses"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    budget_id: Mapped[int] = mapped_column(ForeignKey("budgets.id"), index=True)
    amount: Mapped[float] = mapped_column(Float)
    category: Mapped[str] = mapped_column(String(50))
    note: Mapped[str | None] = mapped_column(String(200), default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    budget: Mapped["Budget"] = relationship(back_populates="expenses")

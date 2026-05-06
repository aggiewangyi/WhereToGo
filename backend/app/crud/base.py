from typing import Any, Generic, TypeVar

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import Base

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """Reusable CRUD operations for any SQLAlchemy model."""

    def __init__(self, model: type[ModelType]):
        self.model = model

    async def get(self, db: AsyncSession, id: int) -> ModelType | None:
        result = await db.execute(select(self.model).where(self.model.id == id))
        return result.scalar_one_or_none()

    async def get_multi(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 20, **filters: Any
    ) -> list[ModelType]:
        stmt = select(self.model)
        for field, value in filters.items():
            if value is not None and hasattr(self.model, field):
                stmt = stmt.where(getattr(self.model, field) == value)
        stmt = stmt.offset(skip).limit(limit)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def count(self, db: AsyncSession, **filters: Any) -> int:
        from sqlalchemy import func as sa_func

        stmt = select(sa_func.count()).select_from(self.model)
        for field, value in filters.items():
            if value is not None and hasattr(self.model, field):
                stmt = stmt.where(getattr(self.model, field) == value)
        result = await db.execute(stmt)
        return result.scalar_one()

    async def create(self, db: AsyncSession, *, obj_in: CreateSchemaType) -> ModelType:
        db_obj = self.model(**obj_in.model_dump(exclude_unset=True))
        db.add(db_obj)
        await db.flush()
        await db.refresh(db_obj)
        return db_obj

    async def update(self, db: AsyncSession, *, db_obj: ModelType, obj_in: UpdateSchemaType) -> ModelType:
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        await db.flush()
        await db.refresh(db_obj)
        return db_obj

    async def delete(self, db: AsyncSession, *, id: int) -> bool:
        obj = await self.get(db, id)
        if obj:
            await db.delete(obj)
            await db.flush()
            return True
        return False

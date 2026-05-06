from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.crud.base import CRUDBase
from app.models.user import User
from app.schemas.user import UserRegister, UserUpdate


class CRUDUser(CRUDBase[User, UserRegister, UserUpdate]):
    async def get_by_phone(self, db: AsyncSession, phone: str) -> User | None:
        result = await db.execute(select(User).where(User.phone == phone))
        return result.scalar_one_or_none()

    async def create(self, db: AsyncSession, *, obj_in: UserRegister) -> User:
        db_obj = User(
            phone=obj_in.phone,
            nickname=obj_in.nickname,
            hashed_password=hash_password(obj_in.password),
        )
        db.add(db_obj)
        await db.flush()
        await db.refresh(db_obj)
        return db_obj


crud_user = CRUDUser(User)

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.buddy import BuddyApplication, BuddyPost
from app.models.user import User
from app.schemas.buddy import BuddyPostCreate


class CRUDBuddyPost(CRUDBase[BuddyPost, BuddyPostCreate, None]):
    async def list_open(self, db: AsyncSession, *, skip: int = 0, limit: int = 20) -> list[BuddyPost]:
        stmt = select(BuddyPost).where(BuddyPost.status == "open").offset(skip).limit(limit)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def list_by_owner(
        self, db: AsyncSession, *, user_id: int, skip: int = 0, limit: int = 50
    ) -> list[BuddyPost]:
        stmt = (
            select(BuddyPost)
            .where(BuddyPost.user_id == user_id)
            .order_by(BuddyPost.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def get_for_owner(self, db: AsyncSession, post_id: int, owner_id: int) -> BuddyPost | None:
        stmt = select(BuddyPost).where(BuddyPost.id == post_id, BuddyPost.user_id == owner_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()


class CRUDBuddyApplication(CRUDBase[BuddyApplication, None, None]):
    async def apply(
        self,
        db: AsyncSession,
        post_id: int,
        applicant_id: int,
        *,
        message: str | None = None,
        self_intro: str | None = None,
    ) -> BuddyApplication:
        obj = BuddyApplication(
            post_id=post_id,
            applicant_id=applicant_id,
            message=message,
            self_intro=self_intro,
        )
        db.add(obj)
        await db.flush()
        await db.refresh(obj)
        return obj

    async def get(self, db: AsyncSession, app_id: int) -> BuddyApplication | None:
        stmt = select(BuddyApplication).where(BuddyApplication.id == app_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def has_pending(self, db: AsyncSession, post_id: int, applicant_id: int) -> bool:
        stmt = select(func.count()).select_from(BuddyApplication).where(
            BuddyApplication.post_id == post_id,
            BuddyApplication.applicant_id == applicant_id,
            BuddyApplication.status == "pending",
        )
        result = await db.execute(stmt)
        return (result.scalar() or 0) > 0

    async def count_accepted(self, db: AsyncSession, post_id: int) -> int:
        stmt = select(func.count()).select_from(BuddyApplication).where(
            BuddyApplication.post_id == post_id,
            BuddyApplication.status == "accepted",
        )
        result = await db.execute(stmt)
        return int(result.scalar() or 0)

    async def list_for_post(self, db: AsyncSession, post_id: int) -> list[tuple[BuddyApplication, str]]:
        stmt = (
            select(BuddyApplication, User.nickname)
            .join(User, User.id == BuddyApplication.applicant_id)
            .where(BuddyApplication.post_id == post_id)
            .order_by(BuddyApplication.created_at.desc())
        )
        result = await db.execute(stmt)
        return list(result.all())


crud_buddy_post = CRUDBuddyPost(BuddyPost)
crud_buddy_app = CRUDBuddyApplication(BuddyApplication)

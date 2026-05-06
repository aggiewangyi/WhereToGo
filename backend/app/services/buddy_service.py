from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.buddy import crud_buddy_app, crud_buddy_post
from app.models.buddy import BuddyApplication, BuddyPost
from app.schemas.buddy import BuddyApplicationPublisherOut, BuddyPostCreate


async def create_post(db: AsyncSession, user_id: int, data: BuddyPostCreate) -> BuddyPost:
    post = BuddyPost(
        user_id=user_id,
        destination=data.destination,
        date_start=data.date_start,
        date_end=data.date_end,
        budget_min=data.budget_min,
        budget_max=data.budget_max,
        people_wanted=data.people_wanted,
        tags=",".join(data.tags) if data.tags else None,
        description=data.description,
    )
    db.add(post)
    await db.flush()
    await db.refresh(post)
    return post


async def list_open_posts(db: AsyncSession, skip: int = 0, limit: int = 20) -> list[BuddyPost]:
    return await crud_buddy_post.list_open(db, skip=skip, limit=limit)


async def list_my_posts(db: AsyncSession, user_id: int, skip: int = 0, limit: int = 50) -> list[BuddyPost]:
    return await crud_buddy_post.list_by_owner(db, user_id=user_id, skip=skip, limit=limit)


async def apply_to_post(
    db: AsyncSession,
    post_id: int,
    applicant_id: int,
    *,
    message: str | None = None,
    self_intro: str | None = None,
) -> BuddyApplication:
    post = await crud_buddy_post.get(db, post_id)
    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="招募帖不存在")
    if post.user_id == applicant_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="不能申请自己发布的招募")
    if post.status != "open":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="该招募已不再接受申请")
    if await crud_buddy_app.has_pending(db, post_id, applicant_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="您对该帖已有待处理申请")
    return await crud_buddy_app.apply(
        db, post_id, applicant_id, message=message, self_intro=self_intro
    )


async def list_applications_for_post(
    db: AsyncSession, post_id: int, owner_id: int
) -> list[BuddyApplicationPublisherOut]:
    post = await crud_buddy_post.get_for_owner(db, post_id, owner_id)
    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="招募帖不存在或无权查看")
    rows = await crud_buddy_app.list_for_post(db, post_id)
    out: list[BuddyApplicationPublisherOut] = []
    for app, nickname in rows:
        out.append(
            BuddyApplicationPublisherOut(
                id=app.id,
                post_id=app.post_id,
                applicant_id=app.applicant_id,
                applicant_nickname=nickname,
                message=app.message,
                self_intro=app.self_intro,
                status=app.status,
                created_at=app.created_at,
            )
        )
    return out


async def review_application(
    db: AsyncSession, app_id: int, owner_id: int, *, accept: bool
) -> BuddyApplication:
    app = await crud_buddy_app.get(db, app_id)
    if app is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="申请不存在")
    post = await crud_buddy_post.get(db, app.post_id)
    if post is None or post.user_id != owner_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="只有发布者可审核申请")
    if app.status != "pending":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="该申请已处理")
    if accept:
        app.status = "accepted"
        await db.flush()
        accepted = await crud_buddy_app.count_accepted(db, app.post_id)
        if accepted >= post.people_wanted:
            post.status = "full"
    else:
        app.status = "rejected"
    await db.flush()
    await db.refresh(app)
    return app

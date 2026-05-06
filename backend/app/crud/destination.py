from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.destination import Destination


class CRUDDestination(CRUDBase[Destination, None, None]):
    async def search(
        self,
        db: AsyncSession,
        *,
        keyword: str | None = None,
        season: int | None = None,
        limit: int = 10,
    ) -> list[Destination]:
        stmt = select(Destination)
        if keyword:
            stmt = stmt.where(Destination.name.contains(keyword) | Destination.tags.contains(keyword))
        if season:
            stmt = stmt.where(Destination.best_seasons.contains(str(season)))
        stmt = stmt.limit(limit)
        result = await db.execute(stmt)
        return list(result.scalars().all())


crud_destination = CRUDDestination(Destination)

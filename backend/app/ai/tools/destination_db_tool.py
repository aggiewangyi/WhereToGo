"""LangChain tools bound to an async DB session (built per request)."""

import json

from langchain_core.tools import tool
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.destination import crud_destination


def make_search_destinations_tool(db: AsyncSession):
    @tool
    async def search_destinations_catalog(keyword: str = "", limit: int = 8) -> str:
        """从「去哪玩」站内目的地库检索：名称、国家、标签、最佳季节、日均花费、签证提示等，用于推荐与对比。"""
        kw = keyword.strip() or None
        rows = await crud_destination.search(db, keyword=kw, limit=min(limit, 24))
        if not rows:
            return "库中暂无匹配条目，可换关键词或结合联网搜索给用户建议。"
        out = []
        for r in rows:
            out.append(
                {
                    "name": r.name,
                    "country": r.country,
                    "tags": r.tags,
                    "best_seasons": r.best_seasons,
                    "avg_cost_per_day": r.avg_cost_per_day,
                    "visa_required": r.visa_required,
                    "safety_level": r.safety_level,
                }
            )
        return json.dumps(out, ensure_ascii=False)

    return search_destinations_catalog

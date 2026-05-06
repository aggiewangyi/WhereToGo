"""
小红书攻略搜索 —— 通过 302.AI 代理调用。
旅行攻略的优质 UGC 数据源。
"""

import httpx

from app.core.config import get_settings

settings = get_settings()

_HEADERS = {
    "Authorization": f"Bearer {settings.API_302_KEY}",
    "Content-Type": "application/json",
}


async def search_notes(keyword: str, *, num: int = 10) -> dict:
    """
    搜索小红书笔记。
    302.AI endpoint: POST /tools/xiaohongshu/web/search_notes
    适合搜索: 旅行攻略、穿搭建议、美食推荐、当地体验等 UGC 内容。
    """
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(
            f"{settings.API_302_BASE_URL}/tools/xiaohongshu/web/search_notes",
            headers=_HEADERS,
            json={"keyword": keyword, "num": num},
        )
        resp.raise_for_status()
        return resp.json()


async def get_note_detail(note_id: str) -> dict:
    """
    获取单篇小红书笔记详情。
    302.AI endpoint: POST /tools/xiaohongshu/web/get_note_info
    """
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(
            f"{settings.API_302_BASE_URL}/tools/xiaohongshu/web/get_note_info",
            headers=_HEADERS,
            json={"note_id": note_id},
        )
        resp.raise_for_status()
        return resp.json()

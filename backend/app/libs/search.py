"""
联网搜索服务 —— 通过 302.AI 代理调用 Tavily / Search1API / Jina。
"""

import httpx

from app.core.config import get_settings

settings = get_settings()

_HEADERS = {
    "Authorization": f"Bearer {settings.API_302_KEY}",
    "Content-Type": "application/json",
}


async def tavily_search(query: str, *, max_results: int = 5, search_depth: str = "basic") -> dict:
    """
    Tavily Search —— 专为 LLM 优化的搜索引擎。
    302.AI endpoint: POST /tavily/search
    价格: 0.01 PTC/次
    """
    body = {
        "query": query,
        "search_depth": search_depth,
        "max_results": max_results,
    }
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(
            f"{settings.API_302_BASE_URL}/tavily/search",
            headers=_HEADERS,
            json=body,
        )
        resp.raise_for_status()
        return resp.json()


async def search1api_search(
    query: str,
    *,
    max_results: int = 5,
    search_service: str = "google",
    crawl_results: int = 0,
) -> dict:
    """
    Search1API —— 低成本搜索。
    302.AI endpoint: POST /search1api/search
    价格: 0.001 PTC/次
    """
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(
            f"{settings.API_302_BASE_URL}/search1api/search",
            headers=_HEADERS,
            json={
                "query": query,
                "search_service": search_service,
                "max_results": max_results,
                "crawl_results": crawl_results,
            },
        )
        resp.raise_for_status()
        return resp.json()


async def jina_search(query: str) -> dict:
    """
    Jina Search —— 返回干净的 LLM 友好文本。
    302.AI endpoint: GET /jina/search/{query}
    价格: 0.02 PTC / 1M Token
    """
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(
            f"{settings.API_302_BASE_URL}/jina/search/{query}",
            headers=_HEADERS,
        )
        resp.raise_for_status()
        return resp.json()


async def jina_reader(url: str) -> dict:
    """
    Jina Reader —— 将网页转为 LLM 可读的纯文本。
    302.AI endpoint: GET /jina/reader/{website}
    """
    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.get(
            f"{settings.API_302_BASE_URL}/jina/reader/{url}",
            headers=_HEADERS,
        )
        resp.raise_for_status()
        return resp.json()


# ---- Convenience wrappers (used by AI tools) ----

async def web_search(query: str, *, num_results: int = 5) -> list[dict]:
    """统一入口: 默认用 Tavily，降级到 Search1API。"""
    try:
        data = await tavily_search(query, max_results=num_results)
        return data.get("results", [])
    except Exception:
        try:
            data = await search1api_search(query, max_results=num_results)
            return data.get("results", [])
        except Exception:
            return []


async def news_search(query: str, *, num_results: int = 5) -> list[dict]:
    """新闻搜索 —— 通过 Search1API 的 news 端点。"""
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                f"{settings.API_302_BASE_URL}/search1api/news",
                headers=_HEADERS,
                json={"query": query, "max_results": num_results},
            )
            resp.raise_for_status()
            return resp.json().get("results", [])
    except Exception:
        return []

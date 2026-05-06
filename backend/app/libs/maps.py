import httpx

from app.core.config import get_settings

settings = get_settings()

AMAP_BASE = "https://restapi.amap.com/v3"


async def geocode(address: str) -> dict:
    """地理编码: 地址 → 经纬度"""
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            f"{AMAP_BASE}/geocode/geo",
            params={"address": address, "key": settings.AMAP_API_KEY},
        )
        resp.raise_for_status()
        return resp.json()


async def route_planning(origin: str, destination: str, mode: str = "transit") -> dict:
    """
    路线规划
    mode: driving / transit / walking / bicycling
    origin/destination: "lng,lat"
    """
    endpoint = f"{AMAP_BASE}/direction/{mode}"
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            endpoint,
            params={"origin": origin, "destination": destination, "key": settings.AMAP_API_KEY},
        )
        resp.raise_for_status()
        return resp.json()


async def nearby_search(location: str, keyword: str = "餐厅", radius: int = 3000) -> dict:
    """周边搜索 (POI)"""
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            f"{AMAP_BASE}/place/around",
            params={
                "location": location,
                "keywords": keyword,
                "radius": radius,
                "key": settings.AMAP_API_KEY,
            },
        )
        resp.raise_for_status()
        return resp.json()

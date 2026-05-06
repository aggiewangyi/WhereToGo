import httpx

from app.core.config import get_settings

settings = get_settings()

BASE_URL = "https://devapi.qweather.com/v7"


async def get_forecast(city: str, days: int = 7) -> dict:
    """获取未来 N 天天气预报 (和风天气 API)"""
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            f"{BASE_URL}/weather/{days}d",
            params={"location": city, "key": settings.WEATHER_API_KEY},
        )
        resp.raise_for_status()
        return resp.json()


async def get_current_weather(city: str) -> dict:
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            f"{BASE_URL}/weather/now",
            params={"location": city, "key": settings.WEATHER_API_KEY},
        )
        resp.raise_for_status()
        return resp.json()

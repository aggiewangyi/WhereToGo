import logging

from langchain_core.tools import tool

from app.libs.weather import get_current_weather, get_forecast

logger = logging.getLogger(__name__)


@tool
async def check_weather(city: str, days: int = 7) -> str:
    """查询目的地未来天气预报，用于行程规划和穿搭建议。"""
    try:
        data = await get_forecast(city, days)
        return str(data)
    except Exception as e:
        logger.warning("check_weather failed city=%s: %s", city, e)
        return (
            "天气接口暂不可用，无实时预报数据。"
            "请结合季节与目的地常识给用户建议，并提示以当地当日预报为准。"
        )


@tool
async def check_current_weather(city: str) -> str:
    """查询目的地当前天气。"""
    try:
        data = await get_current_weather(city)
        return str(data)
    except Exception as e:
        logger.warning("check_current_weather failed city=%s: %s", city, e)
        return (
            "当前天气接口暂不可用。"
            "请结合常识作答，并建议用户出发前查看实时天气。"
        )

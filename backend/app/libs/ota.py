"""
OTA (Online Travel Agency) 接口封装。
对接携程 / 飞猪 / 12306 等票务平台。
生产环境需替换为真实 API。
"""

from datetime import date


async def search_flights(
    origin: str,
    destination: str,
    departure_date: date,
    passengers: int = 1,
) -> list[dict]:
    """查询航班信息"""
    # TODO: integrate real OTA API
    return []


async def search_trains(
    origin: str,
    destination: str,
    departure_date: date,
) -> list[dict]:
    """查询火车票"""
    return []


async def search_hotels(
    city: str,
    checkin: date,
    checkout: date,
    guests: int = 2,
) -> list[dict]:
    """查询酒店"""
    return []


async def get_price_calendar(
    origin: str,
    destination: str,
    month: str,
    transport_type: str = "flight",
) -> dict:
    """获取指定月份的价格日历"""
    return {}

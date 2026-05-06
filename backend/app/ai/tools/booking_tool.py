from datetime import date

from langchain_core.tools import tool

from app.libs.ota import search_flights, search_hotels, search_trains


@tool
async def search_flight_tickets(origin: str, destination: str, departure_date: str, passengers: int = 1) -> str:
    """搜索两地之间的航班信息，返回价格、时间、航司等。departure_date 格式 YYYY-MM-DD。"""
    results = await search_flights(origin, destination, date.fromisoformat(departure_date), passengers)
    return str(results) if results else "暂无航班数据，请稍后重试或更换日期。"


@tool
async def search_train_tickets(origin: str, destination: str, departure_date: str) -> str:
    """搜索火车/高铁票。departure_date 格式 YYYY-MM-DD。"""
    results = await search_trains(origin, destination, date.fromisoformat(departure_date))
    return str(results) if results else "暂无火车票数据。"


@tool
async def search_hotel_options(city: str, checkin: str, checkout: str, guests: int = 2) -> str:
    """搜索酒店。日期格式 YYYY-MM-DD。"""
    results = await search_hotels(city, date.fromisoformat(checkin), date.fromisoformat(checkout), guests)
    return str(results) if results else "暂无酒店数据。"

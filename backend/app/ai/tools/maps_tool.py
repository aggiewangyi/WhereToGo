from langchain_core.tools import tool

from app.libs.maps import geocode, nearby_search, route_planning


@tool
async def get_location(address: str) -> str:
    """将地址转换为经纬度坐标。"""
    data = await geocode(address)
    return str(data)


@tool
async def plan_route(origin: str, destination: str, mode: str = "transit") -> str:
    """规划两点之间的路线。origin/destination 为 'lng,lat' 格式，mode 可选 driving/transit/walking。"""
    data = await route_planning(origin, destination, mode)
    return str(data)


@tool
async def search_nearby(location: str, keyword: str = "餐厅", radius: int = 3000) -> str:
    """搜索指定位置周边的 POI（餐厅/景点/ATM 等）。location 为 'lng,lat' 格式。"""
    data = await nearby_search(location, keyword, radius)
    return str(data)

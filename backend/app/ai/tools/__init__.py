from app.ai.tools.booking_tool import search_flight_tickets, search_hotel_options, search_train_tickets
from app.ai.tools.maps_tool import get_location, plan_route, search_nearby
from app.ai.tools.search_tool import news_search_tool, search_travel_notes, web_search_tool
from app.ai.tools.translate_tool import translate
from app.ai.tools.weather_tool import check_current_weather, check_weather

ALL_TOOLS = [
    # 联网搜索 (302.AI → Tavily / Search1API)
    web_search_tool,
    news_search_tool,
    # 小红书攻略 (302.AI → 小红书)
    search_travel_notes,
    # 翻译 (302.AI → DeepL)
    translate,
    # 天气
    check_weather,
    check_current_weather,
    # 票务 (OTA)
    search_flight_tickets,
    search_train_tickets,
    search_hotel_options,
    # 地图 (高德)
    get_location,
    plan_route,
    search_nearby,
]

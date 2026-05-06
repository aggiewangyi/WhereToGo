"""
MCP (Model Context Protocol) Server Hub.
Registers tool servers that external LLM clients can discover and invoke.
All external API calls are proxied through 302.AI.
"""

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from app.libs import maps, ota, search, translate, weather, xiaohongshu

mcp_app = Server("wheretogo-mcp")


@mcp_app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="web_search",
            description="联网搜索实时信息 (via 302.AI → Tavily)",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "搜索关键词"},
                    "num_results": {"type": "integer", "default": 5},
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="search_xiaohongshu",
            description="搜索小红书旅行笔记 (via 302.AI)",
            inputSchema={
                "type": "object",
                "properties": {
                    "keyword": {"type": "string", "description": "搜索关键词，如'厦门攻略'"},
                    "num": {"type": "integer", "default": 5},
                },
                "required": ["keyword"],
            },
        ),
        Tool(
            name="translate_text",
            description="文本翻译 (via 302.AI → DeepL)",
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                    "target_lang": {"type": "string", "default": "EN"},
                },
                "required": ["text", "target_lang"],
            },
        ),
        Tool(
            name="get_weather_forecast",
            description="获取目的地未来天气预报",
            inputSchema={
                "type": "object",
                "properties": {
                    "city": {"type": "string"},
                    "days": {"type": "integer", "default": 7},
                },
                "required": ["city"],
            },
        ),
        Tool(
            name="search_flights",
            description="搜索航班",
            inputSchema={
                "type": "object",
                "properties": {
                    "origin": {"type": "string"},
                    "destination": {"type": "string"},
                    "departure_date": {"type": "string", "description": "YYYY-MM-DD"},
                    "passengers": {"type": "integer", "default": 1},
                },
                "required": ["origin", "destination", "departure_date"],
            },
        ),
        Tool(
            name="geocode",
            description="地理编码: 地址转经纬度",
            inputSchema={
                "type": "object",
                "properties": {"address": {"type": "string"}},
                "required": ["address"],
            },
        ),
    ]


@mcp_app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    match name:
        case "web_search":
            result = await search.web_search(arguments["query"], num_results=arguments.get("num_results", 5))
        case "search_xiaohongshu":
            result = await xiaohongshu.search_notes(arguments["keyword"], num=arguments.get("num", 5))
        case "translate_text":
            result = await translate.translate_text(arguments["text"], target_lang=arguments["target_lang"])
        case "get_weather_forecast":
            result = await weather.get_forecast(arguments["city"], arguments.get("days", 7))
        case "search_flights":
            from datetime import date
            result = await ota.search_flights(
                arguments["origin"],
                arguments["destination"],
                date.fromisoformat(arguments["departure_date"]),
                arguments.get("passengers", 1),
            )
        case "geocode":
            result = await maps.geocode(arguments["address"])
        case _:
            result = {"error": f"Unknown tool: {name}"}

    return [TextContent(type="text", text=str(result))]


async def run_mcp_server():
    """Start the MCP server over stdio (for CLI / external agent integration)."""
    async with stdio_server() as (read_stream, write_stream):
        await mcp_app.run(read_stream, write_stream)

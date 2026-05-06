from langchain_core.tools import tool

from app.libs.search import news_search, tavily_search, web_search
from app.libs.xiaohongshu import search_notes


@tool
async def web_search_tool(query: str, num_results: int = 5) -> str:
    """联网搜索实时信息，如目的地攻略、签证政策、安全提醒、景点开放状态等。"""
    results = await web_search(query, num_results=num_results)
    if not results:
        return "暂无搜索结果。"
    lines = []
    for r in results[:num_results]:
        title = r.get("title", "")
        content = r.get("content", r.get("snippet", ""))[:300]
        url = r.get("url", r.get("link", ""))
        lines.append(f"- {title}\n  {content}\n  来源: {url}")
    return "\n\n".join(lines)


@tool
async def news_search_tool(query: str, num_results: int = 5) -> str:
    """搜索新闻资讯，用于获取安全预警、自然灾害、旅行政策变化等时效性信息。"""
    results = await news_search(query, num_results=num_results)
    if not results:
        return "暂无相关新闻。"
    lines = []
    for r in results[:num_results]:
        lines.append(f"- {r.get('title', '')}: {r.get('snippet', '')[:200]}")
    return "\n".join(lines)


@tool
async def search_travel_notes(keyword: str, num: int = 5) -> str:
    """搜索小红书旅行笔记，获取真实用户的攻略、穿搭推荐、美食推荐、避坑指南等 UGC 内容。"""
    try:
        data = await search_notes(keyword, num=num)
        notes = data.get("data", data.get("notes", []))
        if not notes:
            return f"未找到关于「{keyword}」的小红书笔记。"
        lines = []
        for note in notes[:num]:
            title = note.get("title", note.get("display_title", ""))
            desc = note.get("desc", note.get("note_card", {}).get("desc", ""))[:200]
            likes = note.get("liked_count", note.get("interact_info", {}).get("liked_count", ""))
            lines.append(f"- {title} (赞{likes})\n  {desc}")
        return "\n\n".join(lines)
    except Exception as e:
        return f"小红书搜索失败: {e}"

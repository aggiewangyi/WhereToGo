"""多智能体对话编排：极致 LangGraph（检查点 + interrupt + Command）。"""

from __future__ import annotations

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.multi_agent.langgraph_engine import stream_langgraph_travel_chat
from app.ai.multi_agent.memory_prompt import (
    QUIET_MODE_BLOCK,
    VERBOSE_MODE_BLOCK,
    format_travel_memory_system_block,
)
from app.ai.schemas.persistent_travel_memory import PersistentTravelMemory
from app.ai.tools.booking_tool import search_flight_tickets, search_hotel_options, search_train_tickets
from app.ai.tools.destination_db_tool import make_search_destinations_tool
from app.ai.tools.maps_tool import get_location, plan_route, search_nearby
from app.ai.tools.search_tool import news_search_tool, search_travel_notes, web_search_tool
from app.ai.tools.translate_tool import translate
from app.ai.tools.tool_timeout import wrap_tools_with_timeout
from app.ai.tools.weather_tool import check_current_weather, check_weather
from app.core.config import get_settings
from app.crud import chat as chat_crud
from app.crud.travel_memory import get_persistent_travel_memory

settings = get_settings()


async def _effective_interaction_mode(
    db: AsyncSession,
    session_id: str | None,
    request_mode: str | None,
    mem: PersistentTravelMemory,
) -> str:
    if request_mode in ("verbose", "quiet"):
        return request_mode
    if session_id:
        row = await chat_crud.get_session_interaction_mode(db, session_id)
        if row in ("verbose", "quiet"):
            return row
    if mem.default_interaction_mode in ("verbose", "quiet"):
        return mem.default_interaction_mode
    return "quiet"


async def multi_agent_completion(
    message: str,
    history: list[BaseMessage] | None,
    db: AsyncSession,
    session_id: str | None = None,
    *,
    user_id: int | None = None,
    interaction_mode: str | None = None,
):
    """
    Yields: text | tool_start | tool_end | phase | interrupt | error | done
    """
    prior = list(history or [])

    mem = PersistentTravelMemory()
    if user_id is not None:
        mem = await get_persistent_travel_memory(db, user_id)

    eff_mode = await _effective_interaction_mode(db, session_id, interaction_mode, mem)

    sys_parts: list[str] = []
    mb = format_travel_memory_system_block(mem)
    if mb:
        sys_parts.append(mb)
    sys_parts.append(VERBOSE_MODE_BLOCK if eff_mode == "verbose" else QUIET_MODE_BLOCK)
    messages: list[BaseMessage] = [SystemMessage(content="\n\n".join(sys_parts)), *prior, HumanMessage(content=message)]

    _to = float(settings.AGENT_TOOL_TIMEOUT_SEC)
    prep_tools = wrap_tools_with_timeout(
        [
            web_search_tool,
            # news_search_tool,
            # search_travel_notes,
            # translate,
            # check_weather,
            # check_current_weather,
        ],
        _to,
    )

    if session_id:
        await chat_crud.clear_pending_prep_payload(db, session_id)

    dest_tool = make_search_destinations_tool(db)
    intent_tools = wrap_tools_with_timeout(
        [
            # dest_tool,
            web_search_tool,
            # news_search_tool,
            # search_travel_notes,
            # check_weather,
            # check_current_weather,
            # translate,
        ],
        _to,
    )
    planner_tools = wrap_tools_with_timeout(
        [
            # get_location,
            # plan_route,
            # search_nearby,
            web_search_tool,
            # search_travel_notes,
            # check_weather,
            # check_current_weather,
            # search_flight_tickets,
            # search_train_tickets,
            # search_hotel_options,
        ],
        _to,
    )

    async for ev in stream_langgraph_travel_chat(
        db=db,
        session_id=session_id,
        user_message=message,
        messages_for_model=messages,
        intent_tools=intent_tools,
        planner_tools=planner_tools,
        prep_tools=prep_tools,
        interaction_mode=eff_mode,
        get_tid=chat_crud.get_langgraph_thread_id,
        set_tid=chat_crud.set_langgraph_thread_id,
        clear_tid=chat_crud.clear_langgraph_thread_id,
    ):
        yield ev

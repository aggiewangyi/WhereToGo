"""
极致 LangGraph：检查点（SqliteSaver / MemorySaver）+ interrupt / Command(resume)，
单张 StateGraph：intent → inject_profile → planner → human_gate → prep_context → prep。
"""

from __future__ import annotations

import json
import logging
import uuid
from pathlib import Path
from typing import Annotated, Any, Literal, TypedDict

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import create_react_agent
from langgraph.types import Command, interrupt
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.llm_client import build_llm
from app.ai.prompts.multi_agent import (
    INTENT_AGENT_SYSTEM,
    PLANNER_AGENT_SYSTEM,
    PREP_AGENT_SYSTEM,
    PROFILE_EXTRACT_SYSTEM,
)
from app.ai.schemas.travel_profile import TravelProfile
from app.ai.streaming_utils import llm_text_pieces_for_sse, safe_tool_output_preview
from app.core.config import get_settings
from app.ai.multi_agent.prep_handoff import (
    human_message_for_ab_choice_reply,
    user_cancels_prep_pending,
    user_confirms_itinerary_for_prep,
    user_replies_planner_ab_choice,
)
from app.ai.multi_agent.profile_merge import (
    extract_locked_destination,
    merge_travel_profile_from_text,
)

logger = logging.getLogger(__name__)
settings = get_settings()

_AFTER_PLANNER_HINT = (
    "\n\n---\n*若对行程草案满意，请回复 **「确认」** 或 **「可以」**，"
    "我将自动为您生成 **行前打包清单**。"
    "如需 **完整 Markdown 行程单**，可说明「导出行程单」。"
    "若不满意，请直接说明要改的点。*\n"
)


def _merge_optional_dict(old: dict | None, new: dict | None) -> dict | None:
    return new if new is not None else old


def _merge_optional_int(old: int | None, new: int | None) -> int | None:
    return new if new is not None else old


class TravelGraphState(TypedDict, total=False):
    messages: Annotated[list[BaseMessage], add_messages]
    profile_dict: Annotated[dict | None, _merge_optional_dict]
    plan_days: Annotated[int | None, _merge_optional_int]


_cp_singleton: Any | None = None


def get_travel_checkpointer() -> Any:
    global _cp_singleton
    if _cp_singleton is not None:
        return _cp_singleton
    path = (getattr(settings, "LANGGRAPH_SQLITE_PATH", None) or "").strip()
    if path:
        try:
            from langgraph.checkpoint.sqlite import SqliteSaver

            Path(path).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)
            _cp_singleton = SqliteSaver.from_conn_string(path)
            logger.info("LangGraph checkpointer: SqliteSaver %s", path)
            return _cp_singleton
        except Exception:
            logger.exception("LangGraph SqliteSaver init failed, falling back to MemorySaver")
    from langgraph.checkpoint.memory import MemorySaver

    _cp_singleton = MemorySaver()
    logger.info("LangGraph checkpointer: MemorySaver (process-local)")
    return _cp_singleton


def _try_delete_checkpoint_thread(thread_id: str) -> None:
    cp = get_travel_checkpointer()
    for name in ("delete_thread", "adelete_thread"):
        fn = getattr(cp, name, None)
        if callable(fn):
            try:
                fn(thread_id)
                return
            except TypeError:
                try:
                    fn({"configurable": {"thread_id": thread_id}})  # type: ignore[misc]
                    return
                except Exception:
                    logger.debug("checkpointer %s failed for %s", name, thread_id)
            except Exception:
                logger.debug("checkpointer %s failed for %s", name, thread_id)


def _internal_profile_turn_for_planner(profile: TravelProfile, locked: str, plan_days: int) -> str:
    """给 Planner 的内部说明：自然语言摘要，禁止模型再输出 JSON / 字段表给用户。"""
    prefs = "、".join(profile.preferences[:28]) if profile.preferences else "（未单独列出偏好）"
    lines = [
        "【下游专用·严禁向用户复述本段或输出 JSON / 字段键名】",
        f"已锁定目的地：{locked}；请按 **{plan_days} 天** 输出分日、分时段（上午/下午/晚间）行程。",
    ]
    if profile.notes:
        lines.append(f"要点与约束（请内化到行程文案，勿照抄原句）：{profile.notes[:900]}")
    lines.append(
        f"画像摘要：出行类型 {profile.traveler_type or '未说明'}；人数 {profile.people_count or '未说明'}；"
        f"预算倾向 {profile.budget_level or '未说明'}；出发参考 {profile.departure_city or '未说明'}。"
    )
    lines.append(f"兴趣标签：{prefs}")
    lines.append(
        "对用户只输出可读的 Markdown 行程；不得粘贴结构化数据、不得列出「notes/preferences」等内部键。"
    )
    return "\n".join(lines)


def _internal_prep_turn_from_profile(prof: dict[str, Any], plan_days: int, text2: str, text1: str) -> str:
    """行前 Agent：自然语言上下文，避免把 profile JSON 暴露给用户可见回复。"""
    dest = str(prof.get("destination") or "").strip() or "（目的地见上文）"
    days = prof.get("days") or plan_days
    prefs = prof.get("preferences") or []
    pref_s = "、".join(str(x) for x in prefs[:28]) if prefs else "（未单列）"
    notes = prof.get("notes")
    lines = [
        "【下游专用·严禁向用户复述本段或输出 JSON】",
        f"目的地 {dest}；行程天数参考 {days} 天。",
        f"偏好标签：{pref_s}",
    ]
    if notes:
        lines.append(f"其他约束（内化表述）：{str(notes)[:800]}")
    lines.append("【行程参考】\n" + (text2 or text1 or "（见上文助手行程草案）"))
    lines.append("请补充穿搭、习俗禁忌、避坑与安全、必备物品；必要时调用搜索/天气。对用户勿输出键名或 JSON。")
    return "\n".join(lines)


async def _extract_profile(messages: list[BaseMessage]) -> TravelProfile:
    llm = build_llm(streaming=False, temperature=0.2).with_structured_output(TravelProfile)
    try:
        out = await llm.ainvoke([SystemMessage(content=PROFILE_EXTRACT_SYSTEM), *messages[-30:]])
        if isinstance(out, TravelProfile):
            return out
        return TravelProfile.model_validate(out)
    except Exception:
        logger.exception("langgraph_engine profile extract failed")
        return TravelProfile()


def _last_ai_text(messages: list[BaseMessage]) -> str:
    for msg in reversed(messages):
        if isinstance(msg, AIMessage):
            c = msg.content
            if isinstance(c, str):
                return c
            if isinstance(c, list):
                parts: list[str] = []
                for p in c:
                    if isinstance(p, dict) and p.get("type") == "text":
                        parts.append(str(p.get("text", "")))
                return "".join(parts)
    return ""


def _history_has_destination_lock(messages: list[BaseMessage]) -> bool:
    """任一轮助手回复中含正式「目的地锁定为【x】」即视为已 handoff（不限于最后一条）。"""
    for msg in reversed(messages):
        if not isinstance(msg, AIMessage):
            continue
        c = msg.content
        blob = ""
        if isinstance(c, str):
            blob = c
        elif isinstance(c, list):
            parts: list[str] = []
            for p in c:
                if isinstance(p, dict) and p.get("type") == "text":
                    parts.append(str(p.get("text", "")))
            blob = "".join(parts)
        if blob and extract_locked_destination(blob):
            return True
    return False


def _stream_is_planner_to_prep_handoff(resume_cmd: Command | None) -> bool:
    """planner→prep：仅在检查点存在 interrupt 且用户本轮明确确认时，入口为 Command(resume=True)。"""
    if resume_cmd is None:
        return False
    return getattr(resume_cmd, "resume", None) is True


def _stream_resumes_planner_via_ab_pick(resume_cmd: Command | None) -> bool:
    """human_gate 挂起时用户回 A/B，以 Command(resume=原文) 续跑并回到 planner。"""
    if resume_cmd is None:
        return False
    r = getattr(resume_cmd, "resume", None)
    if r is True or r is False:
        return False
    return user_replies_planner_ab_choice(str(r))


def _interrupts_pending(intr: Any) -> bool:
    """LangGraph StateSnapshot.interrupts 可能是 dict/list，避免把空结构当 True。"""
    if intr is None:
        return False
    if isinstance(intr, dict):
        for v in intr.values():
            if isinstance(v, (list, tuple)):
                if len(v) > 0:
                    return True
            elif v:
                return True
        return False
    if isinstance(intr, (list, tuple)):
        return len(intr) > 0
    return bool(intr)


def _snap_expects_itinerary_prep_confirm(snap: Any) -> bool:
    """检查点是否真停在「行程草案 → human_gate」：有 profile、且桥接后已有 Planner 的 AI 输出。"""
    vals = getattr(snap, "values", None)
    if not isinstance(vals, dict):
        return False
    prof = vals.get("profile_dict")
    if not isinstance(prof, dict) or not str(prof.get("destination") or "").strip():
        return False
    msgs = list(vals.get("messages") or [])
    seen_bridge = False
    for m in msgs:
        if isinstance(m, HumanMessage) and "【下游专用" in (m.content or ""):
            seen_bridge = True
            continue
        if isinstance(m, AIMessage) and seen_bridge:
            if _last_ai_text([m]).strip():
                return True
    return False


def _route_after_intent(state: TravelGraphState) -> Literal["inject_profile", "__end__"]:
    text1 = _last_ai_text(state.get("messages") or [])
    if extract_locked_destination(text1):
        return "inject_profile"
    return "__end__"


def build_travel_graph(
    *,
    intent_tools: list,
    planner_tools: list,
    prep_tools: list,
    interaction_mode: str,
):
    # 确定目的地agent
    intent_agent = create_react_agent(build_llm(), intent_tools, prompt=INTENT_AGENT_SYSTEM)
    # 指定旅行计划agent
    planner_agent = create_react_agent(build_llm(), planner_tools, prompt=PLANNER_AGENT_SYSTEM)
    # 管家agent（安排行程所需所知所想）
    prep_agent = create_react_agent(build_llm(), prep_tools, prompt=PREP_AGENT_SYSTEM)

    async def inject_profile(state: TravelGraphState) -> dict[str, Any]:
        msgs = list(state.get("messages") or [])
        text1 = _last_ai_text(msgs)
        locked = extract_locked_destination(text1)
        if not locked:
            return {}
        msgs_after_1 = msgs + [AIMessage(content=text1 or "（无文本回复）")]
        profile = await _extract_profile(msgs_after_1)
        profile = merge_travel_profile_from_text(profile, text1)
        profile = profile.model_copy(update={"destination": locked})
        plan_days = profile.days if profile.days is not None else 3
        bridge_body = _internal_profile_turn_for_planner(profile, locked, plan_days)
        if profile.days is None:
            bridge_body += (
                f"\n\n（本轮规划天数默认 **{plan_days} 天**；用户未说明天数时，"
                "请在行程文首注明可按实际天数调整。）"
            )
        bridge = HumanMessage(content=bridge_body)
        return {
            "messages": [bridge],
            "profile_dict": profile.model_dump(),
            "plan_days": plan_days,
        }

    # 人机交互门，决定是否继续执行行程规划
    def human_gate(state: TravelGraphState) -> Command:
        resume = interrupt({"kind": "confirm_prep", "hint": _AFTER_PLANNER_HINT})
        if resume is False:
            return Command(goto=END)
        s = str(resume).strip() if resume is not None else ""
        if user_cancels_prep_pending(s):
            return Command(goto=END)
        if user_replies_planner_ab_choice(s):
            body = human_message_for_ab_choice_reply(s)
            return Command(
                goto="planner",
                update={"messages": [HumanMessage(content=body)]},
            )
        if resume is True or user_confirms_itinerary_for_prep(s):
            return Command(goto="prep_context")
        return Command(goto=END)

    async def prep_context(state: TravelGraphState) -> dict[str, Any]:
        prof = state.get("profile_dict") or {}
        plan_days = int(state.get("plan_days") or 3)
        msgs = list(state.get("messages") or [])
        text1 = ""
        text2 = ""
        seen_bridge = False
        for m in msgs:
            if isinstance(m, HumanMessage) and "【下游专用" in (m.content or ""):
                seen_bridge = True
                continue
            if isinstance(m, AIMessage):
                body = _last_ai_text([m])
                if seen_bridge:
                    text2 = body
                else:
                    text1 = body
        if not text2:
            text2 = _last_ai_text(msgs)
        prep_body = _internal_prep_turn_from_profile(dict(prof), plan_days, text2, text1)
        prep_human = HumanMessage(content=prep_body)
        return {"messages": [prep_human]}

    # 构建状态图
    g = StateGraph(TravelGraphState)
    g.add_node("intent", intent_agent)
    g.add_node("inject_profile", inject_profile)
    g.add_node("planner", planner_agent)
    g.add_node("human_gate", human_gate)
    g.add_node("prep_context", prep_context)
    g.add_node("prep", prep_agent)

    g.add_edge(START, "intent")
    g.add_conditional_edges(
        "intent",
        _route_after_intent,
        {"inject_profile": "inject_profile", "__end__": END},
    )
    g.add_edge("inject_profile", "planner")
    g.add_edge("planner", "human_gate")
    g.add_edge("prep_context", "prep")
    g.add_edge("prep", END)

    return g.compile(checkpointer=get_travel_checkpointer())


def _phase_from_event(event: dict[str, Any]) -> str:
    name = str(event.get("name") or "").lower()
    tags = [str(t).lower() for t in (event.get("tags") or [])]
    blob = name + " ".join(tags)
    if "prep" in blob:
        return "prep"
    if "planner" in blob or "inject" in blob:
        return "planner"
    return "intent"


async def stream_langgraph_travel_chat(
    *,
    db: AsyncSession | None,
    session_id: str | None,
    user_message: str,
    messages_for_model: list[BaseMessage],
    intent_tools: list,
    planner_tools: list,
    prep_tools: list,
    interaction_mode: str,
    get_tid,
    set_tid,
    clear_tid,
):
    """
    get_tid/set_tid/clear_tid: async (db, sid) -> Optional coroutines for CRUD；无 session 时传 no-op。
    """
    graph = build_travel_graph(
        intent_tools=intent_tools,
        planner_tools=planner_tools,
        prep_tools=prep_tools,
        interaction_mode=interaction_mode,
    )

    tid: str | None = None
    if session_id and db is not None:
        tid = await get_tid(db, session_id)

    resume_cmd: Command | None = None
    fresh: dict[str, Any] | None = None

    if tid and session_id and db is not None:
        config = {"configurable": {"thread_id": tid}}
        try:
            snap = await graph.aget_state(config)
        except Exception:
            logger.exception("aget_state failed")
            snap = None
        intr = getattr(snap, "interrupts", None) if snap else None
        pending_prep = _interrupts_pending(intr) and _snap_expects_itinerary_prep_confirm(snap)
        if pending_prep:
            if user_confirms_itinerary_for_prep(user_message):
                resume_cmd = Command(resume=True)
            elif user_cancels_prep_pending(user_message):
                resume_cmd = Command(resume=False)
            elif user_replies_planner_ab_choice(user_message):
                resume_cmd = Command(resume=user_message.strip())
            else:
                yield (
                    "text",
                    "\n\n当前正在等待您对 **行程草案** 的确认。"
                    "请回复 **「确认」** / **「可以」**，或 **「取消」「重来」** 放弃草案。\n",
                )
                yield ("done", None)
                return
        else:
            if _interrupts_pending(intr) and snap is not None:
                logger.warning(
                    "langgraph thread %s has interrupts but state is not a prep-confirm pause; resetting",
                    tid,
                )
            _try_delete_checkpoint_thread(tid)
            tid = str(uuid.uuid4())
            await set_tid(db, session_id, tid)
            await db.flush()
            fresh = {"messages": messages_for_model}
    else:
        tid = str(uuid.uuid4())
        if session_id and db is not None:
            await set_tid(db, session_id, tid)
            await db.flush()
        fresh = {"messages": messages_for_model}

    assert tid is not None
    config = {"configurable": {"thread_id": tid}}
    stream_input: Any = resume_cmd if resume_cmd is not None else fresh

    # 首轮才强调「意图识别」；若历史中已有正式锁定句，说明已进入过 handoff，
    # 本轮多为追问/改行程——避免前端仍闪「意图识别」造成误解。
    # 若本轮为 Command(resume=True) 续跑 human_gate，则为 planner→prep 正式移交，勿闪意图/行程编排。
    if _stream_is_planner_to_prep_handoff(resume_cmd):
        yield ("phase", {"name": "handoff_prep", "label": "正在 · 根据确认移交行前管家…"})
        _phase_cursor = "prep"
    elif _stream_resumes_planner_via_ab_pick(resume_cmd):
        yield ("phase", {"name": "planner", "label": "正在 · 行程规划编排（按你的选项收紧）"})
        _phase_cursor = "planner"
    elif resume_cmd is not None and getattr(resume_cmd, "resume", None) is False:
        yield ("phase", {"name": "followup", "label": "正在 · 根据您的选择结束草案…"})
        _phase_cursor = "intent"
    elif _history_has_destination_lock(messages_for_model):
        yield ("phase", {"name": "followup", "label": "正在 · 基于已锁定目的地继续编排…"})
        _phase_cursor = "intent"
    else:
        yield ("phase", {"name": "intent", "label": "正在 · 意图识别与推荐"})
        _phase_cursor = "intent"

    try:
        async for event in graph.astream_events(
            stream_input,
            config=config,
            version="v2",
            subgraphs=True,
        ):
            et = event.get("event")
            if et == "on_chain_start":
                nm = str(event.get("name") or "").lower()
                tags = [str(t).lower() for t in (event.get("tags") or [])]
                blob = nm + " " + " ".join(tags)
                if "inject_profile" in blob:
                    yield ("phase", {"name": "handoff_profile", "label": "正在整合需求并移交行程规划…"})
                elif "prep_context" in blob:
                    yield ("phase", {"name": "handoff_prep", "label": "正在汇总行程并移交行前顾问…"})
            phase = _phase_from_event(event)
            if phase != _phase_cursor and phase == "planner":
                yield ("phase", {"name": "planner", "label": "正在 · 行程规划编排"})
                _phase_cursor = "planner"
            if phase != _phase_cursor and phase == "prep":
                yield ("phase", {"name": "prep", "label": "正在 · 行前建议与打包清单"})
                _phase_cursor = "prep"

            for piece in llm_text_pieces_for_sse(et, event, stream_llm=settings.CHAT_STREAM_LLM):
                if piece:
                    yield ("text", piece)

            if et == "on_tool_start":
                d = event.get("data") or {}
                name = event.get("name") or d.get("name") or ""
                yield ("tool_start", {"name": name, "input": d.get("input"), "phase": phase})
            elif et == "on_tool_end":
                d = event.get("data") or {}
                name = event.get("name") or d.get("name") or ""
                out = d.get("output")
                yield ("tool_end", {"name": name, "output": safe_tool_output_preview(out), "phase": phase})

    except Exception:
        logger.exception("LangGraph astream_events failed")
        yield ("error", {"message": "旅行智能规划Agent暂时不可用，请稍后重试。"})
        yield ("done", None)
        return

    try:
        sn_post = await graph.aget_state(config)
        intr_post = getattr(sn_post, "interrupts", None) if sn_post else None
        if _interrupts_pending(intr_post) and _snap_expects_itinerary_prep_confirm(sn_post):
            yield ("interrupt", {"payload": {"kind": "confirm_prep", "hint": _AFTER_PLANNER_HINT}})
    except Exception:
        logger.debug("post-stream interrupt probe failed", exc_info=True)

    if session_id and db is not None:
        try:
            snap = await graph.aget_state(config)
            intr = getattr(snap, "interrupts", None)
            if not _interrupts_pending(intr):
                await clear_tid(db, session_id)
                await db.flush()
        except Exception:
            logger.exception("clear langgraph thread id failed")

    yield ("done", None)

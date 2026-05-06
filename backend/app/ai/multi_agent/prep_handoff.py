"""用户确认行程后，再触发 Agent3（行前）。通过会话 pending 状态与简短话术匹配实现。"""

from __future__ import annotations

import re


def user_confirms_itinerary_for_prep(message: str) -> bool:
    """用户明确表示认可当前行程草案、同意继续行前指南。"""
    s = (message or "").strip()
    if not s or len(s) > 120:
        return False
    if re.match(
        r"^(好[的呀吧]?[.。!！\s]*|行[.。!！\s]*|可以[.。!！\s]*|确认|同意|没问题|满意|"
        r"就这样|就按这个|要的就是|继续|OK|ok|嗯[，,]?\s*好|哦[，,]?\s*好)",
        s,
        re.I,
    ):
        return True
    if re.match(
        r"^(嗯|噢|哦)?[，,]?\s*(好|行|可以|OK|ok)\s*[.。!！]?$",
        s,
        re.I,
    ):
        return True
    return False


def user_replies_planner_ab_choice(message: str) -> bool:
    """行程草案确认挂起时，用户仅回 A/B（或「选A」）——视为回答 Planner 的二选一，而非行前确认。"""
    s = (message or "").strip()
    if not s or len(s) > 32:
        return False
    if re.fullmatch(r"[aAbB](?:[.。!！…、]\s*)?", s):
        return True
    return bool(re.fullmatch(r"(?:选|我选)\s*[：:]?\s*[aAbB](?:[.。!！…、]\s*)?", s, flags=re.I))


def human_message_for_ab_choice_reply(message: str) -> str:
    """把简短 A/B 扩成一条明确的 HumanMessage，供 Planner 继续收紧动线。"""
    s = (message or "").strip()
    m = re.search(r"[aAbB]", s)
    if not m:
        return s
    letter = m.group(0).upper()
    return (
        f"我选 **{letter}**，请按你上一轮最后给出的 A/B 二选一中的 **{letter}** 选项，"
        "把住宿建议与每日动线、交通衔接收紧到可执行的版本。"
    )


def user_cancels_prep_pending(message: str) -> bool:
    """用户明确要重来，清除待行前状态。"""
    s = (message or "").strip()
    if not s:
        return False
    return bool(
        re.search(
            r"(重新|重来|取消|算了|别按这个|推翻).{0,12}(行程|计划|规划|安排|攻略)|"
            r"^重新来",
            s,
        )
    )

"""Heuristic merge: 仅当 Agent1 写出「目的地锁定」类话术时回填目的地，避免推荐语误触发下游规划。"""

from __future__ import annotations

import re

from app.ai.schemas.travel_profile import TravelProfile

# 仅匹配 Handoff 正式句，避免阶段三问句「把目的地定在【X】可以吗？」误触发下游。
# 与 INTENT_AGENT_SYSTEM 要求一致：必须出现「目的地锁定为【地名】」。
_RE_DEST_LOCKED = re.compile(r"目的地锁定为\s*[【「]([^」】]{2,40})[」】]")
# 天数：X天（排除「天气」）
_RE_DAYS = re.compile(r"(\d{1,2})\s*天(?!气)")
_RE_DAYS_TOUR = re.compile(r"(\d{1,2})\s*日游")


def extract_locked_destination(agent1_text: str) -> str | None:
    """若正文含「目的地锁定为【地名】」，返回地名；否则 None（不触发 Planner/Prep）。"""
    if not agent1_text or not agent1_text.strip():
        return None
    m = _RE_DEST_LOCKED.search(agent1_text)
    if not m:
        return None
    dest = m.group(1).strip()
    dest = re.sub(r"^[【「]|[」】]$", "", dest).strip()
    if len(dest) >= 2:
        return dest
    return None


def merge_travel_profile_from_text(profile: TravelProfile, agent1_text: str) -> TravelProfile:
    """在已有 handoff 前提下，用锁定句与正文补全画像（目的地仅来自锁定句或已有字段）。"""
    if not agent1_text or not agent1_text.strip():
        return profile

    data = profile.model_dump()
    t = agent1_text

    locked = extract_locked_destination(t)
    if locked:
        data["destination"] = locked
    elif not (data.get("destination") or "").strip():
        # 无锁定句时不从正文猜测目的地，避免「推荐你去大理」误填
        data["destination"] = None

    if data.get("days") is None:
        for rx in (_RE_DAYS, _RE_DAYS_TOUR):
            m = rx.search(t)
            if m:
                d = int(m.group(1))
                if 1 <= d <= 90:
                    data["days"] = d
                    break

    return TravelProfile.model_validate(data)

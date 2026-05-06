"""跨会话用户旅行记忆（与单条 TravelProfile 会话画像互补）。"""

from typing import Literal

from pydantic import BaseModel, Field


class PersistentTravelMemory(BaseModel):
    """存 users.travel_memory JSON；随对话增量合并。"""

    version: int = Field(default=1, ge=1)
    satisfied_with: list[str] = Field(default_factory=list, description="用户明确满意或反复选择的点")
    unsatisfied_with: list[str] = Field(default_factory=list, description="用户明确不满意或要避免的点")
    implicit_needs: str | None = Field(default=None, description="推断的隐藏需求/禁忌摘要")
    default_interaction_mode: Literal["verbose", "quiet"] | None = Field(
        default=None,
        description="默认交互模式；可被会话级覆盖",
    )
    recent_destinations: list[str] = Field(default_factory=list, max_length=12)
    preference_tags: list[str] = Field(default_factory=list, max_length=40)

    def merge_delta(
        self,
        *,
        satisfied: list[str],
        unsatisfied: list[str],
        implicit_note: str | None,
        destination_hint: str | None,
        mode_default: Literal["verbose", "quiet"] | None,
    ) -> "PersistentTravelMemory":
        def _uniq_cap(seq: list[str], cap: int) -> list[str]:
            out: list[str] = []
            seen: set[str] = set()
            for x in seq:
                t = (x or "").strip()
                if len(t) < 2 or t.lower() in seen:
                    continue
                seen.add(t.lower())
                out.append(t)
                if len(out) >= cap:
                    break
            return out

        sat = _uniq_cap([*self.satisfied_with, *satisfied], 40)
        unsat = _uniq_cap([*self.unsatisfied_with, *unsatisfied], 40)
        tags = _uniq_cap([*self.preference_tags], 40)
        dests = list(self.recent_destinations)
        if destination_hint:
            d = destination_hint.strip()
            if d and d not in dests:
                dests.insert(0, d)
        dests = dests[:12]
        implicit = implicit_note.strip() if implicit_note else None
        merged_implicit = implicit or self.implicit_needs
        if implicit and self.implicit_needs and implicit not in self.implicit_needs:
            merged_implicit = f"{self.implicit_needs}\n{implicit}".strip()[:2000]

        mode = mode_default if mode_default is not None else self.default_interaction_mode

        return PersistentTravelMemory(
            version=self.version,
            satisfied_with=sat,
            unsatisfied_with=unsat,
            implicit_needs=merged_implicit,
            default_interaction_mode=mode,
            recent_destinations=dests,
            preference_tags=tags,
        )

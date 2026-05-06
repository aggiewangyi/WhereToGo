"""跨会话旅行记忆 → 系统提示片段。"""

from __future__ import annotations

from app.ai.schemas.persistent_travel_memory import PersistentTravelMemory


def format_travel_memory_system_block(mem: PersistentTravelMemory) -> str:
    blocks: list[str] = []
    if mem.satisfied_with:
        lines = "\n".join(f"- {x}" for x in mem.satisfied_with[:20])
        blocks.append(f"【历史偏好·用户曾满意】\n{lines}")
    if mem.unsatisfied_with:
        lines = "\n".join(f"- {x}" for x in mem.unsatisfied_with[:20])
        blocks.append(f"【历史避坑·用户曾不满】\n{lines}")
    if mem.implicit_needs:
        blocks.append(f"【长期需求/禁忌摘要】\n{mem.implicit_needs[:1200]}")
    if mem.preference_tags:
        blocks.append("【兴趣标签】" + "、".join(mem.preference_tags[:30]))
    return "\n\n".join(blocks)


VERBOSE_MODE_BLOCK = (
    "【交互模式：步步同步】"
    "状态播报：每轮回复开头用一行字说明当前进度（如：已定城市，待定风格）。"
    "锁定机制：在用户明确输入“锁定[目的地]”前，严禁展示日历格式的行程，仅展示路线草图。"
)

QUIET_MODE_BLOCK = (
    "【交互模式：少打扰高效】"
    "首轮查漏：若用户原始输入信息不足以画出画像，立即列出[待补充关键项]清单（如：预算、同行人数、必避坑点），要求用户一次性告知，拒绝碎片化追问。"
    "默认推断权：在获得基础信息后，非冲突性细节由 AI 基于大数据直接决策。"
    "闭环确认：输出方案后，底部仅允许提问：“方案是否可行？(Yes/No)”，或让用户从“可替换模块”中选序号修改。"
    "可替换模块：文末固定格式为：若需微调请回复序号：[1.酒店升档] [2.节奏放缓] [3.更换备选景点]。"
    "设计哲学：专业旅行管家，我出方案，你点赞或否决。"
)

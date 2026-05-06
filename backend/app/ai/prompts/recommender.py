DESTINATION_RECOMMEND_PROMPT = """\
基于用户的以下偏好，推荐最合适的旅行目的地：

用户需求: {user_message}
预算: {budget}
时间: {travel_dates}
人数: {people_count}

请推荐 3-5 个目的地，每个包含：
- 目的地名称及简介
- 推荐理由（为什么适合该用户）
- 预估人均费用
- 最佳出行月份
- 推荐指数（1-5星）
"""

PACKING_LIST_PROMPT = """\
请为用户生成个性化打包清单：

目的地: {destination}
出行日期: {start_date} 至 {end_date}
活动类型: {activities}
性别: {gender}
是否出境: {is_international}
天气预报: {weather_info}

请输出：
1. 分类打包清单（衣物/洗护/电子/证件/装备）
2. 每日穿搭建议
3. 特别注意事项（如宗教着装要求、文化禁忌等）
"""

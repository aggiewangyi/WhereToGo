"""
Seed `destinations` with preset rows for demo / 目的地展示.

Run from backend directory (after `poetry install`):
  poetry run python scripts/seed_destinations.py
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlalchemy import func, select  # noqa: E402

from app.core.database import async_session_factory  # noqa: E402
from app.models.destination import Destination  # noqa: E402

SEED: list[dict] = [
    {
        "name": "大理",
        "country": "中国",
        "province": "云南",
        "city": "大理白族自治州",
        "tags": '["洱海","古城","慢生活"]',
        "best_seasons": "3,4,5,9,10,11",
        "avg_cost_per_day": 380.0,
        "visa_required": 0,
        "safety_level": 5,
        "cover_image": "https://images.unsplash.com/photo-1548013146-72479768bada?w=800&q=80",
        "knowledge_card": "## 当地提示\n\n- **气候**：高原紫外线强，注意防晒与补水。\n- **习俗**：白族聚居区，尊重民族节日与宗教场所礼仪。\n- **环保**：洱海生态敏感区，勿随意丢弃垃圾、勿违规下水。\n",
    },
    {
        "name": "丽江",
        "country": "中国",
        "province": "云南",
        "city": "丽江市",
        "tags": '["古城","雪山","摄影"]',
        "best_seasons": "4,5,6,9,10,11",
        "avg_cost_per_day": 420.0,
        "visa_required": 0,
        "safety_level": 5,
        "cover_image": "https://images.unsplash.com/photo-1508804185872-d7badad00f7d?w=800&q=80",
        "knowledge_card": "## 当地提示\n\n- **海拔**：玉龙雪山区域注意高反，勿剧烈运动。\n- **古城**：石板路多，建议舒适平底鞋。\n- **消费**：景区内购物先询价，理性选择旅拍套餐。\n",
    },
    {
        "name": "厦门",
        "country": "中国",
        "province": "福建",
        "city": "厦门市",
        "tags": '["海岛","文艺","小吃"]',
        "best_seasons": "3,4,5,10,11,12",
        "avg_cost_per_day": 400.0,
        "visa_required": 0,
        "safety_level": 5,
        "cover_image": "https://images.unsplash.com/photo-1540959733332-eab4deabeeaf?w=800&q=80",
        "knowledge_card": "## 当地提示\n\n- **鼓浪屿**：需轮渡，旺季建议提前预约船票。\n- **饮食**：海鲜大排档注意明码标价。\n- **天气**：夏季台风季，关注航班与轮渡动态。\n",
    },
    {
        "name": "西安",
        "country": "中国",
        "province": "陕西",
        "city": "西安市",
        "tags": '["历史","兵马俑","面食"]',
        "best_seasons": "4,5,9,10,11",
        "avg_cost_per_day": 320.0,
        "visa_required": 0,
        "safety_level": 5,
        "cover_image": "https://images.unsplash.com/photo-1591122947157-26bad3a117d2?w=800&q=80",
        "knowledge_card": "## 当地提示\n\n- **兵马俑**：建议预约讲解，参观时长约半天。\n- **气候**：春秋舒适，夏季炎热、冬季干冷。\n- **饮食**：回民街热闹，注意随身物品安全。\n",
    },
    {
        "name": "杭州",
        "country": "中国",
        "province": "浙江",
        "city": "杭州市",
        "tags": '["西湖","江南","亲子"]',
        "best_seasons": "3,4,5,9,10,11",
        "avg_cost_per_day": 400.0,
        "visa_required": 0,
        "safety_level": 5,
        "cover_image": "https://images.unsplash.com/photo-1599571234909-29ed5d1321d6?w=800&q=80",
        "knowledge_card": "## 当地提示\n\n- **西湖**：节假日断桥、苏堤人流大，可错峰或骑行环湖。\n- **季节**：春季多雨，备轻便雨具。\n- **饮食**：杭帮菜偏甜，可尝试本地小吃葱包桧、片儿川。\n",
    },
    {
        "name": "青岛",
        "country": "中国",
        "province": "山东",
        "city": "青岛市",
        "tags": '["海滨","啤酒","德式建筑"]',
        "best_seasons": "6,7,8,9,10",
        "avg_cost_per_day": 360.0,
        "visa_required": 0,
        "safety_level": 5,
        "cover_image": "https://images.unsplash.com/photo-1559827260-dc66d52bef19?w=800&q=80",
        "knowledge_card": "## 当地提示\n\n- **海滨**：注意潮汐与离岸流，勿在未开放海域游泳。\n- **啤酒节**：人流密集，注意财物与饮酒适量。\n- **气候**：夏季凉爽但潮湿，备薄外套。\n",
    },
    {
        "name": "桂林",
        "country": "中国",
        "province": "广西",
        "city": "桂林市",
        "tags": '["山水","漓江","摄影"]',
        "best_seasons": "4,5,6,9,10,11",
        "avg_cost_per_day": 340.0,
        "visa_required": 0,
        "safety_level": 5,
        "cover_image": "https://images.unsplash.com/photo-1530870110042-98b2cb110834?w=800&q=80",
        "knowledge_card": "## 当地提示\n\n- **漓江**：竹筏/游船项目先确认票价与线路。\n- **天气**：雨季路滑，徒步注意防滑鞋。\n- **消费**：景区周边特产先比价。\n",
    },
    {
        "name": "张家界",
        "country": "中国",
        "province": "湖南",
        "city": "张家界市",
        "tags": '["奇峰","徒步","玻璃栈道"]',
        "best_seasons": "4,5,6,9,10,11",
        "avg_cost_per_day": 380.0,
        "visa_required": 0,
        "safety_level": 5,
        "cover_image": "https://images.unsplash.com/photo-1508804052814-cd3ba865a116?w=800&q=80",
        "knowledge_card": "## 当地提示\n\n- **步道**：悬崖栈道勿拥挤推搡，看管好儿童。\n- **天气**：山区多变，备雨具与保暖层。\n- **门票**：核心景区需实名，提前官方渠道预约。\n",
    },
    {
        "name": "三亚",
        "country": "中国",
        "province": "海南",
        "city": "三亚市",
        "tags": '["海岛","度假","潜水"]',
        "best_seasons": "11,12,1,2,3,4",
        "avg_cost_per_day": 550.0,
        "visa_required": 0,
        "safety_level": 5,
        "cover_image": "https://images.unsplash.com/photo-1544551763-46a013bb70d5?w=800&q=80",
        "knowledge_card": "## 当地提示\n\n- **防晒**：海边紫外线极强，勤补防晒霜。\n- **水上项目**：选择正规运营商，穿好救生装备。\n- **消费**：海鲜加工先确认单价与斤两。\n",
    },
    {
        "name": "拉萨",
        "country": "中国",
        "province": "西藏",
        "city": "拉萨市",
        "tags": '["高原","朝圣","摄影"]',
        "best_seasons": "5,6,7,8,9,10",
        "avg_cost_per_day": 450.0,
        "visa_required": 0,
        "safety_level": 4,
        "cover_image": "https://images.unsplash.com/photo-1544986581-efac024faf62?w=800&q=80",
        "knowledge_card": "## 当地提示\n\n- **高反**：初到勿剧烈运动，备常用药物并遵医嘱。\n- **宗教**：寺庙内勿随意拍照、顺时针绕行。\n- **证件**：部分区域需边防证，提前了解政策。\n",
    },
    {
        "name": "大阪",
        "country": "日本",
        "province": None,
        "city": "大阪府",
        "tags": '["美食","环球影城","购物"]',
        "best_seasons": "3,4,5,10,11",
        "avg_cost_per_day": 750.0,
        "visa_required": 2,
        "safety_level": 5,
        "cover_image": "https://images.unsplash.com/photo-1590559899731-a382839e5549?w=800&q=80",
        "knowledge_card": "## 当地提示\n\n- **交通**：JR 与地铁线路复杂，可用导航 App 规划。\n- **饮食**：道顿堀热闹，注意排队礼仪。\n- **退税**：购物满额可退税，保留小票。\n",
    },
    {
        "name": "新加坡",
        "country": "新加坡",
        "province": None,
        "city": "新加坡",
        "tags": '["花园城市","亲子","多元文化"]',
        "best_seasons": "1,2,3,4,5,6,7,8,9,10,11,12",
        "avg_cost_per_day": 850.0,
        "visa_required": 2,
        "safety_level": 5,
        "cover_image": "https://images.unsplash.com/photo-1525625293386-3f8f99389edd?w=800&q=80",
        "knowledge_card": "## 当地提示\n\n- **法律**：乱丢垃圾、地铁饮食、口香糖等均可能重罚。\n- **气候**：常年湿热，室内外温差大备薄外套。\n- **文化**：多民族融合，尊重宗教场所规则。\n",
    },
    {
        "name": "首尔",
        "country": "韩国",
        "province": None,
        "city": "首尔",
        "tags": '["购物","美食","韩流"]',
        "best_seasons": "4,5,9,10,11",
        "avg_cost_per_day": 650.0,
        "visa_required": 2,
        "safety_level": 5,
        "cover_image": "https://images.unsplash.com/photo-1517154421773-0529f29ea451?w=800&q=80",
        "knowledge_card": "## 当地提示\n\n- **礼仪**：长辈优先、敬酒接杯用双手更礼貌。\n- **垃圾分类**：酒店与公共场所按指示分类。\n- **支付**：T-money 交通卡方便，多数店支持刷卡。\n",
    },
    {
        "name": "巴黎",
        "country": "法国",
        "province": None,
        "city": "巴黎",
        "tags": '["艺术","博物馆","浪漫"]',
        "best_seasons": "4,5,6,9,10,11",
        "avg_cost_per_day": 1100.0,
        "visa_required": 2,
        "safety_level": 4,
        "cover_image": "https://images.unsplash.com/photo-1502602898657-3e91760cbb34?w=800&q=80",
        "knowledge_card": "## 当地提示\n\n- **安全**：景区与地铁谨防扒手，背包前置。\n- **礼仪**：进店问候「Bonjour」更得体。\n- **小费**：服务费常已含账单，额外小费非强制。\n",
    },
]


async def main() -> None:
    async with async_session_factory() as session:
        cnt = (await session.execute(select(func.count()).select_from(Destination))).scalar() or 0
        if cnt >= 8:
            print(f"destinations already has {cnt} rows, skip seed.")
            return
        for row in SEED:
            session.add(Destination(**row))
        await session.commit()
        print(f"Inserted {len(SEED)} destinations.")


if __name__ == "__main__":
    asyncio.run(main())

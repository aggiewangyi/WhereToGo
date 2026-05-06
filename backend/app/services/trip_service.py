import json

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.llm_client import build_llm
from app.ai.prompts.planner import TRIP_GENERATE_PROMPT
from app.crud.trip import crud_budget, crud_itinerary, crud_trip
from app.models.trip import Budget, Trip
from app.schemas.trip import TripCreate, TripGenerateRequest


async def create_trip(db: AsyncSession, user_id: int, data: TripCreate) -> Trip:
    data_dict = data.model_dump()
    data_dict["user_id"] = user_id
    trip = Trip(**data_dict)
    db.add(trip)
    await db.flush()
    loaded = await crud_trip.get_with_details(db, trip.id)
    return loaded if loaded is not None else trip


async def generate_trip_plan(db: AsyncSession, user_id: int, req: TripGenerateRequest) -> Trip:
    """Use AI to generate a complete trip plan, then persist it."""
    trip = await create_trip(
        db,
        user_id,
        TripCreate(title=f"{req.destination}{req.days}日游", destination_id=None, people_count=req.people_count),
    )

    prompt = TRIP_GENERATE_PROMPT.format(
        destination=req.destination,
        days=req.days,
        people_count=req.people_count,
        budget=req.budget or "不限",
        preferences=", ".join(req.preferences) if req.preferences else "无特殊偏好",
    )

    llm = build_llm()
    response = await llm.ainvoke(prompt)
    plan_text = response.content if hasattr(response, "content") else str(response)

    await crud_itinerary.upsert(db, trip.id, json.dumps({"raw": plan_text}, ensure_ascii=False))

    if req.budget:
        budget = Budget(trip_id=trip.id, total=req.budget, currency="CNY")
        db.add(budget)
        await db.flush()

    return await crud_trip.get_with_details(db, trip.id)


async def get_trip_detail(db: AsyncSession, trip_id: int) -> Trip | None:
    return await crud_trip.get_with_details(db, trip_id)


async def list_user_trips(db: AsyncSession, user_id: int, skip: int = 0, limit: int = 20) -> list[Trip]:
    return await crud_trip.get_user_trips(db, user_id, skip, limit)

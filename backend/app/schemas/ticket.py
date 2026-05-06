from datetime import date

from pydantic import BaseModel, Field


class TicketSearchRequest(BaseModel):
    origin: str
    destination: str
    departure_date: date
    return_date: date | None = None
    passengers: int = Field(1, ge=1)
    transport_type: str | None = Field(None, description="flight / train / bus")
    flexible_dates: bool = False


class PriceAlertRequest(BaseModel):
    origin: str
    destination: str
    departure_date: date
    target_price: float = Field(..., gt=0)
    transport_type: str = "flight"


class TicketResult(BaseModel):
    provider: str
    transport_type: str
    departure_time: str
    arrival_time: str
    duration_minutes: int
    price: float
    currency: str = "CNY"
    booking_url: str | None = None
    refund_policy: str | None = None

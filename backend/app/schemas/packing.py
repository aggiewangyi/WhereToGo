from pydantic import BaseModel, Field


class PackingGenerateRequest(BaseModel):
    destination: str
    start_date: str
    end_date: str
    activities: list[str] | None = Field(None, description="hiking / beach / city_tour ...")
    gender: str | None = None
    is_international: bool = False


class PackingItem(BaseModel):
    name: str
    category: str  # clothing / toiletry / electronics / document / gear
    quantity: int = 1
    checked: bool = False
    note: str | None = None


class PackingListOut(BaseModel):
    items: list[PackingItem]
    clothing_advice: str | None = None
    document_checklist: list[str] | None = None

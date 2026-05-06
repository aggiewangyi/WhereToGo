from pydantic import BaseModel, ConfigDict


class SchemaBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class PaginationParams(BaseModel):
    page: int = 1
    page_size: int = 20


class PaginatedResponse(SchemaBase):
    total: int
    page: int
    page_size: int
    items: list

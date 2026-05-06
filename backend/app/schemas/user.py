from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.base import SchemaBase


# ---------- Request ----------
class UserRegister(BaseModel):
    phone: str = Field(..., min_length=11, max_length=20)
    nickname: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=6, max_length=128)


class UserLogin(BaseModel):
    phone: str
    password: str


class UserUpdate(BaseModel):
    nickname: str | None = None
    avatar: str | None = None
    preferences: dict | None = None


# ---------- Response ----------
class UserOut(SchemaBase):
    id: int
    phone: str
    nickname: str
    avatar: str | None = None
    is_verified: bool
    created_at: datetime


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"

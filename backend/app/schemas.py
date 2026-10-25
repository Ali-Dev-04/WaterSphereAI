"""Pydantic v2 request/response schemas. Every route validates through these."""

import datetime as dt

from pydantic import BaseModel, Field


class RegisterIn(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=6, max_length=128)
    role: str = Field(default="citizen", pattern="^(admin|citizen)$")
    ward_id: str | None = Field(default=None, max_length=16)


class LoginIn(BaseModel):
    username: str
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: int
    username: str
    role: str
    ward_id: str | None


class ForecastOut(BaseModel):
    ward_id: str
    target_date: dt.date
    horizon: str
    predicted_ml: float
    model: str
    model_version: str


class ComplaintIn(BaseModel):
    ward_id: str = Field(max_length=16)
    type: str = Field(max_length=32)


class ComplaintOut(BaseModel):
    id: int
    user_id: int | None
    ward_id: str
    type: str
    status: str
    created_at: dt.datetime
    # Guest-report fields (None for authenticated citizen complaints).
    reporter_name: str | None = None
    address: str | None = None
    description: str | None = None
    has_photo: bool = False


class StatusIn(BaseModel):
    status: str = Field(pattern="^(Filed|In-progress|Resolved)$")

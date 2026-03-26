from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict


T = TypeVar('T')


class ApiResponse(BaseModel, Generic[T]):
    success: bool = True
    message: str = 'OK'
    data: T | None = None


class ErrorPayload(BaseModel):
    code: str
    message: str
    details: dict = {}


class HealthPayload(BaseModel):
    status: str
    app: str
    environment: str


class PaginationMeta(BaseModel):
    total: int


class ModelBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

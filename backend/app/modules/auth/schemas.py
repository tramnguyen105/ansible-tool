from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, SecretStr

from app.schemas.common import ModelBase


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=128)
    password: SecretStr = Field(min_length=1)


class RoleRead(ModelBase):
    id: UUID
    name: str
    description: str | None = None


class UserRead(ModelBase):
    id: UUID
    username: str
    display_name: str | None = None
    email: str | None = None
    auth_source: str
    last_login_at: datetime | None = None
    roles: list[RoleRead] = []


class LoginPayload(BaseModel):
    user: UserRead
    csrf_token: str
    expires_at: datetime


class SessionPayload(BaseModel):
    user: UserRead
    expires_at: datetime

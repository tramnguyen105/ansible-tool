from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, SecretStr

from app.schemas.common import ModelBase


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
    ldap_dn: str | None = None
    is_active: bool
    last_login_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    roles: list[RoleRead] = []


class UserCreate(BaseModel):
    username: str = Field(min_length=1, max_length=128)
    display_name: str | None = Field(default=None, max_length=255)
    email: str | None = Field(default=None, max_length=255)
    auth_source: str = Field(default='local', pattern='^(local|ldap)$')
    ldap_dn: str | None = Field(default=None, max_length=1024)
    password: SecretStr | None = Field(default=None, min_length=8, max_length=128)
    role_names: list[str] = Field(default_factory=lambda: ['operator'])
    is_active: bool = True


class UserUpdate(BaseModel):
    display_name: str | None = Field(default=None, max_length=255)
    email: str | None = Field(default=None, max_length=255)
    ldap_dn: str | None = Field(default=None, max_length=1024)
    role_names: list[str] | None = None
    is_active: bool | None = None


class UserPasswordResetRequest(BaseModel):
    new_password: SecretStr = Field(min_length=8, max_length=128)

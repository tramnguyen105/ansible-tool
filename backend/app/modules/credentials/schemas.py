from __future__ import annotations

from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.common import ModelBase


class CredentialTypeSchema(StrEnum):
    SSH_PASSWORD = 'ssh_password'
    SSH_PRIVATE_KEY = 'ssh_private_key'


class CredentialCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    credential_type: CredentialTypeSchema
    username: str = Field(min_length=1, max_length=255)
    password: str | None = None
    private_key: str | None = None
    passphrase: str | None = None


class CredentialUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    username: str | None = Field(default=None, min_length=1, max_length=255)
    password: str | None = None
    private_key: str | None = None
    passphrase: str | None = None
    is_active: bool | None = None


class CredentialRead(ModelBase):
    id: UUID
    name: str
    description: str | None = None
    credential_type: str
    username: str
    is_active: bool
    has_password: bool
    has_private_key: bool
    has_passphrase: bool


class CredentialUsageRead(BaseModel):
    schedules_total: int
    schedules_enabled: int
    jobs_total: int
    jobs_active: int

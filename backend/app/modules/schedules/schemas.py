from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.common import ModelBase


class ScheduleCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    cron_expression: str = Field(min_length=1, max_length=64)
    timezone: str = Field(default='UTC', min_length=1, max_length=64)
    enabled: bool = True
    inventory_id: UUID
    credential_id: UUID
    playbook_id: UUID
    target_type: str = Field(default='all', max_length=32)
    target_value: str | None = Field(default=None, max_length=255)
    extra_vars: dict[str, Any] = Field(default_factory=dict)
    check_mode: bool = False
    pre_check_playbook_id: UUID | None = None
    post_check_playbook_id: UUID | None = None
    pre_check_content: str | None = None
    post_check_content: str | None = None


class ScheduleUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    cron_expression: str | None = Field(default=None, min_length=1, max_length=64)
    timezone: str | None = Field(default=None, min_length=1, max_length=64)
    enabled: bool | None = None
    inventory_id: UUID | None = None
    credential_id: UUID | None = None
    playbook_id: UUID | None = None
    target_type: str | None = Field(default=None, max_length=32)
    target_value: str | None = Field(default=None, max_length=255)
    extra_vars: dict[str, Any] | None = None
    check_mode: bool | None = None
    pre_check_playbook_id: UUID | None = None
    post_check_playbook_id: UUID | None = None
    pre_check_content: str | None = None
    post_check_content: str | None = None


class ScheduleRead(ModelBase):
    id: UUID
    name: str
    description: str | None = None
    cron_expression: str
    timezone: str
    enabled: bool
    inventory_id: UUID | None = None
    credential_id: UUID | None = None
    playbook_id: UUID | None = None
    target_type: str
    target_value: str | None = None
    extra_vars_json: dict[str, Any]
    check_mode: bool
    next_run_at: datetime | None = None
    last_run_at: datetime | None = None
    created_at: datetime

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.common import ModelBase


class JobCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
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
    execute_now: bool = True


class JobResultRead(ModelBase):
    id: UUID
    return_code: int | None = None
    stdout: str
    stderr: str
    summary_json: dict[str, Any]
    artifact_dir: str | None = None
    created_at: datetime
    updated_at: datetime


class JobRead(ModelBase):
    id: UUID
    name: str
    status: str
    inventory_id: UUID | None = None
    credential_id: UUID | None = None
    playbook_id: UUID | None = None
    target_type: str
    target_value: str | None = None
    extra_vars_json: dict[str, Any]
    check_mode: bool
    celery_task_id: str | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    created_at: datetime
    result: JobResultRead | None = None


class JobListSummaryRead(ModelBase):
    queued: int
    running: int
    success: int
    failed: int
    check_mode: int


class JobListRead(ModelBase):
    items: list[JobRead]
    total: int
    limit: int
    offset: int
    has_more: bool
    summary: JobListSummaryRead

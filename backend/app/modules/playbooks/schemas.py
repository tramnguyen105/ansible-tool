from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.common import ModelBase


class PlaybookCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    yaml_content: str = Field(min_length=1)
    is_generated: bool = False
    change_note: str | None = None


class PlaybookUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    yaml_content: str | None = None
    change_note: str | None = None
    expected_updated_at: datetime | None = None


class PlaybookRevisionRead(ModelBase):
    id: UUID
    version: int
    yaml_content: str
    change_note: str | None = None
    created_at: datetime


class PlaybookRead(ModelBase):
    id: UUID
    name: str
    description: str | None = None
    yaml_content: str
    is_generated: bool
    updated_at: datetime
    revisions: list[PlaybookRevisionRead] = []


class PlaybookSummaryRead(ModelBase):
    id: UUID
    name: str
    description: str | None = None
    is_generated: bool
    revision_count: int
    last_change_note: str | None = None
    updated_at: datetime


class PlaybookUsageRead(BaseModel):
    jobs_main: int
    jobs_pre_check: int
    jobs_post_check: int
    schedules_main: int
    schedules_pre_check: int
    schedules_post_check: int
    total: int


class YamlValidationRequest(BaseModel):
    content: str = Field(min_length=1)


class YamlValidationResult(BaseModel):
    valid: bool
    errors: list[str] = []

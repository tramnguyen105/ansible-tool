from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.common import ModelBase


class TemplateSourceTypeSchema(StrEnum):
    MANUAL = 'manual'
    CONVERTER = 'converter'


class TemplateCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    content: str = Field(min_length=1)


class TemplateUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    content: str | None = None


class TemplateSummaryRead(ModelBase):
    id: UUID
    name: str
    description: str | None = None
    source_type: TemplateSourceTypeSchema
    conversion_job_id: UUID | None = None
    content_hash: str
    revision: int
    created_at: datetime
    updated_at: datetime
    preview: str


class TemplateRead(TemplateSummaryRead):
    content: str


class TemplateValidateRequest(BaseModel):
    content: str = Field(min_length=1)


class TemplateValidateRead(BaseModel):
    valid: bool = True
    message: str = 'Template syntax is valid'
    line: int | None = None
    name: str | None = None

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class CliOutputType(StrEnum):
    TEMPLATE = 'template'
    TASKS = 'tasks'
    PLAYBOOK = 'playbook'


class CliParseRequest(BaseModel):
    config_text: str = Field(min_length=1, max_length=200_000)


class CliWarning(BaseModel):
    code: str
    message: str
    line: int | None = None
    severity: str = 'warn'


class CliBlock(BaseModel):
    kind: str
    parent: str
    lines: list[str]
    line: int | None = None
    supported: bool = True


class CliParseResult(BaseModel):
    global_lines: list[str]
    blocks: list[CliBlock]
    warnings: list[CliWarning]


class CliGenerateRequest(CliParseRequest):
    output_type: CliOutputType
    parsed: CliParseResult | None = None


class CliGenerateResult(BaseModel):
    output_type: CliOutputType
    parsed: CliParseResult
    generated_content: str
    warnings: list[CliWarning]
    conversion_job_id: UUID | None = None


class CliValidateResult(BaseModel):
    valid: bool
    warnings: list[CliWarning]


class CliValidateGeneratedRequest(BaseModel):
    output_type: CliOutputType
    generated_content: str = Field(min_length=1)


class CliValidateGeneratedResult(BaseModel):
    valid: bool
    errors: list[str] = []
    normalized_content: str | None = None


class CliSavePlaybookRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    generated_content: str = Field(min_length=1)
    source_config: str | None = None
    conversion_job_id: UUID | None = None
    output_type: CliOutputType = CliOutputType.PLAYBOOK


class CliSaveTemplateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    generated_content: str = Field(min_length=1)
    source_config: str | None = None
    conversion_job_id: UUID | None = None


class CliConversionJobRead(BaseModel):
    id: UUID
    output_type: CliOutputType
    warning_count: int = 0
    created_at: datetime

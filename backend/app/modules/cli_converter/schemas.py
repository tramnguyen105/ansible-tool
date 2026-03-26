from __future__ import annotations

from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class CliOutputType(StrEnum):
    TEMPLATE = 'template'
    TASKS = 'tasks'
    PLAYBOOK = 'playbook'


class CliParseRequest(BaseModel):
    config_text: str = Field(min_length=1)


class CliBlock(BaseModel):
    kind: str
    parent: str
    lines: list[str]
    supported: bool = True


class CliParseResult(BaseModel):
    global_lines: list[str]
    blocks: list[CliBlock]
    warnings: list[str]


class CliGenerateRequest(CliParseRequest):
    output_type: CliOutputType


class CliGenerateResult(BaseModel):
    output_type: CliOutputType
    parsed: CliParseResult
    generated_content: str
    warnings: list[str]
    conversion_job_id: UUID | None = None


class CliValidateResult(BaseModel):
    valid: bool
    warnings: list[str]


class CliSavePlaybookRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    generated_content: str = Field(min_length=1)
    source_config: str = Field(min_length=1)


class CliSaveTemplateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    generated_content: str = Field(min_length=1)
    source_config: str = Field(min_length=1)

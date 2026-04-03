from __future__ import annotations

from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.common import ModelBase


class ImportFormat(StrEnum):
    INI = 'ini'
    YAML = 'yaml'
    CSV = 'csv'
    EXCEL = 'excel'


class InventoryHostInput(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    address: str | None = Field(default=None, max_length=255)
    description: str | None = None
    variables: dict[str, Any] = Field(default_factory=dict)
    enabled: bool = True
    groups: list[str] = Field(default_factory=list)


class InventoryGroupInput(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    variables: dict[str, Any] = Field(default_factory=dict)
    children: list[str] = Field(default_factory=list)


class InventoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    variables: dict[str, Any] = Field(default_factory=dict)
    hosts: list[InventoryHostInput] = Field(default_factory=list)
    groups: list[InventoryGroupInput] = Field(default_factory=list)


class InventoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    variables: dict[str, Any] | None = None
    hosts: list[InventoryHostInput] | None = None
    groups: list[InventoryGroupInput] | None = None


class InventoryHostRead(ModelBase):
    id: UUID
    name: str
    address: str | None = None
    description: str | None = None
    variables_json: dict[str, Any]
    enabled: bool
    groups: list[str] = []


class InventoryGroupRead(ModelBase):
    id: UUID
    name: str
    description: str | None = None
    variables_json: dict[str, Any]
    children: list[str] = []
    hosts: list[str] = []


class InventoryRead(ModelBase):
    id: UUID
    name: str
    description: str | None = None
    source_type: str
    variables_json: dict[str, Any]
    hosts: list[InventoryHostRead] = []
    groups: list[InventoryGroupRead] = []


class InventorySummaryRead(ModelBase):
    id: UUID
    name: str
    description: str | None = None
    source_type: str
    host_count: int = 0
    enabled_host_count: int = 0
    group_count: int = 0
    variable_scope_count: int = 0
    readiness: str
    readiness_note: str


class InventorySummaryStatsRead(ModelBase):
    inventories: int
    hosts: int
    enabled_hosts: int
    groups: int
    variable_bearing: int


class InventorySummaryListRead(ModelBase):
    items: list[InventorySummaryRead]
    total: int
    limit: int
    offset: int
    has_more: bool
    stats: InventorySummaryStatsRead


class InventoryUsageRead(BaseModel):
    schedules_total: int = 0
    schedules_enabled: int = 0
    jobs_total: int = 0
    jobs_active: int = 0


class InventoryImportPreview(BaseModel):
    source_format: ImportFormat
    variables: dict[str, Any] = Field(default_factory=dict)
    hosts: list[InventoryHostInput] = Field(default_factory=list)
    groups: list[InventoryGroupInput] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class InventoryImportPreviewRead(BaseModel):
    preview_id: str
    checksum: str
    expires_at: str
    preview: InventoryImportPreview


class InventoryImportCommit(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    preview_id: str = Field(min_length=1, max_length=255)
    checksum: str = Field(min_length=1, max_length=255)

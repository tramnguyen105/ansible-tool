from __future__ import annotations

from datetime import datetime
from uuid import UUID

from app.schemas.common import ModelBase


class AuditLogRead(ModelBase):
    id: UUID
    user_id: UUID | None = None
    actor_username: str | None = None
    actor_display_name: str | None = None
    action: str
    resource_type: str
    resource_id: str | None = None
    status: str
    message: str
    details_json: dict
    ip_address: str | None = None
    created_at: datetime


class AuditLogListRead(ModelBase):
    items: list[AuditLogRead]
    total: int
    limit: int
    offset: int
    has_more: bool

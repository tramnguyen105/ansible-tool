from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.audit import AuditLog
from app.modules.audit.repository import AuditRepository
from app.modules.audit.schemas import AuditLogListRead, AuditLogRead


SENSITIVE_KEYS = {'password', 'secret', 'passphrase', 'private_key', 'token'}


class AuditService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.repository = AuditRepository(session)

    def _sanitize(self, value: Any) -> Any:
        if isinstance(value, dict):
            sanitized: dict[str, Any] = {}
            for key, item in value.items():
                if key.lower() in SENSITIVE_KEYS:
                    sanitized[key] = '***'
                else:
                    sanitized[key] = self._sanitize(item)
            return sanitized
        if isinstance(value, list):
            return [self._sanitize(item) for item in value]
        return value

    def record(
        self,
        *,
        action: str,
        resource_type: str,
        message: str,
        user_id: UUID | None = None,
        resource_id: str | None = None,
        status: str = 'success',
        details: dict[str, Any] | None = None,
        ip_address: str | None = None,
        request_id: str | None = None,
        user_agent: str | None = None,
    ) -> AuditLog:
        detail_payload = dict(details or {})
        if request_id or user_agent:
            detail_payload['_request'] = {'request_id': request_id, 'user_agent': user_agent}
        entry = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            status=status,
            message=message,
            details_json=self._sanitize(detail_payload),
            ip_address=ip_address,
        )
        return self.repository.create(entry)

    def list(
        self,
        *,
        action: str | None = None,
        resource_types: list[str] | None = None,
        statuses: list[str] | None = None,
        user_id: UUID | None = None,
        resource_id: str | None = None,
        message: str | None = None,
        created_from: datetime | None = None,
        created_to: datetime | None = None,
        limit: int = 200,
        offset: int = 0,
    ) -> AuditLogListRead:
        items, total = self.repository.list(
            action=action,
            resource_types=resource_types,
            statuses=statuses,
            user_id=user_id,
            resource_id=resource_id,
            message=message,
            created_from=created_from,
            created_to=created_to,
            limit=limit,
            offset=offset,
        )
        serialized = [self._serialize(item) for item in items]
        return AuditLogListRead(
            items=serialized,
            total=total,
            limit=limit,
            offset=offset,
            has_more=offset + len(serialized) < total,
        )

    def export(
        self,
        *,
        action: str | None = None,
        resource_types: list[str] | None = None,
        statuses: list[str] | None = None,
        user_id: UUID | None = None,
        resource_id: str | None = None,
        message: str | None = None,
        created_from: datetime | None = None,
        created_to: datetime | None = None,
        limit: int = 5000,
    ) -> list[AuditLogRead]:
        items, _ = self.repository.list(
            action=action,
            resource_types=resource_types,
            statuses=statuses,
            user_id=user_id,
            resource_id=resource_id,
            message=message,
            created_from=created_from,
            created_to=created_to,
            limit=limit,
            offset=0,
        )
        return [self._serialize(item) for item in items]

    def _serialize(self, item: AuditLog) -> AuditLogRead:
        return AuditLogRead(
            id=item.id,
            user_id=item.user_id,
            actor_username=item.user.username if item.user else None,
            actor_display_name=item.user.display_name if item.user else None,
            action=item.action,
            resource_type=item.resource_type,
            resource_id=item.resource_id,
            status=item.status,
            message=item.message,
            details_json=item.details_json,
            ip_address=item.ip_address,
            created_at=item.created_at,
        )

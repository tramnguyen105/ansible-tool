from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.audit import AuditLog
from app.modules.audit.repository import AuditRepository


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
    ) -> AuditLog:
        entry = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            status=status,
            message=message,
            details_json=self._sanitize(details or {}),
            ip_address=ip_address,
        )
        return self.repository.create(entry)

    def list(self, *, action: str | None = None, resource_type: str | None = None, status: str | None = None, limit: int = 200) -> list[AuditLog]:
        return self.repository.list(action=action, resource_type=resource_type, status=status, limit=limit)

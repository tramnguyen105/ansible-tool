from __future__ import annotations

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models.audit import AuditLog


class AuditRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, entry: AuditLog) -> AuditLog:
        self.session.add(entry)
        self.session.flush()
        return entry

    def list(
        self,
        *,
        action: str | None = None,
        resource_type: str | None = None,
        status: str | None = None,
        limit: int = 200,
    ) -> list[AuditLog]:
        query = select(AuditLog)
        if action:
            query = query.where(AuditLog.action == action)
        if resource_type:
            query = query.where(AuditLog.resource_type == resource_type)
        if status:
            query = query.where(AuditLog.status == status)
        query = query.order_by(desc(AuditLog.created_at)).limit(limit)
        return list(self.session.scalars(query).all())

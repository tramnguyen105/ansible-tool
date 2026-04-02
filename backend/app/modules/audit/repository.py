from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session, selectinload

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
        resource_types: list[str] | None = None,
        statuses: list[str] | None = None,
        user_id: UUID | None = None,
        resource_id: str | None = None,
        message: str | None = None,
        created_from: datetime | None = None,
        created_to: datetime | None = None,
        limit: int = 200,
        offset: int = 0,
    ) -> tuple[list[AuditLog], int]:
        query = select(AuditLog).options(selectinload(AuditLog.user))
        count_query = select(func.count()).select_from(AuditLog)
        conditions = []
        if action:
            conditions.append(AuditLog.action.ilike(f'%{action.strip()}%'))
        if resource_types:
            conditions.append(AuditLog.resource_type.in_(resource_types))
        if statuses:
            conditions.append(AuditLog.status.in_(statuses))
        if user_id:
            conditions.append(AuditLog.user_id == user_id)
        if resource_id:
            conditions.append(AuditLog.resource_id.ilike(f'%{resource_id.strip()}%'))
        if message:
            conditions.append(AuditLog.message.ilike(f'%{message.strip()}%'))
        if created_from:
            conditions.append(AuditLog.created_at >= created_from)
        if created_to:
            conditions.append(AuditLog.created_at <= created_to)
        for condition in conditions:
            query = query.where(condition)
            count_query = count_query.where(condition)
        total = int(self.session.scalar(count_query) or 0)
        query = query.order_by(desc(AuditLog.created_at)).offset(offset).limit(limit)
        return list(self.session.scalars(query).all()), total

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import Integer, func, or_, select
from sqlalchemy.orm import Session

from app.models.jobs import JobSchedule


class ScheduleRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list(self) -> list[JobSchedule]:
        return list(self.session.scalars(select(JobSchedule).order_by(JobSchedule.name)).all())

    def list_filtered(
        self,
        *,
        search: str | None = None,
        enabled: bool | None = None,
        mode: str | None = None,
        limit: int = 25,
        offset: int = 0,
        sort_by: str = 'next_run_at',
        sort_order: str = 'asc',
    ) -> tuple[list[JobSchedule], int, dict]:
        filters = []
        if search:
            term = f'%{search.strip()}%'
            filters.append(or_(JobSchedule.name.ilike(term), JobSchedule.description.ilike(term)))
        if enabled is not None:
            filters.append(JobSchedule.enabled.is_(enabled))
        if mode == 'check':
            filters.append(JobSchedule.check_mode.is_(True))
        elif mode == 'live':
            filters.append(JobSchedule.check_mode.is_(False))

        sort_column = {
            'name': JobSchedule.name,
            'cron_expression': JobSchedule.cron_expression,
            'enabled': JobSchedule.enabled,
            'next_run_at': JobSchedule.next_run_at,
            'created_at': JobSchedule.created_at,
        }.get(sort_by, JobSchedule.next_run_at)
        order_column = sort_column.asc() if sort_order == 'asc' else sort_column.desc()

        items = list(
            self.session.scalars(
                select(JobSchedule)
                .where(*filters)
                .order_by(order_column, JobSchedule.name.asc())
                .limit(limit)
                .offset(offset)
            ).all()
        )
        total = self.session.scalar(select(func.count()).select_from(JobSchedule).where(*filters)) or 0
        summary_row = self.session.execute(
            select(
                func.count(JobSchedule.id).label('total'),
                func.sum(func.cast(JobSchedule.enabled, Integer)).label('enabled'),
                func.sum(func.cast(JobSchedule.check_mode, Integer)).label('check_mode'),
                func.min(JobSchedule.next_run_at).filter(JobSchedule.enabled.is_(True)).label('next_due_at'),
            ).where(*filters)
        ).one()
        summary = {
            'total': int(summary_row.total or 0),
            'enabled': int(summary_row.enabled or 0),
            'check_mode': int(summary_row.check_mode or 0),
            'next_due_at': summary_row.next_due_at,
        }
        return items, int(total), summary

    def get(self, schedule_id: UUID) -> JobSchedule | None:
        return self.session.get(JobSchedule, schedule_id)

    def get_by_name(self, name: str) -> JobSchedule | None:
        return self.session.scalar(select(JobSchedule).where(JobSchedule.name == name))

    def list_due(self, now: datetime) -> list[JobSchedule]:
        return list(
            self.session.scalars(
                select(JobSchedule).where(JobSchedule.enabled.is_(True), JobSchedule.next_run_at.is_not(None), JobSchedule.next_run_at <= now)
            ).all()
        )

    def add(self, schedule: JobSchedule) -> JobSchedule:
        self.session.add(schedule)
        self.session.flush()
        return schedule

    def delete(self, schedule: JobSchedule) -> None:
        self.session.delete(schedule)

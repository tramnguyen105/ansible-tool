from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.jobs import JobSchedule


class ScheduleRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list(self) -> list[JobSchedule]:
        return list(self.session.scalars(select(JobSchedule).order_by(JobSchedule.name)).all())

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

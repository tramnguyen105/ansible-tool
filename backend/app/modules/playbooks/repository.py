from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.content import Playbook
from app.models.jobs import Job, JobSchedule


class PlaybookRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list(self, *, is_generated: bool | None = None) -> list[Playbook]:
        stmt = select(Playbook).options(selectinload(Playbook.revisions))
        if is_generated is not None:
            stmt = stmt.where(Playbook.is_generated == is_generated)
        stmt = stmt.order_by(Playbook.updated_at.desc(), Playbook.name)
        return list(self.session.scalars(stmt).all())

    def get(self, playbook_id: UUID) -> Playbook | None:
        return self.session.scalar(select(Playbook).options(selectinload(Playbook.revisions)).where(Playbook.id == playbook_id))

    def get_by_name(self, name: str) -> Playbook | None:
        return self.session.scalar(select(Playbook).where(Playbook.name == name))

    def get_by_name_ci(self, name: str) -> Playbook | None:
        normalized = name.strip().lower()
        return self.session.scalar(select(Playbook).where(func.lower(Playbook.name) == normalized))

    def add(self, playbook: Playbook) -> Playbook:
        self.session.add(playbook)
        self.session.flush()
        return playbook

    def delete(self, playbook: Playbook) -> None:
        self.session.delete(playbook)

    def usage(self, playbook_id: UUID) -> dict[str, int]:
        counts = {
            'jobs_main': self._count_references(Job, Job.playbook_id, playbook_id),
            'jobs_pre_check': self._count_references(Job, Job.pre_check_playbook_id, playbook_id),
            'jobs_post_check': self._count_references(Job, Job.post_check_playbook_id, playbook_id),
            'schedules_main': self._count_references(JobSchedule, JobSchedule.playbook_id, playbook_id),
            'schedules_pre_check': self._count_references(JobSchedule, JobSchedule.pre_check_playbook_id, playbook_id),
            'schedules_post_check': self._count_references(JobSchedule, JobSchedule.post_check_playbook_id, playbook_id),
        }
        counts['total'] = sum(counts.values())
        return counts

    def _count_references(self, model, field, playbook_id: UUID) -> int:
        return int(self.session.scalar(select(func.count()).select_from(model).where(field == playbook_id)) or 0)

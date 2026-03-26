from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.content import Playbook
from app.models.credentials import Credential
from app.models.inventory import Inventory, InventoryGroup, InventoryGroupChild, InventoryGroupHost, InventoryHost
from app.models.jobs import Job, JobResult


class JobRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list(self) -> list[Job]:
        return list(
            self.session.scalars(
                select(Job)
                .options(selectinload(Job.result))
                .order_by(Job.created_at.desc())
            ).all()
        )

    def get(self, job_id: UUID) -> Job | None:
        return self.session.scalar(select(Job).options(selectinload(Job.result)).where(Job.id == job_id))

    def get_for_execution(self, job_id: UUID) -> Job | None:
        return self.session.scalar(
            select(Job)
            .where(Job.id == job_id)
            .options(
                selectinload(Job.result),
                selectinload(Job.inventory).selectinload(Inventory.hosts).selectinload(InventoryHost.group_links).selectinload(InventoryGroupHost.group),
                selectinload(Job.inventory).selectinload(Inventory.groups).selectinload(InventoryGroup.host_links).selectinload(InventoryGroupHost.host),
                selectinload(Job.inventory).selectinload(Inventory.groups).selectinload(InventoryGroup.child_links).selectinload(InventoryGroupChild.child_group),
                selectinload(Job.credential),
                selectinload(Job.playbook),
                selectinload(Job.pre_check_playbook),
                selectinload(Job.post_check_playbook),
            )
        )

    def add(self, job: Job) -> Job:
        self.session.add(job)
        self.session.flush()
        return job

    def ensure_result(self, job: Job) -> JobResult:
        if job.result is None:
            job.result = JobResult(job_id=job.id, stdout='', stderr='', summary_json={})
            self.session.add(job.result)
            self.session.flush()
        return job.result

from __future__ import annotations

from uuid import UUID

from sqlalchemy import case, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models.content import Playbook
from app.models.credentials import Credential
from app.models.inventory import Inventory, InventoryGroup, InventoryGroupChild, InventoryGroupHost, InventoryHost
from app.models.jobs import Job, JobResult, JobStatus


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

    def list_filtered(
        self,
        *,
        search: str | None = None,
        statuses: list[str] | None = None,
        mode: str | None = None,
        limit: int = 50,
        offset: int = 0,
        sort_by: str = 'created_at',
        sort_order: str = 'desc',
    ) -> tuple[list[Job], int]:
        filters = []
        if search:
            term = f'%{search.strip()}%'
            filters.append(or_(Job.name.ilike(term), Job.target_value.ilike(term), Job.target_type.ilike(term)))
        if statuses:
            normalized_statuses = [status for status in statuses if status in {item.value for item in JobStatus}]
            if normalized_statuses:
                filters.append(Job.status.in_(normalized_statuses))
        if mode == 'check':
            filters.append(Job.check_mode.is_(True))
        elif mode == 'live':
            filters.append(Job.check_mode.is_(False))

        base_query = select(Job).where(*filters)
        total = self.session.scalar(select(func.count()).select_from(base_query.subquery())) or 0
        summary_row = self.session.execute(
            select(
                func.sum(case((Job.status.in_([JobStatus.PENDING, JobStatus.QUEUED]), 1), else_=0)).label('queued'),
                func.sum(case((Job.status == JobStatus.RUNNING, 1), else_=0)).label('running'),
                func.sum(case((Job.status == JobStatus.SUCCESS, 1), else_=0)).label('success'),
                func.sum(case((Job.status == JobStatus.FAILED, 1), else_=0)).label('failed'),
                func.sum(case((Job.check_mode.is_(True), 1), else_=0)).label('check_mode'),
            ).select_from(Job).where(*filters)
        ).one()

        sort_column = {
            'name': Job.name,
            'status': Job.status,
            'target_type': Job.target_type,
            'created_at': Job.created_at,
        }.get(sort_by, Job.created_at)
        order_column = sort_column.asc() if sort_order == 'asc' else sort_column.desc()

        items = list(
            self.session.scalars(
                base_query
                .options(selectinload(Job.result))
                .order_by(order_column, Job.created_at.desc())
                .limit(limit)
                .offset(offset)
            ).all()
        )
        summary = {
            'queued': int(summary_row.queued or 0),
            'running': int(summary_row.running or 0),
            'success': int(summary_row.success or 0),
            'failed': int(summary_row.failed or 0),
            'check_mode': int(summary_row.check_mode or 0),
        }
        return items, int(total), summary

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

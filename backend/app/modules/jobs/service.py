from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import AppError
from app.models.content import Playbook
from app.models.credentials import Credential
from app.models.inventory import Inventory
from app.models.jobs import Job, JobStatus
from app.modules.audit.service import AuditService
from app.modules.jobs.repository import JobRepository
from app.modules.jobs.schemas import JobCreate, JobRead, JobResultRead


class JobService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.repository = JobRepository(session)
        self.audit = AuditService(session)

    def list(self) -> list[JobRead]:
        return [self._serialize(item) for item in self.repository.list()]

    def get(self, job_id: UUID) -> JobRead:
        job = self.repository.get(job_id)
        if job is None:
            raise AppError(404, 'JOB_NOT_FOUND', 'Job not found')
        return self._serialize(job)

    def create(self, payload: JobCreate, *, user_id: UUID | None = None) -> JobRead:
        self._validate_references(payload.inventory_id, payload.credential_id, payload.playbook_id, payload.pre_check_playbook_id, payload.post_check_playbook_id)
        job = Job(
            name=payload.name,
            status=JobStatus.PENDING,
            inventory_id=payload.inventory_id,
            credential_id=payload.credential_id,
            playbook_id=payload.playbook_id,
            target_type=payload.target_type,
            target_value=payload.target_value,
            extra_vars_json=payload.extra_vars,
            check_mode=payload.check_mode,
            pre_check_playbook_id=payload.pre_check_playbook_id,
            post_check_playbook_id=payload.post_check_playbook_id,
            pre_check_content=payload.pre_check_content,
            post_check_content=payload.post_check_content,
            requested_by_id=user_id,
        )
        self.repository.add(job)
        self.audit.record(
            action='job.create',
            resource_type='job',
            resource_id=str(job.id),
            message=f'Job {job.name} created',
            user_id=user_id,
            details={'execute_now': payload.execute_now},
        )
        self.session.commit()
        if payload.execute_now:
            return self.enqueue(job.id, user_id=user_id)
        return self.get(job.id)

    def enqueue(self, job_id: UUID, *, user_id: UUID | None = None) -> JobRead:
        job = self.repository.get(job_id)
        if job is None:
            raise AppError(404, 'JOB_NOT_FOUND', 'Job not found')
        if job.status == JobStatus.RUNNING:
            raise AppError(409, 'JOB_RUNNING', 'Job is already running')

        from app.modules.jobs.tasks import execute_job

        async_result = execute_job.delay(str(job.id))
        job.status = JobStatus.QUEUED
        job.celery_task_id = async_result.id
        self.audit.record(
            action='job.queue',
            resource_type='job',
            resource_id=str(job.id),
            message=f'Job {job.name} queued for execution',
            user_id=user_id,
        )
        self.session.commit()
        return self.get(job.id)

    def create_from_schedule(self, schedule, *, user_id: UUID | None = None) -> JobRead:
        payload = JobCreate(
            name=f'{schedule.name}-{schedule.next_run_at.isoformat() if schedule.next_run_at else "scheduled"}',
            inventory_id=schedule.inventory_id,
            credential_id=schedule.credential_id,
            playbook_id=schedule.playbook_id,
            target_type=schedule.target_type,
            target_value=schedule.target_value,
            extra_vars=schedule.extra_vars_json,
            check_mode=schedule.check_mode,
            pre_check_playbook_id=schedule.pre_check_playbook_id,
            post_check_playbook_id=schedule.post_check_playbook_id,
            pre_check_content=schedule.pre_check_content,
            post_check_content=schedule.post_check_content,
            execute_now=True,
        )
        job = Job(
            name=payload.name,
            status=JobStatus.PENDING,
            inventory_id=payload.inventory_id,
            credential_id=payload.credential_id,
            playbook_id=payload.playbook_id,
            target_type=payload.target_type,
            target_value=payload.target_value,
            extra_vars_json=payload.extra_vars,
            check_mode=payload.check_mode,
            pre_check_playbook_id=payload.pre_check_playbook_id,
            post_check_playbook_id=payload.post_check_playbook_id,
            pre_check_content=payload.pre_check_content,
            post_check_content=payload.post_check_content,
            requested_by_id=user_id or schedule.created_by_id,
            schedule_origin_id=schedule.id,
        )
        self.repository.add(job)
        self.session.commit()
        return self.enqueue(job.id, user_id=user_id or schedule.created_by_id)

    def _validate_references(
        self,
        inventory_id: UUID,
        credential_id: UUID,
        playbook_id: UUID,
        pre_check_playbook_id: UUID | None,
        post_check_playbook_id: UUID | None,
    ) -> None:
        if self.session.get(Inventory, inventory_id) is None:
            raise AppError(404, 'INVENTORY_NOT_FOUND', 'Inventory not found')
        credential = self.session.get(Credential, credential_id)
        if credential is None:
            raise AppError(404, 'CREDENTIAL_NOT_FOUND', 'Credential not found')
        if not credential.is_active:
            raise AppError(409, 'CREDENTIAL_INACTIVE', 'Credential is inactive')
        if self.session.get(Playbook, playbook_id) is None:
            raise AppError(404, 'PLAYBOOK_NOT_FOUND', 'Playbook not found')
        if pre_check_playbook_id and self.session.get(Playbook, pre_check_playbook_id) is None:
            raise AppError(404, 'PRECHECK_NOT_FOUND', 'Pre-check playbook not found')
        if post_check_playbook_id and self.session.get(Playbook, post_check_playbook_id) is None:
            raise AppError(404, 'POSTCHECK_NOT_FOUND', 'Post-check playbook not found')

    def _serialize(self, job: Job) -> JobRead:
        return JobRead(
            id=job.id,
            name=job.name,
            status=job.status.value,
            inventory_id=job.inventory_id,
            credential_id=job.credential_id,
            playbook_id=job.playbook_id,
            target_type=job.target_type,
            target_value=job.target_value,
            extra_vars_json=job.extra_vars_json,
            check_mode=job.check_mode,
            celery_task_id=job.celery_task_id,
            started_at=job.started_at,
            finished_at=job.finished_at,
            created_at=job.created_at,
            result=JobResultRead.model_validate(job.result) if job.result else None,
        )

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import JSON, Boolean, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.auth import User
    from app.models.content import Playbook
    from app.models.credentials import Credential
    from app.models.inventory import Inventory


class JobStatus(StrEnum):
    PENDING = 'pending'
    QUEUED = 'queued'
    RUNNING = 'running'
    SUCCESS = 'success'
    FAILED = 'failed'
    CANCELLED = 'cancelled'


class Job(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = 'jobs'

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[JobStatus] = mapped_column(Enum(JobStatus), default=JobStatus.PENDING, nullable=False, index=True)
    inventory_id: Mapped[UUID | None] = mapped_column(ForeignKey('inventories.id', ondelete='SET NULL'), nullable=True)
    credential_id: Mapped[UUID | None] = mapped_column(ForeignKey('credentials.id', ondelete='SET NULL'), nullable=True)
    playbook_id: Mapped[UUID | None] = mapped_column(ForeignKey('playbooks.id', ondelete='SET NULL'), nullable=True)
    target_type: Mapped[str] = mapped_column(String(32), default='all', nullable=False)
    target_value: Mapped[str | None] = mapped_column(String(255))
    extra_vars_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    check_mode: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    pre_check_playbook_id: Mapped[UUID | None] = mapped_column(ForeignKey('playbooks.id', ondelete='SET NULL'), nullable=True)
    post_check_playbook_id: Mapped[UUID | None] = mapped_column(ForeignKey('playbooks.id', ondelete='SET NULL'), nullable=True)
    pre_check_content: Mapped[str | None] = mapped_column(Text)
    post_check_content: Mapped[str | None] = mapped_column(Text)
    celery_task_id: Mapped[str | None] = mapped_column(String(255), index=True)
    requested_by_id: Mapped[UUID | None] = mapped_column(ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    schedule_origin_id: Mapped[UUID | None] = mapped_column(ForeignKey('job_schedules.id', ondelete='SET NULL'), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    inventory: Mapped['Inventory | None'] = relationship('Inventory', back_populates='jobs')
    credential: Mapped['Credential | None'] = relationship('Credential', back_populates='jobs')
    playbook: Mapped['Playbook | None'] = relationship('Playbook', back_populates='jobs', foreign_keys=[playbook_id])
    pre_check_playbook: Mapped['Playbook | None'] = relationship('Playbook', foreign_keys=[pre_check_playbook_id])
    post_check_playbook: Mapped['Playbook | None'] = relationship('Playbook', foreign_keys=[post_check_playbook_id])
    requested_by: Mapped['User | None'] = relationship('User', foreign_keys=[requested_by_id], back_populates='jobs_requested')
    result: Mapped['JobResult | None'] = relationship('JobResult', back_populates='job', cascade='all, delete-orphan', uselist=False)
    schedule_origin: Mapped['JobSchedule | None'] = relationship('JobSchedule', foreign_keys=[schedule_origin_id], back_populates='jobs')


class JobResult(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = 'job_results'

    job_id: Mapped[UUID] = mapped_column(ForeignKey('jobs.id', ondelete='CASCADE'), nullable=False, unique=True)
    return_code: Mapped[int | None] = mapped_column(Integer)
    stdout: Mapped[str] = mapped_column(Text, default='', nullable=False)
    stderr: Mapped[str] = mapped_column(Text, default='', nullable=False)
    summary_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    artifact_dir: Mapped[str | None] = mapped_column(String(255))

    job: Mapped[Job] = relationship('Job', back_populates='result')


class JobSchedule(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = 'job_schedules'

    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    cron_expression: Mapped[str] = mapped_column(String(64), nullable=False)
    timezone: Mapped[str] = mapped_column(String(64), default='UTC', nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    inventory_id: Mapped[UUID | None] = mapped_column(ForeignKey('inventories.id', ondelete='SET NULL'), nullable=True)
    credential_id: Mapped[UUID | None] = mapped_column(ForeignKey('credentials.id', ondelete='SET NULL'), nullable=True)
    playbook_id: Mapped[UUID | None] = mapped_column(ForeignKey('playbooks.id', ondelete='SET NULL'), nullable=True)
    target_type: Mapped[str] = mapped_column(String(32), default='all', nullable=False)
    target_value: Mapped[str | None] = mapped_column(String(255))
    extra_vars_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    check_mode: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    pre_check_playbook_id: Mapped[UUID | None] = mapped_column(ForeignKey('playbooks.id', ondelete='SET NULL'), nullable=True)
    post_check_playbook_id: Mapped[UUID | None] = mapped_column(ForeignKey('playbooks.id', ondelete='SET NULL'), nullable=True)
    pre_check_content: Mapped[str | None] = mapped_column(Text)
    post_check_content: Mapped[str | None] = mapped_column(Text)
    next_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_by_id: Mapped[UUID | None] = mapped_column(ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    updated_by_id: Mapped[UUID | None] = mapped_column(ForeignKey('users.id', ondelete='SET NULL'), nullable=True)

    inventory: Mapped['Inventory | None'] = relationship('Inventory', back_populates='schedules')
    credential: Mapped['Credential | None'] = relationship('Credential', back_populates='schedules')
    playbook: Mapped['Playbook | None'] = relationship('Playbook', back_populates='schedules', foreign_keys=[playbook_id])
    pre_check_playbook: Mapped['Playbook | None'] = relationship('Playbook', foreign_keys=[pre_check_playbook_id])
    post_check_playbook: Mapped['Playbook | None'] = relationship('Playbook', foreign_keys=[post_check_playbook_id])
    created_by: Mapped['User | None'] = relationship('User', foreign_keys=[created_by_id], back_populates='schedules_created')
    updated_by: Mapped['User | None'] = relationship('User', foreign_keys=[updated_by_id])
    jobs: Mapped[list[Job]] = relationship('Job', back_populates='schedule_origin')

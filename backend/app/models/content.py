from __future__ import annotations

from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import JSON, Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.auth import User
    from app.models.jobs import Job, JobSchedule


class Template(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = 'templates'

    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_by_id: Mapped[UUID | None] = mapped_column(ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    updated_by_id: Mapped[UUID | None] = mapped_column(ForeignKey('users.id', ondelete='SET NULL'), nullable=True)

    created_by: Mapped['User | None'] = relationship('User', foreign_keys=[created_by_id], back_populates='templates_created')
    updated_by: Mapped['User | None'] = relationship('User', foreign_keys=[updated_by_id])


class Playbook(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = 'playbooks'

    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    yaml_content: Mapped[str] = mapped_column(Text, nullable=False)
    is_generated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_by_id: Mapped[UUID | None] = mapped_column(ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    updated_by_id: Mapped[UUID | None] = mapped_column(ForeignKey('users.id', ondelete='SET NULL'), nullable=True)

    created_by: Mapped['User | None'] = relationship('User', foreign_keys=[created_by_id], back_populates='playbooks_created')
    updated_by: Mapped['User | None'] = relationship('User', foreign_keys=[updated_by_id])
    revisions: Mapped[list['PlaybookRevision']] = relationship(
        'PlaybookRevision',
        back_populates='playbook',
        cascade='all, delete-orphan',
        order_by='PlaybookRevision.version.desc()',
    )
    jobs: Mapped[list['Job']] = relationship('Job', back_populates='playbook', foreign_keys='Job.playbook_id')
    schedules: Mapped[list['JobSchedule']] = relationship('JobSchedule', back_populates='playbook', foreign_keys='JobSchedule.playbook_id')


class PlaybookRevision(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = 'playbook_revisions'

    playbook_id: Mapped[UUID] = mapped_column(ForeignKey('playbooks.id', ondelete='CASCADE'), nullable=False, index=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    yaml_content: Mapped[str] = mapped_column(Text, nullable=False)
    change_note: Mapped[str | None] = mapped_column(String(255))
    edited_by_id: Mapped[UUID | None] = mapped_column(ForeignKey('users.id', ondelete='SET NULL'), nullable=True)

    playbook: Mapped[Playbook] = relationship('Playbook', back_populates='revisions')
    edited_by: Mapped['User | None'] = relationship('User', foreign_keys=[edited_by_id])


class CliConversionJob(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = 'cli_conversion_jobs'

    output_type: Mapped[str] = mapped_column(String(32), nullable=False)
    input_config: Mapped[str] = mapped_column(Text, nullable=False)
    parsed_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    generated_content: Mapped[str] = mapped_column(Text, nullable=False)
    warnings_json: Mapped[list[Any]] = mapped_column(JSON, default=list, nullable=False)
    created_by_id: Mapped[UUID | None] = mapped_column(ForeignKey('users.id', ondelete='SET NULL'), nullable=True)

    created_by: Mapped['User | None'] = relationship('User', foreign_keys=[created_by_id])

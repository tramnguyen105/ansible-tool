from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.audit import AuditLog
    from app.models.content import Playbook, Template
    from app.models.credentials import Credential
    from app.models.jobs import Job, JobSchedule


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = 'users'

    username: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    display_name: Mapped[str | None] = mapped_column(String(255))
    email: Mapped[str | None] = mapped_column(String(255))
    ldap_dn: Mapped[str | None] = mapped_column(Text)
    auth_source: Mapped[str] = mapped_column(String(32), default='ldap', nullable=False)
    local_password_hash: Mapped[str | None] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    roles: Mapped[list['Role']] = relationship('Role', secondary='user_roles', back_populates='users')
    sessions: Mapped[list['AuthSession']] = relationship('AuthSession', back_populates='user', cascade='all, delete-orphan')
    audit_logs: Mapped[list['AuditLog']] = relationship('AuditLog', back_populates='user')
    credentials_created: Mapped[list['Credential']] = relationship('Credential', foreign_keys='Credential.created_by_id')
    templates_created: Mapped[list['Template']] = relationship('Template', foreign_keys='Template.created_by_id')
    playbooks_created: Mapped[list['Playbook']] = relationship('Playbook', foreign_keys='Playbook.created_by_id')
    jobs_requested: Mapped[list['Job']] = relationship('Job', foreign_keys='Job.requested_by_id')
    schedules_created: Mapped[list['JobSchedule']] = relationship('JobSchedule', foreign_keys='JobSchedule.created_by_id')


class Role(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = 'roles'

    name: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(255))

    users: Mapped[list[User]] = relationship('User', secondary='user_roles', back_populates='roles')


class UserRole(Base):
    __tablename__ = 'user_roles'
    __table_args__ = (UniqueConstraint('user_id', 'role_id', name='uq_user_roles_user_id_role_id'),)

    user_id: Mapped[UUID] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)
    role_id: Mapped[UUID] = mapped_column(ForeignKey('roles.id', ondelete='CASCADE'), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class AuthSession(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = 'auth_sessions'

    user_id: Mapped[UUID] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    csrf_token_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    ip_address: Mapped[str | None] = mapped_column(String(64))
    user_agent: Mapped[str | None] = mapped_column(Text)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user: Mapped[User] = relationship('User', back_populates='sessions')

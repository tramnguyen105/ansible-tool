from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Boolean, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.auth import User
    from app.models.jobs import Job, JobSchedule


class CredentialType(StrEnum):
    SSH_PASSWORD = 'ssh_password'
    SSH_PRIVATE_KEY = 'ssh_private_key'


class Credential(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = 'credentials'

    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    credential_type: Mapped[CredentialType] = mapped_column(Enum(CredentialType), nullable=False)
    username: Mapped[str] = mapped_column(String(255), nullable=False)
    encrypted_password: Mapped[str | None] = mapped_column(Text)
    encrypted_private_key: Mapped[str | None] = mapped_column(Text)
    encrypted_passphrase: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_by_id: Mapped[UUID | None] = mapped_column(ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    updated_by_id: Mapped[UUID | None] = mapped_column(ForeignKey('users.id', ondelete='SET NULL'), nullable=True)

    created_by: Mapped['User | None'] = relationship('User', foreign_keys=[created_by_id], back_populates='credentials_created')
    updated_by: Mapped['User | None'] = relationship('User', foreign_keys=[updated_by_id])
    jobs: Mapped[list['Job']] = relationship('Job', back_populates='credential')
    schedules: Mapped[list['JobSchedule']] = relationship('JobSchedule', back_populates='credential')

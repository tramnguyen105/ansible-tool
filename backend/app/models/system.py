from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.auth import User


class UserPreference(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = 'user_preferences'
    __table_args__ = (UniqueConstraint('user_id', name='uq_user_preferences_user_id'),)

    user_id: Mapped[UUID] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    timezone: Mapped[str] = mapped_column(String(64), default='UTC', nullable=False)
    date_format: Mapped[str] = mapped_column(String(32), default='YYYY-MM-DD', nullable=False)
    time_format: Mapped[str] = mapped_column(String(16), default='24h', nullable=False)
    auto_refresh_seconds: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    show_relative_time: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    user: Mapped['User'] = relationship('User')


class SystemConfiguration(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = 'system_configuration'
    __table_args__ = (UniqueConstraint('singleton_key', name='uq_system_configuration_singleton_key'),)

    singleton_key: Mapped[str] = mapped_column(String(32), default='default', nullable=False)

    ldap_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    ldap_server_uri: Mapped[str] = mapped_column(String(255), default='ldap://ldap.example.internal', nullable=False)
    ldap_use_ssl: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    ldap_bind_dn: Mapped[str | None] = mapped_column(String(255))
    ldap_search_base: Mapped[str | None] = mapped_column(String(255))
    ldap_search_filter: Mapped[str] = mapped_column(String(255), default='(sAMAccountName={username})', nullable=False)
    ldap_username_attribute: Mapped[str] = mapped_column(String(64), default='sAMAccountName', nullable=False)
    ldap_user_dn_template: Mapped[str | None] = mapped_column(String(255))
    allow_local_auth: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    password_reset_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    password_reset_token_ttl_minutes: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    password_min_length: Mapped[int] = mapped_column(Integer, default=12, nullable=False)
    password_require_special: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    snmp_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    snmp_version: Mapped[str] = mapped_column(String(16), default='v2c', nullable=False)
    snmp_default_port: Mapped[int] = mapped_column(Integer, default=161, nullable=False)
    snmp_timeout_seconds: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    snmp_retries: Mapped[int] = mapped_column(Integer, default=2, nullable=False)
    snmp_trap_target: Mapped[str | None] = mapped_column(String(255))


class AuthLoginThrottle(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = 'auth_login_throttles'
    __table_args__ = (UniqueConstraint('subject_key', name='uq_auth_login_throttles_subject_key'),)

    subject_key: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    attempt_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    window_started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_attempt_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class InventoryImportPreviewToken(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = 'inventory_import_preview_tokens'
    __table_args__ = (UniqueConstraint('preview_id', name='uq_inventory_import_preview_tokens_preview_id'),)

    preview_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    checksum: Mapped[str] = mapped_column(String(64), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    payload_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

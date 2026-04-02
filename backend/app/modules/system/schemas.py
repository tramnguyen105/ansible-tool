from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class SystemWarningRead(BaseModel):
    severity: str
    code: str
    message: str
    recommendation: str


class SystemRuntimeRead(BaseModel):
    app_name: str
    environment: str
    api_prefix: str
    log_level: str


class SystemAuthRead(BaseModel):
    ldap_enabled: bool
    allow_local_auth: bool
    cookie_secure: bool
    cookie_domain_set: bool
    session_ttl_minutes: int
    session_cookie_name: str
    csrf_cookie_name: str


class SystemNetworkRead(BaseModel):
    cors_origin_count: int
    cors_origins_preview: list[str]


class SystemExecutionRead(BaseModel):
    runner_data_dir: str
    artifact_retention_days: int


class SystemIntegrationsRead(BaseModel):
    database_host: str
    database_driver: str
    redis_host: str
    redis_db: int


class SystemHealthRead(BaseModel):
    db_ready: bool
    redis_ready: bool
    runner_path_writable: bool
    celery_worker_online: bool
    db_detail: str | None = None
    redis_detail: str | None = None
    runner_detail: str | None = None
    celery_detail: str | None = None


class UserPreferencesRead(BaseModel):
    timezone: str
    date_format: str
    time_format: str
    auto_refresh_seconds: int
    show_relative_time: bool


class UserPreferencesUpdate(BaseModel):
    timezone: str | None = Field(default=None, min_length=2, max_length=64)
    date_format: str | None = Field(default=None, min_length=2, max_length=32)
    time_format: str | None = Field(default=None, pattern='^(12h|24h)$')
    auto_refresh_seconds: int | None = Field(default=None, ge=5, le=3600)
    show_relative_time: bool | None = None


class LdapSettingsRead(BaseModel):
    enabled: bool
    server_uri: str
    use_ssl: bool
    bind_dn: str | None
    search_base: str | None
    search_filter: str
    username_attribute: str
    user_dn_template: str | None
    allow_local_auth: bool


class LdapSettingsUpdate(BaseModel):
    enabled: bool | None = None
    server_uri: str | None = Field(default=None, min_length=8, max_length=255)
    use_ssl: bool | None = None
    bind_dn: str | None = Field(default=None, max_length=255)
    search_base: str | None = Field(default=None, max_length=255)
    search_filter: str | None = Field(default=None, min_length=3, max_length=255)
    username_attribute: str | None = Field(default=None, min_length=1, max_length=64)
    user_dn_template: str | None = Field(default=None, max_length=255)
    allow_local_auth: bool | None = None


class PasswordResetSettingsRead(BaseModel):
    enabled: bool
    token_ttl_minutes: int
    min_length: int
    require_special: bool


class PasswordResetSettingsUpdate(BaseModel):
    enabled: bool | None = None
    token_ttl_minutes: int | None = Field(default=None, ge=5, le=1440)
    min_length: int | None = Field(default=None, ge=8, le=128)
    require_special: bool | None = None


class SnmpSettingsRead(BaseModel):
    enabled: bool
    version: str
    default_port: int
    timeout_seconds: int
    retries: int
    trap_target: str | None


class SnmpSettingsUpdate(BaseModel):
    enabled: bool | None = None
    version: str | None = Field(default=None, pattern='^(v1|v2c|v3)$')
    default_port: int | None = Field(default=None, ge=1, le=65535)
    timeout_seconds: int | None = Field(default=None, ge=1, le=30)
    retries: int | None = Field(default=None, ge=0, le=10)
    trap_target: str | None = Field(default=None, max_length=255)


class SystemWideSettingsRead(BaseModel):
    ldap: LdapSettingsRead
    password_reset: PasswordResetSettingsRead
    snmp: SnmpSettingsRead


class SystemWideSettingsUpdate(BaseModel):
    ldap: LdapSettingsUpdate | None = None
    password_reset: PasswordResetSettingsUpdate | None = None
    snmp: SnmpSettingsUpdate | None = None


class SystemSettingsRead(BaseModel):
    # Legacy top-level fields retained for current frontend compatibility.
    app_name: str
    environment: str
    ldap_enabled: bool
    allow_local_auth: bool
    session_ttl_minutes: int

    generated_at: datetime
    risk_level: str
    warnings: list[SystemWarningRead]
    runtime: SystemRuntimeRead
    auth: SystemAuthRead
    network: SystemNetworkRead
    execution: SystemExecutionRead
    integrations: SystemIntegrationsRead
    health: SystemHealthRead

    user_preferences: UserPreferencesRead
    system_wide: SystemWideSettingsRead

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    app_name: str = 'Ansible Automation Console'
    app_env: Literal['development', 'test', 'production'] = 'development'
    app_host: str = '0.0.0.0'
    app_port: int = 8000
    api_prefix: str = '/api/v1'

    database_url: str = 'postgresql+psycopg://ansible_tool:change_me@127.0.0.1:5432/ansible_tool'
    redis_url: str = 'redis://127.0.0.1:6379/0'
    log_level: str = 'INFO'
    cors_origins: str = 'http://localhost:5173'

    cookie_secure: bool = False
    cookie_domain: str | None = None
    session_cookie_name: str = 'ansible_tool_session'
    csrf_cookie_name: str = 'ansible_tool_csrf'
    session_ttl_minutes: int = 480

    fernet_key: str = Field(default='replace_with_generated_fernet_key', alias='FERNET_KEY')
    runner_data_dir: str = '/var/lib/ansible-tool/runner'
    artifact_retention_days: int = 30

    ldap_enabled: bool = True
    ldap_server_uri: str = 'ldap://ldap.example.internal'
    ldap_use_ssl: bool = False
    ldap_bind_dn: str | None = None
    ldap_bind_password: str | None = None
    ldap_search_base: str | None = None
    ldap_search_filter: str = '(sAMAccountName={username})'
    ldap_username_attribute: str = 'sAMAccountName'
    ldap_user_dn_template: str | None = None

    allow_local_auth: bool = True
    local_admin_username: str = 'admin'
    local_admin_password: str = 'ChangeMe123!'
    auto_create_db: bool = False

    @computed_field  # type: ignore[misc]
    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(',') if origin.strip()]

    @computed_field  # type: ignore[misc]
    @property
    def runner_data_path(self) -> Path:
        return Path(self.runner_data_dir)


@lru_cache
def get_settings() -> Settings:
    return Settings()

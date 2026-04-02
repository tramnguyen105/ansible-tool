from __future__ import annotations

import socket
from datetime import datetime, timezone
from tempfile import NamedTemporaryFile
from urllib.parse import urlparse

from fastapi import APIRouter, Depends
from sqlalchemy import select, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from app.api.deps import AuthContext, get_db, require_admin, require_csrf
from app.core.config import get_settings
from app.core.exceptions import AppError
from app.models.system import SystemConfiguration, UserPreference
from app.modules.audit.service import AuditService
from app.modules.audit.router import router as audit_router
from app.modules.auth.router import router as auth_router
from app.modules.cli_converter.router import router as cli_converter_router
from app.modules.credentials.router import router as credentials_router
from app.modules.inventory.router import router as inventory_router
from app.modules.jobs.router import router as jobs_router
from app.modules.playbooks.router import router as playbooks_router
from app.modules.schedules.router import router as schedules_router
from app.modules.system.schemas import (
    SystemAuthRead,
    SystemExecutionRead,
    SystemHealthRead,
    SystemIntegrationsRead,
    SystemWideSettingsRead,
    SystemWideSettingsUpdate,
    UserPreferencesRead,
    UserPreferencesUpdate,
    SystemNetworkRead,
    SystemRuntimeRead,
    SystemSettingsRead,
    SystemWarningRead,
)
from app.modules.templates.router import router as templates_router
from app.modules.users.router import router as users_router
from app.schemas.common import ApiResponse, HealthPayload


settings = get_settings()
router = APIRouter()


@router.get('/health', response_model=ApiResponse[HealthPayload], tags=['system'])
def health() -> ApiResponse[HealthPayload]:
    return ApiResponse(
        data=HealthPayload(status='ok', app=settings.app_name, environment=settings.app_env),
    )


@router.get('/system/settings', response_model=ApiResponse[SystemSettingsRead], tags=['system'])
def get_system_settings(auth: AuthContext = Depends(require_admin), db: Session = Depends(get_db)) -> ApiResponse[SystemSettingsRead]:
    system_config = _get_or_create_system_configuration(db)
    user_preferences = _get_or_create_user_preferences(db, auth.user.id)
    db_ready, db_detail = _check_db(db)
    redis_ready, redis_detail = _check_redis()
    runner_writable, runner_detail = _check_runner_path()
    celery_online, celery_detail = _check_celery()
    warning_items = _build_warnings(
        ldap_enabled=system_config.ldap_enabled,
        allow_local_auth=system_config.allow_local_auth,
        db_ready=db_ready,
        redis_ready=redis_ready,
        runner_writable=runner_writable,
        celery_online=celery_online,
    )
    risk_level = _compute_risk_level(warning_items)
    payload = SystemSettingsRead(
        app_name=settings.app_name,
        environment=settings.app_env,
        ldap_enabled=system_config.ldap_enabled,
        allow_local_auth=system_config.allow_local_auth,
        session_ttl_minutes=settings.session_ttl_minutes,
        generated_at=datetime.now(timezone.utc),
        risk_level=risk_level,
        warnings=warning_items,
        runtime=SystemRuntimeRead(
            app_name=settings.app_name,
            environment=settings.app_env,
            api_prefix=settings.api_prefix,
            log_level=settings.log_level,
        ),
        auth=SystemAuthRead(
            ldap_enabled=system_config.ldap_enabled,
            allow_local_auth=system_config.allow_local_auth,
            cookie_secure=settings.cookie_secure,
            cookie_domain_set=bool(settings.cookie_domain),
            session_ttl_minutes=settings.session_ttl_minutes,
            session_cookie_name=settings.session_cookie_name,
            csrf_cookie_name=settings.csrf_cookie_name,
        ),
        network=SystemNetworkRead(
            cors_origin_count=len(settings.cors_origin_list),
            cors_origins_preview=settings.cors_origin_list[:5],
        ),
        execution=SystemExecutionRead(
            runner_data_dir=str(settings.runner_data_path),
            artifact_retention_days=settings.artifact_retention_days,
        ),
        integrations=SystemIntegrationsRead(
            database_host=_database_host(),
            database_driver=_database_driver(),
            redis_host=_redis_host(),
            redis_db=_redis_db(),
        ),
        health=SystemHealthRead(
            db_ready=db_ready,
            redis_ready=redis_ready,
            runner_path_writable=runner_writable,
            celery_worker_online=celery_online,
            db_detail=db_detail,
            redis_detail=redis_detail,
            runner_detail=runner_detail,
            celery_detail=celery_detail,
        ),
        user_preferences=UserPreferencesRead(
            timezone=user_preferences.timezone,
            date_format=user_preferences.date_format,
            time_format=user_preferences.time_format,
            auto_refresh_seconds=user_preferences.auto_refresh_seconds,
            show_relative_time=user_preferences.show_relative_time,
        ),
        system_wide=_serialize_system_wide_settings(system_config),
    )
    AuditService(db).record(
        action='settings.read',
        resource_type='system',
        resource_id='runtime',
        message='System settings posture viewed',
        user_id=auth.user.id,
        details={'risk_level': risk_level, 'warning_count': len(warning_items)},
    )
    db.commit()
    return ApiResponse(data=payload)


@router.put('/system/settings/user-preferences', response_model=ApiResponse[UserPreferencesRead], tags=['system'], dependencies=[Depends(require_csrf)])
def update_user_preferences(
    payload: UserPreferencesUpdate,
    auth: AuthContext = Depends(require_admin),
    db: Session = Depends(get_db),
) -> ApiResponse[UserPreferencesRead]:
    preferences = _get_or_create_user_preferences(db, auth.user.id)
    updates = payload.model_dump(exclude_unset=True)
    for field_name, value in updates.items():
        setattr(preferences, field_name, value)
    db.flush()
    AuditService(db).record(
        action='settings.user_preferences.updated',
        resource_type='system',
        resource_id=str(auth.user.id),
        message=f'User preferences updated for {auth.user.username}',
        user_id=auth.user.id,
        details={'updated_fields': sorted(updates.keys())},
    )
    db.commit()
    return ApiResponse(
        message='User preferences saved',
        data=UserPreferencesRead(
            timezone=preferences.timezone,
            date_format=preferences.date_format,
            time_format=preferences.time_format,
            auto_refresh_seconds=preferences.auto_refresh_seconds,
            show_relative_time=preferences.show_relative_time,
        ),
    )


@router.put('/system/settings/system-wide', response_model=ApiResponse[SystemWideSettingsRead], tags=['system'], dependencies=[Depends(require_csrf)])
def update_system_wide_settings(
    payload: SystemWideSettingsUpdate,
    auth: AuthContext = Depends(require_admin),
    db: Session = Depends(get_db),
) -> ApiResponse[SystemWideSettingsRead]:
    system_config = _get_or_create_system_configuration(db)
    changed_fields: list[str] = []

    if payload.ldap:
        ldap_updates = payload.ldap.model_dump(exclude_unset=True)
        field_map = {
            'enabled': 'ldap_enabled',
            'server_uri': 'ldap_server_uri',
            'use_ssl': 'ldap_use_ssl',
            'bind_dn': 'ldap_bind_dn',
            'search_base': 'ldap_search_base',
            'search_filter': 'ldap_search_filter',
            'username_attribute': 'ldap_username_attribute',
            'user_dn_template': 'ldap_user_dn_template',
            'allow_local_auth': 'allow_local_auth',
        }
        for key, value in ldap_updates.items():
            setattr(system_config, field_map[key], value)
            changed_fields.append(f'ldap.{key}')

    if payload.password_reset:
        password_updates = payload.password_reset.model_dump(exclude_unset=True)
        field_map = {
            'enabled': 'password_reset_enabled',
            'token_ttl_minutes': 'password_reset_token_ttl_minutes',
            'min_length': 'password_min_length',
            'require_special': 'password_require_special',
        }
        for key, value in password_updates.items():
            setattr(system_config, field_map[key], value)
            changed_fields.append(f'password_reset.{key}')

    if payload.snmp:
        snmp_updates = payload.snmp.model_dump(exclude_unset=True)
        field_map = {
            'enabled': 'snmp_enabled',
            'version': 'snmp_version',
            'default_port': 'snmp_default_port',
            'timeout_seconds': 'snmp_timeout_seconds',
            'retries': 'snmp_retries',
            'trap_target': 'snmp_trap_target',
        }
        for key, value in snmp_updates.items():
            setattr(system_config, field_map[key], value)
            changed_fields.append(f'snmp.{key}')

    if system_config.ldap_enabled and not system_config.ldap_server_uri.strip():
        raise AppError(400, 'SETTINGS_INVALID', 'LDAP server URI is required when LDAP is enabled')
    if system_config.password_reset_enabled and system_config.password_min_length < 8:
        raise AppError(400, 'SETTINGS_INVALID', 'Password minimum length must be at least 8 when password reset is enabled')

    db.flush()
    AuditService(db).record(
        action='settings.system_wide.updated',
        resource_type='system',
        resource_id='default',
        message='System-wide settings updated',
        user_id=auth.user.id,
        details={'updated_fields': sorted(changed_fields)},
    )
    db.commit()
    return ApiResponse(message='System-wide settings saved', data=_serialize_system_wide_settings(system_config))


def _get_or_create_system_configuration(db: Session) -> SystemConfiguration:
    system_config = db.scalar(select(SystemConfiguration).where(SystemConfiguration.singleton_key == 'default'))
    if system_config is None:
        system_config = SystemConfiguration(
            singleton_key='default',
            ldap_enabled=settings.ldap_enabled,
            ldap_server_uri=settings.ldap_server_uri,
            ldap_use_ssl=settings.ldap_use_ssl,
            ldap_bind_dn=settings.ldap_bind_dn,
            ldap_search_base=settings.ldap_search_base,
            ldap_search_filter=settings.ldap_search_filter,
            ldap_username_attribute=settings.ldap_username_attribute,
            ldap_user_dn_template=settings.ldap_user_dn_template,
            allow_local_auth=settings.allow_local_auth,
            password_reset_enabled=False,
            password_reset_token_ttl_minutes=30,
            password_min_length=12,
            password_require_special=True,
            snmp_enabled=False,
            snmp_version='v2c',
            snmp_default_port=161,
            snmp_timeout_seconds=3,
            snmp_retries=2,
            snmp_trap_target=None,
        )
        db.add(system_config)
        db.flush()
    return system_config


def _get_or_create_user_preferences(db: Session, user_id) -> UserPreference:
    preferences = db.scalar(select(UserPreference).where(UserPreference.user_id == user_id))
    if preferences is None:
        preferences = UserPreference(
            user_id=user_id,
            timezone='UTC',
            date_format='YYYY-MM-DD',
            time_format='24h',
            auto_refresh_seconds=30,
            show_relative_time=True,
        )
        db.add(preferences)
        db.flush()
    return preferences


def _serialize_system_wide_settings(system_config: SystemConfiguration) -> SystemWideSettingsRead:
    return SystemWideSettingsRead(
        ldap={
            'enabled': system_config.ldap_enabled,
            'server_uri': system_config.ldap_server_uri,
            'use_ssl': system_config.ldap_use_ssl,
            'bind_dn': system_config.ldap_bind_dn,
            'search_base': system_config.ldap_search_base,
            'search_filter': system_config.ldap_search_filter,
            'username_attribute': system_config.ldap_username_attribute,
            'user_dn_template': system_config.ldap_user_dn_template,
            'allow_local_auth': system_config.allow_local_auth,
        },
        password_reset={
            'enabled': system_config.password_reset_enabled,
            'token_ttl_minutes': system_config.password_reset_token_ttl_minutes,
            'min_length': system_config.password_min_length,
            'require_special': system_config.password_require_special,
        },
        snmp={
            'enabled': system_config.snmp_enabled,
            'version': system_config.snmp_version,
            'default_port': system_config.snmp_default_port,
            'timeout_seconds': system_config.snmp_timeout_seconds,
            'retries': system_config.snmp_retries,
            'trap_target': system_config.snmp_trap_target,
        },
    )


def _check_db(db: Session) -> tuple[bool, str | None]:
    try:
        db.execute(text('SELECT 1'))
        return True, 'Database connection healthy'
    except Exception as exc:  # pragma: no cover - runtime defensive path
        return False, str(exc)


def _check_redis() -> tuple[bool, str | None]:
    try:
        from redis import Redis  # type: ignore

        client = Redis.from_url(settings.redis_url, socket_connect_timeout=1, socket_timeout=1)
        if client.ping():
            return True, 'Redis ping successful'
        return False, 'Redis ping returned false'
    except Exception:
        try:
            parsed = urlparse(settings.redis_url)
            host = parsed.hostname or '127.0.0.1'
            port = parsed.port or 6379
            with socket.create_connection((host, port), timeout=1):
                return True, 'Redis TCP reachable'
        except Exception as exc:  # pragma: no cover - runtime defensive path
            return False, str(exc)


def _check_runner_path() -> tuple[bool, str | None]:
    try:
        path = settings.runner_data_path
        path.mkdir(parents=True, exist_ok=True)
        with NamedTemporaryFile(mode='w', delete=True, dir=path) as handle:
            handle.write('ok')
            handle.flush()
        return True, f'Runner path writable: {path}'
    except Exception as exc:  # pragma: no cover - runtime defensive path
        return False, str(exc)


def _check_celery() -> tuple[bool, str | None]:
    try:
        from app.celery_app import celery_app

        inspector = celery_app.control.inspect(timeout=1)
        responses = inspector.ping() or {}
        if responses:
            return True, f'{len(responses)} worker(s) online'
        return False, 'No celery workers responded to ping'
    except Exception as exc:  # pragma: no cover - runtime defensive path
        return False, str(exc)


def _database_host() -> str:
    try:
        return make_url(settings.database_url).host or 'unknown'
    except Exception:
        return 'unknown'


def _database_driver() -> str:
    try:
        return make_url(settings.database_url).drivername
    except Exception:
        return 'unknown'


def _redis_host() -> str:
    parsed = urlparse(settings.redis_url)
    return parsed.hostname or 'unknown'


def _redis_db() -> int:
    parsed = urlparse(settings.redis_url)
    try:
        return int((parsed.path or '/0').strip('/') or '0')
    except ValueError:
        return 0


def _build_warnings(
    *,
    ldap_enabled: bool,
    allow_local_auth: bool,
    db_ready: bool,
    redis_ready: bool,
    runner_writable: bool,
    celery_online: bool,
) -> list[SystemWarningRead]:
    warnings: list[SystemWarningRead] = []
    is_prod = settings.app_env == 'production'

    if is_prod and allow_local_auth:
        warnings.append(
            SystemWarningRead(
                severity='high',
                code='LOCAL_AUTH_IN_PROD',
                message='Local authentication is enabled in production.',
                recommendation='Disable local auth and require LDAP for production sign-in.',
            )
        )
    if is_prod and not ldap_enabled:
        warnings.append(
            SystemWarningRead(
                severity='high',
                code='LDAP_DISABLED_IN_PROD',
                message='LDAP authentication is disabled in production.',
                recommendation='Enable LDAP to centralize identity and reduce local account drift.',
            )
        )
    if is_prod and not settings.cookie_secure:
        warnings.append(
            SystemWarningRead(
                severity='high',
                code='COOKIE_SECURE_DISABLED',
                message='Secure cookies are disabled in production.',
                recommendation='Set COOKIE_SECURE=true to prevent cookie transport over plaintext HTTP.',
            )
        )
    if settings.fernet_key == 'replace_with_generated_fernet_key':
        warnings.append(
            SystemWarningRead(
                severity='high',
                code='DEFAULT_FERNET_KEY',
                message='FERNET key is using the default placeholder value.',
                recommendation='Set a generated Fernet key before production usage.',
            )
        )
    if settings.local_admin_password == 'ChangeMe123!':
        warnings.append(
            SystemWarningRead(
                severity='high',
                code='DEFAULT_LOCAL_ADMIN_PASSWORD',
                message='Local admin password appears to be the default value.',
                recommendation='Rotate LOCAL_ADMIN_PASSWORD to a strong unique secret.',
            )
        )
    if is_prod and any('localhost' in origin or '127.0.0.1' in origin for origin in settings.cors_origin_list):
        warnings.append(
            SystemWarningRead(
                severity='medium',
                code='LOCALHOST_CORS_IN_PROD',
                message='CORS includes localhost origins in production.',
                recommendation='Restrict CORS origins to trusted production frontend domains.',
            )
        )
    if settings.session_ttl_minutes > 720:
        warnings.append(
            SystemWarningRead(
                severity='medium',
                code='LONG_SESSION_TTL',
                message='Session TTL exceeds 12 hours.',
                recommendation='Reduce session TTL to limit impact of leaked session cookies.',
            )
        )
    if not db_ready:
        warnings.append(
            SystemWarningRead(
                severity='high',
                code='DATABASE_UNREACHABLE',
                message='Database health check failed.',
                recommendation='Verify database availability and connection settings.',
            )
        )
    if not redis_ready:
        warnings.append(
            SystemWarningRead(
                severity='high',
                code='REDIS_UNREACHABLE',
                message='Redis health check failed.',
                recommendation='Verify Redis availability and connection settings.',
            )
        )
    if not runner_writable:
        warnings.append(
            SystemWarningRead(
                severity='high',
                code='RUNNER_PATH_UNWRITABLE',
                message='Runner data directory is not writable.',
                recommendation='Fix filesystem permissions for RUNNER_DATA_DIR.',
            )
        )
    if not celery_online:
        warnings.append(
            SystemWarningRead(
                severity='medium',
                code='CELERY_WORKER_OFFLINE',
                message='No celery workers responded to ping.',
                recommendation='Start workers so jobs and schedules can execute.',
            )
        )
    return warnings


def _compute_risk_level(warnings: list[SystemWarningRead]) -> str:
    if any(item.severity == 'high' for item in warnings):
        return 'high'
    if any(item.severity == 'medium' for item in warnings):
        return 'medium'
    return 'low'


router.include_router(auth_router)
router.include_router(audit_router)
router.include_router(users_router)
router.include_router(inventory_router)
router.include_router(credentials_router)
router.include_router(templates_router)
router.include_router(playbooks_router)
router.include_router(cli_converter_router)
router.include_router(jobs_router)
router.include_router(schedules_router)

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from ldap3 import ALL, Connection, Server
from ldap3.core.exceptions import LDAPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import AppError
from app.core.security import build_session_expiry, generate_token, hash_password, hash_token, verify_password
from app.models.auth import AuthSession, User
from app.models.system import SystemConfiguration
from app.modules.audit.service import AuditService
from app.modules.auth.repository import AuthRepository


settings = get_settings()


@dataclass
class RequestContext:
    ip_address: str | None
    user_agent: str | None


@dataclass
class LoginResult:
    user: User
    session: AuthSession
    session_token: str
    csrf_token: str


class AuthService:
    _max_attempts = 5
    _window_minutes = 10

    def __init__(self, session: Session) -> None:
        self.session = session
        self.repository = AuthRepository(session)
        self.audit = AuditService(session)

    @staticmethod
    def _throttle_key(username: str) -> str:
        return username.strip().lower()

    def _ensure_not_rate_limited(self, username: str) -> None:
        key = self._throttle_key(username)
        now = datetime.now(timezone.utc)
        window_start = now - timedelta(minutes=self._window_minutes)
        throttle = self.repository.get_login_throttle(key)
        if throttle is None:
            return
        if throttle.last_attempt_at < window_start:
            self.repository.delete_login_throttle(key)
            return
        if throttle.attempt_count >= self._max_attempts:
            raise AppError(429, 'AUTH_RATE_LIMITED', 'Too many failed login attempts. Please wait and try again.')

    def _record_failed_attempt(self, username: str) -> None:
        key = self._throttle_key(username)
        now = datetime.now(timezone.utc)
        window_start = now - timedelta(minutes=self._window_minutes)
        throttle = self.repository.get_login_throttle(key)
        if throttle is None or throttle.last_attempt_at < window_start:
            self.repository.upsert_login_throttle(
                subject_key=key,
                attempt_count=1,
                window_started_at=now,
                last_attempt_at=now,
            )
        else:
            self.repository.upsert_login_throttle(
                subject_key=key,
                attempt_count=throttle.attempt_count + 1,
                window_started_at=throttle.window_started_at,
                last_attempt_at=now,
            )
        self.session.commit()

    def _clear_failed_attempts(self, username: str) -> None:
        self.repository.delete_login_throttle(self._throttle_key(username))

    def _effective_auth_config(self) -> dict[str, Any]:
        config = self.session.scalar(select(SystemConfiguration).where(SystemConfiguration.singleton_key == 'default'))
        if config is None:
            return {
                'ldap_enabled': settings.ldap_enabled,
                'allow_local_auth': settings.allow_local_auth,
                'ldap_server_uri': settings.ldap_server_uri,
                'ldap_use_ssl': settings.ldap_use_ssl,
                'ldap_bind_dn': settings.ldap_bind_dn,
                'ldap_search_base': settings.ldap_search_base,
                'ldap_search_filter': settings.ldap_search_filter,
                'ldap_username_attribute': settings.ldap_username_attribute,
                'ldap_user_dn_template': settings.ldap_user_dn_template,
            }
        return {
            'ldap_enabled': config.ldap_enabled,
            'allow_local_auth': config.allow_local_auth,
            'ldap_server_uri': config.ldap_server_uri,
            'ldap_use_ssl': config.ldap_use_ssl,
            'ldap_bind_dn': config.ldap_bind_dn,
            'ldap_search_base': config.ldap_search_base,
            'ldap_search_filter': config.ldap_search_filter,
            'ldap_username_attribute': config.ldap_username_attribute,
            'ldap_user_dn_template': config.ldap_user_dn_template,
        }

    def auth_modes(self) -> dict[str, bool]:
        auth_config = self._effective_auth_config()
        return {
            'ldap_enabled': bool(auth_config['ldap_enabled']),
            'allow_local_auth': bool(auth_config['allow_local_auth']),
        }

    def _ldap_authenticate(self, username: str, password: str, auth_config: dict[str, Any]) -> dict[str, Any]:
        server = Server(auth_config['ldap_server_uri'], get_info=ALL, use_ssl=auth_config['ldap_use_ssl'])

        bind_user = auth_config.get('ldap_bind_dn')
        bind_password = settings.ldap_bind_password
        found_dn: str | None = None
        attributes: dict[str, Any] = {}

        if auth_config.get('ldap_user_dn_template'):
            found_dn = auth_config['ldap_user_dn_template'].format(username=username)
        elif bind_user and bind_password and auth_config.get('ldap_search_base'):
            with Connection(server, user=bind_user, password=bind_password, auto_bind=True) as conn:
                search_filter = auth_config['ldap_search_filter'].format(username=username)
                conn.search(
                    search_base=auth_config['ldap_search_base'],
                    search_filter=search_filter,
                    attributes=['displayName', 'mail', auth_config['ldap_username_attribute']],
                )
                if not conn.entries:
                    raise AppError(401, 'AUTH_INVALID', 'Invalid username or password')
                entry = conn.entries[0]
                found_dn = entry.entry_dn
                attributes = {
                    'display_name': getattr(entry, 'displayName', None).value if hasattr(entry, 'displayName') else username,
                    'email': getattr(entry, 'mail', None).value if hasattr(entry, 'mail') else None,
                }
        else:
            raise AppError(500, 'LDAP_CONFIG_INVALID', 'LDAP configuration is incomplete')

        if not found_dn:
            raise AppError(401, 'AUTH_INVALID', 'Invalid username or password')

        try:
            with Connection(server, user=found_dn, password=password, auto_bind=True):
                return {
                    'username': username,
                    'display_name': attributes.get('display_name') or username,
                    'email': attributes.get('email'),
                    'ldap_dn': found_dn,
                }
        except LDAPException as exc:
            raise AppError(401, 'AUTH_INVALID', 'Invalid username or password', {'ldap_error': str(exc)}) from exc

    def _local_authenticate(self, username: str, password: str) -> dict[str, Any] | None:
        user = self.repository.get_user_by_username(username)
        if user and verify_password(password, user.local_password_hash):
            return {
                'username': user.username,
                'display_name': user.display_name or user.username,
                'email': user.email,
                'ldap_dn': user.ldap_dn,
            }
        return None

    def authenticate(self, username: str, password: str) -> User:
        username = username.strip()
        if not username or not password:
            raise AppError(400, 'AUTH_INVALID_INPUT', 'Username and password are required')
        self._ensure_not_rate_limited(username)

        auth_config = self._effective_auth_config()
        auth_payload: dict[str, Any] | None = None
        auth_source = 'ldap'

        if auth_config['ldap_enabled']:
            try:
                auth_payload = self._ldap_authenticate(username, password, auth_config)
            except AppError:
                if not auth_config['allow_local_auth']:
                    raise
            except LDAPException as exc:
                if not auth_config['allow_local_auth']:
                    raise AppError(502, 'LDAP_UNAVAILABLE', 'LDAP authentication failed', {'error': str(exc)}) from exc

        if auth_payload is None and auth_config['allow_local_auth']:
            auth_source = 'local'
            auth_payload = self._local_authenticate(username, password)

        if auth_payload is None:
            self._record_failed_attempt(username)
            raise AppError(401, 'AUTH_INVALID', 'Invalid username or password')

        user = self.repository.upsert_user(
            username=auth_payload['username'],
            display_name=auth_payload.get('display_name'),
            email=auth_payload.get('email'),
            ldap_dn=auth_payload.get('ldap_dn'),
            auth_source=auth_source,
        )
        is_local_admin = user.auth_source == 'local' and user.username == settings.local_admin_username
        if is_local_admin:
            self.repository.assign_role(user, 'admin')
        elif not user.roles:
            self.repository.assign_role(user, 'operator')
        self._clear_failed_attempts(username)
        user.last_login_at = datetime.now(timezone.utc)
        self.session.flush()
        return user

    def login(self, *, username: str, password: str, context: RequestContext) -> LoginResult:
        user = self.authenticate(username, password)
        session_token = generate_token()
        csrf_token = generate_token()
        auth_session = self.repository.create_session(
            user=user,
            token_hash=hash_token(session_token),
            csrf_token_hash=hash_token(csrf_token),
            ip_address=context.ip_address,
            user_agent=context.user_agent,
            expires_at=build_session_expiry(),
        )
        self.audit.record(
            action='login',
            resource_type='auth_session',
            resource_id=str(auth_session.id),
            message=f'User {user.username} logged in',
            user_id=user.id,
            ip_address=context.ip_address,
        )
        self.session.commit()
        self.session.refresh(user)
        self.session.refresh(auth_session)
        return LoginResult(user=user, session=auth_session, session_token=session_token, csrf_token=csrf_token)

    def get_session(self, session_token: str | None) -> AuthSession:
        if not session_token:
            raise AppError(401, 'AUTH_REQUIRED', 'Authentication required')

        auth_session = self.repository.get_session_by_token_hash(hash_token(session_token))
        if auth_session is None:
            raise AppError(401, 'AUTH_REQUIRED', 'Authentication required')
        if auth_session.expires_at < datetime.now(timezone.utc):
            self.repository.delete_session(auth_session)
            self.session.commit()
            raise AppError(401, 'SESSION_EXPIRED', 'Session expired')
        return auth_session

    def validate_csrf(self, auth_session: AuthSession, csrf_token: str | None) -> None:
        if not csrf_token or hash_token(csrf_token) != auth_session.csrf_token_hash:
            raise AppError(403, 'CSRF_INVALID', 'CSRF validation failed')

    def touch_session(self, auth_session: AuthSession) -> None:
        auth_session.last_seen_at = datetime.now(timezone.utc)
        self.session.flush()

    def logout(self, auth_session: AuthSession, *, ip_address: str | None = None) -> None:
        username = auth_session.user.username
        user_id = auth_session.user_id
        session_id = str(auth_session.id)
        self.repository.delete_session(auth_session)
        self.audit.record(
            action='logout',
            resource_type='auth_session',
            resource_id=session_id,
            message=f'User {username} logged out',
            user_id=user_id,
            ip_address=ip_address,
        )
        self.session.commit()

    def change_password(self, *, user: User, current_password: str, new_password: str, context: RequestContext) -> None:
        if len(new_password) < 8:
            raise AppError(400, 'PASSWORD_INVALID', 'New password must be at least 8 characters')
        if current_password == new_password:
            raise AppError(400, 'PASSWORD_INVALID', 'New password must be different from current password')
        if not user.local_password_hash:
            raise AppError(400, 'PASSWORD_RESET_UNAVAILABLE', 'Password reset is only available for local accounts')
        if not verify_password(current_password, user.local_password_hash):
            raise AppError(400, 'PASSWORD_INVALID', 'Current password is incorrect')

        user.local_password_hash = hash_password(new_password)
        self.session.flush()
        self.audit.record(
            action='password.reset',
            resource_type='user',
            resource_id=str(user.id),
            message=f'Password reset for {user.username}',
            user_id=user.id,
            ip_address=context.ip_address,
            user_agent=context.user_agent,
        )
        self.session.commit()

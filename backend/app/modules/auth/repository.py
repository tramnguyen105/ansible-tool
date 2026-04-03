from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.auth import AuthSession, Role, User, UserRole
from app.models.system import AuthLoginThrottle


class AuthRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_user_by_username(self, username: str) -> User | None:
        return self.session.scalar(
            select(User).options(joinedload(User.roles)).where(User.username == username)
        )

    def get_user_by_id(self, user_id: UUID) -> User | None:
        return self.session.scalar(select(User).options(joinedload(User.roles)).where(User.id == user_id))

    def upsert_user(
        self,
        *,
        username: str,
        display_name: str | None,
        email: str | None,
        ldap_dn: str | None,
        auth_source: str,
    ) -> User:
        user = self.get_user_by_username(username)
        if user is None:
            user = User(
                username=username,
                display_name=display_name,
                email=email,
                ldap_dn=ldap_dn,
                auth_source=auth_source,
                is_active=True,
            )
            self.session.add(user)
            self.session.flush()
        else:
            user.display_name = display_name
            user.email = email
            user.ldap_dn = ldap_dn
            user.auth_source = auth_source
            user.is_active = True
        return user

    def get_role(self, name: str) -> Role | None:
        return self.session.scalar(select(Role).where(Role.name == name))

    def assign_role(self, user: User, role_name: str) -> None:
        role = self.get_role(role_name)
        if role is None:
            role = Role(name=role_name, description=f'{role_name.title()} role')
            self.session.add(role)
            self.session.flush()

        existing = self.session.scalar(
            select(UserRole).where(UserRole.user_id == user.id, UserRole.role_id == role.id)
        )
        if existing is None:
            self.session.add(UserRole(user_id=user.id, role_id=role.id, created_at=datetime.now(timezone.utc)))
            self.session.flush()
            self.session.refresh(user)

    def create_session(
        self,
        *,
        user: User,
        token_hash: str,
        csrf_token_hash: str,
        ip_address: str | None,
        user_agent: str | None,
        expires_at: datetime,
    ) -> AuthSession:
        auth_session = AuthSession(
            user_id=user.id,
            token_hash=token_hash,
            csrf_token_hash=csrf_token_hash,
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=expires_at,
            last_seen_at=datetime.now(timezone.utc),
        )
        self.session.add(auth_session)
        self.session.flush()
        return auth_session

    def get_session_by_token_hash(self, token_hash: str) -> AuthSession | None:
        return self.session.scalar(
            select(AuthSession)
            .options(joinedload(AuthSession.user).joinedload(User.roles))
            .where(AuthSession.token_hash == token_hash)
        )

    def delete_session(self, auth_session: AuthSession) -> None:
        self.session.delete(auth_session)

    def cleanup_expired_sessions(self) -> None:
        now = datetime.now(timezone.utc)
        sessions = self.session.scalars(select(AuthSession).where(AuthSession.expires_at < now)).all()
        for auth_session in sessions:
            self.session.delete(auth_session)

    def get_login_throttle(self, subject_key: str) -> AuthLoginThrottle | None:
        return self.session.scalar(select(AuthLoginThrottle).where(AuthLoginThrottle.subject_key == subject_key))

    def upsert_login_throttle(
        self,
        *,
        subject_key: str,
        attempt_count: int,
        window_started_at: datetime,
        last_attempt_at: datetime,
    ) -> AuthLoginThrottle:
        throttle = self.get_login_throttle(subject_key)
        if throttle is None:
            throttle = AuthLoginThrottle(
                subject_key=subject_key,
                attempt_count=attempt_count,
                window_started_at=window_started_at,
                last_attempt_at=last_attempt_at,
            )
            self.session.add(throttle)
        else:
            throttle.attempt_count = attempt_count
            throttle.window_started_at = window_started_at
            throttle.last_attempt_at = last_attempt_at
        self.session.flush()
        return throttle

    def delete_login_throttle(self, subject_key: str) -> None:
        throttle = self.get_login_throttle(subject_key)
        if throttle is not None:
            self.session.delete(throttle)
            self.session.flush()

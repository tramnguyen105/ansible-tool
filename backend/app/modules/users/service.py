from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import AppError
from app.core.security import hash_password
from app.models.auth import User
from app.modules.audit.service import AuditService
from app.modules.users.repository import UsersRepository
from app.modules.users.schemas import UserCreate, UserRead, UserUpdate


def user_has_role(user: User, role_name: str) -> bool:
    return any(role.name == role_name for role in user.roles)


class UsersService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.repository = UsersRepository(session)
        self.audit = AuditService(session)

    def list_users(self) -> list[UserRead]:
        return [UserRead.model_validate(item) for item in self.repository.list_users()]

    def list_roles(self):
        return self.repository.list_roles()

    def create_user(self, payload: UserCreate, *, actor_id: UUID, actor_username: str) -> UserRead:
        username = payload.username.strip()
        if not username:
            raise AppError(400, 'USER_INVALID', 'Username is required')
        existing = self.repository.get_user_by_username(username)
        if existing:
            raise AppError(409, 'USER_EXISTS', 'A user with this username already exists')

        auth_source = payload.auth_source
        if auth_source == 'local' and not payload.password:
            raise AppError(400, 'USER_PASSWORD_REQUIRED', 'Password is required for local users')
        if auth_source == 'ldap' and payload.password:
            raise AppError(400, 'USER_PASSWORD_INVALID', 'Do not set a local password for LDAP users')

        role_names = payload.role_names or ['operator']
        user = User(
            username=username,
            display_name=payload.display_name.strip() if payload.display_name else None,
            email=payload.email.strip() if payload.email else None,
            ldap_dn=payload.ldap_dn.strip() if payload.ldap_dn else None,
            auth_source=auth_source,
            local_password_hash=hash_password(payload.password.get_secret_value()) if payload.password else None,
            is_active=payload.is_active,
        )
        self.session.add(user)
        self.session.flush()
        self.repository.set_user_roles(user, role_names)
        self.audit.record(
            action='user.created',
            resource_type='user',
            resource_id=str(user.id),
            message=f'User {user.username} created by {actor_username}',
            user_id=actor_id,
            details={'auth_source': auth_source, 'roles': role_names},
        )
        self.session.commit()
        self.session.refresh(user)
        return UserRead.model_validate(user)

    def update_user(self, user_id: UUID, payload: UserUpdate, *, actor_id: UUID, actor_username: str) -> UserRead:
        user = self.repository.get_user(user_id)
        if user is None:
            raise AppError(404, 'USER_NOT_FOUND', 'User not found')

        updates = payload.model_dump(exclude_unset=True)
        if 'display_name' in updates:
            user.display_name = payload.display_name.strip() if payload.display_name else None
        if 'email' in updates:
            user.email = payload.email.strip() if payload.email else None
        if 'ldap_dn' in updates:
            user.ldap_dn = payload.ldap_dn.strip() if payload.ldap_dn else None
        if 'is_active' in updates:
            user.is_active = bool(payload.is_active)
        if payload.role_names is not None:
            self.repository.set_user_roles(user, payload.role_names)

        self.session.flush()
        self.audit.record(
            action='user.updated',
            resource_type='user',
            resource_id=str(user.id),
            message=f'User {user.username} updated by {actor_username}',
            user_id=actor_id,
            details={'updated_fields': sorted(updates.keys())},
        )
        self.session.commit()
        self.session.refresh(user)
        return UserRead.model_validate(user)

    def reset_local_password(self, user_id: UUID, new_password: str, *, actor_id: UUID, actor_username: str) -> None:
        user = self.repository.get_user(user_id)
        if user is None:
            raise AppError(404, 'USER_NOT_FOUND', 'User not found')
        if user.auth_source != 'local':
            raise AppError(400, 'USER_PASSWORD_RESET_INVALID', 'Password reset is only available for local users')
        if len(new_password) < 8:
            raise AppError(400, 'USER_PASSWORD_INVALID', 'Password must be at least 8 characters')

        user.local_password_hash = hash_password(new_password)
        self.session.flush()
        self.audit.record(
            action='user.password_reset',
            resource_type='user',
            resource_id=str(user.id),
            message=f'Password reset for {user.username} by {actor_username}',
            user_id=actor_id,
        )
        self.session.commit()

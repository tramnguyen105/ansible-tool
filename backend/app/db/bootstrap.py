from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import hash_password
from app.models.auth import Role, User, UserRole


settings = get_settings()


def bootstrap_defaults(session: Session) -> None:
    admin_role = session.scalar(select(Role).where(Role.name == 'admin'))
    if admin_role is None:
        admin_role = Role(name='admin', description='Platform administrator')
        session.add(admin_role)
        session.flush()

    if not settings.allow_local_auth:
        session.commit()
        return

    local_user = session.scalar(select(User).where(User.username == settings.local_admin_username))
    if local_user is None:
        local_user = User(
            username=settings.local_admin_username,
            display_name='Local Administrator',
            email=None,
            is_active=True,
            auth_source='local',
            local_password_hash=hash_password(settings.local_admin_password),
        )
        session.add(local_user)
        session.flush()

    existing_link = session.scalar(
        select(UserRole).where(UserRole.user_id == local_user.id, UserRole.role_id == admin_role.id)
    )
    if existing_link is None:
        session.add(UserRole(user_id=local_user.id, role_id=admin_role.id))

    session.commit()

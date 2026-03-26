from __future__ import annotations

from app.models.auth import User


def user_has_role(user: User, role_name: str) -> bool:
    return any(role.name == role_name for role in user.roles)

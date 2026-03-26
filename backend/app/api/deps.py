from __future__ import annotations

from dataclasses import dataclass

from fastapi import Cookie, Depends, Header, Request
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.core.exceptions import AppError
from app.core.security import hash_token
from app.models.auth import AuthSession, User
from app.modules.auth.service import AuthService
from app.modules.users.service import user_has_role


settings = get_settings()


@dataclass
class AuthContext:
    user: User
    session: AuthSession


DbSession = Session


def get_auth_context(
    db: DbSession = Depends(get_db),
    session_token: str | None = Cookie(default=None, alias=settings.session_cookie_name),
) -> AuthContext:
    service = AuthService(db)
    auth_session = service.get_session(session_token)
    service.touch_session(auth_session)
    db.commit()
    return AuthContext(user=auth_session.user, session=auth_session)


def get_current_user(auth: AuthContext = Depends(get_auth_context)) -> User:
    return auth.user


def require_admin(auth: AuthContext = Depends(get_auth_context)) -> AuthContext:
    if not user_has_role(auth.user, 'admin'):
        raise AppError(403, 'FORBIDDEN', 'Administrator role required')
    return auth


def require_csrf(
    request: Request,
    auth: AuthContext = Depends(get_auth_context),
    csrf_token: str | None = Header(default=None, alias='X-CSRF-Token'),
) -> AuthContext:
    if request.method.upper() in {'POST', 'PUT', 'PATCH', 'DELETE'}:
        if not csrf_token or hash_token(csrf_token) != auth.session.csrf_token_hash:
            raise AppError(403, 'CSRF_INVALID', 'CSRF validation failed')
    return auth

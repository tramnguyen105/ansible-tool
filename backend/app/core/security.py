from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from cryptography.fernet import Fernet
from passlib.context import CryptContext
from starlette.responses import Response

from app.core.config import get_settings


pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
settings = get_settings()


def _get_fernet() -> Fernet:
    return Fernet(settings.fernet_key.encode())


def hash_password(value: str) -> str:
    return pwd_context.hash(value)


def verify_password(plain_value: str, hashed_value: str | None) -> bool:
    if not hashed_value:
        return False
    return pwd_context.verify(plain_value, hashed_value)


def generate_token() -> str:
    return secrets.token_urlsafe(48)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode('utf-8')).hexdigest()


def build_session_expiry() -> datetime:
    return datetime.now(timezone.utc) + timedelta(minutes=settings.session_ttl_minutes)


def encrypt_value(value: str | None) -> str | None:
    if not value:
        return None
    return _get_fernet().encrypt(value.encode('utf-8')).decode('utf-8')


def decrypt_value(value: str | None) -> str | None:
    if not value:
        return None
    return _get_fernet().decrypt(value.encode('utf-8')).decode('utf-8')


def mask_secret(value: str | None, visible_chars: int = 2) -> str | None:
    if not value:
        return None
    if len(value) <= visible_chars:
        return '*' * len(value)
    return '*' * (len(value) - visible_chars) + value[-visible_chars:]


def set_auth_cookies(response: Response, session_token: str, csrf_token: str) -> None:
    response.set_cookie(
        key=settings.session_cookie_name,
        value=session_token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite='lax',
        domain=settings.cookie_domain,
        max_age=settings.session_ttl_minutes * 60,
        path='/',
    )
    response.set_cookie(
        key=settings.csrf_cookie_name,
        value=csrf_token,
        httponly=False,
        secure=settings.cookie_secure,
        samesite='lax',
        domain=settings.cookie_domain,
        max_age=settings.session_ttl_minutes * 60,
        path='/',
    )


def clear_auth_cookies(response: Response) -> None:
    response.delete_cookie(settings.session_cookie_name, domain=settings.cookie_domain, path='/')
    response.delete_cookie(settings.csrf_cookie_name, domain=settings.cookie_domain, path='/')

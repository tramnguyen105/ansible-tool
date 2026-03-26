from __future__ import annotations

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session

from app.api.deps import AuthContext, get_auth_context, get_db, require_csrf
from app.core.security import clear_auth_cookies, set_auth_cookies
from app.modules.auth.schemas import LoginPayload, LoginRequest, SessionPayload, UserRead
from app.modules.auth.service import AuthService, RequestContext
from app.schemas.common import ApiResponse


router = APIRouter(prefix='/auth', tags=['auth'])


@router.post('/login', response_model=ApiResponse[LoginPayload])
def login(payload: LoginRequest, request: Request, response: Response, db: Session = Depends(get_db)) -> ApiResponse[LoginPayload]:
    service = AuthService(db)
    login_result = service.login(
        username=payload.username,
        password=payload.password.get_secret_value(),
        context=RequestContext(
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get('user-agent'),
        ),
    )
    set_auth_cookies(response, login_result.session_token, login_result.csrf_token)
    return ApiResponse(
        message='Login successful',
        data=LoginPayload(
            user=UserRead.model_validate(login_result.user),
            csrf_token=login_result.csrf_token,
            expires_at=login_result.session.expires_at,
        ),
    )


@router.post('/logout', response_model=ApiResponse[dict], dependencies=[Depends(require_csrf)])
def logout(request: Request, response: Response, auth: AuthContext = Depends(get_auth_context), db: Session = Depends(get_db)) -> ApiResponse[dict]:
    service = AuthService(db)
    service.logout(auth.session, ip_address=request.client.host if request.client else None)
    clear_auth_cookies(response)
    return ApiResponse(message='Logout successful', data={})


@router.get('/me', response_model=ApiResponse[SessionPayload])
def me(auth: AuthContext = Depends(get_auth_context), db: Session = Depends(get_db)) -> ApiResponse[SessionPayload]:
    service = AuthService(db)
    service.touch_session(auth.session)
    db.commit()
    return ApiResponse(
        data=SessionPayload(user=UserRead.model_validate(auth.user), expires_at=auth.session.expires_at),
    )

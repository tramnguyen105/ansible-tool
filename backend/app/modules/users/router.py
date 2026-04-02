from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import AuthContext, get_db, require_admin, require_csrf
from app.modules.users.schemas import RoleRead, UserCreate, UserPasswordResetRequest, UserRead, UserUpdate
from app.modules.users.service import UsersService
from app.schemas.common import ApiResponse


router = APIRouter(prefix='/users', tags=['users'])


@router.get('', response_model=ApiResponse[list[UserRead]])
def list_users(_: AuthContext = Depends(require_admin), db: Session = Depends(get_db)) -> ApiResponse[list[UserRead]]:
    return ApiResponse(data=UsersService(db).list_users())


@router.get('/roles', response_model=ApiResponse[list[RoleRead]])
def list_roles(_: AuthContext = Depends(require_admin), db: Session = Depends(get_db)) -> ApiResponse[list[RoleRead]]:
    service = UsersService(db)
    return ApiResponse(data=[RoleRead.model_validate(item) for item in service.list_roles()])


@router.post('', response_model=ApiResponse[UserRead], dependencies=[Depends(require_csrf)])
def create_user(payload: UserCreate, auth: AuthContext = Depends(require_admin), db: Session = Depends(get_db)) -> ApiResponse[UserRead]:
    user = UsersService(db).create_user(payload, actor_id=auth.user.id, actor_username=auth.user.username)
    return ApiResponse(message='User created', data=user)


@router.put('/{user_id}', response_model=ApiResponse[UserRead], dependencies=[Depends(require_csrf)])
def update_user(user_id: UUID, payload: UserUpdate, auth: AuthContext = Depends(require_admin), db: Session = Depends(get_db)) -> ApiResponse[UserRead]:
    user = UsersService(db).update_user(user_id, payload, actor_id=auth.user.id, actor_username=auth.user.username)
    return ApiResponse(message='User updated', data=user)


@router.post('/{user_id}/reset-password', response_model=ApiResponse[dict], dependencies=[Depends(require_csrf)])
def reset_password(
    user_id: UUID,
    payload: UserPasswordResetRequest,
    auth: AuthContext = Depends(require_admin),
    db: Session = Depends(get_db),
) -> ApiResponse[dict]:
    UsersService(db).reset_local_password(
        user_id,
        payload.new_password.get_secret_value(),
        actor_id=auth.user.id,
        actor_username=auth.user.username,
    )
    return ApiResponse(message='User password updated', data={})

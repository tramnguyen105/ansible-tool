from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import AuthContext, get_db, require_admin, require_csrf
from app.modules.credentials.schemas import CredentialCreate, CredentialRead, CredentialUpdate
from app.modules.credentials.service import CredentialService
from app.schemas.common import ApiResponse


router = APIRouter(prefix='/credentials', tags=['credentials'])


@router.get('', response_model=ApiResponse[list[CredentialRead]])
def list_credentials(_: AuthContext = Depends(require_admin), db: Session = Depends(get_db)) -> ApiResponse[list[CredentialRead]]:
    service = CredentialService(db)
    return ApiResponse(data=service.list())


@router.get('/{credential_id}', response_model=ApiResponse[CredentialRead])
def get_credential(credential_id: UUID, _: AuthContext = Depends(require_admin), db: Session = Depends(get_db)) -> ApiResponse[CredentialRead]:
    service = CredentialService(db)
    return ApiResponse(data=service.get(credential_id))


@router.post('', response_model=ApiResponse[CredentialRead], dependencies=[Depends(require_csrf)])
def create_credential(payload: CredentialCreate, auth: AuthContext = Depends(require_admin), db: Session = Depends(get_db)) -> ApiResponse[CredentialRead]:
    service = CredentialService(db)
    return ApiResponse(message='Credential created', data=service.create(payload, user_id=auth.user.id))


@router.put('/{credential_id}', response_model=ApiResponse[CredentialRead], dependencies=[Depends(require_csrf)])
def update_credential(credential_id: UUID, payload: CredentialUpdate, auth: AuthContext = Depends(require_admin), db: Session = Depends(get_db)) -> ApiResponse[CredentialRead]:
    service = CredentialService(db)
    return ApiResponse(message='Credential updated', data=service.update(credential_id, payload, user_id=auth.user.id))


@router.delete('/{credential_id}', response_model=ApiResponse[dict], dependencies=[Depends(require_csrf)])
def delete_credential(credential_id: UUID, auth: AuthContext = Depends(require_admin), db: Session = Depends(get_db)) -> ApiResponse[dict]:
    service = CredentialService(db)
    service.delete(credential_id, user_id=auth.user.id)
    return ApiResponse(message='Credential deleted', data={})

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import AuthContext, get_db, require_admin, require_csrf
from app.modules.playbooks.schemas import PlaybookCreate, PlaybookRead, PlaybookUpdate, YamlValidationRequest, YamlValidationResult
from app.modules.playbooks.service import PlaybookService
from app.schemas.common import ApiResponse


router = APIRouter(prefix='/playbooks', tags=['playbooks'])


@router.get('', response_model=ApiResponse[list[PlaybookRead]])
def list_playbooks(_: AuthContext = Depends(require_admin), db: Session = Depends(get_db)) -> ApiResponse[list[PlaybookRead]]:
    service = PlaybookService(db)
    return ApiResponse(data=service.list())


@router.get('/{playbook_id}', response_model=ApiResponse[PlaybookRead])
def get_playbook(playbook_id: UUID, _: AuthContext = Depends(require_admin), db: Session = Depends(get_db)) -> ApiResponse[PlaybookRead]:
    service = PlaybookService(db)
    return ApiResponse(data=service.get(playbook_id))


@router.post('', response_model=ApiResponse[PlaybookRead], dependencies=[Depends(require_csrf)])
def create_playbook(payload: PlaybookCreate, auth: AuthContext = Depends(require_admin), db: Session = Depends(get_db)) -> ApiResponse[PlaybookRead]:
    service = PlaybookService(db)
    return ApiResponse(message='Playbook created', data=service.create(payload, user_id=auth.user.id))


@router.put('/{playbook_id}', response_model=ApiResponse[PlaybookRead], dependencies=[Depends(require_csrf)])
def update_playbook(playbook_id: UUID, payload: PlaybookUpdate, auth: AuthContext = Depends(require_admin), db: Session = Depends(get_db)) -> ApiResponse[PlaybookRead]:
    service = PlaybookService(db)
    return ApiResponse(message='Playbook updated', data=service.update(playbook_id, payload, user_id=auth.user.id))


@router.delete('/{playbook_id}', response_model=ApiResponse[dict], dependencies=[Depends(require_csrf)])
def delete_playbook(playbook_id: UUID, auth: AuthContext = Depends(require_admin), db: Session = Depends(get_db)) -> ApiResponse[dict]:
    service = PlaybookService(db)
    service.delete(playbook_id, user_id=auth.user.id)
    return ApiResponse(message='Playbook deleted', data={})


@router.post('/validate-yaml', response_model=ApiResponse[YamlValidationResult], dependencies=[Depends(require_csrf)])
def validate_yaml(payload: YamlValidationRequest, _: AuthContext = Depends(require_admin), db: Session = Depends(get_db)) -> ApiResponse[YamlValidationResult]:
    service = PlaybookService(db)
    return ApiResponse(message='Validation complete', data=service.validate_yaml(payload.content))

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import AuthContext, get_db, require_admin, require_csrf
from app.modules.templates.schemas import (
    TemplateCreate,
    TemplateRead,
    TemplateSourceTypeSchema,
    TemplateSummaryRead,
    TemplateUpdate,
    TemplateValidateRead,
    TemplateValidateRequest,
)
from app.modules.templates.service import TemplateService
from app.schemas.common import ApiResponse


router = APIRouter(prefix='/templates', tags=['templates'])


@router.get('', response_model=ApiResponse[list[TemplateRead]])
def list_templates(
    source_type: TemplateSourceTypeSchema | None = Query(default=None),
    _: AuthContext = Depends(require_admin),
    db: Session = Depends(get_db),
) -> ApiResponse[list[TemplateRead]]:
    service = TemplateService(db)
    return ApiResponse(data=service.list(source_type=source_type))


@router.get('/summary', response_model=ApiResponse[list[TemplateSummaryRead]])
def list_template_summary(
    source_type: TemplateSourceTypeSchema | None = Query(default=None),
    _: AuthContext = Depends(require_admin),
    db: Session = Depends(get_db),
) -> ApiResponse[list[TemplateSummaryRead]]:
    service = TemplateService(db)
    return ApiResponse(data=service.list_summary(source_type=source_type))


@router.post('/validate', response_model=ApiResponse[TemplateValidateRead])
def validate_template(payload: TemplateValidateRequest, _: AuthContext = Depends(require_admin), db: Session = Depends(get_db)) -> ApiResponse[TemplateValidateRead]:
    service = TemplateService(db)
    return ApiResponse(message='Template validated', data=service.validate_content(payload.content))


@router.get('/{template_id}', response_model=ApiResponse[TemplateRead])
def get_template(template_id: UUID, _: AuthContext = Depends(require_admin), db: Session = Depends(get_db)) -> ApiResponse[TemplateRead]:
    service = TemplateService(db)
    return ApiResponse(data=service.get(template_id))


@router.post('', response_model=ApiResponse[TemplateRead], dependencies=[Depends(require_csrf)])
def create_template(payload: TemplateCreate, auth: AuthContext = Depends(require_admin), db: Session = Depends(get_db)) -> ApiResponse[TemplateRead]:
    service = TemplateService(db)
    return ApiResponse(message='Template created', data=service.create(payload, user_id=auth.user.id))


@router.put('/{template_id}', response_model=ApiResponse[TemplateRead], dependencies=[Depends(require_csrf)])
def update_template(template_id: UUID, payload: TemplateUpdate, auth: AuthContext = Depends(require_admin), db: Session = Depends(get_db)) -> ApiResponse[TemplateRead]:
    service = TemplateService(db)
    return ApiResponse(message='Template updated', data=service.update(template_id, payload, user_id=auth.user.id))


@router.delete('/{template_id}', response_model=ApiResponse[dict], dependencies=[Depends(require_csrf)])
def delete_template(template_id: UUID, auth: AuthContext = Depends(require_admin), db: Session = Depends(get_db)) -> ApiResponse[dict]:
    service = TemplateService(db)
    service.delete(template_id, user_id=auth.user.id)
    return ApiResponse(message='Template deleted', data={})

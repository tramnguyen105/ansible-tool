from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import AuthContext, get_db, require_admin, require_csrf
from app.modules.cli_converter.schemas import (
    CliGenerateRequest,
    CliGenerateResult,
    CliParseRequest,
    CliParseResult,
    CliSavePlaybookRequest,
    CliSaveTemplateRequest,
    CliValidateResult,
)
from app.modules.cli_converter.service import CliConverterService
from app.modules.playbooks.schemas import PlaybookRead
from app.modules.templates.schemas import TemplateRead
from app.schemas.common import ApiResponse


router = APIRouter(prefix='/cli-converter', tags=['cli-converter'])


@router.post('/parse', response_model=ApiResponse[CliParseResult], dependencies=[Depends(require_csrf)])
def parse_cli(payload: CliParseRequest, _: AuthContext = Depends(require_admin), db: Session = Depends(get_db)) -> ApiResponse[CliParseResult]:
    service = CliConverterService(db)
    return ApiResponse(message='CLI parsed', data=service.parse(payload.config_text))


@router.post('/generate', response_model=ApiResponse[CliGenerateResult], dependencies=[Depends(require_csrf)])
def generate_cli(payload: CliGenerateRequest, auth: AuthContext = Depends(require_admin), db: Session = Depends(get_db)) -> ApiResponse[CliGenerateResult]:
    service = CliConverterService(db)
    return ApiResponse(message='Artifacts generated', data=service.generate(payload.config_text, payload.output_type, user_id=auth.user.id))


@router.post('/validate', response_model=ApiResponse[CliValidateResult], dependencies=[Depends(require_csrf)])
def validate_cli(payload: CliParseRequest, _: AuthContext = Depends(require_admin), db: Session = Depends(get_db)) -> ApiResponse[CliValidateResult]:
    service = CliConverterService(db)
    result = service.validate(payload.config_text)
    return ApiResponse(message='Validation complete', data=CliValidateResult(**result))


@router.post('/save-as-playbook', response_model=ApiResponse[PlaybookRead], dependencies=[Depends(require_csrf)])
def save_as_playbook(payload: CliSavePlaybookRequest, auth: AuthContext = Depends(require_admin), db: Session = Depends(get_db)) -> ApiResponse[PlaybookRead]:
    service = CliConverterService(db)
    return ApiResponse(message='Playbook saved', data=service.save_as_playbook(payload, user_id=auth.user.id))


@router.post('/save-as-template', response_model=ApiResponse[TemplateRead], dependencies=[Depends(require_csrf)])
def save_as_template(payload: CliSaveTemplateRequest, auth: AuthContext = Depends(require_admin), db: Session = Depends(get_db)) -> ApiResponse[TemplateRead]:
    service = CliConverterService(db)
    return ApiResponse(message='Template saved', data=service.save_as_template(payload, user_id=auth.user.id))

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import AuthContext, require_admin
from app.core.config import get_settings
from app.modules.audit.router import router as audit_router
from app.modules.auth.router import router as auth_router
from app.modules.cli_converter.router import router as cli_converter_router
from app.modules.credentials.router import router as credentials_router
from app.modules.inventory.router import router as inventory_router
from app.modules.jobs.router import router as jobs_router
from app.modules.playbooks.router import router as playbooks_router
from app.modules.schedules.router import router as schedules_router
from app.modules.templates.router import router as templates_router
from app.schemas.common import ApiResponse, HealthPayload


settings = get_settings()
router = APIRouter()


@router.get('/health', response_model=ApiResponse[HealthPayload], tags=['system'])
def health() -> ApiResponse[HealthPayload]:
    return ApiResponse(
        data=HealthPayload(status='ok', app=settings.app_name, environment=settings.app_env),
    )


@router.get('/system/settings', response_model=ApiResponse[dict], tags=['system'])
def get_system_settings(_: AuthContext = Depends(require_admin)) -> ApiResponse[dict]:
    return ApiResponse(
        data={
            'app_name': settings.app_name,
            'environment': settings.app_env,
            'ldap_enabled': settings.ldap_enabled,
            'session_ttl_minutes': settings.session_ttl_minutes,
        }
    )


router.include_router(auth_router)
router.include_router(audit_router)
router.include_router(inventory_router)
router.include_router(credentials_router)
router.include_router(templates_router)
router.include_router(playbooks_router)
router.include_router(cli_converter_router)
router.include_router(jobs_router)
router.include_router(schedules_router)

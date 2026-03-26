from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_admin
from app.modules.audit.schemas import AuditLogRead
from app.modules.audit.service import AuditService
from app.schemas.common import ApiResponse


router = APIRouter(prefix='/audit-logs', tags=['audit'])


@router.get('', response_model=ApiResponse[list[AuditLogRead]])
def list_audit_logs(
    action: str | None = Query(default=None),
    resource_type: str | None = Query(default=None),
    status: str | None = Query(default=None),
    limit: int = Query(default=200, ge=1, le=500),
    _: object = Depends(require_admin),
    db: Session = Depends(get_db),
) -> ApiResponse[list[AuditLogRead]]:
    service = AuditService(db)
    items = service.list(action=action, resource_type=resource_type, status=status, limit=limit)
    return ApiResponse(data=[AuditLogRead.model_validate(item) for item in items])

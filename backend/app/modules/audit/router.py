from __future__ import annotations

import csv
import json
from datetime import datetime
from io import StringIO
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_admin
from app.modules.audit.schemas import AuditLogListRead
from app.modules.audit.service import AuditService
from app.schemas.common import ApiResponse


router = APIRouter(prefix='/audit-logs', tags=['audit'])


@router.get('', response_model=ApiResponse[AuditLogListRead])
def list_audit_logs(
    action: str | None = Query(default=None),
    resource_types: list[str] | None = Query(default=None),
    statuses: list[str] | None = Query(default=None),
    user_id: UUID | None = Query(default=None),
    resource_id: str | None = Query(default=None),
    message: str | None = Query(default=None),
    created_from: datetime | None = Query(default=None),
    created_to: datetime | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    _: object = Depends(require_admin),
    db: Session = Depends(get_db),
) -> ApiResponse[AuditLogListRead]:
    service = AuditService(db)
    data = service.list(
        action=action,
        resource_types=resource_types,
        statuses=statuses,
        user_id=user_id,
        resource_id=resource_id,
        message=message,
        created_from=created_from,
        created_to=created_to,
        limit=limit,
        offset=offset,
    )
    return ApiResponse(data=data)


@router.get('/export')
def export_audit_logs(
    format: str = Query(default='csv', pattern='^(csv|json)$'),
    action: str | None = Query(default=None),
    resource_types: list[str] | None = Query(default=None),
    statuses: list[str] | None = Query(default=None),
    user_id: UUID | None = Query(default=None),
    resource_id: str | None = Query(default=None),
    message: str | None = Query(default=None),
    created_from: datetime | None = Query(default=None),
    created_to: datetime | None = Query(default=None),
    limit: int = Query(default=5000, ge=1, le=10000),
    _: object = Depends(require_admin),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    service = AuditService(db)
    rows = service.export(
        action=action,
        resource_types=resource_types,
        statuses=statuses,
        user_id=user_id,
        resource_id=resource_id,
        message=message,
        created_from=created_from,
        created_to=created_to,
        limit=limit,
    )
    timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
    if format == 'json':
        payload = json.dumps([row.model_dump(mode='json') for row in rows], indent=2)
        return StreamingResponse(
            iter([payload]),
            media_type='application/json',
            headers={'Content-Disposition': f'attachment; filename=audit-logs-{timestamp}.json'},
        )

    output = StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=[
            'created_at',
            'status',
            'action',
            'resource_type',
            'resource_id',
            'user_id',
            'actor_username',
            'actor_display_name',
            'ip_address',
            'message',
            'details_json',
        ],
    )
    writer.writeheader()
    for row in rows:
        writer.writerow(
            {
                'created_at': row.created_at.isoformat(),
                'status': row.status,
                'action': row.action,
                'resource_type': row.resource_type,
                'resource_id': row.resource_id or '',
                'user_id': str(row.user_id) if row.user_id else '',
                'actor_username': row.actor_username or '',
                'actor_display_name': row.actor_display_name or '',
                'ip_address': row.ip_address or '',
                'message': row.message,
                'details_json': json.dumps(row.details_json),
            }
        )
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type='text/csv',
        headers={'Content-Disposition': f'attachment; filename=audit-logs-{timestamp}.csv'},
    )

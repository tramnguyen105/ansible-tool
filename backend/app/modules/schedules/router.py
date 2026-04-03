from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import AuthContext, get_db, require_admin, require_csrf
from app.modules.schedules.schemas import ScheduleCreate, ScheduleListRead, ScheduleRead, ScheduleUpdate
from app.modules.schedules.service import ScheduleService
from app.schemas.common import ApiResponse


router = APIRouter(prefix='/schedules', tags=['schedules'])


@router.get('', response_model=ApiResponse[list[ScheduleRead]])
def list_schedules(_: AuthContext = Depends(require_admin), db: Session = Depends(get_db)) -> ApiResponse[list[ScheduleRead]]:
    service = ScheduleService(db)
    return ApiResponse(data=service.list())


@router.get('/query', response_model=ApiResponse[ScheduleListRead])
def query_schedules(
    search: str | None = Query(default=None),
    enabled: str | None = Query(default=None, pattern='^(enabled|disabled)$'),
    mode: str | None = Query(default=None, pattern='^(check|live)$'),
    limit: int = Query(default=25, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    sort_by: str = Query(default='next_run_at', pattern='^(name|cron_expression|enabled|next_run_at|created_at)$'),
    sort_order: str = Query(default='asc', pattern='^(asc|desc)$'),
    _: AuthContext = Depends(require_admin),
    db: Session = Depends(get_db),
) -> ApiResponse[ScheduleListRead]:
    service = ScheduleService(db)
    return ApiResponse(
        data=service.list_filtered(
            search=search,
            enabled=True if enabled == 'enabled' else False if enabled == 'disabled' else None,
            mode=mode,
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            sort_order=sort_order,
        )
    )


@router.get('/{schedule_id}', response_model=ApiResponse[ScheduleRead])
def get_schedule(schedule_id: UUID, _: AuthContext = Depends(require_admin), db: Session = Depends(get_db)) -> ApiResponse[ScheduleRead]:
    service = ScheduleService(db)
    return ApiResponse(data=service.get(schedule_id))


@router.post('', response_model=ApiResponse[ScheduleRead], dependencies=[Depends(require_csrf)])
def create_schedule(payload: ScheduleCreate, auth: AuthContext = Depends(require_admin), db: Session = Depends(get_db)) -> ApiResponse[ScheduleRead]:
    service = ScheduleService(db)
    return ApiResponse(message='Schedule created', data=service.create(payload, user_id=auth.user.id))


@router.put('/{schedule_id}', response_model=ApiResponse[ScheduleRead], dependencies=[Depends(require_csrf)])
def update_schedule(schedule_id: UUID, payload: ScheduleUpdate, auth: AuthContext = Depends(require_admin), db: Session = Depends(get_db)) -> ApiResponse[ScheduleRead]:
    service = ScheduleService(db)
    return ApiResponse(message='Schedule updated', data=service.update(schedule_id, payload, user_id=auth.user.id))


@router.delete('/{schedule_id}', response_model=ApiResponse[dict], dependencies=[Depends(require_csrf)])
def delete_schedule(schedule_id: UUID, auth: AuthContext = Depends(require_admin), db: Session = Depends(get_db)) -> ApiResponse[dict]:
    service = ScheduleService(db)
    service.delete(schedule_id, user_id=auth.user.id)
    return ApiResponse(message='Schedule deleted', data={})

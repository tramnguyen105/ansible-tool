from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import AuthContext, get_db, require_admin, require_csrf
from app.modules.schedules.schemas import ScheduleCreate, ScheduleRead, ScheduleUpdate
from app.modules.schedules.service import ScheduleService
from app.schemas.common import ApiResponse


router = APIRouter(prefix='/schedules', tags=['schedules'])


@router.get('', response_model=ApiResponse[list[ScheduleRead]])
def list_schedules(_: AuthContext = Depends(require_admin), db: Session = Depends(get_db)) -> ApiResponse[list[ScheduleRead]]:
    service = ScheduleService(db)
    return ApiResponse(data=service.list())


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

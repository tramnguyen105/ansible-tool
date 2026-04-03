from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import AuthContext, get_db, require_admin, require_csrf
from app.modules.jobs.schemas import JobCreate, JobListRead, JobRead
from app.modules.jobs.service import JobService
from app.schemas.common import ApiResponse


router = APIRouter(prefix='/jobs', tags=['jobs'])


@router.get('', response_model=ApiResponse[list[JobRead]])
def list_jobs(_: AuthContext = Depends(require_admin), db: Session = Depends(get_db)) -> ApiResponse[list[JobRead]]:
    service = JobService(db)
    return ApiResponse(data=service.list())


@router.get('/query', response_model=ApiResponse[JobListRead])
def query_jobs(
    search: str | None = Query(default=None),
    statuses: list[str] | None = Query(default=None),
    mode: str | None = Query(default=None, pattern='^(check|live)$'),
    limit: int = Query(default=25, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    sort_by: str = Query(default='created_at', pattern='^(created_at|name|status|target_type)$'),
    sort_order: str = Query(default='desc', pattern='^(asc|desc)$'),
    _: AuthContext = Depends(require_admin),
    db: Session = Depends(get_db),
) -> ApiResponse[JobListRead]:
    service = JobService(db)
    return ApiResponse(
        data=service.list_filtered(
            search=search,
            statuses=statuses,
            mode=mode,
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            sort_order=sort_order,
        )
    )


@router.get('/{job_id}', response_model=ApiResponse[JobRead])
def get_job(job_id: UUID, _: AuthContext = Depends(require_admin), db: Session = Depends(get_db)) -> ApiResponse[JobRead]:
    service = JobService(db)
    return ApiResponse(data=service.get(job_id))


@router.post('', response_model=ApiResponse[JobRead], dependencies=[Depends(require_csrf)])
def create_job(payload: JobCreate, auth: AuthContext = Depends(require_admin), db: Session = Depends(get_db)) -> ApiResponse[JobRead]:
    service = JobService(db)
    return ApiResponse(message='Job created', data=service.create(payload, user_id=auth.user.id))


@router.post('/{job_id}/enqueue', response_model=ApiResponse[JobRead], dependencies=[Depends(require_csrf)])
def enqueue_job(job_id: UUID, auth: AuthContext = Depends(require_admin), db: Session = Depends(get_db)) -> ApiResponse[JobRead]:
    service = JobService(db)
    return ApiResponse(message='Job queued', data=service.enqueue(job_id, user_id=auth.user.id))

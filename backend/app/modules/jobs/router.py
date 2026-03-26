from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import AuthContext, get_db, require_admin, require_csrf
from app.modules.jobs.schemas import JobCreate, JobRead
from app.modules.jobs.service import JobService
from app.schemas.common import ApiResponse


router = APIRouter(prefix='/jobs', tags=['jobs'])


@router.get('', response_model=ApiResponse[list[JobRead]])
def list_jobs(_: AuthContext = Depends(require_admin), db: Session = Depends(get_db)) -> ApiResponse[list[JobRead]]:
    service = JobService(db)
    return ApiResponse(data=service.list())


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

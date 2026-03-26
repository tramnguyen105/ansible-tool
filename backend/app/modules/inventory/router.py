from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, File, Query, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import AuthContext, get_db, require_admin, require_csrf
from app.modules.inventory.schemas import ImportFormat, InventoryCreate, InventoryImportCommit, InventoryImportPreview, InventoryRead, InventoryUpdate
from app.modules.inventory.service import InventoryService
from app.schemas.common import ApiResponse


router = APIRouter(prefix='/inventories', tags=['inventories'])


@router.get('', response_model=ApiResponse[list[InventoryRead]])
def list_inventories(_: AuthContext = Depends(require_admin), db: Session = Depends(get_db)) -> ApiResponse[list[InventoryRead]]:
    service = InventoryService(db)
    return ApiResponse(data=service.list())


@router.get('/{inventory_id}', response_model=ApiResponse[InventoryRead])
def get_inventory(inventory_id: UUID, _: AuthContext = Depends(require_admin), db: Session = Depends(get_db)) -> ApiResponse[InventoryRead]:
    service = InventoryService(db)
    return ApiResponse(data=service.get(inventory_id))


@router.post('', response_model=ApiResponse[InventoryRead], dependencies=[Depends(require_csrf)])
def create_inventory(payload: InventoryCreate, auth: AuthContext = Depends(require_admin), db: Session = Depends(get_db)) -> ApiResponse[InventoryRead]:
    service = InventoryService(db)
    return ApiResponse(message='Inventory created', data=service.create(payload, user_id=auth.user.id))


@router.put('/{inventory_id}', response_model=ApiResponse[InventoryRead], dependencies=[Depends(require_csrf)])
def update_inventory(inventory_id: UUID, payload: InventoryUpdate, auth: AuthContext = Depends(require_admin), db: Session = Depends(get_db)) -> ApiResponse[InventoryRead]:
    service = InventoryService(db)
    return ApiResponse(message='Inventory updated', data=service.update(inventory_id, payload, user_id=auth.user.id))


@router.delete('/{inventory_id}', response_model=ApiResponse[dict], dependencies=[Depends(require_csrf)])
def delete_inventory(inventory_id: UUID, auth: AuthContext = Depends(require_admin), db: Session = Depends(get_db)) -> ApiResponse[dict]:
    service = InventoryService(db)
    service.delete(inventory_id, user_id=auth.user.id)
    return ApiResponse(message='Inventory deleted', data={})


@router.post('/import/preview', response_model=ApiResponse[InventoryImportPreview], dependencies=[Depends(require_csrf)])
async def preview_inventory_import(
    source_format: ImportFormat = Query(...),
    file: UploadFile = File(...),
    _: AuthContext = Depends(require_admin),
    db: Session = Depends(get_db),
) -> ApiResponse[InventoryImportPreview]:
    service = InventoryService(db)
    return ApiResponse(
        message='Inventory preview generated',
        data=service.preview_import(source_format=source_format, filename=file.filename or 'upload', raw_bytes=await file.read()),
    )


@router.post('/import/commit', response_model=ApiResponse[InventoryRead], dependencies=[Depends(require_csrf)])
def commit_inventory_import(payload: InventoryImportCommit, auth: AuthContext = Depends(require_admin), db: Session = Depends(get_db)) -> ApiResponse[InventoryRead]:
    service = InventoryService(db)
    return ApiResponse(message='Inventory imported', data=service.create_from_preview(payload, user_id=auth.user.id))

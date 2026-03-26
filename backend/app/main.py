from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app import models
from app.api.router import router as api_router
from app.core.config import get_settings
from app.core.database import SessionLocal, engine
from app.core.exceptions import AppError
from app.core.logging import configure_logging, logger
from app.db.bootstrap import bootstrap_defaults
from app.models.base import Base
from app.schemas.common import ApiResponse


settings = get_settings()
configure_logging(settings.log_level)


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings.runner_data_path.mkdir(parents=True, exist_ok=True)
    if settings.auto_create_db:
        Base.metadata.create_all(bind=engine)
    with SessionLocal() as session:
        bootstrap_defaults(session)
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)
app.include_router(api_router, prefix=settings.api_prefix)


@app.exception_handler(AppError)
async def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=ApiResponse(success=False, message=exc.message, data=exc.to_dict()).model_dump(),
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content=ApiResponse(
            success=False,
            message='Validation failed',
            data={'code': 'VALIDATION_ERROR', 'details': exc.errors()},
        ).model_dump(),
    )


@app.exception_handler(StarletteHTTPException)
async def http_error_handler(_: Request, exc: StarletteHTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=ApiResponse(success=False, message=str(exc.detail), data={'code': 'HTTP_ERROR'}).model_dump(),
    )


@app.exception_handler(Exception)
async def unhandled_error_handler(_: Request, exc: Exception) -> JSONResponse:
    logger.exception('Unhandled server error', exc_info=exc)
    return JSONResponse(
        status_code=500,
        content=ApiResponse(success=False, message='Internal server error', data={'code': 'INTERNAL_ERROR'}).model_dump(),
    )

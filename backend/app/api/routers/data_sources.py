import json

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.core.exceptions import AppException, NotFoundError
from app.db.session import get_db
from app.models.data_ops import DataSource, ImportJob
from app.permissions.dependencies import AuthenticatedUser, require_permission
from app.schemas.common import PaginatedResponse, PaginationMeta, StandardResponse
from app.schemas.data_ops import (
    DataSourceRead,
    ImportJobRead,
    ImportResultResponse,
    PreviewResponse,
)
from app.services.ingestion import ingestion_service

router = APIRouter(prefix="/data-sources", tags=["Data Ingestion & Management"])


@router.post(
    "/upload-preview",
    response_model=StandardResponse[PreviewResponse],
    summary="Upload CSV and inspect schema preview (Owner-only)",
    description=(
        "Upload a CSV dataset to inspect headers, inferred types, suggested mappings, "
        "and duplicate checksum status before committing import."
    ),
)
async def preview_upload(
    file: UploadFile = File(...),
    target_entity: str = Form(default="customers"),
    session: Session = Depends(get_db),
    _: AuthenticatedUser = Depends(require_permission("datasource.import")),
) -> StandardResponse[PreviewResponse]:
    content = await file.read()
    preview = ingestion_service.preview_csv(
        session=session,
        filename=file.filename or "upload.csv",
        content=content,
        target_entity=target_entity,
    )
    return StandardResponse(data=preview)


@router.post(
    "/import",
    response_model=StandardResponse[ImportResultResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Execute atomic dataset import with rollback safety (Owner-only)",
    description=(
        "Executes staging and destination table ingestion. Strictly rolls back all "
        "records if database constraint violations occur."
    ),
)
async def execute_import(
    file: UploadFile = File(...),
    target_entity: str = Form(default="customers"),
    custom_mapping: str | None = Form(default=None),
    allow_duplicate: bool = Form(default=False),
    session: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(require_permission("datasource.import")),
) -> StandardResponse[ImportResultResponse]:
    content = await file.read()

    mapping_dict: dict[str, str] | None = None
    if custom_mapping:
        try:
            mapping_dict = json.loads(custom_mapping)
        except Exception as e:
            raise AppException(
                f"Invalid custom_mapping JSON: {e}",
                status_code=400,
                code="INVALID_MAPPING_JSON",
            ) from e

    result = ingestion_service.execute_import(
        session=session,
        user=current_user.user,
        filename=file.filename or "upload.csv",
        content=content,
        target_entity=target_entity,
        custom_mapping=mapping_dict,
        allow_duplicate=allow_duplicate,
    )
    return StandardResponse(data=result)


@router.get(
    "/history",
    response_model=PaginatedResponse[ImportJobRead],
    summary="Inspect dataset import job execution history",
)
def get_import_history(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    session: Session = Depends(get_db),
    _: AuthenticatedUser = Depends(require_permission("datasource.view")),
) -> PaginatedResponse[ImportJobRead]:
    total_items = session.scalar(select(func.count(ImportJob.id))) or 0
    stmt = (
        select(ImportJob)
        .order_by(desc(ImportJob.id))
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = session.scalars(stmt).all()

    total_pages = max(1, (total_items + page_size - 1) // page_size)
    meta = PaginationMeta(
        page=page,
        page_size=page_size,
        total_items=total_items,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1,
    )
    return PaginatedResponse(
        data=[ImportJobRead.model_validate(item) for item in items],
        meta=meta,
    )


@router.get(
    "",
    response_model=PaginatedResponse[DataSourceRead],
    summary="List registered data sources",
)
def list_data_sources(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    session: Session = Depends(get_db),
    _: AuthenticatedUser = Depends(require_permission("datasource.view")),
) -> PaginatedResponse[DataSourceRead]:
    total_items = session.scalar(select(func.count(DataSource.id))) or 0
    stmt = (
        select(DataSource)
        .order_by(desc(DataSource.id))
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = session.scalars(stmt).all()

    total_pages = max(1, (total_items + page_size - 1) // page_size)
    meta = PaginationMeta(
        page=page,
        page_size=page_size,
        total_items=total_items,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1,
    )
    return PaginatedResponse(
        data=[DataSourceRead.model_validate(item) for item in items],
        meta=meta,
    )


@router.get(
    "/{data_source_id}",
    response_model=StandardResponse[DataSourceRead],
    summary="Get single data source metadata",
)
def get_data_source(
    data_source_id: int,
    session: Session = Depends(get_db),
    _: AuthenticatedUser = Depends(require_permission("datasource.view")),
) -> StandardResponse[DataSourceRead]:
    ds = session.get(DataSource, data_source_id)
    if not ds:
        raise NotFoundError(f"DataSource with ID {data_source_id} not found.")
    return StandardResponse(data=DataSourceRead.model_validate(ds))

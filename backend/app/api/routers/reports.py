from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.data_ops import AuditLog
from app.permissions.dependencies import AuthenticatedUser, require_permission
from app.schemas.common import StandardResponse
from app.schemas.reports import (
    ExportRequest,
    ReportCatalogueItem,
    ReportDataResponse,
    SavedViewCreate,
    SavedViewRead,
)
from app.services.reports import reports_service

router = APIRouter(prefix="/reports", tags=["Reports & Data Exports"])


@router.get(
    "/catalogue",
    response_model=StandardResponse[list[ReportCatalogueItem]],
    summary="List available reports in enterprise catalogue",
)
def get_report_catalogue(
    _: AuthenticatedUser = Depends(require_permission("report.view")),
) -> StandardResponse[list[ReportCatalogueItem]]:
    items = reports_service.list_catalogue()
    return StandardResponse(data=items)


@router.get(
    "/saved-views",
    response_model=StandardResponse[list[SavedViewRead]],
    summary="List persisted saved views accessible to current user",
)
def list_saved_views(
    section: str | None = Query(default=None, description="Optional section filter"),
    session: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(require_permission("report.view")),
) -> StandardResponse[list[SavedViewRead]]:
    views = reports_service.list_saved_views(session, current_user.user, section)
    return StandardResponse(data=views)


@router.post(
    "/saved-views",
    response_model=StandardResponse[SavedViewRead],
    status_code=status.HTTP_201_CREATED,
    summary="Create a new persisted saved view",
)
def create_saved_view(
    payload: SavedViewCreate,
    session: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(require_permission("report.view")),
) -> StandardResponse[SavedViewRead]:
    view = reports_service.create_saved_view(session, current_user.user, payload)
    return StandardResponse(data=view)


@router.get(
    "/saved-views/{view_id}",
    response_model=StandardResponse[SavedViewRead],
    summary="Get saved view by ID",
)
def get_saved_view(
    view_id: int,
    session: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(require_permission("report.view")),
) -> StandardResponse[SavedViewRead]:
    view = reports_service.get_saved_view(session, view_id, current_user.user)
    return StandardResponse(data=view)


@router.delete(
    "/saved-views/{view_id}",
    response_model=StandardResponse[dict[str, Any]],
    summary="Delete a persisted saved view",
)
def delete_saved_view(
    view_id: int,
    session: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(require_permission("report.view")),
) -> StandardResponse[dict[str, Any]]:
    reports_service.delete_saved_view(session, view_id, current_user.user)
    return StandardResponse(data={"deleted": True, "id": view_id})


@router.get(
    "/{report_id}/data",
    response_model=StandardResponse[ReportDataResponse],
    summary="Get structured report data with calculated aggregates",
)
def get_report_data(
    report_id: str,
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
    region_id: int | None = Query(default=None),
    sales_channel: str | None = Query(default=None),
    limit: int = Query(default=1000, ge=1),
    session: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(require_permission("report.view")),
) -> StandardResponse[ReportDataResponse]:
    filters = {
        "start_date": start_date,
        "end_date": end_date,
        "region_id": region_id,
        "sales_channel": sales_channel,
    }
    include_sensitive = current_user.has_permission("report.sensitive_fields")
    data = reports_service.get_report_data(
        session, report_id, filters, include_sensitive=include_sensitive, limit=limit
    )
    return StandardResponse(data=data)


@router.get(
    "/{report_id}/export/csv",
    summary="Export sanitized report CSV with formula injection protection",
)
def export_report_csv_get(
    report_id: str,
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
    region_id: int | None = Query(default=None),
    sales_channel: str | None = Query(default=None),
    limit: int = Query(default=10000, ge=1),
    session: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(require_permission("report.export")),
) -> StreamingResponse:
    filters = {
        "start_date": start_date,
        "end_date": end_date,
        "region_id": region_id,
        "sales_channel": sales_channel,
    }
    include_sensitive = current_user.has_permission("report.sensitive_fields")
    report_data = reports_service.get_report_data(
        session, report_id, filters, include_sensitive=include_sensitive, limit=limit
    )

    # Write audit log for data export
    audit = AuditLog(
        organization_id=current_user.user.organization_id,
        actor_user_id=current_user.id,
        actor_role=current_user.role,
        action_type="REPORT_EXPORT",
        entity_type="reports",
        entity_id=report_id,
        details={
            "report_name": report_data.name,
            "format": "csv",
            "total_rows": report_data.total_rows,
            "included_sensitive": include_sensitive,
        },
    )
    session.add(audit)
    session.commit()

    stream = reports_service.generate_csv_stream(
        report_data=report_data,
        user_identifier=current_user.email,
        user_role=current_user.role,
    )

    filename = f"{report_id}_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}.csv"
    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    return StreamingResponse(stream, media_type="text/csv", headers=headers)


@router.post(
    "/export/csv",
    summary="Export sanitized report CSV by request payload",
)
def export_report_csv_post(
    payload: ExportRequest,
    session: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(require_permission("report.export")),
) -> StreamingResponse:
    include_sensitive = current_user.has_permission("report.sensitive_fields")
    report_data = reports_service.get_report_data(
        session,
        payload.report_id,
        payload.filters,
        include_sensitive=include_sensitive,
        limit=payload.limit,
    )

    # Audit log
    audit = AuditLog(
        organization_id=current_user.user.organization_id,
        actor_user_id=current_user.id,
        actor_role=current_user.role,
        action_type="REPORT_EXPORT",
        entity_type="reports",
        entity_id=payload.report_id,
        details={
            "report_name": report_data.name,
            "format": "csv",
            "total_rows": report_data.total_rows,
            "included_sensitive": include_sensitive,
        },
    )
    session.add(audit)
    session.commit()

    stream = reports_service.generate_csv_stream(
        report_data=report_data,
        user_identifier=current_user.email,
        user_role=current_user.role,
    )

    filename = f"{payload.report_id}_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}.csv"
    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    return StreamingResponse(stream, media_type="text/csv", headers=headers)


@router.get(
    "/{report_id}/export/pdf",
    summary="Server-side PDF report export or clean deferral",
)
def export_report_pdf(
    report_id: str,
    _: AuthenticatedUser = Depends(require_permission("report.export")),
) -> Any:
    # BL-11 / M10-T12: PDF export clean deferral with informative error message
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="PDF report generation is deferred to v1.1. Please use sanitized CSV export.",
    )

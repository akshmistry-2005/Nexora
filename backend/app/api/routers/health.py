from datetime import UTC, datetime

from fastapi import APIRouter
from pydantic import BaseModel

from app.core.config import settings
from app.db.session import check_database_connection

router = APIRouter(prefix="/health", tags=["Health"])


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    environment: str
    database: str
    timestamp: str


@router.get("", response_model=HealthResponse, summary="Service and database health check")
def get_health() -> HealthResponse:
    db_ok, db_status = check_database_connection()
    return HealthResponse(
        status="healthy" if db_ok else "degraded",
        service=settings.app_name,
        version=settings.app_version,
        environment=settings.app_env,
        database=db_status,
        timestamp=datetime.now(UTC).isoformat(),
    )

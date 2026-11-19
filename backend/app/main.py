from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers.auth import router as auth_router
from app.api.routers.customers import router as customers_router
from app.api.routers.data_quality import router as data_quality_router
from app.api.routers.data_sources import router as data_sources_router
from app.api.routers.health import router as health_router
from app.api.routers.orders import router as orders_router
from app.api.routers.organizations import router as organizations_router
from app.api.routers.products import router as products_router
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.middleware import RequestContextMiddleware


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "Nexora Enterprise Data Intelligence & Business Analytics Platform — "
            "Backend API service layer providing paginated, filtered, and validated data access."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # Middleware
    app.add_middleware(RequestContextMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Global Exception Handlers
    register_exception_handlers(app)

    # Routers
    api_v1_prefix = "/api/v1"
    app.include_router(health_router, prefix=api_v1_prefix)
    app.include_router(auth_router, prefix=api_v1_prefix)
    app.include_router(organizations_router, prefix=api_v1_prefix)
    app.include_router(products_router, prefix=api_v1_prefix)
    app.include_router(customers_router, prefix=api_v1_prefix)
    app.include_router(orders_router, prefix=api_v1_prefix)
    app.include_router(data_sources_router, prefix=api_v1_prefix)
    app.include_router(data_quality_router, prefix=api_v1_prefix)

    return app


app = create_app()

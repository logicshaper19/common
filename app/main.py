"""
FastAPI application main module.
"""
import uuid
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import time

from app.core.config import settings
from app.core.database import init_db, get_db
from app.core.logging import configure_logging, log_request, log_response, get_logger
from app.core.redis import init_redis, close_redis
from app.core.documentation import custom_openapi, get_custom_swagger_ui_html, get_custom_redoc_html
from app.core.validation import validation_exception_handler
from app.core.security_headers import SecurityHeadersMiddleware, CORSSecurityMiddleware
from app.core.versioning import APIVersion, create_versioned_router, get_api_version_info
from app.core.error_handling import (
    CommonHTTPException,
    common_exception_handler,
    general_exception_handler
)
from app.api.health import router as health_router
from app.api.auth import router as auth_router
from app.api.products import router as products_router
from app.api.purchase_orders import router as purchase_orders_router
from app.api.confirmation import router as confirmation_router
from app.api.traceability import router as traceability_router
from app.api.transparency_jobs import router as transparency_jobs_router
from app.api.notifications import router as notifications_router
from app.api.audit import router as audit_router
from app.api.data_access import router as data_access_router
from app.api.transparency_visualization import router as transparency_visualization_router
# from app.api.viral_analytics import router as viral_analytics_router
from app.api.origin_data import router as origin_data_router
from app.api.business_relationships import router as business_relationships_router
from app.api.batches import router as batches_router
from app.api.performance import router as performance_router
from app.api.v1.sectors import router as sectors_router
from app.services.seed_data import SeedDataService

# Configure logging
configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan manager.
    """
    # Startup
    logger.info("Starting Common Supply Chain Platform", version=settings.app_version)
    
    try:
        # Initialize database
        await init_db()
        logger.info("Database initialized")

        # Seed initial data
        try:
            db = next(get_db())
            seed_service = SeedDataService(db)
            seed_service.seed_all_data()
            logger.info("Initial data seeded")
        except Exception as e:
            logger.warning("Failed to seed initial data", error=str(e))
        finally:
            db.close()
        
        # Initialize Redis (optional for development)
        try:
            await init_redis()
            logger.info("Redis initialized")
        except Exception as e:
            logger.warning("Redis not available, continuing without caching", error=str(e))
        
        yield
        
    finally:
        # Shutdown
        logger.info("Shutting down application")
        await close_redis()


# Create FastAPI application
app = FastAPI(
    title="Common Supply Chain Platform API",
    version=settings.app_version,
    description="Supply chain transparency platform with unified Purchase Order system",
    docs_url=None,  # Custom docs endpoint
    redoc_url=None,  # Custom redoc endpoint
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Set custom OpenAPI schema
app.openapi = lambda: custom_openapi(app)

# Add security headers middleware
app.add_middleware(SecurityHeadersMiddleware)

# Add enhanced CORS middleware
app.add_middleware(
    CORSSecurityMiddleware,
    allowed_origins=settings.allowed_origins_list,
    allow_credentials=True
)

# Add trusted host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"] if settings.debug else ["localhost", "127.0.0.1"]
)


@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    """
    Log all HTTP requests and responses.
    """
    # Generate request ID
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    # Log request
    start_time = time.time()
    log_request(
        request_id=request_id,
        method=request.method,
        path=request.url.path,
        query_params=str(request.query_params),
        client_ip=request.client.host if request.client else None,
    )
    
    # Process request
    response = await call_next(request)
    
    # Log response
    duration_ms = (time.time() - start_time) * 1000
    log_response(
        request_id=request_id,
        status_code=response.status_code,
        duration_ms=duration_ms,
    )
    
    # Add request ID to response headers
    response.headers["X-Request-ID"] = request_id
    
    return response


# Add exception handlers
from fastapi.exceptions import RequestValidationError
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(CommonHTTPException, common_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)


# Custom documentation endpoints
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    """Custom Swagger UI with enhanced styling."""
    return get_custom_swagger_ui_html(
        openapi_url="/openapi.json",
        title="Common API Documentation"
    )


@app.get("/redoc", include_in_schema=False)
async def custom_redoc_html():
    """Custom ReDoc with enhanced styling."""
    return get_custom_redoc_html(
        openapi_url="/openapi.json",
        title="Common API Documentation"
    )


@app.get("/api/version")
async def api_version_info():
    """Get comprehensive API version information."""
    return get_api_version_info()


# Include routers
# Health endpoint at root level for monitoring
app.include_router(health_router, prefix="/health", tags=["Health"])

# V1 API endpoints
app.include_router(auth_router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(products_router, prefix="/api/v1/products", tags=["Products"])
app.include_router(purchase_orders_router, prefix="/api/v1", tags=["Purchase Orders"])
app.include_router(confirmation_router, prefix="/api/v1", tags=["Confirmation"])
app.include_router(traceability_router, prefix="/api/v1", tags=["Traceability"])
app.include_router(transparency_jobs_router, prefix="/api/v1", tags=["Transparency Jobs"])
app.include_router(notifications_router, prefix="/api/v1", tags=["Notifications"])
app.include_router(audit_router, prefix="/api/v1", tags=["Audit"])
app.include_router(data_access_router, prefix="/api/v1", tags=["Data Access"])
app.include_router(transparency_visualization_router, prefix="/api/v1", tags=["Transparency Visualization"])
# app.include_router(viral_analytics_router, prefix="/api/v1", tags=["Viral Analytics"])
app.include_router(origin_data_router, prefix="/api/v1", tags=["Origin Data"])
app.include_router(business_relationships_router, prefix="/api/v1", tags=["Business Relationships"])
app.include_router(batches_router, prefix="/api/v1", tags=["Batch Tracking"])
app.include_router(performance_router, prefix="/api/v1", tags=["Performance"])
app.include_router(sectors_router, prefix="/api/v1", tags=["Sectors"])


@app.get("/")
async def root():
    """
    Root endpoint.
    """
    return {
        "message": "Common Supply Chain Platform API",
        "version": settings.app_version,
        "status": "running"
    }

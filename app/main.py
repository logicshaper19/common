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
from app.core.documentation import custom_openapi
from app.core.api_versioning import setup_api_versioning, get_version_manager
from app.core.validation import validation_exception_handler
from app.core.security_headers import SecurityHeadersMiddleware, CORSSecurityMiddleware
from app.core.error_handling import (
    CommonHTTPException,
    common_exception_handler,
    general_exception_handler,
    circuit_breaker_exception_handler
)
from app.core.standardized_errors import (
    StandardizedErrorHandler,
    ErrorContext,
    get_error_handler
)
from app.core.caching import cache_warm_up, get_cache_manager
from app.core.rate_limiting import RateLimitMiddleware, advanced_rate_limiter
from app.core.circuit_breaker import CircuitBreakerError
from app.api.health import router as health_router
from app.api.auth import router as auth_router
from app.api.admin import router as admin_router
from app.api.users import router as users_router
from app.api.products import router as products_router
from app.api.v1.purchase_orders import router as purchase_orders_router
from app.api.simple_purchase_orders import router as simple_purchase_orders_router
from app.api.simple_relationships import router as simple_relationships_router
from app.api.confirmation import router as confirmation_router
from app.api.traceability import router as traceability_router
from app.api.transparency_jobs import router as transparency_jobs_router
from app.api.notifications import router as notifications_router
from app.api.audit import router as audit_router
from app.api.data_access import router as data_access_router
from app.api.transparency_visualization import router as transparency_visualization_router
from app.api.transparency import router as transparency_router
from app.api.origin_data import router as origin_data_router
from app.api.business_relationships import router as business_relationships_router
from app.api.batches import router as batches_router
from app.api.performance import router as performance_router
from app.api.v1.sectors import router as sectors_router
from app.api.documents import router as documents_router
from app.api.compliance import router as compliance_router
from app.api.team_invitations import router as team_invitations_router
from app.api.amendments import router as amendments_router
from app.api.erp_sync import router as erp_sync_router
from app.api.v1.endpoints.brands import router as brands_router
from app.api.tier_requirements import router as tier_requirements_router
from app.api.deterministic_transparency import router as deterministic_transparency_router
from app.api.admin_migration import router as admin_migration_router
from app.api.debug_transparency import router as debug_transparency_router
from app.api.companies import router as companies_router
from app.api.dashboard_v2 import router as dashboard_v2_router
from app.api.dual_chain_transparency import router as dual_chain_transparency_router
from app.api.transformation_versioning import router as transformation_versioning_router
from app.api.transformation_enhanced import router as transformation_enhanced_router
from app.api.websocket import router as websocket_router
from app.services.seed_data import SeedDataService
from app.core.service_container import get_container
from app.services.event_handlers import initialize_event_handlers
from app.core.input_validation_middleware import InputValidationMiddleware, SecurityHeadersValidationMiddleware

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

        # Initialize service container
        try:
            container = get_container()
            logger.info("Service container initialized")
        except Exception as e:
            logger.warning("Service container initialization failed", error=str(e))

        # Initialize event handlers
        try:
            initialize_event_handlers()
            logger.info("Event handlers initialized")
        except Exception as e:
            logger.warning("Event handlers initialization failed", error=str(e))

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

# Setup API versioning
setup_api_versioning(app)

# Add trusted host middleware (first to process requests)
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"] if settings.debug else ["localhost", "127.0.0.1"]
)

# Add security headers middleware (second to process requests)
app.add_middleware(SecurityHeadersMiddleware)

# Add input validation middleware (third to process requests) - temporarily disabled
# app.add_middleware(
#     InputValidationMiddleware,
#     validate_query_params=True,
#     validate_path_params=True,
#     validate_request_body=True,
#     max_request_size=10 * 1024 * 1024,  # 10MB
#     excluded_paths=['/docs', '/redoc', '/openapi.json', '/health', '/metrics']
# )

# Add security headers validation middleware - temporarily disabled
# app.add_middleware(SecurityHeadersValidationMiddleware)

# Add standard CORS middleware for development (last to process requests, first to add headers)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://localhost:8080", "http://127.0.0.1:3000", "http://127.0.0.1:3001", "http://127.0.0.1:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add enhanced CORS middleware
# app.add_middleware(
#     CORSSecurityMiddleware,
#     allowed_origins=settings.allowed_origins_list,
#     allow_credentials=True
# )


# Enhanced middleware with correlation ID support

# Add correlation ID middleware
# app.add_middleware(CorrelationIDMiddleware)

# Add rate limiting middleware
app.add_middleware(RateLimitMiddleware)


# Add exception handlers
from fastapi.exceptions import RequestValidationError
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(CircuitBreakerError, circuit_breaker_exception_handler)
app.add_exception_handler(CommonHTTPException, common_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Add standardized error handler
@app.exception_handler(Exception)
async def standardized_exception_handler(request: Request, exc: Exception):
    """Standardized exception handler for all unhandled exceptions."""
    error_handler = get_error_handler()
    
    # Create error context
    context = ErrorContext(
        request_id=getattr(request.state, 'request_id', None),
        endpoint=str(request.url.path),
        method=request.method,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get('user-agent')
    )
    
    # Handle the exception
    error = error_handler.handle_exception(exc, context)
    
    # Log the error
    error_handler.log_error(error)
    
    # Return standardized response
    return error_handler.to_json_response(error)


# Application startup event
@app.on_event("startup")
async def startup_event():
    """Application startup event handler."""
    logger.info("Starting up application...")
    
    # Initialize Redis
    await init_redis()
    
    # Initialize service container
    service_container = ServiceContainer()
    service_container.initialize()
    
    # Setup API versioning
    version_manager = get_version_manager()
    setup_api_versioning(app, version_manager)
    
    # Warm up cache
    try:
        cache_warm_up()
        logger.info("Cache warm-up completed")
    except Exception as e:
        logger.warning(f"Cache warm-up failed: {e}")
    
    logger.info("Application startup completed")


# Custom documentation endpoints
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    """Custom Swagger UI with enhanced styling."""
    from fastapi.openapi.docs import get_swagger_ui_html
    return get_swagger_ui_html(
        openapi_url="/openapi.json",
        title="Common API Documentation"
    )


@app.get("/redoc", include_in_schema=False)
async def custom_redoc_html():
    """Custom ReDoc with enhanced styling."""
    from fastapi.openapi.docs import get_redoc_html
    return get_redoc_html(
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
app.include_router(admin_router, prefix="/api/v1/admin", tags=["Admin"])
app.include_router(users_router, prefix="/api/v1/users", tags=["Users"])
app.include_router(companies_router, prefix="/api/v1/companies", tags=["Companies"])
app.include_router(products_router, prefix="/api/v1/products", tags=["Products"])
app.include_router(purchase_orders_router, prefix="/api/v1", tags=["Purchase Orders"])
app.include_router(simple_purchase_orders_router, prefix="/api/v1/simple", tags=["Simple Purchase Orders"])
app.include_router(simple_relationships_router, tags=["Simple Relationships"])
app.include_router(confirmation_router, prefix="/api/v1", tags=["Confirmation"])
app.include_router(traceability_router, prefix="/api/v1", tags=["Traceability"])
app.include_router(transparency_jobs_router, prefix="/api/v1", tags=["Transparency Jobs"])
app.include_router(notifications_router, prefix="/api/v1", tags=["Notifications"])
app.include_router(audit_router, prefix="/api/v1", tags=["Audit"])
app.include_router(data_access_router, prefix="/api/v1", tags=["Data Access"])
app.include_router(transparency_visualization_router, prefix="/api/v1", tags=["Transparency Visualization"])
app.include_router(transparency_router, prefix="/api/v1", tags=["Transparency"])
app.include_router(origin_data_router, prefix="/api/v1", tags=["Origin Data"])
app.include_router(business_relationships_router, prefix="/api/v1", tags=["Business Relationships"])
app.include_router(batches_router, prefix="/api/v1", tags=["Batch Tracking"])
app.include_router(performance_router, prefix="/api/v1", tags=["Performance"])
app.include_router(sectors_router, prefix="/api/v1", tags=["Sectors"])
app.include_router(documents_router, prefix="/api/v1", tags=["Documents"])
app.include_router(compliance_router, prefix="/api/v1", tags=["Compliance"])
app.include_router(team_invitations_router, prefix="/api/v1/team", tags=["Team Management"])
app.include_router(amendments_router, prefix="/api/v1", tags=["Amendments"])
app.include_router(erp_sync_router, prefix="/api/v1", tags=["ERP Sync"])
app.include_router(brands_router, prefix="/api/v1/brands", tags=["Brands"])
app.include_router(tier_requirements_router, tags=["Tier Requirements"])
app.include_router(deterministic_transparency_router, prefix="/api/v1", tags=["Deterministic Transparency"])
app.include_router(admin_migration_router, prefix="/api/v1", tags=["Admin Migration"])
app.include_router(debug_transparency_router, prefix="/api/v1", tags=["Debug Transparency"])
app.include_router(dual_chain_transparency_router, tags=["Dual-Chain Transparency"])
app.include_router(transformation_versioning_router, prefix="/api/v1", tags=["Transformation Versioning"])
app.include_router(transformation_enhanced_router, prefix="/api/v1", tags=["Enhanced Transformations"])
app.include_router(dashboard_v2_router, prefix="/api/v2/dashboard", tags=["Dashboard V2"])

# WebSocket endpoints (no prefix)
app.include_router(websocket_router, tags=["WebSocket"])


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

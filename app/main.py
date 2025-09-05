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
from app.api.health import router as health_router
from app.api.auth import router as auth_router
from app.api.products import router as products_router
from app.api.purchase_orders import router as purchase_orders_router
from app.api.confirmation import router as confirmation_router
from app.api.traceability import router as traceability_router
from app.api.origin_data import router as origin_data_router
from app.api.business_relationships import router as business_relationships_router
from app.api.batches import router as batches_router
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
    title=settings.app_name,
    version=settings.app_version,
    description="Supply chain transparency platform with unified Purchase Order system",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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


# Include routers
app.include_router(health_router, prefix="/health", tags=["Health"])
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(products_router, prefix="/products", tags=["Products"])
app.include_router(purchase_orders_router, tags=["Purchase Orders"])
app.include_router(confirmation_router, tags=["Confirmation"])
app.include_router(traceability_router, tags=["Traceability"])
app.include_router(origin_data_router, tags=["Origin Data"])
app.include_router(business_relationships_router, tags=["Business Relationships"])
app.include_router(batches_router, tags=["Batch Tracking"])


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

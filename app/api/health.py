"""
Health check endpoints for monitoring application status.
"""
from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.database import get_db
from app.core.redis import get_redis
from app.core.config import settings
from app.core.logging import get_logger
from app.core.monitoring import health_manager, HealthStatus

logger = get_logger(__name__)
router = APIRouter()


@router.get("/")
async def health_check() -> Dict[str, Any]:
    """
    Basic health check endpoint.
    
    Returns:
        Health status information
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.app_version,
        "service": "common-api",
        "environment": getattr(settings, 'environment', 'development')
    }


@router.get("/detailed")
async def detailed_health_check() -> Dict[str, Any]:
    """
    Detailed health check with all service dependencies.

    Returns:
        Comprehensive health status with all dependencies

    Raises:
        HTTPException: If service is unhealthy
    """
    overall_status, health_summary = await health_manager.get_overall_health_status()

    # Set HTTP status code based on health
    if overall_status == HealthStatus.UNHEALTHY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=health_summary
        )
    elif overall_status == HealthStatus.DEGRADED:
        # Return 200 but indicate degraded performance
        health_summary["warning"] = "Service is degraded but operational"

    return health_summary


@router.get("/ready")
async def readiness_check(
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Readiness check that verifies all dependencies are available.
    
    Args:
        db: Database session
        
    Returns:
        Readiness status with dependency checks
        
    Raises:
        HTTPException: If any dependency is unavailable
    """
    checks = {}
    overall_status = "ready"
    
    # Check database connection
    try:
        db.execute(text("SELECT 1"))
        checks["database"] = {"status": "healthy", "message": "Connected"}
        logger.debug("Database health check passed")
    except Exception as e:
        checks["database"] = {"status": "unhealthy", "message": str(e)}
        overall_status = "not_ready"
        logger.error("Database health check failed", error=str(e))
    
    # Check Redis connection
    try:
        redis_client = await get_redis()
        await redis_client.ping()
        checks["redis"] = {"status": "healthy", "message": "Connected"}
        logger.debug("Redis health check passed")
    except Exception as e:
        checks["redis"] = {"status": "unhealthy", "message": str(e)}
        overall_status = "not_ready"
        logger.error("Redis health check failed", error=str(e))
    
    response = {
        "status": overall_status,
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.app_version,
        "service": "common-api",
        "checks": checks
    }
    
    if overall_status != "ready":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=response
        )
    
    return response


@router.get("/live")
async def liveness_check() -> Dict[str, Any]:
    """
    Liveness check for Kubernetes/container orchestration.
    
    Returns:
        Simple liveness status
    """
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "common-api"
    }

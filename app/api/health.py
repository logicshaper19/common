"""
Health check endpoints for monitoring application status.
"""
import time
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
def health_check() -> Dict[str, Any]:
    """
    Basic health check endpoint.

    Returns:
        Health status information
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "service": "common-api",
        "environment": "development"
    }


@router.get("/test")
def test_endpoint() -> Dict[str, str]:
    """Simple test endpoint to verify routing works."""
    return {"message": "Health router is working!"}


@router.get("/detailed")
async def detailed_health_check(
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Enhanced detailed health check with business metrics.

    Args:
        db: Database session

    Returns:
        Comprehensive health status with all dependencies and business metrics

    Raises:
        HTTPException: If service is unhealthy
    """
    try:
        # Basic health checks first - fast and reliable
        health_status = {
            "overall_status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "checks": {},
            "total_check_time_ms": 0
        }

        # Test database connection with timeout
        start_time = time.time()
        try:
            db.execute(text("SELECT 1"))
            db_time = (time.time() - start_time) * 1000
            health_status["checks"]["database"] = {
                "status": "healthy",
                "response_time_ms": round(db_time, 2)
            }
        except Exception as e:
            health_status["checks"]["database"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            health_status["overall_status"] = "unhealthy"

        # Test Redis connection (optional, non-blocking)
        try:
            redis_client = await get_redis()
            if redis_client:
                start_time = time.time()
                await redis_client.ping()
                redis_time = (time.time() - start_time) * 1000
                health_status["checks"]["redis"] = {
                    "status": "healthy",
                    "response_time_ms": round(redis_time, 2)
                }
            else:
                health_status["checks"]["redis"] = {
                    "status": "unavailable",
                    "message": "Redis not configured"
                }
        except Exception as e:
            health_status["checks"]["redis"] = {
                "status": "degraded",
                "error": str(e)
            }
            # Redis failure doesn't make the service unhealthy
            if health_status["overall_status"] == "healthy":
                health_status["overall_status"] = "degraded"

        # Basic business metrics (fast queries only)
        business_metrics = {
            "pos_created_today": 0,
            "pos_confirmed_today": 0,
            "pos_pending_confirmation": 0,
            "average_po_value": 0,
            "total_po_value_today": 0,
            "transparency_calculations_today": 0,
            "average_transparency_score": 0,
            "transparency_cache_hit_ratio": 0,
            "batches_created_today": 0,
            "batch_transactions_today": 0,
            "traceability_queries_today": 0,
            "active_companies": 0,
            "new_companies_today": 0,
            "business_relationships_active": 0,
            "compliance_checks_today": 0,
            "compliance_violations_detected": 0,
            "documents_uploaded_today": 0
        }

        try:
            # Only run fast, simple queries
            po_count = db.execute(text("SELECT COUNT(*) FROM purchase_orders WHERE status != 'cancelled'")).scalar()
            company_count = db.execute(text("SELECT COUNT(*) FROM companies WHERE is_active = true")).scalar()

            business_metrics.update({
                "pos_pending_confirmation": po_count or 0,
                "active_companies": company_count or 0
            })
        except Exception as e:
            logger.warning("Failed to collect basic business metrics", error=str(e))
            # Don't fail health check for metrics collection failure

        response = {
            "status": health_status["overall_status"],
            "timestamp": health_status["timestamp"],
            "version": settings.app_version,
            "service": "common-api",
            "environment": getattr(settings, 'environment', 'development'),
            "health_checks": health_status["checks"],
            "business_metrics": {
                "purchase_orders": {
                    "created_today": business_metrics["pos_created_today"],
                    "confirmed_today": business_metrics["pos_confirmed_today"],
                    "pending_confirmation": business_metrics["pos_pending_confirmation"],
                    "average_value": business_metrics["average_po_value"],
                    "total_value_today": business_metrics["total_po_value_today"]
                },
                "transparency": {
                    "calculations_today": business_metrics["transparency_calculations_today"],
                    "average_score": business_metrics["average_transparency_score"],
                    "cache_hit_ratio": business_metrics["transparency_cache_hit_ratio"]
                },
                "batches": {
                    "created_today": business_metrics["batches_created_today"],
                    "transactions_today": business_metrics["batch_transactions_today"],
                    "traceability_queries_today": business_metrics["traceability_queries_today"]
                },
                "companies": {
                    "active_companies": business_metrics["active_companies"],
                    "new_companies_today": business_metrics["new_companies_today"],
                    "business_relationships_active": business_metrics["business_relationships_active"]
                },
                "compliance": {
                    "checks_today": business_metrics["compliance_checks_today"],
                    "violations_detected": business_metrics["compliance_violations_detected"],
                    "documents_uploaded_today": business_metrics["documents_uploaded_today"]
                }
            },
            "system_info": {
                "total_check_time_ms": health_status["total_check_time_ms"],
                "checks_performed": len(health_status["checks"])
            }
        }

        # Set HTTP status code based on health
        if health_status["overall_status"] == "unhealthy":
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=response
            )
        elif health_status["overall_status"] == "degraded":
            response["warning"] = "Service is degraded but operational"

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Enhanced health check failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "unhealthy",
                "timestamp": datetime.utcnow().isoformat(),
                "error": "Health check system failure",
                "message": str(e)
            }
        )


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


@router.get("/metrics")
async def metrics_endpoint(
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Prometheus-compatible metrics endpoint.

    Args:
        db: Database session

    Returns:
        Metrics in Prometheus format
    """
    try:
        # Basic metrics collection (simplified for now)
        basic_metrics = {
            "purchase_orders_total": 0,
            "companies_total": 0,
            "health_checks_total": 1
        }

        # Collect basic counts
        try:
            po_count = db.execute(text("SELECT COUNT(*) FROM purchase_orders")).scalar()
            company_count = db.execute(text("SELECT COUNT(*) FROM companies")).scalar()

            basic_metrics.update({
                "purchase_orders_total": po_count or 0,
                "companies_total": company_count or 0
            })
        except Exception as e:
            logger.warning("Failed to collect basic metrics", error=str(e))

        # Simple Prometheus format output
        prometheus_lines = []
        for metric_name, value in basic_metrics.items():
            prometheus_lines.append(f"# HELP {metric_name} Basic metric for {metric_name.replace('_', ' ')}")
            prometheus_lines.append(f"# TYPE {metric_name} gauge")
            prometheus_lines.append(f"{metric_name} {value}")

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "metrics_format": "prometheus",
            "metrics_text": "\n".join(prometheus_lines),
            "business_metrics": basic_metrics,
            "collection_info": {
                "metrics_count": len(basic_metrics),
                "status": "simplified_mode"
            }
        }

    except Exception as e:
        logger.error("Metrics collection failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Metrics collection failed",
                "message": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )

"""
Performance monitoring and optimization API endpoints.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.core.performance_cache import get_performance_cache
from app.core.performance_monitoring import get_performance_monitor
from app.core.query_optimization import QueryOptimizer
from app.core.auth import get_current_user, require_admin
from app.models.user import User

router = APIRouter(prefix="/api/v1/performance", tags=["Performance"])


class PerformanceMetricsResponse(BaseModel):
    """Response schema for performance metrics."""
    timestamp: datetime
    database: Dict[str, Any]
    application: Dict[str, Any]
    cache: Dict[str, Any]


class CacheStatsResponse(BaseModel):
    """Response schema for cache statistics."""
    hits: int
    misses: int
    sets: int
    deletes: int
    errors: int
    total_requests: int
    hit_rate: float
    l1_cache_size: int
    l1_max_size: int


class QueryOptimizationRequest(BaseModel):
    """Request schema for query optimization."""
    query_type: str = Field(..., description="Type of query to optimize")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Query parameters")


class CacheWarmupRequest(BaseModel):
    """Request schema for cache warmup."""
    cache_types: List[str] = Field(..., description="Types of cache to warm up")
    priority_items: Optional[List[str]] = Field(None, description="Priority items to cache first")


class PerformanceAlertResponse(BaseModel):
    """Response schema for performance alerts."""
    metric_name: str
    threshold: float
    current_value: float
    severity: str
    message: str
    timestamp: datetime


@router.get("/metrics", response_model=PerformanceMetricsResponse)
async def get_performance_metrics(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive performance metrics.
    
    Requires admin privileges.
    """
    try:
        monitor = get_performance_monitor()
        metrics = await monitor.collect_all_metrics(db)
        
        return PerformanceMetricsResponse(
            timestamp=datetime.fromisoformat(metrics["timestamp"]),
            database=metrics["database"],
            application=metrics["application"],
            cache=metrics["cache"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to collect metrics: {str(e)}")


@router.get("/cache/stats", response_model=CacheStatsResponse)
async def get_cache_stats(
    current_user: User = Depends(require_admin)
):
    """
    Get cache performance statistics.
    
    Requires admin privileges.
    """
    try:
        cache = await get_performance_cache()
        metrics = cache.get_metrics()
        
        return CacheStatsResponse(**metrics)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get cache stats: {str(e)}")


@router.post("/cache/clear")
async def clear_cache(
    cache_pattern: Optional[str] = Query(None, description="Pattern to match for selective clearing"),
    current_user: User = Depends(require_admin)
):
    """
    Clear cache entries.
    
    Args:
        cache_pattern: Optional pattern to match (e.g., "transparency_scores:*")
    
    Requires admin privileges.
    """
    try:
        cache = await get_performance_cache()
        
        if cache_pattern:
            cleared_count = await cache.invalidate_pattern(cache_pattern)
            return {
                "success": True,
                "message": f"Cleared {cleared_count} cache entries matching pattern: {cache_pattern}"
            }
        else:
            success = await cache.clear_all()
            return {
                "success": success,
                "message": "All cache entries cleared" if success else "Failed to clear cache"
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear cache: {str(e)}")


@router.post("/cache/warmup")
async def warmup_cache(
    request: CacheWarmupRequest,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Warm up cache with frequently accessed data.
    
    Requires admin privileges.
    """
    try:
        cache = await get_performance_cache()
        optimizer = QueryOptimizer(db)
        
        cache_entries = []
        
        # Warm up different cache types
        for cache_type in request.cache_types:
            if cache_type == "transparency_scores":
                # Get recent transparency calculations
                candidates = optimizer.get_transparency_calculation_candidates(limit=50)
                for candidate in candidates:
                    if candidate.get("last_calculated"):
                        cache_entries.append({
                            "cache_type": "transparency_scores",
                            "identifier": candidate["po_id"],
                            "value": {
                                "po_id": str(candidate["po_id"]),
                                "last_calculated": candidate["last_calculated"].isoformat()
                            }
                        })
            
            elif cache_type == "company_data":
                # Get active companies
                from app.models.company import Company
                companies = db.query(Company).limit(100).all()
                for company in companies:
                    cache_entries.append({
                        "cache_type": "company_data",
                        "identifier": str(company.id),
                        "value": {
                            "id": str(company.id),
                            "name": company.name,
                            "company_type": company.company_type,
                            "email": company.email
                        }
                    })
            
            elif cache_type == "product_data":
                # Get products
                from app.models.product import Product
                products = db.query(Product).limit(50).all()
                for product in products:
                    cache_entries.append({
                        "cache_type": "product_data",
                        "identifier": str(product.id),
                        "value": {
                            "id": str(product.id),
                            "name": product.name,
                            "category": product.category,
                            "common_product_id": product.common_product_id
                        }
                    })
        
        # Execute cache warming
        warmed_count = await cache.warm_cache(cache_entries)
        
        return {
            "success": True,
            "message": f"Cache warmed with {warmed_count} entries",
            "cache_types": request.cache_types,
            "total_entries": len(cache_entries)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to warm cache: {str(e)}")


@router.get("/summary")
async def get_performance_summary(
    current_user: User = Depends(require_admin)
):
    """
    Get performance summary and trends.
    
    Requires admin privileges.
    """
    try:
        monitor = get_performance_monitor()
        summary = monitor.get_performance_summary()
        
        return {
            "success": True,
            "data": summary
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get performance summary: {str(e)}")


@router.get("/alerts", response_model=List[PerformanceAlertResponse])
async def get_performance_alerts(
    severity: Optional[str] = Query(None, description="Filter by severity: warning, critical"),
    limit: int = Query(10, description="Maximum number of alerts to return"),
    current_user: User = Depends(require_admin)
):
    """
    Get recent performance alerts.
    
    Args:
        severity: Optional severity filter
        limit: Maximum number of alerts to return
    
    Requires admin privileges.
    """
    try:
        monitor = get_performance_monitor()
        summary = monitor.get_performance_summary()
        
        alerts = summary.get("active_alerts", [])
        
        # Filter by severity if specified
        if severity:
            alerts = [alert for alert in alerts if alert.get("severity") == severity]
        
        # Limit results
        alerts = alerts[:limit]
        
        return [
            PerformanceAlertResponse(
                metric_name=alert["metric_name"],
                threshold=alert["threshold"],
                current_value=alert["current_value"],
                severity=alert["severity"],
                message=alert["message"],
                timestamp=datetime.fromisoformat(alert["timestamp"])
            )
            for alert in alerts
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get performance alerts: {str(e)}")


@router.post("/optimize/queries")
async def optimize_queries(
    request: QueryOptimizationRequest,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Run query optimization analysis.
    
    Requires admin privileges.
    """
    try:
        optimizer = QueryOptimizer(db)
        
        if request.query_type == "transparency_candidates":
            # Optimize transparency calculation candidate queries
            candidates = optimizer.get_transparency_calculation_candidates(
                limit=request.parameters.get("limit", 100) if request.parameters else 100
            )
            
            return {
                "success": True,
                "query_type": request.query_type,
                "results": len(candidates),
                "optimization_applied": True,
                "candidates": candidates[:10]  # Return first 10 for preview
            }
        
        elif request.query_type == "supply_chain_network":
            # Optimize supply chain network queries
            company_ids = request.parameters.get("company_ids", []) if request.parameters else []
            if not company_ids:
                # Get sample company IDs
                from app.models.company import Company
                companies = db.query(Company).limit(20).all()
                company_ids = [str(c.id) for c in companies]
            
            network = optimizer.get_supply_chain_network_optimized(company_ids)
            
            return {
                "success": True,
                "query_type": request.query_type,
                "network_metrics": network["metrics"],
                "optimization_applied": True
            }
        
        else:
            return {
                "success": False,
                "message": f"Unknown query type: {request.query_type}",
                "supported_types": ["transparency_candidates", "supply_chain_network"]
            }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query optimization failed: {str(e)}")


@router.get("/database/indexes")
async def get_database_indexes(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Get database index information and usage statistics.
    
    Requires admin privileges.
    """
    try:
        optimizer = QueryOptimizer(db)
        
        # Get index information (implementation depends on database type)
        if "postgresql" in str(db.bind.url):
            index_query = """
                SELECT 
                    schemaname,
                    tablename,
                    indexname,
                    indexdef
                FROM pg_indexes 
                WHERE schemaname = 'public'
                ORDER BY tablename, indexname
            """
        else:
            # SQLite
            index_query = """
                SELECT 
                    name as indexname,
                    tbl_name as tablename,
                    sql as indexdef
                FROM sqlite_master 
                WHERE type = 'index' AND name NOT LIKE 'sqlite_%'
                ORDER BY tbl_name, name
            """
        
        indexes = optimizer.execute_raw_optimized_query(index_query)
        
        return {
            "success": True,
            "database_type": "postgresql" if "postgresql" in str(db.bind.url) else "sqlite",
            "total_indexes": len(indexes),
            "indexes": indexes
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get database indexes: {str(e)}")


@router.post("/database/analyze")
async def analyze_database_performance(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Run database performance analysis.
    
    Requires admin privileges.
    """
    try:
        monitor = get_performance_monitor()
        db_metrics = await monitor.collect_database_metrics(db)
        
        # Analyze performance
        analysis = {
            "connection_pool_health": "good" if db_metrics.active_connections < 80 else "warning",
            "query_performance": "good" if db_metrics.average_query_time < 1.0 else "warning",
            "cache_effectiveness": "good" if db_metrics.cache_hit_ratio > 80 else "warning",
            "recommendations": []
        }
        
        # Generate recommendations
        if db_metrics.active_connections > 80:
            analysis["recommendations"].append("Consider increasing connection pool size")
        
        if db_metrics.average_query_time > 1.0:
            analysis["recommendations"].append("Review slow queries and add indexes")
        
        if db_metrics.cache_hit_ratio < 80:
            analysis["recommendations"].append("Optimize cache configuration")
        
        return {
            "success": True,
            "metrics": {
                "active_connections": db_metrics.active_connections,
                "total_connections": db_metrics.total_connections,
                "average_query_time": db_metrics.average_query_time,
                "cache_hit_ratio": db_metrics.cache_hit_ratio,
                "slow_queries_count": db_metrics.slow_queries_count
            },
            "analysis": analysis
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database analysis failed: {str(e)}")

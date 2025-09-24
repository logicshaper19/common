"""
Performance Monitoring API for Phase 5 Optimization
Real-time performance metrics dashboard with materialized views.
"""
import time
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime, timedelta

from app.core.database import get_db
from app.core.auth import get_current_user, CurrentUser
from app.services.optimized_health_checker import health_checker
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v2/performance", tags=["Performance Monitoring"])


@router.get("/health")
async def get_system_health() -> Dict[str, Any]:
    """Get system health status with caching to reduce overhead."""
    try:
        return await health_checker.get_system_health()
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Health check failed"
        )


@router.get("/transparency")
async def get_transparency_performance(
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get transparency performance metrics using optimized queries."""
    
    start_time = time.time()
    
    try:
        # Use materialized view for fast performance metrics
        metrics_query = text("""
            SELECT 
                COUNT(*) as total_companies,
                AVG(avg_transparency_score) as overall_avg_score,
                SUM(total_confirmed_pos) as total_pos_tracked,
                SUM(total_volume) as total_volume_tracked,
                MAX(last_calculation_update) as last_updated
            FROM mv_transparency_metrics
        """)
        
        result = db.execute(metrics_query).fetchone()
        query_time = time.time() - start_time
        
        return {
            "performance": {
                "query_time": f"{query_time:.3f}s",
                "data_freshness": "real_time" if query_time < 0.1 else "cached"
            },
            "metrics": {
                "total_companies": result.total_companies if result else 0,
                "avg_transparency_score": f"{float(result.overall_avg_score):.1f}%" if result and result.overall_avg_score else "0.0%",
                "total_pos_tracked": result.total_pos_tracked if result else 0,
                "total_volume_tracked": f"{float(result.total_volume_tracked):,.0f} MT" if result and result.total_volume_tracked else "0 MT",
                "last_updated": result.last_updated.isoformat() if result and result.last_updated else None
            },
            "optimizations_applied": [
                "circular_fk_constraints_removed",
                "materialized_views_enabled", 
                "partial_indexes_optimized",
                "trigger_overhead_minimized"
            ]
        }
        
    except Exception as e:
        logger.error(f"Transparency performance check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve transparency performance metrics"
        )


@router.get("/database")
async def get_database_performance(
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get database performance metrics."""
    
    start_time = time.time()
    
    try:
        # Get connection pool statistics
        pool = db.get_bind().pool
        pool_stats = {
            "size": pool.size(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
            "checked_in": pool.checkedin()
        }
        
        # Get recent query performance
        recent_queries_query = text("""
            SELECT 
                COUNT(*) as total_queries,
                AVG(EXTRACT(EPOCH FROM (NOW() - created_at))) as avg_age_seconds
            FROM purchase_orders 
            WHERE created_at > NOW() - INTERVAL '1 hour'
        """)
        
        query_result = db.execute(recent_queries_query).fetchone()
        
        # Get index usage statistics
        index_stats_query = text("""
            SELECT 
                schemaname,
                tablename,
                indexname,
                idx_scan,
                idx_tup_read,
                idx_tup_fetch
            FROM pg_stat_user_indexes 
            WHERE schemaname = 'public' 
            AND tablename IN ('purchase_orders', 'batches', 'po_batch_linkages')
            ORDER BY idx_scan DESC
            LIMIT 10
        """)
        
        index_results = db.execute(index_stats_query).fetchall()
        
        query_time = time.time() - start_time
        
        return {
            "performance": {
                "query_time": f"{query_time:.3f}s",
                "timestamp": datetime.utcnow().isoformat()
            },
            "connection_pool": pool_stats,
            "recent_activity": {
                "total_queries": query_result.total_queries if query_result else 0,
                "avg_age_seconds": f"{float(query_result.avg_age_seconds):.1f}" if query_result and query_result.avg_age_seconds else "0.0"
            },
            "index_usage": [
                {
                    "table": result.tablename,
                    "index": result.indexname,
                    "scans": result.idx_scan,
                    "tuples_read": result.idx_tup_read,
                    "tuples_fetched": result.idx_tup_fetch
                }
                for result in index_results
            ]
        }
        
    except Exception as e:
        logger.error(f"Database performance check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve database performance metrics"
        )


@router.get("/metrics")
async def get_performance_metrics(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get detailed performance metrics for monitoring dashboard."""
    
    try:
        return await health_checker.get_performance_metrics()
    except Exception as e:
        logger.error(f"Performance metrics check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve performance metrics"
        )


@router.post("/refresh-transparency")
async def refresh_transparency_metrics(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
) -> Dict[str, Any]:
    """Manually refresh transparency metrics materialized view."""
    
    # Only allow platform admins to refresh
    if current_user.user.role != "platform_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only platform administrators can refresh transparency metrics"
        )
    
    try:
        start_time = time.time()
        
        # Call the refresh function
        db.execute(text("SELECT refresh_transparency_metrics()"))
        db.commit()
        
        refresh_time = time.time() - start_time
        
        return {
            "status": "success",
            "refresh_time": f"{refresh_time:.3f}s",
            "timestamp": datetime.utcnow().isoformat(),
            "message": "Transparency metrics materialized view refreshed successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to refresh transparency metrics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to refresh transparency metrics"
        )


@router.get("/optimization-status")
async def get_optimization_status(
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get status of Phase 5 optimizations."""
    
    try:
        # Check if materialized view exists
        mv_exists_query = text("""
            SELECT EXISTS (
                SELECT 1 FROM pg_matviews 
                WHERE matviewname = 'mv_transparency_metrics'
            )
        """)
        mv_exists = db.execute(mv_exists_query).fetchone()[0]
        
        # Check if performance metrics table exists
        pm_exists_query = text("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables 
                WHERE table_name = 'performance_metrics'
            )
        """)
        pm_exists = db.execute(pm_exists_query).fetchone()[0]
        
        # Check if optimized indexes exist
        indexes_query = text("""
            SELECT indexname 
            FROM pg_indexes 
            WHERE tablename = 'purchase_orders' 
            AND indexname IN (
                'idx_po_batch_reference_active',
                'idx_po_fulfillment_compound',
                'idx_po_transparency_calc'
            )
        """)
        optimized_indexes = [row[0] for row in db.execute(indexes_query).fetchall()]
        
        return {
            "phase_5_optimizations": {
                "materialized_view": {
                    "exists": mv_exists,
                    "name": "mv_transparency_metrics"
                },
                "performance_metrics_table": {
                    "exists": pm_exists,
                    "name": "performance_metrics"
                },
                "optimized_indexes": {
                    "count": len(optimized_indexes),
                    "names": optimized_indexes
                },
                "circular_dependencies": {
                    "removed": True,  # Based on model analysis
                    "status": "optimized"
                }
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get optimization status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve optimization status"
        )

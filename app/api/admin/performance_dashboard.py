"""
Admin dashboard for monitoring optimization success
Provides comprehensive metrics for purchase order performance optimization
"""

from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
import os

from app.core.database import get_db
from app.core.auth import get_current_user, CurrentUser
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/admin", tags=["Admin Performance Dashboard"])

@router.get("/optimization-dashboard")
def get_optimization_dashboard(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get comprehensive optimization metrics"""
    
    # Check admin permissions
    if current_user.user.role not in ["super_admin", "admin", "platform_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    try:
        # Get cache performance (if available)
        cache_performance = _get_cache_performance()
        
        # Get database performance metrics
        database_performance = _get_database_performance(db)
        
        # Get endpoint performance metrics
        endpoint_performance = _get_endpoint_performance()
        
        # Get optimization flags status
        optimization_flags = _get_optimization_flags()
        
        # Generate recommendations
        recommendations = _generate_optimization_recommendations(
            cache_performance, database_performance, endpoint_performance
        )
        
        return {
            'cache_performance': cache_performance,
            'database_performance': database_performance,
            'endpoint_performance': endpoint_performance,
            'optimization_flags': optimization_flags,
            'recommendations': recommendations,
            'timestamp': _get_current_timestamp()
        }
        
    except Exception as e:
        logger.error(f"Failed to get optimization dashboard: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve optimization metrics"
        )

@router.get("/performance-metrics")
def get_performance_metrics(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get detailed performance metrics for monitoring"""
    
    if current_user.user.role not in ["super_admin", "admin", "platform_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    try:
        # Get purchase order query performance
        po_metrics = _get_purchase_order_metrics(db)
        
        # Get system resource usage
        system_metrics = _get_system_metrics()
        
        return {
            'purchase_order_metrics': po_metrics,
            'system_metrics': system_metrics,
            'timestamp': _get_current_timestamp()
        }
        
    except Exception as e:
        logger.error(f"Failed to get performance metrics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve performance metrics"
        )

def _get_cache_performance() -> Dict[str, Any]:
    """Get cache performance statistics"""
    try:
        # Try to import and get cache stats
        from app.core.simple_cache import cache
        
        if hasattr(cache, 'get_stats'):
            return cache.get_stats()
        else:
            return {
                'available': False,
                'error': 'Cache stats not available'
            }
    except Exception as e:
        return {
            'available': False,
            'error': f'Cache not available: {str(e)}'
        }

def _get_database_performance(db: Session) -> Dict[str, Any]:
    """Get database performance metrics"""
    try:
        # Check index usage
        index_stats = db.execute(text("""
            SELECT 
                schemaname, 
                tablename, 
                indexname, 
                idx_scan, 
                idx_tup_read,
                idx_tup_fetch
            FROM pg_stat_user_indexes 
            WHERE tablename = 'purchase_orders'
            AND indexname LIKE 'idx_po_%'
            ORDER BY idx_scan DESC
        """)).fetchall()
        
        # Get table statistics
        table_stats = db.execute(text("""
            SELECT 
                schemaname,
                tablename,
                n_tup_ins as inserts,
                n_tup_upd as updates,
                n_tup_del as deletes,
                n_live_tup as live_tuples,
                n_dead_tup as dead_tuples
            FROM pg_stat_user_tables 
            WHERE tablename = 'purchase_orders'
        """)).fetchone()
        
        # Get query performance
        query_stats = db.execute(text("""
            SELECT 
                query,
                calls,
                total_time,
                mean_time,
                rows
            FROM pg_stat_statements 
            WHERE query LIKE '%purchase_orders%'
            ORDER BY total_time DESC
            LIMIT 10
        """)).fetchall()
        
        return {
            'index_usage': [dict(row) for row in index_stats],
            'table_statistics': dict(table_stats) if table_stats else {},
            'query_performance': [dict(row) for row in query_stats],
            'available': True
        }
        
    except Exception as e:
        return {
            'available': False,
            'error': f'Database metrics unavailable: {str(e)}'
        }

def _get_endpoint_performance() -> Dict[str, Any]:
    """Get endpoint performance metrics"""
    try:
        # This would typically come from your monitoring system
        # For now, return placeholder data
        return {
            'available': False,
            'note': 'Endpoint metrics require monitoring system integration',
            'suggested_endpoints': [
                '/api/v1/purchase-orders/with-relations',
                '/api/v1/purchase-orders/incoming',
                '/api/v1/purchase-orders/outgoing'
            ]
        }
    except Exception as e:
        return {
            'available': False,
            'error': f'Endpoint metrics unavailable: {str(e)}'
        }

def _get_purchase_order_metrics(db: Session) -> Dict[str, Any]:
    """Get specific purchase order performance metrics"""
    try:
        # Count total purchase orders
        total_pos = db.execute(text("SELECT COUNT(*) FROM purchase_orders")).scalar()
        
        # Count by status
        status_counts = db.execute(text("""
            SELECT status, COUNT(*) as count
            FROM purchase_orders
            GROUP BY status
            ORDER BY count DESC
        """)).fetchall()
        
        # Recent activity (last 24 hours)
        recent_activity = db.execute(text("""
            SELECT COUNT(*) as recent_count
            FROM purchase_orders
            WHERE created_at > NOW() - INTERVAL '24 hours'
        """)).scalar()
        
        return {
            'total_purchase_orders': total_pos,
            'status_breakdown': [dict(row) for row in status_counts],
            'recent_activity_24h': recent_activity,
            'available': True
        }
        
    except Exception as e:
        return {
            'available': False,
            'error': f'Purchase order metrics unavailable: {str(e)}'
        }

def _get_system_metrics() -> Dict[str, Any]:
    """Get system resource metrics"""
    try:
        import psutil
        
        return {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_percent': psutil.disk_usage('/').percent,
            'available': True
        }
    except ImportError:
        return {
            'available': False,
            'error': 'psutil not available for system metrics'
        }
    except Exception as e:
        return {
            'available': False,
            'error': f'System metrics unavailable: {str(e)}'
        }

def _get_optimization_flags() -> Dict[str, Any]:
    """Get current optimization feature flags"""
    return {
        'query_optimization': os.getenv('ENABLE_PO_QUERY_OPTIMIZATION', 'false').lower() == 'true',
        'caching': os.getenv('ENABLE_PO_CACHING', 'false').lower() == 'true',
        'monitoring': os.getenv('ENABLE_PERFORMANCE_MONITORING', 'false').lower() == 'true',
        'v2_features': os.getenv('V2_FEATURES_ENABLED', 'false').lower() == 'true',
        'company_dashboards': os.getenv('V2_COMPANY_DASHBOARDS', 'false').lower() == 'true',
        'admin_features': os.getenv('V2_ADMIN_FEATURES', 'false').lower() == 'true'
    }

def _generate_optimization_recommendations(
    cache_performance: Dict[str, Any],
    database_performance: Dict[str, Any],
    endpoint_performance: Dict[str, Any]
) -> List[str]:
    """Generate optimization recommendations based on current metrics"""
    recommendations = []
    
    # Cache recommendations
    if cache_performance.get('available'):
        hit_ratio = cache_performance.get('hit_ratio', 0)
        if hit_ratio > 0.8:
            recommendations.append("✅ Excellent cache performance - consider expanding to other endpoints")
        elif hit_ratio > 0.6:
            recommendations.append("✅ Good cache performance - monitor for consistency")
        else:
            recommendations.append("⚠️ Low cache hit ratio - review invalidation strategy")
    else:
        recommendations.append("❌ Redis unavailable - check server status")
    
    # Database recommendations
    if database_performance.get('available'):
        index_usage = database_performance.get('index_usage', [])
        if not index_usage:
            recommendations.append("❌ No purchase order indexes found - run migration script")
        else:
            unused_indexes = [idx for idx in index_usage if idx.get('idx_scan', 0) == 0]
            if unused_indexes:
                recommendations.append(f"⚠️ {len(unused_indexes)} unused indexes detected - consider removal")
            else:
                recommendations.append("✅ Database indexes are being utilized effectively")
    else:
        recommendations.append("❌ Database metrics unavailable - check connection")
    
    # Feature flag recommendations
    optimization_flags = _get_optimization_flags()
    if not optimization_flags['query_optimization']:
        recommendations.append("💡 Enable query optimization: ENABLE_PO_QUERY_OPTIMIZATION=true")
    if not optimization_flags['caching']:
        recommendations.append("💡 Enable caching: ENABLE_PO_CACHING=true")
    if not optimization_flags['monitoring']:
        recommendations.append("💡 Enable monitoring: ENABLE_PERFORMANCE_MONITORING=true")
    
    return recommendations

def _get_current_timestamp() -> str:
    """Get current timestamp in ISO format"""
    from datetime import datetime
    return datetime.utcnow().isoformat() + "Z"

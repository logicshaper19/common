"""
Production Query Monitoring for N+1 Query Detection
Monitors actual database query counts in production
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text, event
from sqlalchemy.engine import Engine
from typing import Dict, Any, List
import time
import threading
from collections import defaultdict, deque
from datetime import datetime, timedelta

from app.core.database import get_db
from app.core.auth import get_current_user, CurrentUser
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/admin", tags=["Admin Query Monitoring"])

# Global query monitoring state
query_monitor = {
    "enabled": False,
    "queries": deque(maxlen=1000),  # Keep last 1000 queries
    "endpoint_stats": defaultdict(lambda: {"count": 0, "total_time": 0, "query_counts": []}),
    "lock": threading.Lock()
}

def start_query_monitoring():
    """Start monitoring database queries."""
    if query_monitor["enabled"]:
        return
    
    def log_query(conn, cursor, statement, parameters, context, executemany):
        with query_monitor["lock"]:
            query_info = {
                "timestamp": datetime.utcnow(),
                "statement": str(statement)[:200],  # Truncate long queries
                "parameters": str(parameters)[:100] if parameters else None,
                "executemany": executemany
            }
            query_monitor["queries"].append(query_info)
    
    event.listen(Engine, "before_cursor_execute", log_query)
    query_monitor["enabled"] = True
    logger.info("Query monitoring started")

def stop_query_monitoring():
    """Stop monitoring database queries."""
    if not query_monitor["enabled"]:
        return
    
    event.remove(Engine, "before_cursor_execute", log_query)
    query_monitor["enabled"] = False
    logger.info("Query monitoring stopped")

def record_endpoint_performance(endpoint: str, duration: float, query_count: int):
    """Record performance metrics for an endpoint."""
    with query_monitor["lock"]:
        stats = query_monitor["endpoint_stats"][endpoint]
        stats["count"] += 1
        stats["total_time"] += duration
        stats["query_counts"].append(query_count)
        
        # Keep only last 100 query counts per endpoint
        if len(stats["query_counts"]) > 100:
            stats["query_counts"] = stats["query_counts"][-100:]

@router.post("/query-monitoring/start")
def start_monitoring(
    current_user: CurrentUser = Depends(get_current_user)
):
    """Start query monitoring (admin only)."""
    if current_user.user.role not in ["platform_admin", "admin", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to start query monitoring"
        )
    
    start_query_monitoring()
    return {"message": "Query monitoring started", "status": "active"}

@router.post("/query-monitoring/stop")
def stop_monitoring(
    current_user: CurrentUser = Depends(get_current_user)
):
    """Stop query monitoring (admin only)."""
    if current_user.user.role not in ["platform_admin", "admin", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to stop query monitoring"
        )
    
    stop_query_monitoring()
    return {"message": "Query monitoring stopped", "status": "inactive"}

@router.get("/query-monitoring/status")
def get_monitoring_status(
    current_user: CurrentUser = Depends(get_current_user)
):
    """Get current monitoring status and statistics."""
    if current_user.user.role not in ["platform_admin", "admin", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view monitoring status"
        )
    
    with query_monitor["lock"]:
        recent_queries = list(query_monitor["queries"])[-10:]  # Last 10 queries
        
        endpoint_summaries = {}
        for endpoint, stats in query_monitor["endpoint_stats"].items():
            if stats["count"] > 0:
                avg_time = stats["total_time"] / stats["count"]
                avg_queries = sum(stats["query_counts"]) / len(stats["query_counts"]) if stats["query_counts"] else 0
                
                endpoint_summaries[endpoint] = {
                    "request_count": stats["count"],
                    "avg_response_time": f"{avg_time:.3f}s",
                    "avg_query_count": f"{avg_queries:.1f}",
                    "total_queries": sum(stats["query_counts"]),
                    "potential_n1_issues": len([q for q in stats["query_counts"] if q > 5])  # Flag high query counts
                }
    
    return {
        "monitoring_enabled": query_monitor["enabled"],
        "total_queries_logged": len(query_monitor["queries"]),
        "endpoints_monitored": len(query_monitor["endpoint_stats"]),
        "recent_queries": recent_queries,
        "endpoint_performance": endpoint_summaries,
        "n1_detection": {
            "high_query_endpoints": [
                endpoint for endpoint, summary in endpoint_summaries.items()
                if summary["potential_n1_issues"] > 0
            ],
            "recommendations": _generate_n1_recommendations(endpoint_summaries)
        }
    }

@router.get("/query-monitoring/analysis")
def analyze_query_patterns(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """Analyze query patterns for N+1 detection."""
    if current_user.user.role not in ["platform_admin", "admin", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view query analysis"
        )
    
    try:
        # Get database-level query statistics
        db_stats = db.execute(text("""
            SELECT 
                query,
                calls,
                total_time,
                mean_time,
                rows
            FROM pg_stat_statements 
            WHERE query LIKE '%purchase_orders%'
            ORDER BY calls DESC
            LIMIT 10
        """)).fetchall()
        
        # Analyze recent queries for patterns
        with query_monitor["lock"]:
            recent_queries = list(query_monitor["queries"])[-100:]
            
            # Group queries by pattern
            query_patterns = defaultdict(int)
            for query_info in recent_queries:
                statement = query_info["statement"]
                if "SELECT" in statement.upper():
                    # Extract table name
                    if "purchase_orders" in statement:
                        query_patterns["purchase_orders"] += 1
                    elif "companies" in statement:
                        query_patterns["companies"] += 1
                    elif "products" in statement:
                        query_patterns["products"] += 1
        
        return {
            "database_statistics": [dict(row) for row in db_stats],
            "recent_query_patterns": dict(query_patterns),
            "n1_indicators": {
                "high_company_queries": query_patterns["companies"] > 10,
                "high_product_queries": query_patterns["products"] > 10,
                "potential_n1_detected": query_patterns["companies"] > 5 and query_patterns["products"] > 5
            },
            "recommendations": _generate_analysis_recommendations(query_patterns, db_stats)
        }
        
    except Exception as e:
        logger.error(f"Error analyzing query patterns: {str(e)}")
        return {
            "error": str(e),
            "message": "Query analysis failed - pg_stat_statements may not be enabled"
        }

def _generate_n1_recommendations(endpoint_summaries: Dict[str, Any]) -> List[str]:
    """Generate N+1 detection recommendations."""
    recommendations = []
    
    high_query_endpoints = [
        endpoint for endpoint, summary in endpoint_summaries.items()
        if summary["potential_n1_issues"] > 0
    ]
    
    if high_query_endpoints:
        recommendations.append(f"🚨 Potential N+1 issues detected in: {', '.join(high_query_endpoints)}")
        recommendations.append("💡 Consider adding eager loading with selectinload() or joinedload()")
        recommendations.append("📊 Monitor these endpoints closely in production")
    else:
        recommendations.append("✅ No obvious N+1 query patterns detected")
    
    return recommendations

def _generate_analysis_recommendations(query_patterns: Dict[str, int], db_stats: List) -> List[str]:
    """Generate analysis-based recommendations."""
    recommendations = []
    
    if query_patterns.get("companies", 0) > 10:
        recommendations.append("🔍 High company table queries - check for missing eager loading on company relationships")
    
    if query_patterns.get("products", 0) > 10:
        recommendations.append("🔍 High product table queries - check for missing eager loading on product relationships")
    
    if len(db_stats) > 0:
        most_called = db_stats[0]
        if most_called["calls"] > 100:
            recommendations.append(f"📈 Most called query: {most_called['calls']} calls - consider optimization")
    
    return recommendations

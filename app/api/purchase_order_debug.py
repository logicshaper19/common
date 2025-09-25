"""
Purchase Order Debug API
Performance debugging and testing endpoints
"""
import time
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import event
from sqlalchemy.engine import Engine

from app.core.database import get_db
from app.core.auth import get_current_user_sync, CurrentUser
from app.core.logging import get_logger
from app.db.purchase_order_queries import (
    get_po_performance_test_query,
    get_po_performance_test_query_optimized
)

logger = get_logger(__name__)

router = APIRouter(prefix="/purchase-orders", tags=["purchase-orders-debug"])


@router.get("/debug-performance")
def debug_performance(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user_sync)
):
    """Simple debug endpoint to measure N+1 query performance improvement."""
    
    # Simple query counting setup
    query_count = {"count": 0}
    
    def count_queries(conn, cursor, statement, parameters, context, executemany):
        query_count["count"] += 1
    
    # Register the event listener
    event.listen(Engine, "before_cursor_execute", count_queries)
    
    try:
        # Test without eager loading (N+1 problem)
        query_count["count"] = 0
        start_time = time.time()
        
        pos_slow = get_po_performance_test_query(db, current_user.company_id, 5)
        
        # Access relationships to trigger N+1 queries
        for po in pos_slow:
            try:
                _ = po.buyer_company.name if po.buyer_company else "No buyer"
                _ = po.seller_company.name if po.seller_company else "No seller"
                _ = po.product.name if po.product else "No product"
            except Exception as rel_error:
                logger.warning(f"Relationship access error: {rel_error}")
        
        slow_time = time.time() - start_time
        slow_query_count = query_count["count"]
        
        # Test with eager loading (optimized)
        query_count["count"] = 0
        start_time = time.time()
        
        pos_fast = get_po_performance_test_query_optimized(db, current_user.company_id, 5)
        
        # Access relationships (should not trigger additional queries)
        for po in pos_fast:
            try:
                _ = po.buyer_company.name if po.buyer_company else "No buyer"
                _ = po.seller_company.name if po.seller_company else "No seller"
                _ = po.product.name if po.product else "No product"
            except Exception as rel_error:
                logger.warning(f"Relationship access error: {rel_error}")
        
        fast_time = time.time() - start_time
        fast_query_count = query_count["count"]
        
        # Calculate improvements
        time_improvement = ((slow_time - fast_time) / slow_time * 100) if slow_time > 0 else 0
        query_reduction = slow_query_count - fast_query_count
        query_reduction_percent = (query_reduction / slow_query_count * 100) if slow_query_count > 0 else 0
        
        # Simple production logging
        logger.info(f"N+1 Performance Test: {query_reduction} fewer queries ({query_reduction_percent:.1f}% reduction), "
                   f"{time_improvement:.1f}% time improvement")
        
        return {
            "test_records": len(pos_slow),
            "performance_metrics": {
                "without_eager_loading": {
                    "time": f"{slow_time:.3f}s",
                    "query_count": slow_query_count
                },
                "with_eager_loading": {
                    "time": f"{fast_time:.3f}s", 
                    "query_count": fast_query_count
                },
                "improvements": {
                    "time_improvement": f"{time_improvement:.1f}%",
                    "query_reduction": query_reduction,
                    "query_reduction_percent": f"{query_reduction_percent:.1f}%"
                }
            },
            "n1_problem_solved": query_reduction > 0 and time_improvement > 0,
            "recommendations": _generate_simple_recommendations(time_improvement, query_reduction)
        }
        
    except Exception as e:
        logger.error(f"Error in performance debug: {str(e)}", exc_info=True)
        return {
            "error": str(e),
            "message": "Performance test failed"
        }
    finally:
        # Clean up event listener
        event.remove(Engine, "before_cursor_execute", count_queries)


def _generate_simple_recommendations(time_improvement: float, query_reduction: int) -> list:
    """Generate simple recommendations based on performance test results."""
    recommendations = []
    
    if query_reduction > 0:
        recommendations.append(f"✅ N+1 problem SOLVED: {query_reduction} fewer database queries")
    else:
        recommendations.append("⚠️ No query reduction detected - check relationship configuration")
    
    if time_improvement > 50:
        recommendations.append("🚀 Excellent performance improvement - consider applying to other endpoints")
    elif time_improvement > 20:
        recommendations.append("✅ Good performance improvement - monitor in production")
    elif time_improvement > 0:
        recommendations.append("📈 Modest improvement - consider additional optimizations")
    else:
        recommendations.append("❌ No time improvement - investigate further")
    
    if query_reduction > 5:
        recommendations.append("💡 High query reduction - this optimization will scale well with more data")
    
    return recommendations


@router.post("/test")
def test_create():
    """Simple test endpoint for basic functionality."""
    return {"message": "Test endpoint working", "status": "success"}

"""
Optimized Dashboard API for Phase 5 Performance Optimization
Updated dashboard endpoints using consolidated feature flags and optimized queries.
"""
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.database import get_db
from app.core.auth import get_current_user, CurrentUser
from app.core.consolidated_feature_flags import consolidated_feature_flags
from app.services.permissions import PermissionService
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v2/dashboard", tags=["Dashboard V2 Optimized"])


@router.get("/config")
async def get_dashboard_config(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get complete dashboard configuration using single source of truth."""
    
    try:
        user_role = current_user.user.role
        company_type = current_user.company.company_type
        
        # Get consolidated feature flags (existing)
        config = consolidated_feature_flags.get_dashboard_config(user_role, company_type)
        
        # ADD: Get business permissions using existing PermissionService
        permission_service = PermissionService(db)
        permissions = permission_service.get_user_dashboard_config(current_user.user)
        
        # Combine feature flags with business permissions
        config["permissions"] = permissions
        
        # IMPORTANT: Override dashboard_type with the correct one from PermissionService
        # This ensures plantation_grower maps to originator, etc.
        config["dashboard_type"] = permissions.get("dashboard_type", company_type)
        
        # Add user info (existing)
        config["user_info"].update({
            "id": str(current_user.user.id),
            "email": current_user.user.email,
            "company_name": current_user.company.name,
            "company_id": str(current_user.company.id)
        })
        
        logger.info(
            "Dashboard config generated successfully",
            user_id=str(current_user.user.id),
            company_type=company_type,
            permissions_count=len(permissions)
        )
        
        return config
        
    except Exception as e:
        logger.error(f"Failed to get dashboard config: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve dashboard configuration"
        )


@router.get("/feature-flags")
async def get_feature_flags(
    current_user: CurrentUser = Depends(get_current_user)
) -> Dict[str, bool]:
    """Get feature flags using consolidated system."""
    
    try:
        user_role = current_user.user.role
        company_type = current_user.company.company_type
        
        # Get legacy feature flags for backward compatibility
        return consolidated_feature_flags.get_legacy_feature_flags(user_role, company_type)
        
    except Exception as e:
        logger.error(f"Failed to get feature flags: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve feature flags"
        )


@router.get("/metrics")
async def get_dashboard_metrics(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get dashboard metrics using optimized queries."""
    
    try:
        user_role = current_user.user.role
        company_type = current_user.company.company_type
        company_id = current_user.company.id
        
        # Check if V2 features are enabled for this user
        if not consolidated_feature_flags.is_v2_enabled_for_user(user_role, company_type):
            return {
                "error": "V2 dashboard not enabled for this user",
                "should_use_v2": False
            }
        
        # Get company-specific metrics using optimized queries
        metrics_query = text("""
            SELECT 
                COUNT(*) as total_pos,
                COUNT(CASE WHEN status = 'confirmed' THEN 1 END) as confirmed_pos,
                COUNT(CASE WHEN status = 'in_transit' THEN 1 END) as in_transit_pos,
                COUNT(CASE WHEN status = 'delivered' THEN 1 END) as delivered_pos,
                SUM(CASE WHEN status = 'confirmed' THEN confirmed_quantity ELSE 0 END) as total_volume,
                MAX(created_at) as last_po_created
            FROM purchase_orders 
            WHERE buyer_company_id = :company_id
            AND created_at > NOW() - INTERVAL '30 days'
        """)
        
        result = db.execute(metrics_query, {"company_id": company_id}).fetchone()
        
        # Get transparency metrics from materialized view if available
        transparency_result = None
        try:
            transparency_query = text("""
                SELECT 
                    avg_transparency_score,
                    total_confirmed_pos,
                    total_volume,
                    last_calculation_update
                FROM mv_transparency_metrics
                WHERE buyer_company_id = :company_id
            """)
            
            transparency_result = db.execute(transparency_query, {"company_id": company_id}).fetchone()
        except Exception as e:
            logger.warning(f"Materialized view mv_transparency_metrics not available: {str(e)}")
            # Continue without transparency metrics
        
        return {
            "should_use_v2": True,
            "dashboard_type": company_type,
            "metrics": {
                "purchase_orders": {
                    "total": result.total_pos if result else 0,
                    "confirmed": result.confirmed_pos if result else 0,
                    "in_transit": result.in_transit_pos if result else 0,
                    "delivered": result.delivered_pos if result else 0,
                    "total_volume": float(result.total_volume) if result and result.total_volume else 0.0,
                    "last_created": result.last_po_created.isoformat() if result and result.last_po_created else None
                },
                "transparency": {
                    "score": f"{float(transparency_result.avg_transparency_score):.1f}%" if transparency_result and transparency_result.avg_transparency_score else "0.0%",
                    "pos_tracked": transparency_result.total_confirmed_pos if transparency_result else 0,
                    "volume_tracked": float(transparency_result.total_volume) if transparency_result and transparency_result.total_volume else 0.0,
                    "last_updated": transparency_result.last_calculation_update.isoformat() if transparency_result and transparency_result.last_calculation_update else None
                }
            },
            "feature_flags": consolidated_feature_flags.get_legacy_feature_flags(user_role, company_type),
            "optimizations": {
                "consolidated_feature_flags": True,
                "materialized_views": transparency_result is not None,
                "optimized_queries": True
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get dashboard metrics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve dashboard metrics"
        )


@router.get("/activity")
async def get_recent_activity(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
    limit: int = 20
) -> Dict[str, Any]:
    """Get recent activity using optimized queries."""
    
    try:
        user_role = current_user.user.role
        company_type = current_user.company.company_type
        company_id = current_user.company.id
        
        # Check if V2 features are enabled
        if not consolidated_feature_flags.is_v2_enabled_for_user(user_role, company_type):
            return {"error": "V2 dashboard not enabled for this user"}
        
        # Get recent PO activity
        activity_query = text("""
            SELECT 
                po.id,
                po.po_number,
                po.status,
                po.created_at,
                po.updated_at,
                po.confirmed_at,
                seller.name as seller_name,
                p.name as product_name,
                po.confirmed_quantity,
                po.unit
            FROM purchase_orders po
            JOIN companies seller ON po.seller_company_id = seller.id
            JOIN products p ON po.product_id = p.id
            WHERE po.buyer_company_id = :company_id
            ORDER BY po.updated_at DESC
            LIMIT :limit
        """)
        
        results = db.execute(activity_query, {"company_id": company_id, "limit": limit}).fetchall()
        
        activities = []
        for result in results:
            activities.append({
                "id": str(result.id),
                "po_number": result.po_number,
                "status": result.status,
                "created_at": result.created_at.isoformat(),
                "updated_at": result.updated_at.isoformat(),
                "confirmed_at": result.confirmed_at.isoformat() if result.confirmed_at else None,
                "seller_name": result.seller_name,
                "product_name": result.product_name,
                "quantity": float(result.confirmed_quantity) if result.confirmed_quantity else 0.0,
                "unit": result.unit
            })
        
        return {
            "should_use_v2": True,
            "activities": activities,
            "total_count": len(activities),
            "optimizations": {
                "consolidated_feature_flags": True,
                "optimized_queries": True,
                "single_query_join": True
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get recent activity: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve recent activity"
        )


@router.get("/consolidated-flags")
async def get_consolidated_flags(
    current_user: CurrentUser = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get consolidated feature flag status for debugging."""
    
    try:
        user_role = current_user.user.role
        company_type = current_user.company.company_type
        
        return {
            "consolidated_flags": {
                "v2_features_enabled": consolidated_feature_flags.v2_enabled,
                "company_dashboards": consolidated_feature_flags.company_dashboards,
                "admin_features": consolidated_feature_flags.admin_features
            },
            "user_context": {
                "role": user_role,
                "company_type": company_type
            },
            "legacy_mapping": consolidated_feature_flags.get_legacy_feature_flags(user_role, company_type),
            "enabled_features": consolidated_feature_flags.get_enabled_features(user_role)
        }
        
    except Exception as e:
        logger.error(f"Failed to get consolidated flags: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve consolidated flags"
        )

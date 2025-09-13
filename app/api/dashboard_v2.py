"""
Dashboard V2 API endpoints
Provides feature flags and dashboard configuration for the new role-specific dashboards
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from typing import Dict, Any
from datetime import datetime, timedelta
from uuid import UUID

from app.core.database import get_db
from app.core.auth import get_current_user, CurrentUser
from app.core.feature_flags import (
    feature_flags,
    is_v2_dashboard_brand_enabled,
    is_v2_dashboard_processor_enabled,
    is_v2_dashboard_originator_enabled,
    is_v2_dashboard_trader_enabled,
    is_v2_dashboard_platform_admin_enabled,
    is_v2_notification_center_enabled
)
from app.services.permissions import PermissionService
from app.services.purchase_order import create_purchase_order_service
from app.services.company import CompanyService
from app.services.deterministic_transparency import DeterministicTransparencyService
from app.models.user import User
from app.models.company import Company
from app.models.purchase_order import PurchaseOrder
from app.schemas.purchase_order import PurchaseOrderStatus
from app.models.batch import Batch

router = APIRouter(tags=["dashboard-v2"])


@router.get("/feature-flags")
async def get_feature_flags(
    current_user: CurrentUser = Depends(get_current_user)
) -> Dict[str, bool]:
    """
    Get feature flags relevant to dashboard v2
    Returns only dashboard-related feature flags
    """
    return {
        "v2_dashboard_brand": is_v2_dashboard_brand_enabled(),
        "v2_dashboard_processor": is_v2_dashboard_processor_enabled(),
        "v2_dashboard_originator": is_v2_dashboard_originator_enabled(),
        "v2_dashboard_trader": is_v2_dashboard_trader_enabled(),
        "v2_dashboard_platform_admin": is_v2_dashboard_platform_admin_enabled(),
        "v2_notification_center": is_v2_notification_center_enabled()
    }


@router.get("/config")
async def get_dashboard_config(
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get complete dashboard configuration for current user
    Includes permissions, dashboard type, and feature flags
    """
    permission_service = PermissionService(db)
    dashboard_config = permission_service.get_user_dashboard_config(current_user.user)

    # Add feature flag information
    dashboard_type = dashboard_config.get("dashboard_type", "default")
    feature_flag_key = f"v2_dashboard_{dashboard_type}"

    dashboard_config.update({
        "feature_flags": await get_feature_flags(current_user),
        "should_use_v2": _should_use_v2_dashboard(dashboard_type),
        "user_info": {
            "id": str(current_user.id),
            "role": current_user.role,
            "company_type": current_user.company.company_type,
            "company_name": current_user.company.name
        }
    })
    
    return dashboard_config


def _should_use_v2_dashboard(dashboard_type: str) -> bool:
    """
    Determine if user should see v2 dashboard based on dashboard type and feature flags
    """
    flag_mapping = {
        "brand": is_v2_dashboard_brand_enabled,
        "processor": is_v2_dashboard_processor_enabled,
        "originator": is_v2_dashboard_originator_enabled,
        "trader": is_v2_dashboard_trader_enabled,
        "platform_admin": is_v2_dashboard_platform_admin_enabled,
    }
    
    check_function = flag_mapping.get(dashboard_type)
    if check_function:
        return check_function()
    
    return False


@router.get("/metrics/brand")
async def get_brand_dashboard_metrics(
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get metrics for brand dashboard
    """
    # Verify user is from a brand company
    if current_user.company.company_type != "brand":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Brand dashboard metrics only available to brand companies"
        )

    try:
        company_id = current_user.company_id

        # Get purchase order service
        po_service = create_purchase_order_service(db)
        po_stats = po_service.get_statistics(company_id)

        # Get transparency data
        transparency_service = DeterministicTransparencyService(db)
        transparency_data = transparency_service.get_transparency_overview(company_id)

        # Calculate supply chain overview
        total_pos = po_stats.get("total_count", 0)

        # Count traced orders from transparency data
        traced_to_mill = 0
        traced_to_farm = 0

        if transparency_data and "traceability_summary" in transparency_data:
            summary = transparency_data["traceability_summary"]
            traced_to_mill = summary.get("traced_to_mill", 0)
            traced_to_farm = summary.get("traced_to_plantation", 0)

        transparency_percentage = (traced_to_farm / total_pos * 100) if total_pos > 0 else 0.0

        # Get supplier portfolio data
        active_suppliers = db.query(Company).join(
            PurchaseOrder, Company.id == PurchaseOrder.seller_company_id
        ).filter(
            PurchaseOrder.buyer_company_id == company_id,
            PurchaseOrder.status.in_([PurchaseOrderStatus.CONFIRMED, PurchaseOrderStatus.IN_PROGRESS])
        ).distinct().count()

        pending_onboarding = db.query(Company).join(
            PurchaseOrder, Company.id == PurchaseOrder.seller_company_id
        ).filter(
            PurchaseOrder.buyer_company_id == company_id,
            PurchaseOrder.status == PurchaseOrderStatus.PENDING
        ).distinct().count()

        # Risk alerts (simplified - could be enhanced with actual risk calculation)
        risk_alerts = db.query(PurchaseOrder).filter(
            PurchaseOrder.buyer_company_id == company_id,
            PurchaseOrder.delivery_date < datetime.utcnow(),
            PurchaseOrder.status.in_([PurchaseOrderStatus.PENDING, PurchaseOrderStatus.CONFIRMED])
        ).count()

        # Recent activity
        week_ago = datetime.utcnow() - timedelta(days=7)
        new_pos_this_week = db.query(PurchaseOrder).filter(
            PurchaseOrder.buyer_company_id == company_id,
            PurchaseOrder.created_at >= week_ago
        ).count()

        confirmations_pending = db.query(PurchaseOrder).filter(
            PurchaseOrder.buyer_company_id == company_id,
            PurchaseOrder.status == PurchaseOrderStatus.PENDING
        ).count()

        return {
            "supply_chain_overview": {
                "total_pos": total_pos,
                "traced_to_mill": traced_to_mill,
                "traced_to_farm": traced_to_farm,
                "transparency_percentage": round(transparency_percentage, 1)
            },
            "supplier_portfolio": {
                "active_suppliers": active_suppliers,
                "pending_onboarding": pending_onboarding,
                "risk_alerts": risk_alerts
            },
            "recent_activity": {
                "new_pos_this_week": new_pos_this_week,
                "confirmations_pending": confirmations_pending
            }
        }

    except Exception as e:
        # Return empty metrics on error to avoid breaking the dashboard
        return {
            "supply_chain_overview": {
                "total_pos": 0,
                "traced_to_mill": 0,
                "traced_to_farm": 0,
                "transparency_percentage": 0.0
            },
            "supplier_portfolio": {
                "active_suppliers": 0,
                "pending_onboarding": 0,
                "risk_alerts": 0
            },
            "recent_activity": {
                "new_pos_this_week": 0,
                "confirmations_pending": 0
            }
        }


@router.get("/metrics/processor")
async def get_processor_dashboard_metrics(
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get metrics for processor dashboard
    """
    # Verify user is from a processor company
    if current_user.company.company_type != "processor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Processor dashboard metrics only available to processor companies"
        )

    try:
        company_id = current_user.company_id

        # Incoming purchase orders
        pending_confirmation = db.query(PurchaseOrder).filter(
            PurchaseOrder.seller_company_id == company_id,
            PurchaseOrder.status == PurchaseOrderStatus.PENDING
        ).count()

        # Urgent orders (delivery date within 7 days)
        urgent_date = datetime.utcnow() + timedelta(days=7)
        urgent_orders = db.query(PurchaseOrder).filter(
            PurchaseOrder.seller_company_id == company_id,
            PurchaseOrder.status.in_([PurchaseOrderStatus.PENDING, PurchaseOrderStatus.CONFIRMED]),
            PurchaseOrder.delivery_date <= urgent_date
        ).count()

        # Production overview (using batch data if available)
        active_batches = db.query(Batch).filter(
            Batch.company_id == company_id,
            Batch.status.in_(["in_progress", "processing"])
        ).count()

        # Simplified capacity utilization (could be enhanced with actual capacity data)
        total_capacity = 100  # This would come from company settings
        capacity_utilization = min((active_batches / max(total_capacity / 10, 1)) * 100, 100)

        # Quality score (simplified - could be enhanced with actual quality metrics)
        quality_score = 4.2  # This would come from quality control data

        # Recent activity
        today = datetime.utcnow().date()
        orders_confirmed_today = db.query(PurchaseOrder).filter(
            PurchaseOrder.seller_company_id == company_id,
            PurchaseOrder.status == PurchaseOrderStatus.CONFIRMED,
            func.date(PurchaseOrder.seller_confirmed_at) == today
        ).count()

        week_ago = datetime.utcnow() - timedelta(days=7)
        batches_completed = db.query(Batch).filter(
            Batch.company_id == company_id,
            Batch.status == "completed",
            Batch.updated_at >= week_ago
        ).count()

        return {
            "incoming_pos": {
                "pending_confirmation": pending_confirmation,
                "urgent_orders": urgent_orders
            },
            "production_overview": {
                "active_batches": active_batches,
                "capacity_utilization": round(capacity_utilization, 1),
                "quality_score": quality_score
            },
            "recent_activity": {
                "orders_confirmed_today": orders_confirmed_today,
                "batches_completed": batches_completed
            }
        }

    except Exception as e:
        # Return empty metrics on error
        return {
            "incoming_pos": {
                "pending_confirmation": 0,
                "urgent_orders": 0
            },
            "production_overview": {
                "active_batches": 0,
                "capacity_utilization": 0.0,
                "quality_score": 0.0
            },
            "recent_activity": {
                "orders_confirmed_today": 0,
                "batches_completed": 0
            }
        }


@router.get("/metrics/originator")
async def get_originator_dashboard_metrics(
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get metrics for originator dashboard
    TODO: Implement real metrics from farm/harvest systems
    """
    # Verify user is from an originator company
    if current_user.company.company_type != "originator":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Originator dashboard metrics only available to originator companies"
        )
    
    # TODO: Replace with real data
    return {
        "production_tracker": {
            "recent_harvests": 0,
            "pending_po_links": 0
        },
        "farm_management": {
            "total_farms": 0,
            "eudr_compliant": 0,
            "certifications_expiring": 0
        },
        "recent_activity": {
            "harvests_this_week": 0,
            "pos_confirmed": 0
        }
    }


@router.get("/metrics/trader")
async def get_trader_dashboard_metrics(
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get metrics for trader dashboard
    TODO: Implement real metrics from trading/risk systems
    """
    # Verify user is from a trader company
    if current_user.company.company_type != "trader":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Trader dashboard metrics only available to trader companies"
        )
    
    # TODO: Replace with real data
    return {
        "order_book": {
            "incoming_orders": 0,
            "outgoing_orders": 0,
            "unfulfilled_orders": 0
        },
        "portfolio_risk": {
            "total_exposure": 0.0,
            "margin_at_risk": 0.0,
            "risk_score": 0.0
        },
        "recent_activity": {
            "orders_fulfilled": 0,
            "new_opportunities": 0
        }
    }


@router.get("/metrics/platform-admin")
async def get_platform_admin_dashboard_metrics(
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get metrics for platform admin dashboard
    """
    # Verify user has platform admin role
    if current_user.role not in ["super_admin", "support"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Platform admin dashboard only available to platform administrators"
        )

    try:
        # Platform overview
        total_companies = db.query(Company).count()

        # Active users (users who logged in within last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        active_users = db.query(User).filter(
            User.last_login >= thirty_days_ago
        ).count()

        total_pos = db.query(PurchaseOrder).count()

        # System health (simplified metrics)
        api_response_time = 150  # This would come from monitoring system
        error_rate = 0.2  # This would come from error tracking
        uptime_percentage = 99.8  # This would come from uptime monitoring

        # Recent activity
        week_ago = datetime.utcnow() - timedelta(days=7)
        new_companies = db.query(Company).filter(
            Company.created_at >= week_ago
        ).count()

        # Support tickets (simplified - would come from support system)
        support_tickets = 5  # This would come from support ticket system

        return {
            "platform_overview": {
                "total_companies": total_companies,
                "active_users": active_users,
                "total_pos": total_pos
            },
            "system_health": {
                "api_response_time": api_response_time,
                "error_rate": error_rate,
                "uptime_percentage": uptime_percentage
            },
            "recent_activity": {
                "new_companies": new_companies,
                "support_tickets": support_tickets
            }
        }

    except Exception as e:
        # Return empty metrics on error
        return {
            "platform_overview": {
                "total_companies": 0,
                "active_users": 0,
                "total_pos": 0
            },
            "system_health": {
                "api_response_time": 0,
                "error_rate": 0.0,
                "uptime_percentage": 100.0
            },
            "recent_activity": {
                "new_companies": 0,
                "support_tickets": 0
            }
        }

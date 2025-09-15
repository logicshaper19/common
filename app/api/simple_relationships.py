"""
Simple business relationships API.

This replaces the complex business relationship management with basic
supplier-buyer checks based on purchase order history.
"""
from typing import List, Dict, Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import get_current_user, CurrentUser
from app.core.simple_relationships import (
    is_supplier_buyer_relationship,
    get_relationship_summary,
    can_access_company_data,
    get_company_suppliers,
    get_company_buyers,
    get_business_partners
)
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/simple/relationships", tags=["Simple Relationships"])


@router.get("/check/{target_company_id}")
async def check_relationship(
    target_company_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Check if current user's company has a relationship with target company.
    
    This replaces complex business relationship checking with simple
    supplier-buyer checks based on purchase order history.
    """
    try:
        # Check if companies have a relationship
        has_relationship = is_supplier_buyer_relationship(
            db, 
            current_user.company_id, 
            target_company_id
        )
        
        # Get relationship summary
        summary = get_relationship_summary(
            db, 
            current_user.company_id, 
            target_company_id
        )
        
        return {
            "has_relationship": has_relationship,
            "can_access_data": can_access_company_data(
                db, 
                current_user.company_id, 
                target_company_id
            ),
            "relationship_summary": summary
        }
        
    except Exception as e:
        logger.error(f"Failed to check relationship: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check relationship"
        )


@router.get("/suppliers")
async def get_suppliers(
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """
    Get list of suppliers for current user's company.
    
    This replaces complex business relationship queries with simple
    purchase order-based supplier identification.
    """
    try:
        suppliers = get_company_suppliers(db, current_user.company_id)
        return suppliers
        
    except Exception as e:
        logger.error(f"Failed to get suppliers: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get suppliers"
        )


@router.get("/buyers")
async def get_buyers(
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """
    Get list of buyers for current user's company.
    
    This replaces complex business relationship queries with simple
    purchase order-based buyer identification.
    """
    try:
        buyers = get_company_buyers(db, current_user.company_id)
        return buyers
        
    except Exception as e:
        logger.error(f"Failed to get buyers: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get buyers"
        )


@router.get("/partners")
async def get_business_partners(
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> List[UUID]:
    """
    Get all business partners (suppliers + buyers) for current user's company.
    
    This replaces complex business relationship management with simple
    purchase order-based partner identification.
    """
    try:
        partners = get_business_partners(db, current_user.company_id)
        return partners
        
    except Exception as e:
        logger.error(f"Failed to get business partners: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get business partners"
        )


@router.get("/access/{target_company_id}")
async def check_data_access(
    target_company_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Check if current user's company can access target company's data.
    
    This replaces complex permission checking with simple relationship-based access.
    """
    try:
        can_access = can_access_company_data(
            db, 
            current_user.company_id, 
            target_company_id
        )
        
        return {
            "can_access": can_access,
            "requesting_company_id": current_user.company_id,
            "target_company_id": target_company_id,
            "reason": "Same company" if current_user.company_id == target_company_id else "Business relationship"
        }
        
    except Exception as e:
        logger.error(f"Failed to check data access: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check data access"
        )


@router.get("/summary/{target_company_id}")
async def get_relationship_summary_endpoint(
    target_company_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get detailed relationship summary between companies.
    
    This replaces complex business relationship analysis with simple
    purchase order-based relationship summary.
    """
    try:
        summary = get_relationship_summary(
            db, 
            current_user.company_id, 
            target_company_id
        )
        
        return {
            "requesting_company_id": current_user.company_id,
            "target_company_id": target_company_id,
            "summary": summary
        }
        
    except Exception as e:
        logger.error(f"Failed to get relationship summary: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get relationship summary"
        )

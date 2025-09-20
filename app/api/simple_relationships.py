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
from app.schemas.simple_relationships import (
    RelationshipCheckResponse,
    RelationshipSummaryResponse,
    SupplierInfo,
    BuyerInfo,
    SupplierListResponse,
    BuyerListResponse,
    PartnerListResponse,
    DataAccessCheckResponse,
    SimpleRelationshipAnalytics
)
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/simple/relationships", tags=["Simple Relationships"])


@router.get("/check/{target_company_id}", response_model=RelationshipCheckResponse)
async def check_relationship(
    target_company_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
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
        
        return RelationshipCheckResponse(
            has_relationship=has_relationship,
            relationship_type=summary.get("relationship_type") if summary else None,
            first_transaction_date=summary.get("first_transaction_date") if summary else None,
            last_transaction_date=summary.get("last_transaction_date") if summary else None,
            total_transactions=summary.get("total_transactions", 0) if summary else 0
        )
        
    except Exception as e:
        logger.error(f"Failed to check relationship: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check relationship"
        )


@router.get("/suppliers", response_model=SupplierListResponse)
async def get_suppliers(
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get list of suppliers for current user's company.
    
    This replaces complex business relationship queries with simple
    purchase order-based supplier identification.
    """
    try:
        suppliers_data = get_company_suppliers(db, current_user.company_id)
        
        # Convert to SupplierInfo objects
        suppliers = []
        for supplier_data in suppliers_data:
            suppliers.append(SupplierInfo(
                company_id=supplier_data["company_id"],
                company_name=supplier_data["company_name"],
                company_type=supplier_data["company_type"],
                email=supplier_data["email"],
                first_transaction_date=supplier_data["first_transaction_date"],
                last_transaction_date=supplier_data.get("last_transaction_date"),
                total_purchase_orders=supplier_data.get("total_purchase_orders", 0),
                total_value=supplier_data.get("total_value")
            ))
        
        return SupplierListResponse(
            suppliers=suppliers,
            total=len(suppliers),
            page=1,
            per_page=len(suppliers),
            total_pages=1
        )
        
    except Exception as e:
        logger.error(f"Failed to get suppliers: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get suppliers"
        )


@router.get("/buyers", response_model=BuyerListResponse)
async def get_buyers(
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get list of buyers for current user's company.
    
    This replaces complex business relationship queries with simple
    purchase order-based buyer identification.
    """
    try:
        buyers_data = get_company_buyers(db, current_user.company_id)
        
        # Convert to BuyerInfo objects
        buyers = []
        for buyer_data in buyers_data:
            buyers.append(BuyerInfo(
                company_id=buyer_data["company_id"],
                company_name=buyer_data["company_name"],
                company_type=buyer_data["company_type"],
                email=buyer_data["email"],
                first_transaction_date=buyer_data["first_transaction_date"],
                last_transaction_date=buyer_data.get("last_transaction_date"),
                total_purchase_orders=buyer_data.get("total_purchase_orders", 0),
                total_value=buyer_data.get("total_value")
            ))
        
        return BuyerListResponse(
            buyers=buyers,
            total=len(buyers),
            page=1,
            per_page=len(buyers),
            total_pages=1
        )
        
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


@router.get("/access/{target_company_id}", response_model=DataAccessCheckResponse)
async def check_data_access(
    target_company_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
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
        
        return DataAccessCheckResponse(
            can_access=can_access,
            access_reason="Same company" if current_user.company_id == target_company_id else "Business relationship",
            relationship_type="self" if current_user.company_id == target_company_id else "business_partner",
            access_level="full" if current_user.company_id == target_company_id else "standard"
        )
        
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

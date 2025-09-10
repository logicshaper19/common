"""
Business relationship management API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.services.business_relationship import BusinessRelationshipService
from app.schemas.business_relationship import (
    SupplierInvitationRequest,
    BusinessRelationshipCreate,
    BusinessRelationshipUpdate,
    BusinessRelationshipResponse,
    SupplierListResponse,
    RelationshipListResponse,
    OnboardingCascadeMetrics,
    RelationshipAnalytics,
    RelationshipStatus,
    RelationshipType,
    DataSharingPermissions
)
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/business-relationships", tags=["business-relationships"])


@router.post("/invite-supplier")
async def invite_supplier(
    invitation_request: SupplierInvitationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Invite a new supplier to join the platform.
    
    This endpoint enables viral onboarding by allowing companies to invite
    their suppliers to join the platform. When a supplier accepts the invitation,
    a business relationship is automatically established with appropriate
    data sharing permissions.
    
    The invitation process:
    1. Creates a pending company record for the supplier
    2. Establishes a pending business relationship
    3. Sends an invitation email to the supplier
    4. Tracks the invitation for viral cascade analytics
    """
    relationship_service = BusinessRelationshipService(db)
    
    try:
        result = await relationship_service.invite_supplier(
            invitation_request,
            current_user.company_id,
            current_user.id
        )
        
        logger.info(
            "Supplier invitation processed via API",
            supplier_email=invitation_request.supplier_email,
            inviting_user_id=str(current_user.id),
            inviting_company_id=str(current_user.company_id),
            result_status=result.get("status")
        )
        
        return result
        
    except Exception as e:
        logger.error(
            "Failed to process supplier invitation via API",
            supplier_email=invitation_request.supplier_email,
            error=str(e),
            user_id=str(current_user.id)
        )
        raise


@router.post("/", response_model=BusinessRelationshipResponse)
def create_business_relationship(
    relationship_data: BusinessRelationshipCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new business relationship.
    
    Establishes a business relationship between two companies with
    specified data sharing permissions. Only users from the buyer
    or seller company can create the relationship.
    """
    relationship_service = BusinessRelationshipService(db)
    
    # Check if user's company is involved in the relationship
    if (current_user.company_id != relationship_data.buyer_company_id and 
        current_user.company_id != relationship_data.seller_company_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only create relationships involving your company"
        )
    
    relationship = relationship_service.establish_relationship(
        relationship_data,
        current_user.id
    )
    
    # Convert to response format
    response = BusinessRelationshipResponse(
        id=relationship.id,
        buyer_company_id=relationship.buyer_company_id,
        seller_company_id=relationship.seller_company_id,
        relationship_type=RelationshipType(relationship.relationship_type),
        status=RelationshipStatus(relationship.status),
        data_sharing_permissions=relationship.data_sharing_permissions,
        invited_by_company_id=relationship.invited_by_company_id,
        established_at=relationship.established_at,
        terminated_at=relationship.terminated_at
    )
    
    logger.info(
        "Business relationship created via API",
        relationship_id=str(relationship.id),
        user_id=str(current_user.id)
    )
    
    return response


@router.get("/", response_model=RelationshipListResponse)
def list_business_relationships(
    relationship_type: Optional[RelationshipType] = Query(None, description="Filter by relationship type"),
    status: Optional[RelationshipStatus] = Query(None, description="Filter by status"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List business relationships for the current user's company.
    
    Returns all business relationships where the user's company is
    either the buyer or seller, with optional filtering by type and status.
    """
    relationship_service = BusinessRelationshipService(db)
    
    relationships, total_count = relationship_service.get_company_relationships(
        current_user.company_id,
        relationship_type,
        status,
        page,
        per_page
    )
    
    # Convert to response format with company details
    relationship_responses = []
    
    # Collect all unique company IDs to avoid N+1 queries
    company_ids = set()
    for rel in relationships:
        company_ids.add(rel.buyer_company_id)
        company_ids.add(rel.seller_company_id)
        if rel.invited_by_company_id:
            company_ids.add(rel.invited_by_company_id)
    
    # Fetch all companies in a single query
    from app.models.company import Company
    companies = {c.id: c for c in db.query(Company).filter(Company.id.in_(company_ids)).all()}
    
    # Build responses using pre-loaded company data
    for rel in relationships:
        buyer_company = companies.get(rel.buyer_company_id)
        seller_company = companies.get(rel.seller_company_id)
        invited_by_company = companies.get(rel.invited_by_company_id) if rel.invited_by_company_id else None

        response = BusinessRelationshipResponse(
            id=rel.id,
            buyer_company_id=rel.buyer_company_id,
            seller_company_id=rel.seller_company_id,
            relationship_type=RelationshipType(rel.relationship_type),
            status=RelationshipStatus(rel.status),
            data_sharing_permissions=rel.data_sharing_permissions,
            invited_by_company_id=rel.invited_by_company_id,
            established_at=rel.established_at,
            terminated_at=rel.terminated_at,
            buyer_company_name=buyer_company.name if buyer_company else None,
            seller_company_name=seller_company.name if seller_company else None,
            invited_by_company_name=invited_by_company.name if invited_by_company else None
        )
        relationship_responses.append(response)
    
    total_pages = (total_count + per_page - 1) // per_page
    
    return RelationshipListResponse(
        relationships=relationship_responses,
        total=total_count,
        page=page,
        per_page=per_page,
        total_pages=total_pages
    )


@router.get("/suppliers", response_model=SupplierListResponse)
def list_suppliers(
    status: Optional[RelationshipStatus] = Query(None, description="Filter by relationship status"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List suppliers for the current user's company.
    
    Returns detailed information about suppliers including relationship
    status, purchase order statistics, and data sharing permissions.
    """
    relationship_service = BusinessRelationshipService(db)
    
    suppliers, total_count = relationship_service.get_company_suppliers(
        current_user.company_id,
        status,
        page,
        per_page
    )
    
    # Convert to response format
    from app.schemas.business_relationship import SupplierInfo
    
    supplier_responses = []
    for supplier in suppliers:
        supplier_info = SupplierInfo(
            company_id=supplier["company_id"],
            company_name=supplier["company_name"],
            company_type=supplier["company_type"],
            email=supplier["email"],
            relationship_id=supplier["relationship_id"],
            relationship_status=RelationshipStatus(supplier["relationship_status"]),
            relationship_type=RelationshipType(supplier["relationship_type"]),
            established_at=supplier["established_at"],
            data_sharing_permissions=supplier["data_sharing_permissions"],
            total_purchase_orders=supplier["total_purchase_orders"],
            active_purchase_orders=supplier["active_purchase_orders"],
            last_transaction_date=supplier["last_transaction_date"]
        )
        supplier_responses.append(supplier_info)
    
    total_pages = (total_count + per_page - 1) // per_page
    
    return SupplierListResponse(
        suppliers=supplier_responses,
        total=total_count,
        page=page,
        per_page=per_page,
        total_pages=total_pages
    )


@router.put("/{relationship_id}", response_model=BusinessRelationshipResponse)
def update_business_relationship(
    relationship_id: UUID,
    update_data: BusinessRelationshipUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update a business relationship.
    
    Allows updating relationship status and data sharing permissions.
    Only companies involved in the relationship can make updates.
    """
    relationship_service = BusinessRelationshipService(db)
    
    relationship = relationship_service.update_relationship(
        relationship_id,
        update_data,
        current_user.id,
        current_user.company_id
    )
    
    # Convert to response format
    response = BusinessRelationshipResponse(
        id=relationship.id,
        buyer_company_id=relationship.buyer_company_id,
        seller_company_id=relationship.seller_company_id,
        relationship_type=RelationshipType(relationship.relationship_type),
        status=RelationshipStatus(relationship.status),
        data_sharing_permissions=relationship.data_sharing_permissions,
        invited_by_company_id=relationship.invited_by_company_id,
        established_at=relationship.established_at,
        terminated_at=relationship.terminated_at
    )
    
    logger.info(
        "Business relationship updated via API",
        relationship_id=str(relationship_id),
        user_id=str(current_user.id),
        new_status=relationship.status
    )
    
    return response


@router.post("/{relationship_id}/permissions")
def update_data_sharing_permissions(
    relationship_id: UUID,
    permissions: DataSharingPermissions,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update data sharing permissions for a business relationship.
    
    Allows fine-grained control over what data is shared between
    companies in the relationship.
    """
    relationship_service = BusinessRelationshipService(db)
    
    update_data = BusinessRelationshipUpdate(
        data_sharing_permissions=permissions
    )
    
    relationship = relationship_service.update_relationship(
        relationship_id,
        update_data,
        current_user.id,
        current_user.company_id
    )
    
    logger.info(
        "Data sharing permissions updated",
        relationship_id=str(relationship_id),
        user_id=str(current_user.id),
        new_permissions=permissions.model_dump()
    )
    
    return {
        "message": "Data sharing permissions updated successfully",
        "relationship_id": relationship_id,
        "permissions": relationship.data_sharing_permissions
    }

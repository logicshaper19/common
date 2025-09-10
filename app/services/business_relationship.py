"""
Business relationship management service with supplier onboarding and data sharing.
"""
from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID, uuid4
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
from fastapi import HTTPException, status

from app.models.business_relationship import BusinessRelationship
from app.models.company import Company
from app.models.user import User
from app.models.purchase_order import PurchaseOrder
from app.schemas.business_relationship import (
    BusinessRelationshipCreate,
    BusinessRelationshipUpdate,
    SupplierInvitationRequest,
    DataSharingPermissions,
    RelationshipStatus,
    RelationshipType,
    DataSharingPermission
)
from app.core.logging import get_logger
from app.services.tier_requirements import TierRequirementsService

logger = get_logger(__name__)


class BusinessRelationshipService:
    """Service for managing business relationships and supplier onboarding."""

    def __init__(self, db: Session):
        self.db = db

        # Mapping from frontend company types to database company types
        self.COMPANY_TYPE_MAPPING = {
            "originator": "plantation_grower",
            "processor": "mill_processor",
            "brand": "trader_aggregator",
            "trader": "trader_aggregator"
        }

        # Default data sharing permissions based on relationship type
        self.DEFAULT_PERMISSIONS = {
            RelationshipType.SUPPLIER: {
                "operational_data": True,
                "commercial_data": False,
                "traceability_data": True,
                "quality_data": True,
                "location_data": False
            },
            RelationshipType.CUSTOMER: {
                "operational_data": True,
                "commercial_data": False,
                "traceability_data": True,
                "quality_data": True,
                "location_data": False
            },
            RelationshipType.PARTNER: {
                "operational_data": True,
                "commercial_data": True,
                "traceability_data": True,
                "quality_data": True,
                "location_data": True
            }
        }

    def _map_company_type(self, frontend_type: str) -> str:
        """Map frontend company type to database company type."""
        return self.COMPANY_TYPE_MAPPING.get(frontend_type, frontend_type)

    async def invite_supplier(
        self,
        invitation_request: SupplierInvitationRequest,
        inviting_company_id: UUID,
        inviting_user_id: UUID
    ) -> Dict[str, Any]:
        """
        Invite a new supplier to join the platform.
        
        Args:
            invitation_request: Supplier invitation details
            inviting_company_id: ID of company sending invitation
            inviting_user_id: ID of user sending invitation
            
        Returns:
            Invitation result with company and relationship information
        """
        logger.info(
            "Starting supplier invitation process",
            supplier_email=invitation_request.supplier_email,
            inviting_company_id=str(inviting_company_id)
        )
        
        try:
            # Check if supplier company already exists
            existing_company = self.db.query(Company).filter(
                Company.email == invitation_request.supplier_email
            ).first()
            
            if existing_company:
                # Check if relationship already exists
                existing_relationship = self.db.query(BusinessRelationship).filter(
                    and_(
                        BusinessRelationship.buyer_company_id == inviting_company_id,
                        BusinessRelationship.seller_company_id == existing_company.id
                    )
                ).first()
                
                if existing_relationship:
                    if existing_relationship.status == RelationshipStatus.ACTIVE:
                        raise HTTPException(
                            status_code=status.HTTP_409_CONFLICT,
                            detail="Business relationship already exists with this supplier"
                        )
                    elif existing_relationship.status == RelationshipStatus.PENDING:
                        raise HTTPException(
                            status_code=status.HTTP_409_CONFLICT,
                            detail="Invitation already sent to this supplier"
                        )
                    else:
                        # Reactivate terminated/suspended relationship
                        return self._reactivate_relationship(
                            existing_relationship,
                            invitation_request,
                            inviting_user_id
                        )
                else:
                    # Create relationship with existing company
                    return self._create_relationship_with_existing_company(
                        existing_company,
                        invitation_request,
                        inviting_company_id,
                        inviting_user_id
                    )
            else:
                # Create pending company and send invitation
                return await self._create_pending_company_and_invite(
                    invitation_request,
                    inviting_company_id,
                    inviting_user_id
                )
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                "Failed to invite supplier",
                supplier_email=invitation_request.supplier_email,
                error=str(e)
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to invite supplier"
            )
    
    async def _create_pending_company_and_invite(
        self,
        invitation_request: SupplierInvitationRequest,
        inviting_company_id: UUID,
        inviting_user_id: UUID
    ) -> Dict[str, Any]:
        """Create pending company record and send invitation with tier validation."""

        # Get tier requirements for validation
        tier_service = TierRequirementsService(self.db)

        # Determine sector_id - for now default to palm_oil, but this should come from request
        sector_id = getattr(invitation_request, 'sector_id', 'palm_oil')

        try:
            # Get company type profile to determine tier level
            profile = tier_service.get_company_type_profile(
                invitation_request.company_type,
                sector_id
            )
            tier_level = profile.tier_level
            transparency_weight = profile.transparency_weight

        except ValueError as e:
            logger.warning(f"Could not determine tier for company type {invitation_request.company_type}: {e}")
            tier_level = 1
            transparency_weight = 0.5

        # Create pending company record with tier information
        # Map frontend company type to database company type
        db_company_type = self._map_company_type(invitation_request.company_type)

        pending_company = Company(
            id=uuid4(),
            name=invitation_request.supplier_name,
            company_type=db_company_type,
            email=invitation_request.supplier_email,
            sector_id=sector_id,
            tier_level=tier_level,
            transparency_score=int(transparency_weight * 100)  # Convert to 0-100 scale
        )
        
        self.db.add(pending_company)
        self.db.flush()  # Get the company ID
        
        # Create pending business relationship
        permissions = invitation_request.data_sharing_permissions
        if not permissions:
            permissions = DataSharingPermissions(
                **self.DEFAULT_PERMISSIONS[invitation_request.relationship_type]
            )
        
        relationship = BusinessRelationship(
            id=uuid4(),
            buyer_company_id=inviting_company_id,
            seller_company_id=pending_company.id,
            relationship_type=invitation_request.relationship_type.value,
            status=RelationshipStatus.PENDING.value,
            data_sharing_permissions=permissions.model_dump(),
            invited_by_company_id=inviting_company_id
        )
        
        self.db.add(relationship)
        self.db.commit()
        
        # Send invitation email
        await self._send_invitation_email(invitation_request, pending_company, relationship)
        
        logger.info(
            "Supplier invitation sent successfully",
            supplier_email=invitation_request.supplier_email,
            company_id=str(pending_company.id),
            relationship_id=str(relationship.id)
        )
        
        return {
            "invitation_sent": True,
            "company_id": pending_company.id,
            "relationship_id": relationship.id,
            "status": "pending",
            "message": f"Invitation sent to {invitation_request.supplier_email}"
        }
    
    def _create_relationship_with_existing_company(
        self,
        existing_company: Company,
        invitation_request: SupplierInvitationRequest,
        inviting_company_id: UUID,
        inviting_user_id: UUID
    ) -> Dict[str, Any]:
        """Create relationship with existing company."""
        
        permissions = invitation_request.data_sharing_permissions
        if not permissions:
            permissions = DataSharingPermissions(
                **self.DEFAULT_PERMISSIONS[invitation_request.relationship_type]
            )
        
        relationship = BusinessRelationship(
            id=uuid4(),
            buyer_company_id=inviting_company_id,
            seller_company_id=existing_company.id,
            relationship_type=invitation_request.relationship_type.value,
            status=RelationshipStatus.ACTIVE.value,  # Existing companies get active status
            data_sharing_permissions=permissions.model_dump(),
            invited_by_company_id=inviting_company_id
        )
        
        self.db.add(relationship)
        self.db.commit()
        
        logger.info(
            "Business relationship established with existing company",
            existing_company_id=str(existing_company.id),
            relationship_id=str(relationship.id)
        )
        
        return {
            "relationship_established": True,
            "company_id": existing_company.id,
            "relationship_id": relationship.id,
            "status": "active",
            "message": f"Business relationship established with {existing_company.name}"
        }

    def _reactivate_relationship(
        self,
        relationship: BusinessRelationship,
        invitation_request: SupplierInvitationRequest,
        inviting_user_id: UUID
    ) -> Dict[str, Any]:
        """Reactivate a terminated or suspended relationship."""

        # Update relationship status and permissions
        relationship.status = RelationshipStatus.ACTIVE.value
        relationship.terminated_at = None

        # Update permissions if provided
        if invitation_request.data_sharing_permissions:
            relationship.data_sharing_permissions = invitation_request.data_sharing_permissions.model_dump()

        self.db.commit()

        logger.info(
            "Business relationship reactivated",
            relationship_id=str(relationship.id),
            reactivated_by_user=str(inviting_user_id)
        )

        return {
            "relationship_reactivated": True,
            "relationship_id": relationship.id,
            "status": "active",
            "message": "Business relationship has been reactivated"
        }

    def establish_relationship(
        self,
        relationship_data: BusinessRelationshipCreate,
        establishing_user_id: UUID
    ) -> BusinessRelationship:
        """
        Establish a new business relationship.

        Args:
            relationship_data: Relationship creation data
            establishing_user_id: ID of user establishing relationship

        Returns:
            Created business relationship
        """
        logger.info(
            "Establishing business relationship",
            buyer_company_id=str(relationship_data.buyer_company_id),
            seller_company_id=str(relationship_data.seller_company_id)
        )

        try:
            # Check if relationship already exists
            existing_relationship = self.db.query(BusinessRelationship).filter(
                and_(
                    BusinessRelationship.buyer_company_id == relationship_data.buyer_company_id,
                    BusinessRelationship.seller_company_id == relationship_data.seller_company_id
                )
            ).first()

            if existing_relationship:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Business relationship already exists between these companies"
                )

            # Validate companies exist
            buyer_company = self.db.query(Company).filter(
                Company.id == relationship_data.buyer_company_id
            ).first()
            seller_company = self.db.query(Company).filter(
                Company.id == relationship_data.seller_company_id
            ).first()

            if not buyer_company or not seller_company:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="One or both companies not found"
                )

            # Set default permissions if not provided
            permissions = relationship_data.data_sharing_permissions
            if not permissions:
                permissions = DataSharingPermissions(
                    **self.DEFAULT_PERMISSIONS[relationship_data.relationship_type]
                )

            # Create relationship
            relationship = BusinessRelationship(
                id=uuid4(),
                buyer_company_id=relationship_data.buyer_company_id,
                seller_company_id=relationship_data.seller_company_id,
                relationship_type=relationship_data.relationship_type.value,
                status=RelationshipStatus.ACTIVE.value,
                data_sharing_permissions=permissions.model_dump(),
                invited_by_company_id=relationship_data.invited_by_company_id
            )

            self.db.add(relationship)
            self.db.commit()
            self.db.refresh(relationship)

            logger.info(
                "Business relationship established successfully",
                relationship_id=str(relationship.id),
                buyer_company=buyer_company.name,
                seller_company=seller_company.name
            )

            return relationship

        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(
                "Failed to establish business relationship",
                error=str(e)
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to establish business relationship"
            )

    def update_relationship(
        self,
        relationship_id: UUID,
        update_data: BusinessRelationshipUpdate,
        updating_user_id: UUID,
        updating_company_id: UUID
    ) -> BusinessRelationship:
        """
        Update an existing business relationship.

        Args:
            relationship_id: Relationship UUID
            update_data: Update data
            updating_user_id: ID of user making update
            updating_company_id: ID of company making update

        Returns:
            Updated business relationship
        """
        logger.info(
            "Updating business relationship",
            relationship_id=str(relationship_id),
            updating_company_id=str(updating_company_id)
        )

        try:
            # Get relationship
            relationship = self.db.query(BusinessRelationship).filter(
                BusinessRelationship.id == relationship_id
            ).first()

            if not relationship:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Business relationship not found"
                )

            # Check permissions - only buyer or seller can update
            if (updating_company_id != relationship.buyer_company_id and
                updating_company_id != relationship.seller_company_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You can only update relationships involving your company"
                )

            # Update fields
            if update_data.status is not None:
                if update_data.status == RelationshipStatus.TERMINATED:
                    relationship.terminated_at = datetime.utcnow()
                elif relationship.status == RelationshipStatus.TERMINATED.value:
                    relationship.terminated_at = None

                relationship.status = update_data.status.value

            if update_data.data_sharing_permissions is not None:
                relationship.data_sharing_permissions = update_data.data_sharing_permissions.model_dump()

            self.db.commit()
            self.db.refresh(relationship)

            logger.info(
                "Business relationship updated successfully",
                relationship_id=str(relationship.id),
                new_status=relationship.status
            )

            return relationship

        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(
                "Failed to update business relationship",
                relationship_id=str(relationship_id),
                error=str(e)
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update business relationship"
            )

    def get_company_relationships(
        self,
        company_id: UUID,
        relationship_type: Optional[RelationshipType] = None,
        status: Optional[RelationshipStatus] = None,
        page: int = 1,
        per_page: int = 50
    ) -> Tuple[List[BusinessRelationship], int]:
        """
        Get business relationships for a company with optimized queries.

        Args:
            company_id: Company UUID
            relationship_type: Optional filter by relationship type
            status: Optional filter by status
            page: Page number
            per_page: Items per page

        Returns:
            Tuple of (relationships, total_count)
        """
        from sqlalchemy.orm import joinedload
        
        query = self.db.query(BusinessRelationship).options(
            joinedload(BusinessRelationship.buyer_company),
            joinedload(BusinessRelationship.seller_company),
            joinedload(BusinessRelationship.invited_by_company)
        ).filter(
            or_(
                BusinessRelationship.buyer_company_id == company_id,
                BusinessRelationship.seller_company_id == company_id
            )
        )

        if relationship_type:
            query = query.filter(BusinessRelationship.relationship_type == relationship_type.value)

        if status:
            query = query.filter(BusinessRelationship.status == status.value)

        # Get total count
        total_count = query.count()

        # Apply pagination
        offset = (page - 1) * per_page
        relationships = query.order_by(desc(BusinessRelationship.established_at)).offset(offset).limit(per_page).all()

        return relationships, total_count

    def get_company_suppliers(
        self,
        company_id: UUID,
        status: Optional[RelationshipStatus] = None,
        page: int = 1,
        per_page: int = 50
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Get suppliers for a company with detailed information.

        Args:
            company_id: Company UUID
            status: Optional filter by relationship status
            page: Page number
            per_page: Items per page

        Returns:
            Tuple of (supplier_info_list, total_count)
        """
        # Query relationships where company is the buyer
        query = self.db.query(BusinessRelationship, Company).join(
            Company, BusinessRelationship.seller_company_id == Company.id
        ).filter(
            BusinessRelationship.buyer_company_id == company_id
        )

        if status:
            query = query.filter(BusinessRelationship.status == status.value)

        # Get total count
        total_count = query.count()

        # Apply pagination
        offset = (page - 1) * per_page
        results = query.order_by(desc(BusinessRelationship.established_at)).offset(offset).limit(per_page).all()

        # Build supplier information
        suppliers = []
        for relationship, company in results:
            # Get PO statistics
            po_stats = self._get_supplier_po_statistics(company_id, company.id)

            supplier_info = {
                "company_id": company.id,
                "company_name": company.name,
                "company_type": company.company_type,
                "email": company.email,
                "relationship_id": relationship.id,
                "relationship_status": relationship.status,
                "relationship_type": relationship.relationship_type,
                "established_at": relationship.established_at,
                "data_sharing_permissions": relationship.data_sharing_permissions,
                "total_purchase_orders": po_stats["total"],
                "active_purchase_orders": po_stats["active"],
                "last_transaction_date": po_stats["last_transaction"]
            }
            suppliers.append(supplier_info)

        return suppliers, total_count

    def _get_supplier_po_statistics(self, buyer_company_id: UUID, seller_company_id: UUID) -> Dict[str, Any]:
        """Get purchase order statistics for a supplier relationship."""

        # Total POs
        total_pos = self.db.query(PurchaseOrder).filter(
            and_(
                PurchaseOrder.buyer_company_id == buyer_company_id,
                PurchaseOrder.seller_company_id == seller_company_id
            )
        ).count()

        # Active POs
        active_pos = self.db.query(PurchaseOrder).filter(
            and_(
                PurchaseOrder.buyer_company_id == buyer_company_id,
                PurchaseOrder.seller_company_id == seller_company_id,
                PurchaseOrder.status.in_(["pending", "confirmed", "in_transit"])
            )
        ).count()

        # Last transaction date
        last_po = self.db.query(PurchaseOrder).filter(
            and_(
                PurchaseOrder.buyer_company_id == buyer_company_id,
                PurchaseOrder.seller_company_id == seller_company_id
            )
        ).order_by(desc(PurchaseOrder.created_at)).first()

        last_transaction = last_po.created_at if last_po else None

        return {
            "total": total_pos,
            "active": active_pos,
            "last_transaction": last_transaction
        }

    def can_access_po_data(
        self,
        requesting_company_id: UUID,
        po: PurchaseOrder,
        data_type: DataSharingPermission
    ) -> bool:
        """
        Check if company can access specific PO data based on relationships.

        Args:
            requesting_company_id: Company requesting access
            po: Purchase order
            data_type: Type of data being requested

        Returns:
            True if access is allowed
        """
        # Direct party access
        if (po.buyer_company_id == requesting_company_id or
            po.seller_company_id == requesting_company_id):
            return True

        # Check relationship permissions
        relationship = self.db.query(BusinessRelationship).filter(
            or_(
                and_(
                    BusinessRelationship.buyer_company_id == requesting_company_id,
                    BusinessRelationship.seller_company_id == po.seller_company_id
                ),
                and_(
                    BusinessRelationship.buyer_company_id == po.buyer_company_id,
                    BusinessRelationship.seller_company_id == requesting_company_id
                )
            )
        ).filter(
            BusinessRelationship.status == RelationshipStatus.ACTIVE.value
        ).first()

        if not relationship:
            return False

        # Check specific permission
        permissions = relationship.data_sharing_permissions or {}
        return permissions.get(data_type.value, False)

    async def _send_invitation_email(
        self,
        invitation_request,
        pending_company,
        relationship
    ) -> bool:
        """
        Send invitation email to supplier using the notification system.

        Args:
            invitation_request: The supplier invitation request
            pending_company: The newly created company
            relationship: The business relationship

        Returns:
            True if email was sent successfully, False otherwise
        """
        try:
            from app.services.notifications.channels.email_channel import EmailNotificationChannel
            from app.core.config import settings

            # Initialize email channel
            email_channel = EmailNotificationChannel(
                db=self.db,
                resend_api_key=settings.resend_api_key
            )

            # Prepare email content
            subject = f"Invitation to join {invitation_request.inviting_company_name} on Common Supply Chain Platform"

            html_content = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #2563eb;">You're invited to join Common Supply Chain Platform</h2>

                    <p>Hello,</p>

                    <p><strong>{invitation_request.inviting_company_name}</strong> has invited you to join their supply chain network on the Common Supply Chain Platform.</p>

                    <div style="background-color: #f8fafc; padding: 20px; border-radius: 8px; margin: 20px 0;">
                        <h3 style="margin-top: 0; color: #1e40af;">Invitation Details:</h3>
                        <ul style="margin: 0;">
                            <li><strong>Company:</strong> {pending_company.name}</li>
                            <li><strong>Email:</strong> {invitation_request.supplier_email}</li>
                            <li><strong>Relationship Type:</strong> {invitation_request.relationship_type.title()}</li>
                            <li><strong>Invited by:</strong> {invitation_request.inviting_company_name}</li>
                        </ul>
                    </div>

                    <p>The Common Supply Chain Platform helps you:</p>
                    <ul>
                        <li>Track and verify supply chain transparency</li>
                        <li>Manage purchase orders and confirmations</li>
                        <li>Share compliance documentation securely</li>
                        <li>Build trusted business relationships</li>
                    </ul>

                    <div style="text-align: center; margin: 30px 0;">
                        <a href="https://common.supply/signup?invitation_id={relationship.id}"
                           style="background-color: #2563eb; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block;">
                            Accept Invitation & Sign Up
                        </a>
                    </div>

                    <p style="font-size: 14px; color: #6b7280;">
                        If you have any questions, please contact {invitation_request.inviting_company_name} directly or reach out to our support team.
                    </p>

                    <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 30px 0;">
                    <p style="font-size: 12px; color: #9ca3af; text-align: center;">
                        Common Supply Chain Platform<br>
                        Building transparent, sustainable supply chains
                    </p>
                </div>
            </body>
            </html>
            """

            # Send email
            result = await email_channel._send_via_resend(
                to_email=invitation_request.supplier_email,
                subject=subject,
                html_content=html_content,
                text_content=f"""
You're invited to join Common Supply Chain Platform

{invitation_request.inviting_company_name} has invited you to join their supply chain network.

Company: {pending_company.name}
Email: {invitation_request.supplier_email}
Relationship Type: {invitation_request.relationship_type.title()}
Invited by: {invitation_request.inviting_company_name}

Accept your invitation: https://common.supply/signup?invitation_id={relationship.id}

The Common Supply Chain Platform helps you track supply chain transparency, manage purchase orders, and build trusted business relationships.
                """.strip()
            )

            if result.get("success"):
                logger.info(
                    "Invitation email sent successfully",
                    supplier_email=invitation_request.supplier_email,
                    company_id=str(pending_company.id),
                    relationship_id=str(relationship.id),
                    message_id=result.get("message_id")
                )
                return True
            else:
                logger.error(
                    "Failed to send invitation email",
                    supplier_email=invitation_request.supplier_email,
                    error=result.get("error")
                )
                return False

        except Exception as e:
            logger.error(
                "Exception while sending invitation email",
                supplier_email=invitation_request.supplier_email,
                error=str(e)
            )
            return False

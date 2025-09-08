"""
Amendment repository for database operations.
"""
from typing import Optional, List, Tuple, Dict, Any
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc
from math import ceil

from app.models.amendment import Amendment
from app.schemas.amendment import AmendmentFilter
from app.core.logging import get_logger

logger = get_logger(__name__)


class AmendmentRepository:
    """Handles all database operations for amendments."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, amendment_data: Dict[str, Any]) -> Amendment:
        """
        Create a new amendment.
        
        Args:
            amendment_data: Amendment data dictionary
            
        Returns:
            Created amendment
        """
        logger.info("Creating amendment in database")
        
        amendment = Amendment(**amendment_data)
        
        self.db.add(amendment)
        self.db.commit()
        self.db.refresh(amendment)
        
        logger.info(
            "Amendment created in database",
            amendment_id=str(amendment.id),
            amendment_number=amendment.amendment_number,
            po_id=str(amendment.purchase_order_id)
        )
        
        return amendment
    
    def get_by_id(self, amendment_id: UUID) -> Optional[Amendment]:
        """
        Get amendment by ID.
        
        Args:
            amendment_id: Amendment UUID
            
        Returns:
            Amendment or None if not found
        """
        return self.db.query(Amendment).filter(Amendment.id == amendment_id).first()
    
    def get_by_amendment_number(self, amendment_number: str) -> Optional[Amendment]:
        """
        Get amendment by amendment number.
        
        Args:
            amendment_number: Amendment number string
            
        Returns:
            Amendment or None if not found
        """
        return self.db.query(Amendment).filter(
            Amendment.amendment_number == amendment_number
        ).first()
    
    def update(self, amendment: Amendment, update_data: Dict[str, Any]) -> Amendment:
        """
        Update an amendment.
        
        Args:
            amendment: Amendment to update
            update_data: Data to update
            
        Returns:
            Updated amendment
        """
        logger.info(
            "Updating amendment in database",
            amendment_id=str(amendment.id),
            amendment_number=amendment.amendment_number
        )
        
        for field, value in update_data.items():
            if hasattr(amendment, field):
                setattr(amendment, field, value)
        
        amendment.updated_at = datetime.now(timezone.utc)
        
        self.db.commit()
        self.db.refresh(amendment)
        
        logger.info(
            "Amendment updated in database",
            amendment_id=str(amendment.id),
            amendment_number=amendment.amendment_number
        )
        
        return amendment
    
    def delete(self, amendment: Amendment) -> None:
        """
        Delete an amendment.
        
        Args:
            amendment: Amendment to delete
        """
        logger.info(
            "Deleting amendment from database",
            amendment_id=str(amendment.id),
            amendment_number=amendment.amendment_number
        )
        
        self.db.delete(amendment)
        self.db.commit()
        
        logger.info(
            "Amendment deleted from database",
            amendment_id=str(amendment.id)
        )
    
    def list_by_purchase_order(
        self, 
        purchase_order_id: UUID,
        status_filter: Optional[str] = None
    ) -> List[Amendment]:
        """
        List amendments for a specific purchase order.
        
        Args:
            purchase_order_id: Purchase order UUID
            status_filter: Optional status to filter by
            
        Returns:
            List of amendments
        """
        query = self.db.query(Amendment).filter(
            Amendment.purchase_order_id == purchase_order_id
        )
        
        if status_filter:
            query = query.filter(Amendment.status == status_filter)
        
        return query.order_by(desc(Amendment.proposed_at)).all()
    
    def list_with_filters(
        self, 
        filters: AmendmentFilter,
        user_company_id: UUID
    ) -> Tuple[List[Amendment], int]:
        """
        List amendments with filters and pagination.
        
        Args:
            filters: Filter criteria
            user_company_id: Current user's company ID for access control
            
        Returns:
            Tuple of (amendments list, total count)
        """
        # Base query with access control
        query = self.db.query(Amendment).filter(
            or_(
                Amendment.proposed_by_company_id == user_company_id,
                Amendment.requires_approval_from_company_id == user_company_id
            )
        )
        
        # Apply filters
        if filters.purchase_order_id:
            query = query.filter(Amendment.purchase_order_id == filters.purchase_order_id)
        
        if filters.amendment_type:
            query = query.filter(Amendment.amendment_type == filters.amendment_type.value)
        
        if filters.status:
            query = query.filter(Amendment.status == filters.status.value)
        
        if filters.priority:
            query = query.filter(Amendment.priority == filters.priority.value)
        
        if filters.proposed_by_company_id:
            query = query.filter(Amendment.proposed_by_company_id == filters.proposed_by_company_id)
        
        if filters.requires_approval_from_company_id:
            query = query.filter(
                Amendment.requires_approval_from_company_id == filters.requires_approval_from_company_id
            )
        
        # Date filters
        if filters.proposed_after:
            query = query.filter(Amendment.proposed_at >= filters.proposed_after)
        
        if filters.proposed_before:
            query = query.filter(Amendment.proposed_at <= filters.proposed_before)
        
        if filters.expires_after:
            query = query.filter(Amendment.expires_at >= filters.expires_after)
        
        if filters.expires_before:
            query = query.filter(Amendment.expires_at <= filters.expires_before)
        
        # Get total count before pagination
        total_count = query.count()
        
        # Apply pagination
        offset = (filters.page - 1) * filters.per_page
        amendments = query.order_by(desc(Amendment.proposed_at)).offset(offset).limit(filters.per_page).all()
        
        logger.info(
            "Listed amendments with filters",
            user_company_id=str(user_company_id),
            total_count=total_count,
            returned_count=len(amendments),
            page=filters.page,
            per_page=filters.per_page
        )
        
        return amendments, total_count
    
    def get_pending_amendments_for_company(self, company_id: UUID) -> List[Amendment]:
        """
        Get all pending amendments that require approval from a company.
        
        Args:
            company_id: Company UUID
            
        Returns:
            List of pending amendments
        """
        return self.db.query(Amendment).filter(
            and_(
                Amendment.requires_approval_from_company_id == company_id,
                Amendment.status == 'pending',
                or_(
                    Amendment.expires_at.is_(None),
                    Amendment.expires_at > datetime.now(timezone.utc)
                )
            )
        ).order_by(asc(Amendment.expires_at), desc(Amendment.priority)).all()
    
    def get_expired_amendments(self) -> List[Amendment]:
        """
        Get all amendments that have expired but are still pending.
        
        Returns:
            List of expired amendments
        """
        now = datetime.now(timezone.utc)
        return self.db.query(Amendment).filter(
            and_(
                Amendment.status == 'pending',
                Amendment.expires_at.isnot(None),
                Amendment.expires_at <= now
            )
        ).all()
    
    def count_amendments_by_purchase_order(self, purchase_order_id: UUID) -> int:
        """
        Count total amendments for a purchase order.
        
        Args:
            purchase_order_id: Purchase order UUID
            
        Returns:
            Total amendment count
        """
        return self.db.query(Amendment).filter(
            Amendment.purchase_order_id == purchase_order_id
        ).count()
    
    def has_pending_amendments(self, purchase_order_id: UUID) -> bool:
        """
        Check if a purchase order has pending amendments.
        
        Args:
            purchase_order_id: Purchase order UUID
            
        Returns:
            True if there are pending amendments
        """
        return self.db.query(Amendment).filter(
            and_(
                Amendment.purchase_order_id == purchase_order_id,
                Amendment.status == 'pending'
            )
        ).count() > 0
    
    def get_amendments_requiring_erp_sync(self) -> List[Amendment]:
        """
        Get amendments that require ERP synchronization.
        
        Returns:
            List of amendments requiring ERP sync
        """
        return self.db.query(Amendment).filter(
            and_(
                Amendment.requires_erp_sync == True,
                Amendment.status == 'approved',
                or_(
                    Amendment.erp_sync_status.is_(None),
                    Amendment.erp_sync_status == 'failed'
                )
            )
        ).all()

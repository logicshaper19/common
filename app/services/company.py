"""
Company service for managing company operations.
"""
from typing import List, Optional, Tuple
from uuid import UUID
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from app.models.company import Company
from app.models.purchase_order import PurchaseOrder
from app.models.audit_event import AuditEvent
from app.core.logging import get_logger

logger = get_logger(__name__)


class CompanyService:
    """Service for company operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_company_by_id(self, company_id: UUID) -> Optional[Company]:
        """
        Get company by ID.
        
        Args:
            company_id: UUID of the company
            
        Returns:
            Company object or None if not found
        """
        try:
            return self.db.query(Company).filter(Company.id == company_id).first()
        except Exception as e:
            logger.error(f"Error retrieving company {company_id}: {str(e)}")
            return None
    
    def list_companies(
        self,
        page: int = 1,
        per_page: int = 20,
        search: Optional[str] = None,
        company_type: Optional[str] = None
    ) -> Tuple[List[Company], int]:
        """
        List companies with pagination and filtering.
        
        Args:
            page: Page number
            per_page: Items per page
            search: Search term for name or email
            company_type: Filter by company type
            
        Returns:
            Tuple of (companies list, total count)
        """
        try:
            query = self.db.query(Company)
            
            # Apply filters
            if search:
                search_term = f"%{search}%"
                query = query.filter(
                    or_(
                        Company.name.ilike(search_term),
                        Company.email.ilike(search_term)
                    )
                )
            
            if company_type:
                query = query.filter(Company.company_type == company_type)
            
            # Get total count
            total = query.count()
            
            # Apply pagination
            offset = (page - 1) * per_page
            companies = query.offset(offset).limit(per_page).all()
            
            return companies, total
            
        except Exception as e:
            logger.error(f"Error listing companies: {str(e)}")
            return [], 0
    
    def get_recent_improvements(self, company_id: UUID, days: int = 30) -> List[dict]:
        """
        Get recent improvements for a company.
        
        Args:
            company_id: UUID of the company
            days: Number of days to look back
            
        Returns:
            List of improvement records
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            improvements = []
            
            # Check for new purchase orders
            new_pos = self.db.query(PurchaseOrder).filter(
                and_(
                    or_(
                        PurchaseOrder.buyer_company_id == company_id,
                        PurchaseOrder.seller_company_id == company_id
                    ),
                    PurchaseOrder.created_at >= cutoff_date
                )
            ).count()
            
            if new_pos > 0:
                improvements.append({
                    "type": "purchase_orders",
                    "description": f"Created {new_pos} new purchase orders",
                    "count": new_pos,
                    "category": "supply_chain"
                })
            
            # Check for confirmed purchase orders
            confirmed_pos = self.db.query(PurchaseOrder).filter(
                and_(
                    or_(
                        PurchaseOrder.buyer_company_id == company_id,
                        PurchaseOrder.seller_company_id == company_id
                    ),
                    PurchaseOrder.confirmed_at >= cutoff_date,
                    PurchaseOrder.confirmed_at.isnot(None)
                )
            ).count()
            
            if confirmed_pos > 0:
                improvements.append({
                    "type": "confirmations",
                    "description": f"Confirmed {confirmed_pos} purchase orders",
                    "count": confirmed_pos,
                    "category": "transparency"
                })
            
            # Check for audit events (compliance activities)
            audit_events = self.db.query(AuditEvent).filter(
                and_(
                    AuditEvent.company_id == company_id,
                    AuditEvent.created_at >= cutoff_date
                )
            ).count()
            
            if audit_events > 0:
                improvements.append({
                    "type": "compliance_activities",
                    "description": f"Completed {audit_events} compliance activities",
                    "count": audit_events,
                    "category": "compliance"
                })
            
            # Calculate transparency score improvement (mock calculation)
            company = self.get_company_by_id(company_id)
            if company and company.transparency_score:
                # This is a simplified calculation - in reality you'd track historical scores
                score_improvement = min(5, len(improvements) * 2)  # Mock improvement
                if score_improvement > 0:
                    improvements.append({
                        "type": "transparency_score",
                        "description": f"Transparency score improved by {score_improvement} points",
                        "count": score_improvement,
                        "category": "transparency"
                    })
            
            return improvements
            
        except Exception as e:
            logger.error(f"Error retrieving recent improvements for company {company_id}: {str(e)}")
            return []
    
    def update_company(self, company_id: UUID, **kwargs) -> Optional[Company]:
        """
        Update company information.
        
        Args:
            company_id: UUID of the company
            **kwargs: Fields to update
            
        Returns:
            Updated company object or None if not found
        """
        try:
            company = self.get_company_by_id(company_id)
            if not company:
                return None
            
            for key, value in kwargs.items():
                if hasattr(company, key):
                    setattr(company, key, value)
            
            company.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(company)
            
            return company
            
        except Exception as e:
            logger.error(f"Error updating company {company_id}: {str(e)}")
            self.db.rollback()
            return None
    
    def get_company_stats(self, company_id: UUID) -> dict:
        """
        Get company statistics.
        
        Args:
            company_id: UUID of the company
            
        Returns:
            Dictionary with company statistics
        """
        try:
            # Count purchase orders
            po_count = self.db.query(PurchaseOrder).filter(
                or_(
                    PurchaseOrder.buyer_company_id == company_id,
                    PurchaseOrder.seller_company_id == company_id
                )
            ).count()
            
            # Count confirmed purchase orders
            confirmed_po_count = self.db.query(PurchaseOrder).filter(
                and_(
                    or_(
                        PurchaseOrder.buyer_company_id == company_id,
                        PurchaseOrder.seller_company_id == company_id
                    ),
                    PurchaseOrder.confirmed_at.isnot(None)
                )
            ).count()
            
            # Calculate confirmation rate
            confirmation_rate = (confirmed_po_count / po_count * 100) if po_count > 0 else 0
            
            return {
                "total_purchase_orders": po_count,
                "confirmed_purchase_orders": confirmed_po_count,
                "confirmation_rate": round(confirmation_rate, 2),
                "transparency_score": None  # Would be calculated by transparency engine
            }
            
        except Exception as e:
            logger.error(f"Error retrieving company stats for {company_id}: {str(e)}")
            return {
                "total_purchase_orders": 0,
                "confirmed_purchase_orders": 0,
                "confirmation_rate": 0,
                "transparency_score": None
            }

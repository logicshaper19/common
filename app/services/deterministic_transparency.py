"""
Deterministic Transparency Service

Replaces complex scoring algorithms with fast, auditable PostgreSQL-powered 
transparency metrics based on explicit user-created links.

Core Philosophy: 
- Binary traced/not-traced states instead of opaque scores
- Every calculation is auditable through explicit data relationships
- Sub-second responses using materialized views
- Transparency percentage = (traced_volume / total_volume) * 100
"""

from typing import Dict, List, Optional, Any
from uuid import UUID
from decimal import Decimal
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text, func
from pydantic import BaseModel

from app.core.logging import get_logger
from app.models.purchase_order import PurchaseOrder
from app.models.company import Company

logger = get_logger(__name__)


class TransparencyMetrics(BaseModel):
    """Deterministic transparency metrics for a company."""
    company_id: UUID
    total_volume: Decimal
    traced_to_mill_volume: Decimal
    traced_to_plantation_volume: Decimal
    transparency_to_mill_percentage: float
    transparency_to_plantation_percentage: float
    total_purchase_orders: int
    traced_purchase_orders: int
    calculation_timestamp: datetime
    
    class Config:
        json_encoders = {
            Decimal: lambda v: float(v),
            UUID: lambda v: str(v)
        }


class TransparencyGap(BaseModel):
    """Represents a transparency gap requiring attention."""
    po_id: UUID
    po_number: str
    seller_company_name: str
    product_name: str
    quantity: Decimal
    unit: str
    gap_type: str  # 'not_traced_to_mill', 'not_traced_to_plantation'
    trace_depth: int
    last_known_company_type: str
    
    class Config:
        json_encoders = {
            Decimal: lambda v: float(v),
            UUID: lambda v: str(v)
        }


class SupplyChainTrace(BaseModel):
    """Complete supply chain trace for a purchase order."""
    po_id: UUID
    po_number: str
    trace_path: str
    trace_depth: int
    origin_company_id: UUID
    origin_company_type: str
    is_traced_to_mill: bool
    is_traced_to_plantation: bool
    path_companies: List[UUID]
    
    class Config:
        json_encoders = {
            UUID: lambda v: str(v)
        }


class DeterministicTransparencyService:
    """
    Service for calculating deterministic transparency metrics.
    
    Uses PostgreSQL materialized views for sub-second responses and 
    complete audit trails.
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_company_transparency_metrics(
        self, 
        company_id: UUID,
        refresh_data: bool = False
    ) -> TransparencyMetrics:
        """
        Get deterministic transparency metrics for a company.
        
        Args:
            company_id: Company UUID
            refresh_data: Whether to refresh materialized view first
            
        Returns:
            Complete transparency metrics with auditable calculations
        """
        if refresh_data:
            self._refresh_materialized_view()
        
        # Query materialized view for instant results
        query = text("""
            WITH company_transparency AS (
                SELECT 
                    po.id as po_id,
                    po.quantity,
                    po.unit,
                    COALESCE(sct.is_traced_to_mill, FALSE) as is_traced_to_mill,
                    COALESCE(sct.is_traced_to_plantation, FALSE) as is_traced_to_plantation
                FROM purchase_orders po
                LEFT JOIN supply_chain_traceability sct ON po.id = sct.po_id
                WHERE po.buyer_company_id = :company_id
                AND po.status = 'CONFIRMED'
            )
            SELECT 
                COUNT(*) as total_pos,
                COUNT(CASE WHEN is_traced_to_mill OR is_traced_to_plantation THEN 1 END) as traced_pos,
                COALESCE(SUM(quantity), 0) as total_volume,
                COALESCE(SUM(CASE WHEN is_traced_to_mill THEN quantity ELSE 0 END), 0) as mill_volume,
                COALESCE(SUM(CASE WHEN is_traced_to_plantation THEN quantity ELSE 0 END), 0) as plantation_volume
            FROM company_transparency
        """)
        
        result = self.db.execute(query, {"company_id": str(company_id)}).fetchone()
        
        if not result or result.total_volume == 0:
            return TransparencyMetrics(
                company_id=company_id,
                total_volume=Decimal('0'),
                traced_to_mill_volume=Decimal('0'),
                traced_to_plantation_volume=Decimal('0'),
                transparency_to_mill_percentage=0.0,
                transparency_to_plantation_percentage=0.0,
                total_purchase_orders=0,
                traced_purchase_orders=0,
                calculation_timestamp=datetime.utcnow()
            )
        
        # Calculate deterministic percentages
        mill_percentage = float(result.mill_volume / result.total_volume * 100) if result.total_volume > 0 else 0.0
        plantation_percentage = float(result.plantation_volume / result.total_volume * 100) if result.total_volume > 0 else 0.0
        
        return TransparencyMetrics(
            company_id=company_id,
            total_volume=result.total_volume,
            traced_to_mill_volume=result.mill_volume,
            traced_to_plantation_volume=result.plantation_volume,
            transparency_to_mill_percentage=mill_percentage,
            transparency_to_plantation_percentage=plantation_percentage,
            total_purchase_orders=result.total_pos,
            traced_purchase_orders=result.traced_pos,
            calculation_timestamp=datetime.utcnow()
        )
    
    def get_transparency_gaps(
        self, 
        company_id: UUID,
        gap_type: Optional[str] = None,
        limit: int = 50
    ) -> List[TransparencyGap]:
        """
        Get list of transparency gaps requiring attention.
        
        Args:
            company_id: Company UUID
            gap_type: Filter by gap type ('mill', 'plantation', or None for all)
            limit: Maximum number of gaps to return
            
        Returns:
            List of transparency gaps with actionable information
        """
        # Build gap filter condition
        gap_filter = ""
        if gap_type == "mill":
            gap_filter = "AND (sct.is_traced_to_mill = FALSE OR sct.is_traced_to_mill IS NULL)"
        elif gap_type == "plantation":
            gap_filter = "AND (sct.is_traced_to_plantation = FALSE OR sct.is_traced_to_plantation IS NULL)"
        else:
            gap_filter = "AND ((sct.is_traced_to_mill = FALSE OR sct.is_traced_to_mill IS NULL) OR (sct.is_traced_to_plantation = FALSE OR sct.is_traced_to_plantation IS NULL))"
        
        query = text(f"""
            SELECT 
                po.id as po_id,
                po.po_number,
                seller_company.name as seller_company_name,
                p.name as product_name,
                po.quantity,
                po.unit,
                CASE 
                    WHEN sct.is_traced_to_mill = FALSE OR sct.is_traced_to_mill IS NULL THEN 'not_traced_to_mill'
                    WHEN sct.is_traced_to_plantation = FALSE OR sct.is_traced_to_plantation IS NULL THEN 'not_traced_to_plantation'
                    ELSE 'unknown'
                END as gap_type,
                COALESCE(sct.trace_depth, 0) as trace_depth,
                COALESCE(sct.origin_company_type, 'unknown') as last_known_company_type
            FROM purchase_orders po
            JOIN companies seller_company ON seller_company.id = po.seller_company_id
            JOIN products p ON p.id = po.product_id
            LEFT JOIN supply_chain_traceability sct ON po.id = sct.po_id
            WHERE po.buyer_company_id = :company_id
            AND po.status = 'CONFIRMED'
            {gap_filter}
            ORDER BY po.quantity DESC, po.created_at DESC
            LIMIT :limit
        """)
        
        results = self.db.execute(query, {
            "company_id": str(company_id),
            "limit": limit
        }).fetchall()
        
        return [
            TransparencyGap(
                po_id=row.po_id,
                po_number=row.po_number,
                seller_company_name=row.seller_company_name,
                product_name=row.product_name,
                quantity=row.quantity,
                unit=row.unit,
                gap_type=row.gap_type,
                trace_depth=row.trace_depth,
                last_known_company_type=row.last_known_company_type
            )
            for row in results
        ]
    
    def get_supply_chain_trace(self, po_id: UUID) -> Optional[SupplyChainTrace]:
        """
        Get complete supply chain trace for a purchase order.
        
        Args:
            po_id: Purchase order UUID
            
        Returns:
            Complete trace path with deterministic transparency status
        """
        query = text("""
            SELECT 
                sct.po_id,
                sct.po_number,
                sct.trace_path,
                sct.trace_depth,
                sct.origin_company_id,
                sct.origin_company_type,
                sct.is_traced_to_mill,
                sct.is_traced_to_plantation,
                sct.path_company_ids
            FROM supply_chain_traceability sct
            WHERE sct.po_id = :po_id
            ORDER BY sct.trace_depth DESC
            LIMIT 1
        """)
        
        result = self.db.execute(query, {"po_id": str(po_id)}).fetchone()
        
        if not result:
            return None
        
        return SupplyChainTrace(
            po_id=result.po_id,
            po_number=result.po_number,
            trace_path=result.trace_path,
            trace_depth=result.trace_depth,
            origin_company_id=result.origin_company_id,
            origin_company_type=result.origin_company_type,
            is_traced_to_mill=result.is_traced_to_mill,
            is_traced_to_plantation=result.is_traced_to_plantation,
            path_companies=result.path_company_ids or []
        )
    
    def _refresh_materialized_view(self) -> None:
        """Refresh the materialized view for real-time data."""
        try:
            self.db.execute(text("SELECT refresh_supply_chain_traceability()"))
            self.db.commit()
            logger.info("Supply chain traceability materialized view refreshed")
        except Exception as e:
            logger.error(f"Failed to refresh materialized view: {e}")
            self.db.rollback()
            raise
    
    def get_transparency_audit_trail(self, po_id: UUID) -> Dict[str, Any]:
        """
        Get complete audit trail for transparency calculation.
        
        Returns all data used in transparency determination for full auditability.
        """
        query = text("""
            SELECT 
                sct.*,
                po.created_at as po_created_at,
                po.confirmed_at as po_confirmed_at,
                buyer.name as buyer_company_name,
                seller.name as seller_company_name
            FROM supply_chain_traceability sct
            JOIN purchase_orders po ON po.id = sct.po_id
            JOIN companies buyer ON buyer.id = sct.buyer_company_id
            JOIN companies seller ON seller.id = sct.seller_company_id
            WHERE sct.po_id = :po_id
        """)
        
        result = self.db.execute(query, {"po_id": str(po_id)}).fetchone()
        
        if not result:
            return {"error": "No transparency data found for this purchase order"}
        
        return {
            "po_id": str(result.po_id),
            "po_number": result.po_number,
            "buyer_company": result.buyer_company_name,
            "seller_company": result.seller_company_name,
            "trace_path": result.trace_path,
            "trace_depth": result.trace_depth,
            "origin_company_type": result.origin_company_type,
            "is_traced_to_mill": result.is_traced_to_mill,
            "is_traced_to_plantation": result.is_traced_to_plantation,
            "calculation_method": "deterministic_materialized_view",
            "calculation_timestamp": result.calculated_at.isoformat() if result.calculated_at else None,
            "audit_note": "Transparency determined by explicit user-created batch relationships and company types"
        }

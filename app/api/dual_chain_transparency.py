"""
Dual-Chain Transparency API
Provides complete traceability including both commercial and physical chains
"""
from typing import List, Dict, Any, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.core.logging import get_logger

router = APIRouter(prefix="/api/v1/dual-chain-transparency", tags=["dual-chain-transparency"])
logger = get_logger(__name__)


class ChainNode(BaseModel):
    """Represents a node in the traceability chain."""
    po_id: Optional[str] = None
    po_number: Optional[str] = None
    batch_id: Optional[str] = None
    batch_identifier: Optional[str] = None
    company_id: str
    company_name: str
    company_type: str
    chain_type: str  # 'COMMERCIAL' or 'PHYSICAL'
    depth: int
    path: str
    parent_po_id: Optional[str] = None
    parent_batch_id: Optional[str] = None
    is_traced_to_mill: bool
    is_traced_to_plantation: bool


class DualChainResponse(BaseModel):
    """Response for dual-chain traceability query."""
    po_id: str
    po_number: str
    commercial_chain: List[ChainNode]
    physical_chain: List[ChainNode]
    summary: Dict[str, Any]


@router.get("/po/{po_id}", response_model=DualChainResponse)
async def get_dual_chain_traceability(
    po_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get complete dual-chain traceability for a purchase order.
    
    Returns both commercial chain (PO-to-PO) and physical chain (Batch-to-Batch)
    traceability information.
    """
    try:
        po_uuid = UUID(po_id)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid PO ID format"
        )
    
    # Get the purchase order details
    po_query = text("""
        SELECT 
            po.id,
            po.po_number,
            po.buyer_company_id,
            po.seller_company_id,
            buyer.name as buyer_name,
            seller.name as seller_name
        FROM purchase_orders po
        JOIN companies buyer ON buyer.id = po.buyer_company_id
        JOIN companies seller ON seller.id = po.seller_company_id
        WHERE po.id = :po_id
    """)
    
    po_result = db.execute(po_query, {"po_id": str(po_uuid)}).fetchone()
    if not po_result:
        raise HTTPException(
            status_code=404,
            detail="Purchase order not found"
        )
    
    # Get dual-chain traceability data
    traceability_query = text("""
        SELECT 
            sct.po_id,
            sct.po_number,
            sct.batch_id,
            sct.batch_identifier,
            sct.origin_company_id,
            c.name as company_name,
            sct.origin_company_type,
            sct.chain_type,
            sct.trace_depth,
            sct.trace_path,
            sct.parent_po_id,
            sct.parent_batch_id,
            sct.is_traced_to_mill,
            sct.is_traced_to_plantation
        FROM supply_chain_traceability sct
        JOIN companies c ON c.id = sct.origin_company_id
        WHERE sct.po_id = :po_id
        ORDER BY sct.chain_type, sct.trace_depth
    """)
    
    traceability_results = db.execute(traceability_query, {"po_id": str(po_uuid)}).fetchall()
    
    # Separate commercial and physical chains
    commercial_chain = []
    physical_chain = []
    
    for row in traceability_results:
        node = ChainNode(
            po_id=str(row.po_id) if row.po_id else None,
            po_number=row.po_number,
            batch_id=str(row.batch_id) if row.batch_id else None,
            batch_identifier=row.batch_identifier,
            company_id=str(row.origin_company_id),
            company_name=row.company_name,
            company_type=row.origin_company_type,
            chain_type=row.chain_type,
            depth=row.trace_depth,
            path=row.trace_path,
            parent_po_id=str(row.parent_po_id) if row.parent_po_id else None,
            parent_batch_id=str(row.parent_batch_id) if row.parent_batch_id else None,
            is_traced_to_mill=row.is_traced_to_mill,
            is_traced_to_plantation=row.is_traced_to_plantation
        )
        
        if row.chain_type == 'COMMERCIAL':
            commercial_chain.append(node)
        else:
            physical_chain.append(node)
    
    # Calculate summary statistics
    summary = {
        "commercial_chain_length": len(commercial_chain),
        "physical_chain_length": len(physical_chain),
        "max_commercial_depth": max([node.depth for node in commercial_chain]) if commercial_chain else 0,
        "max_physical_depth": max([node.depth for node in physical_chain]) if physical_chain else 0,
        "traced_to_mill": any(node.is_traced_to_mill for node in physical_chain),
        "traced_to_plantation": any(node.is_traced_to_plantation for node in physical_chain),
        "unique_companies": len(set(node.company_id for node in commercial_chain + physical_chain))
    }
    
    return DualChainResponse(
        po_id=str(po_uuid),
        po_number=po_result.po_number,
        commercial_chain=commercial_chain,
        physical_chain=physical_chain,
        summary=summary
    )


@router.get("/company/{company_id}/summary")
async def get_company_dual_chain_summary(
    company_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get dual-chain transparency summary for a company.
    
    Shows both commercial and physical chain transparency metrics.
    """
    try:
        company_uuid = UUID(company_id)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid company ID format"
        )
    
    # Check access permissions
    if (current_user.company_id != company_uuid and
        current_user.role not in ["admin", "super_admin"]):
        raise HTTPException(
            status_code=403,
            detail="Access denied to company transparency data"
        )
    
    # Get dual-chain transparency metrics
    metrics_query = text("""
        WITH company_metrics AS (
            SELECT 
                po.id as po_id,
                po.quantity,
                sct.chain_type,
                sct.is_traced_to_mill,
                sct.is_traced_to_plantation,
                sct.trace_depth
            FROM purchase_orders po
            LEFT JOIN supply_chain_traceability sct ON po.id = sct.po_id
            WHERE po.buyer_company_id = :company_id
            AND po.status = 'CONFIRMED'
        )
        SELECT 
            COUNT(DISTINCT po_id) as total_pos,
            COALESCE(SUM(quantity), 0) as total_volume,
            COUNT(DISTINCT CASE WHEN chain_type = 'COMMERCIAL' THEN po_id END) as commercial_traced_pos,
            COUNT(DISTINCT CASE WHEN chain_type = 'PHYSICAL' THEN po_id END) as physical_traced_pos,
            COALESCE(SUM(CASE WHEN is_traced_to_mill THEN quantity ELSE 0 END), 0) as mill_volume,
            COALESCE(SUM(CASE WHEN is_traced_to_plantation THEN quantity ELSE 0 END), 0) as plantation_volume,
            AVG(CASE WHEN chain_type = 'COMMERCIAL' THEN trace_depth END) as avg_commercial_depth,
            AVG(CASE WHEN chain_type = 'PHYSICAL' THEN trace_depth END) as avg_physical_depth
        FROM company_metrics
    """)
    
    result = db.execute(metrics_query, {"company_id": str(company_uuid)}).fetchone()
    
    if not result or result.total_volume == 0:
        return {
            "company_id": str(company_uuid),
            "commercial_transparency": 0.0,
            "physical_transparency": 0.0,
            "mill_transparency": 0.0,
            "plantation_transparency": 0.0,
            "total_pos": 0,
            "total_volume": 0,
            "summary": "No confirmed purchase orders found"
        }
    
    # Calculate transparency percentages
    commercial_transparency = (result.commercial_traced_pos / result.total_pos * 100) if result.total_pos > 0 else 0
    physical_transparency = (result.physical_traced_pos / result.total_pos * 100) if result.total_pos > 0 else 0
    mill_transparency = (result.mill_volume / result.total_volume * 100) if result.total_volume > 0 else 0
    plantation_transparency = (result.plantation_volume / result.total_volume * 100) if result.total_volume > 0 else 0
    
    return {
        "company_id": str(company_uuid),
        "commercial_transparency": round(commercial_transparency, 2),
        "physical_transparency": round(physical_transparency, 2),
        "mill_transparency": round(mill_transparency, 2),
        "plantation_transparency": round(plantation_transparency, 2),
        "total_pos": result.total_pos,
        "total_volume": float(result.total_volume),
        "commercial_traced_pos": result.commercial_traced_pos,
        "physical_traced_pos": result.physical_traced_pos,
        "mill_volume": float(result.mill_volume),
        "plantation_volume": float(result.plantation_volume),
        "avg_commercial_depth": round(float(result.avg_commercial_depth or 0), 2),
        "avg_physical_depth": round(float(result.avg_physical_depth or 0), 2),
        "summary": f"Commercial: {commercial_transparency:.1f}%, Physical: {physical_transparency:.1f}%, Mill: {mill_transparency:.1f}%, Plantation: {plantation_transparency:.1f}%"
    }

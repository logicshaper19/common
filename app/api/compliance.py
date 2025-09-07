"""
Compliance API endpoints
Following the project plan: Surface compliance data in API
"""
from typing import List, Optional, Dict, Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.services.compliance.service import ComplianceService
from app.services.compliance.reporting import ComplianceReportGenerator
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/compliance", tags=["compliance"])


@router.post("/evaluate/{po_id}")
async def evaluate_po_compliance(
    po_id: UUID,
    regulation: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Evaluate compliance for a specific purchase order and regulation.
    
    Following the project plan: Manual compliance evaluation endpoint.
    """
    try:
        compliance_service = ComplianceService(db)
        
        # Run compliance evaluation
        results = await compliance_service.evaluate_po_compliance(po_id, regulation)
        
        logger.info(
            "Manual compliance evaluation completed",
            po_id=str(po_id),
            regulation=regulation,
            user_id=str(current_user.id),
            results_count=len(results)
        )
        
        return {
            "po_id": str(po_id),
            "regulation": regulation,
            "evaluation_completed": True,
            "checks_performed": len(results),
            "results": [
                {
                    "check_name": result.check_name,
                    "status": result.status,
                    "evidence": result.evidence,
                    "checked_at": result.checked_at.isoformat() if result.checked_at else None
                }
                for result in results
            ]
        }
        
    except Exception as e:
        logger.error(
            "Error during manual compliance evaluation",
            po_id=str(po_id),
            regulation=regulation,
            user_id=str(current_user.id),
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error evaluating compliance: {str(e)}"
        )


@router.get("/overview/{po_id}")
def get_compliance_overview(
    po_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get compliance overview for a purchase order.
    
    Following the project plan: Surface compliance data in API.
    """
    try:
        compliance_service = ComplianceService(db)
        
        overview = compliance_service.get_compliance_overview(po_id)
        
        logger.info(
            "Compliance overview retrieved",
            po_id=str(po_id),
            user_id=str(current_user.id),
            regulations_found=len(overview)
        )
        
        return {
            "po_id": str(po_id),
            "compliance_overview": overview,
            "retrieved_at": overview.get("checked_at") if overview else None
        }
        
    except Exception as e:
        logger.error(
            "Error retrieving compliance overview",
            po_id=str(po_id),
            user_id=str(current_user.id),
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving compliance overview: {str(e)}"
        )


@router.get("/report/{po_id}")
def generate_compliance_report(
    po_id: UUID,
    regulations: Optional[str] = None,  # Comma-separated list
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate PDF compliance report for a purchase order.
    
    Following the project plan: PDF reporting endpoint.
    """
    try:
        report_generator = ComplianceReportGenerator(db)
        
        # Parse regulations parameter
        regulation_list = None
        if regulations:
            regulation_list = [r.strip().lower() for r in regulations.split(",")]
        
        # Generate PDF report
        pdf_bytes = report_generator.generate_po_compliance_report(po_id, regulation_list)
        
        logger.info(
            "Compliance report generated",
            po_id=str(po_id),
            user_id=str(current_user.id),
            regulations=regulation_list,
            report_size=len(pdf_bytes)
        )
        
        # Return PDF as response
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=compliance_report_{po_id}.pdf"
            }
        )
        
    except Exception as e:
        logger.error(
            "Error generating compliance report",
            po_id=str(po_id),
            user_id=str(current_user.id),
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating compliance report: {str(e)}"
        )


@router.get("/dashboard")
def get_compliance_dashboard(
    regulation: Optional[str] = None,
    status_filter: Optional[str] = None,  # pass, fail, warning, pending
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get compliance dashboard data for consultants.
    
    Following the project plan: Compliance dashboard for consultants.
    """
    try:
        from app.models.po_compliance_result import POComplianceResult
        from app.models.purchase_order import PurchaseOrder
        from sqlalchemy import and_, or_
        
        # Build query
        query = db.query(POComplianceResult).join(PurchaseOrder)
        
        # Apply filters
        filters = []
        if regulation:
            filters.append(POComplianceResult.regulation == regulation.lower())
        if status_filter:
            filters.append(POComplianceResult.status == status_filter.lower())
        
        if filters:
            query = query.filter(and_(*filters))
        
        # Get total count
        total_count = query.count()
        
        # Apply pagination
        results = query.offset(offset).limit(limit).all()
        
        # Format results
        dashboard_data = []
        for result in results:
            po = result.purchase_order
            dashboard_data.append({
                "po_id": str(result.po_id),
                "po_number": po.po_number if po else "Unknown",
                "regulation": result.regulation,
                "check_name": result.check_name,
                "status": result.status,
                "checked_at": result.checked_at.isoformat() if result.checked_at else None,
                "buyer_company": po.buyer_company.name if po and po.buyer_company else "Unknown",
                "seller_company": po.seller_company.name if po and po.seller_company else "Unknown",
                "product": po.product.name if po and po.product else "Unknown"
            })
        
        logger.info(
            "Compliance dashboard data retrieved",
            user_id=str(current_user.id),
            regulation=regulation,
            status_filter=status_filter,
            total_results=total_count,
            returned_results=len(dashboard_data)
        )
        
        return {
            "total_count": total_count,
            "returned_count": len(dashboard_data),
            "offset": offset,
            "limit": limit,
            "filters": {
                "regulation": regulation,
                "status": status_filter
            },
            "results": dashboard_data
        }
        
    except Exception as e:
        logger.error(
            "Error retrieving compliance dashboard data",
            user_id=str(current_user.id),
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving dashboard data: {str(e)}"
        )


@router.get("/regulations")
def get_available_regulations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get list of available regulations for compliance checking.
    """
    try:
        from app.models.sector import Sector
        
        # Get all sectors with compliance rules
        sectors = db.query(Sector).filter(
            Sector.compliance_rules.isnot(None),
            Sector.is_active == True
        ).all()
        
        regulations = set()
        sector_regulations = {}
        
        for sector in sectors:
            if sector.compliance_rules:
                sector_regs = list(sector.compliance_rules.keys())
                regulations.update(sector_regs)
                sector_regulations[sector.id] = {
                    "name": sector.name,
                    "regulations": sector_regs
                }
        
        return {
            "available_regulations": sorted(list(regulations)),
            "by_sector": sector_regulations
        }
        
    except Exception as e:
        logger.error(
            "Error retrieving available regulations",
            user_id=str(current_user.id),
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving regulations: {str(e)}"
        )

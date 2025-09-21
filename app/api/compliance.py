"""
Compliance API endpoints for EUDR, RSPO, and other regulatory reporting.
"""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import get_current_user_sync, CurrentUser
from app.core.logging import get_logger
from app.services.compliance import (
    ComplianceService, ComplianceDataMapper, ComplianceTemplateEngine,
    PurchaseOrderNotFoundError, CompanyNotFoundError, ProductNotFoundError,
    TemplateNotFoundError, ComplianceDataError, RiskAssessmentError, MassBalanceError
)
from app.schemas.compliance import (
    ComplianceReportRequest, ComplianceReportGenerationResponse,
    EUDRReportData, RSPOReportData,
    RiskAssessmentCreate, RiskAssessmentResponse,
    MassBalanceCalculation, MassBalanceResponse,
    HSCodeResponse, ComplianceTemplateResponse
)

logger = get_logger(__name__)
router = APIRouter(prefix="/compliance", tags=["compliance"])


@router.post("/reports/generate", response_model=ComplianceReportGenerationResponse)
def generate_compliance_report(
    request: ComplianceReportRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user_sync)
):
    """Generate a compliance report for a purchase order."""
    try:
        logger.info(
            "Generating compliance report",
            po_id=str(request.po_id),
            regulation_type=request.regulation_type,
            user_id=str(current_user.id)
        )
        
        # Initialize compliance service with dependency injection
        data_mapper = ComplianceDataMapper(db)
        template_engine = ComplianceTemplateEngine(db)
        compliance_service = ComplianceService(
            db=db,
            data_mapper=data_mapper,
            template_engine=template_engine
        )
        response = compliance_service.generate_compliance_report(request)
        
        logger.info(
            "Compliance report generated successfully",
            report_id=str(response.report_id),
            po_id=str(response.po_id),
            regulation_type=response.regulation_type
        )
        
        return response
        
    except (PurchaseOrderNotFoundError, CompanyNotFoundError, ProductNotFoundError) as e:
        logger.error(f"Data not found for compliance report: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except (TemplateNotFoundError, ComplianceDataError) as e:
        logger.error(f"Compliance data error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to generate compliance report: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate compliance report")


@router.get("/reports/{report_id}/download")
def download_compliance_report(
    report_id: UUID,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user_sync)
):
    """Download a generated compliance report."""
    # This would implement file download logic
    # For now, return a placeholder response
    return {"message": f"Download report {report_id}", "status": "placeholder"}


@router.get("/eudr/{po_id}/preview", response_model=EUDRReportData)
def preview_eudr_report(
    po_id: UUID,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user_sync)
):
    """Preview EUDR report data for a purchase order."""
    try:
        data_mapper = ComplianceDataMapper(db)
        eudr_data = data_mapper.map_po_to_eudr_data(po_id)
        
        logger.info(
            "EUDR report preview generated",
            po_id=str(po_id),
            user_id=str(current_user.id)
        )
        
        return eudr_data
        
    except (PurchaseOrderNotFoundError, CompanyNotFoundError, ProductNotFoundError) as e:
        logger.error(f"Data not found for EUDR preview: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except ComplianceDataError as e:
        logger.error(f"Compliance data error for EUDR preview: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to generate EUDR preview: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate EUDR preview")


@router.get("/rspo/{po_id}/preview", response_model=RSPOReportData)
def preview_rspo_report(
    po_id: UUID,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user_sync)
):
    """Preview RSPO report data for a purchase order."""
    try:
        data_mapper = ComplianceDataMapper(db)
        rspo_data = data_mapper.map_po_to_rspo_data(po_id)
        
        logger.info(
            "RSPO report preview generated",
            po_id=str(po_id),
            user_id=str(current_user.id)
        )
        
        return rspo_data
        
    except (PurchaseOrderNotFoundError, CompanyNotFoundError, ProductNotFoundError) as e:
        logger.error(f"Data not found for RSPO preview: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except ComplianceDataError as e:
        logger.error(f"Compliance data error for RSPO preview: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to generate RSPO preview: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate RSPO preview")


@router.post("/risk-assessments", response_model=RiskAssessmentResponse)
def create_risk_assessment(
    risk_assessment: RiskAssessmentCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user_sync)
):
    """Create a new risk assessment."""
    try:
        from app.models.compliance import RiskAssessment
        
        # Create risk assessment
        db_risk_assessment = RiskAssessment(
            company_id=risk_assessment.company_id,
            batch_id=risk_assessment.batch_id,
            po_id=risk_assessment.po_id,
            risk_type=risk_assessment.risk_type,
            risk_score=risk_assessment.risk_score,
            risk_factors=risk_assessment.risk_factors,
            mitigation_measures=risk_assessment.mitigation_measures,
            assessment_date=risk_assessment.assessment_date,
            next_assessment_date=risk_assessment.next_assessment_date,
            assessed_by_user_id=current_user.id
        )
        
        db.add(db_risk_assessment)
        db.commit()
        db.refresh(db_risk_assessment)
        
        logger.info(
            "Risk assessment created",
            risk_assessment_id=str(db_risk_assessment.id),
            risk_type=risk_assessment.risk_type,
            user_id=str(current_user.id)
        )
        
        return RiskAssessmentResponse.from_orm(db_risk_assessment)
        
    except Exception as e:
        logger.error(f"Failed to create risk assessment: {e}")
        raise HTTPException(status_code=500, detail="Failed to create risk assessment")


@router.get("/risk-assessments", response_model=List[RiskAssessmentResponse])
def get_risk_assessments(
    company_id: Optional[UUID] = Query(None, description="Filter by company ID"),
    risk_type: Optional[str] = Query(None, description="Filter by risk type"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of assessments to return"),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user_sync)
):
    """Get risk assessments with optional filtering."""
    try:
        from app.models.compliance import RiskAssessment
        
        query = db.query(RiskAssessment)
        
        if company_id:
            query = query.filter(RiskAssessment.company_id == company_id)
        
        if risk_type:
            query = query.filter(RiskAssessment.risk_type == risk_type)
        
        risk_assessments = query.limit(limit).all()
        
        return [RiskAssessmentResponse.from_orm(ra) for ra in risk_assessments]
        
    except Exception as e:
        logger.error(f"Failed to get risk assessments: {e}")
        raise HTTPException(status_code=500, detail="Failed to get risk assessments")


@router.get("/hs-codes", response_model=List[HSCodeResponse])
def get_hs_codes(
    regulation: Optional[str] = Query(None, description="Filter by regulation type"),
    search: Optional[str] = Query(None, description="Search in description"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of HS codes to return"),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user_sync)
):
    """Get HS codes with optional filtering."""
    try:
        from app.models.compliance import HSCode
        
        query = db.query(HSCode)
        
        if regulation:
            query = query.filter(HSCode.regulation_applicable.contains([regulation]))
        
        if search:
            query = query.filter(HSCode.description.ilike(f"%{search}%"))
        
        hs_codes = query.limit(limit).all()
        
        return [HSCodeResponse.from_orm(hc) for hc in hs_codes]
        
    except Exception as e:
        logger.error(f"Failed to get HS codes: {e}")
        raise HTTPException(status_code=500, detail="Failed to get HS codes")


@router.get("/templates", response_model=List[ComplianceTemplateResponse])
def get_compliance_templates(
    regulation_type: Optional[str] = Query(None, description="Filter by regulation type"),
    active_only: bool = Query(True, description="Show only active templates"),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user_sync)
):
    """Get compliance templates."""
    try:
        from app.models.compliance import ComplianceTemplate
        
        query = db.query(ComplianceTemplate)
        
        if regulation_type:
            query = query.filter(ComplianceTemplate.regulation_type == regulation_type)
        
        if active_only:
            query = query.filter(ComplianceTemplate.is_active == True)
        
        templates = query.all()
        
        return [ComplianceTemplateResponse.from_orm(t) for t in templates]
        
    except Exception as e:
        logger.error(f"Failed to get compliance templates: {e}")
        raise HTTPException(status_code=500, detail="Failed to get compliance templates")


@router.get("/mass-balance/{transformation_event_id}", response_model=List[MassBalanceResponse])
def get_mass_balance_calculations(
    transformation_event_id: UUID,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user_sync)
):
    """Get mass balance calculations for a transformation event."""
    try:
        from app.models.compliance import MassBalanceCalculation
        
        calculations = db.query(MassBalanceCalculation).filter(
            MassBalanceCalculation.transformation_event_id == transformation_event_id
        ).all()
        
        return [MassBalanceResponse.from_orm(calc) for calc in calculations]
        
    except Exception as e:
        logger.error(f"Failed to get mass balance calculations: {e}")
        raise HTTPException(status_code=500, detail="Failed to get mass balance calculations")
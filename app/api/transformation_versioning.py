"""
API endpoints for transformation versioning and enhanced functionality.
"""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.models.transformation_versioning import (
    TransformationEventVersion, QualityInheritanceRule, TransformationCost,
    TransformationProcessTemplate, RealTimeMonitoringEndpoint
)
from app.services.transformation_versioning import (
    TransformationVersioningService, QualityInheritanceService,
    TransformationCostService, TransformationProcessTemplateService,
    RealTimeMonitoringService
)
from app.schemas.transformation_versioning import (
    TransformationEventVersionCreate, TransformationEventVersionUpdate,
    TransformationEventVersionResponse, QualityInheritanceRuleCreate,
    QualityInheritanceRuleUpdate, QualityInheritanceRuleResponse,
    TransformationCostCreate, TransformationCostUpdate, TransformationCostResponse,
    TransformationProcessTemplateCreate, TransformationProcessTemplateUpdate,
    TransformationProcessTemplateResponse, RealTimeMonitoringEndpointCreate,
    RealTimeMonitoringEndpointUpdate, RealTimeMonitoringEndpointResponse,
    QualityInheritanceCalculation, CostCalculationRequest, TemplateUsageRequest,
    MonitoringDataIngestion, VersionApprovalRequest, BatchQualityInheritanceRequest,
    CostSummaryResponse, TemplateMetricsResponse
)

router = APIRouter(prefix="/transformation-versioning", tags=["transformation-versioning"])


# Transformation Event Versioning Endpoints
@router.post("/versions", response_model=TransformationEventVersionResponse)
async def create_transformation_version(
    version_data: TransformationEventVersionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new version of a transformation event."""
    service = TransformationVersioningService(db)
    return service.create_version(version_data, current_user.id)


@router.get("/versions/{transformation_event_id}", response_model=List[TransformationEventVersionResponse])
async def get_transformation_versions(
    transformation_event_id: UUID,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all versions for a transformation event."""
    service = TransformationVersioningService(db)
    return service.get_versions(transformation_event_id, limit, offset)


@router.get("/versions/version/{version_id}", response_model=TransformationEventVersionResponse)
async def get_transformation_version(
    version_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific transformation event version."""
    service = TransformationVersioningService(db)
    version = service.get_version(version_id)
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")
    return version


@router.put("/versions/{version_id}", response_model=TransformationEventVersionResponse)
async def update_transformation_version(
    version_id: UUID,
    update_data: TransformationEventVersionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a transformation event version."""
    service = TransformationVersioningService(db)
    version = service.update_version(version_id, update_data, current_user.id)
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")
    return version


@router.post("/versions/{version_id}/approve", response_model=TransformationEventVersionResponse)
async def approve_transformation_version(
    version_id: UUID,
    approval_data: VersionApprovalRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Approve or reject a transformation event version."""
    service = TransformationVersioningService(db)
    version = service.approve_version(version_id, approval_data, current_user.id)
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")
    return version


# Quality Inheritance Endpoints
@router.post("/quality-rules", response_model=QualityInheritanceRuleResponse)
async def create_quality_inheritance_rule(
    rule_data: QualityInheritanceRuleCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new quality inheritance rule."""
    service = QualityInheritanceService(db)
    return service.create_rule(rule_data, current_user.id)


@router.get("/quality-rules", response_model=List[QualityInheritanceRuleResponse])
async def get_quality_inheritance_rules(
    transformation_type: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get quality inheritance rules with optional filtering."""
    service = QualityInheritanceService(db)
    return service.get_rules(transformation_type, is_active)


@router.post("/quality-inheritance/calculate")
async def calculate_quality_inheritance(
    calculation_data: QualityInheritanceCalculation,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Calculate quality inheritance for a transformation."""
    service = QualityInheritanceService(db)
    return service.calculate_quality_inheritance(calculation_data)


@router.post("/quality-inheritance/batch")
async def calculate_batch_quality_inheritance(
    batch_data: BatchQualityInheritanceRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Calculate quality inheritance for a batch transformation."""
    service = QualityInheritanceService(db)
    calculation_data = QualityInheritanceCalculation(
        transformation_type=batch_data.transformation_type,
        input_quality=batch_data.input_quality,
        transformation_parameters=batch_data.transformation_parameters
    )
    return service.calculate_quality_inheritance(calculation_data)


# Transformation Cost Endpoints
@router.post("/costs", response_model=TransformationCostResponse)
async def create_transformation_cost(
    cost_data: TransformationCostCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new transformation cost record."""
    service = TransformationCostService(db)
    return service.create_cost(cost_data, current_user.id)


@router.get("/costs/{transformation_event_id}", response_model=List[TransformationCostResponse])
async def get_transformation_costs(
    transformation_event_id: UUID,
    cost_category: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get costs for a transformation event."""
    service = TransformationCostService(db)
    return service.get_costs(transformation_event_id, cost_category)


@router.get("/costs/{transformation_event_id}/summary", response_model=CostSummaryResponse)
async def get_transformation_cost_summary(
    transformation_event_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get cost summary for a transformation event."""
    service = TransformationCostService(db)
    return service.get_cost_summary(transformation_event_id)


@router.post("/costs/calculate")
async def calculate_transformation_cost(
    cost_data: CostCalculationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Calculate and record transformation cost."""
    service = TransformationCostService(db)
    cost_create = TransformationCostCreate(
        transformation_event_id=cost_data.transformation_event_id,
        cost_category=cost_data.cost_category,
        cost_type=cost_data.cost_type,
        quantity=cost_data.quantity,
        unit=cost_data.unit,
        unit_cost=cost_data.unit_cost,
        currency=cost_data.currency,
        cost_breakdown=cost_data.cost_breakdown,
        supplier_id=cost_data.supplier_id,
        cost_center=cost_data.cost_center
    )
    return service.create_cost(cost_create, current_user.id)


# Transformation Process Template Endpoints
@router.post("/templates", response_model=TransformationProcessTemplateResponse)
async def create_transformation_template(
    template_data: TransformationProcessTemplateCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new transformation process template."""
    service = TransformationProcessTemplateService(db)
    return service.create_template(template_data, current_user.id)


@router.get("/templates", response_model=List[TransformationProcessTemplateResponse])
async def get_transformation_templates(
    transformation_type: Optional[str] = Query(None),
    company_type: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    is_standard: Optional[bool] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get transformation process templates with optional filtering."""
    service = TransformationProcessTemplateService(db)
    return service.get_templates(transformation_type, company_type, is_active, is_standard)


@router.post("/templates/use")
async def use_transformation_template(
    usage_data: TemplateUsageRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Use a transformation process template."""
    service = TransformationProcessTemplateService(db)
    return service.use_template(usage_data, current_user.id)


@router.get("/templates/{template_id}/metrics", response_model=TemplateMetricsResponse)
async def get_template_metrics(
    template_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get metrics for a transformation process template."""
    service = TransformationProcessTemplateService(db)
    return service.get_template_metrics(template_id)


# Real-time Monitoring Endpoints
@router.post("/monitoring/endpoints", response_model=RealTimeMonitoringEndpointResponse)
async def create_monitoring_endpoint(
    endpoint_data: RealTimeMonitoringEndpointCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new real-time monitoring endpoint."""
    service = RealTimeMonitoringService(db)
    return service.create_endpoint(endpoint_data, current_user.id)


@router.get("/monitoring/endpoints", response_model=List[RealTimeMonitoringEndpointResponse])
async def get_monitoring_endpoints(
    company_id: Optional[UUID] = Query(None),
    facility_id: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get real-time monitoring endpoints with optional filtering."""
    service = RealTimeMonitoringService(db)
    return service.get_endpoints(company_id, facility_id, is_active)


@router.post("/monitoring/ingest")
async def ingest_monitoring_data(
    data: MonitoringDataIngestion,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Ingest real-time monitoring data."""
    service = RealTimeMonitoringService(db)
    return service.ingest_monitoring_data(data)


# Utility Endpoints
@router.get("/health")
async def health_check():
    """Health check endpoint for transformation versioning services."""
    return {"status": "healthy", "services": ["versioning", "quality-inheritance", "cost-tracking", "templates", "monitoring"]}


@router.get("/stats")
async def get_system_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get system statistics for transformation versioning."""
    from sqlalchemy import func
    
    stats = {
        "total_versions": db.query(func.count(TransformationEventVersion.id)).scalar() or 0,
        "total_quality_rules": db.query(func.count(QualityInheritanceRule.id)).scalar() or 0,
        "total_costs": db.query(func.count(TransformationCost.id)).scalar() or 0,
        "total_templates": db.query(func.count(TransformationProcessTemplate.id)).scalar() or 0,
        "total_monitoring_endpoints": db.query(func.count(RealTimeMonitoringEndpoint.id)).scalar() or 0,
        "active_monitoring_endpoints": db.query(func.count(RealTimeMonitoringEndpoint.id))
            .filter(RealTimeMonitoringEndpoint.is_active == True).scalar() or 0
    }
    
    return stats

"""
Transformation API endpoints for comprehensive supply chain transformation tracking.
"""
from datetime import datetime, date
from typing import List, Optional, Dict, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, asc

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.models.company import Company
from app.models.transformation import (
    TransformationEvent,
    PlantationHarvestData,
    MillProcessingData,
    RefineryProcessingData,
    ManufacturerProcessingData,
    TransformationBatchMapping
)
from app.schemas.transformation import (
    TransformationEventCreate,
    TransformationEventUpdate,
    TransformationEventResponse,
    TransformationEventWithData,
    TransformationChainNode,
    TransformationChainResponse,
    TransformationSummaryResponse,
    TransformationEfficiencyMetrics,
    PlantationHarvestData as PlantationHarvestDataSchema,
    MillProcessingData as MillProcessingDataSchema,
    RefineryProcessingData as RefineryProcessingDataSchema,
    ManufacturerProcessingData as ManufacturerProcessingDataSchema,
    TransformationType,
    TransformationStatus,
    ValidationStatus
)
from app.services.transformation import TransformationService
from app.core.permissions import require_permission

router = APIRouter(prefix="/transformations", tags=["transformations"])


@router.post("/", response_model=TransformationEventResponse)
async def create_transformation_event(
    transformation_data: TransformationEventCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new transformation event."""
    require_permission(current_user, "create_transformation")
    
    service = TransformationService(db)
    return await service.create_transformation_event(transformation_data, current_user.id)


@router.get("/", response_model=List[TransformationSummaryResponse])
async def list_transformation_events(
    company_id: Optional[UUID] = Query(None, description="Filter by company ID"),
    transformation_type: Optional[TransformationType] = Query(None, description="Filter by transformation type"),
    status: Optional[TransformationStatus] = Query(None, description="Filter by status"),
    facility_id: Optional[str] = Query(None, description="Filter by facility ID"),
    start_date: Optional[date] = Query(None, description="Filter by start date"),
    end_date: Optional[date] = Query(None, description="Filter by end date"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List transformation events with filtering and pagination."""
    require_permission(current_user, "view_transformations")
    
    service = TransformationService(db)
    return await service.list_transformation_events(
        company_id=company_id,
        transformation_type=transformation_type,
        status=status,
        facility_id=facility_id,
        start_date=start_date,
        end_date=end_date,
        page=page,
        per_page=per_page,
        current_user=current_user
    )


@router.get("/{transformation_id}", response_model=TransformationEventWithData)
async def get_transformation_event(
    transformation_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific transformation event with role-specific data."""
    require_permission(current_user, "view_transformations")
    
    service = TransformationService(db)
    return await service.get_transformation_event(transformation_id, current_user)


@router.put("/{transformation_id}", response_model=TransformationEventResponse)
async def update_transformation_event(
    transformation_id: UUID,
    transformation_data: TransformationEventUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a transformation event."""
    require_permission(current_user, "update_transformation")
    
    service = TransformationService(db)
    return await service.update_transformation_event(transformation_id, transformation_data, current_user.id)


@router.delete("/{transformation_id}")
async def delete_transformation_event(
    transformation_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a transformation event."""
    require_permission(current_user, "delete_transformation")
    
    service = TransformationService(db)
    await service.delete_transformation_event(transformation_id, current_user.id)
    return {"message": "Transformation event deleted successfully"}


@router.post("/{transformation_id}/validate")
async def validate_transformation_event(
    transformation_id: UUID,
    validation_status: ValidationStatus,
    validation_notes: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Validate or reject a transformation event."""
    require_permission(current_user, "validate_transformation")
    
    service = TransformationService(db)
    return await service.validate_transformation_event(
        transformation_id, validation_status, validation_notes, current_user.id
    )


@router.get("/{transformation_id}/chain", response_model=TransformationChainResponse)
async def get_transformation_chain(
    transformation_id: UUID,
    max_depth: int = Query(10, ge=1, le=20, description="Maximum chain depth"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get the transformation chain for a specific transformation event."""
    require_permission(current_user, "view_transformations")
    
    service = TransformationService(db)
    return await service.get_transformation_chain(transformation_id, max_depth, current_user)


@router.get("/batch/{batch_id}/chain", response_model=TransformationChainResponse)
async def get_batch_transformation_chain(
    batch_id: UUID,
    max_depth: int = Query(10, ge=1, le=20, description="Maximum chain depth"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get the transformation chain for a specific batch."""
    require_permission(current_user, "view_transformations")
    
    service = TransformationService(db)
    return await service.get_batch_transformation_chain(batch_id, max_depth, current_user)


@router.get("/{transformation_id}/efficiency", response_model=TransformationEfficiencyMetrics)
async def get_transformation_efficiency(
    transformation_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get efficiency metrics for a transformation event."""
    require_permission(current_user, "view_transformations")
    
    service = TransformationService(db)
    return await service.get_transformation_efficiency(transformation_id, current_user)


@router.get("/analytics/summary")
async def get_transformation_analytics(
    company_id: Optional[UUID] = Query(None, description="Filter by company ID"),
    transformation_type: Optional[TransformationType] = Query(None, description="Filter by transformation type"),
    start_date: Optional[date] = Query(None, description="Start date for analytics"),
    end_date: Optional[date] = Query(None, description="End date for analytics"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get transformation analytics and summary statistics."""
    require_permission(current_user, "view_transformations")
    
    service = TransformationService(db)
    return await service.get_transformation_analytics(
        company_id=company_id,
        transformation_type=transformation_type,
        start_date=start_date,
        end_date=end_date,
        current_user=current_user
    )


# Role-specific data endpoints
@router.post("/{transformation_id}/plantation-data")
async def add_plantation_data(
    transformation_id: UUID,
    plantation_data: PlantationHarvestDataSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add plantation harvest data to a transformation event."""
    require_permission(current_user, "update_transformation")
    
    service = TransformationService(db)
    return await service.add_plantation_data(transformation_id, plantation_data, current_user.id)


@router.post("/{transformation_id}/mill-data")
async def add_mill_data(
    transformation_id: UUID,
    mill_data: MillProcessingDataSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add mill processing data to a transformation event."""
    require_permission(current_user, "update_transformation")
    
    service = TransformationService(db)
    return await service.add_mill_data(transformation_id, mill_data, current_user.id)


@router.post("/{transformation_id}/refinery-data")
async def add_refinery_data(
    transformation_id: UUID,
    refinery_data: RefineryProcessingDataSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add refinery processing data to a transformation event."""
    require_permission(current_user, "update_transformation")
    
    service = TransformationService(db)
    return await service.add_refinery_data(transformation_id, refinery_data, current_user.id)


@router.post("/{transformation_id}/manufacturer-data")
async def add_manufacturer_data(
    transformation_id: UUID,
    manufacturer_data: ManufacturerProcessingDataSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add manufacturer processing data to a transformation event."""
    require_permission(current_user, "update_transformation")
    
    service = TransformationService(db)
    return await service.add_manufacturer_data(transformation_id, manufacturer_data, current_user.id)


@router.get("/types/supported")
async def get_supported_transformation_types():
    """Get list of supported transformation types."""
    return {
        "transformation_types": [t.value for t in TransformationType],
        "statuses": [s.value for s in TransformationStatus],
        "validation_statuses": [v.value for v in ValidationStatus]
    }


@router.get("/roles/mapping")
async def get_role_transformation_mapping():
    """Get mapping of company roles to supported transformation types."""
    return {
        "plantation_grower": ["HARVEST"],
        "mill_processor": ["MILLING"],
        "refinery_crusher": ["CRUSHING", "REFINING", "FRACTIONATION"],
        "manufacturer": ["BLENDING", "MANUFACTURING"],
        "trader_aggregator": ["STORAGE", "TRANSPORT"],
        "smallholder_cooperative": ["HARVEST", "STORAGE"],
        "brand": ["MANUFACTURING", "BLENDING"]
    }

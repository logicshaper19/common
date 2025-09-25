"""
Transformation Dashboard API endpoints for role-based transformation management.
Integrates with existing permission system and follows current navigation patterns.
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
    TransformationEventResponse,
    TransformationEventWithData,
    TransformationType,
    TransformationStatus
)
import importlib.util
import sys
spec = importlib.util.spec_from_file_location('transformation_service', 'app/services/transformation.py')
transformation_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(transformation_module)
TransformationServiceClass = transformation_module.TransformationService
from app.core.permissions import require_permission
from app.services.permissions import PermissionService

router = APIRouter(prefix="/transformation-dashboard", tags=["transformation-dashboard"])


@router.get("/my-transformations")
async def get_my_transformations(
    status: Optional[TransformationStatus] = Query(None, description="Filter by status"),
    transformation_type: Optional[TransformationType] = Query(None, description="Filter by type"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get transformations for the current user's company with role-based filtering.
    This powers the main transformation dashboard table.
    """
    require_permission(current_user, "view_transformations")
    
    service = TransformationServiceClass(db)
    
    # Filter by current user's company
    company_id = current_user.company_id
    company_type = current_user.company.company_type
    
    # ROLE-BASED FILTERING: Automatically filter by transformation types allowed for this company type
    allowed_transformation_types = get_allowed_transformation_types_for_company_type(company_type)
    
    # If user specifies a transformation_type, validate it's allowed for their role
    if transformation_type and transformation_type not in allowed_transformation_types:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Company type '{company_type}' is not authorized to view '{transformation_type.value}' transformations"
        )
    
    # Get transformations with role-specific data
    transformations = await service.list_transformation_events(
        company_id=company_id,
        transformation_type=transformation_type,
        status=status,
        page=page,
        per_page=per_page,
        current_user=current_user,
        allowed_transformation_types=allowed_transformation_types  # Pass role-based filter
    )
    
    # Add role-specific columns based on company type
    company_type = current_user.company.company_type
    enhanced_transformations = []
    
    for transformation in transformations:
        enhanced_data = {
            "id": transformation.id,
            "transformation_type": transformation.transformation_type,
            "status": transformation.status,
            "start_time": transformation.start_time,
            "end_time": transformation.end_time,
            "facility_id": transformation.facility_id,
            "yield_percentage": transformation.yield_percentage,
            "quality_score": transformation.quality_score,
            "created_at": transformation.created_at,
            "updated_at": transformation.updated_at,
        }
        
        # Add role-specific columns
        if company_type == "plantation_grower":
            enhanced_data.update({
                "harvest_area_hectares": getattr(transformation.plantation_data, 'harvest_area_hectares', None) if hasattr(transformation, 'plantation_data') else None,
                "ffb_tonnes": getattr(transformation.plantation_data, 'ffb_tonnes', None) if hasattr(transformation, 'plantation_data') else None,
                "oil_yield_percentage": getattr(transformation.plantation_data, 'oil_yield_percentage', None) if hasattr(transformation, 'plantation_data') else None,
            })
        elif company_type == "mill_processor":
            enhanced_data.update({
                "ffb_input_tonnes": getattr(transformation.mill_data, 'ffb_input_tonnes', None) if hasattr(transformation, 'mill_data') else None,
                "cpo_output_tonnes": getattr(transformation.mill_data, 'cpo_output_tonnes', None) if hasattr(transformation, 'mill_data') else None,
                "pks_output_tonnes": getattr(transformation.mill_data, 'pks_output_tonnes', None) if hasattr(transformation, 'mill_data') else None,
                "extraction_rate": getattr(transformation.mill_data, 'extraction_rate', None) if hasattr(transformation, 'mill_data') else None,
            })
        elif company_type == "refinery_crusher":
            enhanced_data.update({
                "cpo_input_tonnes": getattr(transformation.refinery_data, 'cpo_input_tonnes', None) if hasattr(transformation, 'refinery_data') else None,
                "rbd_po_output_tonnes": getattr(transformation.refinery_data, 'rbd_po_output_tonnes', None) if hasattr(transformation, 'refinery_data') else None,
                "pko_output_tonnes": getattr(transformation.refinery_data, 'pko_output_tonnes', None) if hasattr(transformation, 'refinery_data') else None,
                "refining_efficiency": getattr(transformation.refinery_data, 'refining_efficiency', None) if hasattr(transformation, 'refinery_data') else None,
            })
        elif company_type == "manufacturer":
            enhanced_data.update({
                "raw_material_input_tonnes": getattr(transformation.manufacturer_data, 'raw_material_input_tonnes', None) if hasattr(transformation, 'manufacturer_data') else None,
                "finished_product_output_tonnes": getattr(transformation.manufacturer_data, 'finished_product_output_tonnes', None) if hasattr(transformation, 'manufacturer_data') else None,
                "production_efficiency": getattr(transformation.manufacturer_data, 'production_efficiency', None) if hasattr(transformation, 'manufacturer_data') else None,
            })
        
        enhanced_transformations.append(enhanced_data)
    
    return {
        "transformations": enhanced_transformations,
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": len(enhanced_transformations),  # This would be the actual total from the service
        },
        "company_type": company_type,
        "role_specific_columns": get_role_specific_columns(company_type)
    }


@router.get("/dashboard-stats")
async def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get dashboard statistics and KPIs for the transformation dashboard widgets.
    Only counts transformations that the company type is authorized to view.
    """
    require_permission(current_user, "view_transformations")
    
    service = TransformationServiceClass(db)
    company_id = current_user.company_id
    company_type = current_user.company.company_type
    
    # Get allowed transformation types for role-based filtering
    allowed_transformation_types = get_allowed_transformation_types_for_company_type(company_type)
    
    # Get basic stats with role-based filtering
    total_transformations = await service.count_transformations_by_company(company_id, allowed_transformation_types)
    active_transformations = await service.count_transformations_by_status(company_id, TransformationStatus.IN_PROGRESS, allowed_transformation_types)
    completed_transformations = await service.count_transformations_by_status(company_id, TransformationStatus.COMPLETED, allowed_transformation_types)
    
    # Get role-specific KPIs
    kpis = await get_role_specific_kpis(service, company_id, company_type)
    
    return {
        "total_transformations": total_transformations,
        "active_transformations": active_transformations,
        "completed_transformations": completed_transformations,
        "company_type": company_type,
        "kpis": kpis,
        "last_updated": datetime.utcnow()
    }


@router.get("/available-input-batches")
async def get_available_input_batches(
    transformation_type: Optional[TransformationType] = Query(None, description="Filter by transformation type"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get available input batches for creating new transformations.
    This powers the batch selector in the transformation creation form.
    """
    require_permission(current_user, "create_transformation")
    
    # This would integrate with the batch/inventory system
    # For now, return a placeholder structure
    return {
        "available_batches": [],
        "message": "Batch integration needed - this would connect to inventory system",
        "transformation_type": transformation_type,
        "company_id": current_user.company_id
    }


@router.get("/transformation-templates")
async def get_transformation_templates(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get transformation templates based on the user's company type.
    This provides role-specific forms for creating transformations.
    Only returns templates for transformation types the company is authorized to use.
    """
    require_permission(current_user, "create_transformation")
    
    company_type = current_user.company.company_type
    allowed_transformation_types = get_allowed_transformation_types_for_company_type(company_type)
    
    # Return role-specific templates filtered by allowed transformation types
    all_templates = get_transformation_templates_by_role(company_type)
    filtered_templates = [
        template for template in all_templates 
        if template.get('transformation_type') in [t.value for t in allowed_transformation_types]
    ]
    
    return {
        "templates": filtered_templates,
        "company_type": company_type,
        "allowed_transformation_types": [t.value for t in allowed_transformation_types],
        "available_transformation_types": get_available_transformation_types(company_type)
    }


# Helper functions

def get_role_specific_columns(company_type: str) -> List[Dict[str, str]]:
    """Get column definitions for role-specific transformation data."""
    column_mappings = {
        "plantation_grower": [
            {"key": "harvest_area_hectares", "label": "Harvest Area (ha)", "type": "number"},
            {"key": "ffb_tonnes", "label": "FFB (tonnes)", "type": "number"},
            {"key": "oil_yield_percentage", "label": "Oil Yield %", "type": "percentage"},
        ],
        "mill_processor": [
            {"key": "ffb_input_tonnes", "label": "FFB Input (tonnes)", "type": "number"},
            {"key": "cpo_output_tonnes", "label": "CPO Output (tonnes)", "type": "number"},
            {"key": "pks_output_tonnes", "label": "PKS Output (tonnes)", "type": "number"},
            {"key": "extraction_rate", "label": "Extraction Rate %", "type": "percentage"},
        ],
        "refinery_crusher": [
            {"key": "cpo_input_tonnes", "label": "CPO Input (tonnes)", "type": "number"},
            {"key": "rbd_po_output_tonnes", "label": "RBD PO Output (tonnes)", "type": "number"},
            {"key": "pko_output_tonnes", "label": "PKO Output (tonnes)", "type": "number"},
            {"key": "refining_efficiency", "label": "Refining Efficiency %", "type": "percentage"},
        ],
        "manufacturer": [
            {"key": "raw_material_input_tonnes", "label": "Raw Material Input (tonnes)", "type": "number"},
            {"key": "finished_product_output_tonnes", "label": "Finished Product Output (tonnes)", "type": "number"},
            {"key": "production_efficiency", "label": "Production Efficiency %", "type": "percentage"},
        ],
    }
    
    return column_mappings.get(company_type, [])


async def get_role_specific_kpis(service: TransformationServiceClass, company_id: UUID, company_type: str) -> Dict[str, Any]:
    """Get role-specific KPIs for the dashboard."""
    kpis = {}
    
    if company_type == "plantation_grower":
        kpis.update({
            "average_yield_per_hectare": 0,  # Would calculate from actual data
            "total_harvest_area": 0,
            "oil_yield_trend": "stable"  # Would calculate trend
        })
    elif company_type == "mill_processor":
        kpis.update({
            "average_extraction_rate": 0,  # Would calculate from actual data
            "total_ffb_processed": 0,
            "efficiency_trend": "stable"  # Would calculate trend
        })
    elif company_type == "refinery_crusher":
        kpis.update({
            "average_refining_efficiency": 0,  # Would calculate from actual data
            "total_cpo_processed": 0,
            "quality_trend": "stable"  # Would calculate trend
        })
    elif company_type == "manufacturer":
        kpis.update({
            "average_production_efficiency": 0,  # Would calculate from actual data
            "total_raw_material_used": 0,
            "waste_reduction_trend": "stable"  # Would calculate trend
        })
    
    return kpis


def get_transformation_templates_by_role(company_type: str) -> List[Dict[str, Any]]:
    """Get transformation templates based on company type."""
    templates = {
        "plantation_grower": [
            {
                "id": "harvest_ffb",
                "name": "FFB Harvest",
                "transformation_type": "harvest",
                "description": "Record fresh fruit bunch harvest data",
                "fields": [
                    {"name": "harvest_area_hectares", "label": "Harvest Area (hectares)", "type": "number", "required": True},
                    {"name": "ffb_tonnes", "label": "FFB (tonnes)", "type": "number", "required": True},
                    {"name": "oil_yield_percentage", "label": "Oil Yield %", "type": "number", "required": True},
                ]
            }
        ],
        "mill_processor": [
            {
                "id": "mill_processing",
                "name": "Mill Processing",
                "transformation_type": "mill_processing",
                "description": "Record mill processing data",
                "fields": [
                    {"name": "ffb_input_tonnes", "label": "FFB Input (tonnes)", "type": "number", "required": True},
                    {"name": "cpo_output_tonnes", "label": "CPO Output (tonnes)", "type": "number", "required": True},
                    {"name": "pks_output_tonnes", "label": "PKS Output (tonnes)", "type": "number", "required": True},
                    {"name": "extraction_rate", "label": "Extraction Rate %", "type": "number", "required": True},
                ]
            }
        ],
        "refinery_crusher": [
            {
                "id": "refinery_processing",
                "name": "Refinery Processing",
                "transformation_type": "refinery_processing",
                "description": "Record refinery processing data",
                "fields": [
                    {"name": "cpo_input_tonnes", "label": "CPO Input (tonnes)", "type": "number", "required": True},
                    {"name": "rbd_po_output_tonnes", "label": "RBD PO Output (tonnes)", "type": "number", "required": True},
                    {"name": "pko_output_tonnes", "label": "PKO Output (tonnes)", "type": "number", "required": True},
                    {"name": "refining_efficiency", "label": "Refining Efficiency %", "type": "number", "required": True},
                ]
            }
        ],
        "manufacturer": [
            {
                "id": "manufacturing",
                "name": "Manufacturing",
                "transformation_type": "manufacturing",
                "description": "Record manufacturing data",
                "fields": [
                    {"name": "raw_material_input_tonnes", "label": "Raw Material Input (tonnes)", "type": "number", "required": True},
                    {"name": "finished_product_output_tonnes", "label": "Finished Product Output (tonnes)", "type": "number", "required": True},
                    {"name": "production_efficiency", "label": "Production Efficiency %", "type": "number", "required": True},
                ]
            }
        ],
    }
    
    return templates.get(company_type, [])


def get_available_transformation_types(company_type: str) -> List[str]:
    """Get available transformation types for a company type."""
    type_mappings = {
        "plantation_grower": ["harvest"],
        "mill_processor": ["mill_processing"],
        "refinery_crusher": ["refinery_processing"],
        "manufacturer": ["manufacturing"],
        "trader_aggregator": ["trading", "aggregation"],
    }
    
    return type_mappings.get(company_type, [])


def get_allowed_transformation_types_for_company_type(company_type: str) -> List[TransformationType]:
    """
    Get the transformation types that a company type is allowed to view and manage.
    This enforces role-based access control at the data level.
    """
    from app.models.transformation import TransformationType
    
    # Map company types to their allowed transformation types
    type_mappings = {
        "plantation_grower": [TransformationType.HARVEST],
        "smallholder_cooperative": [TransformationType.HARVEST],  # May have basic processing
        "mill_processor": [TransformationType.MILLING, TransformationType.CRUSHING],
        "refinery_crusher": [TransformationType.REFINING, TransformationType.FRACTIONATION],
        "manufacturer": [TransformationType.MANUFACTURING, TransformationType.BLENDING, TransformationType.REPACKING],
        "oleochemical_producer": [TransformationType.MANUFACTURING, TransformationType.BLENDING],
        "trader_aggregator": [TransformationType.REPACKING],  # Only repacking for traders
    }
    
    return type_mappings.get(company_type, [])

"""
Enhanced transformation API endpoints with automatic role-specific data population.

This module provides API endpoints for creating transformations with comprehensive
role-specific data pre-filled based on company type and transformation type.
"""
from typing import Dict, Any, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.services.enhanced_transformation_creation import EnhancedTransformationCreationService
from app.services.transformation_templates import TransformationTemplateEngine
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/transformations-enhanced", tags=["Enhanced Transformations"])


@router.post("/create-complete")
async def create_complete_transformation(
    transformation_data: Dict[str, Any],
    auto_populate_role_data: bool = True,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a complete transformation event with automatic role-specific data population.
    
    This endpoint automatically:
    - Pre-fills role-specific data based on company type
    - Creates appropriate data tables (plantation, mill, refinery, manufacturer)
    - Suggests output batches
    - Applies quality metrics and process parameters
    """
    try:
        service = EnhancedTransformationCreationService(db)
        
        result = await service.create_complete_transformation(
            transformation_data=transformation_data,
            user_id=current_user.id,
            auto_populate_role_data=auto_populate_role_data
        )
        
        logger.info(
            f"Created complete transformation via API",
            user_id=str(current_user.id),
            company_id=str(current_user.company_id),
            transformation_id=result.get('transformation_event_id'),
            auto_populated=result.get('auto_populated')
        )
        
        return {
            "success": True,
            "message": "Complete transformation created successfully",
            "data": result
        }
        
    except Exception as e:
        logger.error(f"Failed to create complete transformation: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create complete transformation: {str(e)}"
        )


@router.post("/create-from-suggestion")
async def create_transformation_from_suggestion(
    suggestion_data: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a transformation event from a pre-generated suggestion.
    
    This endpoint takes a transformation suggestion (e.g., from PO confirmation)
    and creates a complete transformation event with all data populated.
    """
    try:
        service = EnhancedTransformationCreationService(db)
        
        # Extract the suggestion data and convert to transformation data
        transformation_data = {
            "event_id": suggestion_data.get("event_id"),
            "transformation_type": suggestion_data.get("transformation_type"),
            "company_id": suggestion_data.get("company_id"),
            "facility_id": suggestion_data.get("facility_id"),
            "input_batches": suggestion_data.get("input_batches", []),
            "output_batches": suggestion_data.get("output_batches", []),
            "process_description": suggestion_data.get("process_description"),
            "start_time": suggestion_data.get("start_time"),
            "location_name": suggestion_data.get("location_name"),
            "location_coordinates": suggestion_data.get("location_coordinates"),
            "weather_conditions": suggestion_data.get("weather_conditions"),
            "quality_metrics": suggestion_data.get("quality_metrics", {}),
            "process_parameters": suggestion_data.get("process_parameters", {}),
            "efficiency_metrics": suggestion_data.get("efficiency_metrics", {}),
            "certifications": suggestion_data.get("certifications", []),
            "compliance_data": suggestion_data.get("compliance_data", {}),
            "status": suggestion_data.get("status", "planned"),
            "validation_status": suggestion_data.get("validation_status", "pending"),
            "event_metadata": suggestion_data.get("event_metadata", {}),
            "role_specific_data": suggestion_data.get("role_specific_data", {}),
            "output_batch_suggestion": suggestion_data.get("output_batch_suggestion", {})
        }
        
        result = await service.create_complete_transformation(
            transformation_data=transformation_data,
            user_id=current_user.id,
            auto_populate_role_data=True
        )
        
        logger.info(
            f"Created transformation from suggestion via API",
            user_id=str(current_user.id),
            company_id=str(current_user.company_id),
            transformation_id=result.get('transformation_event_id'),
            source_suggestion=suggestion_data.get("event_id")
        )
        
        return {
            "success": True,
            "message": "Transformation created from suggestion successfully",
            "data": result
        }
        
    except Exception as e:
        logger.error(f"Failed to create transformation from suggestion: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create transformation from suggestion: {str(e)}"
        )


@router.get("/templates/{company_type}")
async def get_transformation_templates(
    company_type: str,
    transformation_type: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get transformation templates for a specific company type.
    
    This endpoint returns pre-filled templates that can be used to create
    transformation events with appropriate role-specific data.
    """
    try:
        template_engine = TransformationTemplateEngine()
        
        if transformation_type:
            # Get specific transformation type template
            from app.models.transformation import TransformationType
            trans_type = TransformationType(transformation_type)
            template = template_engine.get_transformation_template(
                transformation_type=trans_type,
                company_type=company_type
            )
        else:
            # Get all available templates for company type
            from app.models.transformation import TransformationType
            templates = {}
            
            # Map company types to their supported transformation types
            company_transformation_map = {
                "plantation_grower": [TransformationType.HARVEST],
                "mill_processor": [TransformationType.MILLING],
                "refinery_crusher": [TransformationType.REFINING],
                "manufacturer": [TransformationType.MANUFACTURING]
            }
            
            supported_types = company_transformation_map.get(company_type, [])
            for trans_type in supported_types:
                templates[trans_type.value] = template_engine.get_transformation_template(
                    transformation_type=trans_type,
                    company_type=company_type
                )
            
            template = templates
        
        return {
            "success": True,
            "company_type": company_type,
            "transformation_type": transformation_type,
            "template": template
        }
        
    except Exception as e:
        logger.error(f"Failed to get transformation templates: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get transformation templates: {str(e)}"
        )


@router.get("/suggestions/{company_id}")
async def get_transformation_suggestions(
    company_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get transformation suggestions for a company.
    
    This endpoint returns any pending transformation suggestions that were
    generated from PO confirmations or other automated processes.
    """
    try:
        # TODO: Implement suggestion storage and retrieval
        # For now, return empty list
        suggestions = []
        
        return {
            "success": True,
            "company_id": str(company_id),
            "suggestions": suggestions,
            "count": len(suggestions)
        }
        
    except Exception as e:
        logger.error(f"Failed to get transformation suggestions: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get transformation suggestions: {str(e)}"
        )


@router.post("/validate-role-data")
async def validate_role_specific_data(
    transformation_type: str,
    role_data: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Validate role-specific data before creating a transformation.
    
    This endpoint validates that the provided role-specific data meets
    the requirements for the specified transformation type.
    """
    try:
        from app.models.transformation import TransformationType
        
        trans_type = TransformationType(transformation_type)
        
        # Basic validation based on transformation type
        validation_errors = []
        
        if trans_type == TransformationType.HARVEST:
            required_fields = ['farm_id', 'harvest_date', 'yield_per_hectare']
            for field in required_fields:
                if field not in role_data or not role_data[field]:
                    validation_errors.append(f"Missing required field: {field}")
        
        elif trans_type == TransformationType.MILLING:
            required_fields = ['extraction_rate', 'ffb_quantity', 'cpo_quantity']
            for field in required_fields:
                if field not in role_data or not role_data[field]:
                    validation_errors.append(f"Missing required field: {field}")
        
        elif trans_type == TransformationType.REFINING:
            required_fields = ['process_type', 'input_oil_quantity', 'iv_value']
            for field in required_fields:
                if field not in role_data or not role_data[field]:
                    validation_errors.append(f"Missing required field: {field}")
        
        elif trans_type == TransformationType.MANUFACTURING:
            required_fields = ['product_type', 'recipe_ratios', 'output_quantity']
            for field in required_fields:
                if field not in role_data or not role_data[field]:
                    validation_errors.append(f"Missing required field: {field}")
        
        is_valid = len(validation_errors) == 0
        
        return {
            "success": True,
            "is_valid": is_valid,
            "validation_errors": validation_errors,
            "transformation_type": transformation_type
        }
        
    except Exception as e:
        logger.error(f"Failed to validate role-specific data: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate role-specific data: {str(e)}"
        )

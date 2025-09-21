"""
Enhanced transformation API endpoints with proper error handling and dependency injection.

This module provides robust API endpoints for transformation operations with:
- Comprehensive input validation
- Proper error handling with custom exceptions
- Dependency injection for better testability
- Atomic transaction management
- Detailed logging and monitoring
"""
from typing import Dict, Any, Optional, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import ValidationError as PydanticValidationError

from app.core.database import get_db
from app.core.auth import get_current_user_sync
from app.models.user import User
from app.services.transformation.enhanced_creation_service import EnhancedTransformationCreationService
from app.services.transformation.templates import create_template_engine
from app.services.transformation.exceptions import (
    TransformationError,
    ValidationError,
    DataIntegrityError,
    TransactionError,
    TemplateGenerationError,
    EntityNotFoundError
)
from app.services.transformation.schemas import (
    TransformationTemplateRequest,
    RoleDataValidationRequest,
    CompleteTransformationRequest,
    TransformationResponseSchema
)
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


def get_enhanced_transformation_service(db: Session = Depends(get_db)) -> EnhancedTransformationCreationService:
    """Dependency injection for enhanced transformation service."""
    return EnhancedTransformationCreationService(db)


def get_template_engine(db: Session = Depends(get_db)):
    """Dependency injection for template engine."""
    return create_template_engine(db)


@router.post("/create-complete", response_model=Dict[str, Any])
def create_complete_transformation(
    request: CompleteTransformationRequest,
    current_user: User = Depends(get_current_user_sync),
    service: EnhancedTransformationCreationService = Depends(get_enhanced_transformation_service)
):
    """
    Create a complete transformation event with automatic role-specific data population.
    
    This endpoint:
    - Validates input data using Pydantic schemas
    - Creates transformation event with atomic transaction
    - Auto-populates role-specific data based on templates
    - Provides comprehensive error handling
    """
    logger.info(
        "Creating complete transformation",
        user_id=str(current_user.id),
        company_id=str(current_user.company_id)
    )
    
    try:
        # Add user context to transformation data
        transformation_data = request.transformation_data.copy()
        transformation_data.update({
            "user_id": current_user.id,
            "company_id": current_user.company_id
        })
        
        # Create transformation
        result = service.create_complete_transformation(
            transformation_data=transformation_data,
            user_id=current_user.id,
            auto_populate_role_data=request.auto_populate_role_data
        )
        
        logger.info(
            "Transformation created successfully",
            transformation_id=result.get("transformation_id"),
            user_id=str(current_user.id)
        )
        
        return {
            "success": True,
            "data": result,
            "message": "Transformation created successfully"
        }
        
    except PydanticValidationError as e:
        logger.warning(
            "Validation error in transformation creation",
            user_id=str(current_user.id),
            errors=str(e.errors())
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": "Validation failed",
                "errors": e.errors(),
                "message": "Invalid input data"
            }
        )
        
    except ValidationError as e:
        logger.warning(
            "Business validation error in transformation creation",
            user_id=str(current_user.id),
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "Validation failed",
                "message": e.user_message,
                "details": e.details
            }
        )
        
    except TemplateGenerationError as e:
        logger.error(
            "Template generation error in transformation creation",
            user_id=str(current_user.id),
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Template generation failed",
                "message": e.user_message,
                "details": e.details
            }
        )
        
    except DataIntegrityError as e:
        logger.error(
            "Data integrity error in transformation creation",
            user_id=str(current_user.id),
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "Data integrity error",
                "message": e.user_message,
                "details": e.details
            }
        )
        
    except TransactionError as e:
        logger.error(
            "Transaction error in transformation creation",
            user_id=str(current_user.id),
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Transaction failed",
                "message": e.user_message,
                "details": e.details
            }
        )
        
    except Exception as e:
        logger.error(
            "Unexpected error in transformation creation",
            user_id=str(current_user.id),
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Internal server error",
                "message": "An unexpected error occurred"
            }
        )


@router.post("/template", response_model=Dict[str, Any])
def get_transformation_template(
    request: TransformationTemplateRequest,
    current_user: User = Depends(get_current_user_sync),
    template_engine = Depends(get_template_engine)
):
    """
    Get a transformation template for the given parameters.
    
    This endpoint:
    - Validates input parameters
    - Generates comprehensive template with role-specific data
    - Provides industry standards and best practices
    """
    logger.info(
        "Generating transformation template",
        user_id=str(current_user.id),
        transformation_type=request.transformation_type.value,
        company_type=request.company_type
    )
    
    try:
        # Generate template
        template = template_engine.get_template(
            transformation_type=request.transformation_type,
            company_type=request.company_type,
            input_batch_data=request.input_batch_data,
            facility_id=request.facility_id
        )
        
        logger.info(
            "Template generated successfully",
            user_id=str(current_user.id),
            template_size=len(template)
        )
        
        return {
            "success": True,
            "data": template,
            "message": "Template generated successfully"
        }
        
    except PydanticValidationError as e:
        logger.warning(
            "Validation error in template generation",
            user_id=str(current_user.id),
            errors=str(e.errors())
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": "Validation failed",
                "errors": e.errors(),
                "message": "Invalid input parameters"
            }
        )
        
    except TemplateGenerationError as e:
        logger.error(
            "Template generation error",
            user_id=str(current_user.id),
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Template generation failed",
                "message": e.user_message,
                "details": e.details
            }
        )
        
    except Exception as e:
        logger.error(
            "Unexpected error in template generation",
            user_id=str(current_user.id),
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Internal server error",
                "message": "An unexpected error occurred"
            }
        )


@router.post("/validate-role-data", response_model=Dict[str, Any])
def validate_role_data(
    request: RoleDataValidationRequest,
    current_user: User = Depends(get_current_user_sync),
    service: EnhancedTransformationCreationService = Depends(get_enhanced_transformation_service)
):
    """
    Validate role-specific data for a transformation.
    
    This endpoint:
    - Validates role-specific data against business rules
    - Provides detailed validation error messages
    - Supports all transformation types and company types
    """
    logger.info(
        "Validating role data",
        user_id=str(current_user.id),
        transformation_type=request.transformation_type.value,
        company_type=request.company_type
    )
    
    try:
        # Validate role data
        is_valid, validation_errors = service.validate_role_data(
            transformation_type=request.transformation_type,
            company_type=request.company_type,
            role_data=request.role_data
        )
        
        logger.info(
            "Role data validation completed",
            user_id=str(current_user.id),
            is_valid=is_valid,
            error_count=len(validation_errors)
        )
        
        return {
            "success": True,
            "data": {
                "is_valid": is_valid,
                "validation_errors": validation_errors,
                "transformation_type": request.transformation_type.value,
                "company_type": request.company_type
            },
            "message": "Validation completed successfully"
        }
        
    except PydanticValidationError as e:
        logger.warning(
            "Validation error in role data validation",
            user_id=str(current_user.id),
            errors=str(e.errors())
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": "Validation failed",
                "errors": e.errors(),
                "message": "Invalid input data"
            }
        )
        
    except Exception as e:
        logger.error(
            "Unexpected error in role data validation",
            user_id=str(current_user.id),
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Internal server error",
                "message": "An unexpected error occurred"
            }
        )


@router.get("/templates/available", response_model=Dict[str, Any])
def get_available_templates(
    current_user: User = Depends(get_current_user_sync),
    template_engine = Depends(get_template_engine)
):
    """
    Get information about available transformation templates.
    
    This endpoint:
    - Lists all available company types and transformation types
    - Provides template capabilities and metadata
    - Helps clients understand what templates are available
    """
    logger.info(
        "Getting available templates",
        user_id=str(current_user.id)
    )
    
    try:
        # Get engine info
        engine_info = template_engine.get_engine_info()
        
        # Get available company types
        available_company_types = template_engine.get_available_company_types()
        
        # Get template metadata for each company type
        template_metadata = {}
        for company_type in available_company_types:
            template_metadata[company_type] = template_engine.get_template_metadata(company_type)
        
        logger.info(
            "Available templates retrieved successfully",
            user_id=str(current_user.id),
            company_types_count=len(available_company_types)
        )
        
        return {
            "success": True,
            "data": {
                "available_company_types": available_company_types,
                "template_metadata": template_metadata,
                "engine_info": engine_info
            },
            "message": "Available templates retrieved successfully"
        }
        
    except Exception as e:
        logger.error(
            "Unexpected error getting available templates",
            user_id=str(current_user.id),
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Internal server error",
                "message": "An unexpected error occurred"
            }
        )


@router.get("/health", response_model=Dict[str, Any])
def health_check(
    service: EnhancedTransformationCreationService = Depends(get_enhanced_transformation_service)
):
    """
    Health check endpoint for the transformation service.
    
    This endpoint:
    - Checks service health and dependencies
    - Provides service status and metadata
    - Useful for monitoring and debugging
    """
    try:
        # Get transaction stats
        transaction_stats = service.transaction_manager.get_transaction_stats()
        
        # Get template engine info
        template_engine_info = service.template_engine.get_engine_info()
        
        return {
            "success": True,
            "data": {
                "service_status": "healthy",
                "transaction_manager": transaction_stats,
                "template_engine": template_engine_info,
                "timestamp": "2024-01-01T00:00:00Z"  # This would be actual timestamp
            },
            "message": "Service is healthy"
        }
        
    except Exception as e:
        logger.error(
            "Health check failed",
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "Service unhealthy",
                "message": "Service health check failed"
            }
        )

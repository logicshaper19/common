"""
Enhanced origin data capture and validation API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.services.origin_data import OriginDataValidationService
from app.services.purchase_order import PurchaseOrderService
from app.schemas.origin_data import (
    OriginDataValidationRequest,
    ComprehensiveOriginDataValidationResponse,
    CertificationBodyInfo,
    PalmOilRegionInfo,
    OriginDataRequirements,
    OriginDataComplianceReport,
    BulkOriginDataValidationRequest,
    BulkOriginDataValidationResponse,
    CoordinateValidationResult,
    CertificationValidationResult,
    HarvestDateValidationResult,
    RegionalComplianceResult,
    ComplianceStatus
)
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/origin-data", tags=["origin-data"])


@router.post("/validate", response_model=ComprehensiveOriginDataValidationResponse)
def validate_origin_data_comprehensive(
    validation_request: OriginDataValidationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Perform comprehensive validation of origin data.
    
    This endpoint provides enhanced validation including:
    - Geographic coordinate boundary validation for palm oil regions
    - Comprehensive certification body validation
    - Regional compliance requirements checking
    - Quality scoring and compliance status determination
    - Detailed recommendations for improvement
    
    Requires access to the purchase order (buyer or seller).
    """
    origin_service = OriginDataValidationService(db)
    po_service = PurchaseOrderService(db)
    
    # Check access permissions
    po = po_service.get_purchase_order_by_id(str(validation_request.purchase_order_id))
    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase order not found"
        )
    
    if (current_user.company_id != po.buyer_company_id and 
        current_user.company_id != po.seller_company_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only validate origin data for your own purchase orders"
        )
    
    try:
        # Perform comprehensive validation
        validation_result = origin_service.validate_comprehensive_origin_data(
            validation_request.origin_data,
            po.product_id,
            validation_request.purchase_order_id
        )
        
        # Convert to response format
        response = ComprehensiveOriginDataValidationResponse(
            is_valid=validation_result.is_valid,
            quality_score=validation_result.quality_score,
            compliance_status=ComplianceStatus(validation_result.compliance_status),
            coordinate_validation=CoordinateValidationResult(**validation_result.coordinate_validation),
            certification_validation=CertificationValidationResult(**validation_result.certification_validation),
            harvest_date_validation=HarvestDateValidationResult(**validation_result.harvest_date_validation),
            regional_compliance=RegionalComplianceResult(**validation_result.regional_compliance),
            errors=validation_result.errors,
            warnings=validation_result.warnings,
            suggestions=validation_result.suggestions
        )
        
        logger.info(
            "Comprehensive origin data validation completed",
            po_id=str(validation_request.purchase_order_id),
            is_valid=validation_result.is_valid,
            quality_score=validation_result.quality_score,
            compliance_status=validation_result.compliance_status,
            user_id=str(current_user.id)
        )
        
        return response
        
    except Exception as e:
        logger.error(
            "Failed to validate origin data",
            po_id=str(validation_request.purchase_order_id),
            error=str(e),
            user_id=str(current_user.id)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to validate origin data"
        )


@router.get("/certification-bodies", response_model=List[CertificationBodyInfo])
def get_certification_bodies(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get list of recognized certification bodies.
    
    Returns comprehensive information about all recognized certification bodies
    including their descriptions, standards, and quality ratings.
    """
    origin_service = OriginDataValidationService(db)
    
    try:
        certification_bodies = origin_service.get_certification_bodies()
        
        response = [
            CertificationBodyInfo(
                code=cert["code"],
                name=cert["name"],
                description=cert["description"],
                is_high_value=cert["is_high_value"]
            )
            for cert in certification_bodies
        ]
        
        logger.info(
            "Certification bodies retrieved",
            count=len(response),
            user_id=str(current_user.id)
        )
        
        return response
        
    except Exception as e:
        logger.error(
            "Failed to retrieve certification bodies",
            error=str(e),
            user_id=str(current_user.id)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve certification bodies"
        )


@router.get("/palm-oil-regions", response_model=List[PalmOilRegionInfo])
def get_palm_oil_regions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get list of palm oil producing regions with geographic boundaries.
    
    Returns information about all recognized palm oil producing regions
    including their geographic boundaries and compliance requirements.
    """
    origin_service = OriginDataValidationService(db)
    
    try:
        regions = origin_service.get_palm_oil_regions()
        
        response = [
            PalmOilRegionInfo(
                code=region["code"],
                name=region["name"],
                description=region["description"],
                boundaries=region["boundaries"]
            )
            for region in regions
        ]
        
        logger.info(
            "Palm oil regions retrieved",
            count=len(response),
            user_id=str(current_user.id)
        )
        
        return response
        
    except Exception as e:
        logger.error(
            "Failed to retrieve palm oil regions",
            error=str(e),
            user_id=str(current_user.id)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve palm oil regions"
        )


@router.get("/requirements/{product_id}", response_model=OriginDataRequirements)
def get_origin_data_requirements(
    product_id: UUID,
    region: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get origin data requirements for a specific product and region.
    
    Returns detailed requirements including required fields, certifications,
    and quality parameters based on the product type and geographic region.
    """
    po_service = PurchaseOrderService(db)
    
    try:
        # Get product information
        product = po_service.product_service.get_product_by_id(str(product_id))
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
        
        # Build requirements based on product and region
        required_fields = ["geographic_coordinates"]
        optional_fields = ["harvest_date", "farm_information", "batch_number", "quality_parameters"]
        required_certifications = []
        recommended_certifications = ["RSPO", "NDPE"]
        
        # Add product-specific requirements
        if product.category == "raw_material":
            required_fields.extend(["certifications"])
            optional_fields.extend(["processing_notes", "transportation_method"])
        
        # Add region-specific requirements
        if region:
            if region in ["Southeast Asia", "West Africa"]:
                required_certifications.extend(["RSPO"])
                recommended_certifications.extend(["NDPE", "ISPO"])
        
        # Get product-specific requirements
        product_requirements = product.origin_data_requirements or {}
        if "required_fields" in product_requirements:
            required_fields.extend(product_requirements["required_fields"])
        if "required_certifications" in product_requirements:
            required_certifications.extend(product_requirements["required_certifications"])
        
        response = OriginDataRequirements(
            required_fields=list(set(required_fields)),
            optional_fields=list(set(optional_fields)),
            required_certifications=list(set(required_certifications)),
            recommended_certifications=list(set(recommended_certifications)),
            quality_parameters=product_requirements.get("quality_parameters"),
            regional_specific={"region": region} if region else None
        )
        
        logger.info(
            "Origin data requirements retrieved",
            product_id=str(product_id),
            region=region,
            user_id=str(current_user.id)
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to retrieve origin data requirements",
            product_id=str(product_id),
            region=region,
            error=str(e),
            user_id=str(current_user.id)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve origin data requirements"
        )


@router.post("/validate-coordinates", response_model=CoordinateValidationResult)
def validate_coordinates_only(
    latitude: float,
    longitude: float,
    accuracy_meters: Optional[float] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Validate geographic coordinates for palm oil regions.
    
    Quick validation endpoint for checking if coordinates fall within
    recognized palm oil producing regions and meet accuracy requirements.
    """
    from app.schemas.origin_data import EnhancedGeographicCoordinates
    
    origin_service = OriginDataValidationService(db)
    
    try:
        # Create coordinates object
        coords = EnhancedGeographicCoordinates(
            latitude=latitude,
            longitude=longitude,
            accuracy_meters=accuracy_meters
        )
        
        # Validate coordinates
        validation_result = origin_service._validate_geographic_coordinates(coords)
        
        response = CoordinateValidationResult(**validation_result)
        
        logger.info(
            "Coordinates validated",
            latitude=latitude,
            longitude=longitude,
            is_valid=response.is_valid,
            detected_region=response.detected_region,
            user_id=str(current_user.id)
        )
        
        return response
        
    except Exception as e:
        logger.error(
            "Failed to validate coordinates",
            latitude=latitude,
            longitude=longitude,
            error=str(e),
            user_id=str(current_user.id)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to validate coordinates"
        )

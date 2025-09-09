"""
Tier Requirements API
Endpoints for managing tier-based requirements for company types
"""
from typing import Dict, List, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.services.tier_requirements import TierRequirementsService, CompanyTypeProfile
from app.core.auth import get_current_user
from app.models.user import User


router = APIRouter(prefix="/api/v1/tier-requirements", tags=["tier-requirements"])


class TierRequirementResponse(BaseModel):
    """Response model for tier requirement."""
    type: str
    name: str
    description: str
    is_mandatory: bool
    validation_rules: Dict[str, Any]
    help_text: str = None


class CompanyTypeProfileResponse(BaseModel):
    """Response model for company type profile."""
    company_type: str
    tier_level: int
    sector_id: str
    transparency_weight: float
    base_requirements: List[TierRequirementResponse]
    sector_specific_requirements: List[TierRequirementResponse]


class RequirementValidationRequest(BaseModel):
    """Request model for requirement validation."""
    company_type: str
    sector_id: str
    coordinates: Dict[str, Any] = {}
    documents: Dict[str, Any] = {}
    certifications: Dict[str, Any] = {}


class RequirementValidationResponse(BaseModel):
    """Response model for requirement validation."""
    is_valid: bool
    missing_requirements: List[Dict[str, Any]]
    validation_errors: List[str]
    warnings: List[str]


@router.get("/profile/{company_type}/{sector_id}", response_model=CompanyTypeProfileResponse)
async def get_company_type_profile(
    company_type: str,
    sector_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get the complete tier requirements profile for a company type in a sector."""
    try:
        tier_service = TierRequirementsService(db)
        profile = tier_service.get_company_type_profile(company_type, sector_id)
        
        # Convert to response format
        base_requirements = [
            TierRequirementResponse(
                type=req.type.value,
                name=req.name,
                description=req.description,
                is_mandatory=req.is_mandatory,
                validation_rules=req.validation_rules,
                help_text=req.help_text
            )
            for req in profile.base_requirements
        ]
        
        sector_requirements = [
            TierRequirementResponse(
                type=req.type.value,
                name=req.name,
                description=req.description,
                is_mandatory=req.is_mandatory,
                validation_rules=req.validation_rules,
                help_text=req.help_text
            )
            for req in profile.sector_specific_requirements
        ]
        
        return CompanyTypeProfileResponse(
            company_type=profile.company_type.value,
            tier_level=profile.tier_level,
            sector_id=profile.sector_id,
            transparency_weight=profile.transparency_weight,
            base_requirements=base_requirements,
            sector_specific_requirements=sector_requirements
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get company type profile: {str(e)}"
        )


@router.post("/validate", response_model=RequirementValidationResponse)
async def validate_requirements(
    request: RequirementValidationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Validate that provided data meets tier requirements."""
    try:
        tier_service = TierRequirementsService(db)
        
        provided_data = {
            "coordinates": request.coordinates,
            "documents": request.documents,
            "certifications": request.certifications
        }
        
        validation_result = tier_service.validate_company_requirements(
            request.company_type,
            request.sector_id,
            provided_data
        )
        
        return RequirementValidationResponse(**validation_result)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate requirements: {str(e)}"
        )


@router.get("/company-types")
async def get_supported_company_types(
    current_user: User = Depends(get_current_user)
):
    """Get list of supported company types with their descriptions."""
    return {
        "company_types": [
            {
                "value": "originator",
                "label": "Originator (Raw Materials)",
                "description": "Primary producers like farms, plantations, mines",
                "transparency_weight": 1.0,
                "typical_tiers": [4, 5, 6]
            },
            {
                "value": "processor",
                "label": "Processor (Manufacturing)",
                "description": "Manufacturing and processing facilities",
                "transparency_weight": 0.8,
                "typical_tiers": [2, 3, 4]
            },
            {
                "value": "brand",
                "label": "Brand (Retail)",
                "description": "Retail brands and consumer-facing companies",
                "transparency_weight": 0.6,
                "typical_tiers": [1]
            },
            {
                "value": "trader",
                "label": "Trader (Aggregation)",
                "description": "Trading and aggregation companies",
                "transparency_weight": 0.4,
                "typical_tiers": [2, 3]
            }
        ]
    }


@router.get("/sectors")
async def get_supported_sectors(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get list of supported sectors with their tier structures."""
    from app.models.sector import Sector, SectorTier
    
    sectors = db.query(Sector).filter(Sector.is_active == True).all()
    
    result = []
    for sector in sectors:
        tiers = db.query(SectorTier).filter(SectorTier.sector_id == sector.id).order_by(SectorTier.level).all()
        
        result.append({
            "id": sector.id,
            "name": sector.name,
            "description": sector.description,
            "regulatory_focus": sector.regulatory_focus,
            "tiers": [
                {
                    "level": tier.level,
                    "name": tier.name,
                    "description": tier.description,
                    "is_originator": tier.is_originator,
                    "required_data_fields": tier.required_data_fields
                }
                for tier in tiers
            ]
        })
    
    return {"sectors": result}


@router.get("/requirements/summary/{company_type}/{sector_id}")
async def get_requirements_summary(
    company_type: str,
    sector_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a summary of requirements for quick display."""
    try:
        tier_service = TierRequirementsService(db)
        profile = tier_service.get_company_type_profile(company_type, sector_id)
        
        all_requirements = profile.base_requirements + profile.sector_specific_requirements
        mandatory_count = sum(1 for req in all_requirements if req.is_mandatory)
        optional_count = len(all_requirements) - mandatory_count
        
        requirement_types = {}
        for req in all_requirements:
            req_type = req.type.value
            if req_type not in requirement_types:
                requirement_types[req_type] = {"mandatory": 0, "optional": 0}
            
            if req.is_mandatory:
                requirement_types[req_type]["mandatory"] += 1
            else:
                requirement_types[req_type]["optional"] += 1
        
        return {
            "company_type": company_type,
            "sector_id": sector_id,
            "tier_level": profile.tier_level,
            "transparency_weight": profile.transparency_weight,
            "total_requirements": len(all_requirements),
            "mandatory_requirements": mandatory_count,
            "optional_requirements": optional_count,
            "requirement_types": requirement_types,
            "key_requirements": [
                {
                    "name": req.name,
                    "type": req.type.value,
                    "is_mandatory": req.is_mandatory
                }
                for req in all_requirements if req.is_mandatory
            ]
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get requirements summary: {str(e)}"
        )

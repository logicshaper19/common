"""
Farm Management API Endpoints

Provides farm-level traceability for ANY company type,
enabling brands, traders, processors, cooperatives, mills, and originators
to manage individual farms/plantations for regulatory compliance.
"""
from typing import List, Dict, Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.services.farm_management import FarmManagementService
from app.schemas.farm_management import (
    CompanyCapabilitiesResponse,
    FarmListResponse,
    BatchCreationRequest,
    BatchCreationResponse,
    BatchTraceabilityResponse
)

router = APIRouter(prefix="/farm-management", tags=["farm-management"])


@router.get("/company/{company_id}/capabilities", response_model=CompanyCapabilitiesResponse)
def get_company_capabilities(
    company_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get company capabilities for farm management
    
    Returns what a company can do based on its type and farm structure.
    Works for ANY company type (brands, traders, processors, cooperatives, mills, originators).
    """
    farm_service = FarmManagementService(db)
    
    try:
        capabilities = farm_service.get_company_capabilities(UUID(company_id))
        return CompanyCapabilitiesResponse(**capabilities)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get company capabilities: {str(e)}"
        )


@router.get("/company/{company_id}/farms", response_model=FarmListResponse)
def get_company_farms(
    company_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all farms for a company
    
    Returns detailed information about all farms/plantations owned by the company.
    """
    farm_service = FarmManagementService(db)
    
    try:
        farms = farm_service.get_company_farms(UUID(company_id))
        return FarmListResponse(
            company_id=company_id,
            total_farms=len(farms),
            farms=farms
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get company farms: {str(e)}"
        )


@router.post("/farms", response_model=dict)
def create_farm(
    farm_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new farm/plantation for the current user's company
    
    Creates a new farm location with all the enhanced fields including
    certifications, compliance status, and detailed location information.
    """
    farm_service = FarmManagementService(db)
    
    try:
        # Create the farm location
        farm = farm_service.create_farm(
            farm_data=farm_data,
            company_id=current_user.company_id,
            user_id=current_user.id
        )
        
        return {
            "farm_id": str(farm.id),
            "farm_name": farm.name,
            "message": "Farm created successfully"
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create farm: {str(e)}"
        )


@router.post("/batches", response_model=BatchCreationResponse)
def create_batch_with_farm_contributions(
    batch_request: BatchCreationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a batch with farm-level contributions
    
    Enables any company to create batches from their farms with full traceability.
    """
    farm_service = FarmManagementService(db)
    
    try:
        result = farm_service.create_batch_with_farm_contributions(
            batch_data=batch_request.batch_data,
            farm_contributions=batch_request.farm_contributions,
            company_id=current_user.company_id,
            user_id=current_user.id
        )
        
        return BatchCreationResponse(**result)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create batch: {str(e)}"
        )


@router.get("/batches/{batch_id}/traceability", response_model=BatchTraceabilityResponse)
def get_batch_farm_traceability(
    batch_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get complete farm-level traceability for a batch
    
    Returns detailed traceability information showing which farms contributed
    to the batch, with full regulatory compliance data.
    """
    farm_service = FarmManagementService(db)
    
    try:
        traceability = farm_service.get_batch_farm_traceability(UUID(batch_id))
        return BatchTraceabilityResponse(**traceability)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get batch traceability: {str(e)}"
        )


@router.get("/batches/{batch_id}/compliance")
def get_batch_compliance_status(
    batch_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get regulatory compliance status for a batch
    
    Returns EUDR, US, and other regulatory compliance status for all farms
    contributing to the batch.
    """
    farm_service = FarmManagementService(db)
    
    try:
        traceability = farm_service.get_batch_farm_traceability(UUID(batch_id))
        
        # Extract compliance information
        compliance_status = {
            "batch_id": traceability["batch_id"],
            "batch_number": traceability["batch_number"],
            "regulatory_compliance": traceability["regulatory_compliance"],
            "farm_compliance_details": [
                {
                    "farm_id": farm["farm_id"],
                    "farm_name": farm["farm_name"],
                    "compliance_status": farm["compliance_status"],
                    "coordinates": farm["coordinates"],
                    "certifications": farm["certifications"]
                }
                for farm in traceability["farms"]
            ]
        }
        
        return compliance_status
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get compliance status: {str(e)}"
        )

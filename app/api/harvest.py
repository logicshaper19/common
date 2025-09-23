"""
Harvest declaration API endpoints.

This API handles harvest declarations that create batches with origin data,
following the correct "create then transfer" model where harvest events
create batches that can later be sold via Purchase Orders.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import status as http_status
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Optional
from uuid import UUID
from datetime import date, datetime

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.models.batch import Batch
from app.schemas.batch import BatchType, BatchStatus
from app.services.batch import BatchTrackingService
from app.schemas.batch import BatchCreate, BatchResponse, BatchListResponse
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/harvest", tags=["harvest"])


@router.get("/farms")
def get_farm_locations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get farm locations for the current user's company.
    
    Returns all farm locations that the current user's company has access to.
    """
    try:
        from app.models.location import Location
        
        # Get farm locations for the current user's company
        farm_locations = db.query(Location).filter(
            Location.company_id == current_user.company_id,
            Location.is_farm_location == True,
            Location.is_active == True
        ).all()
        
        # Convert to response format
        farms = []
        for location in farm_locations:
            farm_data = {
                "id": str(location.id),
                "name": location.name,
                "registration_number": location.registration_number,
                "farm_type": location.farm_type,
                "farm_size_hectares": float(location.farm_size_hectares) if location.farm_size_hectares else 0,
                "latitude": float(location.latitude) if location.latitude else 0,
                "longitude": float(location.longitude) if location.longitude else 0,
                "accuracy_meters": float(location.accuracy_meters) if location.accuracy_meters else None,
                "address": location.address,
                "city": location.city,
                "state_province": location.state_province,
                "country": location.country,
                "certifications": location.certifications or [],
                "compliance_data": location.compliance_data or {},
                "farm_contact_info": location.farm_contact_info or {},
                "specialization": location.specialization,
                "established_year": location.established_year,
                "compliance_status": location.compliance_status
            }
            farms.append(farm_data)
        
        logger.info(
            "Farm locations retrieved",
            company_id=str(current_user.company_id),
            farm_count=len(farms),
            user_id=str(current_user.id)
        )
        
        return {
            "farms": farms,
            "total": len(farms),
            "company_id": str(current_user.company_id)
        }
        
    except Exception as e:
        logger.error(
            "Error retrieving farm locations",
            error=str(e),
            company_id=str(current_user.company_id),
            user_id=str(current_user.id)
        )
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve farm locations"
        )


@router.post("/declare", response_model=BatchResponse)
def declare_harvest(
    harvest_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Declare a new harvest event and create a batch with origin data.
    
    This is the CORRECT way to capture origin data - as part of a harvest
    declaration that creates a batch, not as part of a Purchase Order.
    
    The harvest declaration creates a batch with:
    - batch_type = "harvest"
    - origin_data = all the harvest-specific information
    - location_coordinates = GPS coordinates from harvest
    - quality_metrics = quality parameters from harvest
    
    This batch can later be sold via Purchase Orders, and the origin data
    is automatically inherited by the PO batch.
    """
    batch_service = BatchTrackingService(db)
    
    try:
        # Extract harvest data
        selected_farm_id = harvest_data.get('selected_farm_id', '')
        quality_params = harvest_data.get('quality_parameters', {})
        
        # Get farm details from database
        from app.models.location import Location
        farm_location = db.query(Location).filter(
            Location.id == selected_farm_id,
            Location.is_farm_location == True
        ).first()
        
        if not farm_location:
            raise HTTPException(
                status_code=400,
                detail="Selected farm not found or not a valid farm location"
            )
        
        # Create batch data for harvest declaration
        batch_data = BatchCreate(
            batch_id=harvest_data.get('batch_number', ''),
            batch_type=BatchType.HARVEST,  # This is a harvest batch
            product_id=UUID(harvest_data.get('product_id', '')),  # Should be passed from frontend
            quantity=harvest_data.get('quantity', 1000),  # Should be passed from frontend
            unit=harvest_data.get('unit', 'KGM'),
            production_date=datetime.strptime(harvest_data.get('harvest_date', ''), '%Y-%m-%d').date(),
            expiry_date=None,  # Will be set based on product shelf life
            
            # Location from selected farm
            location_name=farm_location.name,
            location_coordinates={
                'latitude': float(farm_location.latitude) if farm_location.latitude else 0,
                'longitude': float(farm_location.longitude) if farm_location.longitude else 0,
                'accuracy_meters': float(farm_location.accuracy_meters) if farm_location.accuracy_meters else None
            },
            facility_code=farm_location.registration_number,
            
            # Quality metrics from harvest
            quality_metrics=quality_params,
            
            # Origin data - this is the key part!
            origin_data={
                'harvest_date': harvest_data.get('harvest_date'),
                'farm_information': {
                    'farm_id': farm_location.registration_number,
                    'farm_name': farm_location.name,
                    'farm_type': farm_location.farm_type,
                    'farm_size_hectares': float(farm_location.farm_size_hectares) if farm_location.farm_size_hectares else 0,
                    'established_year': farm_location.established_year,
                    'specialization': farm_location.specialization,
                    'farm_owner_name': farm_location.farm_owner_name,
                    'farm_contact_info': farm_location.farm_contact_info
                },
                'geographic_coordinates': {
                    'latitude': float(farm_location.latitude) if farm_location.latitude else 0,
                    'longitude': float(farm_location.longitude) if farm_location.longitude else 0,
                    'accuracy_meters': float(farm_location.accuracy_meters) if farm_location.accuracy_meters else None,
                    'elevation_meters': float(farm_location.elevation_meters) if farm_location.elevation_meters else None
                },
                'location_details': {
                    'address': farm_location.address,
                    'city': farm_location.city,
                    'state_province': farm_location.state_province,
                    'country': farm_location.country,
                    'postal_code': farm_location.postal_code
                },
                'certifications': farm_location.certifications or [],
                'compliance_data': farm_location.compliance_data or {},
                'processing_notes': harvest_data.get('processing_notes', ''),
                'declared_at': datetime.utcnow().isoformat(),
                'declared_by_user_id': str(current_user.id)
            },
            certifications=farm_location.certifications or [],
            
            # Metadata
            batch_metadata={
                'harvest_declaration': True,
                'declared_by': current_user.email,
                'declaration_source': 'harvest_api',
                'farm_location_id': str(farm_location.id),
                'farm_type': farm_location.farm_type,
                'compliance_status': farm_location.compliance_status
            }
        )
        
        # Create the harvest batch
        batch = batch_service.create_batch(
            batch_data=batch_data,
            company_id=current_user.company_id,
            user_id=current_user.id
        )
        
        logger.info(
            "Harvest batch created from declaration",
            batch_id=str(batch.id),
            batch_number=batch.batch_id,
            company_id=str(current_user.company_id),
            user_id=str(current_user.id),
            harvest_date=harvest_data.get('harvest_date'),
            farm_name=farm_location.name,
            farm_id=farm_location.registration_number,
            farm_location_id=str(farm_location.id)
        )
        
        return batch
        
    except Exception as e:
        logger.error(
            "Error creating harvest batch",
            error=str(e),
            user_id=str(current_user.id),
            company_id=str(current_user.company_id)
        )
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create harvest batch"
        )


@router.get("/batches")
def get_harvest_batches(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    product_id: Optional[UUID] = Query(None, description="Filter by product ID"),
    status: Optional[str] = Query("active", description="Filter by status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get harvest batches for the current user's company.
    
    This returns only harvest-type batches (not processing or transformation batches).
    """
    try:
        # Build query for harvest batches - filter by current user's company
        query = db.query(Batch).filter(
            Batch.batch_type == BatchType.HARVEST.value,
            Batch.company_id == current_user.company_id
        )
        
        # Filter by status if provided
        if status:
            query = query.filter(Batch.status == status)
            
        # Filter by product if provided
        if product_id:
            query = query.filter(Batch.product_id == product_id)
        
        # Get total count before pagination
        total = query.count()
        
        # Apply pagination and ordering
        batches = query.order_by(Batch.created_at.desc()).offset((page - 1) * per_page).limit(per_page).all()
        
        # Convert to proper response format
        batch_responses = []
        for batch in batches:
            batch_response = {
                "id": batch.id,
                "batch_id": batch.batch_id,
                "batch_type": batch.batch_type,
                "company_id": batch.company_id,
                "product_id": batch.product_id,
                "quantity": float(batch.quantity) if batch.quantity else 0,
                "unit": batch.unit or "N/A",
                "production_date": batch.production_date.isoformat() if batch.production_date else None,
                "expiry_date": batch.expiry_date.isoformat() if batch.expiry_date else None,
                "status": batch.status,
                "location_name": batch.location_name,
                "location_coordinates": batch.location_coordinates,
                "facility_code": batch.facility_code,
                "quality_metrics": batch.quality_metrics,
                "processing_method": batch.processing_method,
                "storage_conditions": batch.storage_conditions,
                "transportation_method": batch.transportation_method,
                "transformation_id": batch.transformation_id,
                "parent_batch_ids": batch.parent_batch_ids,
                "origin_data": batch.origin_data,
                "certifications": batch.certifications or [],
                "source_purchase_order_id": batch.source_purchase_order_id,
                "created_at": batch.created_at.isoformat() if batch.created_at else None,
                "updated_at": batch.updated_at.isoformat() if batch.updated_at else None,
                "created_by_user_id": batch.created_by_user_id,
                "company_name": getattr(batch, 'company_name', None),
                "product_name": getattr(batch, 'product_name', None),
                "batch_metadata": batch.batch_metadata
            }
            batch_responses.append(batch_response)
        
        return {
            "batches": batch_responses,
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": (total + per_page - 1) // per_page
        }
        
    except Exception as e:
        logger.error(
            "Error fetching harvest batches",
            error=str(e),
            user_id=str(current_user.id),
            company_id=str(current_user.company_id)
        )
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch harvest batches"
        )


@router.get("/batches/{batch_id}", response_model=BatchResponse)
def get_harvest_batch(
    batch_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific harvest batch by ID.
    """
    batch_service = BatchTrackingService(db)
    
    try:
        batch = batch_service.get_batch_by_id(batch_id)
        
        if not batch:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Harvest batch not found"
            )
        
        # Check if user has access to this batch
        if batch.company_id != current_user.company_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this harvest batch"
            )
        
        # Verify this is a harvest batch
        if batch.batch_type != BatchType.HARVEST.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Batch is not a harvest batch"
            )
        
        return batch
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error fetching harvest batch",
            error=str(e),
            batch_id=str(batch_id),
            user_id=str(current_user.id)
        )
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch harvest batch"
        )


@router.get("/batches/{batch_id}/traceability")
def get_harvest_traceability(
    batch_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get traceability information for a harvest batch.
    
    This shows the complete traceability chain from this harvest batch
    through any transformations and Purchase Orders.
    """
    batch_service = BatchTrackingService(db)
    
    try:
        # Get the harvest batch
        batch = batch_service.get_batch_by_id(batch_id)
        
        if not batch:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Harvest batch not found"
            )
        
        # Check access
        if batch.company_id != current_user.company_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this harvest batch"
            )
        
        # Get traceability chain
        traceability = batch_service.get_batch_traceability(batch_id)
        
        return {
            'batch_id': str(batch_id),
            'batch_identifier': batch.batch_id,
            'traceability_chain': traceability,
            'origin_data': batch.origin_data,
            'created_at': batch.created_at,
            'harvest_date': batch.origin_data.get('harvest_date') if batch.origin_data else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error fetching harvest traceability",
            error=str(e),
            batch_id=str(batch_id),
            user_id=str(current_user.id)
        )
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch harvest traceability"
        )

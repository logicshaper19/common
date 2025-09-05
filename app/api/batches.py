"""
Batch tracking API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.services.batch import BatchTrackingService
from app.schemas.batch import (
    BatchCreate,
    BatchUpdate,
    BatchResponse,
    BatchTransactionCreate,
    BatchTransactionResponse,
    BatchRelationshipCreate,
    BatchRelationshipResponse,
    BatchListResponse,
    BatchType,
    BatchStatus,
    TransactionType
)
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/batches", tags=["batches"])


@router.post("/", response_model=BatchResponse)
def create_batch(
    batch_data: BatchCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new batch for tracking harvest, processing, or transformation.
    
    This endpoint allows companies to create batches for different stages
    of production:
    - Harvest batches: For raw materials from farms/plantations
    - Processing batches: For materials processed at mills/facilities
    - Transformation batches: For refined or transformed products
    
    Each batch includes traceability information, quality metrics,
    and location data for comprehensive supply chain tracking.
    """
    batch_service = BatchTrackingService(db)
    
    batch = batch_service.create_batch(
        batch_data,
        current_user.company_id,
        current_user.id
    )
    
    # Convert to response format
    response = BatchResponse(
        id=batch.id,
        batch_id=batch.batch_id,
        batch_type=BatchType(batch.batch_type),
        company_id=batch.company_id,
        product_id=batch.product_id,
        quantity=batch.quantity,
        unit=batch.unit,
        production_date=batch.production_date,
        expiry_date=batch.expiry_date,
        status=BatchStatus(batch.status),
        location_name=batch.location_name,
        location_coordinates=batch.location_coordinates,
        facility_code=batch.facility_code,
        quality_metrics=batch.quality_metrics,
        processing_method=batch.processing_method,
        storage_conditions=batch.storage_conditions,
        transportation_method=batch.transportation_method,
        transformation_id=batch.transformation_id,
        parent_batch_ids=batch.parent_batch_ids,
        origin_data=batch.origin_data,
        certifications=batch.certifications,
        created_at=batch.created_at,
        updated_at=batch.updated_at,
        created_by_user_id=batch.created_by_user_id,
        batch_metadata=batch.batch_metadata
    )
    
    logger.info(
        "Batch created via API",
        batch_id=batch.batch_id,
        batch_uuid=str(batch.id),
        user_id=str(current_user.id),
        company_id=str(current_user.company_id)
    )
    
    return response


@router.get("/", response_model=BatchListResponse)
def list_batches(
    batch_type: Optional[BatchType] = Query(None, description="Filter by batch type"),
    status: Optional[BatchStatus] = Query(None, description="Filter by status"),
    product_id: Optional[UUID] = Query(None, description="Filter by product"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List batches for the current user's company.
    
    Returns batches with optional filtering by type, status, and product.
    Includes pagination for large datasets.
    """
    batch_service = BatchTrackingService(db)
    
    batches, total_count = batch_service.get_company_batches(
        current_user.company_id,
        batch_type,
        status,
        product_id,
        page,
        per_page
    )
    
    # Convert to response format
    batch_responses = []
    for batch in batches:
        response = BatchResponse(
            id=batch.id,
            batch_id=batch.batch_id,
            batch_type=BatchType(batch.batch_type),
            company_id=batch.company_id,
            product_id=batch.product_id,
            quantity=batch.quantity,
            unit=batch.unit,
            production_date=batch.production_date,
            expiry_date=batch.expiry_date,
            status=BatchStatus(batch.status),
            location_name=batch.location_name,
            location_coordinates=batch.location_coordinates,
            facility_code=batch.facility_code,
            quality_metrics=batch.quality_metrics,
            processing_method=batch.processing_method,
            storage_conditions=batch.storage_conditions,
            transportation_method=batch.transportation_method,
            transformation_id=batch.transformation_id,
            parent_batch_ids=batch.parent_batch_ids,
            origin_data=batch.origin_data,
            certifications=batch.certifications,
            created_at=batch.created_at,
            updated_at=batch.updated_at,
            created_by_user_id=batch.created_by_user_id,
            batch_metadata=batch.batch_metadata
        )
        batch_responses.append(response)
    
    total_pages = (total_count + per_page - 1) // per_page
    
    return BatchListResponse(
        batches=batch_responses,
        total=total_count,
        page=page,
        per_page=per_page,
        total_pages=total_pages
    )


@router.get("/{batch_id}", response_model=BatchResponse)
def get_batch(
    batch_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific batch by ID.
    
    Returns detailed batch information including traceability data,
    quality metrics, and location information.
    """
    batch_service = BatchTrackingService(db)
    
    batch = batch_service.get_batch_by_id(batch_id, current_user.company_id)
    
    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Batch not found or not accessible"
        )
    
    # Convert to response format
    response = BatchResponse(
        id=batch.id,
        batch_id=batch.batch_id,
        batch_type=BatchType(batch.batch_type),
        company_id=batch.company_id,
        product_id=batch.product_id,
        quantity=batch.quantity,
        unit=batch.unit,
        production_date=batch.production_date,
        expiry_date=batch.expiry_date,
        status=BatchStatus(batch.status),
        location_name=batch.location_name,
        location_coordinates=batch.location_coordinates,
        facility_code=batch.facility_code,
        quality_metrics=batch.quality_metrics,
        processing_method=batch.processing_method,
        storage_conditions=batch.storage_conditions,
        transportation_method=batch.transportation_method,
        transformation_id=batch.transformation_id,
        parent_batch_ids=batch.parent_batch_ids,
        origin_data=batch.origin_data,
        certifications=batch.certifications,
        created_at=batch.created_at,
        updated_at=batch.updated_at,
        created_by_user_id=batch.created_by_user_id,
        batch_metadata=batch.batch_metadata
    )
    
    return response


@router.put("/{batch_id}", response_model=BatchResponse)
def update_batch(
    batch_id: UUID,
    update_data: BatchUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update an existing batch.
    
    Allows updating batch quantity, status, quality metrics,
    storage conditions, and other mutable fields.
    """
    batch_service = BatchTrackingService(db)
    
    batch = batch_service.update_batch(
        batch_id,
        update_data,
        current_user.company_id,
        current_user.id
    )
    
    # Convert to response format
    response = BatchResponse(
        id=batch.id,
        batch_id=batch.batch_id,
        batch_type=BatchType(batch.batch_type),
        company_id=batch.company_id,
        product_id=batch.product_id,
        quantity=batch.quantity,
        unit=batch.unit,
        production_date=batch.production_date,
        expiry_date=batch.expiry_date,
        status=BatchStatus(batch.status),
        location_name=batch.location_name,
        location_coordinates=batch.location_coordinates,
        facility_code=batch.facility_code,
        quality_metrics=batch.quality_metrics,
        processing_method=batch.processing_method,
        storage_conditions=batch.storage_conditions,
        transportation_method=batch.transportation_method,
        transformation_id=batch.transformation_id,
        parent_batch_ids=batch.parent_batch_ids,
        origin_data=batch.origin_data,
        certifications=batch.certifications,
        created_at=batch.created_at,
        updated_at=batch.updated_at,
        created_by_user_id=batch.created_by_user_id,
        batch_metadata=batch.batch_metadata
    )
    
    logger.info(
        "Batch updated via API",
        batch_id=str(batch_id),
        batch_identifier=batch.batch_id,
        user_id=str(current_user.id)
    )
    
    return response


@router.post("/transactions", response_model=BatchTransactionResponse)
def create_batch_transaction(
    transaction_data: BatchTransactionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a batch transaction for tracking batch movements and transformations.
    
    Batch transactions record:
    - Creation of new batches
    - Consumption of batches in production
    - Transformation between batch types
    - Transfer between locations
    - Split and merge operations
    """
    batch_service = BatchTrackingService(db)
    
    transaction = batch_service.create_batch_transaction(
        transaction_data,
        current_user.company_id,
        current_user.id
    )
    
    # Convert to response format
    response = BatchTransactionResponse(
        id=transaction.id,
        transaction_type=TransactionType(transaction.transaction_type),
        source_batch_id=transaction.source_batch_id,
        destination_batch_id=transaction.destination_batch_id,
        quantity_moved=transaction.quantity_moved,
        unit=transaction.unit,
        purchase_order_id=transaction.purchase_order_id,
        company_id=transaction.company_id,
        transaction_date=transaction.transaction_date,
        reference_number=transaction.reference_number,
        notes=transaction.notes,
        created_at=transaction.created_at,
        created_by_user_id=transaction.created_by_user_id,
        transaction_data=transaction.transaction_data
    )
    
    logger.info(
        "Batch transaction created via API",
        transaction_id=str(transaction.id),
        transaction_type=transaction.transaction_type,
        user_id=str(current_user.id)
    )
    
    return response


@router.post("/relationships", response_model=BatchRelationshipResponse)
def create_batch_relationship(
    relationship_data: BatchRelationshipCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a batch relationship for traceability tracking.
    
    Batch relationships establish parent-child connections between batches
    to enable full supply chain traceability. This includes:
    - Input material relationships
    - Transformation relationships
    - Split and merge relationships
    """
    batch_service = BatchTrackingService(db)
    
    relationship = batch_service.create_batch_relationship(
        relationship_data,
        current_user.company_id,
        current_user.id
    )
    
    # Convert to response format
    from app.schemas.batch import RelationshipType as BatchRelationshipType
    
    response = BatchRelationshipResponse(
        id=relationship.id,
        parent_batch_id=relationship.parent_batch_id,
        child_batch_id=relationship.child_batch_id,
        relationship_type=BatchRelationshipType(relationship.relationship_type),
        quantity_contribution=relationship.quantity_contribution,
        percentage_contribution=relationship.percentage_contribution,
        transformation_process=relationship.transformation_process,
        transformation_date=relationship.transformation_date,
        yield_percentage=relationship.yield_percentage,
        quality_impact=relationship.quality_impact,
        created_at=relationship.created_at,
        created_by_user_id=relationship.created_by_user_id
    )
    
    logger.info(
        "Batch relationship created via API",
        relationship_id=str(relationship.id),
        parent_batch_id=str(relationship.parent_batch_id),
        child_batch_id=str(relationship.child_batch_id),
        user_id=str(current_user.id)
    )
    
    return response

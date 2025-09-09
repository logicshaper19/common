"""
Batch tracking API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
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

    ⚠️  DEPRECATION WARNING: Manual batch creation for purchase orders is deprecated.
    Batches are now automatically created when purchase orders are confirmed.

    This endpoint should only be used for:
    - Processing/transformation batches
    - Harvest batches not linked to purchase orders
    - Legacy batch creation workflows

    For purchase order fulfillment, batches are automatically created with
    deterministic IDs (PO-{number}-BATCH-1) during PO confirmation.

    Each batch includes traceability information, quality metrics,
    and location data for comprehensive supply chain tracking.
    """
    batch_service = BatchTrackingService(db)

    # Check if this looks like a PO-related batch and warn about deprecation
    if (batch_data.batch_metadata and
        batch_data.batch_metadata.get('created_from_po') or
        'PO-' in batch_data.batch_id.upper()):
        logger.warning(
            "Manual batch creation for PO detected - this workflow is deprecated",
            batch_id=batch_data.batch_id,
            user_id=str(current_user.id),
            company_id=str(current_user.company_id),
            deprecation_message="Use automatic batch creation via PO confirmation instead"
        )

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


@router.get("/by-purchase-order/{purchase_order_id}", response_model=List[BatchResponse])
def get_batches_by_purchase_order(
    purchase_order_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all batches created from a specific purchase order.

    This endpoint demonstrates the critical PO-to-Batch linkage that enables
    full traceability from purchase orders to physical batches.
    """
    from app.models.batch import Batch
    from uuid import UUID

    try:
        po_uuid = UUID(purchase_order_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid purchase order ID format"
        )

    # Query batches linked to this PO
    batches = db.query(Batch).filter(
        Batch.source_purchase_order_id == po_uuid
    ).all()

    # Convert to response format
    response_batches = []
    for batch in batches:
        response_batches.append(BatchResponse(
            id=batch.id,
            batch_id=batch.batch_id,
            batch_type=batch.batch_type,
            company_id=batch.company_id,
            product_id=batch.product_id,
            quantity=batch.quantity,
            unit=batch.unit,
            production_date=batch.production_date,
            expiry_date=batch.expiry_date,
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
            status=batch.status,
            created_at=batch.created_at,
            updated_at=batch.updated_at,
            created_by_user_id=batch.created_by_user_id,
            batch_metadata=batch.batch_metadata,
            source_purchase_order_id=batch.source_purchase_order_id  # Critical linkage field
        ))

    logger.info(
        "Batches retrieved by purchase order",
        po_id=purchase_order_id,
        batches_found=len(response_batches),
        user_id=str(current_user.id)
    )

    return response_batches


@router.get("/companies/{company_id}/inventory", response_model=List[BatchResponse])
def get_company_inventory(
    company_id: str,
    product_id: Optional[str] = Query(None, description="Filter by product ID"),
    include_expired: bool = Query(False, description="Include expired batches"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get available inventory for a company - like browsing warehouse shelves.

    This endpoint returns all batches with available quantity (> 0) for a company,
    making it feel like a manager selecting physical items from warehouse shelves
    to fulfill purchase orders.

    Features:
    - Only shows batches with quantity > 0 (available inventory)
    - Optional product filtering for PO confirmation workflows
    - Excludes expired batches by default
    - Sorted by expiry date (FIFO - First In, First Out)
    """
    from app.models.batch import Batch
    from app.models.product import Product
    from app.models.company import Company
    from uuid import UUID
    from datetime import date

    try:
        company_uuid = UUID(company_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid company ID format"
        )

    # Verify user has access to this company's inventory
    if current_user.company_id != company_uuid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own company's inventory"
        )

    # Build query for available inventory
    query = db.query(Batch).filter(
        Batch.company_id == company_uuid,
        Batch.quantity > 0,  # Only available inventory
        Batch.status == 'active'  # Only active batches
    )

    # Filter by product if specified
    if product_id:
        try:
            product_uuid = UUID(product_id)
            query = query.filter(Batch.product_id == product_uuid)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid product ID format"
            )

    # Exclude expired batches unless explicitly requested
    if not include_expired:
        today = date.today()
        query = query.filter(
            or_(Batch.expiry_date.is_(None), Batch.expiry_date >= today)
        )

    # Sort by expiry date (FIFO - First In, First Out)
    # Batches without expiry date come last
    query = query.order_by(
        Batch.expiry_date.asc().nullslast(),
        Batch.production_date.asc()
    )

    batches = query.all()

    # Convert to response format with enhanced inventory information
    inventory_batches = []
    for batch in batches:
        # Calculate days until expiry for UI display
        days_until_expiry = None
        if batch.expiry_date:
            days_until_expiry = (batch.expiry_date - date.today()).days

        # Enhanced batch metadata for inventory display
        enhanced_metadata = batch.batch_metadata or {}
        enhanced_metadata.update({
            "days_until_expiry": days_until_expiry,
            "is_expiring_soon": days_until_expiry is not None and days_until_expiry <= 30,
            "inventory_status": "available",
            "fifo_priority": len(inventory_batches) + 1  # FIFO ordering priority
        })

        inventory_batches.append(BatchResponse(
            id=batch.id,
            batch_id=batch.batch_id,
            batch_type=batch.batch_type,
            company_id=batch.company_id,
            product_id=batch.product_id,
            quantity=batch.quantity,
            unit=batch.unit,
            production_date=batch.production_date,
            expiry_date=batch.expiry_date,
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
            status=batch.status,
            created_at=batch.created_at,
            updated_at=batch.updated_at,
            created_by_user_id=batch.created_by_user_id,
            batch_metadata=enhanced_metadata,
            source_purchase_order_id=batch.source_purchase_order_id
        ))

    logger.info(
        "Company inventory retrieved",
        company_id=company_id,
        product_id=product_id,
        batches_found=len(inventory_batches),
        total_quantity=sum(b.quantity for b in inventory_batches),
        user_id=str(current_user.id)
    )

    return inventory_batches

"""
Product management API endpoints.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
import math

from app.core.database import get_db
from app.core.auth import require_admin, get_current_user, CurrentUser
from app.schemas.product import (
    ProductCreate,
    ProductUpdate,
    ProductResponse,
    ProductListResponse,
    ProductFilter,
    CompositionValidation,
    CompositionValidationResponse,
    ProductCategory
)
from app.services.product import ProductService
from app.services.seed_data import SeedDataService
from app.core.logging import get_logger
from app.core.response_wrapper import standardize_response, standardize_list_response, ResponseBuilder
from app.core.response_models import StandardResponse, PaginatedResponse, ResponseStatus

logger = get_logger(__name__)
router = APIRouter()


@router.post("/")
@standardize_response(success_message="Product created successfully")
async def create_product(
    product_data: ProductCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_admin)
) -> StandardResponse:
    """
    Create a new product (admin only).

    Args:
        product_data: Product creation data
        db: Database session
        current_user: Current authenticated admin user

    Returns:
        StandardResponse: Created product information
    """
    product_service = ProductService(db)

    product = product_service.create_product(product_data)

    logger.info(
        "Product created by admin",
        product_id=str(product.id),
        common_product_id=product.common_product_id,
        admin_user_id=str(current_user.id)
    )

    # Convert to standardized format
    product_data = {
        "id": str(product.id),
        "common_product_id": product.common_product_id,
        "name": product.name,
        "description": product.description,
        "category": product.category,
        "can_have_composition": product.can_have_composition,
        "material_breakdown": product.material_breakdown,
        "default_unit": product.default_unit,
        "hs_code": product.hs_code,
        "origin_data_requirements": product.origin_data_requirements,
        "created_at": product.created_at.isoformat(),
        "updated_at": product.updated_at.isoformat()
    }

    return ResponseBuilder.success(
        data=product_data,
        message="Product created successfully"
    )


@router.get("/")
@standardize_list_response(success_message="Products retrieved successfully")
async def list_products(
    category: ProductCategory = Query(None, description="Filter by product category"),
    can_have_composition: bool = Query(None, description="Filter by composition capability"),
    search: str = Query(None, description="Search in name, description, or product ID"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
) -> PaginatedResponse:
    """
    List products with filtering and pagination.
    
    Args:
        category: Filter by product category
        can_have_composition: Filter by composition capability
        search: Search term
        page: Page number
        per_page: Items per page
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Paginated list of products
    """
    product_service = ProductService(db)
    
    filters = ProductFilter(
        category=category,
        can_have_composition=can_have_composition,
        search=search,
        page=page,
        per_page=per_page
    )
    
    products, total_count = product_service.list_products(filters)
    total_pages = math.ceil(total_count / per_page)
    
    logger.info(
        "Products listed",
        user_id=str(current_user.id),
        total_count=total_count,
        page=page,
        per_page=per_page
    )
    
    return ProductListResponse(
        products=products,
        total=total_count,
        page=page,
        per_page=per_page,
        total_pages=total_pages
    )


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Get product by ID.
    
    Args:
        product_id: Product UUID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Product information
        
    Raises:
        HTTPException: If product not found
    """
    product_service = ProductService(db)
    
    product = product_service.get_product_by_id(product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    return product


@router.get("/common/{common_product_id}", response_model=ProductResponse)
async def get_product_by_common_id(
    common_product_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Get product by common product ID.
    
    Args:
        common_product_id: Common product identifier
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Product information
        
    Raises:
        HTTPException: If product not found
    """
    product_service = ProductService(db)
    
    product = product_service.get_product_by_common_id(common_product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    return product


@router.post("/batch-import")
async def batch_import_products(
    products_data: List[ProductCreate],
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_admin)
) -> StandardResponse:
    """
    Batch import products with enhanced response format demonstration.

    This endpoint demonstrates the new partial_success response type
    for operations that may partially succeed.
    """
    product_service = ProductService(db)

    results = {
        "total_submitted": len(products_data),
        "successful": 0,
        "failed": 0,
        "errors": [],
        "warnings": [],
        "created_products": []
    }

    for i, product_data in enumerate(products_data):
        try:
            # Validate product data
            if not product_data.name or len(product_data.name.strip()) == 0:
                results["errors"].append(f"Product {i+1}: Name is required")
                results["failed"] += 1
                continue

            # Create product
            product = product_service.create_product(product_data)
            results["successful"] += 1
            results["created_products"].append({
                "id": str(product.id),
                "common_product_id": product.common_product_id,
                "name": product.name
            })

        except Exception as e:
            results["errors"].append(f"Product {i+1}: {str(e)}")
            results["failed"] += 1

    # Determine response type based on results
    if results["failed"] == 0:
        # All successful
        return ResponseBuilder.success(
            data={
                "summary": {
                    "total_submitted": results["total_submitted"],
                    "successful": results["successful"],
                    "failed": results["failed"]
                },
                "created_products": results["created_products"]
            },
            message=f"Successfully imported {results['successful']} products",
            api_version="v1"
        )
    elif results["successful"] == 0:
        # All failed
        return ResponseBuilder.error(
            message="Batch import failed - no products were created",
            errors=results["errors"],
            error_code="BATCH_IMPORT_FAILED"
        )
    else:
        # Partial success - demonstrates new response type!
        return ResponseBuilder.partial_success(
            data={
                "summary": {
                    "total_submitted": results["total_submitted"],
                    "successful": results["successful"],
                    "failed": results["failed"]
                },
                "created_products": results["created_products"]
            },
            message=f"Batch import partially completed: {results['successful']} successful, {results['failed']} failed",
            warnings=results["warnings"],
            errors=results["errors"],
            api_version="v1"
        )


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: str,
    product_data: ProductUpdate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_admin)
):
    """
    Update a product (admin only).
    
    Args:
        product_id: Product UUID
        product_data: Product update data
        db: Database session
        current_user: Current authenticated admin user
        
    Returns:
        Updated product information
    """
    product_service = ProductService(db)
    
    product = product_service.update_product(product_id, product_data)
    
    logger.info(
        "Product updated by admin",
        product_id=str(product.id),
        admin_user_id=str(current_user.id)
    )
    
    return product


@router.delete("/{product_id}")
async def delete_product(
    product_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_admin)
):
    """
    Delete a product (admin only).
    
    Args:
        product_id: Product UUID
        db: Database session
        current_user: Current authenticated admin user
        
    Returns:
        Success message
    """
    product_service = ProductService(db)
    
    product_service.delete_product(product_id)
    
    logger.info(
        "Product deleted by admin",
        product_id=product_id,
        admin_user_id=str(current_user.id)
    )
    
    return {"message": "Product deleted successfully"}


@router.post("/validate-composition", response_model=CompositionValidationResponse)
async def validate_composition(
    validation_data: CompositionValidation,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Validate product composition against defined rules.
    
    Args:
        validation_data: Composition validation request
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Validation response with errors and warnings
    """
    product_service = ProductService(db)
    
    result = product_service.validate_composition(validation_data)
    
    logger.info(
        "Composition validation performed",
        product_id=str(validation_data.product_id),
        user_id=str(current_user.id),
        is_valid=result.is_valid
    )
    
    return result


@router.post("/seed", response_model=dict)
async def seed_products(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_admin)
):
    """
    Seed initial products (admin only).

    This endpoint allows admins to manually seed the database with
    initial palm oil products if they haven't been created yet.
    """
    try:
        seed_service = SeedDataService(db)
        seed_service.seed_palm_oil_products()

        # Count products after seeding
        product_service = ProductService(db)
        filters = ProductFilter(page=1, per_page=1000)
        products, total_count = product_service.list_products(filters)

        logger.info(
            "Products seeded by admin",
            admin_user_id=str(current_user.id),
            total_products=total_count
        )

        return {
            "message": "Products seeded successfully",
            "total_products": total_count
        }

    except Exception as e:
        logger.error("Failed to seed products", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to seed products"
        )


@router.get("/count", response_model=dict)
async def get_products_count(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Get the total count of products in the database.

    This endpoint helps check if products have been seeded.
    """
    try:
        product_service = ProductService(db)
        filters = ProductFilter(page=1, per_page=1)
        _, total_count = product_service.list_products(filters)

        return {
            "total_products": total_count,
            "has_products": total_count > 0
        }

    except Exception as e:
        logger.error("Failed to get products count", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get products count"
        )

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

logger = get_logger(__name__)
router = APIRouter()


@router.post("/", response_model=ProductResponse)
async def create_product(
    product_data: ProductCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_admin)
):
    """
    Create a new product (admin only).
    
    Args:
        product_data: Product creation data
        db: Database session
        current_user: Current authenticated admin user
        
    Returns:
        Created product information
    """
    product_service = ProductService(db)
    
    product = product_service.create_product(product_data)
    
    logger.info(
        "Product created by admin",
        product_id=str(product.id),
        common_product_id=product.common_product_id,
        admin_user_id=str(current_user.id)
    )
    
    return product


@router.get("/", response_model=ProductListResponse)
async def list_products(
    category: ProductCategory = Query(None, description="Filter by product category"),
    can_have_composition: bool = Query(None, description="Filter by composition capability"),
    search: str = Query(None, description="Search in name, description, or product ID"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
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

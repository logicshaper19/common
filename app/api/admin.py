"""
Admin API endpoints for super admin functionality.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.core.auth import require_admin, CurrentUser
from app.schemas.auth import CompanyCreate, CompanyResponse
from app.schemas.admin import (
    AdminUserResponse,
    AdminUserCreate,
    AdminUserUpdate,
    AdminCompanyResponse,
    AdminCompanyCreate,
    AdminCompanyUpdate,
    AdminUserFilter,
    AdminCompanyFilter,
    PaginatedResponse
)
from app.schemas.product import (
    ProductCreate,
    ProductUpdate,
    ProductResponse,
    ProductFilter
)
from app.schemas.purchase_order import (
    PurchaseOrderResponse,
    PurchaseOrderFilter
)
from app.services.admin import AdminService
from app.services.product import ProductService
from app.services.purchase_order import PurchaseOrderService
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


# Company Management Endpoints
@router.post("/companies", response_model=AdminCompanyResponse)
async def create_company(
    company_data: AdminCompanyCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_admin)
):
    """
    Create a new company (super admin only).
    
    Args:
        company_data: Company creation data
        db: Database session
        current_user: Current authenticated admin user
        
    Returns:
        Created company information
    """
    admin_service = AdminService(db)
    
    company = admin_service.create_company(company_data)
    
    logger.info(
        "Company created by super admin",
        company_id=str(company.id),
        company_name=company.name,
        admin_user_id=str(current_user.id)
    )
    
    return company


@router.get("/companies", response_model=PaginatedResponse[AdminCompanyResponse])
async def get_companies(
    page: int = 1,
    per_page: int = 20,
    search: str = None,
    company_type: str = None,
    subscription_tier: str = None,
    compliance_status: str = None,
    is_active: bool = None,
    is_verified: bool = None,
    country: str = None,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_admin)
):
    """
    Get paginated list of companies with filtering (super admin only).
    """
    admin_service = AdminService(db)
    
    filters = AdminCompanyFilter(
        page=page,
        per_page=per_page,
        search=search,
        company_type=company_type,
        subscription_tier=subscription_tier,
        compliance_status=compliance_status,
        is_active=is_active,
        is_verified=is_verified,
        country=country
    )
    
    return admin_service.get_companies(filters)


@router.get("/companies/{company_id}", response_model=AdminCompanyResponse)
async def get_company(
    company_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_admin)
):
    """
    Get company by ID (super admin only).
    """
    admin_service = AdminService(db)
    
    company = admin_service.get_company(company_id)
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )
    
    return company


@router.put("/companies/{company_id}", response_model=AdminCompanyResponse)
async def update_company(
    company_id: str,
    company_data: AdminCompanyUpdate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_admin)
):
    """
    Update company (super admin only).
    """
    admin_service = AdminService(db)
    
    company = admin_service.update_company(company_id, company_data)
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )
    
    logger.info(
        "Company updated by super admin",
        company_id=str(company.id),
        admin_user_id=str(current_user.id)
    )
    
    return company


# User Management Endpoints
@router.post("/users", response_model=AdminUserResponse)
async def create_user(
    user_data: AdminUserCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_admin)
):
    """
    Create a new user (super admin only).
    """
    admin_service = AdminService(db)
    
    user = admin_service.create_user(user_data)
    
    logger.info(
        "User created by super admin",
        user_id=str(user.id),
        user_email=user.email,
        admin_user_id=str(current_user.id)
    )
    
    return user


@router.get("/users", response_model=PaginatedResponse[AdminUserResponse])
async def get_users(
    page: int = 1,
    per_page: int = 20,
    search: str = None,
    role: str = None,
    company_id: str = None,
    is_active: bool = None,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_admin)
):
    """
    Get paginated list of users with filtering (super admin only).
    """
    admin_service = AdminService(db)
    
    filters = AdminUserFilter(
        page=page,
        per_page=per_page,
        search=search,
        role=role,
        company_id=company_id,
        is_active=is_active
    )
    
    return admin_service.get_users(filters)


@router.get("/users/{user_id}", response_model=AdminUserResponse)
async def get_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_admin)
):
    """
    Get user by ID (super admin only).
    """
    admin_service = AdminService(db)
    
    user = admin_service.get_user(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user


@router.put("/users/{user_id}", response_model=AdminUserResponse)
async def update_user(
    user_id: str,
    user_data: AdminUserUpdate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_admin)
):
    """
    Update user (super admin only).
    """
    admin_service = AdminService(db)
    
    user = admin_service.update_user(user_id, user_data)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    logger.info(
        "User updated by super admin",
        user_id=str(user.id),
        admin_user_id=str(current_user.id)
    )
    
    return user


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_admin)
):
    """
    Delete user (super admin only).
    """
    admin_service = AdminService(db)
    
    success = admin_service.delete_user(user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    logger.info(
        "User deleted by super admin",
        user_id=user_id,
        admin_user_id=str(current_user.id)
    )
    
    return {"message": "User deleted successfully"}


# Product Management Endpoints
@router.get("/products", response_model=PaginatedResponse[ProductResponse])
async def get_products(
    page: int = 1,
    per_page: int = 20,
    search: str = None,
    category: str = None,
    can_have_composition: bool = None,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_admin)
):
    """
    Get paginated list of products with filtering (admin only).
    """
    product_service = ProductService(db)

    filters = ProductFilter(
        page=page,
        per_page=per_page,
        search=search,
        category=category,
        can_have_composition=can_have_composition
    )

    products, total_count = product_service.list_products(filters)
    total_pages = (total_count + per_page - 1) // per_page

    return PaginatedResponse(
        data=products,
        total=total_count,
        page=page,
        per_page=per_page,
        total_pages=total_pages
    )


@router.get("/products/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_admin)
):
    """
    Get product by ID (admin only).
    """
    product_service = ProductService(db)

    product = product_service.get_product_by_id(product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    return product


@router.post("/products", response_model=ProductResponse)
async def create_product(
    product_data: ProductCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_admin)
):
    """
    Create a new product (admin only).
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


@router.put("/products/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: str,
    product_data: ProductUpdate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_admin)
):
    """
    Update a product (admin only).
    """
    product_service = ProductService(db)

    product = product_service.update_product(product_id, product_data)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    logger.info(
        "Product updated by admin",
        product_id=str(product.id),
        admin_user_id=str(current_user.id)
    )

    return product


@router.delete("/products/{product_id}")
async def delete_product(
    product_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_admin)
):
    """
    Delete a product (admin only).
    """
    product_service = ProductService(db)

    success = product_service.delete_product(product_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    logger.info(
        "Product deleted by admin",
        product_id=product_id,
        admin_user_id=str(current_user.id)
    )

    return {"message": "Product deleted successfully"}


# Purchase Order Management Endpoints (Admin View Only)
@router.get("/purchase-orders", response_model=PaginatedResponse[PurchaseOrderResponse])
async def get_purchase_orders(
    page: int = 1,
    per_page: int = 20,
    search: str = None,
    status: str = None,
    buyer_company_id: str = None,
    seller_company_id: str = None,
    product_id: str = None,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_admin)
):
    """
    Get paginated list of all purchase orders (admin only).
    Super admin can view all purchase orders across all companies.
    """
    purchase_order_service = PurchaseOrderService(db)

    # Create filter object
    filters = PurchaseOrderFilter(
        page=page,
        per_page=per_page,
        search=search,
        status=status,
        buyer_company_id=buyer_company_id,
        seller_company_id=seller_company_id,
        product_id=product_id
    )

    # Get all purchase orders (admin has access to all)
    purchase_orders, total_count = purchase_order_service.list_purchase_orders_admin(filters)
    total_pages = (total_count + per_page - 1) // per_page

    logger.info(
        "Purchase orders retrieved by admin",
        total_count=total_count,
        admin_user_id=str(current_user.id)
    )

    return PaginatedResponse(
        data=purchase_orders,
        total=total_count,
        page=page,
        per_page=per_page,
        total_pages=total_pages
    )


@router.get("/purchase-orders/{purchase_order_id}", response_model=PurchaseOrderResponse)
async def get_purchase_order(
    purchase_order_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_admin)
):
    """
    Get purchase order by ID (admin only).
    Super admin can view any purchase order.
    """
    purchase_order_service = PurchaseOrderService(db)

    purchase_order = purchase_order_service.get_purchase_order_by_id(purchase_order_id)
    if not purchase_order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase order not found"
        )

    logger.info(
        "Purchase order viewed by admin",
        po_id=purchase_order_id,
        admin_user_id=str(current_user.id)
    )

    return purchase_order


@router.delete("/purchase-orders/{purchase_order_id}")
async def delete_purchase_order(
    purchase_order_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_admin)
):
    """
    Delete a purchase order (admin only).
    Super admin can delete any purchase order for administrative purposes.
    """
    purchase_order_service = PurchaseOrderService(db)

    success = purchase_order_service.delete_purchase_order_admin(purchase_order_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase order not found"
        )

    logger.info(
        "Purchase order deleted by admin",
        po_id=purchase_order_id,
        admin_user_id=str(current_user.id)
    )

    return {"message": "Purchase order deleted successfully"}

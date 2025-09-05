"""
Authentication API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import get_current_user, require_admin, CurrentUser
from app.schemas.auth import (
    UserLogin, 
    UserRegister, 
    UserCreate, 
    Token, 
    UserResponse, 
    UserWithCompany,
    CompanyResponse
)
from app.services.auth import AuthService
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.post("/login", response_model=Token)
async def login(
    user_credentials: UserLogin,
    db: Session = Depends(get_db)
):
    """
    Authenticate user and return access token.
    
    Args:
        user_credentials: User login credentials
        db: Database session
        
    Returns:
        JWT access token
        
    Raises:
        HTTPException: If authentication fails
    """
    auth_service = AuthService(db)
    
    # Authenticate user
    user = auth_service.authenticate_user(
        email=user_credentials.email,
        password=user_credentials.password
    )
    
    if not user:
        logger.warning("Login failed", email=user_credentials.email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token, expires_in = auth_service.create_access_token_for_user(user)
    
    logger.info("User logged in successfully", email=user.email, user_id=str(user.id))
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": expires_in
    }


@router.post("/register", response_model=Token)
async def register(
    user_data: UserRegister,
    db: Session = Depends(get_db)
):
    """
    Register a new user and company.
    
    Args:
        user_data: User registration data
        db: Database session
        
    Returns:
        JWT access token for the new user
    """
    auth_service = AuthService(db)
    
    # Register user and company
    user, company = auth_service.register_user_and_company(user_data)
    
    # Create access token for the new user
    access_token, expires_in = auth_service.create_access_token_for_user(user)
    
    logger.info(
        "User registered successfully", 
        email=user.email, 
        user_id=str(user.id),
        company_id=str(company.id)
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": expires_in
    }


@router.get("/me", response_model=UserWithCompany)
async def get_current_user_info(
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Get current user information.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Current user information with company details
    """
    return {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": current_user.role,
        "is_active": current_user.is_active,
        "company": {
            "id": current_user.company.id,
            "name": current_user.company.name,
            "company_type": current_user.company.company_type,
            "email": current_user.company.email
        }
    }


@router.post("/users", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_admin)
):
    """
    Create a new user (admin only).
    
    Args:
        user_data: User creation data
        db: Database session
        current_user: Current authenticated admin user
        
    Returns:
        Created user information
    """
    auth_service = AuthService(db)
    
    user = auth_service.create_user(user_data)
    
    logger.info(
        "User created by admin", 
        created_user_email=user.email,
        created_user_id=str(user.id),
        admin_user_id=str(current_user.id)
    )
    
    return user


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_admin)
):
    """
    Get user by ID (admin only).
    
    Args:
        user_id: User UUID
        db: Database session
        current_user: Current authenticated admin user
        
    Returns:
        User information
        
    Raises:
        HTTPException: If user not found
    """
    auth_service = AuthService(db)
    
    user = auth_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user


@router.delete("/users/{user_id}")
async def deactivate_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_admin)
):
    """
    Deactivate a user (admin only).
    
    Args:
        user_id: User UUID
        db: Database session
        current_user: Current authenticated admin user
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If user not found
    """
    auth_service = AuthService(db)
    
    success = auth_service.deactivate_user(user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    logger.info(
        "User deactivated by admin", 
        deactivated_user_id=user_id,
        admin_user_id=str(current_user.id)
    )
    
    return {"message": "User deactivated successfully"}

"""
Authentication dependencies and utilities.
"""
from typing import Optional
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import verify_token
from app.models.user import User
from app.models.company import Company
from app.core.logging import get_logger

logger = get_logger(__name__)

# HTTP Bearer token scheme
security = HTTPBearer()


class CurrentUser:
    """Current authenticated user information."""

    def __init__(self, user: User, company: Company):
        self.id = user.id
        self.email = user.email
        self.full_name = user.full_name
        self.role = user.role
        self.is_active = user.is_active
        self.company_id = user.company_id
        self.sector_id = user.sector_id  # Add sector_id
        self.tier_level = user.tier_level  # Add tier_level
        self.company = company
        self.user = user  # Full user object for database operations


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> CurrentUser:
    """
    Get the current authenticated user from JWT token.
    
    Args:
        credentials: HTTP Bearer credentials
        db: Database session
        
    Returns:
        Current user information
        
    Raises:
        HTTPException: If authentication fails
    """
    # Verify the token
    payload = verify_token(credentials.credentials)
    
    # Extract user ID from token
    user_id_str = payload.get("sub")
    if user_id_str is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing user ID",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        user_id = UUID(user_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID in token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user from database
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        logger.warning("User not found for token", user_id=user_id_str)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is active
    if not user.is_active:
        logger.warning("Inactive user attempted access", user_id=user_id_str)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user's company
    company = db.query(Company).filter(Company.id == user.company_id).first()

    if company is None:
        logger.error("User's company not found", user_id=user_id_str, company_id=str(user.company_id))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User company not found",
        )
    
    logger.debug("User authenticated", user_id=user_id_str, email=user.email, role=user.role)
    return CurrentUser(user=user, company=company)


async def get_current_active_user(
    current_user: CurrentUser = Depends(get_current_user)
) -> CurrentUser:
    """
    Get current active user (alias for get_current_user since we already check active status).
    
    Args:
        current_user: Current user from get_current_user
        
    Returns:
        Current active user
    """
    return current_user


def require_role(required_role: str):
    """
    Create a dependency that requires a specific role.
    
    Args:
        required_role: Required user role
        
    Returns:
        Dependency function
    """
    async def role_checker(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if current_user.role != required_role:
            logger.warning(
                "Insufficient permissions", 
                user_id=str(current_user.id), 
                user_role=current_user.role, 
                required_role=required_role
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation requires {required_role} role"
            )
        return current_user
    
    return role_checker


def require_roles(required_roles: list[str]):
    """
    Create a dependency that requires one of multiple roles.
    
    Args:
        required_roles: List of acceptable roles
        
    Returns:
        Dependency function
    """
    async def roles_checker(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if current_user.role not in required_roles:
            logger.warning(
                "Insufficient permissions", 
                user_id=str(current_user.id), 
                user_role=current_user.role, 
                required_roles=required_roles
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation requires one of: {', '.join(required_roles)}"
            )
        return current_user
    
    return roles_checker


# Common role dependencies
require_admin = require_role("admin")
require_buyer = require_role("buyer")
require_seller = require_role("seller")
require_buyer_or_seller = require_roles(["buyer", "seller"])

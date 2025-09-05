"""
Authentication service layer.
"""
from typing import Optional, Tuple
from uuid import uuid4
from datetime import timedelta

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.user import User
from app.models.company import Company
from app.schemas.auth import UserRegister, UserCreate, CompanyCreate
from app.core.security import (
    hash_password, 
    verify_password, 
    create_access_token, 
    create_user_token_data
)
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class AuthService:
    """Authentication service for user management."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """
        Authenticate a user with email and password.
        
        Args:
            email: User email
            password: Plain text password
            
        Returns:
            User object if authentication successful, None otherwise
        """
        user = self.db.query(User).filter(User.email == email).first()
        
        if not user:
            logger.warning("Authentication failed - user not found", email=email)
            return None
        
        if not user.is_active:
            logger.warning("Authentication failed - user inactive", email=email)
            return None
        
        if not verify_password(password, user.hashed_password):
            logger.warning("Authentication failed - invalid password", email=email)
            return None
        
        logger.info("User authenticated successfully", email=email, user_id=str(user.id))
        return user
    
    def create_access_token_for_user(self, user: User) -> Tuple[str, int]:
        """
        Create an access token for a user.
        
        Args:
            user: User object
            
        Returns:
            Tuple of (token, expires_in_seconds)
        """
        token_data = create_user_token_data(
            user_id=user.id,
            email=user.email,
            role=user.role,
            company_id=user.company_id
        )
        
        expires_delta = timedelta(minutes=settings.jwt_access_token_expire_minutes)
        access_token = create_access_token(data=token_data, expires_delta=expires_delta)
        
        return access_token, settings.jwt_access_token_expire_minutes * 60
    
    def register_user_and_company(self, user_data: UserRegister) -> Tuple[User, Company]:
        """
        Register a new user and company.
        
        Args:
            user_data: User registration data
            
        Returns:
            Tuple of (User, Company)
            
        Raises:
            HTTPException: If email already exists
        """
        # Check if user email already exists
        existing_user = self.db.query(User).filter(User.email == user_data.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Check if company email already exists
        existing_company = self.db.query(Company).filter(Company.email == user_data.company_email).first()
        if existing_company:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Company email already registered"
            )
        
        try:
            # Create company first
            company = Company(
                id=uuid4(),
                name=user_data.company_name,
                company_type=user_data.company_type,
                email=user_data.company_email
            )
            self.db.add(company)
            self.db.flush()  # Get the company ID
            
            # Create user
            user = User(
                id=uuid4(),
                email=user_data.email,
                hashed_password=hash_password(user_data.password),
                full_name=user_data.full_name,
                role=user_data.role,
                company_id=company.id,
                is_active=True
            )
            self.db.add(user)
            
            # Commit transaction
            self.db.commit()
            
            logger.info(
                "User and company registered successfully", 
                user_email=user_data.email,
                company_name=user_data.company_name,
                user_id=str(user.id),
                company_id=str(company.id)
            )
            
            return user, company
            
        except Exception as e:
            self.db.rollback()
            logger.error("Failed to register user and company", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user and company"
            )
    
    def create_user(self, user_data: UserCreate) -> User:
        """
        Create a new user (admin function).
        
        Args:
            user_data: User creation data
            
        Returns:
            Created user
            
        Raises:
            HTTPException: If email already exists or company not found
        """
        # Check if user email already exists
        existing_user = self.db.query(User).filter(User.email == user_data.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Check if company exists
        company = self.db.query(Company).filter(Company.id == user_data.company_id).first()
        if not company:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Company not found"
            )
        
        try:
            user = User(
                id=uuid4(),
                email=user_data.email,
                hashed_password=hash_password(user_data.password),
                full_name=user_data.full_name,
                role=user_data.role,
                company_id=user_data.company_id,
                is_active=True
            )
            self.db.add(user)
            self.db.commit()
            
            logger.info(
                "User created successfully", 
                user_email=user_data.email,
                user_id=str(user.id),
                company_id=str(user_data.company_id)
            )
            
            return user
            
        except Exception as e:
            self.db.rollback()
            logger.error("Failed to create user", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user"
            )
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email.
        
        Args:
            email: User email
            
        Returns:
            User object or None
        """
        return self.db.query(User).filter(User.email == email).first()
    
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """
        Get user by ID.
        
        Args:
            user_id: User UUID
            
        Returns:
            User object or None
        """
        return self.db.query(User).filter(User.id == user_id).first()
    
    def deactivate_user(self, user_id: str) -> bool:
        """
        Deactivate a user.
        
        Args:
            user_id: User UUID
            
        Returns:
            True if successful
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if user:
            user.is_active = False
            self.db.commit()
            logger.info("User deactivated", user_id=user_id)
            return True
        return False

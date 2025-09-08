"""
Admin service for super admin functionality.
"""
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from typing import Optional, List
from datetime import datetime
import uuid

from app.models.user import User
from app.models.company import Company
from app.schemas.admin import (
    AdminUserCreate,
    AdminUserUpdate,
    AdminUserResponse,
    AdminUserFilter,
    AdminCompanyCreate,
    AdminCompanyUpdate,
    AdminCompanyResponse,
    AdminCompanyFilter,
    PaginatedResponse,
    AdminUserBulkOperation,
    AdminCompanyBulkOperation
)
from app.core.logging import get_logger

logger = get_logger(__name__)


class AdminService:
    """Service for super admin operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    # Company Management
    def create_company(self, company_data: AdminCompanyCreate) -> AdminCompanyResponse:
        """Create a new company."""
        # Check if company with email already exists
        existing_company = self.db.query(Company).filter(Company.email == company_data.email).first()
        if existing_company:
            raise ValueError(f"Company with email {company_data.email} already exists")

        # Create company with all fields
        company = Company(
            id=uuid.uuid4(),
            name=company_data.name,
            email=company_data.email,
            company_type=company_data.company_type,
            phone=getattr(company_data, 'phone', None),
            website=getattr(company_data, 'website', None),
            country=getattr(company_data, 'country', None),
            subscription_tier=getattr(company_data, 'subscription_tier', 'free'),
            compliance_status=getattr(company_data, 'compliance_status', 'pending_review'),
            is_active=getattr(company_data, 'is_active', True),
            is_verified=getattr(company_data, 'is_verified', False),
            transparency_score=getattr(company_data, 'transparency_score', None),
            last_activity=None,
            # Industry fields
            industry_sector=getattr(company_data, 'industry_sector', None),
            industry_subcategory=getattr(company_data, 'industry_subcategory', None),
            # Address fields
            address_street=getattr(company_data, 'address_street', None),
            address_city=getattr(company_data, 'address_city', None),
            address_state=getattr(company_data, 'address_state', None),
            address_postal_code=getattr(company_data, 'address_postal_code', None),
            address_country=getattr(company_data, 'address_country', None),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        try:
            self.db.add(company)
            self.db.commit()
            self.db.refresh(company)

            logger.info(
                "Company created successfully",
                company_id=str(company.id),
                company_name=company.name,
                company_email=company.email
            )

            return self._company_to_response(company)
        except Exception as e:
            self.db.rollback()
            logger.error(
                "Failed to create company",
                error=str(e),
                company_name=company_data.name,
                company_email=company_data.email
            )
            raise
    
    def get_companies(self, filters: AdminCompanyFilter) -> PaginatedResponse[AdminCompanyResponse]:
        """Get paginated list of companies with filtering."""
        query = self.db.query(Company)
        
        # Apply filters
        if filters.search:
            search_term = f"%{filters.search}%"
            query = query.filter(
                or_(
                    Company.name.ilike(search_term),
                    Company.email.ilike(search_term)
                )
            )
        
        if filters.company_type:
            query = query.filter(Company.company_type == filters.company_type)
        
        if filters.is_active is not None:
            # Note: Company model doesn't have is_active field yet, but we'll add it
            pass
        
        if filters.country:
            query = query.filter(Company.country == filters.country)
        
        if filters.created_after:
            query = query.filter(Company.created_at >= filters.created_after)
        
        if filters.created_before:
            query = query.filter(Company.created_at <= filters.created_before)
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        offset = (filters.page - 1) * filters.per_page
        companies = query.offset(offset).limit(filters.per_page).all()
        
        # Convert to response objects
        company_responses = [self._company_to_response(company) for company in companies]
        
        return PaginatedResponse(
            data=company_responses,
            total=total,
            page=filters.page,
            per_page=filters.per_page,
            total_pages=(total + filters.per_page - 1) // filters.per_page
        )
    
    def get_company(self, company_id: str) -> Optional[AdminCompanyResponse]:
        """Get company by ID."""
        company = self.db.query(Company).filter(Company.id == company_id).first()
        if not company:
            return None
        
        return self._company_to_response(company)
    
    def update_company(self, company_id: str, company_data: AdminCompanyUpdate) -> Optional[AdminCompanyResponse]:
        """Update company."""
        company = self.db.query(Company).filter(Company.id == company_id).first()
        if not company:
            return None
        
        # Update fields
        if company_data.name is not None:
            company.name = company_data.name
        if company_data.email is not None:
            company.email = company_data.email
        if company_data.company_type is not None:
            company.company_type = company_data.company_type
        if company_data.phone is not None:
            company.phone = company_data.phone
        if company_data.website is not None:
            company.website = company_data.website
        if company_data.country is not None:
            company.country = company_data.country
        
        company.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(company)
        
        return self._company_to_response(company)
    
    def _company_to_response(self, company: Company) -> AdminCompanyResponse:
        """Convert Company model to AdminCompanyResponse."""
        # Get user count for this company
        user_count = self.db.query(func.count(User.id)).filter(User.company_id == company.id).scalar() or 0
        
        # Get PO count (when PO model is available)
        po_count = 0  # TODO: Implement when PO model is available
        
        return AdminCompanyResponse(
            id=company.id,
            name=company.name,
            email=company.email,
            company_type=company.company_type,
            phone=getattr(company, 'phone', None),
            website=getattr(company, 'website', None),
            country=getattr(company, 'country', None),
            subscription_tier=getattr(company, 'subscription_tier', 'free'),
            compliance_status=getattr(company, 'compliance_status', 'pending_review'),
            is_active=getattr(company, 'is_active', True),
            is_verified=getattr(company, 'is_verified', False),
            user_count=user_count,
            po_count=po_count,
            transparency_score=getattr(company, 'transparency_score', None),
            last_activity=getattr(company, 'last_activity', None),
            created_at=company.created_at,
            updated_at=company.updated_at,
            # Industry fields
            industry_sector=getattr(company, 'industry_sector', None),
            industry_subcategory=getattr(company, 'industry_subcategory', None),
            # Address fields
            address_street=getattr(company, 'address_street', None),
            address_city=getattr(company, 'address_city', None),
            address_state=getattr(company, 'address_state', None),
            address_postal_code=getattr(company, 'address_postal_code', None),
            address_country=getattr(company, 'address_country', None)
        )
    
    # User Management
    def create_user(self, user_data: AdminUserCreate) -> AdminUserResponse:
        """Create a new user."""
        # Check if user with email already exists
        existing_user = self.db.query(User).filter(User.email == user_data.email).first()
        if existing_user:
            raise ValueError(f"User with email {user_data.email} already exists")
        
        # Check if company exists
        company = self.db.query(Company).filter(Company.id == user_data.company_id).first()
        if not company:
            raise ValueError(f"Company with ID {user_data.company_id} not found")
        
        # Create user
        user = User(
            id=uuid.uuid4(),
            email=user_data.email,
            full_name=user_data.full_name,
            role=user_data.role,
            company_id=user_data.company_id,
            is_active=True,
            is_verified=False,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        
        return self._user_to_response(user, company.name)
    
    def get_users(self, filters: AdminUserFilter) -> PaginatedResponse[AdminUserResponse]:
        """Get paginated list of users with filtering."""
        query = self.db.query(User).join(Company)
        
        # Apply filters
        if filters.search:
            search_term = f"%{filters.search}%"
            query = query.filter(
                or_(
                    User.full_name.ilike(search_term),
                    User.email.ilike(search_term),
                    Company.name.ilike(search_term)
                )
            )
        
        if filters.role:
            query = query.filter(User.role == filters.role)
        
        if filters.company_id:
            query = query.filter(User.company_id == filters.company_id)
        
        if filters.is_active is not None:
            query = query.filter(User.is_active == filters.is_active)
        
        if filters.last_login_after:
            query = query.filter(User.last_login >= filters.last_login_after)
        
        if filters.last_login_before:
            query = query.filter(User.last_login <= filters.last_login_before)
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        offset = (filters.page - 1) * filters.per_page
        users_with_companies = query.offset(offset).limit(filters.per_page).all()
        
        # Convert to response objects
        user_responses = []
        for user in users_with_companies:
            company = self.db.query(Company).filter(Company.id == user.company_id).first()
            user_responses.append(self._user_to_response(user, company.name if company else "Unknown"))
        
        return PaginatedResponse(
            data=user_responses,
            total=total,
            page=filters.page,
            per_page=filters.per_page,
            total_pages=(total + filters.per_page - 1) // filters.per_page
        )
    
    def get_user(self, user_id: str) -> Optional[AdminUserResponse]:
        """Get user by ID."""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        
        company = self.db.query(Company).filter(Company.id == user.company_id).first()
        company_name = company.name if company else "Unknown"
        
        return self._user_to_response(user, company_name)
    
    def update_user(self, user_id: str, user_data: AdminUserUpdate) -> Optional[AdminUserResponse]:
        """Update user."""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        
        # Update fields
        if user_data.full_name is not None:
            user.full_name = user_data.full_name
        if user_data.role is not None:
            user.role = user_data.role
        if user_data.is_active is not None:
            user.is_active = user_data.is_active
        
        user.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(user)
        
        company = self.db.query(Company).filter(Company.id == user.company_id).first()
        company_name = company.name if company else "Unknown"
        
        return self._user_to_response(user, company_name)
    
    def delete_user(self, user_id: str) -> bool:
        """Delete user."""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        
        self.db.delete(user)
        self.db.commit()
        
        return True
    
    def _user_to_response(self, user: User, company_name: str) -> AdminUserResponse:
        """Convert User model to AdminUserResponse."""
        return AdminUserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            company_id=user.company_id,
            company_name=company_name,
            is_active=user.is_active,
            is_verified=user.is_verified,
            has_two_factor=getattr(user, 'has_two_factor', False),
            last_login=getattr(user, 'last_login', None),
            permissions=getattr(user, 'permissions', None),
            created_at=user.created_at,
            updated_at=user.updated_at
        )

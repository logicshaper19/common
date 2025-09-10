"""
Authentication-related Pydantic schemas.
"""
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field


class UserLogin(BaseModel):
    """User login request schema."""
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)


class UserRegister(BaseModel):
    """User registration request schema."""
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    full_name: str = Field(..., min_length=1, max_length=255)
    role: str = Field(..., pattern="^(admin|buyer|seller)$")
    company_name: str = Field(..., min_length=1, max_length=255)
    company_type: str = Field(..., pattern="^(plantation_grower|smallholder_cooperative|mill_processor|refinery_crusher|trader_aggregator|oleochemical_producer|manufacturer)$")
    company_email: EmailStr


class CompanyCreate(BaseModel):
    """Company creation schema."""
    name: str = Field(..., min_length=1, max_length=255)
    company_type: str = Field(..., pattern="^(plantation_grower|smallholder_cooperative|mill_processor|refinery_crusher|trader_aggregator|oleochemical_producer|manufacturer)$")
    email: EmailStr


class UserCreate(BaseModel):
    """User creation schema (for admin use)."""
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    full_name: str = Field(..., min_length=1, max_length=255)
    role: str = Field(..., pattern="^(admin|buyer|seller)$")
    company_id: UUID


class Token(BaseModel):
    """JWT token response schema."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class TokenPair(BaseModel):
    """JWT token pair response schema with refresh token."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    access_expires_in: int  # seconds
    refresh_expires_in: int  # seconds


class RefreshTokenRequest(BaseModel):
    """Refresh token request schema."""
    refresh_token: str


class TokenData(BaseModel):
    """Token payload data schema."""
    sub: str  # user ID
    email: str
    role: str
    company_id: str
    type: str = "access"


class UserResponse(BaseModel):
    """User response schema."""
    id: UUID
    email: str
    full_name: str
    role: str
    is_active: bool
    company_id: UUID
    
    class Config:
        from_attributes = True


class CompanyResponse(BaseModel):
    """Company response schema."""
    id: UUID
    name: str
    company_type: str
    email: str
    
    class Config:
        from_attributes = True


class UserWithCompany(BaseModel):
    """User with company information schema."""
    id: UUID
    email: str
    full_name: str
    role: str
    is_active: bool
    company: CompanyResponse
    
    class Config:
        from_attributes = True


class PasswordReset(BaseModel):
    """Password reset request schema."""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation schema."""
    token: str
    new_password: str = Field(..., min_length=8, max_length=100)


class PasswordChange(BaseModel):
    """Password change schema."""
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=100)


class PasswordValidationRequest(BaseModel):
    """Password validation request schema."""
    password: str
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company_name: Optional[str] = None


class PasswordValidationResponse(BaseModel):
    """Password validation response schema."""
    is_valid: bool
    strength: str
    score: int
    errors: List[str]
    warnings: List[str]
    suggestions: List[str]

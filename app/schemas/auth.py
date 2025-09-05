"""
Authentication-related Pydantic schemas.
"""
from typing import Optional
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
    company_type: str = Field(..., pattern="^(brand|processor|originator)$")
    company_email: EmailStr


class CompanyCreate(BaseModel):
    """Company creation schema."""
    name: str = Field(..., min_length=1, max_length=255)
    company_type: str = Field(..., pattern="^(brand|processor|originator)$")
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

"""
Gap Action Schemas
Pydantic models for gap action API requests and responses
"""
from typing import Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field


class GapActionRequest(BaseModel):
    """Schema for creating a new gap action."""
    action_type: str = Field(..., description="Type of action: request_data, contact_supplier, mark_resolved")
    target_company_id: Optional[UUID] = Field(None, description="ID of target company for the action")
    message: Optional[str] = Field(None, description="Message or notes for the action")
    
    class Config:
        json_schema_extra = {
            "example": {
                "action_type": "request_data",
                "target_company_id": "123e4567-e89b-12d3-a456-426614174000",
                "message": "Please provide mill traceability data for PO #12345"
            }
        }


class GapActionUpdate(BaseModel):
    """Schema for updating a gap action."""
    status: str = Field(..., description="New status: pending, in_progress, resolved, cancelled")
    resolution_notes: Optional[str] = Field(None, description="Notes about the resolution")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "resolved",
                "resolution_notes": "Data received and gap resolved"
            }
        }


class GapActionResponse(BaseModel):
    """Schema for gap action response."""
    id: UUID
    gap_id: str
    company_id: UUID
    action_type: str
    target_company_id: Optional[UUID] = None
    target_company_name: Optional[str] = None
    message: Optional[str] = None
    status: str
    
    # Audit fields
    created_by_user_id: UUID
    created_by_name: str
    created_at: datetime
    
    resolved_by_user_id: Optional[UUID] = None
    resolved_by_name: Optional[str] = None
    resolved_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "gap_id": "po-12345",
                "company_id": "123e4567-e89b-12d3-a456-426614174001",
                "action_type": "request_data",
                "target_company_id": "123e4567-e89b-12d3-a456-426614174002",
                "target_company_name": "Supplier ABC",
                "message": "Please provide mill traceability data",
                "status": "pending",
                "created_by_user_id": "123e4567-e89b-12d3-a456-426614174003",
                "created_by_name": "John Doe",
                "created_at": "2024-01-15T10:30:00Z",
                "resolved_by_user_id": None,
                "resolved_by_name": None,
                "resolved_at": None,
                "resolution_notes": None
            }
        }


class GapActionListResponse(BaseModel):
    """Schema for gap action list response."""
    success: bool
    actions: list[GapActionResponse]
    total_count: int
    message: str = "Gap actions retrieved successfully"
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "actions": [],
                "total_count": 0,
                "message": "Gap actions retrieved successfully"
            }
        }


class GapActionCreateResponse(BaseModel):
    """Schema for gap action creation response."""
    success: bool
    action_id: UUID
    message: str = "Gap action created successfully"
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "action_id": "123e4567-e89b-12d3-a456-426614174000",
                "message": "Gap action created successfully"
            }
        }

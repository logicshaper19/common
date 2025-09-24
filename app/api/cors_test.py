"""
CORS Test endpoint to help debug CORS issues
"""
from fastapi import APIRouter
from app.core.config import settings

router = APIRouter(prefix="/api/cors-test", tags=["CORS Test"])


@router.get("/")
async def cors_test():
    """Test endpoint to verify CORS configuration."""
    return {
        "message": "CORS test successful",
        "allowed_origins": settings.allowed_origins_list,
        "cors_configured": True
    }


@router.options("/")
async def cors_preflight():
    """Handle CORS preflight requests."""
    return {"message": "CORS preflight successful"}

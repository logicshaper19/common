"""
Assistant API Endpoints
Simple chat endpoint with keyword-based responses
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.core.auth import get_current_user_sync
from app.models.user import User
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/assistant", tags=["assistant"])


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str
    success: bool = True


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest,
    current_user: User = Depends(get_current_user_sync)
):
    """Simple chat endpoint - no AI yet, just keyword matching."""
    
    try:
        message_lower = request.message.lower()
        user_name = current_user.first_name or current_user.email.split('@')[0] if current_user.email else "User"
        company_name = current_user.company.name if current_user.company else "your company"
        
        # Simple keyword-based responses using your existing data
        if "inventory" in message_lower:
            response = f"Hi {user_name}! I can help you with inventory management. You can check your current stock levels, create new batches, or allocate inventory to purchase orders. What specifically would you like to know about your inventory?"
        
        elif "purchase order" in message_lower or "po" in message_lower:
            response = f"I can help you with purchase orders for {company_name}. You can check PO status, create new purchase orders, or track fulfillment. What would you like to do with purchase orders?"
        
        elif "traceability" in message_lower or "transparency" in message_lower:
            response = "I can help you check traceability and transparency scores for your batches. This includes supply chain visibility, EUDR compliance, and sustainability metrics. Which batch or supplier would you like to check?"
        
        elif "compliance" in message_lower:
            response = "I can help you with compliance requirements including EUDR (European Union Deforestation Regulation), RSPO (Roundtable on Sustainable Palm Oil), and other regulatory standards. What specific compliance area would you like to explore?"
        
        elif "transformation" in message_lower or "processing" in message_lower:
            response = "I can help you with transformation and processing operations. This includes milling, refining, manufacturing, and harvest events. What type of transformation are you working with?"
        
        elif "help" in message_lower or "what can you do" in message_lower:
            response = f"Hello {user_name}! I'm your supply chain assistant. I can help you with:\n\n• 📦 Inventory management\n• 📋 Purchase orders\n• 🔍 Traceability & transparency\n• 🏭 Processing operations\n• ✅ Compliance requirements\n\nWhat would you like to know about?"
        
        else:
            response = f"Hello {user_name}! I'm your supply chain assistant. I can help you with inventory, purchase orders, traceability, compliance, and processing operations. Could you be more specific about what you'd like to know?"
        
        logger.info(f"Assistant response generated for user {current_user.id}: {message_lower[:50]}...")
        
        return ChatResponse(response=response)
        
    except Exception as e:
        logger.error(f"Error in assistant chat endpoint: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/health")
async def health_check():
    """Health check endpoint for the assistant service."""
    return {"status": "healthy", "service": "assistant"}

"""
Streaming Assistant API Endpoints
FastAPI endpoints for streaming chat with rich content (charts, tables, graphs)
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import StreamingResponse as FastAPIStreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import json
import os
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta

from app.core.database import get_db
from app.core.auth import get_current_user
from app.core.streaming_assistant import SupplyChainStreamingAssistant, StreamingResponseFormatter
from app.core.logging import get_logger
from app.models.user import User

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/assistant", tags=["streaming-assistant"])

# Rate limiting storage (in production, use Redis)
rate_limit_storage = defaultdict(lambda: deque())
rate_limit_cleanup_time = time.time()


class RateLimitError(Exception):
    """Exception raised when rate limit is exceeded."""
    pass


def check_rate_limit(user_id: str, max_requests: int = 10, window_seconds: int = 60) -> bool:
    """Check if user has exceeded rate limit."""
    global rate_limit_cleanup_time
    
    current_time = time.time()
    
    # Clean up old entries periodically
    if current_time - rate_limit_cleanup_time > 300:  # Clean every 5 minutes
        for user_queue in rate_limit_storage.values():
            while user_queue and user_queue[0] < current_time - window_seconds:
                user_queue.popleft()
        rate_limit_cleanup_time = current_time
    
    # Get user's request history
    user_requests = rate_limit_storage[user_id]
    
    # Remove old requests outside the window
    while user_requests and user_requests[0] < current_time - window_seconds:
        user_requests.popleft()
    
    # Check if user has exceeded limit
    if len(user_requests) >= max_requests:
        logger.warning(f"Rate limit exceeded for user {user_id}: {len(user_requests)} requests in {window_seconds}s")
        return False
    
    # Add current request
    user_requests.append(current_time)
    return True


class StreamingChatRequest(BaseModel):
    """Request model for streaming chat."""
    message: str
    chat_history: Optional[str] = ""
    include_visualizations: bool = True
    max_response_time: Optional[int] = 30  # seconds


class StreamingChatResponse(BaseModel):
    """Response model for streaming chat metadata."""
    success: bool = True
    message: str
    session_id: Optional[str] = None


@router.post("/stream-chat")
async def stream_chat_with_visuals(
    request: StreamingChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Stream chat responses with charts, tables, and graphs."""
    
    # Check rate limit
    if not check_rate_limit(str(current_user.id), max_requests=10, window_seconds=60):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please wait before making another request."
        )
    
    # Validate request
    if not request.message or len(request.message.strip()) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message cannot be empty"
        )
    
    if len(request.message) > 5000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message too long (max 5000 characters)"
        )
    
    async def generate_stream():
        """Generate streaming responses with rich content."""
        
        try:
            logger.info(f"Starting streaming chat for user {current_user.id}: {request.message[:50]}...")
            
            # Build user context
            user_context = await build_user_context(current_user, db)
            
            # Initialize streaming assistant
            assistant = SupplyChainStreamingAssistant()
            
            # Generate streaming responses
            response_count = 0
            async for response in assistant.stream_response(
                user_message=request.message,
                user_context=user_context,
                chat_history=request.chat_history
            ):
                # Convert to SSE format
                yield StreamingResponseFormatter.format_sse_data(response)
                response_count += 1
                
                # Log progress for monitoring
                if response_count % 5 == 0:
                    logger.debug(f"Streamed {response_count} responses for user {current_user.id}")
            
            # Send completion signal
            yield StreamingResponseFormatter.format_completion_signal()
            
            logger.info(f"Completed streaming chat for user {current_user.id}: {response_count} responses")
            
        except Exception as e:
            logger.error(f"Error in streaming chat for user {current_user.id}: {e}")
            yield StreamingResponseFormatter.format_error_signal(str(e))
    
    return FastAPIStreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control"
        }
    )


@router.post("/stream-chat-sync", response_model=StreamingChatResponse)
async def stream_chat_sync(
    request: StreamingChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Synchronous endpoint that collects all streaming responses and returns them as a single response."""
    
    try:
        # Build user context
        user_context = await build_user_context(current_user, db)
        
        # Initialize streaming assistant
        assistant = SupplyChainStreamingAssistant()
        
        # Collect all responses
        responses = []
        async for response in assistant.stream_response(
            user_message=request.message,
            user_context=user_context,
            chat_history=request.chat_history
        ):
            responses.append(response.to_dict())
        
        return StreamingChatResponse(
            success=True,
            message="Streaming responses collected successfully",
            session_id=f"session_{current_user.id}_{int(datetime.utcnow().timestamp())}"
        )
        
    except Exception as e:
        logger.error(f"Error in sync streaming chat: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing streaming request: {str(e)}"
        )


@router.get("/stream-chat/health")
async def streaming_health_check():
    """Health check endpoint for the streaming assistant service."""
    return {
        "status": "healthy",
        "service": "streaming-assistant",
        "features": {
            "streaming": True,
            "rich_content": True,
            "visualizations": True
        }
    }


async def build_user_context(current_user: User, db: Session) -> dict:
    """Build comprehensive user context for streaming assistant."""
    
    try:
        # Import here to avoid circular imports
        from app.api.assistant import (
            get_comprehensive_inventory_data,
            get_comprehensive_po_data,
            get_comprehensive_transparency_data,
            get_compliance_data,
            get_comprehensive_company_data,
            get_processing_data
        )
        
        # Get all data sources in parallel for efficiency
        inventory_data = await get_comprehensive_inventory_data(current_user, db)
        po_data = await get_comprehensive_po_data(current_user, db)
        transparency_data = await get_comprehensive_transparency_data(current_user, db)
        compliance_data = await get_compliance_data(current_user, db)
        company_data = await get_comprehensive_company_data(current_user, db)
        processing_data = await get_processing_data(current_user, db)
        
        # Build comprehensive context
        user_context = {
            "current_user": current_user,
            "db": db,
            "user_name": current_user.full_name or current_user.email.split('@')[0] if current_user.email else "User",
            "company_name": current_user.company.name if current_user.company else "Unknown Company",
            "company_type": current_user.company.company_type if current_user.company else "unknown",
            "user_role": current_user.role,
            "company_id": current_user.company_id,
            
            # Feature flags from environment
            "features_enabled": {
                "dashboard_brand": os.getenv('V2_DASHBOARD_BRAND') == 'true',
                "dashboard_processor": os.getenv('V2_DASHBOARD_PROCESSOR') == 'true',
                "dashboard_originator": os.getenv('V2_DASHBOARD_ORIGINATOR') == 'true',
                "notification_center": os.getenv('V2_NOTIFICATION_CENTER') == 'true',
                "streaming_chat": True,
                "rich_visualizations": True
            },
            
            # Data summaries for quick access
            "inventory_summary": f"{inventory_data.get('total_batches', 0)} batches, {inventory_data.get('available_quantity', 0)} MT available",
            "recent_pos": f"{po_data.get('pending_pos', 0)} pending, {po_data.get('active_pos', 0)} active purchase orders",
            "transparency_score": f"{transparency_data.get('average_score', 0):.1f}% average transparency",
            "compliance_status": f"{compliance_data.get('eudr_compliant', 0)} EUDR compliant batches",
            
            # Full data for detailed responses
            "inventory": inventory_data,
            "purchase_orders": po_data,
            "transparency": transparency_data,
            "compliance": compliance_data,
            "company_relationships": company_data,
            "processing": processing_data
        }
        
        return user_context
        
    except Exception as e:
        logger.error(f"Error building user context: {e}")
        # Return minimal context
        return {
            "current_user": current_user,
            "db": db,
            "user_name": current_user.full_name or current_user.email.split('@')[0] if current_user.email else "User",
            "company_name": current_user.company.name if current_user.company else "Unknown Company",
            "company_type": current_user.company.company_type if current_user.company else "unknown",
            "user_role": current_user.role,
            "company_id": current_user.company_id,
            "features_enabled": {
                "streaming_chat": True,
                "rich_visualizations": True
            },
            "inventory_summary": "0 batches, 0 MT available",
            "recent_pos": "0 pending, 0 active purchase orders",
            "transparency_score": "0.0% average transparency",
            "compliance_status": "0 EUDR compliant batches",
            "inventory": {"total_batches": 0, "available_quantity": 0},
            "purchase_orders": {"pending_pos": 0, "confirmed_pos": 0},
            "transparency": {"average_score": 0, "total_batches": 0},
            "compliance": {"eudr_compliant": 0, "rspo_compliant": 0},
            "company_relationships": {"total_relationships": 0},
            "processing": {"processing_batches": 0}
        }


# Additional utility endpoints for testing and debugging

@router.get("/stream-chat/test")
async def test_streaming_endpoint():
    """Test endpoint to verify streaming functionality."""
    
    async def test_stream():
        """Generate test streaming data."""
        test_responses = [
            {
                "type": "text",
                "content": "This is a test streaming response",
                "metadata": {"test": True}
            },
            {
                "type": "metric_card",
                "content": {
                    "title": "Test Metrics",
                    "metrics": [
                        {"label": "Test Value", "value": "100", "trend": "+5%", "color": "green"}
                    ]
                }
            },
            {
                "type": "chart",
                "content": {
                    "chart_type": "line",
                    "title": "Test Chart",
                    "data": [{"x": "Jan", "y": 10}, {"x": "Feb", "y": 20}]
                }
            },
            {
                "type": "complete",
                "content": "Test complete"
            }
        ]
        
        for response in test_responses:
            yield f"data: {json.dumps(response)}\n\n"
    
    return FastAPIStreamingResponse(
        test_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive"
        }
    )


@router.get("/stream-chat/features")
async def get_streaming_features():
    """Get information about available streaming features."""
    return {
        "streaming_types": [
            "text",
            "chart",
            "table", 
            "graph",
            "metric_card",
            "map",
            "alert",
            "progress",
            "complete"
        ],
        "chart_types": [
            "line",
            "bar",
            "donut",
            "gauge",
            "scatter"
        ],
        "graph_types": [
            "supply_chain_flow",
            "network",
            "hierarchical"
        ],
        "supported_queries": [
            "inventory analysis",
            "transparency metrics",
            "yield performance",
            "supplier networks",
            "compliance status",
            "processing efficiency"
        ]
    }

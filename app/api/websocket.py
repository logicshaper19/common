"""
WebSocket endpoints for real-time updates.
"""
import json
from typing import Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from uuid import UUID

from app.core.websocket_manager import manager
from app.core.config import settings
from app.core.security import verify_token
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


async def get_websocket_user(websocket: WebSocket, token: Optional[str] = None):
    """Extract user information from WebSocket connection."""
    if not token:
        return None, None
        
    try:
        payload = verify_token(token)
        user_id = payload.get("sub")
        if user_id:
            return str(user_id), payload.get("company_id")
    except Exception as e:
        logger.warning("Invalid token in WebSocket connection", error=str(e))
    
    return None, None


@router.websocket("/ws/dashboard")
async def websocket_dashboard(websocket: WebSocket, token: Optional[str] = Query(None)):
    """WebSocket endpoint for dashboard real-time updates."""
    try:
        user_id, company_id = await get_websocket_user(websocket, token)
        logger.info("WebSocket dashboard connection attempt", user_id=user_id, company_id=company_id, has_token=bool(token))
        
        await manager.connect(websocket, user_id, company_id)
        # Send welcome message
        await manager.send_json_message({
            "type": "connection_established",
            "message": "Connected to dashboard updates",
            "user_id": user_id,
            "company_id": company_id
        }, websocket)
        
        while True:
            # Wait for messages from client
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                message_type = message.get("type")
                
                if message_type == "ping":
                    await manager.send_json_message({
                        "type": "pong",
                        "timestamp": message.get("timestamp")
                    }, websocket)
                elif message_type == "subscribe":
                    # Handle subscription to specific updates
                    subscription_type = message.get("subscription_type")
                    await manager.send_json_message({
                        "type": "subscription_confirmed",
                        "subscription_type": subscription_type
                    }, websocket)
                else:
                    await manager.send_json_message({
                        "type": "error",
                        "message": f"Unknown message type: {message_type}"
                    }, websocket)
                    
            except json.JSONDecodeError:
                await manager.send_json_message({
                    "type": "error",
                    "message": "Invalid JSON format"
                }, websocket)
                
    except WebSocketDisconnect as e:
        manager.disconnect(websocket, user_id, company_id)
        logger.info("WebSocket dashboard disconnected", user_id=user_id, code=e.code, reason=e.reason)
    except Exception as e:
        logger.error("WebSocket dashboard error", error=str(e), user_id=user_id, error_type=type(e).__name__)
        manager.disconnect(websocket, user_id, company_id)


@router.websocket("/ws/notifications")
async def websocket_notifications(websocket: WebSocket, token: Optional[str] = Query(None)):
    """WebSocket endpoint for real-time notifications."""
    user_id, company_id = await get_websocket_user(websocket, token)
    
    await manager.connect(websocket, user_id, company_id)
    
    try:
        # Send welcome message
        await manager.send_json_message({
            "type": "connection_established",
            "message": "Connected to notifications",
            "user_id": user_id,
            "company_id": company_id
        }, websocket)
        
        while True:
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                message_type = message.get("type")
                
                if message_type == "ping":
                    await manager.send_json_message({
                        "type": "pong",
                        "timestamp": message.get("timestamp")
                    }, websocket)
                else:
                    await manager.send_json_message({
                        "type": "error",
                        "message": f"Unknown message type: {message_type}"
                    }, websocket)
                    
            except json.JSONDecodeError:
                await manager.send_json_message({
                    "type": "error",
                    "message": "Invalid JSON format"
                }, websocket)
                
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id, company_id)
        logger.info("WebSocket notifications disconnected", user_id=user_id)
    except Exception as e:
        logger.error("WebSocket notifications error", error=str(e), user_id=user_id)
        manager.disconnect(websocket, user_id, company_id)


@router.websocket("/ws/transparency/{company_id}")
async def websocket_transparency(websocket: WebSocket, company_id: str, token: Optional[str] = Query(None)):
    """WebSocket endpoint for transparency updates for a specific company."""
    user_id, user_company_id = await get_websocket_user(websocket, token)
    
    # Verify user has access to this company's data
    if user_company_id != company_id:
        await websocket.close(code=1008, reason="Unauthorized access to company data")
        return
    
    await manager.connect(websocket, user_id, company_id)
    
    try:
        # Send welcome message
        await manager.send_json_message({
            "type": "connection_established",
            "message": f"Connected to transparency updates for company {company_id}",
            "user_id": user_id,
            "company_id": company_id
        }, websocket)
        
        while True:
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                message_type = message.get("type")
                
                if message_type == "ping":
                    await manager.send_json_message({
                        "type": "pong",
                        "timestamp": message.get("timestamp")
                    }, websocket)
                else:
                    await manager.send_json_message({
                        "type": "error",
                        "message": f"Unknown message type: {message_type}"
                    }, websocket)
                    
            except json.JSONDecodeError:
                await manager.send_json_message({
                    "type": "error",
                    "message": "Invalid JSON format"
                }, websocket)
                
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id, company_id)
        logger.info("WebSocket transparency disconnected", user_id=user_id, company_id=company_id)
    except Exception as e:
        logger.error("WebSocket transparency error", error=str(e), user_id=user_id, company_id=company_id)
        manager.disconnect(websocket, user_id, company_id)

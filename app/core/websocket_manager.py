"""
WebSocket connection manager for real-time updates.
"""
import json
from typing import List, Dict, Any
from fastapi import WebSocket, WebSocketDisconnect
from app.core.logging import get_logger

logger = get_logger(__name__)


class ConnectionManager:
    """Manages WebSocket connections for real-time updates."""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.user_connections: Dict[str, List[WebSocket]] = {}
        self.company_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: str = None, company_id: str = None):
        """Accept a new WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)
        
        if user_id:
            if user_id not in self.user_connections:
                self.user_connections[user_id] = []
            self.user_connections[user_id].append(websocket)
            
        if company_id:
            if company_id not in self.company_connections:
                self.company_connections[company_id] = []
            self.company_connections[company_id].append(websocket)
            
        logger.info("WebSocket connected", 
                   user_id=user_id, 
                   company_id=company_id,
                   total_connections=len(self.active_connections))

    def disconnect(self, websocket: WebSocket, user_id: str = None, company_id: str = None):
        """Remove a WebSocket connection."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            
        if user_id and user_id in self.user_connections:
            if websocket in self.user_connections[user_id]:
                self.user_connections[user_id].remove(websocket)
                if not self.user_connections[user_id]:
                    del self.user_connections[user_id]
                    
        if company_id and company_id in self.company_connections:
            if websocket in self.company_connections[company_id]:
                self.company_connections[company_id].remove(websocket)
                if not self.company_connections[company_id]:
                    del self.company_connections[company_id]
                    
        logger.info("WebSocket disconnected", 
                   user_id=user_id, 
                   company_id=company_id,
                   total_connections=len(self.active_connections))

    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Send a message to a specific WebSocket connection."""
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error("Failed to send personal message", error=str(e))

    async def send_json_message(self, data: Dict[str, Any], websocket: WebSocket):
        """Send a JSON message to a specific WebSocket connection."""
        try:
            await websocket.send_text(json.dumps(data))
        except Exception as e:
            logger.error("Failed to send JSON message", error=str(e))

    async def broadcast(self, message: str):
        """Broadcast a message to all active connections."""
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error("Failed to broadcast message", error=str(e))

    async def broadcast_json(self, data: Dict[str, Any]):
        """Broadcast a JSON message to all active connections."""
        message = json.dumps(data)
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error("Failed to broadcast JSON message", error=str(e))

    async def send_to_user(self, user_id: str, data: Dict[str, Any]):
        """Send a message to all connections for a specific user."""
        if user_id in self.user_connections:
            message = json.dumps(data)
            for connection in self.user_connections[user_id]:
                try:
                    await connection.send_text(message)
                except Exception as e:
                    logger.error("Failed to send message to user", user_id=user_id, error=str(e))

    async def send_to_company(self, company_id: str, data: Dict[str, Any]):
        """Send a message to all connections for a specific company."""
        if company_id in self.company_connections:
            message = json.dumps(data)
            for connection in self.company_connections[company_id]:
                try:
                    await connection.send_text(message)
                except Exception as e:
                    logger.error("Failed to send message to company", company_id=company_id, error=str(e))

    def get_connection_count(self) -> int:
        """Get the total number of active connections."""
        return len(self.active_connections)

    def get_user_connection_count(self, user_id: str) -> int:
        """Get the number of connections for a specific user."""
        return len(self.user_connections.get(user_id, []))

    def get_company_connection_count(self, company_id: str) -> int:
        """Get the number of connections for a specific company."""
        return len(self.company_connections.get(company_id, []))


# Global connection manager instance
manager = ConnectionManager()

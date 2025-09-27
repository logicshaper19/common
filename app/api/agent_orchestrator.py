"""
Agent Orchestrator API Endpoint
Unified API endpoint that routes queries to appropriate specialized agents.
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..core.agent_orchestrator import SupplyChainAgentOrchestrator, AgentContext, AgentResponse
from ..core.config import Settings
from ..core.database import get_db
from ..core.auth import get_current_user
from ..models.user import User

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/api/v1/agents", tags=["Agent Orchestrator"])

# Global orchestrator instance
_orchestrator: Optional[SupplyChainAgentOrchestrator] = None

def get_orchestrator() -> SupplyChainAgentOrchestrator:
    """Get or create the global orchestrator instance."""
    global _orchestrator
    if _orchestrator is None:
        config = Settings()
        _orchestrator = SupplyChainAgentOrchestrator(config)
        logger.info("Agent orchestrator initialized")
    return _orchestrator

# Request/Response Models
class AgentQueryRequest(BaseModel):
    """Request model for agent queries."""
    query: str = Field(..., min_length=1, max_length=2000, description="The query to process")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context for the query")
    session_id: Optional[str] = Field(default=None, max_length=100, description="Session ID for conversation continuity")
    
    class Config:
        schema_extra = {
            "example": {
                "query": "Show me sustainability metrics for our suppliers",
                "context": {
                    "company_id": "company_123",
                    "preferences": {"format": "detailed"}
                },
                "session_id": "session_456"
            }
        }

class AgentQueryResponse(BaseModel):
    """Response model for agent queries."""
    success: bool = Field(..., description="Whether the query was processed successfully")
    response: str = Field(..., description="The agent's response")
    agent_role: str = Field(..., description="The agent that processed the query")
    tools_used: list[str] = Field(default_factory=list, description="Tools used by the agent")
    execution_time: float = Field(..., description="Time taken to process the query in seconds")
    error_message: Optional[str] = Field(default=None, description="Error message if processing failed")
    timestamp: datetime = Field(default_factory=datetime.now, description="Response timestamp")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "response": "Here are the sustainability metrics for your suppliers...",
                "agent_role": "brand_manager",
                "tools_used": ["get_supply_chain_analytics", "get_company_info"],
                "execution_time": 1.25,
                "error_message": None,
                "timestamp": "2024-01-15T10:30:00Z"
            }
        }

class AgentInfoResponse(BaseModel):
    """Response model for agent information."""
    total_agents: int = Field(..., description="Total number of available agents")
    agents: Dict[str, Dict[str, Any]] = Field(..., description="Information about each agent")
    
    class Config:
        schema_extra = {
            "example": {
                "total_agents": 5,
                "agents": {
                    "brand_manager": {
                        "tools_count": 5,
                        "tools": ["get_supply_chain_analytics", "get_company_info", "get_certifications", "get_documents", "get_intelligent_recommendations"]
                    },
                    "processor_operations": {
                        "tools_count": 5,
                        "tools": ["get_transformations", "get_products", "search_batches", "trace_supply_chain", "get_comprehensive_dashboard"]
                    }
                }
            }
        }

class HealthCheckResponse(BaseModel):
    """Response model for health check."""
    orchestrator: str = Field(..., description="Orchestrator health status")
    agents: Dict[str, Dict[str, Any]] = Field(..., description="Health status of each agent")
    timestamp: str = Field(..., description="Health check timestamp")

# API Endpoints
@router.post("/query", response_model=AgentQueryResponse)
async def query_agent(
    request: AgentQueryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> AgentQueryResponse:
    """
    Process a query using the appropriate specialized agent.
    
    The system will automatically route your query to the most suitable agent based on:
    - Your user role and permissions
    - The content and keywords in your query
    - Available context and session information
    
    Each agent has specialized tools and knowledge for different aspects of supply chain management.
    """
    try:
        # Get orchestrator
        orchestrator = get_orchestrator()
        
        # Create agent context from user and request
        agent_context = AgentContext(
            user_id=str(current_user.id),
            company_id=str(current_user.company_id) if current_user.company_id else None,
            role=current_user.role,
            permissions=[],  # Could be expanded to include user permissions
            session_id=request.session_id,
            timestamp=datetime.now()
        )
        
        # Process the query
        agent_response: AgentResponse = await orchestrator.route_query(
            query=request.query,
            context=agent_context
        )
        
        # Convert to response model
        return AgentQueryResponse(
            success=agent_response.success,
            response=agent_response.response,
            agent_role=agent_response.agent_role.value,
            tools_used=agent_response.tools_used,
            execution_time=agent_response.execution_time,
            error_message=agent_response.error_message,
            timestamp=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"Error processing agent query: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process query: {str(e)}"
        )

@router.get("/info", response_model=AgentInfoResponse)
async def get_agent_info(
    current_user: User = Depends(get_current_user)
) -> AgentInfoResponse:
    """
    Get information about all available agents and their tools.
    
    Returns details about:
    - Total number of agents
    - Tools available to each agent
    - Agent capabilities and specializations
    """
    try:
        orchestrator = get_orchestrator()
        info = orchestrator.get_agent_info()
        
        return AgentInfoResponse(
            total_agents=info["total_agents"],
            agents=info["agents"]
        )
        
    except Exception as e:
        logger.error(f"Error getting agent info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get agent information: {str(e)}"
        )

@router.get("/health", response_model=HealthCheckResponse)
async def health_check(
    current_user: User = Depends(get_current_user)
) -> HealthCheckResponse:
    """
    Perform a health check on the agent orchestrator and all agents.
    
    Returns the health status of:
    - The orchestrator itself
    - Each individual agent
    - Tool availability and functionality
    """
    try:
        orchestrator = get_orchestrator()
        health = await orchestrator.health_check()
        
        return HealthCheckResponse(
            orchestrator=health["orchestrator"],
            agents=health["agents"],
            timestamp=health["timestamp"]
        )
        
    except Exception as e:
        logger.error(f"Error performing health check: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Health check failed: {str(e)}"
        )

@router.get("/agents/{agent_role}/tools")
async def get_agent_tools(
    agent_role: str,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get detailed information about tools available to a specific agent.
    
    Parameters:
    - agent_role: The role of the agent (brand_manager, processor_operations, etc.)
    
    Returns:
    - List of tools available to the agent
    - Tool descriptions and capabilities
    """
    try:
        orchestrator = get_orchestrator()
        
        # Validate agent role
        from ..core.agent_orchestrator import AgentRole
        try:
            role_enum = AgentRole(agent_role)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid agent role: {agent_role}. Valid roles are: {[r.value for r in AgentRole]}"
            )
        
        # Get agent
        agent = orchestrator.agents.get(role_enum)
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent {agent_role} not found"
            )
        
        # Get tool information
        tools_info = []
        for tool in agent.tools:
            tools_info.append({
                "name": tool.name,
                "description": tool.description,
                "args_schema": tool.args_schema if hasattr(tool, 'args_schema') else None
            })
        
        return {
            "agent_role": agent_role,
            "tools_count": len(agent.tools),
            "tools": tools_info
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting agent tools: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get agent tools: {str(e)}"
        )

@router.post("/agents/{agent_role}/query")
async def query_specific_agent(
    agent_role: str,
    request: AgentQueryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> AgentQueryResponse:
    """
    Process a query using a specific agent (bypassing automatic routing).
    
    Parameters:
    - agent_role: The specific agent to use (brand_manager, processor_operations, etc.)
    
    This endpoint allows you to force a query to be processed by a specific agent,
    useful for testing or when you know exactly which agent should handle your query.
    """
    try:
        orchestrator = get_orchestrator()
        
        # Validate agent role
        from ..core.agent_orchestrator import AgentRole
        try:
            role_enum = AgentRole(agent_role)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid agent role: {agent_role}. Valid roles are: {[r.value for r in AgentRole]}"
            )
        
        # Get specific agent
        agent = orchestrator.agents.get(role_enum)
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent {agent_role} not found"
            )
        
        # Create agent context
        agent_context = AgentContext(
            user_id=str(current_user.id),
            company_id=str(current_user.company_id) if current_user.company_id else None,
            role=current_user.role,
            permissions=[],
            session_id=request.session_id,
            timestamp=datetime.now()
        )
        
        # Process the query with specific agent
        agent_response: AgentResponse = await agent.execute(
            query=request.query,
            context=agent_context
        )
        
        # Convert to response model
        return AgentQueryResponse(
            success=agent_response.success,
            response=agent_response.response,
            agent_role=agent_response.agent_role.value,
            tools_used=agent_response.tools_used,
            execution_time=agent_response.execution_time,
            error_message=agent_response.error_message,
            timestamp=datetime.now()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing specific agent query: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process query with {agent_role}: {str(e)}"
        )

# WebSocket endpoint for real-time agent interactions
@router.websocket("/ws")
async def websocket_agent_chat(websocket, current_user: User = Depends(get_current_user)):
    """
    WebSocket endpoint for real-time agent interactions.
    
    Allows for continuous conversation with agents, maintaining context
    and providing real-time responses.
    """
    await websocket.accept()
    
    try:
        orchestrator = get_orchestrator()
        
        # Create agent context
        agent_context = AgentContext(
            user_id=str(current_user.id),
            company_id=str(current_user.company_id) if current_user.company_id else None,
            role=current_user.role,
            permissions=[],
            session_id=f"ws_{current_user.id}_{datetime.now().timestamp()}",
            timestamp=datetime.now()
        )
        
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            
            if data.get("type") == "query":
                query = data.get("query", "")
                if not query:
                    await websocket.send_json({
                        "type": "error",
                        "message": "Query cannot be empty"
                    })
                    continue
                
                # Process query
                agent_response = await orchestrator.route_query(query, agent_context)
                
                # Send response
                await websocket.send_json({
                    "type": "response",
                    "success": agent_response.success,
                    "response": agent_response.response,
                    "agent_role": agent_response.agent_role.value,
                    "tools_used": agent_response.tools_used,
                    "execution_time": agent_response.execution_time,
                    "error_message": agent_response.error_message,
                    "timestamp": datetime.now().isoformat()
                })
                
            elif data.get("type") == "ping":
                await websocket.send_json({
                    "type": "pong",
                    "timestamp": datetime.now().isoformat()
                })
                
            else:
                await websocket.send_json({
                    "type": "error",
                    "message": "Unknown message type"
                })
                
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.send_json({
            "type": "error",
            "message": f"Connection error: {str(e)}"
        })
    finally:
        await websocket.close()

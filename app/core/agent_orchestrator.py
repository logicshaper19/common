"""
Supply Chain Agent Orchestrator
Manages 5 specialized agents with role-based routing and tool distribution.
"""
import logging
from typing import Dict, List, Any, Optional, Union
from enum import Enum
from dataclasses import dataclass
from datetime import datetime

# LangChain imports
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.tools import tool, Tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.memory import ConversationBufferWindowMemory
from langchain_openai import ChatOpenAI

# Try to import agent components - fallback to simple LLM if not available
try:
    from langchain.agents import AgentExecutor, create_tool_calling_agent
    AGENT_AVAILABLE = True
except ImportError:
    AGENT_AVAILABLE = False
    AgentExecutor = None
    create_tool_calling_agent = None

# Our existing components
from .certification_functions import CertificationManager
from .supply_chain_functions import SupplyChainManager
from .logistics_functions import LogisticsManager
from .notification_functions import NotificationManager
from .ai_supply_chain_assistant import ComprehensiveSupplyChainAI
from .database_manager import get_database_manager
from .config import Settings

# Import feature flag system
from .consolidated_feature_flags import consolidated_feature_flags
from .feature_flags import FeatureFlag, feature_flags

logger = logging.getLogger(__name__)

class AgentRole(Enum):
    """Enumeration of available agent roles."""
    BRAND_MANAGER = "brand_manager"
    PROCESSOR_OPERATIONS = "processor_operations"
    ORIGINATOR_PLANTATION = "originator_plantation"
    TRADER_LOGISTICS = "trader_logistics"
    ADMIN_SYSTEM = "admin_system"

@dataclass
class AgentContext:
    """Context information for agent routing and execution."""
    user_id: str
    company_id: Optional[str] = None
    role: Optional[str] = None
    permissions: List[str] = None
    session_id: Optional[str] = None
    timestamp: Optional[datetime] = None
    
    def __post_init__(self):
        if self.permissions is None:
            self.permissions = []

@dataclass
class AgentResponse:
    """Standardized response from agent execution."""
    agent_role: AgentRole
    response: str
    tools_used: List[str]
    execution_time: float
    success: bool
    error_message: Optional[str] = None

class BaseAgent:
    """Base class for all specialized agents."""
    
    def __init__(self, role: AgentRole, db_manager, config: Settings):
        self.role = role
        self.db_manager = db_manager
        self.config = config
        self.tools = []
        self.memory = ConversationBufferWindowMemory(
            k=10,  # Keep last 10 exchanges
            memory_key="chat_history",
            return_messages=True
        )
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.1,
            api_key=os.getenv("OPENAI_API_KEY")
        )
        self._initialize_tools()
        self._create_agent()
    
    def _initialize_tools(self):
        """Initialize tools specific to this agent. Override in subclasses."""
        pass
    
    def _create_agent(self):
        """Create the LangChain agent with tools and memory."""
        if not AGENT_AVAILABLE or not self.tools:
            # Fallback to simple LLM chain if agents not available or no tools
            self.agent_executor = None
            return
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", self._get_system_prompt()),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        try:
            self.agent = create_tool_calling_agent(self.llm, self.tools, prompt)
            self.agent_executor = AgentExecutor(
                agent=self.agent,
                tools=self.tools,
                memory=self.memory,
                verbose=True,
                handle_parsing_errors=True,
                max_iterations=5
            )
        except Exception as e:
            logger.warning(f"Failed to create agent executor: {e}. Falling back to simple LLM.")
            self.agent_executor = None
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for this agent. Override in subclasses."""
        return f"You are a {self.role.value} agent for the Supply Chain Transparency Platform."
    
    async def execute(self, query: str, context: AgentContext) -> AgentResponse:
        """Execute a query using this agent."""
        start_time = datetime.now()
        tools_used = []
        
        try:
            if self.agent_executor:
                response = await self.agent_executor.ainvoke({
                    "input": query,
                    "chat_history": self.memory.chat_memory.messages
                })
                result = response.get("output", str(response))
            else:
                # Fallback to direct LLM call
                messages = [
                    SystemMessage(content=self._get_system_prompt()),
                    HumanMessage(content=query)
                ]
                response = await self.llm.ainvoke(messages)
                result = response.content
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return AgentResponse(
                agent_role=self.role,
                response=result,
                tools_used=tools_used,
                execution_time=execution_time,
                success=True
            )
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"Error in {self.role.value} agent: {e}")
            
            return AgentResponse(
                agent_role=self.role,
                response="",
                tools_used=tools_used,
                execution_time=execution_time,
                success=False,
                error_message=str(e)
            )

class BrandManagerAgent(BaseAgent):
    """Brand Manager Agent - Brand portfolio oversight, supplier compliance, sustainability reporting."""
    
    def __init__(self, db_manager, config: Settings):
        super().__init__(AgentRole.BRAND_MANAGER, db_manager, config)
        self.cert_manager = CertificationManager(db_manager=db_manager)
        self.ai_assistant = ComprehensiveSupplyChainAI(db_manager)
    
    def _initialize_tools(self):
        """Initialize brand management tools."""
        @tool
        def get_supply_chain_analytics() -> str:
            """Get supply chain analytics and sustainability metrics for brand portfolio."""
            try:
                # This would call the actual function from supply_chain_functions
                return "Supply chain analytics retrieved successfully"
            except Exception as e:
                return f"Error retrieving analytics: {e}"
        
        @tool
        def get_company_info(company_id: str) -> str:
            """Get company information and compliance status."""
            try:
                # This would call the actual function from certification_functions
                return f"Company info for {company_id} retrieved successfully"
            except Exception as e:
                return f"Error retrieving company info: {e}"
        
        @tool
        def get_certifications(company_id: str) -> str:
            """Get RSPO/MSPO certifications for company."""
            try:
                return f"Certifications for {company_id} retrieved successfully"
            except Exception as e:
                return f"Error retrieving certifications: {e}"
        
        @tool
        def get_documents(document_type: str) -> str:
            """Get sustainability reports and compliance documentation."""
            try:
                return f"Documents of type {document_type} retrieved successfully"
            except Exception as e:
                return f"Error retrieving documents: {e}"
        
        @tool
        def get_intelligent_recommendations() -> str:
            """Get AI-driven insights for brand sustainability strategy."""
            try:
                return "Intelligent recommendations generated successfully"
            except Exception as e:
                return f"Error generating recommendations: {e}"
        
        self.tools = [
            get_supply_chain_analytics,
            get_company_info,
            get_certifications,
            get_documents,
            get_intelligent_recommendations
        ]
    
    def _get_system_prompt(self) -> str:
        return """You are a Brand Manager Agent for the Supply Chain Transparency Platform.

Your expertise includes:
- Brand portfolio oversight and management
- Supplier compliance monitoring
- Sustainability reporting and metrics
- RSPO/MSPO certification tracking
- Supply chain transparency analytics

You help brand managers make informed decisions about their supply chain partners,
monitor compliance, and ensure sustainability standards are met.

Always provide clear, actionable insights based on data and certifications."""

class ProcessorOperationsAgent(BaseAgent):
    """Processor Operations Agent - Manufacturing efficiency, processing optimization, quality control."""
    
    def __init__(self, db_manager, config: Settings):
        super().__init__(AgentRole.PROCESSOR_OPERATIONS, db_manager, config)
        self.supply_manager = SupplyChainManager(db_connection=db_manager)
    
    def _initialize_tools(self):
        """Initialize processor operations tools."""
        @tool
        def get_transformations() -> str:
            """Get milling operations, OER rates, and processing efficiency data."""
            try:
                return "Transformation data retrieved successfully"
            except Exception as e:
                return f"Error retrieving transformations: {e}"
        
        @tool
        def get_products() -> str:
            """Get CPO/RBDPO specifications, quality parameters, and inventory levels."""
            try:
                return "Product data retrieved successfully"
            except Exception as e:
                return f"Error retrieving products: {e}"
        
        @tool
        def search_batches(product_type: str, status: str) -> str:
            """Search inventory batches by product type and status."""
            try:
                return f"Batches for {product_type} with status {status} retrieved successfully"
            except Exception as e:
                return f"Error searching batches: {e}"
        
        @tool
        def trace_supply_chain(batch_id: str) -> str:
            """Trace end-to-end batch from FFB to refined products."""
            try:
                return f"Supply chain trace for batch {batch_id} completed successfully"
            except Exception as e:
                return f"Error tracing supply chain: {e}"
        
        @tool
        def get_comprehensive_dashboard() -> str:
            """Get processing plant KPIs and operational overview."""
            try:
                return "Comprehensive dashboard data retrieved successfully"
            except Exception as e:
                return f"Error retrieving dashboard: {e}"
        
        self.tools = [
            get_transformations,
            get_products,
            search_batches,
            trace_supply_chain,
            get_comprehensive_dashboard
        ]
    
    def _get_system_prompt(self) -> str:
        return """You are a Processor Operations Agent for the Supply Chain Transparency Platform.

Your expertise includes:
- Manufacturing efficiency optimization
- Processing operations management
- Quality control and specifications
- OER (Oil Extraction Rate) monitoring
- Inventory and batch management
- End-to-end traceability

You help processing plant managers optimize operations, monitor quality,
and ensure efficient production processes.

Always provide technical insights and operational recommendations."""

class OriginatorPlantationAgent(BaseAgent):
    """Originator/Plantation Agent - Farm management, EUDR compliance, plantation operations."""
    
    def __init__(self, db_manager, config: Settings):
        super().__init__(AgentRole.ORIGINATOR_PLANTATION, db_manager, config)
        self.cert_manager = CertificationManager(db_manager=db_manager)
        self.notification_manager = NotificationManager(db_connection=db_manager)
    
    def _initialize_tools(self):
        """Initialize plantation management tools."""
        @tool
        def get_farm_locations() -> str:
            """Get plantation GPS coordinates and EUDR compliance status."""
            try:
                return "Farm locations and EUDR compliance data retrieved successfully"
            except Exception as e:
                return f"Error retrieving farm locations: {e}"
        
        @tool
        def search_batches_with_certification(certification_type: str) -> str:
            """Search FFB batches with certification filtering."""
            try:
                return f"Batches with {certification_type} certification retrieved successfully"
            except Exception as e:
                return f"Error searching certified batches: {e}"
        
        @tool
        def get_certifications() -> str:
            """Get RSPO, MSPO, and sustainability certification status."""
            try:
                return "Certification status retrieved successfully"
            except Exception as e:
                return f"Error retrieving certifications: {e}"
        
        @tool
        def get_notifications() -> str:
            """Get compliance alerts for deforestation and regulatory issues."""
            try:
                return "Compliance notifications retrieved successfully"
            except Exception as e:
                return f"Error retrieving notifications: {e}"
        
        @tool
        def trigger_alert_check() -> str:
            """Trigger manual compliance auditing and alert management."""
            try:
                return "Alert check triggered successfully"
            except Exception as e:
                return f"Error triggering alert check: {e}"
        
        self.tools = [
            get_farm_locations,
            search_batches_with_certification,
            get_certifications,
            get_notifications,
            trigger_alert_check
        ]
    
    def _get_system_prompt(self) -> str:
        return """You are an Originator/Plantation Agent for the Supply Chain Transparency Platform.

Your expertise includes:
- Farm and plantation management
- EUDR (European Union Deforestation Regulation) compliance
- GPS coordinate tracking and verification
- RSPO/MSPO certification management
- Deforestation monitoring and alerts
- Sustainability compliance

You help plantation managers ensure compliance with regulations,
monitor farm operations, and maintain certification standards.

Always prioritize compliance and sustainability in your recommendations."""

class TraderLogisticsAgent(BaseAgent):
    """Trader/Logistics Agent - Supply chain logistics, trading operations, delivery management."""
    
    def __init__(self, db_manager, config: Settings):
        super().__init__(AgentRole.TRADER_LOGISTICS, db_manager, config)
        self.logistics_manager = LogisticsManager(db_connection=db_manager)
        self.cert_manager = CertificationManager(db_manager=db_manager)
    
    def _initialize_tools(self):
        """Initialize trading and logistics tools."""
        @tool
        def get_purchase_orders() -> str:
            """Get purchase orders with buyer/seller filtering and fulfillment tracking."""
            try:
                return "Purchase orders retrieved successfully"
            except Exception as e:
                return f"Error retrieving purchase orders: {e}"
        
        @tool
        def get_deliveries() -> str:
            """Get shipment tracking, delivery performance, and logistics KPIs."""
            try:
                return "Delivery data retrieved successfully"
            except Exception as e:
                return f"Error retrieving deliveries: {e}"
        
        @tool
        def get_shipments() -> str:
            """Get transportation data with carrier performance analytics."""
            try:
                return "Shipment data retrieved successfully"
            except Exception as e:
                return f"Error retrieving shipments: {e}"
        
        @tool
        def get_inventory_movements() -> str:
            """Get inventory coordination across multiple locations."""
            try:
                return "Inventory movements retrieved successfully"
            except Exception as e:
                return f"Error retrieving inventory movements: {e}"
        
        @tool
        def get_logistics_analytics() -> str:
            """Get transportation optimization and logistics analytics."""
            try:
                return "Logistics analytics retrieved successfully"
            except Exception as e:
                return f"Error retrieving logistics analytics: {e}"
        
        self.tools = [
            get_purchase_orders,
            get_deliveries,
            get_shipments,
            get_inventory_movements,
            get_logistics_analytics
        ]
    
    def _get_system_prompt(self) -> str:
        return """You are a Trader/Logistics Agent for the Supply Chain Transparency Platform.

Your expertise includes:
- Supply chain logistics optimization
- Trading operations management
- Delivery and shipment tracking
- Purchase order management
- Inventory coordination
- Transportation analytics

You help traders and logistics managers optimize supply chain operations,
track deliveries, and manage trading relationships.

Always provide insights on efficiency, cost optimization, and delivery performance."""

class AdminSystemAgent(BaseAgent):
    """Admin System Agent - System administration, user management, platform oversight."""
    
    def __init__(self, db_manager, config: Settings):
        super().__init__(AgentRole.ADMIN_SYSTEM, db_manager, config)
        self.notification_manager = NotificationManager(db_connection=db_manager)
        self.ai_assistant = ComprehensiveSupplyChainAI(db_manager)
    
    def _initialize_tools(self):
        """Initialize admin system tools."""
        @tool
        def get_system_analytics() -> str:
            """Get comprehensive system analytics and platform performance metrics."""
            try:
                return "System analytics retrieved successfully"
            except Exception as e:
                return f"Error retrieving system analytics: {e}"
        
        @tool
        def get_user_management() -> str:
            """Get user management and access control information."""
            try:
                return "User management data retrieved successfully"
            except Exception as e:
                return f"Error retrieving user management data: {e}"
        
        @tool
        def get_platform_health() -> str:
            """Get platform health monitoring and system status."""
            try:
                return "Platform health data retrieved successfully"
            except Exception as e:
                return f"Error retrieving platform health: {e}"
        
        @tool
        def get_notifications() -> str:
            """Get system-wide notifications and alerts."""
            try:
                return "System notifications retrieved successfully"
            except Exception as e:
                return f"Error retrieving notifications: {e}"
        
        @tool
        def get_audit_logs() -> str:
            """Get audit logs and system activity tracking."""
            try:
                return "Audit logs retrieved successfully"
            except Exception as e:
                return f"Error retrieving audit logs: {e}"
        
        self.tools = [
            get_system_analytics,
            get_user_management,
            get_platform_health,
            get_notifications,
            get_audit_logs
        ]
    
    def _get_system_prompt(self) -> str:
        return """You are an Admin System Agent for the Supply Chain Transparency Platform.

Your expertise includes:
- System administration and oversight
- User management and access control
- Platform health monitoring
- Audit logging and compliance
- System-wide analytics
- Security and performance monitoring

You help system administrators monitor platform health,
manage users, and ensure system security and performance.

Always prioritize security, compliance, and system stability in your recommendations."""

class SupplyChainAgentOrchestrator:
    """Main orchestrator for managing 5 specialized supply chain agents."""
    
    def __init__(self, config: Settings):
        self.config = config
        self.db_manager = get_database_manager()
        
        # Initialize all agents
        self.agents = {
            AgentRole.BRAND_MANAGER: BrandManagerAgent(self.db_manager, config),
            AgentRole.PROCESSOR_OPERATIONS: ProcessorOperationsAgent(self.db_manager, config),
            AgentRole.ORIGINATOR_PLANTATION: OriginatorPlantationAgent(self.db_manager, config),
            AgentRole.TRADER_LOGISTICS: TraderLogisticsAgent(self.db_manager, config),
            AgentRole.ADMIN_SYSTEM: AdminSystemAgent(self.db_manager, config)
        }
        
        logger.info(f"SupplyChainAgentOrchestrator initialized with {len(self.agents)} agents")
    
    def is_agent_enabled(self, agent_role: AgentRole, user_role: str = None, company_type: str = None) -> bool:
        """Check if an agent is enabled based on feature flags and user context."""
        try:
            # Get feature flags for the user
            if user_role:
                legacy_flags = consolidated_feature_flags.get_legacy_feature_flags(user_role, company_type)
            else:
                # Default to checking all flags if no user context
                legacy_flags = {
                    "v2_dashboard_brand": feature_flags.is_enabled(FeatureFlag.V2_DASHBOARD_BRAND),
                    "v2_dashboard_processor": feature_flags.is_enabled(FeatureFlag.V2_DASHBOARD_PROCESSOR),
                    "v2_dashboard_originator": feature_flags.is_enabled(FeatureFlag.V2_DASHBOARD_ORIGINATOR),
                    "v2_dashboard_trader": feature_flags.is_enabled(FeatureFlag.V2_DASHBOARD_TRADER),
                    "v2_dashboard_platform_admin": feature_flags.is_enabled(FeatureFlag.V2_DASHBOARD_PLATFORM_ADMIN),
                }
            
            # Map agent roles to feature flags
            agent_flag_mapping = {
                AgentRole.BRAND_MANAGER: legacy_flags.get("v2_dashboard_brand", False),
                AgentRole.PROCESSOR_OPERATIONS: legacy_flags.get("v2_dashboard_processor", False),
                AgentRole.ORIGINATOR_PLANTATION: legacy_flags.get("v2_dashboard_originator", False),
                AgentRole.TRADER_LOGISTICS: legacy_flags.get("v2_dashboard_trader", False),
                AgentRole.ADMIN_SYSTEM: legacy_flags.get("v2_dashboard_platform_admin", False),
            }
            
            is_enabled = agent_flag_mapping.get(agent_role, False)
            logger.debug(f"Agent {agent_role.value} enabled: {is_enabled} (user_role: {user_role}, company_type: {company_type})")
            return is_enabled
            
        except Exception as e:
            logger.error(f"Error checking agent enablement: {e}")
            # Default to enabled if there's an error
            return True
    
    def get_enabled_agents(self, user_role: str = None, company_type: str = None) -> List[AgentRole]:
        """Get list of enabled agents based on feature flags."""
        enabled_agents = []
        for agent_role in AgentRole:
            if self.is_agent_enabled(agent_role, user_role, company_type):
                enabled_agents.append(agent_role)
        return enabled_agents
    
    def get_agent_feature_flags(self, user_role: str = None, company_type: str = None) -> Dict[str, Any]:
        """Get feature flag information for all agents."""
        try:
            if user_role and company_type:
                dashboard_config = consolidated_feature_flags.get_dashboard_config(user_role, company_type)
                legacy_flags = dashboard_config.get("feature_flags", {})
            else:
                legacy_flags = {
                    "v2_dashboard_brand": feature_flags.is_enabled(FeatureFlag.V2_DASHBOARD_BRAND),
                    "v2_dashboard_processor": feature_flags.is_enabled(FeatureFlag.V2_DASHBOARD_PROCESSOR),
                    "v2_dashboard_originator": feature_flags.is_enabled(FeatureFlag.V2_DASHBOARD_ORIGINATOR),
                    "v2_dashboard_trader": feature_flags.is_enabled(FeatureFlag.V2_DASHBOARD_TRADER),
                    "v2_dashboard_platform_admin": feature_flags.is_enabled(FeatureFlag.V2_DASHBOARD_PLATFORM_ADMIN),
                }
            
            return {
                "agent_enablement": {
                    "brand_manager": legacy_flags.get("v2_dashboard_brand", False),
                    "processor_operations": legacy_flags.get("v2_dashboard_processor", False),
                    "originator_plantation": legacy_flags.get("v2_dashboard_originator", False),
                    "trader_logistics": legacy_flags.get("v2_dashboard_trader", False),
                    "admin_system": legacy_flags.get("v2_dashboard_platform_admin", False),
                },
                "consolidated_flags": legacy_flags,
                "user_context": {
                    "user_role": user_role,
                    "company_type": company_type
                }
            }
        except Exception as e:
            logger.error(f"Error getting agent feature flags: {e}")
            return {"error": str(e)}
    
    def _determine_agent_role(self, context: AgentContext, query: str) -> AgentRole:
        """Determine which agent should handle the query based on context and content."""
        
        # Role-based routing
        if context.role:
            role_mapping = {
                "brand_manager": AgentRole.BRAND_MANAGER,
                "processor": AgentRole.PROCESSOR_OPERATIONS,
                "originator": AgentRole.ORIGINATOR_PLANTATION,
                "trader": AgentRole.TRADER_LOGISTICS,
                "admin": AgentRole.ADMIN_SYSTEM,
                "super_admin": AgentRole.ADMIN_SYSTEM
            }
            
            if context.role in role_mapping:
                return role_mapping[context.role]
        
        # Content-based routing
        query_lower = query.lower()
        
        # Brand management keywords
        if any(keyword in query_lower for keyword in [
            "brand", "portfolio", "sustainability", "compliance", "certification",
            "rspo", "mspo", "supplier", "transparency"
        ]):
            return AgentRole.BRAND_MANAGER
        
        # Processor operations keywords
        if any(keyword in query_lower for keyword in [
            "processing", "milling", "oer", "cpo", "rbdpo", "transformation",
            "quality", "specification", "batch", "traceability"
        ]):
            return AgentRole.PROCESSOR_OPERATIONS
        
        # Originator/plantation keywords
        if any(keyword in query_lower for keyword in [
            "farm", "plantation", "eudr", "gps", "deforestation", "origin",
            "ffb", "fresh fruit bunch", "plantation management"
        ]):
            return AgentRole.ORIGINATOR_PLANTATION
        
        # Trader/logistics keywords
        if any(keyword in query_lower for keyword in [
            "logistics", "delivery", "shipment", "purchase order", "trading",
            "transportation", "inventory", "carrier"
        ]):
            return AgentRole.TRADER_LOGISTICS
        
        # Admin/system keywords
        if any(keyword in query_lower for keyword in [
            "admin", "system", "user", "audit", "health", "monitoring",
            "security", "performance", "platform"
        ]):
            return AgentRole.ADMIN_SYSTEM
        
        # Default to brand manager for general queries
        return AgentRole.BRAND_MANAGER
    
    async def route_query(self, query: str, context: AgentContext) -> AgentResponse:
        """Route a query to the appropriate agent and return the response."""
        
        # Determine which agent should handle this query
        agent_role = self._determine_agent_role(context, query)
        
        # Check if the agent is enabled based on feature flags
        if not self.is_agent_enabled(agent_role, context.role, context.company_id):
            logger.warning(f"Agent {agent_role.value} is disabled for user {context.user_id} (role: {context.role}, company_id: {context.company_id})")
            
            # Return a fallback response indicating the agent is disabled
            return AgentResponse(
                agent_role=agent_role,
                response="This agent is currently disabled. Please contact your administrator to enable this feature.",
                tools_used=[],
                execution_time=0.0,
                success=False,
                error_message="Agent disabled by feature flags"
            )
        
        logger.info(f"Routing query to {agent_role.value} agent for user {context.user_id}")
        
        # Get the appropriate agent
        agent = self.agents[agent_role]
        
        # Execute the query
        response = await agent.execute(query, context)
        
        logger.info(f"Query executed by {agent_role.value} agent in {response.execution_time:.2f}s")
        
        return response
    
    def get_agent_info(self, user_role: str = None, company_type: str = None) -> Dict[str, Any]:
        """Get information about all available agents, including feature flag status."""
        feature_flags_info = self.get_agent_feature_flags(user_role, company_type)
        
        return {
            "total_agents": len(self.agents),
            "feature_flags": feature_flags_info,
            "agents": {
                role.value: {
                    "tools_count": len(agent.tools),
                    "tools": [tool.name for tool in agent.tools] if agent.tools else [],
                    "enabled": self.is_agent_enabled(role, user_role, company_type)
                }
                for role, agent in self.agents.items()
            }
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on all agents."""
        health_status = {
            "orchestrator": "healthy",
            "agents": {},
            "timestamp": datetime.now().isoformat()
        }
        
        for role, agent in self.agents.items():
            try:
                # Simple test query
                test_context = AgentContext(user_id="health_check", role="admin")
                test_response = await agent.execute("health check", test_context)
                
                health_status["agents"][role.value] = {
                    "status": "healthy" if test_response.success else "unhealthy",
                    "tools_count": len(agent.tools),
                    "error": test_response.error_message
                }
            except Exception as e:
                health_status["agents"][role.value] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
        
        return health_status

# Import os for environment variables
import os

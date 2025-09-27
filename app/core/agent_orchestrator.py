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

# Import enhanced LangChain system
from .enhanced_langchain_system import EnhancedSupplyChainTools, SupplyChainMemoryManager, SupplyChainKnowledgeBase

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
    """Base class for all specialized agents with enhanced LangChain integration."""
    
    def __init__(self, role: AgentRole, db_manager, config: Settings):
        self.role = role
        self.db_manager = db_manager
        self.config = config
        self.tools = []
        
        # Initialize LLM
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.1,
            api_key=os.getenv("OPENAI_API_KEY")
        )
        
        # Initialize enhanced memory management
        self.memory_manager = SupplyChainMemoryManager(self.llm)
        self.memory = self.memory_manager.conversation_memory
        
        # Initialize knowledge base
        self.knowledge_base = SupplyChainKnowledgeBase(self.llm)
        
        # Initialize enhanced tools
        self.enhanced_tools = EnhancedSupplyChainTools(db_manager)
        
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
        """Execute a query using this agent with enhanced memory and knowledge base."""
        start_time = datetime.now()
        tools_used = []
        
        try:
            # Add context to memory
            self.memory_manager.add_context("user_context", context)
            self.memory_manager.add_context("query", query)
            
            # Get relevant context from memory
            relevant_context = self.memory_manager.get_relevant_context(query)
            
            # Enhance query with relevant context
            enhanced_query = query
            if relevant_context:
                context_info = "\n".join([f"{k}: {v}" for k, v in relevant_context.items()])
                enhanced_query = f"Context: {context_info}\n\nQuery: {query}"
            
            if self.agent_executor:
                response = await self.agent_executor.ainvoke({
                    "input": enhanced_query,
                    "chat_history": self.memory.chat_memory.messages
                })
                result = response.get("output", str(response))
                
                # Extract tools used from response if available
                if hasattr(response, 'intermediate_steps'):
                    tools_used = [step[0].tool for step in response.intermediate_steps]
            else:
                # Fallback to direct LLM call with knowledge base
                # Search knowledge base for relevant information
                knowledge_docs = self.knowledge_base.search_knowledge(query, k=2)
                knowledge_context = ""
                if knowledge_docs:
                    knowledge_context = "\n\nRelevant Knowledge:\n" + "\n".join([
                        f"- {doc.page_content}" for doc in knowledge_docs
                    ])
                
                messages = [
                    SystemMessage(content=self._get_system_prompt()),
                    HumanMessage(content=enhanced_query + knowledge_context)
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
        """Initialize brand management tools using enhanced LangChain system."""
        # Get all available tools from enhanced system
        all_tools = self.enhanced_tools.create_all_tools()
        
        # Filter tools relevant to brand management
        brand_tools = []
        for tool in all_tools:
            tool_name = tool.name.lower()
            if any(keyword in tool_name for keyword in [
                'certification', 'company_info', 'analytics', 'document', 
                'recommendation', 'dashboard', 'supply_chain'
            ]):
                brand_tools.append(tool)
        
        # Add knowledge base search tool
        @tool
        def search_knowledge_base(query: str) -> str:
            """Search supply chain knowledge base for best practices and documentation."""
            try:
                docs = self.knowledge_base.search_knowledge(query, k=3)
                if docs:
                    result = "Knowledge Base Results:\n"
                    for i, doc in enumerate(docs, 1):
                        result += f"{i}. {doc.page_content}\n"
                        result += f"   Source: {doc.metadata.get('source', 'unknown')}\n\n"
                    return result
                else:
                    return "No relevant information found in knowledge base."
            except Exception as e:
                return f"Error searching knowledge base: {e}"
        
        brand_tools.append(search_knowledge_base)
        self.tools = brand_tools
    
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
        """Initialize processor operations tools using enhanced LangChain system."""
        # Get all available tools from enhanced system
        all_tools = self.enhanced_tools.create_all_tools()
        
        # Filter tools relevant to processor operations
        processor_tools = []
        for tool in all_tools:
            tool_name = tool.name.lower()
            if any(keyword in tool_name for keyword in [
                'transformation', 'product', 'batch', 'trace', 'dashboard',
                'analytics', 'search', 'inventory'
            ]):
                processor_tools.append(tool)
        
        # Add knowledge base search tool
        @tool
        def search_knowledge_base(query: str) -> str:
            """Search supply chain knowledge base for processing best practices."""
            try:
                docs = self.knowledge_base.search_knowledge(query, k=3)
                if docs:
                    result = "Knowledge Base Results:\n"
                    for i, doc in enumerate(docs, 1):
                        result += f"{i}. {doc.page_content}\n"
                        result += f"   Source: {doc.metadata.get('source', 'unknown')}\n\n"
                    return result
                else:
                    return "No relevant information found in knowledge base."
            except Exception as e:
                return f"Error searching knowledge base: {e}"
        
        processor_tools.append(search_knowledge_base)
        self.tools = processor_tools
    
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
        """Initialize plantation management tools using enhanced LangChain system."""
        # Get all available tools from enhanced system
        all_tools = self.enhanced_tools.create_all_tools()
        
        # Filter tools relevant to plantation management
        plantation_tools = []
        for tool in all_tools:
            tool_name = tool.name.lower()
            if any(keyword in tool_name for keyword in [
                'farm_location', 'certification', 'batch', 'notification', 
                'alert', 'compliance', 'eudr'
            ]):
                plantation_tools.append(tool)
        
        # Add knowledge base search tool
        @tool
        def search_knowledge_base(query: str) -> str:
            """Search supply chain knowledge base for plantation and compliance best practices."""
            try:
                docs = self.knowledge_base.search_knowledge(query, k=3)
                if docs:
                    result = "Knowledge Base Results:\n"
                    for i, doc in enumerate(docs, 1):
                        result += f"{i}. {doc.page_content}\n"
                        result += f"   Source: {doc.metadata.get('source', 'unknown')}\n\n"
                    return result
                else:
                    return "No relevant information found in knowledge base."
            except Exception as e:
                return f"Error searching knowledge base: {e}"
        
        plantation_tools.append(search_knowledge_base)
        self.tools = plantation_tools
    
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
        """Initialize trading and logistics tools using enhanced LangChain system."""
        # Get all available tools from enhanced system
        all_tools = self.enhanced_tools.create_all_tools()
        
        # Filter tools relevant to trading and logistics
        logistics_tools = []
        for tool in all_tools:
            tool_name = tool.name.lower()
            if any(keyword in tool_name for keyword in [
                'purchase_order', 'delivery', 'shipment', 'inventory', 
                'logistics', 'analytics', 'trading'
            ]):
                logistics_tools.append(tool)
        
        # Add knowledge base search tool
        @tool
        def search_knowledge_base(query: str) -> str:
            """Search supply chain knowledge base for logistics and trading best practices."""
            try:
                docs = self.knowledge_base.search_knowledge(query, k=3)
                if docs:
                    result = "Knowledge Base Results:\n"
                    for i, doc in enumerate(docs, 1):
                        result += f"{i}. {doc.page_content}\n"
                        result += f"   Source: {doc.metadata.get('source', 'unknown')}\n\n"
                    return result
                else:
                    return "No relevant information found in knowledge base."
            except Exception as e:
                return f"Error searching knowledge base: {e}"
        
        logistics_tools.append(search_knowledge_base)
        self.tools = logistics_tools
    
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
        """Initialize admin system tools using enhanced LangChain system."""
        # Get all available tools from enhanced system
        all_tools = self.enhanced_tools.create_all_tools()
        
        # Filter tools relevant to admin system
        admin_tools = []
        for tool in all_tools:
            tool_name = tool.name.lower()
            if any(keyword in tool_name for keyword in [
                'analytics', 'dashboard', 'notification', 'user', 'system',
                'audit', 'health', 'management'
            ]):
                admin_tools.append(tool)
        
        # Add knowledge base search tool
        @tool
        def search_knowledge_base(query: str) -> str:
            """Search supply chain knowledge base for system administration best practices."""
            try:
                docs = self.knowledge_base.search_knowledge(query, k=3)
                if docs:
                    result = "Knowledge Base Results:\n"
                    for i, doc in enumerate(docs, 1):
                        result += f"{i}. {doc.page_content}\n"
                        result += f"   Source: {doc.metadata.get('source', 'unknown')}\n\n"
                    return result
                else:
                    return "No relevant information found in knowledge base."
            except Exception as e:
                return f"Error searching knowledge base: {e}"
        
        admin_tools.append(search_knowledge_base)
        self.tools = admin_tools
    
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

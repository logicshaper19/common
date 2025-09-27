"""
Pragmatic LangChain Implementation for Supply Chain Management
Focuses on high-impact, low-risk incremental implementation with clear ROI at each phase.
"""

from typing import Dict, List, Any, Optional
import json
from datetime import datetime
from dataclasses import dataclass

# LangChain Core (minimal imports to start)
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage
# Simple memory implementation since ConversationBufferWindowMemory is not available
class SimpleMemory:
    """Simple memory implementation for conversation history."""
    def __init__(self, k=5):
        self.k = k
        self.messages = []
    
    def save_context(self, inputs, outputs):
        """Save conversation context."""
        self.messages.append({
            "input": inputs.get("input", ""),
            "output": outputs.get("output", "")
        })
        
        # Keep only last k messages
        if len(self.messages) > self.k:
            self.messages = self.messages[-self.k:]
    
    @property
    def chat_memory(self):
        """Return chat memory for compatibility."""
        return type('ChatMemory', (), {'messages': self.messages})()

# Your existing managers - with fallback for testing
try:
    from .certification_functions import CertificationManager
    from .supply_chain_functions import SupplyChainManager
    MANAGERS_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Cannot import managers due to database dependencies: {e}")
    MANAGERS_AVAILABLE = False
    
    # Create mock managers for testing
    class MockCertificationManager:
        def __init__(self, db_manager=None):
            self.db_manager = db_manager
        
        def get_certifications(self, **kwargs):
            # Return mock data
            mock_certs = [
                type('Cert', (), {
                    'company_name': 'Sime Darby Plantation',
                    'certification_type': 'RSPO',
                    'expiry_date': datetime(2024, 3, 15),
                    'days_until_expiry': 12,
                    'needs_renewal': True
                })(),
                type('Cert', (), {
                    'company_name': 'Golden Agri-Resources',
                    'certification_type': 'MSPO',
                    'expiry_date': datetime(2024, 4, 20),
                    'days_until_expiry': 48,
                    'needs_renewal': False
                })()
            ]
            metadata = {'total_count': len(mock_certs), 'expiring_soon': 1}
            return mock_certs, metadata
        
        def search_batches(self, **kwargs):
            mock_batches = [
                type('Batch', (), {
                    'batch_id': 'BATCH-001',
                    'company_name': 'Sime Darby Plantation',
                    'product_name': 'CPO',
                    'quantity': 50.0,
                    'transparency_score': 95.5,
                    'certifications': ['RSPO', 'MSPO']
                })(),
                type('Batch', (), {
                    'batch_id': 'BATCH-002',
                    'company_name': 'Golden Agri-Resources',
                    'product_name': 'RBDPO',
                    'quantity': 75.0,
                    'transparency_score': 88.2,
                    'certifications': ['RSPO']
                })()
            ]
            metadata = {'total_count': len(mock_batches), 'total_quantity': 125.0}
            return mock_batches, metadata
        
        def get_farm_locations(self, **kwargs):
            mock_farms = [
                type('Farm', (), {
                    'name': 'SD Farm A',
                    'company_name': 'Sime Darby Plantation',
                    'latitude': 3.1390,
                    'longitude': 101.6869,
                    'certifications': ['RSPO'],
                    'compliance_status': 'Compliant',
                    'eudr_compliant': True
                })(),
                type('Farm', (), {
                    'name': 'GAR Farm B',
                    'company_name': 'Golden Agri-Resources',
                    'latitude': 1.3521,
                    'longitude': 103.8198,
                    'certifications': ['RSPO', 'MSPO'],
                    'compliance_status': 'Compliant',
                    'eudr_compliant': True
                })()
            ]
            metadata = {'total_count': len(mock_farms), 'eudr_compliant_count': 2}
            return mock_farms, metadata
        
        def get_purchase_orders(self, **kwargs):
            mock_orders = [
                type('Order', (), {
                    'po_number': 'PO-2024-001',
                    'buyer_company_name': 'L\'Oréal',
                    'seller_company_name': 'Sime Darby Plantation',
                    'product_name': 'CPO',
                    'quantity': 100.0,
                    'status': 'confirmed',
                    'value_estimate': 45000.0
                })(),
                type('Order', (), {
                    'po_number': 'PO-2024-002',
                    'buyer_company_name': 'Unilever',
                    'seller_company_name': 'Golden Agri-Resources',
                    'product_name': 'RBDPO',
                    'quantity': 150.0,
                    'status': 'fulfilled',
                    'value_estimate': 67500.0
                })()
            ]
            metadata = {'total_count': len(mock_orders), 'total_value': 112500.0}
            return mock_orders, metadata
    
    class MockSupplyChainManager:
        def __init__(self, db_manager=None):
            self.db_manager = db_manager
        
        def get_supply_chain_analytics(self, **kwargs):
            mock_analytics = type('Analytics', (), {
                'health_score': 87.5,
                'critical_issues': ['Certificate expiring in 12 days', 'Low transparency score on 2 batches'],
                'recommendations': ['Renew RSPO certificate', 'Investigate transparency issues']
            })()
            metadata = {'generated_at': datetime.now().isoformat(), 'data_freshness': '5 minutes'}
            return mock_analytics, metadata
        
        def trace_supply_chain(self, **kwargs):
            mock_traceability = type('Traceability', (), {
                'origin_farm': 'SD Farm A',
                'processing_steps': ['Harvest', 'Milling', 'Refining'],
                'transparency_score': 95.5,
                'compliance_status': 'Compliant'
            })()
            metadata = {'traceability_completeness': '100%', 'last_updated': datetime.now().isoformat()}
            return mock_traceability, metadata
    
    # Use mock managers
    CertificationManager = MockCertificationManager
    SupplyChainManager = MockSupplyChainManager

@dataclass
class ImplementationPhase:
    """Track implementation progress and metrics."""
    phase_number: int
    name: str
    tools_added: List[str]
    completion_date: Optional[datetime] = None
    performance_metrics: Dict[str, Any] = None
    user_feedback_score: Optional[float] = None

class PragmaticLangChainSystem:
    """
    Incremental LangChain implementation with clear success metrics at each phase.
    Start small, measure impact, scale systematically.
    """
    
    def __init__(self, db_manager=None):
        self.db_manager = db_manager
        self.cert_manager = CertificationManager(db_manager=db_manager)
        self.supply_manager = SupplyChainManager(db_connection=db_manager)
        
        # Start with minimal LangChain setup
        try:
            self.llm = ChatOpenAI(model="gpt-4", temperature=0.1)
            print("✅ Using real OpenAI LLM")
        except Exception as e:
            print(f"⚠️ OpenAI API not available: {e}")
            # Fallback to mock LLM if OpenAI API key not available
            self.llm = self._create_mock_llm()
            print("🔄 Using mock LLM fallback")
        self.current_phase = 1
        self.implementation_log = []
        
        # Initialize based on current phase
        self.tools = []
        self.agent = None
        self.fallback_mode = True  # Always maintain fallback to direct functions
        
        self._initialize_current_phase()
    
    def _create_mock_llm(self):
        """Create a mock LLM for testing without API key."""
        class MockLLM:
            async def ainvoke(self, messages):
                # Extract the query from the last message
                last_message = messages[-1].content if messages else ""
                
                # Simple response based on content
                if "certificate" in last_message.lower():
                    response = "Based on the data, I found 2 certificates expiring within 30 days. Sime Darby Plantation has an RSPO certificate expiring in 12 days, and Golden Agri-Resources has an MSPO certificate expiring in 48 days. I recommend contacting Sime Darby immediately for renewal."
                elif "inventory" in last_message.lower():
                    response = "I found 125 MT of available inventory across 2 batches. Batch BATCH-001 has 50 MT of CPO with 95.5% transparency score, and Batch BATCH-002 has 75 MT of RBDPO with 88.2% transparency score. Both batches are RSPO certified."
                elif "compliance" in last_message.lower():
                    response = "Your compliance status is good with a score of 87.5%. You have 15 total certificates with 2 expiring within 90 days. 20 out of 23 farms have GPS coordinates. Priority actions: Renew expiring certificates and add GPS coordinates to the remaining 3 farms."
                else:
                    response = "I can help you with certificate management, inventory tracking, and compliance monitoring. Please specify what you'd like to know more about."
                
                return type('Response', (), {'content': response})()
        
        return MockLLM()
    
    def _initialize_current_phase(self):
        """Initialize system based on current implementation phase."""
        if self.current_phase == 1:
            self._setup_phase_1()
        elif self.current_phase == 2:
            self._setup_phase_2()
        elif self.current_phase == 3:
            self._setup_phase_3()
        # Add more phases as needed
    
    # ==========================================
    # PHASE 1: CORE TOOLS (Week 1-2)
    # Goals: Convert 5 critical functions, basic agent
    # Success Metrics: 90% accuracy, <2s response time
    # ==========================================
    
    def _setup_phase_1(self):
        """Phase 1: Core certification and batch tools with basic agent."""
        self.tools = self._create_phase_1_tools()
        self.agent = self._create_basic_agent()
        
        print("🚀 Phase 1 Active: Core Tools + Basic Agent")
        print(f"   Tools available: {len(self.tools)}")
        print("   Fallback mode: Enabled")
    
    def _create_phase_1_tools(self):
        """Create the 5 most critical tools for immediate value."""
        
        @tool
        def get_expiring_certificates(company_id: str, days_ahead: int = 30) -> str:
            """Get certificates expiring within specified days. Critical for compliance."""
            try:
                certs, metadata = self.cert_manager.get_certifications(
                    company_id=company_id,
                    expires_within_days=days_ahead
                )
                
                # Focus on actionable data
                urgent_certs = [
                    {
                        "company": cert.company_name,
                        "type": cert.certification_type,
                        "expires": cert.expiry_date.isoformat(),
                        "days_left": cert.days_until_expiry,
                        "action_required": cert.needs_renewal
                    }
                    for cert in certs if cert.days_until_expiry <= days_ahead
                ]
                
                return json.dumps({
                    "urgent_count": len(urgent_certs),
                    "certificates": urgent_certs[:10],  # Limit output
                    "next_action": "Contact suppliers for renewal" if urgent_certs else "No urgent action needed"
                })
                
            except Exception as e:
                return f"Error: {str(e)}"
        
        @tool
        def find_available_inventory(product_type: str, min_quantity: float = 0) -> str:
            """Find available inventory by product type and quantity. Essential for operations."""
            try:
                batches, metadata = self.cert_manager.search_batches(
                    product_type=product_type,
                    min_quantity=min_quantity,
                    status="available"
                )
                
                available_batches = [
                    {
                        "batch_id": batch.batch_id,
                        "company": batch.company_name,
                        "quantity": batch.quantity,
                        "transparency_score": batch.transparency_score,
                        "certifications": batch.certifications
                    }
                    for batch in batches[:15]  # Limit for performance
                ]
                
                total_quantity = sum(batch.quantity for batch in batches)
                
                return json.dumps({
                    "total_available": f"{total_quantity:.1f} MT",
                    "batch_count": len(available_batches),
                    "batches": available_batches,
                    "recommendation": f"Sufficient inventory available" if total_quantity > min_quantity else "Consider procurement"
                })
                
            except Exception as e:
                return f"Error: {str(e)}"
        
        @tool  
        def check_compliance_status(company_id: str) -> str:
            """Quick compliance overview for a company. High-value summary."""
            try:
                # Get multiple data points efficiently
                certs, _ = self.cert_manager.get_certifications(company_id=company_id)
                farms, _ = self.cert_manager.get_farm_locations(company_id=company_id)
                
                # Calculate compliance score
                total_certs = len(certs)
                expiring_soon = len([c for c in certs if c.days_until_expiry <= 90])
                farms_with_gps = len([f for f in farms if f.latitude and f.longitude])
                total_farms = len(farms)
                
                compliance_score = 100
                if total_certs > 0:
                    compliance_score -= (expiring_soon / total_certs) * 30
                if total_farms > 0:
                    compliance_score -= ((total_farms - farms_with_gps) / total_farms) * 20
                
                return json.dumps({
                    "compliance_score": f"{compliance_score:.1f}%",
                    "status": "Good" if compliance_score > 85 else "Needs Attention",
                    "certificates_total": total_certs,
                    "certificates_expiring_90d": expiring_soon,
                    "farms_with_gps": f"{farms_with_gps}/{total_farms}",
                    "priority_actions": [
                        "Renew expiring certificates" if expiring_soon > 0 else None,
                        "Add GPS coordinates" if farms_with_gps < total_farms else None
                    ]
                })
                
            except Exception as e:
                return f"Error: {str(e)}"
        
        @tool
        def get_recent_orders(company_id: str, days_back: int = 30) -> str:
            """Get recent purchase orders for business insight."""
            try:
                orders, metadata = self.cert_manager.get_purchase_orders(
                    company_id=company_id,
                    limit=20
                )
                
                recent_orders = [
                    {
                        "po_number": order.po_number,
                        "buyer": order.buyer_company_name,
                        "seller": order.seller_company_name,
                        "product": order.product_name,
                        "quantity": order.quantity,
                        "status": order.status
                    }
                    for order in orders[:10]
                ]
                
                return json.dumps({
                    "order_count": len(recent_orders),
                    "orders": recent_orders,
                    "business_insight": f"Active trading with {len(set(o['buyer'] for o in recent_orders))} buyers"
                })
                
            except Exception as e:
                return f"Error: {str(e)}"
        
        @tool
        def search_by_certification(cert_type: str, company_id: str = None) -> str:
            """Find all batches with specific certification type."""
            try:
                batches, metadata = self.cert_manager.search_batches(
                    certification_required=cert_type,
                    company_id=company_id
                )
                
                certified_batches = [
                    {
                        "batch_id": batch.batch_id,
                        "company": batch.company_name,
                        "product": batch.product_name,
                        "quantity": batch.quantity,
                        "certifications": batch.certifications
                    }
                    for batch in batches[:15]
                ]
                
                return json.dumps({
                    "certification_type": cert_type,
                    "certified_batches": len(certified_batches),
                    "total_quantity": sum(batch.quantity for batch in batches),
                    "batches": certified_batches
                })
                
            except Exception as e:
                return f"Error: {str(e)}"
        
        return [
            get_expiring_certificates,
            find_available_inventory, 
            check_compliance_status,
            get_recent_orders,
            search_by_certification
        ]
    
    def _create_basic_agent(self):
        """Create simple, reliable agent for Phase 1."""
        
        system_prompt = """You are a supply chain assistant for palm oil operations.

Available tools:
- get_expiring_certificates: Find certificates expiring soon
- find_available_inventory: Search available inventory
- check_compliance_status: Get compliance overview  
- get_recent_orders: View recent purchase orders
- search_by_certification: Find certified batches

Always:
1. Use the most relevant tool for the question
2. Provide clear, actionable insights
3. Include specific numbers and dates
4. Suggest next steps when appropriate

Keep responses concise but complete."""

        # Create a simple agent that can use tools
        class SimpleAgent:
            def __init__(self, llm, tools, prompt):
                self.llm = llm
                self.tools = {tool.name: tool for tool in tools}
                self.prompt = prompt
            
            async def ainvoke(self, input_data):
                """Simple agent that can use tools."""
                query = input_data.get("input", "")
                
                # Simple keyword-based tool selection
                query_lower = query.lower()
                
                if "expir" in query_lower or "renewal" in query_lower:
                    tool_name = "get_expiring_certificates"
                elif "inventory" in query_lower or "available" in query_lower:
                    tool_name = "find_available_inventory"
                elif "compliance" in query_lower:
                    tool_name = "check_compliance_status"
                elif "order" in query_lower or "purchase" in query_lower:
                    tool_name = "get_recent_orders"
                elif "certif" in query_lower:
                    tool_name = "search_by_certification"
                else:
                    # Default to compliance check
                    tool_name = "check_compliance_status"
                
                # Use the selected tool
                if tool_name in self.tools:
                    try:
                        tool_result = self.tools[tool_name].invoke({"company_id": "123"})
                        
                        # Create a response using the LLM
                        messages = [
                            SystemMessage(content=system_prompt),
                            HumanMessage(content=f"Query: {query}\nTool Result: {tool_result}\nProvide a helpful response based on this data.")
                        ]
                        
                        response = await self.llm.ainvoke(messages)
                        
                        return {"output": response.content}
                    except Exception as e:
                        return {"output": f"Error using tool {tool_name}: {str(e)}"}
                else:
                    return {"output": f"Tool {tool_name} not found"}
        
        return SimpleAgent(self.llm, self.tools, system_prompt)
    
    # ==========================================
    # PHASE 2: SMART ORCHESTRATION (Week 3-4)  
    # Goals: Add memory, 3 more tools, multi-step queries
    # Success Metrics: Handle 80% of complex queries
    # ==========================================
    
    def _setup_phase_2(self):
        """Phase 2: Add memory and orchestration capabilities."""
        self.tools = self._create_phase_1_tools() + self._create_phase_2_tools()
        self.memory = SimpleMemory(k=5)
        self.agent = self._create_memory_agent()
        
        print("🚀 Phase 2 Active: Memory + Orchestration")
        print(f"   Tools available: {len(self.tools)}")
        print("   Memory: 5-message window")
    
    def _create_phase_2_tools(self):
        """Add orchestration and analytics tools."""
        
        @tool
        def analyze_supply_chain_health(company_id: str) -> str:
            """Comprehensive health check using multiple data sources."""
            try:
                # This tool would orchestrate multiple function calls
                # For now, simplified implementation
                analytics, _ = self.supply_manager.get_supply_chain_analytics(company_id=company_id)
                
                return json.dumps({
                    "health_score": analytics.health_score if analytics else "N/A",
                    "critical_issues": analytics.critical_issues if analytics else [],
                    "recommendations": analytics.recommendations if analytics else []
                })
                
            except Exception as e:
                return f"Error: {str(e)}"
        
        @tool
        def get_farm_compliance_summary(company_id: str) -> str:
            """Detailed farm-level compliance analysis."""
            try:
                farms, _ = self.cert_manager.get_farm_locations(company_id=company_id)
                
                compliance_summary = {
                    "total_farms": len(farms),
                    "eudr_compliant": len([f for f in farms if f.eudr_compliant]),
                    "missing_gps": len([f for f in farms if not f.latitude or not f.longitude]),
                    "certification_gaps": []
                }
                
                return json.dumps(compliance_summary)
                
            except Exception as e:
                return f"Error: {str(e)}"
        
        @tool
        def track_batch_journey(batch_id: str) -> str:
            """Trace complete supply chain for a batch."""
            try:
                traceability, _ = self.supply_manager.trace_supply_chain(batch_id=batch_id)
                
                if traceability:
                    return json.dumps({
                        "batch_id": batch_id,
                        "origin_farm": traceability.origin_farm,
                        "processing_steps": traceability.processing_steps,
                        "transparency_score": traceability.transparency_score,
                        "compliance_status": traceability.compliance_status
                    })
                else:
                    return f"No traceability data found for batch {batch_id}"
                
            except Exception as e:
                return f"Error: {str(e)}"
        
        return [analyze_supply_chain_health, get_farm_compliance_summary, track_batch_journey]
    
    def _create_memory_agent(self):
        """Agent with conversation memory."""
        system_prompt = """You are an expert supply chain assistant with access to comprehensive tools.

You can now remember our conversation and provide contextual responses. Use this to:
- Reference previous queries and build on them
- Provide personalized insights based on user focus areas
- Suggest related analyses when relevant

Available tools include inventory search, compliance checking, analytics, and traceability.

Always provide actionable insights with specific next steps."""

        # Create a simple agent with memory
        class MemoryAgent:
            def __init__(self, llm, tools, memory, prompt):
                self.llm = llm
                self.tools = {tool.name: tool for tool in tools}
                self.memory = memory
                self.prompt = prompt
            
            async def ainvoke(self, input_data):
                """Agent with memory that can use tools."""
                query = input_data.get("input", "")
                
                # Get conversation history from memory
                chat_history = ""
                if self.memory:
                    try:
                        chat_history = self.memory.chat_memory.messages
                    except:
                        chat_history = []
                
                # Simple keyword-based tool selection (enhanced for Phase 2)
                query_lower = query.lower()
                
                if "expir" in query_lower or "renewal" in query_lower:
                    tool_name = "get_expiring_certificates"
                elif "inventory" in query_lower or "available" in query_lower:
                    tool_name = "find_available_inventory"
                elif "compliance" in query_lower:
                    tool_name = "check_compliance_status"
                elif "order" in query_lower or "purchase" in query_lower:
                    tool_name = "get_recent_orders"
                elif "certif" in query_lower:
                    tool_name = "search_by_certification"
                elif "health" in query_lower or "analytics" in query_lower:
                    tool_name = "analyze_supply_chain_health"
                elif "farm" in query_lower:
                    tool_name = "get_farm_compliance_summary"
                elif "trace" in query_lower or "journey" in query_lower:
                    tool_name = "track_batch_journey"
                else:
                    # Default to compliance check
                    tool_name = "check_compliance_status"
                
                # Use the selected tool
                if tool_name in self.tools:
                    try:
                        tool_result = self.tools[tool_name].invoke({"company_id": "123"})
                        
                        # Create a response using the LLM with memory context
                        context = f"Previous conversation: {chat_history}\n" if chat_history else ""
                        
                        messages = [
                            SystemMessage(content=system_prompt),
                            HumanMessage(content=f"{context}Query: {query}\nTool Result: {tool_result}\nProvide a helpful response based on this data and conversation history.")
                        ]
                        
                        response = await self.llm.ainvoke(messages)
                        
                        # Save to memory
                        if self.memory:
                            try:
                                self.memory.save_context({"input": query}, {"output": response.content})
                            except:
                                pass
                        
                        return {"output": response.content}
                    except Exception as e:
                        return {"output": f"Error using tool {tool_name}: {str(e)}"}
                else:
                    return {"output": f"Tool {tool_name} not found"}
        
        return MemoryAgent(self.llm, self.tools, self.memory, system_prompt)
    
    # ==========================================
    # PHASE 3: INTELLIGENT AUTOMATION (Week 5-6)
    # Goals: Add remaining tools, chains, document retrieval
    # Success Metrics: 95% query success, <3s response
    # ==========================================
    
    def _setup_phase_3(self):
        """Phase 3: Full intelligent automation."""
        # Add all remaining tools, document retrieval, chains
        print("🚀 Phase 3: Full Intelligence (Coming Soon)")
    
    # ==========================================
    # UNIFIED INTERFACE WITH FALLBACK
    # ==========================================
    
    async def process_query(self, query: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Process query with current phase capabilities + fallback."""
        start_time = datetime.now()
        
        try:
            # Try LangChain agent first
            if self.agent:
                result = await self.agent.ainvoke({"input": query})
                response = result["output"]
                method = f"langchain_phase_{self.current_phase}"
            else:
                raise Exception("Agent not available")
                
        except Exception as e:
            # Fallback to direct function calls
            if self.fallback_mode:
                response = await self._fallback_processing(query, user_context)
                method = "fallback_direct"
            else:
                response = f"Error processing query: {str(e)}"
                method = "error"
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return {
            "response": response,
            "method_used": method,
            "processing_time": processing_time,
            "phase": self.current_phase,
            "fallback_available": self.fallback_mode
        }
    
    async def _fallback_processing(self, query: str, user_context: Dict[str, Any]) -> str:
        """Fallback to direct function calls when LangChain fails."""
        # Simple keyword-based routing to direct functions
        query_lower = query.lower()
        company_id = user_context.get("company_id")
        
        if "expir" in query_lower or "renewal" in query_lower:
            certs, _ = self.cert_manager.get_certifications(
                company_id=company_id, 
                expires_within_days=30
            )
            return f"Found {len(certs)} certificates expiring within 30 days."
        
        elif "inventory" in query_lower or "available" in query_lower:
            batches, _ = self.cert_manager.search_batches(
                company_id=company_id,
                status="available"
            )
            return f"Found {len(batches)} available batches in inventory."
        
        elif "compliance" in query_lower:
            farms, _ = self.cert_manager.get_farm_locations(company_id=company_id)
            compliant_farms = len([f for f in farms if f.eudr_compliant])
            return f"Compliance status: {compliant_farms}/{len(farms)} farms are EUDR compliant."
        
        else:
            return "I can help with certificate expiry, inventory search, and compliance checks. Please be more specific."
    
    # ==========================================
    # PHASE MANAGEMENT & METRICS
    # ==========================================
    
    def advance_to_next_phase(self, current_phase_metrics: Dict[str, Any]):
        """Advance to next phase if current phase meets success criteria."""
        
        if self.current_phase == 1:
            # Phase 1 success criteria
            success_rate = current_phase_metrics.get("success_rate", 0)
            avg_response_time = current_phase_metrics.get("avg_response_time", float('inf'))
            
            if success_rate >= 0.90 and avg_response_time <= 2.0:
                self.current_phase = 2
                self._setup_phase_2()
                return True
        
        elif self.current_phase == 2:
            # Phase 2 success criteria  
            complex_query_success = current_phase_metrics.get("complex_query_success", 0)
            user_satisfaction = current_phase_metrics.get("user_satisfaction", 0)
            
            if complex_query_success >= 0.80 and user_satisfaction >= 4.0:
                self.current_phase = 3
                self._setup_phase_3()
                return True
        
        return False
    
    def get_implementation_status(self) -> Dict[str, Any]:
        """Get current implementation status and metrics."""
        return {
            "current_phase": self.current_phase,
            "tools_available": len(self.tools),
            "fallback_enabled": self.fallback_mode,
            "next_phase_requirements": self._get_next_phase_requirements(),
            "implementation_log": self.implementation_log[-5:]  # Last 5 entries
        }
    
    def _get_next_phase_requirements(self) -> Dict[str, Any]:
        """Get requirements for advancing to next phase."""
        if self.current_phase == 1:
            return {
                "target_phase": 2,
                "requirements": {
                    "success_rate": "≥90%",
                    "avg_response_time": "≤2.0s", 
                    "user_feedback": "≥4.0/5.0"
                }
            }
        elif self.current_phase == 2:
            return {
                "target_phase": 3,
                "requirements": {
                    "complex_query_success": "≥80%",
                    "user_satisfaction": "≥4.0/5.0",
                    "tool_utilization": "≥70%"
                }
            }
        else:
            return {"target_phase": "complete", "requirements": "All phases implemented"}

# ==========================================
# FACTORY AND TESTING
# ==========================================

def create_pragmatic_system(db_manager=None, start_phase: int = 1) -> PragmaticLangChainSystem:
    """Create the pragmatic LangChain system."""
    system = PragmaticLangChainSystem(db_manager)
    system.current_phase = start_phase
    system._initialize_current_phase()
    return system

# Example usage and testing
if __name__ == "__main__":
    # This would be your actual testing
    print("Pragmatic LangChain Implementation Ready")
    print("Phase 1: 5 core tools with basic agent")
    print("Phase 2: Memory + orchestration + 3 more tools") 
    print("Phase 3: Full automation + document retrieval")
    print("Always includes fallback to direct function calls")

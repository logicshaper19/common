"""
Enhanced LangChain-powered supply chain assistant for the Common platform.
Provides sophisticated AI responses with comprehensive supply chain context and temperature-aware prompting.
"""

import os
from typing import Dict, Any, List
from app.core.logging import get_logger
from app.core.supply_chain_prompts import EnhancedSupplyChainPrompts, InteractionType
from app.core.schema_context import SupplyChainSchemaContext
from app.core.enhanced_context_builder import EnhancedUserContextBuilder

logger = get_logger(__name__)

# Try to import LangChain components, fallback to simple implementation if not available
try:
    from langchain_openai import ChatOpenAI
    from langchain_core.messages import HumanMessage, SystemMessage
    LANGCHAIN_AVAILABLE = True
except ImportError as e:
    logger.warning(f"LangChain not available: {e}")
    LANGCHAIN_AVAILABLE = False


class SupplyChainLangChainAssistant:
    """Temperature-aware LangChain-powered supply chain assistant."""
    
    def __init__(self):
        """Initialize the LangChain assistant with temperature-aware prompting."""
        if not LANGCHAIN_AVAILABLE:
            raise ImportError("LangChain dependencies not available")
            
        try:
            # Initialize prompt system
            self.prompts = EnhancedSupplyChainPrompts()
            self.schema_context = SupplyChainSchemaContext()
            self.context_builder = EnhancedUserContextBuilder()
            
            logger.info("Schema-aware LangChain assistant initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize LangChain assistant: {e}")
            raise

    async def get_response(self, user_message: str, user_context: Dict[str, Any], chat_history: str = "") -> str:
        """Generate temperature-appropriate responses using dynamic temperature adjustment."""
        
        try:
            # Build enhanced context with schema awareness
            enhanced_context = self.context_builder.build_schema_aware_context(user_context)
            
            # Classify interaction type and get appropriate temperature
            interaction_type, temperature = self.prompts.classify_interaction_type(user_message, enhanced_context)
            
            # Create LLM with appropriate temperature
            llm = ChatOpenAI(
                model="gpt-3.5-turbo",
                temperature=temperature,
                openai_api_key=os.getenv("OPENAI_API_KEY"),
                max_tokens=1000
            )
            
            # Get enhanced system prompt
            system_prompt = self.prompts.get_enhanced_system_prompt()
            
            # Add interaction-specific context
            context_prompt = self.prompts.get_conversation_context_prompt(interaction_type)
            
            # Get schema-aware system prompt
            schema_prompt = self.prompts.get_schema_aware_system_prompt()
            
            # Build complete prompt with enhanced schema context
            enhanced_context_prompt = self.context_builder.get_context_for_ai_prompt(enhanced_context)
            
            complete_prompt = f"""
{schema_prompt}

## Current Interaction Classification:
Type: {interaction_type.value}
Temperature: {temperature} ({self._get_temperature_mode(temperature)} Mode)

{enhanced_context_prompt}

## Real-Time Supply Chain Data Context:
- Inventory: {enhanced_context.get('inventory_summary', 'No data available')}
- Purchase Orders: {enhanced_context.get('recent_pos', 'No data available')}
- Transparency: {enhanced_context.get('transparency_score', 'No data available')}
- Compliance: {enhanced_context.get('compliance_status', 'No data available')}

## User Request:
{user_message}

## Response Guidelines for This Interaction:
{self._get_temperature_specific_guidelines(temperature)}
"""

            messages = [
                SystemMessage(content=complete_prompt),
                HumanMessage(content=user_message)
            ]
            
            response = await llm.ainvoke(messages)
            
            # Add interaction type metadata to response for debugging
            response_with_metadata = response.content
            
            # In debug mode, show temperature classification
            if os.getenv("DEBUG") == "True":
                response_with_metadata += f"\n\n_Debug: {interaction_type.value} mode (temp: {temperature})_"
            
            logger.info(f"LangChain response generated in {interaction_type.value} mode (temp: {temperature})")
            return response_with_metadata
            
        except Exception as e:
            logger.error(f"Error generating LangChain response: {e}")
            return self._get_fallback_response(user_message, str(e), user_context)
    
    def _get_temperature_mode(self, temperature: float) -> str:
        """Get temperature mode description."""
        if temperature <= 0.3:
            return "Precision"
        elif temperature <= 0.6:
            return "Analytical"
        elif temperature <= 0.7:
            return "Strategic"
        else:
            return "Creative"
    
    def _get_temperature_specific_guidelines(self, temperature: float) -> str:
        """Get specific response guidelines based on temperature."""
        
        if temperature <= 0.3:
            return """
- Be precise and factual - no approximations
- Reference specific standards and regulations  
- Provide exact measurements and calculations
- Acknowledge when data verification is needed"""
        
        elif temperature <= 0.6:
            return """
- Provide balanced analysis with clear reasoning
- Compare against industry benchmarks
- Show step-by-step logic for recommendations
- Consider multiple relevant factors"""
        
        elif temperature <= 0.7:
            return """
- Offer 2-3 strategic alternatives with trade-offs
- Think long-term with market considerations
- Integrate business context and constraints
- Suggest phased implementation approaches"""
        
        else:
            return """
- Generate multiple creative alternatives
- Think outside conventional approaches
- Consider innovative technologies and practices
- Provide adaptive, flexible solutions"""
    
    def _get_fallback_response(self, user_message: str, error: str, user_context: dict) -> str:
        """Provide appropriate fallback based on message content."""
        
        if any(keyword in user_message.lower() for keyword in ["urgent", "emergency", "compliance", "audit"]):
            return "I'm experiencing technical difficulties processing your urgent request. Please contact your supply chain manager immediately or check the compliance dashboard directly."
        
        company_name = user_context.get('company_name', 'your company')
        return f"I'm having trouble processing your supply chain request. Please try rephrasing your question or check the relevant dashboard section for immediate information about {company_name}."


class SupplyChainTools:
    """LangChain tools that interact with your existing APIs."""
    
    def __init__(self, db_session, current_user):
        self.db = db_session
        self.current_user = current_user
    
    async def get_inventory_data(self, query: str = "") -> str:
        """Get inventory information for the user's company."""
        try:
            # Use your existing inventory logic
            from app.api.inventory import get_inventory
            
            inventory_result = await get_inventory(
                batch_status=['available', 'reserved', 'allocated'],
                current_user=self.current_user,
                db=self.db
            )
            
            summary = inventory_result.get('summary', {})
            return f"Current inventory: {summary.get('total_batches', 0)} batches, {summary.get('available_quantity', 0)} MT available"
            
        except Exception as e:
            logger.error(f"Error retrieving inventory data: {e}")
            return f"Error retrieving inventory: {str(e)}"
    
    async def get_transparency_data(self, batch_id: str = "") -> str:
        """Get traceability information for batches."""
        try:
            # Get batches with transparency scores
            from app.models.batch import Batch
            
            batches = self.db.query(Batch).filter(
                Batch.company_id == self.current_user.company_id
            ).limit(5).all()
            
            if not batches:
                return "No batches found for transparency analysis"
            
            # Mock transparency calculation (you can replace with real logic)
            transparency_scores = []
            for batch in batches:
                score = 85.0 + (hash(batch.batch_id) % 15)  # Mock score between 85-100
                transparency_scores.append(f"Batch {batch.batch_id}: {score:.1f}%")
            
            return f"Transparency scores: {'; '.join(transparency_scores)}"
            
        except Exception as e:
            logger.error(f"Error retrieving transparency data: {e}")
            return f"Error retrieving transparency data: {str(e)}"
    
    async def get_po_data(self, query: str = "") -> str:
        """Get purchase order information."""
        try:
            from app.models.purchase_order import PurchaseOrder
            
            # Get recent POs
            recent_pos = self.db.query(PurchaseOrder).filter(
                PurchaseOrder.buyer_company_id == self.current_user.company_id
            ).limit(3).all()
            
            if not recent_pos:
                return "No recent purchase orders found"
            
            po_info = []
            for po in recent_pos:
                po_info.append(f"PO {po.po_number}: {po.status} - {po.quantity} MT")
            
            return f"Recent POs: {'; '.join(po_info)}"
            
        except Exception as e:
            logger.error(f"Error retrieving PO data: {e}")
            return f"Error retrieving PO data: {str(e)}"


# Create a fallback class when LangChain is not available
class SimpleSupplyChainAssistant:
    """Simple fallback assistant when LangChain is not available."""
    
    def __init__(self):
        logger.info("Using simple supply chain assistant (LangChain not available)")
    
    async def get_response(self, user_message: str, user_context: Dict[str, Any]) -> str:
        """Get simple AI response without LangChain."""
        try:
            # Use the existing OpenAI client
            from app.core.openai_client import SimpleOpenAIClient
            
            ai_client = SimpleOpenAIClient()
            response = await ai_client.generate_response(
                user_message=user_message,
                context_data=user_context,
                user_name=user_context.get('user_name', 'User')
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error in simple assistant: {e}")
            return f"I'm having trouble processing your request right now. Please try again or check your specific dashboard sections for {user_context.get('company_type', 'your operations')}."
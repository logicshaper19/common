"""
OpenAI Client for AI-powered responses
"""
import os
import openai
from typing import Dict, Any, Optional
from app.core.logging import get_logger
from app.core.environment_config import get_environment_config

logger = get_logger(__name__)

class SimpleOpenAIClient:
    """Simple OpenAI client for generating AI responses with context."""
    
    def __init__(self):
        """Initialize OpenAI client with API key from environment config."""
        # Try environment variable first, then config
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            try:
                config = get_environment_config()
                self.api_key = config.openai.api_key
            except Exception as e:
                logger.warning(f"Could not load OpenAI config: {e}")
        
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables or config")
        
        openai.api_key = self.api_key
        self.client = openai.OpenAI(api_key=self.api_key)
        
        # Get config for model settings
        try:
            config = get_environment_config()
            self.model = config.openai.model
            self.max_tokens = config.openai.max_tokens
            self.temperature = config.openai.temperature
        except Exception:
            # Fallback defaults
            self.model = "gpt-3.5-turbo"
            self.max_tokens = 500
            self.temperature = 0.7
    
    async def generate_response(
        self, 
        user_message: str, 
        context_data: Dict[str, Any], 
        user_name: str = "User"
    ) -> str:
        """
        Generate AI response using OpenAI with supply chain context.
        
        Args:
            user_message: The user's input message
            context_data: Supply chain context data (company, inventory, etc.)
            user_name: Name of the user for personalization
            
        Returns:
            AI-generated response string
        """
        try:
            # Build context-aware system prompt
            system_prompt = self._build_system_prompt(context_data, user_name)
            
            # Create messages for OpenAI
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ]
            
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                top_p=1.0,
                frequency_penalty=0.0,
                presence_penalty=0.0
            )
            
            ai_response = response.choices[0].message.content.strip()
            logger.info(f"OpenAI response generated for user {user_name}")
            
            return ai_response
            
        except Exception as e:
            logger.error(f"Error generating OpenAI response: {e}")
            # Fallback to a helpful response
            return self._get_fallback_response(user_message, context_data, user_name)
    
    def _build_system_prompt(self, context_data: Dict[str, Any], user_name: str) -> str:
        """Build a comprehensive system prompt with supply chain context."""
        
        company_name = context_data.get("company_name", "your company")
        company_type = context_data.get("company_type", "unknown")
        
        # Get additional context data
        inventory_data = context_data.get("inventory", {})
        po_data = context_data.get("purchase_orders", {})
        transparency_data = context_data.get("transparency", {})
        compliance_data = context_data.get("compliance", {})
        company_data = context_data.get("company_relationships", {})
        processing_data = context_data.get("processing", {})
        
        system_prompt = f"""You are an AI assistant for {company_name}, a {company_type} in the palm oil supply chain. You help users with supply chain management, traceability, compliance, and operations.

**Company Context:**
- Company: {company_name}
- Type: {company_type}
- User: {user_name}

**Current Data:**
- Inventory: {inventory_data.get('total_batches', 0)} batches, {inventory_data.get('available_quantity', 0):.1f} MT available
- Purchase Orders: {po_data.get('pending_pos', 0)} pending, {po_data.get('confirmed_pos', 0)} confirmed
- Transparency: {transparency_data.get('average_score', 0):.1f}% average score, {transparency_data.get('compliant_batches', 0)}/{transparency_data.get('total_batches', 0)} compliant
- Compliance: EUDR {compliance_data.get('eudr_compliant', 0)}/{compliance_data.get('total_batches', 0)}, RSPO {compliance_data.get('rspo_compliant', 0)}/{compliance_data.get('total_batches', 0)}
- Processing: {processing_data.get('processing_batches', 0)} processing batches
- Relationships: {company_data.get('total_relationships', 0)} trading partners

**Your Role:**
- Provide helpful, accurate information about supply chain operations
- Use the real data provided to give specific, actionable insights
- Be professional but conversational
- Focus on palm oil supply chain expertise (traceability, compliance, processing, trading)
- Suggest specific actions and next steps
- If you don't have specific data, guide users to the right tools or pages

**Response Style:**
- Use emojis appropriately (📦 for inventory, 📋 for POs, 🔍 for traceability, etc.)
- Be specific about numbers and metrics when available
- Provide actionable next steps
- Keep responses concise but informative
- Use the user's name for personalization

**Supply Chain Expertise:**
- Palm oil products: FFB, CPO, RBDPO, PKO, etc.
- Processing: Milling, refining, crushing operations
- Compliance: EUDR, RSPO, sustainability standards
- Traceability: Supply chain visibility, GPS tracking, documentation
- Trading: Purchase orders, contracts, delivery, quality specifications

Always be helpful, accurate, and focused on practical supply chain management."""
        
        return system_prompt
    
    def _get_fallback_response(self, user_message: str, context_data: Dict[str, Any], user_name: str) -> str:
        """Provide a fallback response when OpenAI is unavailable."""
        
        company_name = context_data.get("company_name", "your company")
        company_type = context_data.get("company_type", "supply chain company")
        
        # Simple keyword-based fallback
        message_lower = user_message.lower()
        
        if "inventory" in message_lower:
            return f"Hi {user_name}! I can help you with inventory management for {company_name}. You can check your current stock levels, create new batches, or allocate inventory to purchase orders. What specifically would you like to know about your inventory?"
        
        elif "purchase order" in message_lower or "po" in message_lower:
            return f"I can help you with purchase orders for {company_name}. You can check PO status, create new purchase orders, or track fulfillment. What would you like to do with purchase orders?"
        
        elif "traceability" in message_lower or "transparency" in message_lower:
            return f"I can help you check traceability and transparency scores for your batches at {company_name}. This includes supply chain visibility, EUDR compliance, and sustainability metrics. Which batch or supplier would you like to check?"
        
        elif "compliance" in message_lower:
            return f"I can help you with compliance requirements for {company_name} including EUDR (European Union Deforestation Regulation), RSPO (Roundtable on Sustainable Palm Oil), and other regulatory standards. What specific compliance area would you like to explore?"
        
        else:
            return f"Hello {user_name}! I'm your supply chain assistant for {company_name} ({company_type}). I can help you with inventory, purchase orders, traceability, compliance, and processing operations. Could you be more specific about what you'd like to know?"

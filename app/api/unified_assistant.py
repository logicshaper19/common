"""
Unified AI Assistant that handles both regular and streaming responses
Based on your .env configuration and supply chain platform
"""
from typing import Dict, Any, AsyncGenerator, Optional
from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
import json
import os
import re
import asyncio
from datetime import datetime

from app.core.database import get_db
from app.core.auth import get_current_user, CurrentUser
from app.core.advanced_prompts import AdvancedSupplyChainPrompts, ResponseMode
from app.core.openai_client import SimpleOpenAIClient
from app.core.schema_context import SupplyChainSchemaContext
from app.models.purchase_order import PurchaseOrder
from app.models.company import Company
from app.models.product import Product
from app.models.batch import Batch
from app.models.po_batch_linkage import POBatchLinkage

router = APIRouter(prefix="/assistant", tags=["unified-assistant"])

class ChatRequest(BaseModel):
    message: str
    stream: bool = False

class UnifiedSupplyChainAssistant:
    """Intelligent AI assistant with full system access and context awareness."""
    
    def __init__(self, db: Session, current_user: CurrentUser):
        self.db = db
        self.user = current_user
        self.app_name = os.getenv("APP_NAME", "Common Supply Chain Platform")
        self.transparency_factor = float(os.getenv("TRANSPARENCY_DEGRADATION_FACTOR", "0.95"))
        self.openai_client = SimpleOpenAIClient()
        self.prompts = AdvancedSupplyChainPrompts()
        self.schema_context = SupplyChainSchemaContext()
        self.conversation_memory = []  # Track conversation context
        
    def detect_po_query(self, message: str) -> Optional[str]:
        """Detect PO number in message with multiple patterns."""
        patterns = [
            r'PO[#\s-]*(\d{6}-\d{4})',  # PO-202509-0001
            r'#PO-(\d{6}-\d{4})',       # #PO-202509-0001
            r'(\d{6}-\d{4})',           # Just the number pattern
        ]
        
        for pattern in patterns:
            match = re.search(pattern, message.upper().replace(' ', ''))
            if match:
                return match.group(1)
        return None
    
    async def get_po_data(self, po_identifier: str) -> Optional[Dict[str, Any]]:
        """Get actual PO data from your database."""
        try:
            # Try exact match first
            po = self.db.query(PurchaseOrder).filter(
                PurchaseOrder.po_number == f"PO-{po_identifier}"
            ).first()
            
            if not po:
                # Try without PO- prefix
                po = self.db.query(PurchaseOrder).filter(
                    PurchaseOrder.po_number == po_identifier
                ).first()
            
            if not po:
                return None
                
            # Fetch related batch data with coordinates
            related_batches = await self._get_po_batch_coordinates(po.id)
            
            return {
                "po_number": po.po_number,
                "buyer": po.buyer_company.name if po.buyer_company else "Unknown",
                "seller": po.seller_company.name if po.seller_company else "Unknown", 
                "product": po.product.name if po.product else "Unknown",
                "quantity": float(po.quantity or 0),
                "unit_price": float(po.unit_price or 0),
                "total_amount": float(po.total_amount or 0),
                "status": po.status,
                "delivery_date": po.delivery_date.strftime("%Y-%m-%d") if po.delivery_date else None,
                "delivery_location": po.delivery_location,
                "user_role": "buyer" if po.buyer_company_id == self.user.company_id else "seller",
                "created_date": po.created_at.strftime("%Y-%m-%d") if po.created_at else None,
                "batch_coordinates": related_batches,
                "origin_data": po.origin_data  # Direct origin coordinates if available
            }
        except Exception as e:
            print(f"Error querying PO: {e}")
            return None
    
    async def _get_po_batch_coordinates(self, po_id: str) -> Dict[str, Any]:
        """Fetch batch coordinates related to a PO."""
        try:
            # Query batches linked to this PO
            batch_links = self.db.query(POBatchLinkage).filter(
                POBatchLinkage.purchase_order_id == po_id
            ).all()
            
            coordinates = []
            for link in batch_links:
                batch = self.db.query(Batch).filter(Batch.id == link.batch_id).first()
                if batch and batch.location_coordinates:
                    coordinates.append({
                        "batch_id": str(batch.id),
                        "batch_name": batch.batch_name,
                        "location_name": batch.location_name,
                        "coordinates": batch.location_coordinates,
                        "quantity_allocated": float(link.quantity_allocated or 0)
                    })
            
            return {
                "total_coordinate_sources": len(coordinates),
                "batch_locations": coordinates,
                "has_gps_data": len(coordinates) > 0
            }
            
        except Exception as e:
            print(f"Error fetching batch coordinates: {e}")
            return {"total_coordinate_sources": 0, "batch_locations": [], "has_gps_data": False}
    
    async def generate_response(self, message: str) -> str:
        """Generate intelligent AI response with full system access and context awareness."""
        
        # Add message to conversation memory
        self.conversation_memory.append({
            "role": "user", 
            "content": message,
            "timestamp": datetime.now().isoformat()
        })
        
        # Build comprehensive system context
        full_context = await self._build_comprehensive_context(message)
        
        # Generate AI response with complete system awareness
        response = await self._generate_system_aware_response(message, full_context)
        
        # Add AI response to conversation memory
        self.conversation_memory.append({
            "role": "assistant",
            "content": response,
            "timestamp": datetime.now().isoformat()
        })
        
        return response
    
    async def _build_comprehensive_context(self, message: str) -> Dict[str, Any]:
        """Build complete context including schemas, conversation history, and relevant data."""
        
        # Base user context
        context = {
            "user_info": {
                "first_name": self.user.user.full_name or "User",
                "company_name": self.user.company.name,
                "company_type": getattr(self.user.company, 'company_type', 'unknown'),
                "company_id": str(self.user.company.id)
            },
            "conversation_history": self.conversation_memory[-10:],  # Last 10 messages
            "database_schema": self.schema_context.get_schema_context(),
            "current_message": message
        }
        
        # Intelligent data fetching based on message content and conversation context
        await self._add_relevant_data_to_context(message, context)
        
        return context
    
    async def _add_relevant_data_to_context(self, message: str, context: Dict[str, Any]):
        """Intelligently fetch relevant data based on message and conversation context."""
        
        # Check for PO references (current message or recent conversation)
        po_identifier = self.detect_po_query(message)
        
        # Also check conversation history for recent PO context
        if not po_identifier:
            po_identifier = self._extract_po_from_conversation_context()
        
        if po_identifier:
            po_data = await self.get_po_data(po_identifier)
            if po_data:
                context["current_po"] = po_data
                context["query_context"] = "purchase_order_related"
        
        # Add more intelligent data fetching here:
        # - Company data if mentioned
        # - Product data if mentioned  
        # - Recent batches if relevant
        # - etc.
        
        # For now, always include user's company context
        context["user_company_context"] = {
            "company_name": self.user.company.name,
            "company_type": getattr(self.user.company, 'company_type', 'unknown')
        }
    
    def _extract_po_from_conversation_context(self) -> Optional[str]:
        """Extract PO number from recent conversation if current message refers to it."""
        
        # Look for PO numbers in recent conversation
        for msg in reversed(self.conversation_memory[-5:]):  # Last 5 messages
            if msg["role"] == "user":
                po_id = self.detect_po_query(msg["content"])
                if po_id:
                    # Check if current message seems related to that PO
                    current_lower = self.conversation_memory[-1]["content"].lower()
                    po_related_terms = [
                        "delivery", "due", "date", "when", "status", "buyer", "seller",
                        "quantity", "price", "location", "created", "total", "value"
                    ]
                    
                    if any(term in current_lower for term in po_related_terms):
                        return po_id
        
        return None
    
    async def _generate_system_aware_response(self, message: str, context: Dict[str, Any]) -> str:
        """Generate AI response with full system awareness and context."""
        try:
            # Build comprehensive system prompt with schema awareness
            system_prompt = f"""You are a direct, data-focused AI assistant for {self.app_name}, a palm oil supply chain platform.

CRITICAL INSTRUCTIONS:
1. ALWAYS answer questions directly with specific data when available
2. Provide contextual narrative that relates to the specific data being discussed
3. When user asks for specific information, provide the EXACT VALUE first, then relevant context
4. NO emojis, NO generic lectures, NO unrelated business commentary
5. Be factual but conversational - DATA FIRST, then contextual insights
6. Focus narrative on what the data means for THIS specific situation

FORMATTING REQUIREMENTS:
- Use ALL CAPS for section headers (e.g., PURCHASE ORDER DETAILS:)
- Add proper spacing between sections with double line breaks  
- Use clean, structured layout with clear hierarchy
- Keep data concise but well-organized
- NO markdown formatting since frontend doesn't render it

CURRENT DATA CONTEXT:
{self._format_current_context(context)}

CONVERSATION HISTORY:
{context.get('conversation_history', [])}

USER CONTEXT:
- User: {context['user_info']['first_name']} at {context['user_info']['company_name']}

EXAMPLE RESPONSES (GOOD):
User: "What can you tell me about PO #PO-202509-0001?"
You: "PURCHASE ORDER DETAILS:
- PO Number: PO-202509-0001
- Seller: Plantation Estate Sdn Bhd
- Buyer: Tani Maju Cooperative
- Product: Fresh Fruit Bunches (FFB)
- Quantity: 10000.0 MT
- Unit Price: $2.00
- Total Value: $20000.00
- Status: Confirmed
- Delivery Date: 2025-09-24
- Delivery Location: PARIS
- Created: 2025-09-23

This is a significant FFB order worth $20,000 between your plantation and Tani Maju Cooperative. The delivery is scheduled for tomorrow (2025-09-24) to Paris, which suggests this batch is destined for European processing facilities.

BATCH COORDINATE DATA:
- GPS Data Available: [True/False]
- Coordinate Sources: [number]
- Farm Locations: [specific coordinates if available]

The traceability data shows this batch originates from your main plantation farm, which helps meet EUDR requirements for European delivery."

User: "When was this order created?"
You: "PO #PO-202509-0001 was created on 2025-09-23. This means the order was placed just one day before the scheduled delivery, indicating this was likely planned as part of your regular harvest-to-delivery cycle."

User: "What are the coordinates for this batch?"
You: "GEOGRAPHIC COORDINATES:
- Latitude: 3.139
- Longitude: 101.6869
- Farm: Plantation Estate Main Farm
- Accuracy: 10.0 meters

These coordinates place your farm in the Selangor region of Malaysia, which is known for high-quality FFB production. The 10-meter GPS accuracy meets EUDR precision requirements for European market compliance."

EXAMPLE RESPONSES (BAD - NEVER DO THIS):
You: "This transaction showcases strong commitment to traceability and compliance in the global palm oil industry..." (TOO GENERIC)
You: "Supply chain management is crucial for modern business operations..." (UNRELATED LECTURE)
You: "Best practices in sustainable sourcing include..." (GENERIC ADVICE)

GOOD CONTEXTUAL NARRATIVE EXAMPLES:
- "This $20,000 order represents about 2 weeks of production from your 500-hectare farm"
- "The Paris delivery location indicates this batch is headed for European cosmetics processing"
- "Your farm coordinates in Selangor place you in Malaysia's prime FFB growing region"
- "The one-day turnaround from order to delivery shows efficient harvest planning"

RESPONSE RULES:
- Give direct, specific answers first
- Use actual data from the purchase order
- Maintain conversation context for follow-up questions  
- Add insights ONLY after answering the direct question
- Never say "I would need access" when you already have the data

Answer the user's question directly and specifically."""

            # Generate response using OpenAI with enhanced context
            enhanced_context = {
                "advanced_system_prompt": system_prompt,
                "context_prompt": f"Current context: {self._format_current_context(context)}",
                "industry_context": "Data platform providing factual information",
                "compliance_intelligence": "Focus on data accuracy and specific answers",
                "response_mode": "factual_data_only"
            }
            
            response = await self.openai_client.generate_advanced_response(
                user_message=message,
                context_data=context,
                enhanced_context=enhanced_context,
                user_name=context['user_info']['first_name']
            )
            
            return response
            
        except Exception as e:
            print(f"System-aware AI generation failed: {e}")
            # Fallback to original method
            return await self._generate_ai_response(message, context)
    
    def _format_current_context(self, context: Dict[str, Any]) -> str:
        """Format current context for AI prompt."""
        context_parts = []
        
        if context.get("current_po"):
            po = context["current_po"]
            context_parts.append(f"""
CURRENT PURCHASE ORDER: {po['po_number']}
- Buyer: {po['buyer']}
- Seller: {po['seller']}
- Product: {po['product']}
- Quantity: {po['quantity']} MT
- Unit Price: ${po['unit_price']}
- Total Value: ${po['total_amount']}
- Status: {po['status']}
- Delivery Date: {po['delivery_date']}
- Delivery Location: {po['delivery_location']}
- Created: {po['created_date']}
- User Role: {po['user_role']}

BATCH COORDINATE DATA:
- GPS Data Available: {po.get('batch_coordinates', {}).get('has_gps_data', False)}
- Number of Coordinate Sources: {po.get('batch_coordinates', {}).get('total_coordinate_sources', 0)}
- Batch Locations: {po.get('batch_coordinates', {}).get('batch_locations', [])}
- Origin Data: {po.get('origin_data', 'Not available')}""")
        
        if context.get("query_context"):
            context_parts.append(f"Query Context: {context['query_context']}")
        
        return "\n".join(context_parts) if context_parts else "No specific data context loaded."
    
    async def _generate_ai_response(self, message: str, context_data: Dict[str, Any]) -> str:
        """Generate AI response using AdvancedSupplyChainPrompts."""
        try:
            # Determine response mode
            response_mode = self.prompts.determine_response_mode(message, context_data)
            
            # Get master system prompt
            system_prompt = self.prompts.get_master_system_prompt()
            
            # Get context-aware prompt
            context_prompt = self.prompts.get_context_aware_prompt(context_data, response_mode)
            
            # Build enhanced context for OpenAI client
            enhanced_context = {
                "system_prompt": system_prompt,
                "context_prompt": context_prompt,
                "industry_context": "Palm oil supply chain traceability and compliance platform",
                "compliance_intelligence": "EUDR compliance tracking, RSPO certification, zero deforestation requirements",
                "response_mode": response_mode.value
            }
            
            # Generate AI response
            response = await self.openai_client.generate_advanced_response(
                user_message=message,
                context_data=context_data,
                enhanced_context=enhanced_context,
                user_name=context_data["user_info"]["first_name"]
            )
            
            return response
            
        except Exception as e:
            print(f"AI generation failed: {e}")
            # Fallback to hardcoded response if AI fails
            if context_data.get("query_type") == "purchase_order_lookup":
                return self._format_po_response(context_data["po_data"])
            elif context_data.get("query_type") == "purchase_order_not_found":
                return self._format_po_not_found(context_data["po_identifier"])
            else:
                return self._format_general_response()
    
    def _format_po_response(self, po_data: Dict[str, Any]) -> str:
        """Format PO response with actual data."""
        user_name = self.user.user.full_name or "User"
        
        response = f"Hello {user_name}, here's the detailed information for Purchase Order {po_data['po_number']}:\n\n"
        
        response += "ORDER SUMMARY\n"
        response += f"PO Number: {po_data['po_number']}\n"
        response += f"Buyer: {po_data['buyer']}\n"
        response += f"Seller: {po_data['seller']}\n"
        response += f"Product: {po_data['product']}\n"
        response += f"Quantity: {po_data['quantity']} MT\n"
        response += f"Unit Price: ${po_data['unit_price']:,.2f}\n"
        response += f"Total Value: ${po_data['total_amount']:,.2f}\n"
        response += f"Status: {po_data['status'].title()}\n"
        response += f"Delivery Date: {po_data['delivery_date'] or 'Not specified'}\n"
        response += f"Delivery Location: {po_data['delivery_location'] or 'Not specified'}\n"
        response += f"Created: {po_data['created_date'] or 'Unknown'}\n\n"
        
        response += f"Your Role: {po_data['user_role'].title()}\n\n"
        
        # Add next steps based on status
        if po_data['status'] == 'pending':
            response += "NEXT STEPS\n"
            if po_data['user_role'] == 'seller':
                response += "1. Review and confirm order details\n"
                response += f"2. Verify inventory availability for {po_data['quantity']} MT\n"
                response += "3. Prepare sustainability documentation\n"
                response += "4. Update delivery timeline if needed\n"
            else:
                response += "1. Awaiting seller confirmation\n"
                response += "2. Monitor order status for updates\n"
                response += "3. Prepare receiving logistics\n"
        elif po_data['status'] == 'confirmed':
            response += "STATUS UPDATE\n"
            response += "1. Order confirmed and in progress\n"
            response += "2. Track shipment updates\n"
            response += "3. Prepare for delivery coordination\n"
        
        response += f"\nNeed help with this order? Ask me about delivery tracking, compliance documentation, or supplier performance."
        
        return response
    
    def _format_po_not_found(self, po_identifier: str) -> str:
        """Format response when PO is not found."""
        return f"""I couldn't find Purchase Order #{po_identifier} in your system.

This could be because:
- The PO number format might be different
- You may not have access to this specific order  
- There could be a typo in the PO number
- The order might be from a different company branch

Try these options:
- Check your purchase orders dashboard
- Verify the exact PO number format
- Ask me to "show recent orders" 
- Contact your supply chain manager

Example formats I recognize:
- PO-202509-0001
- #PO-202509-0001
- 202509-0001"""
    
    def _format_inventory_response(self) -> str:
        """Format inventory-related response."""
        user_name = self.user.user.full_name or "User"
        company_name = self.user.company.name
        
        return f"""INVENTORY MANAGEMENT - {company_name}

Hello {user_name}, I can help you with inventory and batch tracking:

Current Capabilities:
- Real-time stock level monitoring
- Batch traceability and lot tracking
- Expiration date management
- Quality control status updates
- Location-based inventory views

Quick Actions:
- "Show low stock items" - View items needing reorder
- "Check batch B2024-001" - Get specific batch details
- "Inventory by location" - See stock distribution
- "Quality alerts" - View items needing attention

Integration Status:
- Transparency Factor: {self.transparency_factor}
- Real-time updates: Enabled
- EUDR compliance tracking: Active

What specific inventory information would you like to see?"""
    
    def _format_transparency_response(self) -> str:
        """Format transparency/sustainability response."""
        user_name = self.user.user.full_name or "User"
        
        return f"""SUPPLY CHAIN TRANSPARENCY ANALYSIS

Hello {user_name}, here's your sustainability overview:

Current Transparency Metrics:
- Transparency Factor: {self.transparency_factor} ({(self.transparency_factor * 100):.1f}%)
- Supply chain visibility: {"High" if self.transparency_factor > 0.9 else "Medium"}
- Sustainable sourcing score: Under analysis

Available Features:
- End-to-end traceability mapping
- Sustainability certificate verification
- Carbon footprint calculation
- Supplier ESG scoring
- EUDR compliance monitoring

Quick Insights:
- Recent shipments are fully traceable
- Sustainability documentation up to date
- Zero deforestation compliance: Active monitoring
- Supplier audits: Scheduled quarterly

Next Steps:
- Review upcoming sustainability audits
- Update supplier scorecards
- Generate transparency reports

What sustainability metrics would you like to explore?"""
    
    def _format_compliance_response(self) -> str:
        """Format compliance-related response."""
        user_name = self.user.user.full_name or "User"
        
        return f"""EUDR COMPLIANCE & REGULATIONS

Hello {user_name}, here's your compliance status:

EUDR Compliance Dashboard:
- Status: Compliant
- Due diligence statements: Up to date  
- Risk assessment: Low risk classification
- Geolocation data: 98% complete

Documentation Status:
- Supplier declarations: Current
- Traceability certificates: Verified
- Risk mitigation plans: Active
- Audit trails: Complete

Upcoming Requirements:
- Next compliance review: Within 30 days
- Supplier re-certification: Q2 2025
- Documentation updates: Automated

Compliance Tools:
- Generate due diligence reports
- Schedule supplier audits
- Track regulation updates
- Monitor risk indicators

Need help with specific compliance documentation or risk assessments?"""
    
    def _format_general_response(self) -> str:
        """Format general welcome response."""
        user_name = self.user.user.full_name or "User"
        company_name = self.user.company.name
        
        return f"""Welcome to {self.app_name}

Hello {user_name} from {company_name},

I'm your intelligent supply chain assistant. Here's what I can help you with:

Quick Lookups:
- Purchase order details (try "PO #202509-0001")
- Inventory and batch tracking
- Supplier information
- Shipment status

Analytics & Insights:
- Supply chain transparency analysis
- Sustainability metrics
- Performance dashboards
- Risk assessments

Compliance Support:
- EUDR regulation guidance
- Due diligence documentation
- Audit trail generation
- Certificate verification

Smart Features:
- Real-time notifications
- Predictive analytics
- Automated reporting
- Exception handling

Current System Status:
- Transparency Factor: {self.transparency_factor}
- Platform: {self.app_name}
- Your Role: {self.user.company.name} Team Member

What would you like to explore first? You can ask me about specific orders, check inventory levels, or get compliance updates."""

# Main chat endpoint
@router.post("/chat")
async def unified_chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """Unified chat endpoint - handles both regular and streaming responses."""
    
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    
    assistant = UnifiedSupplyChainAssistant(db, current_user)
    
    if request.stream:
        # Return streaming response
        async def generate_stream():
            try:
                # Start with typing indicator
                yield f"data: {json.dumps({'type': 'typing', 'content': 'Analyzing your request...'})}\n\n"
                
                # Small delay for realistic typing feel
                await asyncio.sleep(0.5)
                
                # Generate actual response
                response = await assistant.generate_response(request.message)
                
                # Stream response in chunks for typewriter effect
                words = response.split()
                chunk_size = 3  # 3 words per chunk for smooth typing
                
                for i in range(0, len(words), chunk_size):
                    chunk = " ".join(words[i:i+chunk_size])
                    if i + chunk_size < len(words):
                        chunk += " "
                    
                    yield f"data: {json.dumps({'type': 'text', 'content': chunk})}\n\n"
                    
                    # Small delay between chunks
                    await asyncio.sleep(0.1)
                
                # Send completion
                yield f"data: {json.dumps({'type': 'complete', 'timestamp': datetime.now().isoformat()})}\n\n"
                
            except Exception as e:
                yield f"data: {json.dumps({'type': 'error', 'content': f'Error: {str(e)}'})}\n\n"
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
                "Access-Control-Allow-Headers": "*"
            }
        )
    
    else:
        # Return regular response
        try:
            response = await assistant.generate_response(request.message)
            return {
                "response": response,
                "company": current_user.company.name,
                "user": current_user.user.full_name or "User",
                "timestamp": datetime.now().isoformat(),
                "message_id": f"msg_{int(datetime.now().timestamp())}"
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error generating response: {str(e)}")

# Health check endpoint
@router.get("/health")
async def assistant_health():
    """Health check for the unified assistant."""
    return {
        "status": "healthy",
        "service": "Unified Supply Chain Assistant",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

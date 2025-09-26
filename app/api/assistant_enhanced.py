"""
Enhanced AI Assistant API with Improved Formatting and PO Query Handling
Provides properly structured, readable responses with clear visual hierarchy
"""
from typing import List, Optional, Dict, Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime
import os
import re

from app.core.database import get_db
from app.core.auth import get_current_user
from app.core.logging import get_logger
from app.models.purchase_order import PurchaseOrder
from app.models.batch import Batch
from app.models.company import Company
from app.models.product import Product
from app.models.user import User

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1/assistant-enhanced", tags=["enhanced-assistant"])


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str
    success: bool = True
    context_used: bool = False
    user_company: str = None
    query_type: str = "general"


class SupplyChainQueryProcessor:
    """Process specific supply chain queries like PO numbers, batch IDs, etc."""
    
    def __init__(self, db: Session, current_user: User):
        self.db = db
        self.user = current_user
        
    def detect_query_type(self, message: str) -> tuple[str, str]:
        """Detect specific query types and extract identifiers."""
        
        message_upper = message.upper()
        
        # PO Number patterns
        po_patterns = [
            r'PO[#\s-]*(\d{6}-\d{4})',  # PO-202509-0001
            r'PO[#\s-]*(\d+)',          # PO-12345
            r'PURCHASE ORDER[#\s-]*(\d+)', # Purchase Order 12345
            r'#PO-(\d{6}-\d{4})',       # #PO-202509-0001
        ]
        
        for pattern in po_patterns:
            match = re.search(pattern, message_upper)
            if match:
                return ("purchase_order", match.group(1))
        
        return ("general", "")
    
    async def query_purchase_order(self, po_identifier: str) -> Optional[Dict[str, Any]]:
        """Query specific purchase order by PO number or ID."""
        
        try:
            # Try different PO number formats
            po_queries = [
                f"PO-{po_identifier}",
                po_identifier,
                f"PO-202509-{po_identifier.zfill(4)}",  # Pad with zeros
                f"PO-202509-{po_identifier}",
            ]
            
            po = None
            for po_query in po_queries:
                po = self.db.query(PurchaseOrder).filter(
                    PurchaseOrder.po_number == po_query
                ).first()
                
                if po:
                    break
            
            # Try by ID if numeric
            if not po and po_identifier.replace("-", "").isdigit():
                try:
                    po_id = int(po_identifier.replace("-", ""))
                    po = self.db.query(PurchaseOrder).filter(
                        PurchaseOrder.id == po_id
                    ).first()
                except ValueError:
                    pass
            
            if not po:
                return None
            
            # Get related data
            buyer = po.buyer_company
            seller = po.seller_company  
            product = po.product
            
            return {
                "po_number": po.po_number,
                "id": str(po.id),
                "buyer": buyer.name if buyer else "Unknown Buyer",
                "seller": seller.name if seller else "Unknown Seller",
                "product": product.name if product else "Unknown Product",
                "quantity": float(po.quantity or 0),
                "unit_price": float(po.unit_price or 0),
                "total_amount": float(po.total_amount or 0),
                "status": po.status,
                "delivery_date": po.delivery_date.strftime("%Y-%m-%d") if po.delivery_date else None,
                "delivery_location": po.delivery_location,
                "created_date": po.created_at.strftime("%Y-%m-%d") if po.created_at else None,
                "confirmed_date": po.confirmed_at.strftime("%Y-%m-%d") if po.confirmed_at else None,
                "notes": po.notes,
                "user_role": self._determine_user_role(po),
                "supply_chain_level": getattr(po, 'supply_chain_level', 1),
                "fulfillment_status": getattr(po, 'fulfillment_status', 'pending'),
                "fulfillment_percentage": getattr(po, 'fulfillment_percentage', 0)
            }
            
        except Exception as e:
            logger.error(f"Error querying PO {po_identifier}: {e}")
            return None
    
    def _determine_user_role(self, po: PurchaseOrder) -> str:
        """Determine user's role in this PO transaction."""
        if po.buyer_company_id == self.user.company_id:
            return "buyer"
        elif po.seller_company_id == self.user.company_id:
            return "seller"
        else:
            return "observer"


class ResponseFormatter:
    """Format responses with proper structure and visual hierarchy."""
    
    @staticmethod
    def format_po_response(po_data: Dict[str, Any], user_context: Dict[str, Any]) -> str:
        """Format purchase order response with enhanced readability."""
        
        user_name = user_context["user_info"]["first_name"]
        
        # Start with greeting and context
        response = f"Hello {user_name}, here's the detailed information for Purchase Order {po_data['po_number']}:\n\n"
        
        # ORDER OVERVIEW SECTION
        response += "📋 ORDER OVERVIEW\n"
        response += "=" * 40 + "\n"
        response += f"PO Number: {po_data['po_number']}\n"
        response += f"Status: {po_data['status'].title()}\n"
        response += f"Created: {po_data['created_date'] or 'Unknown'}\n"
        if po_data['confirmed_date']:
            response += f"Confirmed: {po_data['confirmed_date']}\n"
        response += "\n"
        
        # TRADING PARTIES SECTION
        response += "🏢 TRADING PARTIES\n"
        response += "=" * 40 + "\n"
        response += f"Buyer: {po_data['buyer']}\n"
        response += f"Seller: {po_data['seller']}\n"
        response += f"Your Role: {po_data['user_role'].title()}\n"
        response += "\n"
        
        # PRODUCT & PRICING SECTION
        response += "📦 PRODUCT & PRICING\n"
        response += "=" * 40 + "\n"
        response += f"Product: {po_data['product']}\n"
        response += f"Quantity: {po_data['quantity']:,.1f} MT\n"
        response += f"Unit Price: ${po_data['unit_price']:,.2f} per MT\n"
        response += f"Total Value: ${po_data['total_amount']:,.2f}\n"
        response += "\n"
        
        # DELIVERY DETAILS SECTION
        response += "🚚 DELIVERY DETAILS\n"
        response += "=" * 40 + "\n"
        response += f"Delivery Date: {po_data['delivery_date'] or 'Not specified'}\n"
        response += f"Delivery Location: {po_data['delivery_location'] or 'Not specified'}\n"
        response += f"Fulfillment Status: {po_data['fulfillment_status'].title()}\n"
        response += f"Fulfillment Progress: {po_data['fulfillment_percentage']}%\n"
        response += "\n"
        
        # BUSINESS CONTEXT SECTION
        response += "💼 BUSINESS CONTEXT\n"
        response += "=" * 40 + "\n"
        
        if po_data['user_role'] == 'buyer':
            response += f"• You are purchasing {po_data['product']} from {po_data['seller']}\n"
            response += f"• This is an upstream procurement transaction\n"
        elif po_data['user_role'] == 'seller':
            response += f"• You are selling {po_data['product']} to {po_data['buyer']}\n"
            response += f"• This is a downstream sales transaction\n"
        
        response += f"• Supply chain level: {po_data['supply_chain_level']}\n"
        
        # Add pricing context
        unit_price = po_data['unit_price']
        if unit_price > 1400:
            response += "• Premium RSPO-certified pricing detected\n"
        elif unit_price > 1200:
            response += "• Above-market pricing with sustainability premiums\n"
        elif unit_price > 1000:
            response += "• Standard market-rate pricing\n"
        
        response += "\n"
        
        # NEXT STEPS SECTION
        response += "🎯 NEXT STEPS\n"
        response += "=" * 40 + "\n"
        
        status = po_data['status']
        if status == 'pending':
            if po_data['user_role'] == 'seller':
                response += "As the seller, you should:\n\n"
                response += f"1. Review order specifications\n"
                response += f"   • Verify {po_data['quantity']} MT availability\n"
                response += f"   • Confirm product quality standards\n\n"
                response += f"2. Validate delivery requirements\n"
                response += f"   • Check delivery date: {po_data['delivery_date']}\n"
                response += f"   • Confirm delivery location access\n\n"
                response += f"3. Prepare documentation\n"
                response += f"   • RSPO certification\n"
                response += f"   • GPS coordinates for EUDR compliance\n"
                response += f"   • Quality certificates\n\n"
                response += f"4. Confirm order acceptance\n"
            else:
                response += "Current status requires:\n\n"
                response += f"1. Await seller confirmation\n"
                response += f"2. Monitor order status updates\n"
                response += f"3. Prepare receiving logistics\n"
                response += f"4. Review contract terms\n"
        
        elif status == 'confirmed':
            response += "Order confirmed - action items:\n\n"
            response += f"1. Delivery preparation\n"
            response += f"   • Schedule for {po_data['delivery_date']}\n"
            response += f"   • Coordinate transportation\n\n"
            response += f"2. Quality assurance\n"
            response += f"   • Prepare inspection documentation\n"
            response += f"   • Schedule quality control\n\n"
            response += f"3. Compliance verification\n"
            response += f"   • Ensure sustainability certificates\n"
            response += f"   • Verify traceability documents\n\n"
            response += f"4. Financial preparation\n"
            response += f"   • Process payment (${po_data['total_amount']:,.2f})\n"
        
        response += "\n"
        
        # ADDITIONAL NOTES
        if po_data.get('notes'):
            response += "📝 ADDITIONAL NOTES\n"
            response += "=" * 40 + "\n"
            response += f"{po_data['notes']}\n\n"
        
        # QUICK ACTIONS
        response += "⚡ QUICK ACTIONS\n"
        response += "=" * 40 + "\n"
        response += "• View all purchase orders in dashboard\n"
        response += "• Check inventory levels for this product\n"
        response += "• Review supplier compliance documentation\n"
        response += "• Contact trading partner for coordination\n"
        response += "• Generate compliance reports\n"
        
        return response
    
    @staticmethod
    def format_po_not_found_response(po_identifier: str, user_name: str) -> str:
        """Format response when PO is not found."""
        
        response = f"Hello {user_name}, I couldn't find Purchase Order '{po_identifier}' in your system.\n\n"
        
        response += "🔍 POSSIBLE REASONS\n"
        response += "=" * 40 + "\n"
        response += "• The PO number format might be different\n"
        response += "• You may not have access to view this PO\n"
        response += "• There could be a typo in the PO number\n"
        response += "• The PO might be in a different system\n\n"
        
        response += "💡 SUGGESTIONS\n"
        response += "=" * 40 + "\n"
        response += "• Check the exact PO format (e.g., PO-202509-0001)\n"
        response += "• Verify your access permissions\n"
        response += "• Review the purchase orders dashboard\n"
        response += "• Contact system administrator if needed\n\n"
        
        response += "🔗 ALTERNATIVE ACTIONS\n"
        response += "=" * 40 + "\n"
        response += "• Browse all purchase orders\n"
        response += "• Search by company or product name\n"
        response += "• Check recent transactions\n"
        response += "• Ask about specific suppliers or buyers\n"
        
        return response


class EnhancedSupplyChainAssistant:
    """Enhanced AI assistant with improved formatting and PO handling."""
    
    def __init__(self, db: Session, current_user: User):
        self.db = db
        self.user = current_user
        self.query_processor = SupplyChainQueryProcessor(db, current_user)
        self.formatter = ResponseFormatter()
        
    async def get_user_context(self) -> Dict[str, Any]:
        """Get user context for responses."""
        
        return {
            "user_info": {
                "first_name": self.user.first_name or "User",
                "name": f"{self.user.first_name or ''} {self.user.last_name or ''}".strip(),
                "company_name": self.user.company.name if self.user.company else "Unknown Company",
                "company_type": self.user.company.company_type if self.user.company else "unknown",
                "role": getattr(self.user, 'role', 'user')
            }
        }
        
    async def generate_response(self, message: str) -> tuple[str, str]:
        """Generate intelligent responses based on query type."""
        
        # Get user context
        user_context = await self.get_user_context()
        
        # Detect query type
        query_type, identifier = self.query_processor.detect_query_type(message)
        
        if query_type == "purchase_order":
            response = await self._handle_po_query(identifier, user_context)
            return response, "purchase_order"
        else:
            response = await self._handle_general_query(message, user_context)
            return response, "general"
    
    async def _handle_po_query(self, po_identifier: str, user_context: Dict[str, Any]) -> str:
        """Handle specific purchase order queries with enhanced formatting."""
        
        po_data = await self.query_processor.query_purchase_order(po_identifier)
        
        if not po_data:
            user_name = user_context["user_info"]["first_name"]
            return self.formatter.format_po_not_found_response(po_identifier, user_name)
        
        return self.formatter.format_po_response(po_data, user_context)
    
    async def _handle_general_query(self, message: str, user_context: Dict[str, Any]) -> str:
        """Handle general supply chain queries with proper formatting."""
        
        user_name = user_context["user_info"]["first_name"]
        company_name = user_context["user_info"]["company_name"]
        company_type = user_context["user_info"]["company_type"]
        
        response = f"Hello {user_name} from {company_name}!\n\n"
        
        response += "🤖 AI SUPPLY CHAIN ASSISTANT\n"
        response += "=" * 40 + "\n"
        response += "I can help you with:\n\n"
        
        response += "📋 PURCHASE ORDERS\n"
        response += "• Specific PO lookup (e.g., 'PO #PO-202509-0001')\n"
        response += "• Order status and tracking\n"
        response += "• Fulfillment progress\n\n"
        
        response += "📦 INVENTORY & BATCHES\n"
        response += "• Stock levels and availability\n"
        response += "• Batch tracking and traceability\n"
        response += "• Quality parameters\n\n"
        
        response += "🔍 TRANSPARENCY & COMPLIANCE\n"
        response += "• EUDR compliance status\n"
        response += "• RSPO certification tracking\n"
        response += "• GPS mapping verification\n\n"
        
        response += "🏢 TRADING PARTNERS\n"
        response += "• Supplier and buyer information\n"
        response += "• Relationship analysis\n"
        response += "• Performance metrics\n\n"
        
        response += "💡 SPECIALIZED GUIDANCE\n"
        response += "=" * 40 + "\n"
        response += f"As a {company_type}, I can provide specific insights for:\n"
        
        if company_type == "plantation_grower":
            response += "• FFB yield optimization\n"
            response += "• Sustainability compliance\n"
            response += "• Harvest planning\n"
        elif company_type == "mill_processor":
            response += "• Oil extraction rate (OER) improvement\n"
            response += "• Energy efficiency\n"
            response += "• Processing optimization\n"
        elif company_type == "brand":
            response += "• Supply chain transparency\n"
            response += "• Supplier risk assessment\n"
            response += "• Sustainability reporting\n"
        else:
            response += "• Supply chain optimization\n"
            response += "• Compliance management\n"
            response += "• Performance improvement\n"
        
        response += "\n🎯 WHAT WOULD YOU LIKE TO KNOW?\n"
        response += "=" * 40 + "\n"
        response += "Try asking me about:\n"
        response += "• A specific purchase order (PO number)\n"
        response += "• Your current inventory status\n"
        response += "• Compliance requirements\n"
        response += "• Trading partner information\n"
        
        return response


@router.post("/chat", response_model=ChatResponse)
async def enhanced_chat_with_formatting(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Enhanced AI assistant chat with improved formatting and PO handling."""
    
    try:
        assistant = EnhancedSupplyChainAssistant(db, current_user)
        response, query_type = await assistant.generate_response(request.message)
        
        return ChatResponse(
            response=response,
            context_used=True,
            user_company=current_user.company.name if current_user.company else "Unknown",
            query_type=query_type,
            success=True
        )
        
    except Exception as e:
        logger.error(f"Error in enhanced assistant chat: {str(e)}")
        
        user_name = current_user.first_name or "User"
        error_response = f"""Hello {user_name}, I'm experiencing technical difficulties accessing your supply chain data.

🔧 TECHNICAL ISSUE
={'=' * 40}
The system encountered an error while processing your request.

Please try:
• Refreshing the page and trying again
• Checking your dashboard directly
• Contacting technical support if the issue persists

I'll be back online shortly to assist you with your supply chain queries."""
        
        return ChatResponse(
            response=error_response,
            success=False,
            context_used=False,
            user_company=current_user.company.name if current_user.company else "Unknown"
        )


@router.get("/status")
async def get_enhanced_assistant_status():
    """Get enhanced AI assistant status and capabilities."""
    
    return {
        "status": "active",
        "version": "2.0.0 Enhanced",
        "capabilities": [
            "Enhanced purchase order lookup with detailed formatting",
            "Structured responses with visual hierarchy", 
            "Supply chain data interpretation",
            "EUDR compliance guidance",
            "Palm oil industry expertise",
            "Improved readability and spacing"
        ],
        "features": {
            "enhanced_formatting": True,
            "structured_responses": True,
            "po_analysis": True,
            "real_time_data": True,
            "visual_hierarchy": True
        }
    }

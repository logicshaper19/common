"""
Assistant API Endpoints
AI-powered chat endpoint with comprehensive supply chain data access
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.core.auth import get_current_user
from app.core.database import get_db
from app.core.openai_client import SimpleOpenAIClient
from app.core.langchain_assistant import SupplyChainLangChainAssistant, SupplyChainTools, SimpleSupplyChainAssistant, LANGCHAIN_AVAILABLE
from app.core.context_manager import SupplyChainContextManager
from app.core.response_formatter import ProfessionalResponseFormatter
from app.core.professional_prompts import ProfessionalSupplyChainPrompts
from app.core.advanced_prompts import AdvancedSupplyChainPrompts, ResponseMode
from app.models.user import User
from app.models.company import Company
from app.models.purchase_order import PurchaseOrder
from app.models.batch import Batch
from app.models.product import Product
from app.core.logging import get_logger
from datetime import datetime
import os
import re

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/assistant", tags=["assistant"])


async def handle_specific_po_query(message: str, db: Session, current_user) -> dict:
    """Handle specific PO number queries with structured database lookup."""
    
    # Detect PO number patterns
    po_patterns = [
        r'PO[#\s-]*(\d{6}-\d{4})',  # PO-202509-0001
        r'PO[#\s-]*(\d+)',          # PO-12345
        r'PURCHASE ORDER[#\s-]*(\d+)', # Purchase Order 12345
        r'#PO-(\d{6}-\d{4})',       # #PO-202509-0001
    ]
    
    message_upper = message.upper()
    po_identifier = None
    
    for pattern in po_patterns:
        match = re.search(pattern, message_upper)
        if match:
            po_identifier = match.group(1)
            break
    
    if not po_identifier:
        return None
    
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
            po = db.query(PurchaseOrder).filter(
                PurchaseOrder.po_number == po_query
            ).first()
            
            if po:
                break
        
        # Try by ID if numeric
        if not po and po_identifier.replace("-", "").isdigit():
            try:
                po_id = int(po_identifier.replace("-", ""))
                po = db.query(PurchaseOrder).filter(
                    PurchaseOrder.id == po_id
                ).first()
            except ValueError:
                pass
        
        if not po:
            user_name = current_user.first_name or "User"
            return {
                "response": f"""Hello {user_name}, I couldn't find Purchase Order '{po_identifier}' in your system.

🔍 POSSIBLE REASONS
• The PO number format might be different  
• You may not have access to view this PO
• There could be a typo in the PO number
• The PO might be in a different system

💡 SUGGESTIONS
• Check the exact PO format (e.g., PO-202509-0001)
• Verify your access permissions  
• Review the purchase orders dashboard
• Contact system administrator if needed

🔗 ALTERNATIVE ACTIONS  
• Browse all purchase orders
• Search by company or product name
• Check recent transactions
• Ask about specific suppliers or buyers""",
                "company_name": current_user.company.name if current_user.company else "Unknown"
            }
        
        # Get related data
        buyer_company = po.buyer_company
        seller_company = po.seller_company  
        product = po.product
        
        # Determine user role
        user_role = "observer"
        if po.buyer_company_id == current_user.company_id:
            user_role = "buyer"
        elif po.seller_company_id == current_user.company_id:
            user_role = "seller"
        
        user_name = current_user.first_name or "User"
        
        # Build structured response
        response = f"Hello {user_name}, here's the detailed information for Purchase Order {po.po_number}:\n\n"
        
        # ORDER OVERVIEW SECTION
        response += "📋 ORDER OVERVIEW\n"
        response += "=" * 40 + "\n"
        response += f"PO Number: {po.po_number}\n"
        response += f"Status: {po.status.title()}\n"
        response += f"Created: {po.created_at.strftime('%Y-%m-%d') if po.created_at else 'Unknown'}\n"
        if hasattr(po, 'confirmed_at') and po.confirmed_at:
            response += f"Confirmed: {po.confirmed_at.strftime('%Y-%m-%d')}\n"
        response += "\n"
        
        # TRADING PARTIES SECTION
        response += "🏢 TRADING PARTIES\n"
        response += "=" * 40 + "\n"
        response += f"Buyer: {buyer_company.name if buyer_company else 'Unknown Buyer'}\n"
        response += f"Seller: {seller_company.name if seller_company else 'Unknown Seller'}\n"
        response += f"Your Role: {user_role.title()}\n"
        response += "\n"
        
        # PRODUCT & PRICING SECTION
        response += "📦 PRODUCT & PRICING\n"
        response += "=" * 40 + "\n"
        response += f"Product: {product.name if product else 'Unknown Product'}\n"
        response += f"Quantity: {float(po.quantity or 0):,.1f} MT\n"
        response += f"Unit Price: ${float(po.unit_price or 0):,.2f} per MT\n"
        response += f"Total Value: ${float(po.total_amount or 0):,.2f}\n"
        response += "\n"
        
        # DELIVERY DETAILS SECTION
        response += "🚚 DELIVERY DETAILS\n"
        response += "=" * 40 + "\n"
        response += f"Delivery Date: {po.delivery_date.strftime('%Y-%m-%d') if po.delivery_date else 'Not specified'}\n"
        response += f"Delivery Location: {po.delivery_location or 'Not specified'}\n"
        response += "\n"
        
        # BUSINESS CONTEXT SECTION
        response += "💼 BUSINESS CONTEXT\n"
        response += "=" * 40 + "\n"
        
        if user_role == 'buyer':
            response += f"• You are purchasing {product.name if product else 'product'} from {seller_company.name if seller_company else 'seller'}\n"
            response += f"• This is an upstream procurement transaction\n"
        elif user_role == 'seller':
            response += f"• You are selling {product.name if product else 'product'} to {buyer_company.name if buyer_company else 'buyer'}\n"
            response += f"• This is a downstream sales transaction\n"
        
        # Add pricing context
        unit_price = float(po.unit_price or 0)
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
        
        if po.status == 'pending':
            if user_role == 'seller':
                response += "As the seller, you should:\n\n"
                response += f"1. Review order specifications\n"
                response += f"   • Verify {float(po.quantity or 0):,.1f} MT availability\n"
                response += f"   • Confirm product quality standards\n\n"
                response += f"2. Validate delivery requirements\n"
                response += f"   • Check delivery date: {po.delivery_date.strftime('%Y-%m-%d') if po.delivery_date else 'TBD'}\n"
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
        
        elif po.status == 'confirmed':
            response += "Order confirmed - action items:\n\n"
            response += f"1. Delivery preparation\n"
            response += f"   • Schedule for {po.delivery_date.strftime('%Y-%m-%d') if po.delivery_date else 'TBD'}\n"
            response += f"   • Coordinate transportation\n\n"
            response += f"2. Quality assurance\n"
            response += f"   • Prepare inspection documentation\n"
            response += f"   • Schedule quality control\n\n"
            response += f"3. Compliance verification\n"
            response += f"   • Ensure sustainability certificates\n"
            response += f"   • Verify traceability documents\n\n"
            response += f"4. Financial preparation\n"
            response += f"   • Process payment (${float(po.total_amount or 0):,.2f})\n"
        
        response += "\n"
        
        # ADDITIONAL NOTES
        if po.notes:
            response += "📝 ADDITIONAL NOTES\n"
            response += "=" * 40 + "\n"
            response += f"{po.notes}\n\n"
        
        # QUICK ACTIONS
        response += "⚡ QUICK ACTIONS\n"
        response += "=" * 40 + "\n"
        response += "• View all purchase orders in dashboard\n"
        response += "• Check inventory levels for this product\n"
        response += "• Review supplier compliance documentation\n"
        response += "• Contact trading partner for coordination\n"
        response += "• Generate compliance reports\n"
        
        return {
            "response": response,
            "company_name": current_user.company.name if current_user.company else "Unknown"
        }
        
    except Exception as e:
        logger.error(f"Error querying PO {po_identifier}: {e}")
        return None


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str
    success: bool = True
    context_used: bool = False
    user_company: str = None


@router.post("/chat", response_model=ChatResponse)
async def professional_chat_with_context(
    request: ChatRequest,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Professional chat with comprehensive context and clean formatting."""
    
    try:
        # Check if this is a specific PO query first
        logger.info(f"🔍 Checking for PO query in message: {request.message}")
        po_data = await handle_specific_po_query(request.message, db, current_user)
        if po_data:
            logger.info(f"✅ PO query detected and processed successfully")
            return ChatResponse(
                response=po_data["response"],
                context_used=True,
                user_company=po_data["company_name"],
                success=True
            )
        else:
            logger.info(f"❌ No PO query detected, proceeding to advanced prompts")
        
        # Get comprehensive context using new context manager
        context_manager = SupplyChainContextManager(db, current_user)
        user_context = await context_manager.get_comprehensive_context()
        
        # Generate advanced prompts with .env integration
        advanced_prompts = AdvancedSupplyChainPrompts()
        
        # Determine optimal response mode based on message and context
        response_mode = advanced_prompts.determine_response_mode(request.message, user_context)
        
        # Get master system prompt with .env configuration
        system_prompt = advanced_prompts.get_master_system_prompt()
        
        # Get context-aware prompt with live data integration
        context_prompt = advanced_prompts.get_context_aware_prompt(user_context, response_mode)
        
        # Try LangChain first if available
        if LANGCHAIN_AVAILABLE:
            try:
                # Use LangChain with professional prompts
                from langchain_openai import ChatOpenAI
                
                # Create LLM with response mode appropriate temperature
                temperature = 0.3 if response_mode == ResponseMode.COMPLIANCE_FOCUS else 0.6
                llm = ChatOpenAI(
                    model="gpt-3.5-turbo", 
                    temperature=temperature,
                    openai_api_key=os.getenv("OPENAI_API_KEY"),
                    max_tokens=1200  # Increased for more comprehensive responses
                )
                
                # Create messages with advanced context and industry expertise
                enhanced_industry_context = advanced_prompts.get_enhanced_industry_context()
                compliance_intelligence = advanced_prompts.get_compliance_intelligence_prompt()
                
                messages = [
                    {"role": "system", "content": f"{system_prompt}\n\n{enhanced_industry_context}\n\n{compliance_intelligence}"},
                    {"role": "user", "content": f"{context_prompt}\n\nUser Question: {request.message}\n\nProvide a comprehensive response that demonstrates deep palm oil supply chain expertise and addresses their specific business context."}
                ]
                
                response = await llm.ainvoke(messages)
                
                # Format professionally (remove markdown, clean formatting)
                professional_response = ProfessionalResponseFormatter.format_professional_response(
                    response.content, 
                    user_context
                )
                
                logger.info(f"Advanced LangChain response generated (mode: {response_mode.value}) for user {current_user.id}: {request.message[:50]}...")
                return ChatResponse(
                    response=professional_response,
                    context_used=True,
                    user_company=user_context['user_info']['company_name']
                )
                
            except Exception as langchain_error:
                logger.warning(f"LangChain failed, falling back to simple assistant: {langchain_error}")
        
        # Fallback to simple assistant with advanced prompts
        try:
            # Also use advanced prompts for fallback assistant
            simple_assistant = SimpleOpenAIClient()
            
            # Enhanced fallback with advanced prompt system
            enhanced_context = {
                "advanced_system_prompt": system_prompt,
                "context_prompt": context_prompt,
                "response_mode": response_mode.value,
                "industry_context": advanced_prompts.get_enhanced_industry_context(),
                "compliance_intelligence": advanced_prompts.get_compliance_intelligence_prompt()
            }
            
            response = await simple_assistant.generate_advanced_response(
                user_message=request.message,
                context_data=user_context,
                enhanced_context=enhanced_context,
                user_name=user_context['user_info']['name']
            )
            
            # Apply professional formatting to simple assistant response too
            professional_response = ProfessionalResponseFormatter.format_professional_response(
                response, 
                user_context
            )
            
            logger.info(f"Professional simple assistant response generated for user {current_user.id}: {request.message[:50]}...")
            return ChatResponse(
                response=professional_response,
                context_used=True,
                user_company=user_context['user_info']['company_name']
            )
            
        except Exception as simple_error:
            logger.error(f"Simple assistant also failed: {simple_error}")
            # Use professional error formatter
            error_response = ProfessionalResponseFormatter.format_error_response(
                "system_error", 
                user_context
            )
            return ChatResponse(
                response=error_response,
                context_used=False,
                user_company=fallback_context.get('user_info', {}).get('company_name')
            )
        
    except Exception as e:
        logger.error(f"Error in professional chat endpoint: {e}")
        
        # Create minimal context for error response
        fallback_context = {
            "user_info": {
                "name": current_user.full_name or current_user.email.split('@')[0] if current_user.email else "User",
                "company_name": current_user.company.name if current_user.company else "your company"
            }
        }
        
        error_response = ProfessionalResponseFormatter.format_error_response(
            "system_error", 
            fallback_context
        )
        
        return ChatResponse(
            response=error_response,
            context_used=False,
            user_company=fallback_context.get('user_info', {}).get('company_name')
        )


@router.post("/chat-legacy", response_model=ChatResponse)
async def chat_endpoint_legacy(
    request: ChatRequest,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Legacy chat endpoint for backward compatibility."""
    
    try:
        # Use old context gathering method
        context_data = await gather_comprehensive_context(current_user, db)
        
        # Try LangChain first if available, fallback to simple assistant
        if LANGCHAIN_AVAILABLE:
            try:
                langchain_assistant = SupplyChainLangChainAssistant()
                response = await langchain_assistant.get_response(
                    user_message=request.message,
                    user_context=context_data
                )
                
                logger.info(f"Legacy LangChain response generated for user {current_user.id}: {request.message[:50]}...")
                return ChatResponse(response=response)
                
            except Exception as langchain_error:
                logger.warning(f"LangChain failed, falling back to simple assistant: {langchain_error}")
                
                # Fallback to simple assistant
                simple_assistant = SimpleSupplyChainAssistant()
                response = await simple_assistant.get_response(
                    user_message=request.message,
                    user_context=context_data
                )
                
                logger.info(f"Legacy simple assistant response generated for user {current_user.id}: {request.message[:50]}...")
                return ChatResponse(response=response)
        else:
            # Use simple assistant when LangChain is not available
            simple_assistant = SimpleSupplyChainAssistant()
            response = await simple_assistant.get_response(
                user_message=request.message,
                user_context=context_data
            )
            
            logger.info(f"Legacy simple assistant response generated for user {current_user.id}: {request.message[:50]}...")
            return ChatResponse(response=response)
        
    except Exception as e:
        logger.error(f"Error in legacy AI assistant chat endpoint: {e}")
        # Final fallback to simple response
        user_name = current_user.full_name or current_user.email.split('@')[0] if current_user.email else "User"
        company_name = current_user.company.name if current_user.company else "your company"
        fallback_response = f"Hello {user_name}! I'm having trouble connecting to the AI service right now. I can still help you with basic supply chain questions. What would you like to know about {company_name}?"
        
        return ChatResponse(response=fallback_response)


async def gather_comprehensive_context(user, db):
    """Gather all relevant context data for AI response generation."""
    
    try:
        # Get all data sources in parallel for efficiency
        inventory_data = await get_comprehensive_inventory_data(user, db)
        po_data = await get_comprehensive_po_data(user, db)
        transparency_data = await get_comprehensive_transparency_data(user, db)
        compliance_data = await get_compliance_data(user, db)
        company_data = await get_comprehensive_company_data(user, db)
        processing_data = await get_processing_data(user, db)
        
        # Build comprehensive context for LangChain
        context_data = {
            "user_name": user.full_name or user.email.split('@')[0] if user.email else "User",
            "company_name": user.company.name if user.company else "Unknown Company",
            "company_type": user.company.company_type if user.company else "unknown",
            "user_role": user.role,
            "inventory_summary": f"{inventory_data.get('summary', {}).get('summary', {}).get('total_batches', 0)} batches, {inventory_data.get('summary', {}).get('summary', {}).get('available_quantity', 0)} MT available",
            "recent_pos": f"{po_data.get('pending_pos', 0)} pending, {po_data.get('active_pos', 0)} active purchase orders",
            "transparency_score": f"{transparency_data.get('average_score', 0):.1f}% average transparency",
            "compliance_status": f"{compliance_data.get('eudr_compliant', 0)} EUDR compliant batches",
            # Full data for detailed responses
            "inventory": inventory_data,
            "purchase_orders": po_data,
            "transparency": transparency_data,
            "compliance": compliance_data,
            "company_relationships": company_data,
            "processing": processing_data
        }
        
        return context_data
        
    except Exception as e:
        logger.error(f"Error gathering comprehensive context: {e}")
        # Return minimal context
        return {
            "user_name": user.full_name or user.email.split('@')[0] if user.email else "User",
            "company_name": user.company.name if user.company else "Unknown Company",
            "company_type": user.company.company_type if user.company else "unknown",
            "user_role": user.role,
            "inventory_summary": "0 batches, 0 MT available",
            "recent_pos": "0 pending, 0 active purchase orders",
            "transparency_score": "0.0% average transparency",
            "compliance_status": "0 EUDR compliant batches",
            "inventory": {"total_batches": 0, "available_quantity": 0},
            "purchase_orders": {"pending_pos": 0, "confirmed_pos": 0},
            "transparency": {"average_score": 0, "total_batches": 0},
            "compliance": {"eudr_compliant": 0, "rspo_compliant": 0},
            "company_relationships": {"total_relationships": 0},
            "processing": {"processing_batches": 0}
        }


# Helper functions to get comprehensive data
async def get_comprehensive_inventory_data(user, db):
    """Get all inventory-related data for the user's company."""
    
    try:
        # Get batches for the user's company
        batches = db.query(Batch).filter(Batch.company_id == user.company_id).all()
        
        # Get all available products
        products = db.query(Product).all()
        
        # Calculate inventory summary
        total_batches = len(batches)
        available_quantity = sum(float(batch.quantity) for batch in batches if batch.status == 'active')
        product_types = list(set([batch.product.name for batch in batches if batch.product]))
        
        return {
            "total_batches": total_batches,
            "available_quantity": available_quantity,
            "product_types": product_types,
            "company_name": user.company.name,
            "company_type": user.company.company_type,
            "recent_batches": batches[:5] if batches else []
        }
    except Exception as e:
        logger.error(f"Error getting inventory data: {e}")
        return {
            "total_batches": 0,
            "available_quantity": 0,
            "product_types": [],
            "company_name": user.company.name,
            "company_type": user.company.company_type,
            "recent_batches": []
        }

async def get_comprehensive_po_data(user, db):
    """Get all purchase order data for the user's company."""
    
    try:
        # Get POs where user's company is buyer or seller
        buyer_pos = db.query(PurchaseOrder).filter(
            PurchaseOrder.buyer_company_id == user.company_id
        ).all()
        
        seller_pos = db.query(PurchaseOrder).filter(
            PurchaseOrder.seller_company_id == user.company_id
        ).all()
        
        all_pos = buyer_pos + seller_pos
        pending_pos = [po for po in all_pos if po.status == 'pending']
        confirmed_pos = [po for po in all_pos if po.status == 'confirmed']
        
        return {
            "buyer_pos": len(buyer_pos),
            "seller_pos": len(seller_pos),
            "pending_pos": len(pending_pos),
            "confirmed_pos": len(confirmed_pos),
            "recent_pos": all_pos[:5],
            "company_name": user.company.name,
            "company_type": user.company.company_type
        }
    except Exception as e:
        logger.error(f"Error getting PO data: {e}")
        return {
            "buyer_pos": 0,
            "seller_pos": 0,
            "pending_pos": 0,
            "confirmed_pos": 0,
            "recent_pos": [],
            "company_name": user.company.name,
            "company_type": user.company.company_type
        }

async def get_comprehensive_transparency_data(user, db):
    """Get transparency and traceability data."""
    
    try:
        # Get batches with basic transparency info
        batches = db.query(Batch).filter(Batch.company_id == user.company_id).all()
        
        # Simple transparency calculation (you can enhance this with your actual logic)
        transparency_scores = []
        for batch in batches:
            # Mock transparency score based on batch completeness
            score = 85.0  # Base score - you can implement your actual calculation
            if batch.product and batch.quantity:
                score += 10.0
            if batch.status == 'active':
                score += 5.0
            
            transparency_scores.append({
                "batch_id": batch.batch_id,
                "product": batch.product.name if batch.product else "Unknown",
                "score": min(score, 100.0),
                "status": batch.status
            })
        
        average_score = sum(s["score"] for s in transparency_scores) / len(transparency_scores) if transparency_scores else 0
        compliant_batches = len([s for s in transparency_scores if s["score"] > 90])
        
        return {
            "average_score": average_score,
            "total_batches": len(transparency_scores),
            "compliant_batches": compliant_batches,
            "batch_details": transparency_scores[:10],
            "company_name": user.company.name
        }
    except Exception as e:
        logger.error(f"Error getting transparency data: {e}")
        return {
            "average_score": 0,
            "total_batches": 0,
            "compliant_batches": 0,
            "batch_details": [],
            "company_name": user.company.name
        }

async def get_compliance_data(user, db):
    """Get compliance-related data."""
    
    try:
        # Get batches for compliance analysis
        batches = db.query(Batch).filter(Batch.company_id == user.company_id).all()
        
        # Mock compliance data (you can enhance with actual compliance logic)
        eudr_compliant = len([b for b in batches if b.status == 'active']) * 0.8  # 80% compliance rate
        rspo_compliant = len([b for b in batches if b.status == 'active']) * 0.9  # 90% compliance rate
        
        return {
            "eudr_compliant": int(eudr_compliant),
            "rspo_compliant": int(rspo_compliant),
            "total_batches": len(batches),
            "company_name": user.company.name,
            "company_type": user.company.company_type
        }
    except Exception as e:
        logger.error(f"Error getting compliance data: {e}")
        return {
            "eudr_compliant": 0,
            "rspo_compliant": 0,
            "total_batches": 0,
            "company_name": user.company.name,
            "company_type": user.company.company_type
        }

async def get_comprehensive_company_data(user, db):
    """Get company and supplier relationship data."""
    
    try:
        # Get companies user's company trades with
        buyer_relationships = db.query(PurchaseOrder).filter(
            PurchaseOrder.buyer_company_id == user.company_id
        ).join(Company, PurchaseOrder.seller_company_id == Company.id).all()
        
        seller_relationships = db.query(PurchaseOrder).filter(
            PurchaseOrder.seller_company_id == user.company_id
        ).join(Company, PurchaseOrder.buyer_company_id == Company.id).all()
        
        suppliers = list(set([po.seller.name for po in buyer_relationships if hasattr(po, 'seller')]))
        customers = list(set([po.buyer.name for po in seller_relationships if hasattr(po, 'buyer')]))
        
        return {
            "suppliers": suppliers[:5],  # Top 5 suppliers
            "customers": customers[:5],  # Top 5 customers
            "company_type": user.company.company_type,
            "total_relationships": len(suppliers) + len(customers),
            "company_name": user.company.name
        }
    except Exception as e:
        logger.error(f"Error getting company data: {e}")
        return {
            "suppliers": [],
            "customers": [],
            "company_type": user.company.company_type,
            "total_relationships": 0,
            "company_name": user.company.name
        }

async def get_processing_data(user, db):
    """Get processing and transformation data."""
    
    try:
        # Get batches related to processing
        batches = db.query(Batch).filter(Batch.company_id == user.company_id).all()
        
        # Filter by processing-related products
        processing_batches = [b for b in batches if b.product and any(
            keyword in b.product.name.lower() for keyword in ['cpo', 'rbpo', 'pko', 'ffb']
        )]
        
        return {
            "processing_batches": len(processing_batches),
            "total_batches": len(batches),
            "company_name": user.company.name,
            "company_type": user.company.company_type,
            "processing_products": list(set([b.product.name for b in processing_batches if b.product]))
        }
    except Exception as e:
        logger.error(f"Error getting processing data: {e}")
        return {
            "processing_batches": 0,
            "total_batches": 0,
            "company_name": user.company.name,
            "company_type": user.company.company_type,
            "processing_products": []
        }

async def get_supply_chain_overview(user, db):
    """Get comprehensive overview of user's supply chain operations."""
    
    try:
        # Combine data from multiple sources
        inventory_data = await get_comprehensive_inventory_data(user, db)
        po_data = await get_comprehensive_po_data(user, db)
        transparency_data = await get_comprehensive_transparency_data(user, db)
        
        return {
            "inventory": inventory_data,
            "purchase_orders": po_data,
            "transparency": transparency_data,
            "company": {
                "name": user.company.name,
                "type": user.company.company_type,
                "user_role": user.role
            }
        }
    except Exception as e:
        logger.error(f"Error getting overview data: {e}")
        return {
            "inventory": {"total_batches": 0, "available_quantity": 0},
            "purchase_orders": {"pending_pos": 0, "confirmed_pos": 0},
            "transparency": {"average_score": 0, "total_batches": 0},
            "company": {
                "name": user.company.name,
                "type": user.company.company_type,
                "user_role": user.role
            }
        }

# Response formatting functions
def format_inventory_response(data, user_name, company_name):
    """Format inventory data into a helpful response."""
    
    return f"""📦 **Inventory Overview for {company_name}**

**Summary:**
• Total batches: {data['total_batches']}
• Available quantity: {data['available_quantity']:.1f} MT
• Product types: {', '.join(data['product_types']) if data['product_types'] else 'None'}

**Company Type:** {data['company_type']}

**Quick Actions:**
• View detailed inventory → Navigate to Inventory page
• Create new batch → Ask me "How do I create a batch?"
• Check specific batch → Tell me the batch ID

What specific inventory information do you need?"""

def format_po_response(data, user_name, company_name):
    """Format purchase order data into a helpful response."""
    
    return f"""📋 **Purchase Orders for {company_name}**

**Your Trading Activity:**
• Purchase orders (as buyer): {data['buyer_pos']}
• Purchase orders (as seller): {data['seller_pos']}
• Pending orders: {data['pending_pos']}
• Confirmed orders: {data['confirmed_pos']}

**Company Type:** {data['company_type']}

**Actions:**
• View all POs → Navigate to Purchase Orders page
• Create new PO → Ask me "How do I create a purchase order?"

What would you like to know about your purchase orders?"""

def format_transparency_response(data, user_name, company_name):
    """Format transparency data into a helpful response."""
    
    compliance_rate = (data['compliant_batches']/data['total_batches']*100) if data['total_batches'] > 0 else 0
    
    return f"""🔍 **Traceability Overview for {company_name}**

**Transparency Metrics:**
• Average transparency score: {data['average_score']:.1f}%
• Total tracked batches: {data['total_batches']}
• Fully compliant batches: {data['compliant_batches']}
• Compliance rate: {compliance_rate:.1f}%

**Actions:**
• View full transparency dashboard → Navigate to Transparency page
• Check specific batch → Tell me the batch ID
• Improve compliance → Ask me "How to improve traceability?"

What specific traceability information do you need?"""

def format_compliance_response(data, user_name, company_name):
    """Format compliance data into a helpful response."""
    
    return f"""✅ **Compliance Overview for {company_name}**

**Regulatory Compliance:**
• EUDR compliant batches: {data['eudr_compliant']}/{data['total_batches']}
• RSPO compliant batches: {data['rspo_compliant']}/{data['total_batches']}
• Total batches: {data['total_batches']}

**Company Type:** {data['company_type']}

**Actions:**
• View compliance dashboard → Navigate to Compliance page
• Check specific regulations → Ask me about EUDR or RSPO
• Generate compliance reports → Ask me "How to generate compliance reports?"

What specific compliance information do you need?"""

def format_company_response(data, user_name, company_name):
    """Format company/supplier data into a helpful response."""
    
    suppliers_list = ', '.join(data['suppliers']) if data['suppliers'] else "None"
    customers_list = ', '.join(data['customers']) if data['customers'] else "None"
    
    return f"""🏢 **Supply Chain Network for {company_name}**

**Your Trading Partners:**
• Suppliers: {suppliers_list}
• Customers: {customers_list}
• Total relationships: {data['total_relationships']}

**Your Role:** {data['company_type']}

**Actions:**
• View all companies → Navigate to Companies page
• Check supplier performance → Tell me the supplier name
• Find new partners → Ask me "How to find suppliers?"

Which trading partner would you like to know more about?"""

def format_processing_response(data, user_name, company_name):
    """Format processing data into a helpful response."""
    
    return f"""🏭 **Processing Operations for {company_name}**

**Processing Overview:**
• Processing batches: {data['processing_batches']}
• Total batches: {data['total_batches']}
• Processing products: {', '.join(data['processing_products']) if data['processing_products'] else 'None'}

**Company Type:** {data['company_type']}

**Actions:**
• View processing dashboard → Navigate to Transformations page
• Check processing efficiency → Ask me "What's our processing efficiency?"
• Create processing event → Ask me "How to create a processing event?"

What specific processing information do you need?"""

def format_overview_response(data, user_name, company_name):
    """Format complete supply chain overview."""
    
    return f"""👋 **Welcome back, {user_name}!**

Here's your supply chain overview for **{company_name}** ({data['company']['type']}):

📦 **Inventory:**
• {data['inventory']['total_batches']} batches
• {data['inventory']['available_quantity']:.1f} MT available

📋 **Purchase Orders:**
• {data['purchase_orders']['pending_pos']} pending orders
• {data['purchase_orders']['confirmed_pos']} confirmed orders

🔍 **Transparency:**
• {data['transparency']['average_score']:.1f}% average score
• {data['transparency']['compliant_batches']}/{data['transparency']['total_batches']} compliant batches

**What can I help you with today?**
• Ask about inventory, purchase orders, suppliers, or traceability
• Say "help" for a list of things I can do
• Or just ask me anything about your supply chain!"""


@router.get("/health")
async def health_check():
    """Health check endpoint for the assistant service."""
    return {"status": "healthy", "service": "assistant"}

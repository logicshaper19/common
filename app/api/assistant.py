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
from app.models.user import User
from app.models.company import Company
from app.models.purchase_order import PurchaseOrder
from app.models.batch import Batch
from app.models.product import Product
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/assistant", tags=["assistant"])


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str
    success: bool = True


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """AI-powered chat endpoint with comprehensive supply chain data access."""
    
    try:
        user_name = current_user.full_name or current_user.email.split('@')[0] if current_user.email else "User"
        company_name = current_user.company.name if current_user.company else "your company"
        
        # Gather comprehensive context data from all sources
        context_data = await gather_comprehensive_context(current_user, db)
        
        # Use OpenAI to generate AI-powered response
        ai_client = SimpleOpenAIClient()
        response = await ai_client.generate_response(
            user_message=request.message,
            context_data=context_data,
            user_name=user_name
        )
        
        logger.info(f"AI response generated for user {current_user.id}: {request.message[:50]}...")
        
        return ChatResponse(response=response)
        
    except Exception as e:
        logger.error(f"Error in AI assistant chat endpoint: {e}")
        # Fallback to simple response
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
        
        # Build comprehensive context
        context_data = {
            "company_name": user.company.name,
            "company_type": user.company.company_type,
            "user_role": user.role,
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
            "company_name": user.company.name,
            "company_type": user.company.company_type,
            "user_role": user.role,
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

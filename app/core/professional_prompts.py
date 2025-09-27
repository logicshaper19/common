"""
Professional supply chain prompts that enforce business-appropriate communication.
Creates context-aware prompts with real user data integration.
"""

from typing import Dict, Any
from app.core.logging import get_logger

logger = get_logger(__name__)


class ProfessionalSupplyChainPrompts:
    """Professional prompts for supply chain AI assistant."""
    
    @staticmethod
    def get_professional_system_prompt() -> str:
        """System prompt that enforces professional business communication."""
        
        return """You are a professional supply chain assistant for the Common Supply Chain Platform.

## Communication Guidelines:
- Use PROFESSIONAL BUSINESS LANGUAGE at all times
- Use minimal, strategic formatting for clarity and readability
- NO casual expressions or excessive emojis in business responses
- Present information in well-organized sections with clear hierarchy
- Use proper industry terminology without over-explaining basic concepts

## Response Structure & Formatting:
1. **Key Information Headers**: Use bold for main section titles and critical data labels
2. **Organized Content**: Group related information into logical sections
3. **Clear Data Presentation**: Format numbers, dates, and metrics for easy scanning
4. **Actionable Items**: Present next steps in numbered or bulleted format
5. **Professional Layout**: Use spacing and structure for readability

## Formatting Guidelines:
- **Section Headers**: Bold for main topics (e.g., **Purchase Order Details**, **Current Status**)
- **Key Labels**: Bold for important data fields (e.g., **Status:** Confirmed, **Quantity:** 500 MT)
- **Bullet Points**: Use • for lists and sub-items
- **Numbers**: Present clearly with units (e.g., 500 MT, 95.2%, October 15, 2025)
- **Line Breaks**: Use spacing between sections for visual clarity

## Professional Formatting Examples:
GOOD: 
**Purchase Order PO-202509-0001:**
**Status:** Confirmed
**Product:** CPO (Crude Palm Oil)  
**Quantity:** 500 MT
**Delivery Date:** October 15, 2025

• Key specifications: FFA < 3.5%, Moisture < 0.1%
• Transparency score: 95.2%
• Payment terms: Net 30 days

**Next Steps:**
1. Review delivery schedule
2. Verify quality specifications
3. Confirm logistics arrangements

## Content Focus:
- Reference actual data from the user's company operations
- Use specific palm oil industry terminology appropriately
- Provide quantitative information when available
- Include relevant compliance and regulatory context
- Suggest practical business actions

## Business Context:
You are addressing supply chain professionals who expect clear, actionable business information presented in standard professional format. Always be helpful, accurate, and focused on practical supply chain management."""

    @staticmethod
    def get_context_aware_prompt(user_context: Dict[str, Any]) -> str:
        """Generate context-aware prompt with user's actual data."""
        
        user_info = user_context.get('user_info', {})
        current_data = user_context.get('current_data', {})
        business_rules = user_context.get('business_rules', {})
        
        prompt_parts = [
            "## Current User Context:",
            f"User: {user_info.get('name', 'Unknown')}",
            f"Company: {user_info.get('company_name', 'Unknown Company')}",
            f"Role: {user_info.get('company_type', 'Unknown')}",
            f"Environment: {business_rules.get('environment', 'development')}"
        ]
        
        # Add inventory context if available
        if 'inventory' in current_data:
            inv = current_data['inventory']
            prompt_parts.extend([
                "",
                "## Live Inventory Data:",
                f"• Total batches: {inv.get('total_batches', 0)}",
                f"• Available batches: {inv.get('available_batches', 0)}",
                f"• Total quantity: {inv.get('total_quantity', 0):.1f} MT"
            ])
            
            if inv.get('avg_transparency', 0) > 0:
                prompt_parts.append(f"• Average transparency score: {inv.get('avg_transparency', 0):.1f}%")

        # Add PO context if available
        if 'purchase_orders' in current_data:
            po = current_data['purchase_orders']
            prompt_parts.extend([
                "",
                "## Purchase Order Activity:",
                f"• Orders as buyer: {po.get('as_buyer', 0)}",
                f"• Orders as seller: {po.get('as_seller', 0)}",
                f"• Pending orders: {po.get('pending_orders', 0)}"
            ])

        # Add trading partners if available
        if 'trading_partners' in current_data and current_data['trading_partners']:
            partners = current_data['trading_partners'][:5]  # Limit to 5
            prompt_parts.extend([
                "",
                f"## Trading Partners: {', '.join(partners)}"
            ])
        
        # Add business configuration
        if business_rules:
            prompt_parts.extend([
                "",
                "## Business Configuration:",
                f"• Transparency degradation factor: {business_rules.get('transparency_degradation_factor', 'not configured')}",
                f"• Transparency timeout: {business_rules.get('transparency_timeout', 'not configured')}s"
            ])

        prompt_parts.extend([
            "",
            "## Instructions:",
            "Provide professional, factual responses using this actual data context.",
            "Do not use markdown formatting.",
            "Present information clearly and suggest actionable next steps based on the user's current business situation.",
            "Reference specific numbers and metrics from the live data when relevant."
        ])
        
        return '\n'.join(prompt_parts)
    
    @staticmethod
    def get_data_driven_prompt(query_type: str, data: Dict[str, Any]) -> str:
        """Generate prompts that focus on specific data types."""
        
        if query_type == "inventory":
            return ProfessionalSupplyChainPrompts._get_inventory_prompt(data)
        elif query_type == "purchase_orders":
            return ProfessionalSupplyChainPrompts._get_po_prompt(data)
        elif query_type == "transparency":
            return ProfessionalSupplyChainPrompts._get_transparency_prompt(data)
        elif query_type == "compliance":
            return ProfessionalSupplyChainPrompts._get_compliance_prompt(data)
        else:
            return ProfessionalSupplyChainPrompts._get_general_prompt(data)
    
    @staticmethod
    def _get_inventory_prompt(data: Dict[str, Any]) -> str:
        """Generate inventory-focused prompt."""
        
        inv_data = data.get('current_data', {}).get('inventory', {})
        
        return f"""## Inventory Analysis Request

Current Inventory Status:
• Total batches: {inv_data.get('total_batches', 0)}
• Available batches: {inv_data.get('available_batches', 0)}
• Total quantity: {inv_data.get('total_quantity', 0):.1f} MT
• Average transparency: {inv_data.get('avg_transparency', 0):.1f}%

Focus on:
- Current stock levels and availability
- Product distribution and allocation
- Transparency scores and quality metrics
- Inventory optimization recommendations
- Batch utilization and turnover"""
    
    @staticmethod
    def _get_po_prompt(data: Dict[str, Any]) -> str:
        """Generate purchase order-focused prompt."""
        
        po_data = data.get('current_data', {}).get('purchase_orders', {})
        
        return f"""## Purchase Order Analysis Request

Current PO Status:
• Orders as buyer: {po_data.get('as_buyer', 0)}
• Orders as seller: {po_data.get('as_seller', 0)}
• Pending orders: {po_data.get('pending_orders', 0)}
• Total active orders: {po_data.get('total_orders', 0)}

Focus on:
- Purchase order status and workflow
- Buyer and seller relationships
- Order fulfillment and delivery
- Contract terms and compliance
- Trading partner performance"""
    
    @staticmethod
    def _get_transparency_prompt(data: Dict[str, Any]) -> str:
        """Generate transparency-focused prompt."""
        
        business_rules = data.get('business_rules', {})
        inv_data = data.get('current_data', {}).get('inventory', {})
        
        return f"""## Transparency Analysis Request

Transparency Configuration:
• Degradation factor: {business_rules.get('transparency_degradation_factor', 'not configured')}
• Calculation timeout: {business_rules.get('transparency_timeout', 'not configured')}s
• Current average score: {inv_data.get('avg_transparency', 0):.1f}%

Focus on:
- Supply chain traceability scores
- GPS verification and documentation
- Upstream and downstream visibility
- Compliance with transparency requirements
- Improvement recommendations"""
    
    @staticmethod
    def _get_compliance_prompt(data: Dict[str, Any]) -> str:
        """Generate compliance-focused prompt."""
        
        return """## Compliance Analysis Request

Focus on:
- EUDR compliance status and requirements
- RSPO certification and standards
- GPS coordinates and forest risk assessment
- Certificate validity and documentation
- Regulatory compliance gaps and actions needed"""
    
    @staticmethod
    def _get_general_prompt(data: Dict[str, Any]) -> str:
        """Generate general analysis prompt."""
        
        return """## General Supply Chain Analysis Request

Provide a comprehensive overview covering:
- Current operational status
- Key performance indicators
- Business relationships and trading activity
- Compliance and transparency status
- Recommended actions and next steps"""
    
    @staticmethod
    def get_error_handling_prompt(error_type: str) -> str:
        """Generate professional error handling prompts."""
        
        error_prompts = {
            "data_unavailable": """## Data Availability Issue

The requested data is currently unavailable. Provide guidance on:
- Alternative ways to access the information
- Expected timeframe for data availability
- Contact information for technical support
- Interim actions the user can take""",
            
            "permission_denied": """## Access Permission Issue

The user doesn't have permission for this data. Explain:
- What level of access is required
- Who can grant the necessary permissions
- Alternative information sources available
- Steps to request appropriate access""",
            
            "system_error": """## System Technical Issue

A technical error has occurred. Provide:
- Acknowledgment of the issue
- Expected resolution timeframe
- Alternative ways to get assistance
- Steps to report the issue if it persists"""
        }
        
        return error_prompts.get(error_type, error_prompts["system_error"])
    
    @staticmethod
    def get_actionable_recommendations_prompt(context: Dict[str, Any]) -> str:
        """Generate prompts that focus on actionable business recommendations."""
        
        user_info = context.get('user_info', {})
        company_type = user_info.get('company_type', 'unknown')
        
        type_specific_actions = {
            "plantation_grower": [
                "FFB quality optimization",
                "Yield improvement strategies",
                "Sustainability certification",
                "GPS tracking implementation"
            ],
            "mill_processor": [
                "OER optimization",
                "Energy efficiency improvements",
                "Quality control measures",
                "Traceability system enhancement"
            ],
            "refinery_crusher": [
                "Processing efficiency analysis",
                "Product quality assurance",
                "Supply chain optimization",
                "Market demand planning"
            ],
            "trader_aggregator": [
                "Market analysis and pricing",
                "Inventory management",
                "Supplier relationship optimization",
                "Risk management strategies"
            ],
            "brand": [
                "Supply chain transparency",
                "Compliance monitoring",
                "Supplier verification",
                "Sustainability reporting"
            ]
        }
        
        actions = type_specific_actions.get(company_type, [
            "Operational efficiency improvements",
            "Compliance verification",
            "Data quality enhancement",
            "Performance monitoring"
        ])
        
        return f"""## Actionable Business Recommendations

Based on the company type ({company_type}), focus recommendations on:
{chr(10).join('• ' + action for action in actions)}

Ensure all recommendations are:
- Specific and measurable
- Achievable with current resources
- Relevant to business objectives
- Time-bound with clear milestones"""

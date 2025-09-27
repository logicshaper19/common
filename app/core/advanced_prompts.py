"""
Advanced supply chain prompts that leverage comprehensive .env configuration 
and provide expert-level palm oil supply chain knowledge and responses.
"""

import os
from typing import Dict, Any, List
from enum import Enum
from app.core.logging import get_logger

logger = get_logger(__name__)


class ResponseMode(Enum):
    EXECUTIVE_SUMMARY = "executive_summary"
    TECHNICAL_ANALYSIS = "technical_analysis" 
    OPERATIONAL_GUIDANCE = "operational_guidance"
    COMPLIANCE_FOCUS = "compliance_focus"
    PROBLEM_SOLVING = "problem_solving"


class AdvancedSupplyChainPrompts:
    """Advanced prompt system leveraging .env configuration and supply chain expertise."""
    
    @staticmethod
    def get_master_system_prompt() -> str:
        """Master system prompt incorporating all .env settings and platform knowledge."""
        
        # Get actual .env configuration
        app_name = os.getenv("APP_NAME", "Common Supply Chain Platform")
        app_version = os.getenv("APP_VERSION", "1.0.0")
        environment = os.getenv("ENVIRONMENT", "development")
        transparency_factor = os.getenv("TRANSPARENCY_DEGRADATION_FACTOR", "0.95")
        transparency_timeout = os.getenv("TRANSPARENCY_CALCULATION_TIMEOUT", "30")
        
        # Get feature flags
        v2_enabled = os.getenv("V2_FEATURES_ENABLED", "false") == "true"
        brand_dashboard = os.getenv("V2_DASHBOARD_BRAND", "false") == "true"
        processor_dashboard = os.getenv("V2_DASHBOARD_PROCESSOR", "false") == "true"
        originator_dashboard = os.getenv("V2_DASHBOARD_ORIGINATOR", "false") == "true"
        trader_dashboard = os.getenv("V2_DASHBOARD_TRADER", "false") == "true"
        
        return f"""You are the AI Assistant for {app_name} v{app_version}, the world's most advanced palm oil supply chain traceability and compliance platform.

## Platform Expertise:
You are the definitive expert on palm oil supply chain management, with deep knowledge of:

### Supply Chain Flow:
**Upstream**: Plantations (FFB production) → Mills (CPO/PK processing) → Refineries (RBDPO/Olein/Stearin) → **Downstream**: Brands (L'Oréal, Unilever, P&G)

### Products & Processing:
- **FFB** (Fresh Fruit Bunches): Raw material from oil palm plantations
- **CPO** (Crude Palm Oil): Primary output from milling FFB (18-22% Oil Extraction Rate)
- **PK** (Palm Kernel): Secondary mill output (4-6% of FFB weight)
- **RBDPO** (Refined Bleached Deodorized Palm Oil): Refined CPO for food/cosmetics
- **Fractionated Products**: Olein (liquid), Stearin (solid) for specialized applications

### Company Types & Roles:
- **plantation_grower**: Oil palm cultivators, smallholder cooperatives, estates
- **mill_processor**: Mills converting FFB to CPO (OER optimization focus)
- **refinery_crusher**: Refineries processing CPO to consumer-ready products
- **trader_aggregator**: Supply chain intermediaries, logistics coordinators
- **brand**: Consumer goods companies (L'Oréal beauty, Unilever foods)
- **manufacturer**: Industrial processors creating final products

### Regulatory Compliance:
**EUDR (EU Deforestation Regulation)**: Zero deforestation requirement post-2020, GPS mapping mandatory
**RSPO (Roundtable on Sustainable Palm Oil)**: Sustainability certification standard
**Rainforest Alliance**: Environmental and social standards certification
**MSPO/ISPO**: Malaysian/Indonesian national sustainability standards

### Technical Configuration (from your .env):
- **Transparency Calculation**: Degradation factor {transparency_factor} (each missing data point reduces score by {(1 - float(transparency_factor)) * 100:.1f}%)
- **System Timeout**: {transparency_timeout} seconds for complex supply chain calculations
- **Environment**: Currently running in {environment} mode
- **V2 Features**: {"Enabled" if v2_enabled else "Disabled"}

### Dashboard Features Available:
{"• Brand Dashboard: Advanced transparency tracking, supplier risk assessment" if brand_dashboard else ""}
{"• Processor Dashboard: OER optimization, yield analytics, energy efficiency" if processor_dashboard else ""}
{"• Originator Dashboard: Harvest planning, GPS compliance, plantation management" if originator_dashboard else ""}
{"• Trader Dashboard: Inventory optimization, market insights, logistics coordination" if trader_dashboard else ""}

### Response Excellence Standards:
1. **Industry Authority**: Use precise palm oil terminology without over-explanation
2. **Data-Driven**: Reference actual user data, specific metrics, quantifiable insights
3. **Actionable**: Provide clear next steps, specific recommendations, business impact
4. **Context-Aware**: Adapt advice to company type, role, and current business situation
5. **Compliance-Focused**: Always consider regulatory implications (EUDR, RSPO, quality standards)
6. **Professional**: Business-appropriate language, no markdown formatting, clean structure

### Performance Benchmarks to Reference:
- **Excellent OER**: 20-22% (Oil Extraction Rate for mills)
- **Target Transparency**: 95% (best practice), 90% (good), 70% (minimum compliance)
- **Energy Efficiency**: 35-45 kWh/MT (mill processing)
- **Quality Standards**: FFA <3%, Moisture <0.1%, Impurities <0.02%

Your responses should demonstrate that you understand the complete palm oil supply chain ecosystem, from plantation management through consumer products, with deep expertise in sustainability, compliance, and operational efficiency."""

    @staticmethod
    def get_context_aware_prompt(user_context: Dict[str, Any], response_mode: ResponseMode) -> str:
        """Generate context-aware prompts based on user data and desired response type."""
        
        user_info = user_context.get("user_info", {})
        company_name = user_info.get("company_name", "Unknown Company")
        company_type = user_info.get("company_type", "unknown")
        user_name = user_info.get("first_name", "User")
        
        # Get actual data context
        inventory = user_context.get("current_data", {}).get("inventory", {})
        purchase_orders = user_context.get("current_data", {}).get("purchase_orders", {})
        trading_partners = user_context.get("current_data", {}).get("trading_partners", [])
        
        base_context = f"""
## Current User Profile:
**User**: {user_name} at {company_name}
**Company Type**: {company_type}
**Role in Supply Chain**: {AdvancedSupplyChainPrompts._get_supply_chain_role(company_type)}

## Live Business Context:"""

        # Add inventory context with business interpretation
        if inventory and not inventory.get("error"):
            total_qty = inventory.get("total_quantity", 0)
            avg_transparency = inventory.get("avg_transparency", 0)
            available_batches = inventory.get("available_batches", 0)
            
            base_context += f"""
**Inventory Position**: {total_qty} MT across {inventory.get("total_batches", 0)} batches
**Operational Status**: {available_batches} batches available for allocation
**Compliance Position**: {avg_transparency}% average transparency ({AdvancedSupplyChainPrompts._interpret_transparency_score(avg_transparency)})"""

        # Add purchase order context with supply chain insights
        if purchase_orders and not purchase_orders.get("error"):
            buyer_orders = purchase_orders.get("as_buyer", 0)
            seller_orders = purchase_orders.get("as_seller", 0)
            pending = purchase_orders.get("pending_orders", 0)
            
            base_context += f"""
**Trading Activity**: {buyer_orders} upstream orders, {seller_orders} downstream orders
**Supply Chain Flow**: {"Healthy bilateral trading" if buyer_orders > 0 and seller_orders > 0 else "Primarily " + ("buying" if buyer_orders > seller_orders else "selling")}
**Operational Priority**: {pending} orders requiring immediate attention"""

        # Add trading network context
        if trading_partners:
            partner_count = len(trading_partners)
            partner_list = ", ".join(trading_partners[:3])
            if len(trading_partners) > 3:
                partner_list += f" + {len(trading_partners) - 3} others"
                
            base_context += f"""
**Trading Network**: {partner_count} active relationships ({partner_list})
**Supply Chain Depth**: {AdvancedSupplyChainPrompts._assess_supply_chain_depth(partner_count)}"""

        # Add response mode specific guidance
        mode_guidance = AdvancedSupplyChainPrompts._get_response_mode_guidance(response_mode, company_type)
        
        return f"{base_context}\n\n## Response Requirements:\n{mode_guidance}"

    @staticmethod
    def _get_supply_chain_role(company_type: str) -> str:
        """Get detailed supply chain role description."""
        roles = {
            "plantation_grower": "Upstream originator - FFB production, sustainability compliance",
            "mill_processor": "Primary processor - FFB to CPO conversion, yield optimization",
            "refinery_crusher": "Secondary processor - CPO refinement to consumer products",
            "trader_aggregator": "Supply chain coordinator - inventory management, logistics",
            "brand": "Downstream customer - sustainability sourcing, consumer products",
            "manufacturer": "Final processor - consumer goods manufacturing"
        }
        return roles.get(company_type, "Supply chain participant")

    @staticmethod
    def _interpret_transparency_score(score: float) -> str:
        """Interpret transparency scores with business context."""
        if score >= 95:
            return "Industry leading compliance"
        elif score >= 90:
            return "Strong compliance position"
        elif score >= 80:
            return "Meeting requirements, improvement opportunities"
        elif score >= 70:
            return "Minimum compliance, risks present"
        else:
            return "Below compliance threshold - immediate action required"

    @staticmethod
    def _assess_supply_chain_depth(partner_count: int) -> str:
        """Assess supply chain network strength."""
        if partner_count >= 10:
            return "Diversified network, strong resilience"
        elif partner_count >= 5:
            return "Moderate diversification, good foundation"
        elif partner_count >= 2:
            return "Limited diversification, concentration risk"
        else:
            return "Single-partner dependency, high risk"

    @staticmethod
    def _get_response_mode_guidance(mode: ResponseMode, company_type: str) -> str:
        """Get specific guidance based on response mode and company type."""
        
        base_guidance = {
            ResponseMode.EXECUTIVE_SUMMARY: """
Provide a concise executive summary focusing on:
• Key performance indicators and business impact
• Strategic recommendations with quantified benefits
• Risk assessment and mitigation priorities
• Competitive positioning and market opportunities""",
            
            ResponseMode.TECHNICAL_ANALYSIS: """
Provide detailed technical analysis including:
• Specific process parameters and optimization opportunities
• Quantitative performance metrics and benchmarking
• Technical root cause analysis and solutions
• Implementation specifications and requirements""",
            
            ResponseMode.OPERATIONAL_GUIDANCE: """
Provide actionable operational guidance covering:
• Immediate action items with clear priorities
• Step-by-step implementation procedures
• Resource requirements and timeline estimates
• Success metrics and monitoring approaches""",
            
            ResponseMode.COMPLIANCE_FOCUS: """
Provide compliance-focused analysis addressing:
• Regulatory requirement gaps and remediation plans
• Certification status and renewal requirements
• Risk assessment with specific mitigation strategies
• Documentation and audit preparation needs""",
            
            ResponseMode.PROBLEM_SOLVING: """
Provide systematic problem-solving approach:
• Root cause analysis with evidence-based conclusions
• Multiple solution alternatives with trade-off analysis
• Implementation roadmap with risk mitigation
• Success metrics and contingency planning"""
        }
        
        company_specific = {
            "plantation_grower": "Focus on yield optimization, sustainability compliance, and harvest planning",
            "mill_processor": "Emphasize OER improvements, energy efficiency, and processing optimization",
            "refinery_crusher": "Highlight product quality, yield rates, and market positioning",
            "trader_aggregator": "Focus on inventory optimization, market insights, and logistics efficiency",
            "brand": "Emphasize transparency, supplier risk, and sustainability credentials",
            "manufacturer": "Focus on supply security, cost optimization, and quality consistency"
        }
        
        return f"{base_guidance.get(mode, '')}\n\n**Company-Specific Focus**: {company_specific.get(company_type, 'General supply chain optimization')}"

    @staticmethod
    def determine_response_mode(message: str, user_context: Dict[str, Any]) -> ResponseMode:
        """Automatically determine the best response mode based on message and context."""
        
        message_lower = message.lower()
        
        # Executive summary keywords
        if any(word in message_lower for word in ["overview", "summary", "dashboard", "status", "performance"]):
            return ResponseMode.EXECUTIVE_SUMMARY
            
        # Technical analysis keywords
        elif any(word in message_lower for word in ["oer", "yield", "efficiency", "optimization", "technical", "process"]):
            return ResponseMode.TECHNICAL_ANALYSIS
            
        # Operational guidance keywords
        elif any(word in message_lower for word in ["how to", "what should", "next steps", "implement", "action"]):
            return ResponseMode.OPERATIONAL_GUIDANCE
            
        # Compliance focus keywords
        elif any(word in message_lower for word in ["compliance", "eudr", "rspo", "certification", "audit", "regulation"]):
            return ResponseMode.COMPLIANCE_FOCUS
            
        # Problem solving keywords
        elif any(word in message_lower for word in ["problem", "issue", "trouble", "fix", "solve", "error"]):
            return ResponseMode.PROBLEM_SOLVING
            
        # Default based on company type
        company_type = user_context.get("user_info", {}).get("company_type", "")
        if company_type == "brand":
            return ResponseMode.COMPLIANCE_FOCUS
        elif company_type in ["mill_processor", "refinery_crusher"]:
            return ResponseMode.TECHNICAL_ANALYSIS
        else:
            return ResponseMode.EXECUTIVE_SUMMARY

    @staticmethod
    def get_enhanced_industry_context() -> str:
        """Get enhanced industry context for deeper supply chain expertise."""
        
        return """
## Advanced Industry Context:

### Supply Chain Economics:
- **CPO Pricing**: Typically $600-900/MT (varies by quality, location, sustainability premiums)
- **Processing Margins**: Mills typically achieve 15-25% gross margins on CPO sales
- **Transparency Premium**: Certified/traceable palm oil commands 5-15% price premium
- **Quality Discounts**: FFA >3% can reduce value by $20-50/MT

### Critical Success Factors by Role:
**Plantation Growers**: FFB quality (low FFA), yield per hectare, RSPO certification, GPS mapping
**Mill Processors**: OER optimization (target 20%+), energy efficiency, throughput capacity
**Refineries**: Product yield, quality consistency, market demand alignment
**Traders**: Inventory turnover, transparency scoring, relationship management
**Brands**: Supply chain transparency, compliance verification, sustainability reporting

### Risk Management:
- **Quality Risks**: FFA degradation, moisture content, contamination
- **Compliance Risks**: EUDR mapping gaps, certification lapses, audit findings
- **Operational Risks**: Processing downtime, logistics delays, supply disruptions
- **Market Risks**: Price volatility, demand fluctuations, regulatory changes

### Performance Optimization:
- **Transparency Enhancement**: GPS verification, document digitization, supplier engagement
- **Quality Improvement**: Storage optimization, processing efficiency, contamination prevention
- **Compliance Assurance**: Regular audits, certification maintenance, continuous monitoring
- **Cost Reduction**: Energy efficiency, waste minimization, process automation"""

    @staticmethod
    def get_compliance_intelligence_prompt() -> str:
        """Get specialized compliance intelligence for regulatory guidance."""
        
        return """
## Compliance Intelligence Framework:

### EUDR Compliance Checklist:
1. **Geographic Verification**: GPS coordinates for all production areas
2. **Deforestation Assessment**: Satellite imagery analysis post-2020
3. **Due Diligence Documentation**: Risk assessment and mitigation measures
4. **Supply Chain Mapping**: Complete traceability to farm level
5. **Regular Monitoring**: Ongoing surveillance and verification

### RSPO Certification Requirements:
- **Principle 1**: Legal compliance and use of best practices
- **Principle 2**: Environmental responsibility and conservation
- **Principle 3**: Consideration for employees and communities
- **Principle 4**: Responsible development of new plantings
- **Principle 5**: Environmental responsibility and conservation of biodiversity

### Quality Compliance Standards:
**CPO Quality Parameters**: FFA <3%, Moisture <0.1%, Impurities <0.02%
**Storage Requirements**: Temperature control, contamination prevention
**Transport Standards**: Food-grade containers, temperature monitoring
**Documentation**: Certificates of analysis, transport records, quality assessments

### Audit Preparation Guidelines:
- **Document Management**: Digital records, version control, access management
- **Process Documentation**: Standard operating procedures, quality manuals
- **Training Records**: Staff competency, continuous education, certification
- **Continuous Improvement**: Corrective actions, preventive measures, performance monitoring"""

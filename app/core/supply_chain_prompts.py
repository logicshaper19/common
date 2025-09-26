"""
Enhanced supply chain prompts with schema awareness.
"""
from enum import Enum
from typing import Tuple, Dict, Any
from app.core.schema_context import SupplyChainSchemaContext

class InteractionType(Enum):
    """Types of user interactions with different temperature requirements."""
    FACTUAL_QUERY = "factual_query"
    ANALYTICAL_REQUEST = "analytical_request" 
    CREATIVE_PLANNING = "creative_planning"
    TROUBLESHOOTING = "troubleshooting"
    GENERAL_CONVERSATION = "general_conversation"

class EnhancedSupplyChainPrompts:
    
    @staticmethod
    def get_schema_aware_system_prompt() -> str:
        """System prompt that includes safe database schema context."""
        
        schema_context = SupplyChainSchemaContext.get_schema_context()
        
        return f"""You are an AI assistant for the Common Supply Chain Platform with deep understanding of the database structure and business logic.

## Database Schema Context:

### Core Tables & Relationships:
**Companies Table**: {schema_context['tables']['companies']['description']}
- Key fields: {', '.join(schema_context['tables']['companies']['key_fields'])}
- Company types: {', '.join(schema_context['tables']['companies']['company_types'])}
- Example companies: {', '.join(schema_context['tables']['companies']['sample_companies'])}

**Purchase Orders**: {schema_context['tables']['purchase_orders']['description']}
- Statuses: {', '.join(schema_context['tables']['purchase_orders']['statuses'])}
- Typical flow: {schema_context['tables']['purchase_orders']['typical_flow']}

**Batches/Inventory**: {schema_context['tables']['batches']['description']}
- Transparency calculation: {schema_context['tables']['batches']['transparency_calculation']}
- Statuses: {', '.join(schema_context['tables']['batches']['statuses'])}

**Products**: Palm oil products - {', '.join(schema_context['tables']['products']['product_types'])}
- Processing flow: {schema_context['tables']['products']['processing_flow']}

**Transformations**: Processing operations with yield tracking
- Types: {', '.join(schema_context['tables']['transformations']['transformation_types'])}
- Typical yields: FFB→CPO: 18-22%, CPO→RBDPO: 95-98%

### Business Rules You Must Follow:
1. **Transparency Scoring**: Uses degradation factor {schema_context['business_rules']['transparency_calculation']['degradation_factor']}, timeout {schema_context['business_rules']['transparency_calculation']['timeout_seconds']}s
2. **OER Targets**: {schema_context['business_rules']['processing_constraints']['oer_target']}
3. **EUDR Compliance**: {schema_context['business_rules']['compliance_requirements']['eudr_gps_required']}

### Data Relationships:
- Supply chain: {schema_context['relationships']['supply_chain_flow']}
- Traceability: {schema_context['relationships']['traceability']}

### Feature Access (from .env flags):
- Brand dashboard: {schema_context['feature_flags']['v2_dashboards']['brand']}
- Processor dashboard: {schema_context['feature_flags']['v2_dashboards']['processor']}
- Originator dashboard: {schema_context['feature_flags']['v2_dashboards']['originator']}

### Security & Data Access:
- Never expose: {', '.join(schema_context['safety_measures']['excluded_fields'])}
- Access by role: {schema_context['safety_measures']['access_levels']}

### Query Examples You Can Reference:
**Inventory Queries:**
{chr(10).join(['- ' + q for q in schema_context['query_examples']['inventory_queries']])}

**Purchase Order Queries:**
{chr(10).join(['- ' + q for q in schema_context['query_examples']['purchase_order_queries']])}

**Transparency Queries:**
{chr(10).join(['- ' + q for q in schema_context['query_examples']['transparency_queries']])}

## Response Guidelines:
1. **Reference actual fields** - Use real column names and table relationships
2. **Respect data constraints** - Don't suggest operations that violate business rules
3. **Consider feature flags** - Only reference available dashboard features
4. **Use proper terminology** - FFB, CPO, RBDPO, OER, transparency score, etc.
5. **Understand relationships** - Know how companies, POs, batches, and transformations connect

When users ask about data, you understand exactly what exists and can provide accurate, actionable responses based on the actual database structure."""
    
    @staticmethod
    def classify_interaction_type(user_message: str, user_context: Dict[str, Any]) -> Tuple[InteractionType, float]:
        """Classify user interaction and return appropriate temperature."""
        
        # Analyze message content to determine interaction type
        message_lower = user_message.lower()
        
        # Factual queries (low temperature)
        factual_keywords = ['what is', 'how many', 'when did', 'where is', 'show me', 'list', 'status of']
        if any(keyword in message_lower for keyword in factual_keywords):
            return InteractionType.FACTUAL_QUERY, 0.1
        
        # Analytical requests (medium temperature)  
        analytical_keywords = ['analyze', 'compare', 'trend', 'performance', 'why', 'impact', 'correlation']
        if any(keyword in message_lower for keyword in analytical_keywords):
            return InteractionType.ANALYTICAL_REQUEST, 0.3
        
        # Troubleshooting (medium temperature)
        troubleshooting_keywords = ['problem', 'error', 'issue', 'not working', 'fix', 'troubleshoot']
        if any(keyword in message_lower for keyword in troubleshooting_keywords):
            return InteractionType.TROUBLESHOOTING, 0.4
        
        # Creative planning (high temperature)
        creative_keywords = ['plan', 'strategy', 'idea', 'suggest', 'recommend', 'optimize', 'improve']
        if any(keyword in message_lower for keyword in creative_keywords):
            return InteractionType.CREATIVE_PLANNING, 0.7
        
        # Default to general conversation
        return InteractionType.GENERAL_CONVERSATION, 0.5
    
    @staticmethod
    def get_conversation_context_prompt(interaction_type: InteractionType) -> str:
        """Get context-specific prompt based on interaction type."""
        
        prompts = {
            InteractionType.FACTUAL_QUERY: "Focus on providing accurate, specific facts from the database.",
            InteractionType.ANALYTICAL_REQUEST: "Provide analytical insights with data-driven reasoning.",
            InteractionType.CREATIVE_PLANNING: "Offer creative solutions and strategic recommendations.",
            InteractionType.TROUBLESHOOTING: "Help identify and resolve operational issues systematically.", 
            InteractionType.GENERAL_CONVERSATION: "Engage naturally while staying focused on supply chain topics."
        }
        
        return prompts.get(interaction_type, prompts[InteractionType.GENERAL_CONVERSATION])
    
    @staticmethod
    def get_enhanced_system_prompt() -> str:
        """Get the enhanced system prompt for general use."""
        return "You are a knowledgeable supply chain assistant with deep expertise in palm oil operations."

    @staticmethod
    def get_query_generation_context() -> str:
        """Context for generating accurate database queries."""
        
        return """
## Safe Query Patterns:

### Inventory Queries:
```sql
-- Get available inventory by company
SELECT batch_id, product.name, quantity, status, transparency_score 
FROM batches 
JOIN products ON batches.product_id = products.id
WHERE company_id = ? AND status = 'available'

-- Transparency score analysis
SELECT AVG(transparency_score), company.name
FROM batches 
JOIN companies ON batches.company_id = companies.id
GROUP BY companies.name
```

### Supply Chain Queries:
```sql
-- Purchase order flow
SELECT buyer.name, seller.name, product.name, quantity, status
FROM purchase_orders po
JOIN companies buyer ON po.buyer_company_id = buyer.id
JOIN companies seller ON po.seller_company_id = seller.id  
JOIN products ON po.product_id = products.id

-- Processing yield analysis
SELECT transformation_type, AVG(yield_percentage)
FROM transformations
GROUP BY transformation_type
```

Always use parameterized queries and respect user's company access permissions."""
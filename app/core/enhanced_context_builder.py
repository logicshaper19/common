"""
Enhanced user context builder that includes database schema awareness.
"""
from typing import Dict, Any
from app.core.schema_context import SupplyChainSchemaContext
from app.core.logging import get_logger

logger = get_logger(__name__)

class EnhancedUserContextBuilder:
    """Builds enhanced user context with schema awareness and data access patterns."""
    
    def __init__(self):
        self.schema_context = SupplyChainSchemaContext()
    
    def build_schema_aware_context(self, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance user context with schema awareness and access patterns."""
        
        try:
            schema_data = self.schema_context.get_schema_context()
            user_role = user_context.get('user_role', 'unknown')
            company_type = user_context.get('company_type', 'unknown')
            
            enhanced_context = {
                **user_context,
                
                # Add schema context
                "available_tables": self._get_accessible_tables(user_role, company_type, schema_data),
                "query_patterns": self._get_query_patterns_for_role(user_role, schema_data),
                "data_constraints": self._get_data_constraints(user_role, schema_data),
                "business_rules": schema_data['business_rules'],
                
                # Add feature flags
                "feature_access": {
                    "dashboards": schema_data['feature_flags']['v2_dashboards'],
                    "notifications": schema_data['feature_flags']['notifications']
                },
                
                # Add relationship guidance
                "data_relationships": schema_data['relationships'],
                
                # Add safety measures
                "security_context": {
                    "excluded_fields": schema_data['safety_measures']['excluded_fields'],
                    "access_level": schema_data['safety_measures']['access_levels'].get(company_type, []),
                    "masking_rules": schema_data['safety_measures']['data_masking']
                }
            }
            
            logger.info(f"Enhanced context built for {user_role} at {company_type}")
            return enhanced_context
            
        except Exception as e:
            logger.error(f"Failed to build enhanced context: {e}")
            return user_context  # Fallback to original context
    
    def _get_accessible_tables(self, user_role: str, company_type: str, schema_data: Dict[str, Any]) -> Dict[str, Any]:
        """Determine which tables and fields the user can access."""
        
        base_tables = {
            "companies": schema_data['tables']['companies'],
            "products": schema_data['tables']['products']
        }
        
        # Role-based table access
        if company_type == "plantation_grower":
            base_tables.update({
                "batches": schema_data['tables']['batches'],
                "transformations": schema_data['tables']['transformations']
            })
        elif company_type == "mill_processor":
            base_tables.update({
                "batches": schema_data['tables']['batches'],
                "transformations": schema_data['tables']['transformations'],
                "purchase_orders": schema_data['tables']['purchase_orders']
            })
        elif company_type == "brand":
            base_tables.update({
                "purchase_orders": schema_data['tables']['purchase_orders'],
                "transparency": {"description": "Supply chain transparency data"}
            })
        
        return base_tables
    
    def _get_query_patterns_for_role(self, user_role: str, schema_data: Dict[str, Any]) -> Dict[str, list]:
        """Get relevant query patterns based on user role."""
        
        patterns = {}
        
        if user_role in ["manager", "analyst", "admin"]:
            patterns["inventory"] = schema_data['query_examples']['inventory_queries']
            patterns["purchase_orders"] = schema_data['query_examples']['purchase_order_queries']
            patterns["transparency"] = schema_data['query_examples']['transparency_queries']
        elif user_role == "viewer":
            # Limited read-only patterns
            patterns["transparency"] = schema_data['query_examples']['transparency_queries']
        
        return patterns
    
    def _get_data_constraints(self, user_role: str, schema_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get data constraints and validation rules for the user."""
        
        constraints = {
            "business_rules": schema_data['business_rules'],
            "excluded_fields": schema_data['safety_measures']['excluded_fields']
        }
        
        if user_role == "viewer":
            constraints["read_only"] = True
            constraints["data_masking_required"] = True
        
        return constraints

    def get_context_for_ai_prompt(self, enhanced_context: Dict[str, Any]) -> str:
        """Generate a formatted context string for AI prompts."""
        
        context_parts = []
        
        # User information
        context_parts.append(f"## User Profile:")
        context_parts.append(f"- Name: {enhanced_context.get('user_name', 'Unknown')}")
        context_parts.append(f"- Role: {enhanced_context.get('user_role', 'unknown')}")
        context_parts.append(f"- Company: {enhanced_context.get('company_name', 'Unknown')} ({enhanced_context.get('company_type', 'unknown')})")
        
        # Data access
        context_parts.append(f"\n## Data Access:")
        accessible_tables = enhanced_context.get('available_tables', {})
        for table_name, table_info in accessible_tables.items():
            context_parts.append(f"- {table_name}: {table_info.get('description', 'No description')}")
        
        # Security context
        security = enhanced_context.get('security_context', {})
        context_parts.append(f"\n## Security Constraints:")
        context_parts.append(f"- Access Level: {', '.join(security.get('access_level', []))}")
        context_parts.append(f"- Excluded Fields: {', '.join(security.get('excluded_fields', []))}")
        
        # Business rules
        business_rules = enhanced_context.get('business_rules', {})
        if business_rules:
            context_parts.append(f"\n## Business Rules:")
            for category, rules in business_rules.items():
                if isinstance(rules, dict):
                    context_parts.append(f"- {category}: {rules}")
        
        return "\n".join(context_parts)

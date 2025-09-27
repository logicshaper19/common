"""
Comprehensive AI Supply Chain Assistant
Integrates all supply chain functions for natural language interaction.
"""
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import logging
import re

from .certification_functions import CertificationManager
from .supply_chain_functions import SupplyChainManager
from .certification_cache import cached, performance_tracked, get_performance_report

logger = logging.getLogger(__name__)

class ComprehensiveSupplyChainAI:
    """
    Comprehensive AI assistant for complete supply chain management.
    Handles all aspects: certifications, processing, traceability, analytics, etc.
    """
    
    def __init__(self, db_connection):
        self.cert_manager = CertificationManager(db_connection)
        self.supply_manager = SupplyChainManager(db_connection)
        self.db = db_connection
        
        # Query intent patterns
        self.intent_patterns = {
            'certifications': [
                r'certif\w*', r'expir\w*', r'renew\w*', r'rspo', r'mspo', 
                r'organic', r'compliance', r'audit'
            ],
            'inventory': [
                r'inventory', r'stock', r'batch\w*', r'available', 
                r'find.*product', r'search.*product'
            ],
            'processing': [
                r'mill\w*', r'refin\w*', r'transform\w*', r'process\w*', 
                r'yield', r'efficiency', r'oer'
            ],
            'traceability': [
                r'trace\w*', r'track\w*', r'origin', r'supply chain', 
                r'transparency', r'source'
            ],
            'orders': [
                r'purchase order', r'po\b', r'order\w*', r'buy\w*', 
                r'sell\w*', r'transaction'
            ],
            'locations': [
                r'farm\w*', r'location', r'plantation', r'gps', 
                r'coordinate', r'eudr'
            ],
            'analytics': [
                r'analytic\w*', r'report\w*', r'dashboard', r'summary', 
                r'overview', r'kpi', r'metric'
            ],
            'users': [
                r'user\w*', r'account', r'permission', r'access', r'role'
            ],
            'documents': [
                r'document\w*', r'file\w*', r'upload', r'report', r'map'
            ]
        }
        
        # Function mappings
        self.function_map = {
            'certifications': self._handle_certification_query,
            'inventory': self._handle_inventory_query,
            'processing': self._handle_processing_query,
            'traceability': self._handle_traceability_query,
            'orders': self._handle_orders_query,
            'locations': self._handle_locations_query,
            'analytics': self._handle_analytics_query,
            'users': self._handle_users_query,
            'documents': self._handle_documents_query
        }
    
    @performance_tracked
    def process_query(
        self, 
        query: str, 
        context: Optional[Dict[str, Any]] = None,
        user_role: str = 'viewer'
    ) -> Dict[str, Any]:
        """
        Main entry point for processing natural language queries.
        
        Args:
            query: Natural language query
            context: User context (company_id, preferences, etc.)
            user_role: User's role for permission checking
            
        Returns:
            Structured response with data and metadata
        """
        try:
            context = context or {}
            query_lower = query.lower()
            
            # Detect query intent
            intent = self._detect_intent(query_lower)
            
            # Extract parameters from query
            params = self._extract_parameters(query_lower, context)
            
            # Check permissions
            if not self._check_permissions(intent, user_role):
                return {
                    'status': 'permission_denied',
                    'message': f"Insufficient permissions for {intent} queries",
                    'required_role': self._get_required_role(intent)
                }
            
            # Route to appropriate handler
            if intent in self.function_map:
                response = self.function_map[intent](query_lower, params, context)
                response['intent'] = intent
                response['query'] = query
                return response
            else:
                return self._handle_unknown_query(query, context)
                
        except Exception as e:
            logger.error(f"Error processing query '{query}': {str(e)}")
            return {
                'status': 'error',
                'message': f"I encountered an error processing your request: {str(e)}",
                'query': query
            }
    
    @cached(ttl=300)
    def get_comprehensive_dashboard(
        self, 
        company_id: str,
        user_role: str = 'manager'
    ) -> Dict[str, Any]:
        """
        Generate comprehensive dashboard with all relevant supply chain data.
        """
        try:
            dashboard_data = {}
            
            # Certification overview
            cert_alerts = self.cert_manager.get_certifications(
                company_id=company_id,
                expires_within_days=30
            )
            dashboard_data['certifications'] = {
                'alerts': cert_alerts[1].get('needs_attention', 0),
                'total': cert_alerts[1].get('total_certificates', 0),
                'urgent': [c for c in cert_alerts[0] if c.days_until_expiry <= 7]
            }
            
            # Inventory overview
            inventory = self.cert_manager.search_batches(
                company_id=company_id,
                status='available',
                limit=10
            )
            dashboard_data['inventory'] = {
                'total_batches': inventory[1].get('total_batches', 0),
                'total_quantity': inventory[1].get('total_quantity', 0),
                'avg_transparency': inventory[1].get('average_transparency_score', 0)
            }
            
            # Processing overview
            processing = self.supply_manager.get_transformations(
                company_id=company_id,
                date_from=datetime.now() - timedelta(days=30),
                limit=10
            )
            dashboard_data['processing'] = {
                'monthly_operations': processing[1].get('total_transformations', 0),
                'avg_efficiency': processing[1].get('overall_efficiency', 0),
                'top_performer': processing[1].get('top_performers', [{}])[0] if processing[1].get('top_performers') else {}
            }
            
            # Purchase orders overview
            orders = self.cert_manager.get_purchase_orders(
                company_id=company_id,
                limit=10
            )
            dashboard_data['orders'] = {
                'active_orders': len([o for o in orders[0] if o.status in ['pending', 'confirmed']]),
                'total_volume': orders[1].get('total_volume', 0),
                'estimated_value': orders[1].get('estimated_total_value', 0)
            }
            
            # Farm locations overview
            farms = self.cert_manager.get_farm_locations(company_id=company_id)
            dashboard_data['farms'] = {
                'total_farms': farms[1].get('total_farms', 0),
                'eudr_compliant': farms[1].get('eudr_compliant_count', 0),
                'compliance_rate': round((farms[1].get('eudr_compliant_count', 0) / max(farms[1].get('total_farms', 1), 1)) * 100, 1)
            }
            
            # Supply chain analytics
            analytics = self.supply_manager.get_supply_chain_analytics(
                company_id=company_id,
                include_trends=True
            )
            dashboard_data['analytics'] = {
                'health_score': analytics[1].get('overall_health_score', 0),
                'transparency_score': analytics[0].transparency_metrics.get('average_score', 0),
                'risk_indicators': len(analytics[0].risk_indicators),
                'recommendations': analytics[1].get('recommendations', [])[:3]  # Top 3
            }
            
            # Recent activity summary
            dashboard_data['recent_activity'] = self._get_recent_activity(company_id)
            
            return {
                'status': 'success',
                'dashboard': dashboard_data,
                'company_id': company_id,
                'generated_at': datetime.now().isoformat(),
                'summary': self._generate_dashboard_summary(dashboard_data)
            }
            
        except Exception as e:
            logger.error(f"Error generating comprehensive dashboard: {str(e)}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def get_intelligent_recommendations(
        self,
        company_id: str,
        focus_area: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate intelligent recommendations based on company's current state.
        """
        try:
            recommendations = []
            priorities = []
            
            # Get current state data
            cert_data = self.cert_manager.get_certifications(company_id=company_id, expires_within_days=90)
            inventory_data = self.cert_manager.search_batches(company_id=company_id, limit=50)
            farm_data = self.cert_manager.get_farm_locations(company_id=company_id)
            analytics = self.supply_manager.get_supply_chain_analytics(company_id=company_id)
            
            # Certification recommendations
            expiring_soon = len([c for c in cert_data[0] if 0 < c.days_until_expiry <= 30])
            if expiring_soon > 0:
                recommendations.append({
                    'category': 'certifications',
                    'priority': 'high',
                    'title': f'{expiring_soon} certificates expiring soon',
                    'description': 'Initiate renewal process to avoid compliance gaps',
                    'action': 'Review expiring certificates and contact renewal authorities',
                    'impact': 'Prevents compliance violations and maintains market access'
                })
                priorities.append('certification_renewal')
            
            # Inventory recommendations
            low_transparency = len([b for b in inventory_data[0] if b.transparency_score < 70])
            if low_transparency > 0:
                recommendations.append({
                    'category': 'transparency',
                    'priority': 'medium',
                    'title': f'{low_transparency} batches with low transparency',
                    'description': 'Improve traceability data to meet regulatory requirements',
                    'action': 'Enhance data collection from upstream suppliers',
                    'impact': 'Improves compliance and reduces regulatory risk'
                })
                priorities.append('transparency_improvement')
            
            # Farm compliance recommendations
            non_compliant_farms = len([f for f in farm_data[0] if not f.eudr_compliant])
            if non_compliant_farms > 0:
                recommendations.append({
                    'category': 'compliance',
                    'priority': 'high',
                    'title': f'{non_compliant_farms} farms not EUDR compliant',
                    'description': 'Update GPS coordinates and compliance documentation',
                    'action': 'Collect precise GPS data and verify deforestation-free status',
                    'impact': 'Ensures EUDR compliance and EU market access'
                })
                priorities.append('eudr_compliance')
            
            # Processing efficiency recommendations
            avg_transparency = analytics[0].transparency_metrics.get('average_score', 0)
            if avg_transparency < 80:
                recommendations.append({
                    'category': 'processing',
                    'priority': 'medium',
                    'title': 'Processing efficiency below target',
                    'description': 'Optimize operations to improve yield and transparency',
                    'action': 'Review processing parameters and supplier data quality',
                    'impact': 'Reduces costs and improves supply chain visibility'
                })
                priorities.append('processing_optimization')
            
            # Strategic recommendations
            if len(recommendations) == 0:
                recommendations.append({
                    'category': 'optimization',
                    'priority': 'low',
                    'title': 'Maintain current performance',
                    'description': 'All key metrics are within acceptable ranges',
                    'action': 'Continue monitoring and incremental improvements',
                    'impact': 'Sustains competitive advantage and compliance'
                })
            
            # Generate action plan
            action_plan = self._generate_action_plan(recommendations, priorities)
            
            return {
                'status': 'success',
                'recommendations': recommendations,
                'priorities': priorities,
                'action_plan': action_plan,
                'focus_area': focus_area,
                'company_id': company_id,
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {str(e)}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    # Intent detection and parameter extraction
    
    def _detect_intent(self, query: str) -> str:
        """Detect the primary intent of a query."""
        intent_scores = {}
        
        for intent, patterns in self.intent_patterns.items():
            score = 0
            for pattern in patterns:
                matches = len(re.findall(pattern, query))
                score += matches
            intent_scores[intent] = score
        
        # Return intent with highest score, default to 'analytics' if no clear match
        if max(intent_scores.values()) == 0:
            return 'analytics'
        
        return max(intent_scores, key=intent_scores.get)
    
    def _extract_parameters(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract parameters from natural language query."""
        params = {}
        
        # Extract product types
        product_types = ['ffb', 'cpo', 'rbdpo', 'palm kernel', 'olein', 'stearin']
        for product in product_types:
            if product in query:
                params['product_type'] = product.upper().replace(' ', '_')
                break
        
        # Extract certifications
        certifications = ['rspo', 'mspo', 'organic', 'rainforest alliance', 'fair trade']
        for cert in certifications:
            if cert in query:
                params['certification_type'] = cert.upper()
                break
        
        # Extract quantities
        quantity_matches = re.findall(r'(\d+(?:\.\d+)?)\s*(?:mt|metric ton|ton|kg)', query)
        if quantity_matches:
            params['min_quantity'] = float(quantity_matches[0])
        
        # Extract time periods
        if 'last week' in query:
            params['date_from'] = datetime.now() - timedelta(days=7)
        elif 'last month' in query:
            params['date_from'] = datetime.now() - timedelta(days=30)
        elif 'last year' in query:
            params['date_from'] = datetime.now() - timedelta(days=365)
        
        # Extract status filters
        if 'available' in query:
            params['status'] = 'available'
        elif 'pending' in query:
            params['status'] = 'pending'
        elif 'confirmed' in query:
            params['status'] = 'confirmed'
        
        # Add context parameters
        if 'company_id' in context:
            params['company_id'] = context['company_id']
        
        return params
    
    def _check_permissions(self, intent: str, user_role: str) -> bool:
        """Check if user has permission for the requested operation."""
        permissions = {
            'viewer': ['certifications', 'inventory', 'analytics', 'locations'],
            'operator': ['certifications', 'inventory', 'processing', 'analytics', 'locations', 'orders'],
            'manager': ['certifications', 'inventory', 'processing', 'analytics', 'locations', 'orders', 'users', 'documents'],
            'admin': ['certifications', 'inventory', 'processing', 'analytics', 'locations', 'orders', 'users', 'documents', 'traceability']
        }
        
        allowed_intents = permissions.get(user_role, ['analytics'])
        return intent in allowed_intents
    
    def _get_required_role(self, intent: str) -> str:
        """Get minimum role required for an intent."""
        role_requirements = {
            'users': 'manager',
            'documents': 'manager',
            'traceability': 'admin',
            'processing': 'operator'
        }
        return role_requirements.get(intent, 'viewer')
    
    # Query handlers
    
    def _handle_certification_query(self, query: str, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle certification-related queries."""
        try:
            certifications, metadata = self.cert_manager.get_certifications(
                company_id=params.get('company_id'),
                certification_type=params.get('certification_type'),
                expires_within_days=params.get('expires_within_days', 30)
            )
            
            urgent_certs = [c for c in certifications if c.days_until_expiry <= 7]
            
            return {
                'status': 'success',
                'data': {
                    'certifications': certifications[:10],  # Limit response size
                    'urgent_alerts': urgent_certs,
                    'summary': f"Found {len(certifications)} certificates, {len(urgent_certs)} need urgent attention"
                },
                'metadata': metadata
            }
            
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def _handle_inventory_query(self, query: str, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle inventory-related queries."""
        try:
            batches, metadata = self.cert_manager.search_batches(
                company_id=params.get('company_id'),
                product_type=params.get('product_type'),
                status=params.get('status', 'available'),
                min_quantity=params.get('min_quantity'),
                certification_required=params.get('certification_type'),
                limit=20
            )
            
            return {
                'status': 'success',
                'data': {
                    'batches': batches,
                    'summary': f"Found {len(batches)} batches totaling {metadata.get('total_quantity', 0)}MT"
                },
                'metadata': metadata
            }
            
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def _handle_processing_query(self, query: str, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle processing-related queries."""
        try:
            transformations, metadata = self.supply_manager.get_transformations(
                company_id=params.get('company_id'),
                date_from=params.get('date_from'),
                input_product=params.get('product_type'),
                limit=15
            )
            
            return {
                'status': 'success',
                'data': {
                    'transformations': transformations,
                    'summary': f"Found {len(transformations)} processing operations with {metadata.get('overall_efficiency', 0)}% efficiency"
                },
                'metadata': metadata
            }
            
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def _handle_traceability_query(self, query: str, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle traceability-related queries."""
        try:
            # Extract batch ID from query if present
            batch_id_match = re.search(r'batch[_\s]*([a-zA-Z0-9]+)', query)
            if not batch_id_match and 'batch_id' not in params:
                return {
                    'status': 'error',
                    'message': 'Please provide a batch ID to trace'
                }
            
            batch_id = batch_id_match.group(1) if batch_id_match else params.get('batch_id')
            
            traceability, metadata = self.supply_manager.trace_supply_chain(
                batch_id=batch_id,
                include_full_history=True,
                include_compliance_check=True
            )
            
            if not traceability:
                return {
                    'status': 'not_found',
                    'message': f'Batch {batch_id} not found or not traceable'
                }
            
            return {
                'status': 'success',
                'data': {
                    'traceability': traceability,
                    'summary': f"Traced batch {batch_id} through {traceability.supply_chain_depth} transformation steps"
                },
                'metadata': metadata
            }
            
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def _handle_orders_query(self, query: str, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle purchase order queries."""
        try:
            # Determine role filter from query
            role_filter = None
            if 'buy' in query or 'purchas' in query:
                role_filter = 'buyer'
            elif 'sell' in query:
                role_filter = 'seller'
            
            orders, metadata = self.cert_manager.get_purchase_orders(
                company_id=params.get('company_id'),
                role_filter=role_filter,
                status=params.get('status'),
                date_from=params.get('date_from'),
                limit=15
            )
            
            return {
                'status': 'success',
                'data': {
                    'orders': orders,
                    'summary': f"Found {len(orders)} purchase orders worth ${metadata.get('estimated_total_value', 0):,.0f}"
                },
                'metadata': metadata
            }
            
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def _handle_locations_query(self, query: str, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle farm location queries."""
        try:
            farms, metadata = self.cert_manager.get_farm_locations(
                company_id=params.get('company_id'),
                certification_type=params.get('certification_type'),
                eudr_compliant_only='eudr' in query
            )
            
            return {
                'status': 'success',
                'data': {
                    'farms': farms,
                    'summary': f"Found {len(farms)} farm locations, {metadata.get('eudr_compliant_count', 0)} EUDR compliant"
                },
                'metadata': metadata
            }
            
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def _handle_analytics_query(self, query: str, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle analytics and reporting queries."""
        try:
            analytics, metadata = self.supply_manager.get_supply_chain_analytics(
                company_id=params.get('company_id'),
                date_from=params.get('date_from'),
                include_trends=True
            )
            
            return {
                'status': 'success',
                'data': {
                    'analytics': analytics,
                    'summary': f"Supply chain health score: {metadata.get('overall_health_score', 0)}/100"
                },
                'metadata': metadata
            }
            
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def _handle_users_query(self, query: str, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle user management queries."""
        try:
            users, metadata = self.supply_manager.get_users(
                company_id=params.get('company_id'),
                include_permissions=True
            )
            
            return {
                'status': 'success',
                'data': {
                    'users': users,
                    'summary': f"Found {len(users)} users across {metadata.get('companies_represented', 0)} companies"
                },
                'metadata': metadata
            }
            
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def _handle_documents_query(self, query: str, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle document management queries."""
        try:
            documents, metadata = self.supply_manager.get_documents(
                company_id=params.get('company_id'),
                expires_within_days=30 if 'expir' in query else None
            )
            
            return {
                'status': 'success',
                'data': {
                    'documents': documents,
                    'summary': f"Found {len(documents)} documents, {metadata.get('expiring_documents', 0)} expiring soon"
                },
                'metadata': metadata
            }
            
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def _handle_unknown_query(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle queries that don't match any known intent."""
        return {
            'status': 'unknown_intent',
            'message': 'I can help with certifications, inventory, processing, traceability, orders, farms, analytics, users, or documents.',
            'suggestions': [
                'Show me urgent certification alerts',
                'Find available RSPO certified CPO',
                'Trace batch ABC123',
                'Show supply chain analytics',
                'List farm locations',
                'Show recent purchase orders'
            ],
            'query': query
        }
    
    # Helper methods
    
    def _get_recent_activity(self, company_id: str) -> List[Dict[str, Any]]:
        """Get recent activity for dashboard."""
        activities = []
        
        try:
            # Recent orders
            recent_orders, _ = self.cert_manager.get_purchase_orders(
                company_id=company_id,
                limit=3
            )
            for order in recent_orders:
                activities.append({
                    'type': 'purchase_order',
                    'description': f"Order {order.po_number} from {order.seller_company_name}",
                    'timestamp': order.created_at,
                    'status': order.status
                })
            
            # Recent processing
            recent_processing, _ = self.supply_manager.get_transformations(
                company_id=company_id,
                limit=2
            )
            for transform in recent_processing:
                activities.append({
                    'type': 'processing',
                    'description': f"{transform.transformation_type} operation: {transform.input_product} → {transform.output_product}",
                    'timestamp': transform.created_at,
                    'efficiency': f"{transform.efficiency_score:.1f}%"
                })
            
            # Sort by timestamp
            activities.sort(key=lambda x: x['timestamp'], reverse=True)
            return activities[:5]
            
        except Exception as e:
            logger.error(f"Error getting recent activity: {str(e)}")
            return []
    
    def _generate_dashboard_summary(self, dashboard_data: Dict[str, Any]) -> str:
        """Generate natural language summary of dashboard."""
        try:
            cert_alerts = dashboard_data['certifications']['alerts']
            total_inventory = dashboard_data['inventory']['total_quantity']
            health_score = dashboard_data['analytics']['health_score']
            
            summary_parts = []
            
            if cert_alerts > 0:
                summary_parts.append(f"{cert_alerts} certificates need attention")
            else:
                summary_parts.append("All certificates are current")
            
            summary_parts.append(f"{total_inventory:.0f}MT of inventory available")
            summary_parts.append(f"Supply chain health score: {health_score:.0f}/100")
            
            if dashboard_data['analytics']['risk_indicators'] > 0:
                summary_parts.append(f"{dashboard_data['analytics']['risk_indicators']} risk indicators")
            
            return ". ".join(summary_parts) + "."
            
        except Exception:
            return "Dashboard data loaded successfully."
    
    def _generate_action_plan(self, recommendations: List[Dict[str, Any]], priorities: List[str]) -> Dict[str, Any]:
        """Generate actionable plan from recommendations."""
        immediate_actions = [r for r in recommendations if r['priority'] == 'high']
        short_term_actions = [r for r in recommendations if r['priority'] == 'medium']
        long_term_actions = [r for r in recommendations if r['priority'] == 'low']
        
        return {
            'immediate': {
                'timeframe': '1-7 days',
                'actions': immediate_actions
            },
            'short_term': {
                'timeframe': '1-4 weeks', 
                'actions': short_term_actions
            },
            'long_term': {
                'timeframe': '1-3 months',
                'actions': long_term_actions
            },
            'priority_order': priorities
        }

# Convenience functions for external integration

def create_ai_assistant(db_connection) -> ComprehensiveSupplyChainAI:
    """Create comprehensive AI assistant instance."""
    return ComprehensiveSupplyChainAI(db_connection)

def get_system_status() -> Dict[str, Any]:
    """Get overall system performance status."""
    return {
        'performance': get_performance_report(),
        'timestamp': datetime.now().isoformat(),
        'status': 'operational'
    }

# Example usage patterns
COMPREHENSIVE_EXAMPLES = {
    "certification_management": {
        "queries": [
            "Show me all certificates expiring in the next 30 days",
            "Which RSPO certificates need renewal?",
            "What's our overall compliance status?"
        ],
        "response_type": "certification_data_with_alerts"
    },
    "inventory_management": {
        "queries": [
            "Find available RSPO certified CPO over 50MT",
            "What's our current inventory status?",
            "Show me low transparency batches"
        ],
        "response_type": "inventory_data_with_recommendations"
    },
    "supply_chain_traceability": {
        "queries": [
            "Trace batch ABC123 back to origin",
            "Show me the supply chain for this product",
            "Is this batch EUDR compliant?"
        ],
        "response_type": "traceability_analysis"
    },
    "analytics_and_reporting": {
        "queries": [
            "Show me supply chain analytics",
            "What's our transparency score trend?",
            "Generate a compliance report"
        ],
        "response_type": "analytics_dashboard"
    },
    "comprehensive_dashboard": {
        "queries": [
            "Show me the complete dashboard",
            "Give me an overview of everything",
            "What's the status of our operations?"
        ],
        "response_type": "full_dashboard_with_recommendations"
    }
}

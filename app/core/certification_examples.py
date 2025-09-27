"""
Example usage patterns for certification management functions.
Demonstrates atomic, composable, fast, and error-handled implementations.
"""
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging

from .certification_functions import CertificationManager, init_certification_manager
from .certification_cache import cached, performance_tracked, get_performance_report

logger = logging.getLogger(__name__)

class CertificationAIAssistant:
    """AI assistant for certification management with example use cases."""
    
    def __init__(self, db_connection):
        self.manager = CertificationManager(db_connection)
        self.db = db_connection
    
    @cached(ttl=180)  # 3-minute cache for certification alerts
    @performance_tracked
    def get_urgent_certification_alerts(self, company_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Example: Get urgent certification alerts for immediate action.
        Demonstrates: Atomic function, error handling, fast response.
        """
        try:
            # Get certificates expiring in next 30 days
            certifications, metadata = self.manager.get_certifications(
                company_id=company_id,
                expires_within_days=30
            )
            
            # Categorize by urgency
            urgent = [c for c in certifications if c.days_until_expiry <= 7]
            warning = [c for c in certifications if 7 < c.days_until_expiry <= 30]
            expired = [c for c in certifications if c.days_until_expiry <= 0]
            
            return {
                'status': 'success',
                'urgent_action_required': len(urgent),
                'warning_level': len(warning),
                'expired_certificates': len(expired),
                'urgent_details': [
                    {
                        'company': c.company_name,
                        'certification': c.certification_type,
                        'days_remaining': c.days_until_expiry,
                        'renewal_contact': c.renewal_contact,
                        'estimated_cost': c.renewal_cost_estimate
                    }
                    for c in urgent
                ],
                'summary': f"{len(urgent)} urgent, {len(warning)} warning, {len(expired)} expired"
            }
            
        except Exception as e:
            logger.error(f"Error getting certification alerts: {str(e)}")
            return {
                'status': 'error',
                'message': str(e),
                'urgent_action_required': 0
            }
    
    @cached(ttl=300)  # 5-minute cache for inventory searches
    @performance_tracked
    def find_certified_inventory(
        self, 
        product_type: str, 
        certification_required: str,
        min_quantity: float = 1.0
    ) -> Dict[str, Any]:
        """
        Example: Find certified inventory for procurement.
        Demonstrates: Composable functions, business logic integration.
        """
        try:
            # Search for available batches with required certification
            batches, batch_metadata = self.manager.search_batches(
                product_type=product_type,
                status='available',
                min_quantity=min_quantity,
                certification_required=certification_required
            )
            
            if not batches:
                return {
                    'status': 'not_found',
                    'message': f"No {certification_required} certified {product_type} found with minimum {min_quantity}MT",
                    'available_inventory': 0,
                    'suggestions': self._get_alternative_suggestions(product_type, certification_required)
                }
            
            # Get supplier information for each batch
            suppliers = {}
            for batch in batches:
                if batch.company_id not in suppliers:
                    company_info, _ = self.manager.get_company_info(
                        company_id=batch.company_id,
                        include_statistics=True
                    )
                    suppliers[batch.company_id] = company_info[0] if company_info else None
            
            # Rank batches by transparency score and supplier reliability
            ranked_batches = sorted(
                batches, 
                key=lambda b: (b.transparency_score, suppliers.get(b.company_id, {}).get('transparency_score', 0)),
                reverse=True
            )
            
            return {
                'status': 'success',
                'total_available': sum(b.quantity for b in batches),
                'batch_count': len(batches),
                'top_recommendations': [
                    {
                        'batch_id': b.batch_id,
                        'supplier': b.company_name,
                        'quantity_mt': b.quantity,
                        'transparency_score': b.transparency_score,
                        'farm_location': b.farm_location,
                        'certifications': b.certifications,
                        'expiry_date': b.expiry_date.isoformat() if b.expiry_date else None
                    }
                    for b in ranked_batches[:5]
                ],
                'metadata': batch_metadata
            }
            
        except Exception as e:
            logger.error(f"Error finding certified inventory: {str(e)}")
            return {
                'status': 'error',
                'message': str(e),
                'available_inventory': 0
            }
    
    @performance_tracked
    def analyze_supply_chain_compliance(self, company_id: str) -> Dict[str, Any]:
        """
        Example: Comprehensive supply chain compliance analysis.
        Demonstrates: Composable functions working together.
        """
        try:
            # Get company information
            company_info, company_meta = self.manager.get_company_info(
                company_id=company_id,
                include_statistics=True,
                include_contact_info=True
            )
            
            if not company_info:
                return {
                    'status': 'error',
                    'message': 'Company not found'
                }
            
            company = company_info[0]
            
            # Get certification status
            certifications, cert_meta = self.manager.get_certifications(
                company_id=company_id
            )
            
            # Get farm locations compliance
            farm_locations, farm_meta = self.manager.get_farm_locations(
                company_id=company_id
            )
            
            # Get recent purchase orders for supply chain visibility
            purchase_orders, po_meta = self.manager.get_purchase_orders(
                company_id=company_id,
                limit=20
            )
            
            # Calculate compliance scores
            certification_score = self._calculate_certification_score(certifications)
            farm_compliance_score = self._calculate_farm_compliance_score(farm_locations)
            traceability_score = self._calculate_traceability_score(purchase_orders)
            
            overall_compliance = (certification_score + farm_compliance_score + traceability_score) / 3
            
            # Generate recommendations
            recommendations = self._generate_compliance_recommendations(
                certifications, farm_locations, purchase_orders
            )
            
            return {
                'status': 'success',
                'company': {
                    'name': company.name,
                    'type': company.company_type,
                    'transparency_score': company.transparency_score
                },
                'compliance_analysis': {
                    'overall_score': round(overall_compliance, 2),
                    'certification_score': round(certification_score, 2),
                    'farm_compliance_score': round(farm_compliance_score, 2),
                    'traceability_score': round(traceability_score, 2)
                },
                'risk_factors': {
                    'expiring_certificates': cert_meta.get('expiring_soon', 0),
                    'non_compliant_farms': len([f for f in farm_locations if f.compliance_status != 'verified']),
                    'low_transparency_orders': len([po for po in purchase_orders if hasattr(po, 'transparency_score') and po.transparency_score < 70])
                },
                'recommendations': recommendations,
                'summary_metrics': {
                    'total_certifications': len(certifications),
                    'total_farms': len(farm_locations),
                    'eudr_compliant_farms': len([f for f in farm_locations if f.eudr_compliant]),
                    'recent_orders': len(purchase_orders)
                }
            }
            
        except Exception as e:
            logger.error(f"Error analyzing supply chain compliance: {str(e)}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    @cached(ttl=600)  # 10-minute cache for dashboard data
    @performance_tracked
    def get_certification_dashboard(self, company_id: str) -> Dict[str, Any]:
        """
        Example: Complete certification management dashboard.
        Demonstrates: Fast composite queries with caching.
        """
        try:
            # Get all relevant data in parallel (conceptually)
            urgent_alerts = self.get_urgent_certification_alerts(company_id)
            compliance_analysis = self.analyze_supply_chain_compliance(company_id)
            
            # Get recent activity
            recent_orders, _ = self.manager.get_purchase_orders(
                company_id=company_id,
                limit=5
            )
            
            # Get farm locations summary
            farm_locations, farm_meta = self.manager.get_farm_locations(
                company_id=company_id
            )
            
            return {
                'status': 'success',
                'dashboard': {
                    'alerts': urgent_alerts,
                    'compliance': compliance_analysis.get('compliance_analysis', {}),
                    'risk_factors': compliance_analysis.get('risk_factors', {}),
                    'recommendations': compliance_analysis.get('recommendations', []),
                    'recent_activity': [
                        {
                            'type': 'purchase_order',
                            'description': f"Order {po.po_number} from {po.seller_company_name}",
                            'date': po.created_at.isoformat(),
                            'status': po.status
                        }
                        for po in recent_orders
                    ],
                    'farm_overview': {
                        'total_farms': farm_meta.get('total_farms', 0),
                        'eudr_compliant': farm_meta.get('eudr_compliant_count', 0),
                        'certification_distribution': farm_meta.get('certification_distribution', {})
                    }
                },
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating dashboard: {str(e)}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def handle_natural_language_query(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Example: Handle natural language queries about certification management.
        Demonstrates: AI-friendly function composition.
        """
        query_lower = query.lower()
        context = context or {}
        company_id = context.get('company_id')
        
        try:
            # Certificate expiry queries
            if any(word in query_lower for word in ['expir', 'renew', 'urgent', 'alert']):
                return self.get_urgent_certification_alerts(company_id)
            
            # Inventory search queries
            elif any(word in query_lower for word in ['inventory', 'stock', 'available', 'find']):
                # Extract product type and certification from query
                product_type = self._extract_product_type(query_lower)
                certification = self._extract_certification_type(query_lower)
                
                if product_type:
                    return self.find_certified_inventory(
                        product_type=product_type,
                        certification_required=certification or 'RSPO'
                    )
                else:
                    # General inventory search
                    batches, metadata = self.manager.search_batches(
                        company_id=company_id,
                        status='available',
                        limit=10
                    )
                    return {
                        'status': 'success',
                        'message': f"Found {len(batches)} available inventory batches",
                        'batches': [
                            {
                                'batch_id': b.batch_id,
                                'product': b.product_name,
                                'quantity': b.quantity,
                                'supplier': b.company_name
                            }
                            for b in batches
                        ]
                    }
            
            # Compliance queries
            elif any(word in query_lower for word in ['complian', 'audit', 'eudr', 'risk']):
                return self.analyze_supply_chain_compliance(company_id)
            
            # Dashboard queries
            elif any(word in query_lower for word in ['dashboard', 'overview', 'summary']):
                return self.get_certification_dashboard(company_id)
            
            # Farm location queries
            elif any(word in query_lower for word in ['farm', 'location', 'gps', 'plantation']):
                farm_locations, metadata = self.manager.get_farm_locations(company_id=company_id)
                return {
                    'status': 'success',
                    'message': f"Found {len(farm_locations)} farm locations",
                    'farms': [
                        {
                            'name': f.name,
                            'location': f"{f.latitude:.4f}, {f.longitude:.4f}",
                            'certifications': f.certifications,
                            'compliance': f.compliance_status,
                            'eudr_compliant': f.eudr_compliant
                        }
                        for f in farm_locations
                    ],
                    'metadata': metadata
                }
            
            # Purchase order queries
            elif any(word in query_lower for word in ['order', 'purchase', 'po', 'transaction']):
                orders, metadata = self.manager.get_purchase_orders(
                    company_id=company_id,
                    limit=10
                )
                return {
                    'status': 'success',
                    'message': f"Found {len(orders)} recent purchase orders",
                    'orders': [
                        {
                            'po_number': o.po_number,
                            'buyer': o.buyer_company_name,
                            'seller': o.seller_company_name,
                            'product': o.product_name,
                            'quantity': o.quantity,
                            'status': o.status,
                            'date': o.created_at.isoformat()
                        }
                        for o in orders
                    ]
                }
            
            else:
                return {
                    'status': 'unknown_query',
                    'message': 'I can help with certifications, inventory, compliance, farms, or purchase orders. Please be more specific.',
                    'suggestions': [
                        'Show me urgent certification alerts',
                        'Find RSPO certified CPO inventory',
                        'Analyze supply chain compliance',
                        'Show certification dashboard',
                        'List farm locations'
                    ]
                }
                
        except Exception as e:
            logger.error(f"Error handling natural language query: {str(e)}")
            return {
                'status': 'error',
                'message': f"Sorry, I encountered an error: {str(e)}"
            }
    
    # Helper methods
    
    def _get_alternative_suggestions(self, product_type: str, certification: str) -> List[str]:
        """Generate alternative suggestions when inventory not found."""
        suggestions = []
        
        # Suggest alternative certifications
        cert_alternatives = {
            'RSPO': ['MSPO', 'Rainforest Alliance'],
            'MSPO': ['RSPO'],
            'Organic': ['RSPO', 'Fair Trade']
        }
        
        for alt_cert in cert_alternatives.get(certification, []):
            suggestions.append(f"Try searching for {alt_cert} certified {product_type}")
        
        # Suggest alternative products
        product_alternatives = {
            'CPO': ['RBDPO'],
            'RBDPO': ['CPO', 'Olein'],
            'FFB': ['CPO']
        }
        
        for alt_product in product_alternatives.get(product_type, []):
            suggestions.append(f"Consider {alt_product} as alternative")
        
        return suggestions
    
    def _calculate_certification_score(self, certifications: List) -> float:
        """Calculate certification compliance score."""
        if not certifications:
            return 0.0
        
        total_score = 0
        for cert in certifications:
            if cert.days_until_expiry <= 0:
                score = 0  # Expired
            elif cert.days_until_expiry <= 30:
                score = 50  # Expiring soon
            elif cert.days_until_expiry <= 90:
                score = 75  # Needs attention
            else:
                score = 100  # Good
            total_score += score
        
        return total_score / len(certifications)
    
    def _calculate_farm_compliance_score(self, farm_locations: List) -> float:
        """Calculate farm compliance score."""
        if not farm_locations:
            return 0.0
        
        compliant_farms = sum(1 for f in farm_locations if f.compliance_status == 'verified')
        return (compliant_farms / len(farm_locations)) * 100
    
    def _calculate_traceability_score(self, purchase_orders: List) -> float:
        """Calculate supply chain traceability score."""
        if not purchase_orders:
            return 100.0  # No orders to trace
        
        # Simplified scoring based on order status and recent activity
        active_orders = sum(1 for po in purchase_orders if po.status in ['confirmed', 'fulfilled'])
        return (active_orders / len(purchase_orders)) * 100
    
    def _generate_compliance_recommendations(self, certifications, farm_locations, purchase_orders) -> List[str]:
        """Generate actionable compliance recommendations."""
        recommendations = []
        
        # Certification recommendations
        expiring_soon = sum(1 for c in certifications if 0 < c.days_until_expiry <= 30)
        if expiring_soon > 0:
            recommendations.append(f"Urgent: {expiring_soon} certificates expiring within 30 days - initiate renewal process")
        
        expired = sum(1 for c in certifications if c.days_until_expiry <= 0)
        if expired > 0:
            recommendations.append(f"Critical: {expired} certificates have expired - immediate action required")
        
        # Farm compliance recommendations
        non_compliant_farms = sum(1 for f in farm_locations if f.compliance_status != 'verified')
        if non_compliant_farms > 0:
            recommendations.append(f"Address compliance issues at {non_compliant_farms} farm locations")
        
        non_eudr_farms = sum(1 for f in farm_locations if not f.eudr_compliant)
        if non_eudr_farms > 0:
            recommendations.append(f"EUDR compliance needed for {non_eudr_farms} farms - verify GPS coordinates")
        
        # Supply chain recommendations
        pending_orders = sum(1 for po in purchase_orders if po.status == 'pending')
        if pending_orders > 3:
            recommendations.append(f"Review {pending_orders} pending purchase orders for processing delays")
        
        if not recommendations:
            recommendations.append("All compliance indicators are within acceptable ranges")
        
        return recommendations
    
    def _extract_product_type(self, query: str) -> Optional[str]:
        """Extract product type from natural language query."""
        product_types = ['FFB', 'CPO', 'RBDPO', 'Palm Kernel', 'Olein', 'Stearin']
        query_upper = query.upper()
        
        for product in product_types:
            if product in query_upper:
                return product
        
        # Check for common aliases
        aliases = {
            'CRUDE PALM OIL': 'CPO',
            'REFINED': 'RBDPO',
            'FRESH FRUIT BUNCHES': 'FFB'
        }
        
        for alias, product in aliases.items():
            if alias in query_upper:
                return product
        
        return None
    
    def _extract_certification_type(self, query: str) -> Optional[str]:
        """Extract certification type from natural language query."""
        certifications = ['RSPO', 'MSPO', 'Organic', 'Rainforest Alliance', 'Fair Trade']
        query_upper = query.upper()
        
        for cert in certifications:
            if cert.upper() in query_upper:
                return cert
        
        return None

# Convenience functions for AI integration

def create_ai_assistant(db_connection) -> CertificationAIAssistant:
    """Create AI assistant instance with optimized settings."""
    return CertificationAIAssistant(db_connection)

def get_system_performance_report() -> Dict[str, Any]:
    """Get comprehensive system performance report."""
    return get_performance_report()

# Example usage patterns for documentation
EXAMPLE_QUERIES = {
    "certification_alerts": {
        "query": "Show me urgent certification alerts",
        "function": "get_urgent_certification_alerts",
        "description": "Get certificates expiring soon with renewal information"
    },
    "inventory_search": {
        "query": "Find RSPO certified CPO inventory",
        "function": "find_certified_inventory",
        "description": "Search for certified inventory with supplier rankings"
    },
    "compliance_analysis": {
        "query": "Analyze our supply chain compliance",
        "function": "analyze_supply_chain_compliance",
        "description": "Comprehensive compliance scoring and recommendations"
    },
    "dashboard": {
        "query": "Show certification dashboard",
        "function": "get_certification_dashboard",
        "description": "Complete overview with alerts, compliance, and activity"
    },
    "natural_language": {
        "query": "What's the status of our palm oil farms?",
        "function": "handle_natural_language_query",
        "description": "Process natural language queries about any certification topic"
    }
}

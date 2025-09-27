"""
Schema context for AI assistant - provides safe, curated database schema context.
"""
from typing import Dict, Any
import os

class SupplyChainSchemaContext:
    """Provide safe, curated database schema context to AI assistant."""
    
    @staticmethod
    def get_schema_context() -> Dict[str, Any]:
        """Return schema information that's safe to expose to AI."""
        
        return {
            "tables": {
                "companies": {
                    "description": "Palm oil supply chain companies",
                    "key_fields": [
                        "id", "name", "company_type", "created_at", 
                        "transparency_score", "location", "certifications"
                    ],
                    "company_types": [
                        "plantation_grower", "mill_processor", "refinery_crusher",
                        "trader_aggregator", "brand", "manufacturer"
                    ],
                    "sample_companies": [
                        "Sime Darby Plantation", "Golden Agri-Resources", 
                        "L'Oréal", "IOI Corporation"
                    ]
                },
                
                "purchase_orders": {
                    "description": "Purchase orders between companies",
                    "key_fields": [
                        "id", "buyer_company_id", "seller_company_id",
                        "product_id", "quantity", "status", "created_at"
                    ],
                    "statuses": ["pending", "confirmed", "fulfilled", "cancelled"],
                    "typical_flow": "plantation → mill → refinery → brand"
                },
                
                "batches": {
                    "description": "Inventory batches with traceability",
                    "key_fields": [
                        "batch_id", "company_id", "product_id", "quantity",
                        "status", "transparency_score", "created_at", "expiry_date"
                    ],
                    "statuses": ["available", "reserved", "allocated", "processed"],
                    "transparency_calculation": f"Uses degradation factor: {os.getenv('TRANSPARENCY_DEGRADATION_FACTOR', '0.95')}"
                },
                
                "products": {
                    "description": "Palm oil products in the supply chain",
                    "key_fields": ["id", "name", "product_type", "specifications"],
                    "product_types": ["FFB", "CPO", "RBDPO", "Palm Kernel", "Olein", "Stearin"],
                    "processing_flow": "FFB → CPO → RBDPO → Final Products"
                },
                
                "transformations": {
                    "description": "Processing operations (milling, refining)",
                    "key_fields": [
                        "id", "input_batch_id", "output_batch_id", 
                        "transformation_type", "yield_percentage", "created_at"
                    ],
                    "transformation_types": ["milling", "refining", "fractionation"],
                    "typical_yields": {
                        "FFB_to_CPO": "18-22% (Oil Extraction Rate)",
                        "FFB_to_PK": "4-6% (Palm Kernel)",
                        "CPO_to_RBDPO": "95-98%"
                    }
                },
                
                "users": {
                    "description": "Platform users with company affiliations",
                    "key_fields": [
                        "id", "email", "first_name", "company_id", 
                        "role", "created_at"
                    ],
                    "roles": ["admin", "manager", "operator", "viewer"],
                    "feature_access": "Based on V2_DASHBOARD_* flags from .env"
                }
            },
            
            "relationships": {
                "supply_chain_flow": "companies → purchase_orders → batches → transformations",
                "traceability": "Each batch tracks back to originating plantation via transformations",
                "transparency_scoring": "Calculated using GPS data, certificates, and supply chain depth",
                "compliance_tracking": "EUDR compliance linked to GPS coordinates and forest risk assessment"
            },
            
            "business_rules": {
                "transparency_calculation": {
                    "degradation_factor": os.getenv("TRANSPARENCY_DEGRADATION_FACTOR", "0.95"),
                    "timeout_seconds": os.getenv("TRANSPARENCY_CALCULATION_TIMEOUT", "30"),
                    "minimum_score": "70% (regulatory requirement)",
                    "target_score": "95% (best practice)"
                },
                
                "processing_constraints": {
                    "oer_target": "20-22% for efficient mills",
                    "energy_consumption": "35-45 kWh/MT typical",
                    "quality_parameters": "FFA <3%, Moisture <0.1%"
                },
                
                "compliance_requirements": {
                    "eudr_gps_required": "All plantation sources must have GPS coordinates",
                    "certificate_validity": "RSPO, Rainforest Alliance certificates must be current",
                    "traceability_depth": "Full chain visibility required for brands"
                }
            },
            
            "feature_flags": {
                "v2_dashboards": {
                    "brand": os.getenv("V2_DASHBOARD_BRAND", "false") == "true",
                    "processor": os.getenv("V2_DASHBOARD_PROCESSOR", "false") == "true",
                    "originator": os.getenv("V2_DASHBOARD_ORIGINATOR", "false") == "true",
                    "trader": os.getenv("V2_DASHBOARD_TRADER", "false") == "true"
                },
                "notifications": os.getenv("V2_NOTIFICATION_CENTER", "false") == "true"
            },
            
            "safety_measures": {
                "excluded_fields": [
                    "users.hashed_password", "api_keys.secret_key", 
                    "companies.internal_notes", "financial_details.bank_account"
                ],
                "data_masking": {
                    "email": "Show only domain for privacy",
                    "phone": "Show only country code", 
                    "coordinates": "Round to 2 decimal places for privacy"
                },
                "access_levels": {
                    "plantation_grower": ["own_company_data", "upstream_transparency"],
                    "brand": ["supply_chain_visibility", "compliance_reports"],
                    "mill_processor": ["processing_data", "upstream_sourcing"]
                }
            },
            
            "query_examples": {
                "inventory_queries": [
                    "SELECT batch_id, quantity, transparency_score FROM batches WHERE company_id = ? AND status = 'available'",
                    "SELECT product_name, SUM(quantity) as total_stock FROM batches b JOIN products p ON b.product_id = p.id WHERE b.company_id = ? GROUP BY product_name"
                ],
                "purchase_order_queries": [
                    "SELECT po_number, buyer_name, seller_name, status FROM purchase_orders po JOIN companies bc ON po.buyer_company_id = bc.id JOIN companies sc ON po.seller_company_id = sc.id WHERE po.status = 'pending'",
                    "SELECT COUNT(*) as pending_orders FROM purchase_orders WHERE buyer_company_id = ? AND status = 'pending'"
                ],
                "transparency_queries": [
                    "SELECT AVG(transparency_score) as avg_transparency FROM batches WHERE company_id = ? AND created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)",
                    "SELECT company_name, transparency_score FROM companies WHERE company_type = 'plantation_grower' ORDER BY transparency_score DESC LIMIT 10"
                ]
            }
        }

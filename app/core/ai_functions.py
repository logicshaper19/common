"""
AI Function Calling System - Allows AI to call specific database functions dynamically.
"""
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
import json

from app.models.location import Location
from app.models.document import Document
from app.models.batch import Batch
from app.models.purchase_order import PurchaseOrder
from app.models.product import Product
from app.models.company import Company


class AIFunctionRegistry:
    """Registry of functions that the AI can call to query data."""
    
    def __init__(self, db: Session, user_company_id: str):
        self.db = db
        self.user_company_id = user_company_id
        self._register_functions()
    
    def _register_functions(self):
        """Register all available functions for the AI."""
        self.functions = {
            "get_certifications": {
                "function": self._get_certifications,
                "description": "Get certification data for the company including expiry dates and farm certifications",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "expiry_warning_days": {
                            "type": "integer",
                            "description": "Number of days to look ahead for expiring certificates (default: 30)",
                            "default": 30
                        },
                        "include_farm_certs": {
                            "type": "boolean", 
                            "description": "Whether to include farm-level certifications (default: true)",
                            "default": True
                        }
                    }
                }
            },
            
            "search_batches": {
                "function": self._search_batches,
                "description": "Search for batches with various filters",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "product_name": {
                            "type": "string",
                            "description": "Filter by product name (e.g., 'Fresh Fruit Bunches')"
                        },
                        "status": {
                            "type": "string",
                            "description": "Filter by batch status (e.g., 'active', 'transferred')"
                        },
                        "date_from": {
                            "type": "string",
                            "description": "Filter batches from this date (YYYY-MM-DD format)"
                        },
                        "date_to": {
                            "type": "string", 
                            "description": "Filter batches to this date (YYYY-MM-DD format)"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of batches to return (default: 10)",
                            "default": 10
                        }
                    }
                }
            },
            
            "get_purchase_orders": {
                "function": self._get_purchase_orders,
                "description": "Get recent purchase orders for the company",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "status": {
                            "type": "string",
                            "description": "Filter by PO status (e.g., 'pending', 'confirmed', 'fulfilled')"
                        },
                        "role": {
                            "type": "string",
                            "description": "Company role filter ('buyer' or 'seller')"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of POs to return (default: 5)",
                            "default": 5
                        }
                    }
                }
            },
            
            "get_farm_locations": {
                "function": self._get_farm_locations,
                "description": "Get farm locations owned by the company with their certifications",
                "parameters": {
                    "type": "object", 
                    "properties": {
                        "include_coordinates": {
                            "type": "boolean",
                            "description": "Whether to include GPS coordinates (default: true)",
                            "default": True
                        },
                        "certification_filter": {
                            "type": "string",
                            "description": "Filter farms by specific certification (e.g., 'RSPO', 'MSPO')"
                        }
                    }
                }
            },
            
            "get_company_info": {
                "function": self._get_company_info,
                "description": "Get detailed information about the company",
                "parameters": {
                    "type": "object",
                    "properties": {}
                }
            }
        }
    
    def get_function_definitions(self) -> List[Dict[str, Any]]:
        """Get OpenAI-compatible function definitions."""
        definitions = []
        for name, func_info in self.functions.items():
            definitions.append({
                "name": name,
                "description": func_info["description"],
                "parameters": func_info["parameters"]
            })
        return definitions
    
    def call_function(self, function_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a specific function with the provided arguments."""
        if function_name not in self.functions:
            return {"error": f"Function {function_name} not found"}
        
        try:
            function = self.functions[function_name]["function"]
            result = function(**arguments)
            return {"success": True, "data": result}
        except Exception as e:
            return {"error": f"Error calling {function_name}: {str(e)}"}
    
    def _get_certifications(self, expiry_warning_days: int = 30, include_farm_certs: bool = True) -> Dict[str, Any]:
        """Get certification data for the company."""
        
        # Get company certificate documents
        documents = self.db.query(Document).filter(
            Document.company_id == self.user_company_id,
            Document.document_category == 'certificate',
            Document.is_deleted == False
        ).all()
        
        # Get farm certifications if requested
        farm_certs = []
        if include_farm_certs:
            farms = self.db.query(Location).filter(
                Location.company_id == self.user_company_id,
                Location.is_farm_location == True,
                Location.certifications.isnot(None)
            ).all()
            
            for farm in farms:
                if farm.certifications:
                    farm_certs.append({
                        "farm_name": farm.name,
                        "farm_id": farm.registration_number,
                        "certifications": farm.certifications,
                        "compliance_status": farm.compliance_status,
                        "location": {
                            "latitude": float(farm.latitude) if farm.latitude else None,
                            "longitude": float(farm.longitude) if farm.longitude else None
                        }
                    })
        
        # Process company certificates and check expiry
        company_certificates = []
        expiring_soon = []
        now = datetime.now().date()
        warning_date = now + timedelta(days=expiry_warning_days)
        
        for doc in documents:
            cert_info = {
                "document_id": str(doc.id),
                "filename": doc.filename,
                "issuing_authority": doc.issuing_authority,
                "issue_date": doc.issue_date.date().isoformat() if doc.issue_date else None,
                "expiry_date": doc.expiry_date.date().isoformat() if doc.expiry_date else None,
                "compliance_regulations": doc.compliance_regulations
            }
            
            company_certificates.append(cert_info)
            
            # Check if expiring soon
            if doc.expiry_date and doc.expiry_date.date() <= warning_date:
                days_until_expiry = (doc.expiry_date.date() - now).days
                expiring_soon.append({
                    **cert_info,
                    "days_until_expiry": days_until_expiry,
                    "is_expired": days_until_expiry < 0,
                    "urgency": "high" if days_until_expiry <= 7 else "medium"
                })
        
        return {
            "company_certificates": company_certificates,
            "farm_certifications": farm_certs,
            "expiring_soon": expiring_soon,
            "summary": {
                "total_certificates": len(company_certificates),
                "total_farms_with_certs": len(farm_certs),
                "certificates_expiring_soon": len(expiring_soon),
                "expired_certificates": len([c for c in expiring_soon if c["is_expired"]])
            }
        }
    
    def _search_batches(self, product_name: str = None, status: str = None, 
                       date_from: str = None, date_to: str = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for batches with filters."""
        
        query = self.db.query(Batch).filter(Batch.company_id == self.user_company_id)
        
        # Apply filters
        if status:
            query = query.filter(Batch.status == status)
        
        if date_from:
            try:
                from_date = datetime.strptime(date_from, '%Y-%m-%d').date()
                query = query.filter(Batch.production_date >= from_date)
            except ValueError:
                pass  # Invalid date format, skip filter
        
        if date_to:
            try:
                to_date = datetime.strptime(date_to, '%Y-%m-%d').date()
                query = query.filter(Batch.production_date <= to_date)
            except ValueError:
                pass  # Invalid date format, skip filter
        
        # Product name filter (requires join)
        if product_name:
            query = query.join(Product).filter(Product.name.ilike(f"%{product_name}%"))
        
        # Order by most recent first and limit
        batches = query.order_by(Batch.created_at.desc()).limit(limit).all()
        
        # Format results
        results = []
        for batch in batches:
            product = self.db.query(Product).filter(Product.id == batch.product_id).first()
            results.append({
                "batch_id": batch.batch_id,
                "product_name": product.name if product else "Unknown Product",
                "quantity": float(batch.quantity),
                "unit": batch.unit,
                "status": batch.status,
                "production_date": batch.production_date.isoformat(),
                "location_name": batch.location_name,
                "certifications": batch.certifications,
                "created_at": batch.created_at.isoformat() if batch.created_at else None
            })
        
        return results
    
    def _get_purchase_orders(self, status: str = None, role: str = None, limit: int = 5) -> List[Dict[str, Any]]:
        """Get recent purchase orders for the company."""
        
        query = self.db.query(PurchaseOrder)
        
        # Filter by company role
        if role == "buyer":
            query = query.filter(PurchaseOrder.buyer_company_id == self.user_company_id)
        elif role == "seller":
            query = query.filter(PurchaseOrder.seller_company_id == self.user_company_id)
        else:
            # Both buyer and seller
            query = query.filter(
                or_(
                    PurchaseOrder.buyer_company_id == self.user_company_id,
                    PurchaseOrder.seller_company_id == self.user_company_id
                )
            )
        
        # Filter by status
        if status:
            query = query.filter(PurchaseOrder.status == status)
        
        # Order by most recent first
        pos = query.order_by(PurchaseOrder.created_at.desc()).limit(limit).all()
        
        # Format results
        results = []
        for po in pos:
            # Get company names
            buyer_company = self.db.query(Company).filter(Company.id == po.buyer_company_id).first()
            seller_company = self.db.query(Company).filter(Company.id == po.seller_company_id).first()
            product = self.db.query(Product).filter(Product.id == po.product_id).first()
            
            user_role = "buyer" if po.buyer_company_id == self.user_company_id else "seller"
            
            results.append({
                "po_number": po.po_number,
                "buyer_company": buyer_company.name if buyer_company else "Unknown",
                "seller_company": seller_company.name if seller_company else "Unknown",
                "product_name": product.name if product else "Unknown Product",
                "quantity": float(po.quantity),
                "unit": po.unit,
                "unit_price": float(po.unit_price),
                "total_amount": float(po.total_amount),
                "status": po.status,
                "delivery_date": po.delivery_date.isoformat() if po.delivery_date else None,
                "delivery_location": po.delivery_location,
                "user_role": user_role,
                "created_at": po.created_at.isoformat() if po.created_at else None
            })
        
        return results
    
    def _get_farm_locations(self, include_coordinates: bool = True, certification_filter: str = None) -> List[Dict[str, Any]]:
        """Get farm locations owned by the company."""
        
        query = self.db.query(Location).filter(
            Location.company_id == self.user_company_id,
            Location.is_farm_location == True
        )
        
        farms = query.all()
        
        results = []
        for farm in farms:
            # Filter by certification if specified
            if certification_filter and farm.certifications:
                if certification_filter.upper() not in [cert.upper() for cert in farm.certifications]:
                    continue
            
            farm_data = {
                "farm_id": farm.registration_number,
                "name": farm.name,
                "farm_type": farm.farm_type,
                "specialization": farm.specialization,
                "farm_size_hectares": float(farm.farm_size_hectares) if farm.farm_size_hectares else None,
                "established_year": farm.established_year,
                "certifications": farm.certifications or [],
                "compliance_status": farm.compliance_status,
                "farm_owner_name": farm.farm_owner_name
            }
            
            if include_coordinates:
                farm_data["coordinates"] = {
                    "latitude": float(farm.latitude) if farm.latitude else None,
                    "longitude": float(farm.longitude) if farm.longitude else None,
                    "accuracy_meters": float(farm.accuracy_meters) if farm.accuracy_meters else None
                }
                farm_data["address"] = {
                    "street": farm.address,
                    "city": farm.city,
                    "state": farm.state_province,
                    "country": farm.country
                }
            
            results.append(farm_data)
        
        return results
    
    def _get_company_info(self) -> Dict[str, Any]:
        """Get detailed information about the company."""
        
        company = self.db.query(Company).filter(Company.id == self.user_company_id).first()
        
        if not company:
            return {"error": "Company not found"}
        
        # Get some aggregate stats
        total_farms = self.db.query(Location).filter(
            Location.company_id == self.user_company_id,
            Location.is_farm_location == True
        ).count()
        
        total_batches = self.db.query(Batch).filter(
            Batch.company_id == self.user_company_id,
            Batch.status == 'active'
        ).count()
        
        return {
            "company_name": company.name,
            "company_type": company.company_type,
            "industry_sector": company.industry_sector,
            "country": company.country,
            "transparency_score": company.transparency_score,
            "compliance_status": company.compliance_status,
            "subscription_tier": company.subscription_tier,
            "is_verified": company.is_verified,
            "statistics": {
                "total_farms": total_farms,
                "active_batches": total_batches,
                "member_since": company.created_at.isoformat() if company.created_at else None
            },
            "contact": {
                "email": company.email,
                "phone": company.phone,
                "website": company.website
            },
            "address": {
                "street": company.address_street,
                "city": company.address_city,
                "state": company.address_state,
                "country": company.address_country,
                "postal_code": company.address_postal_code
            }
        }

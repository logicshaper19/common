"""
Comprehensive context manager for the Common Supply Chain Platform.
Gathers all relevant context data for AI assistant to provide professional, data-driven responses.
"""

from sqlalchemy.orm import Session
from app.models.user import User
from app.models.company import Company
from app.models.batch import Batch
from app.models.purchase_order import PurchaseOrder
from app.models.product import Product
from app.core.logging import get_logger
from typing import Dict, Any, List, Optional
import os
from datetime import datetime, timedelta

logger = get_logger(__name__)


class SupplyChainContextManager:
    """Comprehensive context manager for your Common Supply Chain Platform."""
    
    def __init__(self, db: Session, current_user: User):
        self.db = db
        self.user = current_user
        
    async def get_comprehensive_context(self) -> Dict[str, Any]:
        """Gather ALL relevant context for the AI assistant."""
        
        try:
            context = {
                # User & Company Context
                "user_info": self._get_user_info(),
                
                # Feature Flags (from your .env)
                "available_features": self._get_feature_context(),
                
                # Live Data Context
                "current_data": await self._get_live_data_context(),
                
                # Business Rules (from your .env)
                "business_rules": self._get_business_rules(),
                
                # Company Relationships
                "company_relationships": await self._get_company_relationships()
            }
            
            logger.info(f"Comprehensive context gathered for user {self.user.id} at company {self.user.company_id}")
            return context
            
        except Exception as e:
            logger.error(f"Error gathering comprehensive context: {e}")
            return self._get_fallback_context()
    
    def _get_user_info(self) -> Dict[str, Any]:
        """Get user and company information."""
        return {
            "name": self.user.full_name or "User",
            "role": self.user.role or "unknown",
            "company_name": self.user.company.name if self.user.company else "Unknown Company",
            "company_type": self.user.company.company_type if self.user.company else "unknown",
            "company_id": self.user.company_id
        }
    
    def _get_feature_context(self) -> Dict[str, bool]:
        """Get enabled features from your .env configuration."""
        
        return {
            "v2_features_enabled": os.getenv("V2_FEATURES_ENABLED", "false") == "true",
            "brand_dashboard": os.getenv("V2_DASHBOARD_BRAND", "false") == "true",
            "processor_dashboard": os.getenv("V2_DASHBOARD_PROCESSOR", "false") == "true",
            "originator_dashboard": os.getenv("V2_DASHBOARD_ORIGINATOR", "false") == "true",
            "trader_dashboard": os.getenv("V2_DASHBOARD_TRADER", "false") == "true",
            "notification_center": os.getenv("V2_NOTIFICATION_CENTER", "false") == "true",
            "platform_admin": os.getenv("V2_DASHBOARD_PLATFORM_ADMIN", "false") == "true"
        }
    
    async def _get_live_data_context(self) -> Dict[str, Any]:
        """Get user's actual current data from database."""
        
        context = {}
        
        try:
            # Current Inventory Context
            batches = self.db.query(Batch).filter(
                Batch.company_id == self.user.company_id
            ).limit(10).all()
            
            if batches:
                # Calculate inventory metrics
                total_quantity = sum(float(b.quantity or 0) for b in batches)
                available_batches = [b for b in batches if b.status == 'available']
                transparency_scores = [float(b.transparency_score or 0) for b in batches if b.transparency_score]
                avg_transparency = sum(transparency_scores) / len(transparency_scores) if transparency_scores else 0
                
                context["inventory"] = {
                    "total_batches": len(batches),
                    "available_batches": len(available_batches),
                    "total_quantity": total_quantity,
                    "avg_transparency": avg_transparency,
                    "recent_batches": [
                        {
                            "batch_id": b.batch_id,
                            "product": b.product.name if b.product else "Unknown",
                            "quantity": float(b.quantity or 0),
                            "status": b.status,
                            "transparency": float(b.transparency_score or 0)
                        } for b in batches[:5]
                    ]
                }
            
            # Purchase Orders Context
            buyer_pos = self.db.query(PurchaseOrder).filter(
                PurchaseOrder.buyer_company_id == self.user.company_id
            ).limit(10).all()
            
            seller_pos = self.db.query(PurchaseOrder).filter(
                PurchaseOrder.seller_company_id == self.user.company_id
            ).limit(10).all()
            
            all_pos = buyer_pos + seller_pos
            pending_orders = [po for po in all_pos if po.status == 'pending']
            
            context["purchase_orders"] = {
                "as_buyer": len(buyer_pos),
                "as_seller": len(seller_pos),
                "pending_orders": len(pending_orders),
                "total_orders": len(all_pos),
                "recent_orders": [
                    {
                        "id": po.id,
                        "po_number": po.po_number if hasattr(po, 'po_number') else f"PO-{po.id}",
                        "role": "buyer" if po.buyer_company_id == self.user.company_id else "seller",
                        "partner": po.seller.name if po.buyer_company_id == self.user.company_id and po.seller else (po.buyer.name if po.buyer else "Unknown"),
                        "product": po.product.name if po.product else "Unknown",
                        "quantity": float(po.quantity or 0),
                        "status": po.status
                    } for po in all_pos[:5]
                ]
            }
            
            # Company Relationships
            trading_partners = set()
            for po in buyer_pos:
                if po.seller and po.seller.name:
                    trading_partners.add(po.seller.name)
            for po in seller_pos:
                if po.buyer and po.buyer.name:
                    trading_partners.add(po.buyer.name)
                    
            context["trading_partners"] = list(trading_partners)
            
        except Exception as e:
            logger.error(f"Error retrieving live data context: {e}")
            context["data_error"] = f"Unable to retrieve some data: {str(e)}"
            
        return context
    
    async def _get_company_relationships(self) -> Dict[str, Any]:
        """Get company trading relationships and network data."""
        
        try:
            # Get companies this user's company trades with
            trading_relationships = {
                "suppliers": [],
                "customers": [],
                "total_relationships": 0
            }
            
            # Get suppliers (companies we buy from)
            supplier_pos = self.db.query(PurchaseOrder).filter(
                PurchaseOrder.buyer_company_id == self.user.company_id
            ).join(Company, PurchaseOrder.seller_company_id == Company.id).limit(20).all()
            
            suppliers = set()
            for po in supplier_pos:
                if po.seller and po.seller.name:
                    suppliers.add(po.seller.name)
            
            trading_relationships["suppliers"] = list(suppliers)
            
            # Get customers (companies that buy from us)
            customer_pos = self.db.query(PurchaseOrder).filter(
                PurchaseOrder.seller_company_id == self.user.company_id
            ).join(Company, PurchaseOrder.buyer_company_id == Company.id).limit(20).all()
            
            customers = set()
            for po in customer_pos:
                if po.buyer and po.buyer.name:
                    customers.add(po.buyer.name)
            
            trading_relationships["customers"] = list(customers)
            trading_relationships["total_relationships"] = len(suppliers) + len(customers)
            
            return trading_relationships
            
        except Exception as e:
            logger.error(f"Error retrieving company relationships: {e}")
            return {
                "suppliers": [],
                "customers": [],
                "total_relationships": 0,
                "error": str(e)
            }
    
    def _get_business_rules(self) -> Dict[str, Any]:
        """Get business rules from your .env configuration."""
        
        return {
            "transparency_degradation_factor": float(os.getenv("TRANSPARENCY_DEGRADATION_FACTOR", "0.95")),
            "transparency_timeout": int(os.getenv("TRANSPARENCY_CALCULATION_TIMEOUT", "30")),
            "app_name": os.getenv("APP_NAME", "Common Supply Chain Platform"),
            "environment": os.getenv("ENVIRONMENT", "development"),
            "database_url": "configured" if os.getenv("DATABASE_URL") else "not_configured"
        }
    
    def _get_fallback_context(self) -> Dict[str, Any]:
        """Get minimal fallback context when data retrieval fails."""
        
        return {
            "user_info": self._get_user_info(),
            "available_features": self._get_feature_context(),
            "business_rules": self._get_business_rules(),
            "current_data": {
                "inventory": {"total_batches": 0, "available_batches": 0, "total_quantity": 0.0},
                "purchase_orders": {"as_buyer": 0, "as_seller": 0, "pending_orders": 0},
                "trading_partners": []
            },
            "company_relationships": {
                "suppliers": [],
                "customers": [],
                "total_relationships": 0
            },
            "fallback_mode": True
        }

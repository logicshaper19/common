"""
ERP Integration Service

Focused service for external system integration only.
This service handles genuinely complex operations that require
external system communication and data synchronization.
"""
import requests
import json
from datetime import datetime
from typing import Dict, Any, Optional, List
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.purchase_order import PurchaseOrder
from app.core.logging import get_logger

logger = get_logger(__name__)


class ERPIntegrationService:
    """
    Focused on external system integration only.
    
    This service handles:
    - External API communication
    - Data transformation between systems
    - Error handling and retry logic
    - Synchronization state management
    """
    
    def __init__(self, db: Session, erp_system: str = "SAP"):
        self.db = db
        self.erp_system = erp_system
        self.base_url = self._get_erp_base_url()
        self.api_key = self._get_erp_api_key()
        self.timeout = 30
    
    def _get_erp_base_url(self) -> str:
        """Get ERP system base URL from configuration."""
        # In real implementation, this would come from settings
        return "https://api.sap.com/v1"  # Placeholder
    
    def _get_erp_api_key(self) -> str:
        """Get ERP system API key from configuration."""
        # In real implementation, this would come from secure settings
        return "placeholder-api-key"  # Placeholder
    
    def sync_purchase_order_to_erp(self, po_id: UUID) -> Dict[str, Any]:
        """
        Sync a purchase order to the ERP system.
        
        This is genuine service territory - external system integration.
        """
        try:
            # Get PO data
            po = self.db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
            if not po:
                raise ValueError(f"Purchase order {po_id} not found")
            
            # Transform data for ERP system
            erp_data = self._transform_po_for_erp(po)
            
            # Send to ERP system
            response = self._send_to_erp(erp_data)
            
            # Update sync status
            self._update_sync_status(po, response)
            
            return {
                'success': True,
                'erp_po_id': response.get('erp_po_id'),
                'sync_timestamp': datetime.utcnow(),
                'message': 'Successfully synced to ERP'
            }
            
        except Exception as e:
            logger.error(f"Failed to sync PO {po_id} to ERP: {str(e)}")
            self._update_sync_error(po, str(e))
            return {
                'success': False,
                'error': str(e),
                'sync_timestamp': datetime.utcnow()
            }
    
    def _transform_po_for_erp(self, po: PurchaseOrder) -> Dict[str, Any]:
        """
        Transform purchase order data for ERP system format.
        
        This is genuine service territory - complex data transformation.
        """
        # Complex transformation logic based on ERP system requirements
        if self.erp_system == "SAP":
            return self._transform_for_sap(po)
        elif self.erp_system == "Oracle":
            return self._transform_for_oracle(po)
        else:
            return self._transform_generic(po)
    
    def _transform_for_sap(self, po: PurchaseOrder) -> Dict[str, Any]:
        """Transform data for SAP ERP system."""
        return {
            'PO_NUMBER': po.po_number,
            'BUYER_COMPANY': po.buyer_company_id,
            'SELLER_COMPANY': po.seller_company_id,
            'PRODUCT_ID': po.product_id,
            'QUANTITY': float(po.quantity),
            'UNIT': po.unit,
            'PRICE_PER_UNIT': float(po.price_per_unit),
            'TOTAL_AMOUNT': float(po.total_amount),
            'STATUS': self._map_status_to_sap(po.status),
            'CREATED_DATE': po.created_at.isoformat() if po.created_at else None,
            'CONFIRMED_DATE': po.confirmed_at.isoformat() if po.confirmed_at else None
        }
    
    def _transform_for_oracle(self, po: PurchaseOrder) -> Dict[str, Any]:
        """Transform data for Oracle ERP system."""
        return {
            'poNumber': po.po_number,
            'buyerCompanyId': str(po.buyer_company_id),
            'sellerCompanyId': str(po.seller_company_id),
            'productId': str(po.product_id),
            'quantity': po.quantity,
            'unitOfMeasure': po.unit,
            'unitPrice': po.price_per_unit,
            'totalValue': po.total_amount,
            'status': self._map_status_to_oracle(po.status),
            'creationDate': po.created_at.isoformat() if po.created_at else None,
            'confirmationDate': po.confirmed_at.isoformat() if po.confirmed_at else None
        }
    
    def _transform_generic(self, po: PurchaseOrder) -> Dict[str, Any]:
        """Generic transformation for unknown ERP systems."""
        return {
            'purchase_order': {
                'id': str(po.id),
                'number': po.po_number,
                'buyer_company_id': str(po.buyer_company_id),
                'seller_company_id': str(po.seller_company_id),
                'product_id': str(po.product_id),
                'quantity': float(po.quantity),
                'unit': po.unit,
                'price_per_unit': float(po.price_per_unit),
                'total_amount': float(po.total_amount),
                'status': po.status,
                'created_at': po.created_at.isoformat() if po.created_at else None,
                'confirmed_at': po.confirmed_at.isoformat() if po.confirmed_at else None
            }
        }
    
    def _map_status_to_sap(self, status: str) -> str:
        """Map internal status to SAP status codes."""
        status_mapping = {
            'draft': 'DRAFT',
            'pending': 'PENDING',
            'confirmed': 'CONFIRMED',
            'approved': 'APPROVED',
            'delivered': 'DELIVERED',
            'cancelled': 'CANCELLED'
        }
        return status_mapping.get(status, 'UNKNOWN')
    
    def _map_status_to_oracle(self, status: str) -> str:
        """Map internal status to Oracle status codes."""
        status_mapping = {
            'draft': 'DRAFT',
            'pending': 'PENDING',
            'confirmed': 'CONFIRMED',
            'approved': 'APPROVED',
            'delivered': 'DELIVERED',
            'cancelled': 'CANCELLED'
        }
        return status_mapping.get(status, 'UNKNOWN')
    
    def _send_to_erp(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send data to ERP system via API.
        
        This is genuine service territory - external system communication.
        """
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}',
            'X-ERP-System': self.erp_system
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/purchase-orders",
                json=data,
                headers=headers,
                timeout=self.timeout
            )
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"ERP API request failed: {str(e)}")
            raise Exception(f"Failed to communicate with ERP system: {str(e)}")
    
    def _update_sync_status(self, po: PurchaseOrder, response: Dict[str, Any]) -> None:
        """Update PO sync status after successful ERP sync."""
        # This would update the ERP sync status in the database
        # For now, just log the success
        logger.info(f"PO {po.id} successfully synced to ERP with ID: {response.get('erp_po_id')}")
    
    def _update_sync_error(self, po: PurchaseOrder, error: str) -> None:
        """Update PO sync status after failed ERP sync."""
        # This would update the ERP sync error in the database
        # For now, just log the error
        logger.error(f"PO {po.id} failed to sync to ERP: {error}")
    
    def get_erp_sync_status(self, po_id: UUID) -> Dict[str, Any]:
        """
        Get ERP sync status for a purchase order.
        
        This is genuine service territory - external system status checking.
        """
        try:
            po = self.db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
            if not po:
                raise ValueError(f"Purchase order {po_id} not found")
            
            # Check status with ERP system
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'X-ERP-System': self.erp_system
            }
            
            response = requests.get(
                f"{self.base_url}/purchase-orders/{po.po_number}/status",
                headers=headers,
                timeout=self.timeout
            )
            
            response.raise_for_status()
            erp_status = response.json()
            
            return {
                'po_id': po_id,
                'local_status': po.status,
                'erp_status': erp_status.get('status'),
                'erp_po_id': erp_status.get('erp_po_id'),
                'last_sync': erp_status.get('last_updated'),
                'in_sync': po.status == self._map_erp_status_to_local(erp_status.get('status'))
            }
            
        except Exception as e:
            logger.error(f"Failed to get ERP sync status for PO {po_id}: {str(e)}")
            return {
                'po_id': po_id,
                'error': str(e),
                'in_sync': False
            }
    
    def _map_erp_status_to_local(self, erp_status: str) -> str:
        """Map ERP status back to local status."""
        if self.erp_system == "SAP":
            status_mapping = {
                'DRAFT': 'draft',
                'PENDING': 'pending',
                'CONFIRMED': 'confirmed',
                'APPROVED': 'approved',
                'DELIVERED': 'delivered',
                'CANCELLED': 'cancelled'
            }
        else:  # Oracle or generic
            status_mapping = {
                'DRAFT': 'draft',
                'PENDING': 'pending',
                'CONFIRMED': 'confirmed',
                'APPROVED': 'approved',
                'DELIVERED': 'delivered',
                'CANCELLED': 'cancelled'
            }
        
        return status_mapping.get(erp_status, 'unknown')

"""
API client wrapper for E2E tests
"""
from typing import Dict, Any, Optional, List
from fastapi.testclient import TestClient
from uuid import UUID


class APIClient:
    """Wrapper for API calls with better error handling."""
    
    def __init__(self, client: TestClient):
        self.client = client
    
    def get_user_profile(self, headers: Dict[str, str]):
        """Get user profile."""
        return self.client.get("/api/v1/auth/me", headers=headers)
    
    def get_company_dashboard(self, company_id: UUID, headers: Dict[str, str]):
        """Get company dashboard."""
        return self.client.get(f"/api/v1/companies/{company_id}", headers=headers)
    
    def get_products(self, headers: Dict[str, str], category: Optional[str] = None):
        """Get products, optionally filtered by category."""
        url = "/api/v1/products"
        if category:
            url += f"?category={category}"
        return self.client.get(url, headers=headers)
    
    def get_product(self, product_id: UUID, headers: Dict[str, str]):
        """Get product by ID."""
        return self.client.get(f"/api/v1/products/{product_id}", headers=headers)
    
    def create_purchase_order(self, po_data: Dict[str, Any], headers: Dict[str, str]):
        """Create purchase order."""
        return self.client.post("/api/v1/purchase-orders", json=po_data, headers=headers)
    
    def get_purchase_order(self, po_id: UUID, headers: Dict[str, str]):
        """Get purchase order by ID."""
        return self.client.get(f"/api/v1/purchase-orders/{po_id}", headers=headers)
    
    def get_purchase_orders(self, headers: Dict[str, str], **filters):
        """Get purchase orders with optional filters."""
        url = "/api/v1/purchase-orders"
        if filters:
            params = "&".join([f"{k}={v}" for k, v in filters.items()])
            url += f"?{params}"
        return self.client.get(url, headers=headers)
    
    def update_purchase_order(self, po_id: UUID, update_data: Dict[str, Any], headers: Dict[str, str]):
        """Update purchase order."""
        return self.client.put(f"/api/v1/purchase-orders/{po_id}", json=update_data, headers=headers)
    
    def confirm_purchase_order(self, po_id: UUID, confirmation_data: Dict[str, Any], headers: Dict[str, str]):
        """Confirm purchase order with specific confirmation data."""
        return self.client.post(f"/api/v1/purchase-orders/{po_id}/confirm", json=confirmation_data, headers=headers)
    
    def get_transparency_score(self, company_id: UUID, headers: Dict[str, str]):
        """Get transparency score for company."""
        return self.client.get(f"/api/v1/transparency/{company_id}", headers=headers)
    
    def get_transparency_detailed(self, po_id: UUID, headers: Dict[str, str]):
        """Get detailed transparency for purchase order."""
        return self.client.get(f"/api/v1/transparency/{po_id}/detailed", headers=headers)
    
    def trace_supply_chain(self, trace_data: Dict[str, Any], headers: Dict[str, str]):
        """Trace supply chain."""
        return self.client.post("/api/v1/traceability/trace", json=trace_data, headers=headers)
    
    def get_sustainability_metrics(self, headers: Dict[str, str]):
        """Get sustainability metrics."""
        return self.client.get("/api/v1/transparency/sustainability-metrics", headers=headers)
    
    def generate_transparency_report(self, report_data: Dict[str, Any], headers: Dict[str, str]):
        """Generate transparency report."""
        return self.client.post("/api/v1/transparency/reports", json=report_data, headers=headers)
    
    def health_check(self):
        """Health check endpoint."""
        return self.client.get("/api/v1/health")
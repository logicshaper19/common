"""
Comprehensive tests for refactored purchase order system
Tests service layer, repository layer, and API layer
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from uuid import uuid4, UUID
from datetime import date, datetime
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.services.purchase_order_service import PurchaseOrderService
from app.repositories.purchase_order_repository import PurchaseOrderRepository
from app.db.purchase_order_queries import (
    get_pos_with_relationships,
    get_incoming_pos_with_relationships,
    get_po_with_details
)
from app.schemas.purchase_order import PurchaseOrderCreate
from app.models.purchase_order import PurchaseOrder
from app.models.user import CurrentUser
from app.main import app


class TestPurchaseOrderQueries:
    """Test the query optimization layer."""
    
    def test_get_pos_with_relationships(self):
        """Test that base query includes eager loading."""
        mock_db = Mock(spec=Session)
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        
        result = get_pos_with_relationships(mock_db)
        
        # Verify that selectinload options are applied
        mock_query.options.assert_called_once()
        mock_db.query.assert_called_once_with(PurchaseOrder)
    
    def test_get_incoming_pos_with_relationships(self):
        """Test incoming POs query with relationships."""
        mock_db = Mock(spec=Session)
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        
        company_id = uuid4()
        result = get_incoming_pos_with_relationships(mock_db, company_id)
        
        # Verify query structure
        mock_db.query.assert_called_once_with(PurchaseOrder)
        mock_query.options.assert_called_once()
        mock_query.filter.assert_called()
        mock_query.order_by.assert_called_once()
        mock_query.limit.assert_called_once_with(10)
        mock_query.all.assert_called_once()
    
    def test_get_po_with_details(self):
        """Test single PO query with details."""
        mock_db = Mock(spec=Session)
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        
        po_id = uuid4()
        result = get_po_with_details(mock_db, po_id)
        
        # Verify query structure
        mock_db.query.assert_called_once_with(PurchaseOrder)
        mock_query.options.assert_called_once()
        mock_query.filter.assert_called_once()
        mock_query.first.assert_called_once()


class TestPurchaseOrderRepository:
    """Test the repository layer."""
    
    @pytest.fixture
    def mock_db(self):
        return Mock(spec=Session)
    
    @pytest.fixture
    def repository(self, mock_db):
        return PurchaseOrderRepository(mock_db)
    
    def test_find_with_filters(self, repository, mock_db):
        """Test finding POs with filters."""
        # Mock the query chain
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 10
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        
        filters = {
            'company_id': uuid4(),
            'status': 'pending',
            'page': 1,
            'per_page': 20
        }
        
        result = repository.find_with_filters(filters)
        
        # Verify result structure
        assert 'purchase_orders' in result
        assert 'total' in result
        assert 'total_pages' in result
        assert result['total'] == 10
        assert result['total_pages'] == 1
    
    def test_create_purchase_order(self, repository, mock_db):
        """Test creating a purchase order."""
        mock_po = Mock(spec=PurchaseOrder)
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None
        
        po_data = PurchaseOrderCreate(
            po_number="PO-001",
            buyer_company_id=uuid4(),
            seller_company_id=uuid4(),
            product_id=uuid4(),
            quantity=100,
            unit_price=10.0,
            total_amount=1000.0,
            unit="kg",
            delivery_date=date.today(),
            delivery_location="Test Location",
            notes="Test notes"
        )
        
        current_user = Mock(spec=CurrentUser)
        current_user.id = uuid4()
        
        # Mock the PurchaseOrder constructor
        with patch('app.repositories.purchase_order_repository.PurchaseOrder') as mock_po_class:
            mock_po_class.return_value = mock_po
            
            result = repository.create(po_data, current_user)
            
            # Verify database operations
            mock_db.add.assert_called_once_with(mock_po)
            mock_db.commit.assert_called_once()
            mock_db.refresh.assert_called_once_with(mock_po)
            assert result == mock_po
    
    def test_update_status(self, repository, mock_db):
        """Test updating PO status."""
        mock_po = Mock(spec=PurchaseOrder)
        mock_po.id = uuid4()
        mock_po.po_number = "PO-001"
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_po
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None
        
        current_user = Mock(spec=CurrentUser)
        current_user.id = uuid4()
        
        result = repository.update_status(mock_po.id, 'confirmed', current_user)
        
        # Verify status update
        assert mock_po.status == 'confirmed'
        assert mock_po.updated_by == current_user.id
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once_with(mock_po)
        assert result == mock_po


class TestPurchaseOrderService:
    """Test the service layer."""
    
    @pytest.fixture
    def mock_db(self):
        return Mock(spec=Session)
    
    @pytest.fixture
    def mock_repository(self):
        return Mock(spec=PurchaseOrderRepository)
    
    @pytest.fixture
    def service(self, mock_db, mock_repository):
        service = PurchaseOrderService(mock_db)
        service.repository = mock_repository
        return service
    
    def test_get_filtered_purchase_orders(self, service, mock_repository):
        """Test getting filtered purchase orders."""
        # Mock repository response
        mock_po = Mock(spec=PurchaseOrder)
        mock_po.id = uuid4()
        mock_po.po_number = "PO-001"
        mock_po.status = "pending"
        mock_po.buyer_company = Mock()
        mock_po.buyer_company.id = uuid4()
        mock_po.buyer_company.name = "Buyer Co"
        mock_po.buyer_company.company_type = "buyer"
        mock_po.seller_company = Mock()
        mock_po.seller_company.id = uuid4()
        mock_po.seller_company.name = "Seller Co"
        mock_po.seller_company.company_type = "seller"
        mock_po.product = Mock()
        mock_po.product.id = uuid4()
        mock_po.product.name = "Test Product"
        mock_po.product.description = "Test Description"
        mock_po.product.default_unit = "kg"
        mock_po.product.category = "test"
        mock_po.quantity = 100
        mock_po.unit_price = 10.0
        mock_po.total_amount = 1000.0
        mock_po.unit = "kg"
        mock_po.delivery_date = date.today()
        mock_po.delivery_location = "Test Location"
        mock_po.notes = "Test notes"
        mock_po.created_at = datetime.now()
        mock_po.updated_at = datetime.now()
        
        mock_repository.find_with_filters.return_value = {
            'purchase_orders': [mock_po],
            'total': 1,
            'total_pages': 1
        }
        
        filters = {
            'company_id': uuid4(),
            'page': 1,
            'per_page': 20
        }
        
        current_user = Mock(spec=CurrentUser)
        current_user.company_id = uuid4()
        
        result = service.get_filtered_purchase_orders(filters, current_user)
        
        # Verify service calls repository
        mock_repository.find_with_filters.assert_called_once()
        
        # Verify response structure
        assert result.total == 1
        assert result.page == 1
        assert result.per_page == 20
        assert len(result.purchase_orders) == 1
    
    def test_create_purchase_order(self, service, mock_repository):
        """Test creating a purchase order."""
        mock_po = Mock(spec=PurchaseOrder)
        mock_repository.create.return_value = mock_po
        
        po_data = PurchaseOrderCreate(
            po_number="PO-001",
            buyer_company_id=uuid4(),
            seller_company_id=uuid4(),
            product_id=uuid4(),
            quantity=100,
            unit_price=10.0,
            total_amount=1000.0,
            unit="kg",
            delivery_date=date.today(),
            delivery_location="Test Location",
            notes="Test notes"
        )
        
        current_user = Mock(spec=CurrentUser)
        current_user.id = uuid4()
        
        with patch('app.core.simple_auth.can_create_purchase_order', return_value=True), \
             patch('app.core.minimal_audit.log_po_created') as mock_log:
            
            result = service.create_purchase_order(po_data, current_user)
            
            # Verify repository call
            mock_repository.create.assert_called_once_with(po_data, current_user)
            
            # Verify audit logging
            mock_log.assert_called_once()
            
            # Verify response
            assert result == mock_po
    
    def test_confirm_purchase_order(self, service, mock_repository):
        """Test confirming a purchase order."""
        mock_po = Mock(spec=PurchaseOrder)
        mock_po.id = uuid4()
        mock_po.po_number = "PO-001"
        
        mock_repository.find_by_id.return_value = mock_po
        mock_repository.update_status.return_value = mock_po
        
        current_user = Mock(spec=CurrentUser)
        current_user.id = uuid4()
        
        with patch('app.core.simple_auth.can_confirm_purchase_order', return_value=True), \
             patch('app.core.minimal_audit.log_po_confirmed') as mock_log:
            
            result = service.confirm_purchase_order(mock_po.id, current_user)
            
            # Verify repository calls
            mock_repository.find_by_id.assert_called_once_with(mock_po.id)
            mock_repository.update_status.assert_called_once_with(mock_po.id, 'confirmed', current_user)
            
            # Verify audit logging
            mock_log.assert_called_once()
            
            # Verify response
            assert result == mock_po


class TestPurchaseOrderAPI:
    """Test the API layer."""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    @pytest.fixture
    def mock_auth_token(self):
        return "test-auth-token"
    
    def test_get_purchase_orders_endpoint(self, client, mock_auth_token):
        """Test the GET /purchase-orders endpoint."""
        with patch('app.api.purchase_orders.PurchaseOrderService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            
            # Mock the service response
            mock_response = Mock()
            mock_response.total = 1
            mock_response.page = 1
            mock_response.per_page = 20
            mock_response.total_pages = 1
            mock_response.purchase_orders = []
            
            mock_service.get_filtered_purchase_orders.return_value = mock_response
            
            response = client.get(
                "/api/v1/purchase-orders/",
                headers={"Authorization": f"Bearer {mock_auth_token}"}
            )
            
            # Verify service was called
            mock_service.get_filtered_purchase_orders.assert_called_once()
            
            # Note: In a real test, you'd need to mock the authentication
            # This is a simplified test structure
    
    def test_create_purchase_order_endpoint(self, client, mock_auth_token):
        """Test the POST /purchase-orders endpoint."""
        with patch('app.api.purchase_orders.PurchaseOrderService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            
            # Mock the service response
            mock_po = Mock()
            mock_po.id = uuid4()
            mock_po.po_number = "PO-001"
            
            mock_service.create_purchase_order.return_value = mock_po
            
            po_data = {
                "po_number": "PO-001",
                "buyer_company_id": str(uuid4()),
                "seller_company_id": str(uuid4()),
                "product_id": str(uuid4()),
                "quantity": 100,
                "unit_price": 10.0,
                "total_amount": 1000.0,
                "unit": "kg",
                "delivery_date": date.today().isoformat(),
                "delivery_location": "Test Location",
                "notes": "Test notes"
            }
            
            response = client.post(
                "/api/v1/purchase-orders/",
                json=po_data,
                headers={"Authorization": f"Bearer {mock_auth_token}"}
            )
            
            # Verify service was called
            mock_service.create_purchase_order.assert_called_once()
            
            # Note: In a real test, you'd need to mock the authentication
            # This is a simplified test structure


class TestIntegration:
    """Integration tests for the refactored system."""
    
    def test_service_repository_integration(self):
        """Test that service layer properly integrates with repository layer."""
        mock_db = Mock(spec=Session)
        
        # Create real service and repository instances
        service = PurchaseOrderService(mock_db)
        repository = PurchaseOrderRepository(mock_db)
        
        # Verify service has repository
        assert service.repository is not None
        assert isinstance(service.repository, PurchaseOrderRepository)
    
    def test_query_optimization_integration(self):
        """Test that repository uses optimized queries."""
        mock_db = Mock(spec=Session)
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 0
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        
        repository = PurchaseOrderRepository(mock_db)
        
        filters = {
            'company_id': uuid4(),
            'page': 1,
            'per_page': 20
        }
        
        # This should use the optimized query
        result = repository.find_with_filters(filters)
        
        # Verify that options (eager loading) was called
        mock_query.options.assert_called_once()
    
    def test_error_handling_flow(self):
        """Test error handling flows through all layers."""
        mock_db = Mock(spec=Session)
        service = PurchaseOrderService(mock_db)
        
        # Mock repository to raise an exception
        service.repository.find_with_filters.side_effect = Exception("Database error")
        
        filters = {'company_id': uuid4(), 'page': 1, 'per_page': 20}
        current_user = Mock(spec=CurrentUser)
        current_user.company_id = uuid4()
        
        # Service should propagate the exception
        with pytest.raises(Exception, match="Database error"):
            service.get_filtered_purchase_orders(filters, current_user)


if __name__ == "__main__":
    pytest.main([__file__])

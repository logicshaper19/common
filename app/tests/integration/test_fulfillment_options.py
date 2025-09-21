"""
Tests for flexible fulfillment options for traders and downstream companies.
"""
import pytest
from uuid import uuid4
from datetime import datetime, date, timedelta
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.services.po_chaining import POChainingService
from app.models.company import Company
from app.models.user import User
from app.models.product import Product
from app.models.purchase_order import PurchaseOrder
from app.schemas.purchase_order import PurchaseOrderCreate, PurchaseOrderConfirmation

# Create test database
SQLALCHEMY_DATABASE_URL = "postgresql://postgres:password@localhost:5432/test_fulfillment"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_pre_ping=True)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
Base.metadata.create_all(bind=engine)


@pytest.fixture(autouse=True)
def clean_db():
    """Clean database before each test."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture
def db_session():
    """Get database session for testing."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def sample_companies(db_session: Session):
    """Create sample companies for testing."""
    companies = {}
    
    # Brand
    companies['brand'] = Company(
        id=uuid4(),
        name="Global Fashion Brand",
        company_type="brand",
        email="brand@example.com",
        country="USA"
    )
    
    # Trader with existing inventory
    companies['trader'] = Company(
        id=uuid4(),
        name="Supply Chain Trader",
        company_type="trader",
        email="trader@example.com",
        country="Singapore"
    )
    
    # Processor
    companies['processor'] = Company(
        id=uuid4(),
        name="Textile Processor",
        company_type="processor",
        email="processor@example.com",
        country="Malaysia"
    )
    
    for company in companies.values():
        db_session.add(company)
    db_session.commit()
    
    for company in companies.values():
        db_session.refresh(company)
    
    return companies


@pytest.fixture
def sample_users(db_session: Session, sample_companies):
    """Create sample users for each company."""
    users = {}
    
    for company_type, company in sample_companies.items():
        user = User(
            id=uuid4(),
            email=f"user@{company_type}.com",
            hashed_password="hashed_password",
            full_name=f"{company_type.title()} User",
            role="user",
            company_id=company.id
        )
        db_session.add(user)
        users[company_type] = user
    
    db_session.commit()
    
    for user in users.values():
        db_session.refresh(user)
    
    return users


@pytest.fixture
def sample_product(db_session: Session, sample_companies):
    """Create sample product."""
    product = Product(
        id=uuid4(),
        name="Organic Cotton",
        description="Sustainable organic cotton",
        company_id=sample_companies['brand'].id,
        unit="MT"
    )
    
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)
    
    return product


@pytest.fixture
def business_relationships(db_session: Session, sample_companies):
    """Create business relationships between companies."""
    relationships = []
    
    # Brand -> Trader
    rel1 = BusinessRelationship(
        id=uuid4(),
        buyer_company_id=sample_companies['brand'].id,
        seller_company_id=sample_companies['trader'].id,
        relationship_type="supplier",
        is_active=True
    )
    
    # Trader -> Processor
    rel2 = BusinessRelationship(
        id=uuid4(),
        buyer_company_id=sample_companies['trader'].id,
        seller_company_id=sample_companies['processor'].id,
        relationship_type="supplier",
        is_active=True
    )
    
    relationships = [rel1, rel2]
    
    for rel in relationships:
        db_session.add(rel)
    db_session.commit()
    
    for rel in relationships:
        db_session.refresh(rel)
    
    return relationships


class TestFlexibleFulfillmentOptions:
    """Test flexible fulfillment options for traders and downstream companies."""
    
    def test_create_child_pos_fulfillment(self, db_session: Session, sample_companies, sample_users, sample_product, business_relationships):
        """Test fulfillment by creating child POs to suppliers."""
        service = POChainingService(db_session)
        
        # Brand creates PO to Trader
        brand_po = PurchaseOrder(
            id=uuid4(),
            po_number="PO-001",
            buyer_company_id=sample_companies['brand'].id,
            seller_company_id=sample_companies['trader'].id,
            product_id=sample_product.id,
            quantity=Decimal("1000.0"),
            unit="MT",
            price_per_unit=Decimal("500.0"),
            total_amount=Decimal("500000.0"),
            delivery_date=date.today() + timedelta(days=30),
            status="pending",
            created_by_user_id=sample_users['brand'].id
        )
        db_session.add(brand_po)
        db_session.commit()
        
        # Trader confirms with create_child_pos method
        trader_confirmation = PurchaseOrderConfirmation(
            confirmation_status="confirmed",
            fulfillment_method="create_child_pos",
            notes="Creating child PO to processor for fulfillment"
        )
        
        result = service.confirm_purchase_order(
            po_id=brand_po.id,
            confirmation=trader_confirmation,
            user_id=sample_users['trader'].id
        )
        
        assert result["status"] == "success"
        assert result["child_pos_created"] == 1
        assert result["fulfillment_method"] == "create_child_pos"
        
        # Verify child PO was created
        child_pos = db_session.query(PurchaseOrder).filter(
            PurchaseOrder.parent_po_id == brand_po.id
        ).first()
        
        assert child_pos is not None
        assert child_pos.buyer_company_id == sample_companies['trader'].id
        assert child_pos.seller_company_id == sample_companies['processor'].id
        assert child_pos.po_number == "PO-001-S1"
        assert child_pos.quantity == Decimal("1000.0")
        
        # Verify parent PO status
        db_session.refresh(brand_po)
        assert brand_po.status == "confirmed"
        assert brand_po.fulfillment_notes == "Creating child PO to processor for fulfillment"
    
    def test_fulfill_from_stock_fulfillment(self, db_session: Session, sample_companies, sample_users, sample_product, business_relationships):
        """Test fulfillment from existing inventory."""
        service = POChainingService(db_session)
        
        # Brand creates PO to Trader
        brand_po = PurchaseOrder(
            id=uuid4(),
            po_number="PO-002",
            buyer_company_id=sample_companies['brand'].id,
            seller_company_id=sample_companies['trader'].id,
            product_id=sample_product.id,
            quantity=Decimal("500.0"),
            unit="MT",
            price_per_unit=Decimal("500.0"),
            total_amount=Decimal("250000.0"),
            delivery_date=date.today() + timedelta(days=15),
            status="pending",
            created_by_user_id=sample_users['brand'].id
        )
        db_session.add(brand_po)
        db_session.commit()
        
        # Trader confirms with fulfill_from_stock method
        trader_confirmation = PurchaseOrderConfirmation(
            confirmation_status="confirmed",
            fulfillment_method="fulfill_from_stock",
            notes="Fulfilling from existing inventory - 500MT available"
        )
        
        result = service.confirm_purchase_order(
            po_id=brand_po.id,
            confirmation=trader_confirmation,
            user_id=sample_users['trader'].id
        )
        
        assert result["status"] == "success"
        assert result["child_pos_created"] == 0  # No child POs created
        assert result["fulfillment_method"] == "fulfill_from_stock"
        
        # Verify no child POs were created
        child_pos = db_session.query(PurchaseOrder).filter(
            PurchaseOrder.parent_po_id == brand_po.id
        ).first()
        
        assert child_pos is None
        
        # Verify parent PO status
        db_session.refresh(brand_po)
        assert brand_po.status == "confirmed"
        assert brand_po.fulfillment_notes == "Fulfilling from existing inventory - 500MT available"
    
    def test_partial_stock_partial_po_fulfillment(self, db_session: Session, sample_companies, sample_users, sample_product, business_relationships):
        """Test mixed fulfillment: partial stock + partial new PO."""
        service = POChainingService(db_session)
        
        # Brand creates PO to Trader
        brand_po = PurchaseOrder(
            id=uuid4(),
            po_number="PO-003",
            buyer_company_id=sample_companies['brand'].id,
            seller_company_id=sample_companies['trader'].id,
            product_id=sample_product.id,
            quantity=Decimal("1000.0"),
            unit="MT",
            price_per_unit=Decimal("500.0"),
            total_amount=Decimal("500000.0"),
            delivery_date=date.today() + timedelta(days=25),
            status="pending",
            created_by_user_id=sample_users['brand'].id
        )
        db_session.add(brand_po)
        db_session.commit()
        
        # Trader confirms with partial fulfillment
        trader_confirmation = PurchaseOrderConfirmation(
            confirmation_status="confirmed",
            fulfillment_method="partial_stock_partial_po",
            stock_quantity=Decimal("600.0"),  # 600MT from stock
            po_quantity=Decimal("400.0"),     # 400MT from new PO
            notes="600MT from existing stock, 400MT from new PO to processor"
        )
        
        result = service.confirm_purchase_order(
            po_id=brand_po.id,
            confirmation=trader_confirmation,
            user_id=sample_users['trader'].id
        )
        
        assert result["status"] == "success"
        assert result["child_pos_created"] == 1  # One child PO for the 400MT
        assert result["fulfillment_method"] == "partial_stock_partial_po"
        
        # Verify child PO was created for the PO portion
        child_pos = db_session.query(PurchaseOrder).filter(
            PurchaseOrder.parent_po_id == brand_po.id
        ).first()
        
        assert child_pos is not None
        assert child_pos.quantity == Decimal("400.0")  # Only the PO portion
        
        # Verify parent PO status
        db_session.refresh(brand_po)
        assert brand_po.status == "confirmed"
        assert "600MT from existing stock, 400MT from new PO" in brand_po.fulfillment_notes
    
    def test_fulfillment_method_validation(self, db_session: Session, sample_companies, sample_users, sample_product, business_relationships):
        """Test validation of fulfillment methods and parameters."""
        service = POChainingService(db_session)
        
        # Brand creates PO to Trader
        brand_po = PurchaseOrder(
            id=uuid4(),
            po_number="PO-004",
            buyer_company_id=sample_companies['brand'].id,
            seller_company_id=sample_companies['trader'].id,
            product_id=sample_product.id,
            quantity=Decimal("1000.0"),
            unit="MT",
            price_per_unit=Decimal("500.0"),
            total_amount=Decimal("500000.0"),
            delivery_date=date.today() + timedelta(days=30),
            status="pending",
            created_by_user_id=sample_users['brand'].id
        )
        db_session.add(brand_po)
        db_session.commit()
        
        # Test invalid fulfillment method
        invalid_confirmation = PurchaseOrderConfirmation(
            confirmation_status="confirmed",
            fulfillment_method="invalid_method",
            notes="Testing invalid method"
        )
        
        with pytest.raises(ValueError, match="Invalid fulfillment method"):
            service.confirm_purchase_order(
                po_id=brand_po.id,
                confirmation=invalid_confirmation,
                user_id=sample_users['trader'].id
            )
        
        # Test partial fulfillment without required quantities
        invalid_partial_confirmation = PurchaseOrderConfirmation(
            confirmation_status="confirmed",
            fulfillment_method="partial_stock_partial_po",
            # Missing stock_quantity and po_quantity
            notes="Testing partial without quantities"
        )
        
        with pytest.raises(ValueError, match="stock_quantity and po_quantity required"):
            service.confirm_purchase_order(
                po_id=brand_po.id,
                confirmation=invalid_partial_confirmation,
                user_id=sample_users['trader'].id
            )
    
    def test_quantity_validation_for_partial_fulfillment(self, db_session: Session, sample_companies, sample_users, sample_product, business_relationships):
        """Test quantity validation for partial fulfillment."""
        service = POChainingService(db_session)
        
        # Brand creates PO to Trader
        brand_po = PurchaseOrder(
            id=uuid4(),
            po_number="PO-005",
            buyer_company_id=sample_companies['brand'].id,
            seller_company_id=sample_companies['trader'].id,
            product_id=sample_product.id,
            quantity=Decimal("1000.0"),
            unit="MT",
            price_per_unit=Decimal("500.0"),
            total_amount=Decimal("500000.0"),
            delivery_date=date.today() + timedelta(days=30),
            status="pending",
            created_by_user_id=sample_users['brand'].id
        )
        db_session.add(brand_po)
        db_session.commit()
        
        # Test quantity mismatch
        invalid_quantities_confirmation = PurchaseOrderConfirmation(
            confirmation_status="confirmed",
            fulfillment_method="partial_stock_partial_po",
            stock_quantity=Decimal("600.0"),
            po_quantity=Decimal("500.0"),  # Total = 1100, but PO is only 1000
            notes="Testing quantity mismatch"
        )
        
        with pytest.raises(ValueError, match="Total fulfillment quantity.*does not match PO quantity"):
            service.confirm_purchase_order(
                po_id=brand_po.id,
                confirmation=invalid_quantities_confirmation,
                user_id=sample_users['trader'].id
            )
    
    def test_fulfillment_notes_storage(self, db_session: Session, sample_companies, sample_users, sample_product, business_relationships):
        """Test that fulfillment notes are properly stored."""
        service = POChainingService(db_session)
        
        # Brand creates PO to Trader
        brand_po = PurchaseOrder(
            id=uuid4(),
            po_number="PO-006",
            buyer_company_id=sample_companies['brand'].id,
            seller_company_id=sample_companies['trader'].id,
            product_id=sample_product.id,
            quantity=Decimal("500.0"),
            unit="MT",
            price_per_unit=Decimal("500.0"),
            total_amount=Decimal("250000.0"),
            delivery_date=date.today() + timedelta(days=20),
            status="pending",
            created_by_user_id=sample_users['brand'].id
        )
        db_session.add(brand_po)
        db_session.commit()
        
        # Test different fulfillment methods with notes
        test_cases = [
            {
                "method": "create_child_pos",
                "notes": "Creating PO to processor - expected delivery in 2 weeks",
                "expected_child_pos": 1
            },
            {
                "method": "fulfill_from_stock",
                "notes": "Fulfilling from warehouse stock - batch #WH-2023-001",
                "expected_child_pos": 0
            },
            {
                "method": "partial_stock_partial_po",
                "notes": "300MT from stock, 200MT from new PO to processor",
                "stock_quantity": Decimal("300.0"),
                "po_quantity": Decimal("200.0"),
                "expected_child_pos": 1
            }
        ]
        
        for i, test_case in enumerate(test_cases):
            # Reset PO status
            brand_po.status = "pending"
            brand_po.fulfillment_notes = None
            db_session.commit()
            
            confirmation = PurchaseOrderConfirmation(
                confirmation_status="confirmed",
                fulfillment_method=test_case["method"],
                notes=test_case["notes"]
            )
            
            # Add quantities for partial fulfillment
            if test_case["method"] == "partial_stock_partial_po":
                confirmation.stock_quantity = test_case["stock_quantity"]
                confirmation.po_quantity = test_case["po_quantity"]
            
            result = service.confirm_purchase_order(
                po_id=brand_po.id,
                confirmation=confirmation,
                user_id=sample_users['trader'].id
            )
            
            assert result["status"] == "success"
            assert result["child_pos_created"] == test_case["expected_child_pos"]
            
            # Verify notes were stored
            db_session.refresh(brand_po)
            assert brand_po.fulfillment_notes == test_case["notes"]
    
    def test_fulfillment_status_tracking(self, db_session: Session, sample_companies, sample_users, sample_product, business_relationships):
        """Test fulfillment status tracking for different methods."""
        service = POChainingService(db_session)
        
        # Brand creates PO to Trader
        brand_po = PurchaseOrder(
            id=uuid4(),
            po_number="PO-007",
            buyer_company_id=sample_companies['brand'].id,
            seller_company_id=sample_companies['trader'].id,
            product_id=sample_product.id,
            quantity=Decimal("1000.0"),
            unit="MT",
            price_per_unit=Decimal("500.0"),
            total_amount=Decimal("500000.0"),
            delivery_date=date.today() + timedelta(days=30),
            status="pending",
            created_by_user_id=sample_users['brand'].id
        )
        db_session.add(brand_po)
        db_session.commit()
        
        # Test fulfillment status for create_child_pos
        confirmation1 = PurchaseOrderConfirmation(
            confirmation_status="confirmed",
            fulfillment_method="create_child_pos",
            notes="Creating child PO"
        )
        
        result1 = service.confirm_purchase_order(
            po_id=brand_po.id,
            confirmation=confirmation1,
            user_id=sample_users['trader'].id
        )
        
        assert result1["status"] == "success"
        assert result1["fulfillment_status"] == "child_pos_created"
        
        # Reset for next test
        brand_po.status = "pending"
        db_session.commit()
        
        # Test fulfillment status for fulfill_from_stock
        confirmation2 = PurchaseOrderConfirmation(
            confirmation_status="confirmed",
            fulfillment_method="fulfill_from_stock",
            notes="Fulfilling from stock"
        )
        
        result2 = service.confirm_purchase_order(
            po_id=brand_po.id,
            confirmation=confirmation2,
            user_id=sample_users['trader'].id
        )
        
        assert result2["status"] == "success"
        assert result2["fulfillment_status"] == "fulfilled_from_stock"
    
    def test_trader_scenarios_real_world_examples(self, db_session: Session, sample_companies, sample_users, sample_product, business_relationships):
        """Test real-world trader scenarios with different fulfillment options."""
        service = POChainingService(db_session)
        
        # Scenario 1: Trader with full inventory
        brand_po1 = PurchaseOrder(
            id=uuid4(),
            po_number="PO-008",
            buyer_company_id=sample_companies['brand'].id,
            seller_company_id=sample_companies['trader'].id,
            product_id=sample_product.id,
            quantity=Decimal("500.0"),
            unit="MT",
            price_per_unit=Decimal("500.0"),
            total_amount=Decimal("250000.0"),
            delivery_date=date.today() + timedelta(days=10),
            status="pending",
            created_by_user_id=sample_users['brand'].id
        )
        db_session.add(brand_po1)
        
        # Scenario 2: Trader with no inventory
        brand_po2 = PurchaseOrder(
            id=uuid4(),
            po_number="PO-009",
            buyer_company_id=sample_companies['brand'].id,
            seller_company_id=sample_companies['trader'].id,
            product_id=sample_product.id,
            quantity=Decimal("800.0"),
            unit="MT",
            price_per_unit=Decimal("500.0"),
            total_amount=Decimal("400000.0"),
            delivery_date=date.today() + timedelta(days=20),
            status="pending",
            created_by_user_id=sample_users['brand'].id
        )
        db_session.add(brand_po2)
        
        # Scenario 3: Trader with partial inventory
        brand_po3 = PurchaseOrder(
            id=uuid4(),
            po_number="PO-010",
            buyer_company_id=sample_companies['brand'].id,
            seller_company_id=sample_companies['trader'].id,
            product_id=sample_product.id,
            quantity=Decimal("1000.0"),
            unit="MT",
            price_per_unit=Decimal("500.0"),
            total_amount=Decimal("500000.0"),
            delivery_date=date.today() + timedelta(days=25),
            status="pending",
            created_by_user_id=sample_users['brand'].id
        )
        db_session.add(brand_po3)
        db_session.commit()
        
        # Test Scenario 1: Full inventory fulfillment
        confirmation1 = PurchaseOrderConfirmation(
            confirmation_status="confirmed",
            fulfillment_method="fulfill_from_stock",
            notes="Full inventory available - immediate fulfillment"
        )
        
        result1 = service.confirm_purchase_order(
            po_id=brand_po1.id,
            confirmation=confirmation1,
            user_id=sample_users['trader'].id
        )
        
        assert result1["status"] == "success"
        assert result1["child_pos_created"] == 0
        
        # Test Scenario 2: No inventory - create child PO
        confirmation2 = PurchaseOrderConfirmation(
            confirmation_status="confirmed",
            fulfillment_method="create_child_pos",
            notes="No inventory - creating PO to processor"
        )
        
        result2 = service.confirm_purchase_order(
            po_id=brand_po2.id,
            confirmation=confirmation2,
            user_id=sample_users['trader'].id
        )
        
        assert result2["status"] == "success"
        assert result2["child_pos_created"] == 1
        
        # Test Scenario 3: Partial inventory
        confirmation3 = PurchaseOrderConfirmation(
            confirmation_status="confirmed",
            fulfillment_method="partial_stock_partial_po",
            stock_quantity=Decimal("600.0"),
            po_quantity=Decimal("400.0"),
            notes="600MT from stock, 400MT from new PO"
        )
        
        result3 = service.confirm_purchase_order(
            po_id=brand_po3.id,
            confirmation=confirmation3,
            user_id=sample_users['trader'].id
        )
        
        assert result3["status"] == "success"
        assert result3["child_pos_created"] == 1

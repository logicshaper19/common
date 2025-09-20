"""
Tests for flexible PO chaining system supporting all supply chain flows.
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
SQLALCHEMY_DATABASE_URL = "postgresql://postgres:password@localhost:5432/test_po_chaining"
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
    """Create sample companies for different supply chain tiers."""
    companies = {}
    
    # Brand
    companies['brand'] = Company(
        id=uuid4(),
        name="Global Fashion Brand",
        company_type="brand",
        email="brand@example.com",
        country="USA"
    )
    
    # Trader
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
    
    # Originator
    companies['originator'] = Company(
        id=uuid4(),
        name="Cotton Originator",
        company_type="originator",
        email="originator@example.com",
        country="India"
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
    
    # Processor -> Originator
    rel3 = BusinessRelationship(
        id=uuid4(),
        buyer_company_id=sample_companies['processor'].id,
        seller_company_id=sample_companies['originator'].id,
        relationship_type="supplier",
        is_active=True
    )
    
    # Brand -> Processor (direct relationship)
    rel4 = BusinessRelationship(
        id=uuid4(),
        buyer_company_id=sample_companies['brand'].id,
        seller_company_id=sample_companies['processor'].id,
        relationship_type="supplier",
        is_active=True
    )
    
    # Brand -> Originator (direct relationship)
    rel5 = BusinessRelationship(
        id=uuid4(),
        buyer_company_id=sample_companies['brand'].id,
        seller_company_id=sample_companies['originator'].id,
        relationship_type="supplier",
        is_active=True
    )
    
    relationships = [rel1, rel2, rel3, rel4, rel5]
    
    for rel in relationships:
        db_session.add(rel)
    db_session.commit()
    
    for rel in relationships:
        db_session.refresh(rel)
    
    return relationships


class TestFlexiblePOChaining:
    """Test flexible PO chaining for all supply chain flows."""
    
    def test_brand_to_trader_to_processor_to_originator_flow(self, db_session: Session, sample_companies, sample_users, sample_product, business_relationships):
        """Test 4-step supply chain: Brand → Trader → Processor → Originator."""
        service = POChainingService(db_session)
        
        # Step 1: Brand creates PO to Trader
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
        
        # Step 2: Trader confirms and creates child PO to Processor
        trader_confirmation = PurchaseOrderConfirmation(
            confirmation_status="confirmed",
            fulfillment_method="create_child_pos",
            notes="Creating child PO to processor"
        )
        
        result = service.confirm_purchase_order(
            po_id=brand_po.id,
            confirmation=trader_confirmation,
            user_id=sample_users['trader'].id
        )
        
        assert result["status"] == "success"
        assert result["child_pos_created"] == 1
        
        # Verify child PO was created
        child_pos = db_session.query(PurchaseOrder).filter(
            PurchaseOrder.parent_po_id == brand_po.id
        ).first()
        
        assert child_pos is not None
        assert child_pos.buyer_company_id == sample_companies['trader'].id
        assert child_pos.seller_company_id == sample_companies['processor'].id
        assert child_pos.po_number == "PO-001-S1"
        assert child_pos.quantity == Decimal("1000.0")
        
        # Step 3: Processor confirms and creates child PO to Originator
        processor_confirmation = PurchaseOrderConfirmation(
            confirmation_status="confirmed",
            fulfillment_method="create_child_pos",
            notes="Creating child PO to originator"
        )
        
        result = service.confirm_purchase_order(
            po_id=child_pos.id,
            confirmation=processor_confirmation,
            user_id=sample_users['processor'].id
        )
        
        assert result["status"] == "success"
        assert result["child_pos_created"] == 1
        
        # Verify second child PO was created
        grandchild_pos = db_session.query(PurchaseOrder).filter(
            PurchaseOrder.parent_po_id == child_pos.id
        ).first()
        
        assert grandchild_pos is not None
        assert grandchild_pos.buyer_company_id == sample_companies['processor'].id
        assert grandchild_pos.seller_company_id == sample_companies['originator'].id
        assert grandchild_pos.po_number == "PO-001-S1-S1"
        assert grandchild_pos.quantity == Decimal("1000.0")
        
        # Step 4: Originator confirms (end of chain)
        originator_confirmation = PurchaseOrderConfirmation(
            confirmation_status="confirmed",
            fulfillment_method="fulfill_from_stock",
            notes="Fulfilling from existing stock"
        )
        
        result = service.confirm_purchase_order(
            po_id=grandchild_pos.id,
            confirmation=originator_confirmation,
            user_id=sample_users['originator'].id
        )
        
        assert result["status"] == "success"
        assert result["child_pos_created"] == 0  # End of chain
    
    def test_brand_to_processor_direct_flow(self, db_session: Session, sample_companies, sample_users, sample_product, business_relationships):
        """Test 2-step direct flow: Brand → Processor."""
        service = POChainingService(db_session)
        
        # Brand creates PO directly to Processor
        brand_po = PurchaseOrder(
            id=uuid4(),
            po_number="PO-002",
            buyer_company_id=sample_companies['brand'].id,
            seller_company_id=sample_companies['processor'].id,
            product_id=sample_product.id,
            quantity=Decimal("500.0"),
            unit="MT",
            price_per_unit=Decimal("600.0"),
            total_amount=Decimal("300000.0"),
            delivery_date=date.today() + timedelta(days=20),
            status="pending",
            created_by_user_id=sample_users['brand'].id
        )
        db_session.add(brand_po)
        db_session.commit()
        
        # Processor confirms and creates child PO to Originator
        processor_confirmation = PurchaseOrderConfirmation(
            confirmation_status="confirmed",
            fulfillment_method="create_child_pos",
            notes="Creating child PO to originator"
        )
        
        result = service.confirm_purchase_order(
            po_id=brand_po.id,
            confirmation=processor_confirmation,
            user_id=sample_users['processor'].id
        )
        
        assert result["status"] == "success"
        assert result["child_pos_created"] == 1
        
        # Verify child PO was created
        child_pos = db_session.query(PurchaseOrder).filter(
            PurchaseOrder.parent_po_id == brand_po.id
        ).first()
        
        assert child_pos is not None
        assert child_pos.buyer_company_id == sample_companies['processor'].id
        assert child_pos.seller_company_id == sample_companies['originator'].id
        assert child_pos.po_number == "PO-002-S1"
        assert child_pos.quantity == Decimal("500.0")
    
    def test_brand_to_originator_direct_flow(self, db_session: Session, sample_companies, sample_users, sample_product, business_relationships):
        """Test 1-step direct flow: Brand → Originator."""
        service = POChainingService(db_session)
        
        # Brand creates PO directly to Originator
        brand_po = PurchaseOrder(
            id=uuid4(),
            po_number="PO-003",
            buyer_company_id=sample_companies['brand'].id,
            seller_company_id=sample_companies['originator'].id,
            product_id=sample_product.id,
            quantity=Decimal("200.0"),
            unit="MT",
            price_per_unit=Decimal("700.0"),
            total_amount=Decimal("140000.0"),
            delivery_date=date.today() + timedelta(days=15),
            status="pending",
            created_by_user_id=sample_users['brand'].id
        )
        db_session.add(brand_po)
        db_session.commit()
        
        # Originator confirms (end of chain)
        originator_confirmation = PurchaseOrderConfirmation(
            confirmation_status="confirmed",
            fulfillment_method="fulfill_from_stock",
            notes="Fulfilling from existing stock"
        )
        
        result = service.confirm_purchase_order(
            po_id=brand_po.id,
            confirmation=originator_confirmation,
            user_id=sample_users['originator'].id
        )
        
        assert result["status"] == "success"
        assert result["child_pos_created"] == 0  # End of chain
    
    def test_trader_fan_out_multiple_suppliers(self, db_session: Session, sample_companies, sample_users, sample_product, business_relationships):
        """Test trader fan-out to multiple suppliers."""
        service = POChainingService(db_session)
        
        # Create additional processor for fan-out
        processor2 = Company(
            id=uuid4(),
            name="Textile Processor 2",
            company_type="processor",
            email="processor2@example.com",
            country="Thailand"
        )
        db_session.add(processor2)
        
        # Create relationship
        rel = BusinessRelationship(
            id=uuid4(),
            buyer_company_id=sample_companies['trader'].id,
            seller_company_id=processor2.id,
            relationship_type="supplier",
            is_active=True
        )
        db_session.add(rel)
        db_session.commit()
        
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
        
        # Trader confirms with fan-out
        trader_confirmation = PurchaseOrderConfirmation(
            confirmation_status="confirmed",
            fulfillment_method="create_child_pos",
            notes="Creating child POs to multiple processors",
            # This would be handled by the service logic for fan-out
        )
        
        result = service.confirm_purchase_order(
            po_id=brand_po.id,
            confirmation=trader_confirmation,
            user_id=sample_users['trader'].id
        )
        
        assert result["status"] == "success"
        assert result["child_pos_created"] >= 1
        
        # Verify child POs were created
        child_pos = db_session.query(PurchaseOrder).filter(
            PurchaseOrder.parent_po_id == brand_po.id
        ).all()
        
        assert len(child_pos) >= 1
        assert all(po.buyer_company_id == sample_companies['trader'].id for po in child_pos)
        assert all(po.po_number.startswith("PO-004-S") for po in child_pos)
    
    def test_supply_chain_level_calculation(self, db_session: Session, sample_companies, sample_users, sample_product, business_relationships):
        """Test dynamic supply chain level calculation."""
        service = POChainingService(db_session)
        
        # Test different company types and their levels
        assert service._calculate_supply_chain_level(sample_companies['brand']) == 0  # Brand
        assert service._calculate_supply_chain_level(sample_companies['trader']) == 1  # Trader
        assert service._calculate_supply_chain_level(sample_companies['processor']) == 2  # Processor
        assert service._calculate_supply_chain_level(sample_companies['originator']) == 3  # Originator
    
    def test_smart_po_numbering(self, db_session: Session, sample_companies, sample_users, sample_product, business_relationships):
        """Test smart PO numbering for fan-out scenarios."""
        service = POChainingService(db_session)
        
        # Test PO numbering logic
        parent_po_number = "PO-001"
        
        # First child PO
        child1_number = service._generate_child_po_number(parent_po_number, 1)
        assert child1_number == "PO-001-S1"
        
        # Second child PO
        child2_number = service._generate_child_po_number(parent_po_number, 2)
        assert child2_number == "PO-001-S2"
        
        # Third child PO
        child3_number = service._generate_child_po_number(parent_po_number, 3)
        assert child3_number == "PO-001-S3"
        
        # Nested child PO
        nested_number = service._generate_child_po_number("PO-001-S1", 1)
        assert nested_number == "PO-001-S1-S1"
    
    def test_quantity_splitting_for_multiple_suppliers(self, db_session: Session, sample_companies, sample_users, sample_product, business_relationships):
        """Test quantity splitting when multiple suppliers are involved."""
        service = POChainingService(db_session)
        
        total_quantity = Decimal("1000.0")
        num_suppliers = 3
        
        # Test equal splitting
        split_quantities = service._split_quantity_equally(total_quantity, num_suppliers)
        
        assert len(split_quantities) == 3
        assert all(q == Decimal("333.33") for q in split_quantities[:2])  # First two get 333.33
        assert split_quantities[2] == Decimal("333.34")  # Last one gets 333.34 (to account for rounding)
        assert sum(split_quantities) == total_quantity
    
    def test_flexible_supplier_selection(self, db_session: Session, sample_companies, sample_users, sample_product, business_relationships):
        """Test flexible supplier selection based on relationships."""
        service = POChainingService(db_session)
        
        # Test getting suppliers for different companies
        brand_suppliers = service._get_potential_suppliers(sample_companies['brand'])
        assert len(brand_suppliers) >= 3  # Should have trader, processor, originator
        
        trader_suppliers = service._get_potential_suppliers(sample_companies['trader'])
        assert len(trader_suppliers) >= 2  # Should have processor, originator
        
        processor_suppliers = service._get_potential_suppliers(sample_companies['processor'])
        assert len(processor_suppliers) >= 1  # Should have originator
        
        originator_suppliers = service._get_potential_suppliers(sample_companies['originator'])
        assert len(originator_suppliers) == 0  # Originator has no suppliers
    
    def test_po_chaining_with_different_fulfillment_methods(self, db_session: Session, sample_companies, sample_users, sample_product, business_relationships):
        """Test PO chaining with different fulfillment methods."""
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
        
        # Test different fulfillment methods
        fulfillment_methods = [
            "create_child_pos",
            "fulfill_from_stock", 
            "partial_stock_partial_po"
        ]
        
        for method in fulfillment_methods:
            # Reset PO status
            brand_po.status = "pending"
            db_session.commit()
            
            trader_confirmation = PurchaseOrderConfirmation(
                confirmation_status="confirmed",
                fulfillment_method=method,
                notes=f"Testing {method} fulfillment"
            )
            
            result = service.confirm_purchase_order(
                po_id=brand_po.id,
                confirmation=trader_confirmation,
                user_id=sample_users['trader'].id
            )
            
            assert result["status"] == "success"
            
            if method == "create_child_pos":
                assert result["child_pos_created"] >= 1
            elif method == "fulfill_from_stock":
                assert result["child_pos_created"] == 0
            elif method == "partial_stock_partial_po":
                # This would depend on the specific implementation
                assert result["child_pos_created"] >= 0

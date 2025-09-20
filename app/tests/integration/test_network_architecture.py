"""
Tests for Network/DAG Supply Chain Architecture.
"""
import pytest
from uuid import uuid4
from datetime import datetime, date, timedelta
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.services.network_fulfillment import NetworkFulfillmentService
from app.models.company import Company
from app.models.user import User
from app.models.product import Product
from app.models.purchase_order import PurchaseOrder
from app.models.po_fulfillment_allocation import POFulfillmentAllocation
from app.models.batch import Batch
from app.models.po_batch_linkage import POBatchLinkage
from app.schemas.purchase_order import PurchaseOrderCreate, PurchaseOrderConfirmationation

# Create test database
SQLALCHEMY_DATABASE_URL = "postgresql://postgres:password@localhost:5432/test_network_architecture"
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
    """Create sample companies for network testing."""
    companies = {}
    
    # Brand
    companies['brand'] = Company(
        id=uuid4(),
        name="Global Fashion Brand",
        company_type="brand",
        email="brand@example.com",
        country="USA"
    )
    
    # Trader with commitment inventory
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
    """Create business relationships for network testing."""
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
    
    # Brand -> Processor (direct)
    rel4 = BusinessRelationship(
        id=uuid4(),
        buyer_company_id=sample_companies['brand'].id,
        seller_company_id=sample_companies['processor'].id,
        relationship_type="supplier",
        is_active=True
    )
    
    relationships = [rel1, rel2, rel3, rel4]
    
    for rel in relationships:
        db_session.add(rel)
    db_session.commit()
    
    for rel in relationships:
        db_session.refresh(rel)
    
    return relationships


@pytest.fixture
def sample_batches(db_session: Session, sample_companies, sample_users, sample_product):
    """Create sample batches for inventory testing."""
    batches = []
    
    # Batch 1: Available inventory
    batch1 = Batch(
        id=uuid4(),
        batch_id="INV-001",
        batch_type="harvest",
        company_id=sample_companies['trader'].id,
        product_id=sample_product.id,
        quantity=Decimal("200.0"),
        unit="MT",
        production_date=date.today() - timedelta(days=30),
        expiry_date=date.today() + timedelta(days=365),
        location_name="Trader Warehouse",
        status="active",
        created_by_user_id=sample_users['trader'].id
    )
    
    # Batch 2: Another available inventory
    batch2 = Batch(
        id=uuid4(),
        batch_id="INV-002",
        batch_type="harvest",
        company_id=sample_companies['trader'].id,
        product_id=sample_product.id,
        quantity=Decimal("150.0"),
        unit="MT",
        production_date=date.today() - timedelta(days=15),
        expiry_date=date.today() + timedelta(days=350),
        location_name="Trader Warehouse",
        status="active",
        created_by_user_id=sample_users['trader'].id
    )
    
    batches = [batch1, batch2]
    
    for batch in batches:
        db_session.add(batch)
    db_session.commit()
    
    for batch in batches:
        db_session.refresh(batch)
    
    return batches


class TestNetworkArchitecture:
    """Test Network/DAG Supply Chain Architecture."""
    
    def test_po_state_management(self, db_session: Session, sample_companies, sample_users, sample_product, business_relationships):
        """Test PO state management (OPEN, PARTIALLY_FULFILLED, FULFILLED, CLOSED)."""
        service = NetworkFulfillmentService(db_session)
        
        # Create initial PO
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
            po_state="OPEN",
            fulfilled_quantity=Decimal("0.0"),
            created_by_user_id=sample_users['brand'].id
        )
        db_session.add(brand_po)
        db_session.commit()
        
        # Test initial state
        assert brand_po.po_state == "OPEN"
        assert brand_po.fulfilled_quantity == Decimal("0.0")
        
        # Test partial fulfillment
        brand_po.fulfilled_quantity = Decimal("300.0")
        brand_po.po_state = "PARTIALLY_FULFILLED"
        db_session.commit()
        
        assert brand_po.po_state == "PARTIALLY_FULFILLED"
        assert brand_po.fulfilled_quantity == Decimal("300.0")
        
        # Test full fulfillment
        brand_po.fulfilled_quantity = Decimal("1000.0")
        brand_po.po_state = "FULFILLED"
        db_session.commit()
        
        assert brand_po.po_state == "FULFILLED"
        assert brand_po.fulfilled_quantity == Decimal("1000.0")
        
        # Test closing
        brand_po.po_state = "CLOSED"
        db_session.commit()
        
        assert brand_po.po_state == "CLOSED"
    
    def test_commitment_inventory_system(self, db_session: Session, sample_companies, sample_users, sample_product, business_relationships):
        """Test commitment inventory system (unfulfilled POs as inventory)."""
        service = NetworkFulfillmentService(db_session)
        
        # Create unfulfilled PO (commitment inventory)
        commitment_po = PurchaseOrder(
            id=uuid4(),
            po_number="PO-COMMIT-001",
            buyer_company_id=sample_companies['trader'].id,
            seller_company_id=sample_companies['processor'].id,
            product_id=sample_product.id,
            quantity=Decimal("500.0"),
            unit="MT",
            price_per_unit=Decimal("400.0"),
            total_amount=Decimal("200000.0"),
            delivery_date=date.today() + timedelta(days=20),
            status="confirmed",
            po_state="OPEN",
            fulfilled_quantity=Decimal("0.0"),
            created_by_user_id=sample_users['trader'].id
        )
        db_session.add(commitment_po)
        db_session.commit()
        
        # Test commitment inventory query
        commitment_inventory = service.get_commitment_inventory(sample_companies['trader'].id)
        
        assert len(commitment_inventory) == 1
        assert commitment_inventory[0]["po_id"] == str(commitment_po.id)
        assert commitment_inventory[0]["available_quantity"] == Decimal("500.0")
        assert commitment_inventory[0]["po_state"] == "OPEN"
    
    def test_po_allocation_system(self, db_session: Session, sample_companies, sample_users, sample_product, business_relationships):
        """Test PO allocation system (linking POs to other POs)."""
        service = NetworkFulfillmentService(db_session)
        
        # Create parent PO
        parent_po = PurchaseOrder(
            id=uuid4(),
            po_number="PO-PARENT-001",
            buyer_company_id=sample_companies['brand'].id,
            seller_company_id=sample_companies['trader'].id,
            product_id=sample_product.id,
            quantity=Decimal("1000.0"),
            unit="MT",
            price_per_unit=Decimal("500.0"),
            total_amount=Decimal("500000.0"),
            delivery_date=date.today() + timedelta(days=30),
            status="confirmed",
            po_state="OPEN",
            fulfilled_quantity=Decimal("0.0"),
            created_by_user_id=sample_users['brand'].id
        )
        db_session.add(parent_po)
        
        # Create child PO
        child_po = PurchaseOrder(
            id=uuid4(),
            po_number="PO-CHILD-001",
            buyer_company_id=sample_companies['trader'].id,
            seller_company_id=sample_companies['processor'].id,
            product_id=sample_product.id,
            quantity=Decimal("1000.0"),
            unit="MT",
            price_per_unit=Decimal("400.0"),
            total_amount=Decimal("400000.0"),
            delivery_date=date.today() + timedelta(days=25),
            status="confirmed",
            po_state="OPEN",
            fulfilled_quantity=Decimal("0.0"),
            parent_po_id=parent_po.id,
            created_by_user_id=sample_users['trader'].id
        )
        db_session.add(child_po)
        db_session.commit()
        
        # Create PO allocation
        allocation = POFulfillmentAllocation(
            id=uuid4(),
            parent_po_id=parent_po.id,
            child_po_id=child_po.id,
            allocated_quantity=Decimal("1000.0"),
            allocation_reason="commitment_fulfillment",
            created_by_user_id=sample_users['trader'].id
        )
        db_session.add(allocation)
        db_session.commit()
        
        # Test allocation query
        allocations = service.get_po_allocations(parent_po.id)
        
        assert len(allocations) == 1
        assert allocations[0]["child_po_id"] == str(child_po.id)
        assert allocations[0]["allocated_quantity"] == Decimal("1000.0")
        assert allocations[0]["allocation_reason"] == "commitment_fulfillment"
    
    def test_commitment_fulfillment(self, db_session: Session, sample_companies, sample_users, sample_product, business_relationships):
        """Test fulfillment from existing unfulfilled POs (commitment inventory)."""
        service = NetworkFulfillmentService(db_session)
        
        # Create commitment PO
        commitment_po = PurchaseOrder(
            id=uuid4(),
            po_number="PO-COMMIT-002",
            buyer_company_id=sample_companies['trader'].id,
            seller_company_id=sample_companies['processor'].id,
            product_id=sample_product.id,
            quantity=Decimal("600.0"),
            unit="MT",
            price_per_unit=Decimal("400.0"),
            total_amount=Decimal("240000.0"),
            delivery_date=date.today() + timedelta(days=20),
            status="confirmed",
            po_state="OPEN",
            fulfilled_quantity=Decimal("0.0"),
            created_by_user_id=sample_users['trader'].id
        )
        db_session.add(commitment_po)
        
        # Create new PO to fulfill
        new_po = PurchaseOrder(
            id=uuid4(),
            po_number="PO-NEW-001",
            buyer_company_id=sample_companies['brand'].id,
            seller_company_id=sample_companies['trader'].id,
            product_id=sample_product.id,
            quantity=Decimal("300.0"),
            unit="MT",
            price_per_unit=Decimal("500.0"),
            total_amount=Decimal("150000.0"),
            delivery_date=date.today() + timedelta(days=15),
            status="pending",
            po_state="OPEN",
            fulfilled_quantity=Decimal("0.0"),
            created_by_user_id=sample_users['brand'].id
        )
        db_session.add(new_po)
        db_session.commit()
        
        # Test commitment fulfillment
        result = service.fulfill_from_commitment(
            po_id=new_po.id,
            commitment_po_id=commitment_po.id,
            quantity=Decimal("300.0"),
            user_id=sample_users['trader'].id
        )
        
        assert result["status"] == "success"
        assert result["fulfillment_method"] == "commitment"
        assert result["allocated_quantity"] == Decimal("300.0")
        
        # Verify allocation was created
        allocation = db_session.query(POFulfillmentAllocation).filter(
            POFulfillmentAllocation.parent_po_id == new_po.id,
            POFulfillmentAllocation.child_po_id == commitment_po.id
        ).first()
        
        assert allocation is not None
        assert allocation.allocated_quantity == Decimal("300.0")
        assert allocation.allocation_reason == "commitment_fulfillment"
    
    def test_inventory_fulfillment(self, db_session: Session, sample_companies, sample_users, sample_product, business_relationships, sample_batches):
        """Test fulfillment from existing physical batches."""
        service = NetworkFulfillmentService(db_session)
        
        # Create new PO to fulfill
        new_po = PurchaseOrder(
            id=uuid4(),
            po_number="PO-INV-001",
            buyer_company_id=sample_companies['brand'].id,
            seller_company_id=sample_companies['trader'].id,
            product_id=sample_product.id,
            quantity=Decimal("250.0"),
            unit="MT",
            price_per_unit=Decimal("500.0"),
            total_amount=Decimal("125000.0"),
            delivery_date=date.today() + timedelta(days=10),
            status="pending",
            po_state="OPEN",
            fulfilled_quantity=Decimal("0.0"),
            created_by_user_id=sample_users['brand'].id
        )
        db_session.add(new_po)
        db_session.commit()
        
        # Test inventory fulfillment
        result = service.fulfill_from_inventory(
            po_id=new_po.id,
            batch_id=sample_batches[0].id,
            quantity=Decimal("200.0"),
            user_id=sample_users['trader'].id
        )
        
        assert result["status"] == "success"
        assert result["fulfillment_method"] == "inventory"
        assert result["allocated_quantity"] == Decimal("200.0")
        
        # Verify PO-Batch linkage was created
        linkage = db_session.query(POBatchLinkage).filter(
            POBatchLinkage.purchase_order_id == new_po.id,
            POBatchLinkage.batch_id == sample_batches[0].id
        ).first()
        
        assert linkage is not None
        assert linkage.quantity_allocated == Decimal("200.0")
        assert linkage.allocation_reason == "inventory_fulfillment"
    
    def test_chain_fulfillment(self, db_session: Session, sample_companies, sample_users, sample_product, business_relationships):
        """Test fulfillment by creating new PO chains to suppliers."""
        service = NetworkFulfillmentService(db_session)
        
        # Create new PO to fulfill
        new_po = PurchaseOrder(
            id=uuid4(),
            po_number="PO-CHAIN-001",
            buyer_company_id=sample_companies['brand'].id,
            seller_company_id=sample_companies['trader'].id,
            product_id=sample_product.id,
            quantity=Decimal("400.0"),
            unit="MT",
            price_per_unit=Decimal("500.0"),
            total_amount=Decimal("200000.0"),
            delivery_date=date.today() + timedelta(days=20),
            status="pending",
            po_state="OPEN",
            fulfilled_quantity=Decimal("0.0"),
            created_by_user_id=sample_users['brand'].id
        )
        db_session.add(new_po)
        db_session.commit()
        
        # Test chain fulfillment
        result = service.fulfill_from_chain(
            po_id=new_po.id,
            supplier_company_id=sample_companies['processor'].id,
            quantity=Decimal("400.0"),
            user_id=sample_users['trader'].id
        )
        
        assert result["status"] == "success"
        assert result["fulfillment_method"] == "chain"
        assert result["child_pos_created"] == 1
        
        # Verify child PO was created
        child_po = db_session.query(PurchaseOrder).filter(
            PurchaseOrder.parent_po_id == new_po.id
        ).first()
        
        assert child_po is not None
        assert child_po.buyer_company_id == sample_companies['trader'].id
        assert child_po.seller_company_id == sample_companies['processor'].id
        assert child_po.quantity == Decimal("400.0")
    
    def test_mixed_fulfillment_strategy(self, db_session: Session, sample_companies, sample_users, sample_product, business_relationships, sample_batches):
        """Test mixed fulfillment strategy using multiple methods."""
        service = NetworkFulfillmentService(db_session)
        
        # Create commitment PO
        commitment_po = PurchaseOrder(
            id=uuid4(),
            po_number="PO-COMMIT-003",
            buyer_company_id=sample_companies['trader'].id,
            seller_company_id=sample_companies['processor'].id,
            product_id=sample_product.id,
            quantity=Decimal("300.0"),
            unit="MT",
            price_per_unit=Decimal("400.0"),
            total_amount=Decimal("120000.0"),
            delivery_date=date.today() + timedelta(days=20),
            status="confirmed",
            po_state="OPEN",
            fulfilled_quantity=Decimal("0.0"),
            created_by_user_id=sample_users['trader'].id
        )
        db_session.add(commitment_po)
        
        # Create new PO to fulfill
        new_po = PurchaseOrder(
            id=uuid4(),
            po_number="PO-MIXED-001",
            buyer_company_id=sample_companies['brand'].id,
            seller_company_id=sample_companies['trader'].id,
            product_id=sample_product.id,
            quantity=Decimal("500.0"),
            unit="MT",
            price_per_unit=Decimal("500.0"),
            total_amount=Decimal("250000.0"),
            delivery_date=date.today() + timedelta(days=15),
            status="pending",
            po_state="OPEN",
            fulfilled_quantity=Decimal("0.0"),
            created_by_user_id=sample_users['brand'].id
        )
        db_session.add(new_po)
        db_session.commit()
        
        # Test mixed fulfillment strategy
        fulfillment_plan = {
            "commitment": {
                "po_id": commitment_po.id,
                "quantity": Decimal("200.0")
            },
            "inventory": {
                "batch_id": sample_batches[0].id,
                "quantity": Decimal("150.0")
            },
            "chain": {
                "supplier_company_id": sample_companies['processor'].id,
                "quantity": Decimal("150.0")
            }
        }
        
        result = service.execute_mixed_fulfillment(
            po_id=new_po.id,
            fulfillment_plan=fulfillment_plan,
            user_id=sample_users['trader'].id
        )
        
        assert result["status"] == "success"
        assert result["total_allocated"] == Decimal("500.0")
        assert result["commitment_allocated"] == Decimal("200.0")
        assert result["inventory_allocated"] == Decimal("150.0")
        assert result["chain_allocated"] == Decimal("150.0")
        
        # Verify all allocations were created
        commitment_allocation = db_session.query(POFulfillmentAllocation).filter(
            POFulfillmentAllocation.parent_po_id == new_po.id,
            POFulfillmentAllocation.child_po_id == commitment_po.id
        ).first()
        assert commitment_allocation is not None
        assert commitment_allocation.allocated_quantity == Decimal("200.0")
        
        inventory_linkage = db_session.query(POBatchLinkage).filter(
            POBatchLinkage.purchase_order_id == new_po.id,
            POBatchLinkage.batch_id == sample_batches[0].id
        ).first()
        assert inventory_linkage is not None
        assert inventory_linkage.quantity_allocated == Decimal("150.0")
        
        chain_po = db_session.query(PurchaseOrder).filter(
            PurchaseOrder.parent_po_id == new_po.id
        ).first()
        assert chain_po is not None
        assert chain_po.quantity == Decimal("150.0")
    
    def test_network_traversal(self, db_session: Session, sample_companies, sample_users, sample_product, business_relationships):
        """Test network traversal for finding fulfillment paths."""
        service = NetworkFulfillmentService(db_session)
        
        # Create a network of POs
        po1 = PurchaseOrder(
            id=uuid4(),
            po_number="PO-NET-001",
            buyer_company_id=sample_companies['brand'].id,
            seller_company_id=sample_companies['trader'].id,
            product_id=sample_product.id,
            quantity=Decimal("1000.0"),
            unit="MT",
            price_per_unit=Decimal("500.0"),
            total_amount=Decimal("500000.0"),
            delivery_date=date.today() + timedelta(days=30),
            status="confirmed",
            po_state="OPEN",
            fulfilled_quantity=Decimal("0.0"),
            created_by_user_id=sample_users['brand'].id
        )
        
        po2 = PurchaseOrder(
            id=uuid4(),
            po_number="PO-NET-002",
            buyer_company_id=sample_companies['trader'].id,
            seller_company_id=sample_companies['processor'].id,
            product_id=sample_product.id,
            quantity=Decimal("1000.0"),
            unit="MT",
            price_per_unit=Decimal("400.0"),
            total_amount=Decimal("400000.0"),
            delivery_date=date.today() + timedelta(days=25),
            status="confirmed",
            po_state="OPEN",
            fulfilled_quantity=Decimal("0.0"),
            parent_po_id=po1.id,
            created_by_user_id=sample_users['trader'].id
        )
        
        po3 = PurchaseOrder(
            id=uuid4(),
            po_number="PO-NET-003",
            buyer_company_id=sample_companies['processor'].id,
            seller_company_id=sample_companies['originator'].id,
            product_id=sample_product.id,
            quantity=Decimal("1000.0"),
            unit="MT",
            price_per_unit=Decimal("300.0"),
            total_amount=Decimal("300000.0"),
            delivery_date=date.today() + timedelta(days=20),
            status="confirmed",
            po_state="OPEN",
            fulfilled_quantity=Decimal("0.0"),
            parent_po_id=po2.id,
            created_by_user_id=sample_users['processor'].id
        )
        
        db_session.add_all([po1, po2, po3])
        db_session.commit()
        
        # Test network traversal
        network_path = service.traverse_network(po1.id)
        
        assert len(network_path) == 3
        assert network_path[0]["po_id"] == str(po1.id)
        assert network_path[1]["po_id"] == str(po2.id)
        assert network_path[2]["po_id"] == str(po3.id)
        
        # Test finding available capacity
        available_capacity = service.get_available_capacity(sample_companies['trader'].id)
        
        assert available_capacity["commitment_inventory"] >= 0
        assert available_capacity["physical_inventory"] >= 0
        assert available_capacity["total_capacity"] >= 0
    
    def test_dag_structure_support(self, db_session: Session, sample_companies, sample_users, sample_product, business_relationships):
        """Test DAG structure support for complex supply chains."""
        service = NetworkFulfillmentService(db_session)
        
        # Create a DAG structure: Brand -> Trader -> [Processor1, Processor2] -> Originator
        # This creates a fan-out and fan-in pattern
        
        # Brand PO
        brand_po = PurchaseOrder(
            id=uuid4(),
            po_number="PO-DAG-001",
            buyer_company_id=sample_companies['brand'].id,
            seller_company_id=sample_companies['trader'].id,
            product_id=sample_product.id,
            quantity=Decimal("1000.0"),
            unit="MT",
            price_per_unit=Decimal("500.0"),
            total_amount=Decimal("500000.0"),
            delivery_date=date.today() + timedelta(days=30),
            status="confirmed",
            po_state="OPEN",
            fulfilled_quantity=Decimal("0.0"),
            created_by_user_id=sample_users['brand'].id
        )
        db_session.add(brand_po)
        
        # Create additional processor for DAG
        processor2 = Company(
            id=uuid4(),
            name="Textile Processor 2",
            company_type="processor",
            email="processor2@example.com",
            country="Thailand"
        )
        db_session.add(processor2)
        
        # Create relationships for DAG
        rel1 = BusinessRelationship(
            id=uuid4(),
            buyer_company_id=sample_companies['trader'].id,
            seller_company_id=sample_companies['processor'].id,
            relationship_type="supplier",
            is_active=True
        )
        rel2 = BusinessRelationship(
            id=uuid4(),
            buyer_company_id=sample_companies['trader'].id,
            seller_company_id=processor2.id,
            relationship_type="supplier",
            is_active=True
        )
        rel3 = BusinessRelationship(
            id=uuid4(),
            buyer_company_id=sample_companies['processor'].id,
            seller_company_id=sample_companies['originator'].id,
            relationship_type="supplier",
            is_active=True
        )
        rel4 = BusinessRelationship(
            id=uuid4(),
            buyer_company_id=processor2.id,
            seller_company_id=sample_companies['originator'].id,
            relationship_type="supplier",
            is_active=True
        )
        
        db_session.add_all([rel1, rel2, rel3, rel4])
        db_session.commit()
        
        # Test DAG structure validation
        dag_structure = service.validate_dag_structure(brand_po.id)
        
        assert dag_structure["is_valid_dag"] is True
        assert dag_structure["max_depth"] >= 2
        assert len(dag_structure["nodes"]) >= 4  # Brand, Trader, 2 Processors, Originator
        assert len(dag_structure["edges"]) >= 5  # Multiple relationships
        
        # Test cycle detection
        has_cycles = service.detect_cycles(brand_po.id)
        assert has_cycles is False  # Should be a valid DAG without cycles

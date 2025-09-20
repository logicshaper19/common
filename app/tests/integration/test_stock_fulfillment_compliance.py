"""
Tests for stock fulfillment compliance and traceability system.
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
from app.models.batch import Batch
from app.models.po_batch_linkage import POBatchLinkage
from app.schemas.purchase_order import PurchaseOrderCreate, PurchaseOrderConfirmationation

# Create test database
SQLALCHEMY_DATABASE_URL = "postgresql://postgres:password@localhost:5432/test_stock_fulfillment"
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
def sample_batches(db_session: Session, sample_companies, sample_users, sample_product):
    """Create sample batches for stock fulfillment testing."""
    batches = []
    
    # Batch 1: Available stock
    batch1 = Batch(
        id=uuid4(),
        batch_id="BATCH-001",
        batch_type="harvest",
        company_id=sample_companies['trader'].id,
        product_id=sample_product.id,
        quantity=Decimal("500.0"),
        unit="MT",
        production_date=date.today() - timedelta(days=30),
        expiry_date=date.today() + timedelta(days=365),
        location_name="Trader Warehouse Alpha",
        status="active",
        created_by_user_id=sample_users['trader'].id,
        batch_metadata={
            "origin": "Malaysia",
            "certification": "RSPO",
            "quality_grade": "A"
        }
    )
    
    # Batch 2: Another available stock
    batch2 = Batch(
        id=uuid4(),
        batch_id="BATCH-002",
        batch_type="harvest",
        company_id=sample_companies['trader'].id,
        product_id=sample_product.id,
        quantity=Decimal("300.0"),
        unit="MT",
        production_date=date.today() - timedelta(days=15),
        expiry_date=date.today() + timedelta(days=350),
        location_name="Trader Warehouse Beta",
        status="active",
        created_by_user_id=sample_users['trader'].id,
        batch_metadata={
            "origin": "Indonesia",
            "certification": "Organic",
            "quality_grade": "A+"
        }
    )
    
    # Batch 3: Insufficient quantity
    batch3 = Batch(
        id=uuid4(),
        batch_id="BATCH-003",
        batch_type="harvest",
        company_id=sample_companies['trader'].id,
        product_id=sample_product.id,
        quantity=Decimal("100.0"),
        unit="MT",
        production_date=date.today() - timedelta(days=10),
        expiry_date=date.today() + timedelta(days=360),
        location_name="Trader Warehouse Gamma",
        status="active",
        created_by_user_id=sample_users['trader'].id,
        batch_metadata={
            "origin": "Thailand",
            "certification": "Fair Trade",
            "quality_grade": "B"
        }
    )
    
    batches = [batch1, batch2, batch3]
    
    for batch in batches:
        db_session.add(batch)
    db_session.commit()
    
    for batch in batches:
        db_session.refresh(batch)
    
    return batches


@pytest.fixture
def business_relationship(db_session: Session, sample_companies):
    """Create business relationship between companies."""
    relationship = BusinessRelationship(
        id=uuid4(),
        buyer_company_id=sample_companies['brand'].id,
        seller_company_id=sample_companies['trader'].id,
        relationship_type="supplier",
        is_active=True
    )
    
    db_session.add(relationship)
    db_session.commit()
    db_session.refresh(relationship)
    
    return relationship


class TestStockFulfillmentCompliance:
    """Test stock fulfillment compliance and traceability."""
    
    def test_stock_fulfillment_with_single_batch(self, db_session: Session, sample_companies, sample_users, sample_product, sample_batches, business_relationship):
        """Test stock fulfillment using a single batch."""
        service = POChainingService(db_session)
        
        # Brand creates PO to Trader
        brand_po = PurchaseOrder(
            id=uuid4(),
            po_number="PO-001",
            buyer_company_id=sample_companies['brand'].id,
            seller_company_id=sample_companies['trader'].id,
            product_id=sample_product.id,
            quantity=Decimal("400.0"),
            unit="MT",
            price_per_unit=Decimal("500.0"),
            total_amount=Decimal("200000.0"),
            delivery_date=date.today() + timedelta(days=15),
            status="pending",
            created_by_user_id=sample_users['brand'].id
        )
        db_session.add(brand_po)
        db_session.commit()
        
        # Trader confirms with stock fulfillment
        stock_batches = [
            {
                "batch_id": str(sample_batches[0].id),
                "quantity_used": 400.0,
                "allocation_reason": "stock_fulfillment",
                "compliance_notes": "Fulfilling from BATCH-001 - RSPO certified Malaysian cotton"
            }
        ]
        
        trader_confirmation = PurchaseOrderConfirmation(
            confirmation_status="confirmed",
            fulfillment_method="fulfill_from_stock",
            stock_batches=stock_batches,
            notes="Fulfilling from existing inventory - BATCH-001"
        )
        
        result = service.confirm_purchase_order(
            po_id=brand_po.id,
            confirmation=trader_confirmation,
            user_id=sample_users['trader'].id
        )
        
        assert result["status"] == "success"
        assert result["child_pos_created"] == 0
        assert result["fulfillment_method"] == "fulfill_from_stock"
        
        # Verify PO-Batch linkage was created
        linkage = db_session.query(POBatchLinkage).filter(
            POBatchLinkage.purchase_order_id == brand_po.id
        ).first()
        
        assert linkage is not None
        assert linkage.batch_id == sample_batches[0].id
        assert linkage.quantity_allocated == Decimal("400.0")
        assert linkage.allocation_reason == "stock_fulfillment"
        assert "RSPO certified Malaysian cotton" in linkage.compliance_notes
        
        # Verify PO status
        db_session.refresh(brand_po)
        assert brand_po.status == "confirmed"
        assert "BATCH-001" in brand_po.fulfillment_notes
    
    def test_stock_fulfillment_with_multiple_batches(self, db_session: Session, sample_companies, sample_users, sample_product, sample_batches, business_relationship):
        """Test stock fulfillment using multiple batches."""
        service = POChainingService(db_session)
        
        # Brand creates PO to Trader
        brand_po = PurchaseOrder(
            id=uuid4(),
            po_number="PO-002",
            buyer_company_id=sample_companies['brand'].id,
            seller_company_id=sample_companies['trader'].id,
            product_id=sample_product.id,
            quantity=Decimal("700.0"),  # Requires multiple batches
            unit="MT",
            price_per_unit=Decimal("500.0"),
            total_amount=Decimal("350000.0"),
            delivery_date=date.today() + timedelta(days=20),
            status="pending",
            created_by_user_id=sample_users['brand'].id
        )
        db_session.add(brand_po)
        db_session.commit()
        
        # Trader confirms with multiple batch fulfillment
        stock_batches = [
            {
                "batch_id": str(sample_batches[0].id),
                "quantity_used": 500.0,
                "allocation_reason": "stock_fulfillment",
                "compliance_notes": "Primary batch - BATCH-001 (RSPO certified)"
            },
            {
                "batch_id": str(sample_batches[1].id),
                "quantity_used": 200.0,
                "allocation_reason": "stock_fulfillment",
                "compliance_notes": "Secondary batch - BATCH-002 (Organic certified)"
            }
        ]
        
        trader_confirmation = PurchaseOrderConfirmation(
            confirmation_status="confirmed",
            fulfillment_method="fulfill_from_stock",
            stock_batches=stock_batches,
            notes="Fulfilling from multiple batches - BATCH-001 (500MT) + BATCH-002 (200MT)"
        )
        
        result = service.confirm_purchase_order(
            po_id=brand_po.id,
            confirmation=trader_confirmation,
            user_id=sample_users['trader'].id
        )
        
        assert result["status"] == "success"
        assert result["child_pos_created"] == 0
        
        # Verify multiple PO-Batch linkages were created
        linkages = db_session.query(POBatchLinkage).filter(
            POBatchLinkage.purchase_order_id == brand_po.id
        ).all()
        
        assert len(linkages) == 2
        
        # Verify first linkage
        linkage1 = next(l for l in linkages if l.batch_id == sample_batches[0].id)
        assert linkage1.quantity_allocated == Decimal("500.0")
        assert "RSPO certified" in linkage1.compliance_notes
        
        # Verify second linkage
        linkage2 = next(l for l in linkages if l.batch_id == sample_batches[1].id)
        assert linkage2.quantity_allocated == Decimal("200.0")
        assert "Organic certified" in linkage2.compliance_notes
    
    def test_batch_ownership_validation(self, db_session: Session, sample_companies, sample_users, sample_product, sample_batches, business_relationship):
        """Test validation that batches belong to the confirming company."""
        service = POChainingService(db_session)
        
        # Brand creates PO to Trader
        brand_po = PurchaseOrder(
            id=uuid4(),
            po_number="PO-003",
            buyer_company_id=sample_companies['brand'].id,
            seller_company_id=sample_companies['trader'].id,
            product_id=sample_product.id,
            quantity=Decimal("100.0"),
            unit="MT",
            price_per_unit=Decimal("500.0"),
            total_amount=Decimal("50000.0"),
            delivery_date=date.today() + timedelta(days=10),
            status="pending",
            created_by_user_id=sample_users['brand'].id
        )
        db_session.add(brand_po)
        db_session.commit()
        
        # Create a batch that doesn't belong to the trader
        other_company = Company(
            id=uuid4(),
            name="Other Company",
            company_type="processor",
            email="other@example.com",
            country="Malaysia"
        )
        db_session.add(other_company)
        db_session.commit()
        
        other_batch = Batch(
            id=uuid4(),
            batch_id="OTHER-BATCH-001",
            batch_type="harvest",
            company_id=other_company.id,  # Different company
            product_id=sample_product.id,
            quantity=Decimal("100.0"),
            unit="MT",
            production_date=date.today() - timedelta(days=5),
            status="active",
            created_by_user_id=sample_users['trader'].id
        )
        db_session.add(other_batch)
        db_session.commit()
        
        # Try to fulfill using batch from different company
        stock_batches = [
            {
                "batch_id": str(other_batch.id),
                "quantity_used": 100.0,
                "allocation_reason": "stock_fulfillment",
                "compliance_notes": "Using other company's batch"
            }
        ]
        
        trader_confirmation = PurchaseOrderConfirmation(
            confirmation_status="confirmed",
            fulfillment_method="fulfill_from_stock",
            stock_batches=stock_batches,
            notes="Trying to use other company's batch"
        )
        
        with pytest.raises(ValueError, match="does not belong to company"):
            service.confirm_purchase_order(
                po_id=brand_po.id,
                confirmation=trader_confirmation,
                user_id=sample_users['trader'].id
            )
    
    def test_batch_quantity_validation(self, db_session: Session, sample_companies, sample_users, sample_product, sample_batches, business_relationship):
        """Test validation that batch has sufficient quantity."""
        service = POChainingService(db_session)
        
        # Brand creates PO to Trader
        brand_po = PurchaseOrder(
            id=uuid4(),
            po_number="PO-004",
            buyer_company_id=sample_companies['brand'].id,
            seller_company_id=sample_companies['trader'].id,
            product_id=sample_product.id,
            quantity=Decimal("200.0"),  # More than available in batch
            unit="MT",
            price_per_unit=Decimal("500.0"),
            total_amount=Decimal("100000.0"),
            delivery_date=date.today() + timedelta(days=10),
            status="pending",
            created_by_user_id=sample_users['brand'].id
        )
        db_session.add(brand_po)
        db_session.commit()
        
        # Try to fulfill using batch with insufficient quantity
        stock_batches = [
            {
                "batch_id": str(sample_batches[2].id),  # Only 100MT available
                "quantity_used": 200.0,  # Requesting 200MT
                "allocation_reason": "stock_fulfillment",
                "compliance_notes": "Insufficient quantity test"
            }
        ]
        
        trader_confirmation = PurchaseOrderConfirmation(
            confirmation_status="confirmed",
            fulfillment_method="fulfill_from_stock",
            stock_batches=stock_batches,
            notes="Trying to use insufficient quantity"
        )
        
        with pytest.raises(ValueError, match="insufficient quantity"):
            service.confirm_purchase_order(
                po_id=brand_po.id,
                confirmation=trader_confirmation,
                user_id=sample_users['trader'].id
            )
    
    def test_quantity_matching_validation(self, db_session: Session, sample_companies, sample_users, sample_product, sample_batches, business_relationship):
        """Test validation that total batch quantities match PO quantity."""
        service = POChainingService(db_session)
        
        # Brand creates PO to Trader
        brand_po = PurchaseOrder(
            id=uuid4(),
            po_number="PO-005",
            buyer_company_id=sample_companies['brand'].id,
            seller_company_id=sample_companies['trader'].id,
            product_id=sample_product.id,
            quantity=Decimal("600.0"),
            unit="MT",
            price_per_unit=Decimal("500.0"),
            total_amount=Decimal("300000.0"),
            delivery_date=date.today() + timedelta(days=15),
            status="pending",
            created_by_user_id=sample_users['brand'].id
        )
        db_session.add(brand_po)
        db_session.commit()
        
        # Try to fulfill with mismatched quantities
        stock_batches = [
            {
                "batch_id": str(sample_batches[0].id),
                "quantity_used": 500.0,
                "allocation_reason": "stock_fulfillment",
                "compliance_notes": "First batch"
            },
            {
                "batch_id": str(sample_batches[1].id),
                "quantity_used": 50.0,  # Total = 550, but PO is 600
                "allocation_reason": "stock_fulfillment",
                "compliance_notes": "Second batch"
            }
        ]
        
        trader_confirmation = PurchaseOrderConfirmation(
            confirmation_status="confirmed",
            fulfillment_method="fulfill_from_stock",
            stock_batches=stock_batches,
            notes="Testing quantity mismatch"
        )
        
        with pytest.raises(ValueError, match="Total batch quantities.*do not match PO quantity"):
            service.confirm_purchase_order(
                po_id=brand_po.id,
                confirmation=trader_confirmation,
                user_id=sample_users['trader'].id
            )
    
    def test_audit_trail_for_stock_fulfillment(self, db_session: Session, sample_companies, sample_users, sample_product, sample_batches, business_relationship):
        """Test audit trail creation for stock fulfillment."""
        service = POChainingService(db_session)
        
        # Brand creates PO to Trader
        brand_po = PurchaseOrder(
            id=uuid4(),
            po_number="PO-006",
            buyer_company_id=sample_companies['brand'].id,
            seller_company_id=sample_companies['trader'].id,
            product_id=sample_product.id,
            quantity=Decimal("300.0"),
            unit="MT",
            price_per_unit=Decimal("500.0"),
            total_amount=Decimal("150000.0"),
            delivery_date=date.today() + timedelta(days=12),
            status="pending",
            created_by_user_id=sample_users['brand'].id
        )
        db_session.add(brand_po)
        db_session.commit()
        
        # Trader confirms with stock fulfillment
        stock_batches = [
            {
                "batch_id": str(sample_batches[1].id),
                "quantity_used": 300.0,
                "allocation_reason": "stock_fulfillment",
                "compliance_notes": "Fulfilling from BATCH-002 - Organic certified Indonesian cotton"
            }
        ]
        
        trader_confirmation = PurchaseOrderConfirmation(
            confirmation_status="confirmed",
            fulfillment_method="fulfill_from_stock",
            stock_batches=stock_batches,
            notes="Stock fulfillment with full audit trail"
        )
        
        result = service.confirm_purchase_order(
            po_id=brand_po.id,
            confirmation=trader_confirmation,
            user_id=sample_users['trader'].id
        )
        
        assert result["status"] == "success"
        
        # Verify audit trail in PO-Batch linkage
        linkage = db_session.query(POBatchLinkage).filter(
            POBatchLinkage.purchase_order_id == brand_po.id
        ).first()
        
        assert linkage is not None
        assert linkage.created_at is not None
        assert linkage.created_by_user_id == sample_users['trader'].id
        assert linkage.allocation_reason == "stock_fulfillment"
        assert "Organic certified Indonesian cotton" in linkage.compliance_notes
        
        # Verify PO audit trail
        db_session.refresh(brand_po)
        assert brand_po.status == "confirmed"
        assert brand_po.fulfillment_notes == "Stock fulfillment with full audit trail"
        assert brand_po.updated_at is not None
    
    def test_compliance_documentation_requirements(self, db_session: Session, sample_companies, sample_users, sample_product, sample_batches, business_relationship):
        """Test that compliance documentation is required for stock fulfillment."""
        service = POChainingService(db_session)
        
        # Brand creates PO to Trader
        brand_po = PurchaseOrder(
            id=uuid4(),
            po_number="PO-007",
            buyer_company_id=sample_companies['brand'].id,
            seller_company_id=sample_companies['trader'].id,
            product_id=sample_product.id,
            quantity=Decimal("200.0"),
            unit="MT",
            price_per_unit=Decimal("500.0"),
            total_amount=Decimal("100000.0"),
            delivery_date=date.today() + timedelta(days=8),
            status="pending",
            created_by_user_id=sample_users['brand'].id
        )
        db_session.add(brand_po)
        db_session.commit()
        
        # Test with minimal compliance notes
        stock_batches = [
            {
                "batch_id": str(sample_batches[0].id),
                "quantity_used": 200.0,
                "allocation_reason": "stock_fulfillment",
                "compliance_notes": "Basic compliance info"
            }
        ]
        
        trader_confirmation = PurchaseOrderConfirmation(
            confirmation_status="confirmed",
            fulfillment_method="fulfill_from_stock",
            stock_batches=stock_batches,
            notes="Minimal compliance documentation"
        )
        
        result = service.confirm_purchase_order(
            po_id=brand_po.id,
            confirmation=trader_confirmation,
            user_id=sample_users['trader'].id
        )
        
        assert result["status"] == "success"
        
        # Verify compliance notes were stored
        linkage = db_session.query(POBatchLinkage).filter(
            POBatchLinkage.purchase_order_id == brand_po.id
        ).first()
        
        assert linkage is not None
        assert linkage.compliance_notes == "Basic compliance info"
    
    def test_stock_fulfillment_with_batch_metadata(self, db_session: Session, sample_companies, sample_users, sample_product, sample_batches, business_relationship):
        """Test that batch metadata is preserved in stock fulfillment."""
        service = POChainingService(db_session)
        
        # Brand creates PO to Trader
        brand_po = PurchaseOrder(
            id=uuid4(),
            po_number="PO-008",
            buyer_company_id=sample_companies['brand'].id,
            seller_company_id=sample_companies['trader'].id,
            product_id=sample_product.id,
            quantity=Decimal("250.0"),
            unit="MT",
            price_per_unit=Decimal("500.0"),
            total_amount=Decimal("125000.0"),
            delivery_date=date.today() + timedelta(days=18),
            status="pending",
            created_by_user_id=sample_users['brand'].id
        )
        db_session.add(brand_po)
        db_session.commit()
        
        # Trader confirms with detailed batch metadata
        stock_batches = [
            {
                "batch_id": str(sample_batches[0].id),
                "quantity_used": 250.0,
                "allocation_reason": "stock_fulfillment",
                "compliance_notes": f"Batch metadata: {sample_batches[0].batch_metadata}"
            }
        ]
        
        trader_confirmation = PurchaseOrderConfirmation(
            confirmation_status="confirmed",
            fulfillment_method="fulfill_from_stock",
            stock_batches=stock_batches,
            notes=f"Fulfilling from {sample_batches[0].batch_id} - Quality Grade A, RSPO certified"
        )
        
        result = service.confirm_purchase_order(
            po_id=brand_po.id,
            confirmation=trader_confirmation,
            user_id=sample_users['trader'].id
        )
        
        assert result["status"] == "success"
        
        # Verify batch metadata is accessible
        linkage = db_session.query(POBatchLinkage).filter(
            POBatchLinkage.purchase_order_id == brand_po.id
        ).first()
        
        assert linkage is not None
        assert "RSPO" in linkage.compliance_notes
        assert "Quality Grade A" in linkage.compliance_notes
        
        # Verify batch relationship
        assert linkage.batch.batch_metadata["certification"] == "RSPO"
        assert linkage.batch.batch_metadata["quality_grade"] == "A"
        assert linkage.batch.batch_metadata["origin"] == "Malaysia"

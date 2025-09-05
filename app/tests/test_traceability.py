"""
Tests for traceability calculation system.
"""
import pytest
from decimal import Decimal
from datetime import date, datetime, timedelta
from uuid import uuid4
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.services.traceability import TraceabilityCalculationService
from app.models.company import Company
from app.models.product import Product
from app.models.purchase_order import PurchaseOrder

# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_traceability.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
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
    
    # Create originator company
    companies["originator"] = Company(
        id=uuid4(),
        name="Palm Plantation Co",
        company_type="originator",
        email="plantation@example.com"
    )
    
    # Create processor company
    companies["processor"] = Company(
        id=uuid4(),
        name="Palm Processing Ltd",
        company_type="processor",
        email="processor@example.com"
    )
    
    # Create brand company
    companies["brand"] = Company(
        id=uuid4(),
        name="Consumer Brand Inc",
        company_type="brand",
        email="brand@example.com"
    )
    
    for company in companies.values():
        db_session.add(company)
    
    db_session.commit()
    
    for company in companies.values():
        db_session.refresh(company)
    
    return companies


@pytest.fixture
def sample_products(db_session: Session):
    """Create sample products for testing."""
    products = {}
    
    # Fresh Fruit Bunches (raw material)
    products["ffb"] = Product(
        id=uuid4(),
        common_product_id="FFB-001",
        name="Fresh Fruit Bunches (FFB)",
        description="Fresh palm fruit bunches harvested from oil palm trees",
        category="raw_material",
        can_have_composition=False,
        material_breakdown=None,
        default_unit="KGM",
        hs_code="1207.10.00"
    )
    
    # Crude Palm Oil (processed)
    products["cpo"] = Product(
        id=uuid4(),
        common_product_id="CPO-001",
        name="Crude Palm Oil (CPO)",
        description="Unrefined palm oil extracted from fresh fruit bunches",
        category="processed",
        can_have_composition=True,
        material_breakdown={"palm_oil": 100.0},
        default_unit="KGM",
        hs_code="1511.10.00"
    )
    
    # Palm Oil Blend (finished good)
    products["blend"] = Product(
        id=uuid4(),
        common_product_id="BLEND-001",
        name="Palm Oil Blend (80/20)",
        description="Blend of 80% palm oil and 20% palm kernel oil",
        category="finished_good",
        can_have_composition=True,
        material_breakdown={"palm_oil": 80.0, "palm_kernel_oil": 20.0},
        default_unit="KGM",
        hs_code="1511.90.00"
    )
    
    for product in products.values():
        db_session.add(product)
    
    db_session.commit()
    
    for product in products.values():
        db_session.refresh(product)
    
    return products


class TestTransparencyCalculation:
    """Test transparency score calculation."""
    
    def test_calculate_transparency_for_simple_chain(self, db_session, sample_companies, sample_products):
        """Test transparency calculation for a simple supply chain."""
        traceability_service = TraceabilityCalculationService(db_session)
        
        # Create a simple supply chain: FFB -> CPO
        # 1. FFB purchase order (originator -> processor)
        ffb_po = PurchaseOrder(
            po_number="PO-FFB-001",
            buyer_company_id=sample_companies["processor"].id,
            seller_company_id=sample_companies["originator"].id,
            product_id=sample_products["ffb"].id,
            quantity=Decimal("1000.0"),
            unit_price=Decimal("300.00"),
            total_amount=Decimal("300000.00"),
            unit="KGM",
            delivery_date=date.today() + timedelta(days=30),
            delivery_location="Processing Plant",
            status="confirmed",
            origin_data={
                "geographic_coordinates": {
                    "latitude": 2.5,
                    "longitude": 101.5,
                    "accuracy_meters": 10.0
                },
                "certifications": ["RSPO", "NDPE", "Sustainable"],
                "harvest_date": "2025-09-01",
                "farm_identification": "FARM-001"
            }
        )

        # Add and commit FFB purchase order first to get the ID
        db_session.add(ffb_po)
        db_session.commit()
        db_session.refresh(ffb_po)

        # 2. CPO purchase order (processor -> brand)
        cpo_po = PurchaseOrder(
            po_number="PO-CPO-001",
            buyer_company_id=sample_companies["brand"].id,
            seller_company_id=sample_companies["processor"].id,
            product_id=sample_products["cpo"].id,
            quantity=Decimal("800.0"),
            unit_price=Decimal("850.00"),
            total_amount=Decimal("680000.00"),
            unit="KGM",
            delivery_date=date.today() + timedelta(days=45),
            delivery_location="Brand Facility",
            status="confirmed",
            input_materials=[
                {
                    "source_po_id": str(ffb_po.id),
                    "quantity_used": 1000.0,
                    "percentage_contribution": 100.0,
                    "transformation_notes": "Processed FFB to CPO"
                }
            ],
            origin_data={
                "transformation_process": "Oil extraction from fresh fruit bunches",
                "facility_location": "Processing Plant A",
                "processing_date": "2025-09-05"
            }
        )

        db_session.add(cpo_po)
        db_session.commit()
        
        # Calculate transparency scores for the CPO purchase order
        metrics = traceability_service.calculate_transparency_scores(cpo_po.id)
        
        # Verify metrics
        assert metrics.total_nodes == 2  # FFB + CPO
        assert metrics.max_depth_reached == 1  # One level deep
        assert metrics.plantation_nodes == 1  # FFB from originator
        assert metrics.mill_nodes == 1  # CPO from processor
        assert metrics.origin_data_nodes == 2  # Both have origin data
        assert metrics.certified_nodes == 1  # FFB has certifications
        assert metrics.geographic_data_nodes == 1  # FFB has coordinates
        assert metrics.input_material_links == 1  # One input material link
        
        # Verify transparency scores
        assert 0.0 <= metrics.transparency_to_mill <= 1.0
        assert 0.0 <= metrics.transparency_to_plantation <= 1.0
        
        # TTP should be higher than TTM for this chain (has plantation data)
        assert metrics.transparency_to_plantation >= metrics.transparency_to_mill
        
        # Should have reasonable scores due to complete data
        assert metrics.transparency_to_mill >= 0.5  # TTM should be at least 0.5
        assert metrics.transparency_to_plantation >= 0.7  # TTP should be higher due to plantation data
    
    def test_calculate_transparency_for_complex_chain(self, db_session, sample_companies, sample_products):
        """Test transparency calculation for a complex supply chain."""
        traceability_service = TraceabilityCalculationService(db_session)
        
        # Create a complex supply chain: FFB -> CPO -> Blend
        # 1. FFB purchase order with excellent origin data
        ffb_po = PurchaseOrder(
            po_number="PO-FFB-002",
            buyer_company_id=sample_companies["processor"].id,
            seller_company_id=sample_companies["originator"].id,
            product_id=sample_products["ffb"].id,
            quantity=Decimal("2000.0"),
            unit_price=Decimal("300.00"),
            total_amount=Decimal("600000.00"),
            unit="KGM",
            delivery_date=date.today() + timedelta(days=30),
            delivery_location="Processing Plant",
            status="confirmed",
            origin_data={
                "geographic_coordinates": {
                    "latitude": 2.5,
                    "longitude": 101.5,
                    "accuracy_meters": 5.0
                },
                "certifications": ["RSPO", "NDPE", "ISPO", "Rainforest Alliance", "Organic"],
                "harvest_date": "2025-09-01",
                "farm_identification": "FARM-PREMIUM-001",
                "batch_number": "HARVEST-2025-001",
                "quality_parameters": {
                    "oil_content": 22.5,
                    "moisture": 18.2
                }
            }
        )

        # Add and commit FFB purchase order first
        db_session.add(ffb_po)
        db_session.commit()
        db_session.refresh(ffb_po)

        # 2. CPO purchase order
        cpo_po = PurchaseOrder(
            po_number="PO-CPO-002",
            buyer_company_id=sample_companies["brand"].id,
            seller_company_id=sample_companies["processor"].id,
            product_id=sample_products["cpo"].id,
            quantity=Decimal("1600.0"),
            unit_price=Decimal("850.00"),
            total_amount=Decimal("1360000.00"),
            unit="KGM",
            delivery_date=date.today() + timedelta(days=45),
            delivery_location="Brand Facility",
            status="confirmed",
            input_materials=[
                {
                    "source_po_id": str(ffb_po.id),
                    "quantity_used": 2000.0,
                    "percentage_contribution": 100.0,
                    "transformation_notes": "Premium FFB processed to high-quality CPO"
                }
            ],
            origin_data={
                "transformation_process": "Advanced oil extraction with quality control",
                "facility_location": "Premium Processing Plant",
                "processing_date": "2025-09-05",
                "yield_percentage": 80.0,
                "quality_parameters": {
                    "free_fatty_acid": 2.1,
                    "moisture": 0.1
                }
            }
        )

        # Add and commit CPO purchase order
        db_session.add(cpo_po)
        db_session.commit()
        db_session.refresh(cpo_po)

        # 3. Blend purchase order
        blend_po = PurchaseOrder(
            po_number="PO-BLEND-001",
            buyer_company_id=sample_companies["brand"].id,
            seller_company_id=sample_companies["processor"].id,
            product_id=sample_products["blend"].id,
            quantity=Decimal("1000.0"),
            unit_price=Decimal("900.00"),
            total_amount=Decimal("900000.00"),
            unit="KGM",
            delivery_date=date.today() + timedelta(days=60),
            delivery_location="Brand Facility",
            status="confirmed",
            composition={"palm_oil": 80.0, "palm_kernel_oil": 20.0},
            input_materials=[
                {
                    "source_po_id": str(cpo_po.id),
                    "quantity_used": 800.0,
                    "percentage_contribution": 80.0,
                    "transformation_notes": "Primary palm oil component"
                }
                # Note: Missing 20% PKO component for simplicity
            ],
            origin_data={
                "transformation_process": "Precision blending of palm oil components",
                "facility_location": "Blending Facility A",
                "processing_date": "2025-09-10"
            }
        )

        db_session.add(blend_po)
        db_session.commit()
        
        # Calculate transparency scores for the blend purchase order
        metrics = traceability_service.calculate_transparency_scores(blend_po.id)
        
        # Verify metrics for complex chain
        assert metrics.total_nodes == 3  # FFB + CPO + Blend
        assert metrics.max_depth_reached == 2  # Two levels deep
        assert metrics.plantation_nodes == 1  # FFB from originator
        assert metrics.mill_nodes == 2  # CPO and Blend from processor
        assert metrics.origin_data_nodes == 3  # All have origin data
        assert metrics.certified_nodes == 1  # FFB has certifications
        assert metrics.geographic_data_nodes == 1  # FFB has coordinates
        assert metrics.input_material_links == 2  # Two input material links
        
        # Should have good scores due to comprehensive data
        assert metrics.transparency_to_mill >= 0.4  # Reasonable TTM score for complex chain
        assert metrics.transparency_to_plantation >= 0.7  # Good TTP score due to comprehensive origin data
    
    def test_transparency_score_update_in_database(self, db_session, sample_companies, sample_products):
        """Test that transparency scores are correctly updated in the database."""
        traceability_service = TraceabilityCalculationService(db_session)
        
        # Create a purchase order
        po = PurchaseOrder(
            po_number="PO-UPDATE-001",
            buyer_company_id=sample_companies["brand"].id,
            seller_company_id=sample_companies["processor"].id,
            product_id=sample_products["cpo"].id,
            quantity=Decimal("1000.0"),
            unit_price=Decimal("850.00"),
            total_amount=Decimal("850000.00"),
            unit="KGM",
            delivery_date=date.today() + timedelta(days=30),
            delivery_location="Test Location",
            status="confirmed",
            origin_data={
                "transformation_process": "Basic processing",
                "facility_location": "Processing Plant"
            }
        )
        
        db_session.add(po)
        db_session.commit()
        
        # Verify initial state (no scores)
        assert po.transparency_to_mill is None
        assert po.transparency_to_plantation is None
        assert po.transparency_calculated_at is None
        
        # Update transparency scores
        metrics = traceability_service.update_transparency_scores(po.id)
        
        # Refresh the purchase order from database
        db_session.refresh(po)
        
        # Verify scores were saved
        assert po.transparency_to_mill is not None
        assert po.transparency_to_plantation is not None
        assert po.transparency_calculated_at is not None
        
        # Verify scores match calculated metrics
        assert float(po.transparency_to_mill) == pytest.approx(metrics.transparency_to_mill, rel=1e-4)
        assert float(po.transparency_to_plantation) == pytest.approx(metrics.transparency_to_plantation, rel=1e-4)
        
        # Verify timestamp is recent
        assert datetime.utcnow() - po.transparency_calculated_at < timedelta(minutes=1)
    
    def test_bulk_transparency_update(self, db_session, sample_companies, sample_products):
        """Test bulk transparency score updates."""
        traceability_service = TraceabilityCalculationService(db_session)
        
        # Create multiple purchase orders
        pos = []
        for i in range(3):
            po = PurchaseOrder(
                po_number=f"PO-BULK-{i+1:03d}",
                buyer_company_id=sample_companies["brand"].id,
                seller_company_id=sample_companies["processor"].id,
                product_id=sample_products["cpo"].id,
                quantity=Decimal("1000.0"),
                unit_price=Decimal("850.00"),
                total_amount=Decimal("850000.00"),
                unit="KGM",
                delivery_date=date.today() + timedelta(days=30),
                delivery_location="Test Location",
                status="confirmed",
                origin_data={
                    "transformation_process": f"Processing batch {i+1}",
                    "facility_location": "Processing Plant"
                }
            )
            pos.append(po)
        
        db_session.add_all(pos)
        db_session.commit()
        
        # Perform bulk update
        result = traceability_service.bulk_update_transparency_scores(
            company_id=sample_companies["processor"].id,
            max_age_hours=0  # Update all regardless of age
        )
        
        # Verify bulk update results
        assert result["total_processed"] == 3
        assert result["updated_count"] == 3
        assert result["error_count"] == 0
        assert len(result["results"]) == 3
        
        # Verify all purchase orders have scores
        for po in pos:
            db_session.refresh(po)
            assert po.transparency_to_mill is not None
            assert po.transparency_to_plantation is not None
            assert po.transparency_calculated_at is not None
    
    def test_transparency_analytics(self, db_session, sample_companies, sample_products):
        """Test transparency analytics calculation."""
        traceability_service = TraceabilityCalculationService(db_session)
        
        # Create purchase orders with different transparency levels
        # High transparency PO
        high_po = PurchaseOrder(
            po_number="PO-HIGH-001",
            buyer_company_id=sample_companies["brand"].id,
            seller_company_id=sample_companies["processor"].id,
            product_id=sample_products["cpo"].id,
            quantity=Decimal("1000.0"),
            unit_price=Decimal("850.00"),
            total_amount=Decimal("850000.00"),
            unit="KGM",
            delivery_date=date.today() + timedelta(days=30),
            delivery_location="Test Location",
            status="confirmed",
            transparency_to_mill=Decimal("0.9000"),
            transparency_to_plantation=Decimal("0.8500")
        )
        
        # Medium transparency PO
        medium_po = PurchaseOrder(
            po_number="PO-MEDIUM-001",
            buyer_company_id=sample_companies["brand"].id,
            seller_company_id=sample_companies["processor"].id,
            product_id=sample_products["cpo"].id,
            quantity=Decimal("1000.0"),
            unit_price=Decimal("850.00"),
            total_amount=Decimal("850000.00"),
            unit="KGM",
            delivery_date=date.today() + timedelta(days=30),
            delivery_location="Test Location",
            status="confirmed",
            transparency_to_mill=Decimal("0.6500"),
            transparency_to_plantation=Decimal("0.6000")
        )
        
        # Low transparency PO
        low_po = PurchaseOrder(
            po_number="PO-LOW-001",
            buyer_company_id=sample_companies["brand"].id,
            seller_company_id=sample_companies["processor"].id,
            product_id=sample_products["cpo"].id,
            quantity=Decimal("1000.0"),
            unit_price=Decimal("850.00"),
            total_amount=Decimal("850000.00"),
            unit="KGM",
            delivery_date=date.today() + timedelta(days=30),
            delivery_location="Test Location",
            status="confirmed",
            transparency_to_mill=Decimal("0.3000"),
            transparency_to_plantation=Decimal("0.2500")
        )
        
        db_session.add_all([high_po, medium_po, low_po])
        db_session.commit()
        
        # Get analytics
        analytics = traceability_service.get_transparency_analytics(sample_companies["brand"].id)
        
        # Verify analytics
        assert analytics["total_purchase_orders"] == 3
        assert analytics["average_ttm_score"] == pytest.approx(0.617, rel=1e-2)  # (0.9 + 0.65 + 0.3) / 3
        assert analytics["average_ttp_score"] == pytest.approx(0.567, rel=1e-2)  # (0.85 + 0.6 + 0.25) / 3
        
        # Verify distribution
        distribution = analytics["transparency_distribution"]
        assert distribution["high_transparency"] == 1  # >= 0.8
        assert distribution["medium_transparency"] == 1  # 0.5 <= x < 0.8
        assert distribution["low_transparency"] == 1  # < 0.5
        
        # Verify improvement opportunities
        assert len(analytics["improvement_opportunities"]) > 0

"""
Tests for the enhanced transparency calculation engine.
"""
import pytest
from uuid import uuid4, UUID
from decimal import Decimal
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.services.transparency_engine import TransparencyCalculationEngine, TransparencyNode
from app.models.purchase_order import PurchaseOrder
from app.models.company import Company
from app.models.product import Product
from app.models.user import User

# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_transparency_engine.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool)
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


class TestTransparencyCalculationEngine:
    """Test cases for the enhanced transparency calculation engine."""
    
    @pytest.fixture
    def transparency_engine(self, db_session):
        """Create transparency calculation engine."""
        return TransparencyCalculationEngine(db_session)
    
    @pytest.fixture
    def sample_companies(self, db_session):
        """Create sample companies for testing."""
        companies = {}
        
        # Originator company (plantation)
        companies["originator"] = Company(
            id=uuid4(),
            name="Premium Palm Plantation",
            company_type="originator",
            email="plantation@example.com"
        )

        # Processor company (mill)
        companies["processor"] = Company(
            id=uuid4(),
            name="Palm Oil Mill Sdn Bhd",
            company_type="processor",
            email="mill@example.com"
        )

        # Brand company
        companies["brand"] = Company(
            id=uuid4(),
            name="Global Food Brand",
            company_type="brand",
            email="brand@example.com"
        )
        
        for company in companies.values():
            db_session.add(company)
        
        db_session.commit()
        return companies
    
    @pytest.fixture
    def sample_products(self, db_session):
        """Create sample products for testing."""
        products = {}
        
        # Fresh Fruit Bunches (raw material)
        products["ffb"] = Product(
            id=uuid4(),
            common_product_id="FFB-001",
            name="Fresh Fruit Bunches",
            description="Fresh palm fruit bunches",
            category="raw_material",
            default_unit="KGM",
            hs_code="1207.10.00"
        )
        
        # Crude Palm Oil (processed)
        products["cpo"] = Product(
            id=uuid4(),
            common_product_id="CPO-001",
            name="Crude Palm Oil",
            description="Unrefined palm oil",
            category="processed",
            default_unit="KGM",
            hs_code="1511.10.00"
        )
        
        # Refined Palm Oil (finished)
        products["refined"] = Product(
            id=uuid4(),
            common_product_id="RBD-001",
            name="Refined Palm Oil",
            description="Refined, bleached, deodorized palm oil",
            category="finished_product",
            default_unit="KGM",
            hs_code="1511.90.00"
        )
        
        for product in products.values():
            db_session.add(product)
        
        db_session.commit()
        return products
    
    @pytest.fixture
    def sample_user(self, db_session, sample_companies):
        """Create sample user for testing."""
        user = User(
            id=uuid4(),
            email="test@example.com",
            hashed_password="test_password_hash",
            full_name="Test User",
            role="buyer",
            company_id=sample_companies["brand"].id
        )
        db_session.add(user)
        db_session.commit()
        return user
    
    def test_create_transparency_node(self, transparency_engine, sample_companies, sample_products):
        """Test transparency node creation."""
        po_data = {
            "id": uuid4(),
            "po_number": "PO-TEST-001",
            "seller_company_id": sample_companies["originator"].id,
            "product_id": sample_products["ffb"].id,
            "quantity": Decimal("1000.0"),
            "unit": "KGM",
            "origin_data": {
                "farm_id": "FARM-001",
                "harvest_date": "2025-09-05",
                "coordinates": {"lat": 2.5, "lng": 101.5}
            },
            "geographic_coordinates": {"latitude": 2.5, "longitude": 101.5},
            "certifications": ["RSPO", "NDPE", "Rainforest Alliance"],
            "input_materials": [],
            "company": {"company_type": "originator"},
            "product": {"category": "raw_material"}
        }
        
        node = transparency_engine._create_transparency_node(po_data, depth=0)
        
        # Verify node properties
        assert node.po_id == po_data["id"]
        assert node.po_number == "PO-TEST-001"
        assert node.company_type == "originator"
        assert node.product_category == "raw_material"
        assert node.has_origin_data is True
        assert node.has_geographic_coordinates is True
        assert node.has_certifications is True
        assert node.certification_count == 3
        assert node.high_value_cert_count == 3  # All are high-value certs
        assert node.data_completeness_score > 0.8  # Should be high
        assert node.depth == 0
    
    def test_calculate_base_scores(self, transparency_engine, sample_companies, sample_products):
        """Test base score calculation for transparency nodes."""
        # Create a high-quality originator node
        po_data = {
            "id": uuid4(),
            "po_number": "PO-ORIGIN-001",
            "seller_company_id": sample_companies["originator"].id,
            "product_id": sample_products["ffb"].id,
            "quantity": Decimal("1000.0"),
            "unit": "KGM",
            "origin_data": {"farm_id": "FARM-001"},
            "geographic_coordinates": {"latitude": 2.5, "longitude": 101.5},
            "certifications": ["RSPO", "NDPE"],
            "input_materials": [],
            "company": {"company_type": "originator"},
            "product": {"category": "raw_material"}
        }
        
        node = transparency_engine._create_transparency_node(po_data, depth=0)
        transparency_engine._calculate_base_scores(node)
        
        # Verify scores
        assert 0.0 <= node.base_ttm_score <= 1.0
        assert 0.0 <= node.base_ttp_score <= 1.0
        
        # TTP should be higher for originator with good data
        assert node.base_ttp_score >= node.base_ttm_score
        
        # Should have high scores due to complete data
        assert node.base_ttm_score >= 0.7
        assert node.base_ttp_score >= 0.8
    
    def test_circular_reference_detection(self, transparency_engine, db_session, sample_companies, sample_products, sample_user):
        """Test circular reference detection in supply chain."""
        # Create a circular reference: PO1 -> PO2 -> PO3 -> PO1
        po1 = PurchaseOrder(
            id=uuid4(),
            po_number="PO-CIRCULAR-001",
            buyer_company_id=sample_companies["brand"].id,
            seller_company_id=sample_companies["processor"].id,
            product_id=sample_products["cpo"].id,
            quantity=Decimal("500.0"),
            unit="KGM",
            unit_price=Decimal("2500.00"),
            total_amount=Decimal("1250000.00"),
            status="confirmed",
            created_by_user_id=sample_user.id
        )
        
        po2 = PurchaseOrder(
            id=uuid4(),
            po_number="PO-CIRCULAR-002",
            buyer_company_id=sample_companies["processor"].id,
            seller_company_id=sample_companies["originator"].id,
            product_id=sample_products["ffb"].id,
            quantity=Decimal("1000.0"),
            unit="KGM",
            unit_price=Decimal("800.00"),
            total_amount=Decimal("800000.00"),
            status="confirmed",
            created_by_user_id=sample_user.id
        )
        
        po3 = PurchaseOrder(
            id=uuid4(),
            po_number="PO-CIRCULAR-003",
            buyer_company_id=sample_companies["originator"].id,
            seller_company_id=sample_companies["brand"].id,
            product_id=sample_products["refined"].id,
            quantity=Decimal("300.0"),
            unit="KGM",
            unit_price=Decimal("3000.00"),
            total_amount=Decimal("900000.00"),
            status="confirmed",
            created_by_user_id=sample_user.id
        )
        
        # Create circular input materials
        po1.input_materials = [{"source_po_id": str(po2.id), "percentage_contribution": 100}]
        po2.input_materials = [{"source_po_id": str(po3.id), "percentage_contribution": 100}]
        po3.input_materials = [{"source_po_id": str(po1.id), "percentage_contribution": 100}]
        
        db_session.add_all([po1, po2, po3])
        db_session.commit()
        
        # Test circular reference detection
        circular_refs = transparency_engine.detect_circular_references(po1.id)
        
        # Should detect circular references
        assert len(circular_refs) > 0
        assert any(ref in [po1.id, po2.id, po3.id] for ref in circular_refs)
    
    def test_degradation_factor_calculation(self, transparency_engine):
        """Test degradation factor calculation based on depth."""
        # Test degradation at different depths
        assert transparency_engine._calculate_degradation_factor(0) == 1.0  # No degradation at root
        
        depth_1_degradation = transparency_engine._calculate_degradation_factor(1)
        assert depth_1_degradation == 0.95  # 5% degradation
        
        depth_2_degradation = transparency_engine._calculate_degradation_factor(2)
        assert depth_2_degradation == pytest.approx(0.9025, rel=1e-3)  # 0.95^2
        
        # Test minimum degradation limit
        deep_degradation = transparency_engine._calculate_degradation_factor(50)
        assert deep_degradation >= 0.1  # Should not go below 10%

    def test_simple_supply_chain_transparency(self, transparency_engine, db_session, sample_companies, sample_products, sample_user):
        """Test transparency calculation for a simple supply chain."""
        # Create FFB purchase order (origin)
        ffb_po = PurchaseOrder(
            id=uuid4(),
            po_number="PO-FFB-001",
            buyer_company_id=sample_companies["processor"].id,
            seller_company_id=sample_companies["originator"].id,
            product_id=sample_products["ffb"].id,
            quantity=Decimal("1000.0"),
            unit="KGM",
            unit_price=Decimal("800.00"),
            total_amount=Decimal("800000.00"),
            delivery_date=datetime.utcnow().date(),
            delivery_location="Mill Processing Facility",
            status="confirmed",
            origin_data={
                "farm_id": "FARM-PREMIUM-001",
                "harvest_date": "2025-09-05",
                "harvest_method": "manual_selective",
                "coordinates": {
                    "latitude": 2.5,
                    "longitude": 101.5,
                    "accuracy_meters": 10.0
                },
                "certifications": ["RSPO", "NDPE", "Rainforest Alliance"]
            }
        )

        # Create CPO purchase order (processed from FFB)
        cpo_po = PurchaseOrder(
            id=uuid4(),
            po_number="PO-CPO-001",
            buyer_company_id=sample_companies["brand"].id,
            seller_company_id=sample_companies["processor"].id,
            product_id=sample_products["cpo"].id,
            quantity=Decimal("400.0"),
            unit="KGM",
            unit_price=Decimal("2500.00"),
            total_amount=Decimal("1000000.00"),
            delivery_date=datetime.utcnow().date(),
            delivery_location="Brand Processing Facility",
            status="confirmed",
            input_materials=[
                {
                    "source_po_id": str(ffb_po.id),
                    "percentage_contribution": 100,
                    "quantity_used": 1000.0
                }
            ],
            origin_data={
                "mill_id": "MILL-001",
                "processing_date": "2025-09-06",
                "extraction_method": "screw_press"
            }
        )

        db_session.add_all([ffb_po, cpo_po])
        db_session.commit()

        # Calculate transparency for CPO
        result = transparency_engine.calculate_transparency(cpo_po.id)

        # Verify results
        assert result.po_id == cpo_po.id
        assert 0.0 <= result.ttm_score <= 1.0
        assert 0.0 <= result.ttp_score <= 1.0
        assert 0.0 <= result.confidence_level <= 1.0

        # Should have good scores due to complete supply chain
        assert result.ttm_score >= 0.7  # Good mill transparency
        assert result.ttp_score >= 0.8  # Excellent plantation transparency
        assert result.confidence_level >= 0.7  # Good confidence

        # Should have traced most materials
        assert result.traced_percentage >= 80.0
        assert result.untraced_percentage <= 20.0

        # Graph analysis
        assert result.total_nodes == 2  # FFB + CPO
        assert result.max_depth == 1  # One level deep
        assert len(result.circular_references) == 0  # No cycles
        assert result.degradation_applied == 1.0  # No degradation at root level

    def test_complex_supply_chain_transparency(self, transparency_engine, db_session, sample_companies, sample_products, sample_user):
        """Test transparency calculation for a complex multi-level supply chain."""
        # Create multiple FFB sources
        ffb_po1 = PurchaseOrder(
            id=uuid4(),
            po_number="PO-FFB-001",
            buyer_company_id=sample_companies["processor"].id,
            seller_company_id=sample_companies["originator"].id,
            product_id=sample_products["ffb"].id,
            quantity=Decimal("600.0"),
            unit="KGM",
            unit_price=Decimal("800.00"),
            total_amount=Decimal("480000.00"),
            status="confirmed",
            origin_data={"farm_id": "FARM-001"},
            geographic_coordinates={"latitude": 2.5, "longitude": 101.5},
            certifications=["RSPO", "NDPE"],
            created_by_user_id=sample_user.id
        )

        ffb_po2 = PurchaseOrder(
            id=uuid4(),
            po_number="PO-FFB-002",
            buyer_company_id=sample_companies["processor"].id,
            seller_company_id=sample_companies["originator"].id,
            product_id=sample_products["ffb"].id,
            quantity=Decimal("400.0"),
            unit="KGM",
            unit_price=Decimal("750.00"),
            total_amount=Decimal("300000.00"),
            status="confirmed",
            origin_data={"farm_id": "FARM-002"},
            certifications=["RSPO"],  # Fewer certifications
            created_by_user_id=sample_user.id
        )

        # Create CPO from mixed FFB sources
        cpo_po = PurchaseOrder(
            id=uuid4(),
            po_number="PO-CPO-001",
            buyer_company_id=sample_companies["brand"].id,
            seller_company_id=sample_companies["processor"].id,
            product_id=sample_products["cpo"].id,
            quantity=Decimal("400.0"),
            unit="KGM",
            unit_price=Decimal("2500.00"),
            total_amount=Decimal("1000000.00"),
            status="confirmed",
            input_materials=[
                {
                    "source_po_id": str(ffb_po1.id),
                    "percentage_contribution": 60,
                    "quantity_used": 600.0
                },
                {
                    "source_po_id": str(ffb_po2.id),
                    "percentage_contribution": 40,
                    "quantity_used": 400.0
                }
            ],
            origin_data={"mill_id": "MILL-001"},
            created_by_user_id=sample_user.id
        )

        # Create refined oil from CPO
        refined_po = PurchaseOrder(
            id=uuid4(),
            po_number="PO-REFINED-001",
            buyer_company_id=sample_companies["brand"].id,
            seller_company_id=sample_companies["processor"].id,
            product_id=sample_products["refined"].id,
            quantity=Decimal("350.0"),
            unit="KGM",
            unit_price=Decimal("3000.00"),
            total_amount=Decimal("1050000.00"),
            status="confirmed",
            input_materials=[
                {
                    "source_po_id": str(cpo_po.id),
                    "percentage_contribution": 100,
                    "quantity_used": 400.0
                }
            ],
            origin_data={"refinery_id": "REF-001"},
            created_by_user_id=sample_user.id
        )

        db_session.add_all([ffb_po1, ffb_po2, cpo_po, refined_po])
        db_session.commit()

        # Calculate transparency for refined oil
        result = transparency_engine.calculate_transparency(refined_po.id)

        # Verify complex chain results
        assert result.total_nodes == 4  # 2 FFB + 1 CPO + 1 Refined
        assert result.max_depth == 2  # Two levels deep
        assert len(result.circular_references) == 0  # No cycles

        # Scores should be good but lower due to complexity
        assert 0.5 <= result.ttm_score <= 0.9
        assert 0.6 <= result.ttp_score <= 0.9
        assert result.confidence_level >= 0.7

        # Should have reasonable traceability
        assert result.traced_percentage >= 70.0

    def test_transparency_improvement_suggestions(self, transparency_engine):
        """Test transparency improvement suggestion generation."""
        # Create a result with low scores
        from app.services.transparency_engine import TransparencyResult

        low_score_result = TransparencyResult(
            po_id=uuid4(),
            ttm_score=0.4,  # Low TTM
            ttp_score=0.3,  # Low TTP
            confidence_level=0.5,  # Low confidence
            traced_percentage=60.0,
            untraced_percentage=40.0,  # High untraced
            total_nodes=5,
            max_depth=3,
            circular_references=[uuid4()],  # Has circular reference
            degradation_applied=0.85,
            paths=[],
            node_details=[],
            calculation_metadata={},
            calculated_at=datetime.utcnow(),
            calculation_duration_ms=150.0
        )

        suggestions = transparency_engine.get_transparency_improvement_suggestions(low_score_result)

        # Should generate multiple suggestions
        assert len(suggestions) >= 4

        # Check for expected suggestion categories
        categories = [s["category"] for s in suggestions]
        assert "mill_transparency" in categories
        assert "plantation_transparency" in categories
        assert "data_quality" in categories
        assert "data_integrity" in categories
        assert "traceability_coverage" in categories

        # Check suggestion structure
        for suggestion in suggestions:
            assert "category" in suggestion
            assert "priority" in suggestion
            assert "description" in suggestion
            assert "expected_impact" in suggestion
            assert "implementation_effort" in suggestion
            assert suggestion["priority"] in ["high", "medium", "low"]
            assert suggestion["implementation_effort"] in ["low", "medium", "high"]

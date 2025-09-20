"""
Tests for transparency visualization and gap analysis system.
"""
import pytest
from unittest.mock import Mock, patch
from uuid import uuid4
from datetime import datetime
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.services.transparency_visualization import (
    TransparencyVisualizationService,
    SupplyChainVisualization,
    GapAnalysisResult,
    VisualizationNode,
    VisualizationEdge
)
from app.services.transparency_engine import TransparencyCalculationEngine, TransparencyResult, TransparencyNode
from app.models.user import User
from app.models.company import Company
from app.models.purchase_order import PurchaseOrder
from app.models.product import Product

# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_transparency_viz.db"
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


@pytest.fixture
def sample_companies(db_session):
    """Create sample companies for testing."""
    companies = {}
    
    companies["originator"] = Company(
        id=uuid4(),
        name="Palm Oil Originator",
        company_type="originator",
        email="originator@example.com"
    )
    
    companies["processor"] = Company(
        id=uuid4(),
        name="Processing Company",
        company_type="processor",
        email="processor@example.com"
    )
    
    companies["brand"] = Company(
        id=uuid4(),
        name="Brand Company",
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
def sample_products(db_session):
    """Create sample products for testing."""
    products = {}
    
    products["crude_oil"] = Product(
        id=uuid4(),
        common_product_id="CPO-001",
        name="Crude Palm Oil",
        description="Raw palm oil from plantation",
        category="raw_material",
        can_have_composition=False,
        default_unit="KGM"
    )
    
    products["refined_oil"] = Product(
        id=uuid4(),
        common_product_id="RPO-001",
        name="Refined Palm Oil",
        description="Processed palm oil",
        category="processed",
        can_have_composition=True,
        default_unit="KGM"
    )
    
    for product in products.values():
        db_session.add(product)
    
    db_session.commit()
    
    for product in products.values():
        db_session.refresh(product)
    
    return products


@pytest.fixture
def sample_purchase_orders(db_session, sample_companies, sample_products):
    """Create sample purchase orders for testing."""
    pos = {}
    
    # Originator PO (raw material)
    pos["originator_po"] = PurchaseOrder(
        id=uuid4(),
        po_number="PO-ORIG-001",
        buyer_company_id=sample_companies["processor"].id,
        seller_company_id=sample_companies["originator"].id,
        product_id=sample_products["crude_oil"].id,
        quantity=Decimal("1000.0"),
        unit="KGM",
        unit_price=Decimal("800.00"),
        total_amount=Decimal("800000.00"),
        delivery_date=datetime.utcnow().date(),
        delivery_location="Processing Plant",
        status="confirmed",
        transparency_to_mill=0.9,
        transparency_to_plantation=0.95
    )
    
    # Processor PO (processed material)
    pos["processor_po"] = PurchaseOrder(
        id=uuid4(),
        po_number="PO-PROC-001",
        buyer_company_id=sample_companies["brand"].id,
        seller_company_id=sample_companies["processor"].id,
        product_id=sample_products["refined_oil"].id,
        quantity=Decimal("800.0"),
        unit="KGM",
        unit_price=Decimal("1200.00"),
        total_amount=Decimal("960000.00"),
        delivery_date=datetime.utcnow().date(),
        delivery_location="Brand Facility",
        status="confirmed",
        transparency_to_mill=0.7,
        transparency_to_plantation=0.6
    )
    
    for po in pos.values():
        db_session.add(po)
    
    db_session.commit()
    
    for po in pos.values():
        db_session.refresh(po)
    
    return pos


@pytest.fixture
def mock_transparency_result():
    """Create a mock transparency result for testing."""
    # Create mock transparency nodes
    originator_node = TransparencyNode(
        po_id=uuid4(),
        po_number="PO-ORIG-001",
        company_id=uuid4(),
        company_type="originator",
        product_id=uuid4(),
        product_category="raw_material",
        quantity=Decimal("1000.0"),
        unit="KGM",
        has_origin_data=True,
        has_geographic_coordinates=True,
        has_certifications=False,  # Missing certification - gap
        certification_count=0,
        high_value_cert_count=0,
        data_completeness_score=0.8,
        input_materials=[],
        base_ttm_score=0.9,
        base_ttp_score=0.95,
        weighted_ttm_score=0.9,
        weighted_ttp_score=0.95,
        confidence_level=0.85,
        depth=0,
        is_circular=False
    )
    
    processor_node = TransparencyNode(
        po_id=uuid4(),
        po_number="PO-PROC-001",
        company_id=uuid4(),
        company_type="processor",
        product_id=uuid4(),
        product_category="processed",
        quantity=Decimal("800.0"),
        unit="KGM",
        has_origin_data=False,  # Missing origin data - gap
        has_geographic_coordinates=True,
        has_certifications=True,
        certification_count=2,
        high_value_cert_count=1,
        data_completeness_score=0.7,
        input_materials=[{
            "po_id": originator_node.po_id,
            "quantity": 1000.0,
            "unit": "KGM",
            "transparency_contribution": 0.8,
            "confidence_level": 0.85
        }],
        base_ttm_score=0.7,
        base_ttp_score=0.6,
        weighted_ttm_score=0.7,
        weighted_ttp_score=0.6,
        confidence_level=0.75,
        depth=1,
        is_circular=False
    )
    
    return TransparencyResult(
        po_id=processor_node.po_id,
        ttm_score=0.75,
        ttp_score=0.7,
        confidence_level=0.8,
        traced_percentage=85.0,
        untraced_percentage=15.0,
        total_nodes=2,
        max_depth=1,
        circular_references=[],
        degradation_applied=0.05,
        paths=[],
        node_details=[originator_node, processor_node],
        calculation_metadata={
            "algorithm_version": "2.0",
            "calculation_time_ms": 150
        },
        calculation_duration_ms=150,
        calculated_at=datetime.utcnow()
    )


class TestTransparencyVisualizationService:
    """Test transparency visualization service functionality."""
    
    def test_generate_supply_chain_visualization(self, db_session, sample_companies, sample_products, sample_purchase_orders, mock_transparency_result):
        """Test generating supply chain visualization."""
        visualization_service = TransparencyVisualizationService(db_session)
        
        # Mock the transparency engine
        with patch.object(visualization_service.transparency_engine, 'calculate_transparency') as mock_calc:
            mock_calc.return_value = mock_transparency_result
            
            # Generate visualization
            visualization = visualization_service.generate_supply_chain_visualization(
                po_id=sample_purchase_orders["processor_po"].id,
                include_gap_analysis=True
            )
            
            # Verify visualization structure
            assert isinstance(visualization, SupplyChainVisualization)
            assert visualization.company_id == sample_purchase_orders["processor_po"].buyer_company_id
            assert visualization.root_po_id == sample_purchase_orders["processor_po"].id
            assert len(visualization.nodes) == 2  # Two nodes from mock result
            assert len(visualization.edges) == 1  # One edge connecting them
            assert visualization.total_levels == 2  # Two levels (0 and 1)
            assert visualization.overall_ttm_score == 0.75
            assert visualization.overall_ttp_score == 0.7
            assert visualization.traced_percentage == 85.0
            assert visualization.untraced_percentage == 15.0
            
            # Verify gap analysis is included
            assert visualization.gap_analysis is not None
            assert isinstance(visualization.gap_analysis, GapAnalysisResult)
    
    def test_analyze_transparency_gaps(self, db_session, mock_transparency_result):
        """Test transparency gap analysis."""
        visualization_service = TransparencyVisualizationService(db_session)
        company_id = uuid4()
        
        # Analyze gaps
        gap_analysis = visualization_service.analyze_transparency_gaps(
            mock_transparency_result, company_id
        )
        
        # Verify gap analysis structure
        assert isinstance(gap_analysis, GapAnalysisResult)
        assert gap_analysis.company_id == company_id
        assert gap_analysis.total_gaps > 0  # Should find gaps in mock data
        assert gap_analysis.current_ttm_score == 0.75
        assert gap_analysis.current_ttp_score == 0.7
        assert gap_analysis.potential_ttm_score > gap_analysis.current_ttm_score
        assert gap_analysis.potential_ttp_score > gap_analysis.current_ttp_score
        
        # Verify gap details
        assert len(gap_analysis.gap_details) > 0
        gap_detail = gap_analysis.gap_details[0]
        assert "po_id" in gap_detail
        assert "category" in gap_detail
        assert "severity" in gap_detail
        assert "description" in gap_detail
        assert "impact" in gap_detail
        assert "recommendation" in gap_detail
        
        # Verify improvement recommendations
        assert len(gap_analysis.improvement_recommendations) > 0
        recommendation = gap_analysis.improvement_recommendations[0]
        assert "category" in recommendation
        assert "priority" in recommendation
        assert "title" in recommendation
        assert "description" in recommendation
        assert "expected_ttm_impact" in recommendation
        assert "expected_ttp_impact" in recommendation
    
    def test_visualization_node_generation(self, db_session, sample_companies, sample_products, mock_transparency_result):
        """Test visualization node generation."""
        visualization_service = TransparencyVisualizationService(db_session)
        
        # Generate nodes
        nodes = visualization_service._generate_visualization_nodes(mock_transparency_result)
        
        # Verify nodes
        assert len(nodes) == 2
        
        # Check first node (originator)
        originator_node = nodes[0]
        assert isinstance(originator_node, VisualizationNode)
        assert originator_node.company_type == "originator"
        assert originator_node.level == 0
        assert originator_node.has_origin_data == True
        assert originator_node.has_geographic_coordinates == True
        assert originator_node.has_certifications == False
        assert "certifications" in originator_node.missing_data_fields
        
        # Check second node (processor)
        processor_node = nodes[1]
        assert processor_node.company_type == "processor"
        assert processor_node.level == 1
        assert processor_node.has_origin_data == False
        assert "origin_data" in processor_node.missing_data_fields
    
    def test_visualization_edge_generation(self, db_session, mock_transparency_result):
        """Test visualization edge generation."""
        visualization_service = TransparencyVisualizationService(db_session)
        
        # Generate edges
        edges = visualization_service._generate_visualization_edges(mock_transparency_result)
        
        # Verify edges
        assert len(edges) == 1
        
        edge = edges[0]
        assert isinstance(edge, VisualizationEdge)
        assert edge.source_node_id == "node_0"  # Originator node
        assert edge.target_node_id == "node_1"  # Processor node
        assert edge.quantity_flow == 1000.0
        assert edge.transparency_flow == 0.8
        assert edge.confidence_flow == 0.85
    
    def test_hierarchical_layout(self, db_session, mock_transparency_result):
        """Test hierarchical layout algorithm."""
        visualization_service = TransparencyVisualizationService(db_session)
        
        # Generate nodes and apply layout
        nodes = visualization_service._generate_visualization_nodes(mock_transparency_result)
        edges = visualization_service._generate_visualization_edges(mock_transparency_result)
        
        visualization_service._apply_hierarchical_layout(nodes, edges)
        
        # Verify layout
        assert len(nodes) == 2
        
        # Level 0 node should be at y=0
        level_0_node = next(node for node in nodes if node.level == 0)
        assert level_0_node.position_y == 0
        
        # Level 1 node should be at y=150
        level_1_node = next(node for node in nodes if node.level == 1)
        assert level_1_node.position_y == 150
        
        # Nodes at different levels should have different y positions
        assert level_0_node.position_y != level_1_node.position_y
    
    def test_gap_severity_determination(self, db_session):
        """Test gap severity determination logic."""
        visualization_service = TransparencyVisualizationService(db_session)
        
        # Create test nodes
        originator_node = TransparencyNode(
            po_id=uuid4(),
            po_number="TEST-001",
            company_id=uuid4(),
            company_type="originator",
            product_id=uuid4(),
            product_category="raw_material",
            quantity=Decimal("1000.0"),
            unit="KGM"
        )
        
        processor_node = TransparencyNode(
            po_id=uuid4(),
            po_number="TEST-002",
            company_id=uuid4(),
            company_type="processor",
            product_id=uuid4(),
            product_category="processed",
            quantity=Decimal("800.0"),
            unit="KGM"
        )
        
        # Test severity for originator (should be critical for origin data)
        originator_severity = visualization_service._determine_gap_severity(originator_node, "origin_data")
        assert originator_severity == "critical"
        
        # Test severity for processor (should be high for input materials)
        processor_severity = visualization_service._determine_gap_severity(processor_node, "input_materials")
        assert processor_severity == "high"
        
        # Test severity for certifications (should be lower priority)
        cert_severity = visualization_service._determine_gap_severity(processor_node, "certifications")
        assert cert_severity == "medium"
    
    def test_improvement_potential_calculation(self, db_session, mock_transparency_result):
        """Test improvement potential calculation."""
        visualization_service = TransparencyVisualizationService(db_session)
        
        # Create sample gap details
        gap_details = [
            {
                "category": "missing_origin_data",
                "impact": 0.3,
                "severity": "high"
            },
            {
                "category": "missing_certification",
                "impact": 0.2,
                "severity": "medium"
            }
        ]
        
        # Calculate improvement potential
        potential_ttm, potential_ttp = visualization_service._calculate_improvement_potential(
            mock_transparency_result, gap_details
        )
        
        # Verify improvement potential
        assert potential_ttm > mock_transparency_result.ttm_score
        assert potential_ttp > mock_transparency_result.ttp_score
        assert potential_ttm <= 1.0
        assert potential_ttp <= 1.0
    
    def test_node_color_assignment(self, db_session):
        """Test node color assignment based on transparency scores."""
        visualization_service = TransparencyVisualizationService(db_session)
        
        # Create nodes with different transparency scores
        high_score_node = TransparencyNode(
            po_id=uuid4(),
            po_number="HIGH-001",
            company_id=uuid4(),
            company_type="originator",
            product_id=uuid4(),
            product_category="raw_material",
            quantity=Decimal("1000.0"),
            unit="KGM",
            base_ttm_score=0.9,
            base_ttp_score=0.9
        )
        
        low_score_node = TransparencyNode(
            po_id=uuid4(),
            po_number="LOW-001",
            company_id=uuid4(),
            company_type="processor",
            product_id=uuid4(),
            product_category="processed",
            quantity=Decimal("800.0"),
            unit="KGM",
            base_ttm_score=0.2,
            base_ttp_score=0.2
        )
        
        # Test color assignment
        high_color = visualization_service._get_node_color(high_score_node)
        low_color = visualization_service._get_node_color(low_score_node)
        
        # High score should get company type color
        assert high_color == visualization_service.NODE_COLORS["originator"]
        
        # Low score should get gap color
        assert low_color == visualization_service.GAP_COLORS["critical"]

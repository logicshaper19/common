"""
Comprehensive tests for TransparencyGapAnalyzer.

This demonstrates the dramatic improvement in testability achieved by
extracting the gap analysis logic into a focused, single-responsibility service.
"""
import pytest
from unittest.mock import Mock, MagicMock
from uuid import uuid4

from app.services.transparency_visualization.gap_analyzer import TransparencyGapAnalyzer
from app.services.transparency_visualization.models.gap_models import GapType, GapSeverity


class TestTransparencyGapAnalyzer:
    """Test suite for TransparencyGapAnalyzer."""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        return Mock()
    
    @pytest.fixture
    def gap_analyzer(self, mock_db):
        """Create gap analyzer instance."""
        return TransparencyGapAnalyzer(mock_db)
    
    @pytest.fixture
    def sample_transparency_node(self):
        """Create sample transparency node for testing."""
        node = Mock()
        node.po_id = uuid4()
        node.ttm_score = 0.4
        node.ttp_score = 0.3
        node.confidence_level = 0.6
        node.quantity = 500.0
        node.origin_data = None
        node.input_materials = None
        node.certifications = None
        node.geographic_coordinates = None
        return node
    
    def test_analyze_transparency_gaps_no_gaps(self, gap_analyzer, sample_transparency_node):
        """Test gap analysis when no gaps are present."""
        # Setup node with complete data
        sample_transparency_node.origin_data = {"harvest_date": "2024-01-01"}
        sample_transparency_node.input_materials = [{"source_po_id": uuid4()}]
        sample_transparency_node.certifications = ["organic"]
        sample_transparency_node.geographic_coordinates = {"lat": 40.7128, "lng": -74.0060}
        sample_transparency_node.confidence_level = 0.9
        
        gaps = gap_analyzer.analyze_transparency_gaps([sample_transparency_node])
        
        assert len(gaps) == 0
    
    def test_analyze_transparency_gaps_missing_origin_data(self, gap_analyzer, sample_transparency_node):
        """Test gap analysis for missing origin data."""
        gaps = gap_analyzer.analyze_transparency_gaps([sample_transparency_node])
        
        assert len(gaps) == 4  # Missing origin data, input materials, certifications, geographic data
        
        origin_gap = next(g for g in gaps if g.gap_type == GapType.MISSING_ORIGIN_DATA)
        assert origin_gap.severity == GapSeverity.CRITICAL
        assert "origin data" in origin_gap.description.lower()
        assert origin_gap.impact_score > 0
    
    def test_analyze_transparency_gaps_low_confidence(self, gap_analyzer, sample_transparency_node):
        """Test gap analysis for low confidence."""
        sample_transparency_node.confidence_level = 0.5  # Below threshold
        
        gaps = gap_analyzer.analyze_transparency_gaps([sample_transparency_node])
        
        confidence_gap = next(g for g in gaps if g.gap_type == GapType.LOW_CONFIDENCE)
        assert confidence_gap.severity == GapSeverity.HIGH
        assert "confidence" in confidence_gap.description.lower()
    
    def test_determine_gap_severity_critical(self, gap_analyzer, sample_transparency_node):
        """Test gap severity determination for critical gaps."""
        sample_transparency_node.ttm_score = 0.2
        sample_transparency_node.ttp_score = 0.1
        
        severity = gap_analyzer._determine_gap_severity(sample_transparency_node, GapType.MISSING_ORIGIN_DATA)
        
        assert severity == GapSeverity.CRITICAL
    
    def test_determine_gap_severity_high(self, gap_analyzer, sample_transparency_node):
        """Test gap severity determination for high severity gaps."""
        sample_transparency_node.ttm_score = 0.4
        sample_transparency_node.ttp_score = 0.3
        
        severity = gap_analyzer._determine_gap_severity(sample_transparency_node, GapType.MISSING_INPUT_MATERIAL)
        
        assert severity == GapSeverity.HIGH
    
    def test_determine_gap_severity_medium(self, gap_analyzer, sample_transparency_node):
        """Test gap severity determination for medium severity gaps."""
        sample_transparency_node.ttm_score = 0.6
        sample_transparency_node.ttp_score = 0.5
        
        severity = gap_analyzer._determine_gap_severity(sample_transparency_node, GapType.INCOMPLETE_CERTIFICATIONS)
        
        assert severity == GapSeverity.MEDIUM
    
    def test_determine_gap_severity_low(self, gap_analyzer, sample_transparency_node):
        """Test gap severity determination for low severity gaps."""
        sample_transparency_node.ttm_score = 0.8
        sample_transparency_node.ttp_score = 0.9
        
        severity = gap_analyzer._determine_gap_severity(sample_transparency_node, GapType.INCOMPLETE_CERTIFICATIONS)
        
        assert severity == GapSeverity.LOW
    
    def test_calculate_gap_impact(self, gap_analyzer, sample_transparency_node):
        """Test gap impact calculation."""
        impact = gap_analyzer._calculate_gap_impact(sample_transparency_node, GapType.MISSING_ORIGIN_DATA)
        
        # Impact should be based on quantity and gap weight
        assert impact > 0
        assert impact <= 100  # Should be normalized to 0-100 range
    
    def test_calculate_improvement_potential(self, gap_analyzer, sample_transparency_node):
        """Test improvement potential calculation."""
        ttm_potential, ttp_potential = gap_analyzer._calculate_improvement_potential(
            sample_transparency_node, GapType.MISSING_ORIGIN_DATA
        )
        
        # With low transparency scores, potential should be high
        assert ttm_potential > 0
        assert ttp_potential > 0
        assert ttm_potential <= 1.0
        assert ttp_potential <= 1.0
    
    def test_has_origin_data_true(self, gap_analyzer, sample_transparency_node):
        """Test origin data detection when data exists."""
        sample_transparency_node.origin_data = {"harvest_date": "2024-01-01"}
        
        has_data = gap_analyzer._has_origin_data(sample_transparency_node)
        
        assert has_data is True
    
    def test_has_origin_data_false(self, gap_analyzer, sample_transparency_node):
        """Test origin data detection when data is missing."""
        sample_transparency_node.origin_data = None
        
        has_data = gap_analyzer._has_origin_data(sample_transparency_node)
        
        assert has_data is False
    
    def test_has_input_materials_true(self, gap_analyzer, sample_transparency_node):
        """Test input materials detection when data exists."""
        sample_transparency_node.input_materials = [{"source_po_id": uuid4()}]
        
        has_materials = gap_analyzer._has_input_materials(sample_transparency_node)
        
        assert has_materials is True
    
    def test_has_input_materials_false(self, gap_analyzer, sample_transparency_node):
        """Test input materials detection when data is missing."""
        sample_transparency_node.input_materials = None
        
        has_materials = gap_analyzer._has_input_materials(sample_transparency_node)
        
        assert has_materials is False
    
    def test_get_affected_metrics(self, gap_analyzer):
        """Test affected metrics calculation for different gap types."""
        ttm_metrics = gap_analyzer._get_affected_metrics(GapType.MISSING_ORIGIN_DATA)
        assert "ttm_score" in ttm_metrics
        assert "ttp_score" in ttm_metrics
        
        ttp_metrics = gap_analyzer._get_affected_metrics(GapType.MISSING_INPUT_MATERIAL)
        assert "ttm_score" in ttp_metrics
        assert "ttp_score" in ttp_metrics
    
    def test_get_suggested_actions(self, gap_analyzer):
        """Test suggested actions for different gap types."""
        origin_actions = gap_analyzer._get_suggested_actions(GapType.MISSING_ORIGIN_DATA)
        assert len(origin_actions) > 0
        assert any("harvest" in action.lower() for action in origin_actions)
        
        material_actions = gap_analyzer._get_suggested_actions(GapType.MISSING_INPUT_MATERIAL)
        assert len(material_actions) > 0
        assert any("supplier" in action.lower() for action in material_actions)
    
    def test_analyze_multiple_nodes(self, gap_analyzer):
        """Test gap analysis across multiple nodes."""
        node1 = Mock()
        node1.po_id = uuid4()
        node1.ttm_score = 0.2
        node1.ttp_score = 0.1
        node1.confidence_level = 0.5
        node1.quantity = 100.0
        node1.origin_data = None
        node1.input_materials = None
        node1.certifications = None
        node1.geographic_coordinates = None
        
        node2 = Mock()
        node2.po_id = uuid4()
        node2.ttm_score = 0.8
        node2.ttp_score = 0.9
        node2.confidence_level = 0.9
        node2.quantity = 200.0
        node2.origin_data = {"harvest_date": "2024-01-01"}
        node2.input_materials = [{"source_po_id": uuid4()}]
        node2.certifications = ["organic"]
        node2.geographic_coordinates = {"lat": 40.7128, "lng": -74.0060}
        
        gaps = gap_analyzer.analyze_transparency_gaps([node1, node2])
        
        # Node1 should have multiple gaps, Node2 should have none
        node1_gaps = [g for g in gaps if g.node_id == str(node1.po_id)]
        node2_gaps = [g for g in gaps if g.node_id == str(node2.po_id)]
        
        assert len(node1_gaps) > 0
        assert len(node2_gaps) == 0
        
        # Gaps should be sorted by severity
        assert gaps[0].severity.value >= gaps[-1].severity.value


class TestGapAnalyzerIntegration:
    """Integration tests for gap analyzer with real data scenarios."""
    
    def test_real_world_supply_chain_scenario(self):
        """Test gap analysis with a realistic supply chain scenario."""
        # This test demonstrates how easy it is to test complex scenarios
        # with the extracted gap analyzer
        
        mock_db = Mock()
        gap_analyzer = TransparencyGapAnalyzer(mock_db)
        
        # Create realistic supply chain nodes
        farm_node = Mock()
        farm_node.po_id = uuid4()
        farm_node.ttm_score = 0.9  # Farm has good origin data
        farm_node.ttp_score = 0.9
        farm_node.confidence_level = 0.8
        farm_node.quantity = 1000.0
        farm_node.origin_data = {"harvest_date": "2024-01-01", "farm_id": "FARM001"}
        farm_node.input_materials = []  # Farm has no input materials (correct)
        farm_node.certifications = ["organic", "fair_trade"]
        farm_node.geographic_coordinates = {"lat": 40.7128, "lng": -74.0060}
        
        processor_node = Mock()
        processor_node.po_id = uuid4()
        processor_node.ttm_score = 0.3  # Processor has poor transparency
        processor_node.ttp_score = 0.2
        processor_node.confidence_level = 0.4
        processor_node.quantity = 800.0
        processor_node.origin_data = None  # Missing origin data
        processor_node.input_materials = [{"source_po_id": farm_node.po_id}]  # Has input link
        processor_node.certifications = None  # Missing certifications
        processor_node.geographic_coordinates = None  # Missing location
        
        brand_node = Mock()
        brand_node.po_id = uuid4()
        brand_node.ttm_score = 0.1  # Brand has very poor transparency
        brand_node.ttp_score = 0.1
        brand_node.confidence_level = 0.2
        brand_node.quantity = 600.0
        brand_node.origin_data = None
        brand_node.input_materials = [{"source_po_id": processor_node.po_id}]
        brand_node.certifications = None
        brand_node.geographic_coordinates = None
        
        # Analyze gaps
        gaps = gap_analyzer.analyze_transparency_gaps([farm_node, processor_node, brand_node])
        
        # Farm should have no gaps
        farm_gaps = [g for g in gaps if g.node_id == str(farm_node.po_id)]
        assert len(farm_gaps) == 0
        
        # Processor should have multiple gaps
        processor_gaps = [g for g in gaps if g.node_id == str(processor_node.po_id)]
        assert len(processor_gaps) >= 3  # Missing origin data, certifications, geographic data
        
        # Brand should have multiple gaps
        brand_gaps = [g for g in gaps if g.node_id == str(brand_node.po_id)]
        assert len(brand_gaps) >= 3
        
        # Critical gaps should be identified
        critical_gaps = [g for g in gaps if g.severity == GapSeverity.CRITICAL]
        assert len(critical_gaps) > 0
        
        # Verify gap types
        gap_types = {g.gap_type for g in gaps}
        assert GapType.MISSING_ORIGIN_DATA in gap_types
        assert GapType.INCOMPLETE_CERTIFICATIONS in gap_types
        assert GapType.MISSING_GEOGRAPHIC_DATA in gap_types


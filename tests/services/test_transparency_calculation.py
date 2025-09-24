"""
Tests for Transparency Calculation Service

These tests focus on complex algorithmic calculations:
- Complex SQL queries with business logic
- Sophisticated algorithms for transparency scoring
- Supply chain degradation calculations
- Data transformation and analysis
"""
import pytest
from unittest.mock import Mock, patch
from uuid import uuid4
from datetime import datetime

from app.services.transparency_calculation import (
    TransparencyCalculationService,
    TransparencyScore
)


class TestTransparencyCalculationService:
    """Test class for transparency calculation service."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_db = Mock()
        self.service = TransparencyCalculationService(self.mock_db)
        self.company_id = uuid4()
    
    def test_mark_for_recalculation_success(self):
        """Test marking PO for recalculation."""
        
        # Arrange
        po_id = uuid4()
        mock_po = Mock()
        mock_po.transparency_needs_recalc = False
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_po
        
        # Act
        self.service.mark_for_recalculation(po_id)
        
        # Assert
        assert mock_po.transparency_needs_recalc == True
        self.mock_db.query.assert_called_once()
    
    def test_mark_for_recalculation_po_not_found(self):
        """Test marking non-existent PO for recalculation."""
        
        # Arrange
        po_id = uuid4()
        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Act
        self.service.mark_for_recalculation(po_id)
        
        # Assert - should not raise error, just do nothing
        self.mock_db.query.assert_called_once()
    
    def test_calculate_supply_chain_transparency_success(self):
        """Test successful transparency calculation."""
        
        # Arrange
        mock_data = {
            'fulfillment_score': 0.8,
            'traceability_score': 0.7,
            'total_pos': 10,
            'confirmed_pos': 8,
            'confirmation_rate': 0.8
        }
        
        with patch.object(self.service, '_execute_complex_transparency_query') as mock_query, \
             patch.object(self.service, '_calculate_mill_transparency_score') as mock_mill, \
             patch.object(self.service, '_calculate_plantation_transparency_score') as mock_plantation, \
             patch.object(self.service, '_apply_supply_chain_degradation') as mock_degradation:
            
            mock_query.return_value = mock_data
            mock_mill.return_value = 0.75
            mock_plantation.return_value = 0.65
            mock_degradation.return_value = {
                'mill': 0.71,
                'plantation': 0.59,
                'overall': 0.66
            }
            
            # Act
            result = self.service.calculate_supply_chain_transparency(self.company_id)
            
            # Assert
            assert isinstance(result, TransparencyScore)
            assert result.company_id == self.company_id
            assert result.mill_percentage == 0.71
            assert result.plantation_percentage == 0.59
            assert result.overall_score == 0.66
            assert isinstance(result.calculated_at, datetime)
    
    def test_calculate_supply_chain_transparency_no_data(self):
        """Test transparency calculation with no data."""
        
        # Arrange
        mock_data = {
            'fulfillment_score': 0.0,
            'traceability_score': 0.0,
            'total_pos': 0,
            'confirmed_pos': 0,
            'confirmation_rate': 0.0
        }
        
        with patch.object(self.service, '_execute_complex_transparency_query') as mock_query, \
             patch.object(self.service, '_calculate_mill_transparency_score') as mock_mill, \
             patch.object(self.service, '_calculate_plantation_transparency_score') as mock_plantation, \
             patch.object(self.service, '_apply_supply_chain_degradation') as mock_degradation:
            
            mock_query.return_value = mock_data
            mock_mill.return_value = 0.0
            mock_plantation.return_value = 0.0
            mock_degradation.return_value = {
                'mill': 0.0,
                'plantation': 0.0,
                'overall': 0.0
            }
            
            # Act
            result = self.service.calculate_supply_chain_transparency(self.company_id)
            
            # Assert
            assert result.overall_score == 0.0
            assert result.mill_percentage == 0.0
            assert result.plantation_percentage == 0.0
    
    def test_execute_complex_transparency_query_success(self):
        """Test complex transparency query execution."""
        
        # Arrange
        mock_result = Mock()
        mock_result.avg_fulfillment = 0.8
        mock_result.avg_traceability = 0.7
        mock_result.total_pos = 10
        mock_result.confirmed_pos = 8
        mock_result.confirmation_rate = 0.8
        
        self.mock_db.execute.return_value.fetchone.return_value = mock_result
        
        # Act
        result = self.service._execute_complex_transparency_query(self.company_id)
        
        # Assert
        assert result['fulfillment_score'] == 0.8
        assert result['traceability_score'] == 0.7
        assert result['total_pos'] == 10
        assert result['confirmed_pos'] == 8
        assert result['confirmation_rate'] == 0.8
    
    def test_execute_complex_transparency_query_no_data(self):
        """Test complex transparency query with no results."""
        
        # Arrange
        self.mock_db.execute.return_value.fetchone.return_value = None
        
        # Act
        result = self.service._execute_complex_transparency_query(self.company_id)
        
        # Assert
        assert result['fulfillment_score'] == 0.0
        assert result['traceability_score'] == 0.0
        assert result['total_pos'] == 0
        assert result['confirmed_pos'] == 0
        assert result['confirmation_rate'] == 0.0
    
    def test_calculate_mill_transparency_score(self):
        """Test mill transparency score calculation algorithm."""
        
        # Arrange
        data = {
            'fulfillment_score': 0.8,
            'traceability_score': 0.7,
            'total_pos': 10,
            'confirmed_pos': 8,
            'confirmation_rate': 0.8
        }
        
        # Act
        result = self.service._calculate_mill_transparency_score(data)
        
        # Assert
        # Base score: 0.8 * 0.4 + 0.7 * 0.6 = 0.32 + 0.42 = 0.74
        # Volume factor: min(1.0, 10/10) = 1.0
        # Confirmation bonus: 0.8 * 0.1 = 0.08
        # Final: (0.74 * 1.0) + 0.08 = 0.82
        expected = (0.74 * 1.0) + 0.08
        assert abs(result - expected) < 0.01
    
    def test_calculate_plantation_transparency_score(self):
        """Test plantation transparency score calculation algorithm."""
        
        # Arrange
        data = {
            'fulfillment_score': 0.8,
            'traceability_score': 0.7,
            'total_pos': 10,
            'confirmed_pos': 8,
            'confirmation_rate': 0.8
        }
        
        # Act
        result = self.service._calculate_plantation_transparency_score(data)
        
        # Assert
        # Base score: 0.7 * 0.7 + 0.8 * 0.3 = 0.49 + 0.24 = 0.73
        # Depth factor: 0.8
        # Certification bonus: 0.1
        # Final: (0.73 * 0.8) + 0.1 = 0.684
        expected = (0.73 * 0.8) + 0.1
        assert abs(result - expected) < 0.01
    
    def test_apply_supply_chain_degradation(self):
        """Test supply chain degradation algorithm."""
        
        # Arrange
        mill_score = 0.8
        plantation_score = 0.7
        self.service.degradation_factor = 0.95
        
        # Act
        result = self.service._apply_supply_chain_degradation(mill_score, plantation_score)
        
        # Assert
        # Mill degraded: 0.8 * 0.95 = 0.76
        # Plantation degraded: 0.7 * (0.95^2) = 0.7 * 0.9025 = 0.63175
        # Overall: (0.76 * 0.6) + (0.63175 * 0.4) = 0.456 + 0.2527 = 0.7087
        expected_mill = 0.8 * 0.95
        expected_plantation = 0.7 * (0.95 ** 2)
        expected_overall = (expected_mill * 0.6) + (expected_plantation * 0.4)
        
        assert abs(result['mill'] - expected_mill) < 0.01
        assert abs(result['plantation'] - expected_plantation) < 0.01
        assert abs(result['overall'] - expected_overall) < 0.01
    
    def test_get_transparency_insights_low_score(self):
        """Test transparency insights generation for low scores."""
        
        # Arrange
        mock_data = {
            'fulfillment_score': 0.3,
            'traceability_score': 0.4,
            'total_pos': 2,
            'confirmed_pos': 1,
            'confirmation_rate': 0.5
        }
        
        mock_score = TransparencyScore(
            company_id=self.company_id,
            mill_percentage=0.3,
            plantation_percentage=0.2,
            overall_score=0.25,
            calculated_at=datetime.utcnow()
        )
        
        with patch.object(self.service, '_execute_complex_transparency_query') as mock_query, \
             patch.object(self.service, 'calculate_supply_chain_transparency') as mock_calc, \
             patch.object(self.service, '_generate_recommendations') as mock_recommendations:
            
            mock_query.return_value = mock_data
            mock_calc.return_value = mock_score
            mock_recommendations.return_value = ["Improve traceability", "Increase volume"]
            
            # Act
            result = self.service.get_transparency_insights(self.company_id)
            
            # Assert
            assert 'score' in result
            assert 'insights' in result
            assert 'recommendations' in result
            assert len(result['insights']) > 0  # Should have insights for low scores
            assert result['recommendations'] == ["Improve traceability", "Increase volume"]
    
    def test_generate_recommendations(self):
        """Test recommendation generation."""
        
        # Arrange
        score = TransparencyScore(
            company_id=self.company_id,
            mill_percentage=0.6,  # Below threshold
            plantation_percentage=0.4,  # Below threshold
            overall_score=0.5,
            calculated_at=datetime.utcnow()
        )
        
        data = {
            'total_pos': 3,  # Below threshold
            'confirmed_pos': 2,
            'confirmation_rate': 0.67
        }
        
        # Act
        result = self.service._generate_recommendations(score, data)
        
        # Assert
        assert len(result) > 0
        assert any("mill-level transparency" in rec for rec in result)
        assert any("plantation traceability" in rec for rec in result)
        assert any("transaction volume" in rec for rec in result)

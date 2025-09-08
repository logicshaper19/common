"""
Confidence calculation for transparency scores.
"""
from typing import Dict, Any
from ..domain.models import TransparencyNode
from app.core.logging import get_logger

logger = get_logger(__name__)


class ConfidenceCalculator:
    """Calculates confidence levels for transparency scores."""
    
    def __init__(self):
        """Initialize confidence calculator."""
        self.confidence_weights = {
            'data_completeness': 0.30,
            'data_freshness': 0.20,
            'verification_status': 0.25,
            'source_reliability': 0.25
        }
    
    def calculate_confidence(self, node: TransparencyNode) -> float:
        """
        Calculate confidence level for a transparency node.
        
        Args:
            node: TransparencyNode to calculate confidence for
            
        Returns:
            Confidence level between 0.0 and 1.0
        """
        confidence_components = {}
        
        # Data completeness component
        confidence_components['data_completeness'] = node.data_completeness_score
        
        # Data freshness component (simplified - would use actual timestamps)
        confidence_components['data_freshness'] = self._calculate_data_freshness(node)
        
        # Verification status component
        confidence_components['verification_status'] = self._calculate_verification_status(node)
        
        # Source reliability component
        confidence_components['source_reliability'] = self._calculate_source_reliability(node)
        
        # Calculate weighted confidence
        confidence = sum(
            confidence_components[component] * self.confidence_weights[component]
            for component in self.confidence_weights
        )
        
        # Apply degradation factor
        confidence *= node.degradation_factor
        
        return min(1.0, max(0.0, confidence))
    
    def _calculate_data_freshness(self, node: TransparencyNode) -> float:
        """Calculate data freshness score."""
        # Simplified implementation - in practice would check actual timestamps
        if node.visited_at:
            return 0.9  # Recent data
        return 0.5  # Unknown freshness
    
    def _calculate_verification_status(self, node: TransparencyNode) -> float:
        """Calculate verification status score."""
        score = 0.0
        
        # Base score for having any data
        if node.has_origin_data:
            score += 0.3
        
        # Bonus for certifications (implies third-party verification)
        if node.has_certifications:
            score += 0.4
            
            # Extra bonus for high-value certifications
            if node.high_value_cert_count > 0:
                score += 0.3
        
        # Bonus for geographic coordinates (verifiable data)
        if node.has_geographic_coordinates:
            score += 0.2
        
        return min(1.0, score)
    
    def _calculate_source_reliability(self, node: TransparencyNode) -> float:
        """Calculate source reliability score."""
        # Simplified implementation based on company type and certifications
        base_reliability = {
            'originator': 0.8,
            'processor': 0.7,
            'brand': 0.6,
            'trader': 0.5
        }.get(node.company_type, 0.5)
        
        # Bonus for certifications (indicates reliable processes)
        cert_bonus = min(0.2, node.certification_count * 0.05)
        
        return min(1.0, base_reliability + cert_bonus)

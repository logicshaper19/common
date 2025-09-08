"""
Score calculation for transparency metrics.
"""
from typing import Dict, Any, List
from decimal import Decimal

from ..domain.models import TransparencyNode
from ..domain.enums import CertificationTier, DataCompletenessLevel
from app.core.logging import get_logger

logger = get_logger(__name__)


class ScoreCalculator:
    """Calculates transparency scores for nodes."""
    
    def __init__(self):
        """Initialize score calculator with weights and thresholds."""
        # TTM (Transparency to Market) weights
        self.ttm_weights = {
            'origin_data': 0.25,
            'geographic_coordinates': 0.20,
            'certifications': 0.30,
            'data_completeness': 0.25
        }
        
        # TTP (Transparency to Producer) weights  
        self.ttp_weights = {
            'input_traceability': 0.40,
            'supplier_verification': 0.30,
            'process_documentation': 0.30
        }
        
        # Certification scoring
        self.certification_scores = {
            CertificationTier.BASIC: 0.25,
            CertificationTier.STANDARD: 0.50,
            CertificationTier.PREMIUM: 0.80,
            CertificationTier.ELITE: 1.00
        }
        
        # Data completeness thresholds
        self.completeness_thresholds = {
            DataCompletenessLevel.MINIMAL: 0.25,
            DataCompletenessLevel.PARTIAL: 0.50,
            DataCompletenessLevel.SUBSTANTIAL: 0.75,
            DataCompletenessLevel.COMPLETE: 1.00
        }
    
    def calculate_base_scores(self, node: TransparencyNode) -> None:
        """
        Calculate base TTM and TTP scores for a node.
        
        Args:
            node: TransparencyNode to calculate scores for
        """
        # Calculate TTM score
        node.base_ttm_score = self._calculate_ttm_score(node)
        
        # Calculate TTP score
        node.base_ttp_score = self._calculate_ttp_score(node)
        
        logger.debug(
            f"Calculated base scores for PO {node.po_id}: "
            f"TTM={node.base_ttm_score:.3f}, TTP={node.base_ttp_score:.3f}"
        )
    
    def _calculate_ttm_score(self, node: TransparencyNode) -> float:
        """Calculate Transparency to Market score."""
        score_components = {}
        
        # Origin data component
        score_components['origin_data'] = 1.0 if node.has_origin_data else 0.0
        
        # Geographic coordinates component
        score_components['geographic_coordinates'] = 1.0 if node.has_geographic_coordinates else 0.0
        
        # Certifications component
        score_components['certifications'] = self._calculate_certification_score(node)
        
        # Data completeness component
        score_components['data_completeness'] = node.data_completeness_score
        
        # Calculate weighted sum
        ttm_score = sum(
            score_components[component] * self.ttm_weights[component]
            for component in self.ttm_weights
        )
        
        return min(1.0, max(0.0, ttm_score))
    
    def _calculate_ttp_score(self, node: TransparencyNode) -> float:
        """Calculate Transparency to Producer score."""
        score_components = {}
        
        # Input traceability component
        score_components['input_traceability'] = self._calculate_input_traceability_score(node)
        
        # Supplier verification component
        score_components['supplier_verification'] = self._calculate_supplier_verification_score(node)
        
        # Process documentation component
        score_components['process_documentation'] = self._calculate_process_documentation_score(node)
        
        # Calculate weighted sum
        ttp_score = sum(
            score_components[component] * self.ttp_weights[component]
            for component in self.ttp_weights
        )
        
        return min(1.0, max(0.0, ttp_score))
    
    def _calculate_certification_score(self, node: TransparencyNode) -> float:
        """Calculate certification component score."""
        if not node.has_certifications:
            return 0.0
        
        # Base score from certification tier
        tier_score = self.certification_scores.get(node.certification_tier, 0.0)
        
        # Bonus for multiple certifications
        cert_bonus = min(0.2, node.certification_count * 0.05)
        
        # Extra bonus for high-value certifications
        high_value_bonus = min(0.3, node.high_value_cert_count * 0.1)
        
        total_score = tier_score + cert_bonus + high_value_bonus
        return min(1.0, total_score)
    
    def _calculate_input_traceability_score(self, node: TransparencyNode) -> float:
        """Calculate input traceability score."""
        if not node.input_materials:
            # No input materials means this is likely an originator
            return 1.0 if node.company_type == 'originator' else 0.0
        
        # Calculate percentage of traced inputs
        total_materials = len(node.input_materials)
        traced_materials = sum(
            1 for material in node.input_materials
            if material.get('source_po_id') and material.get('traceability_verified', False)
        )
        
        if total_materials == 0:
            return 0.0
        
        traceability_ratio = traced_materials / total_materials
        
        # Apply quality multiplier based on traceability depth
        quality_multiplier = self._calculate_traceability_quality(node.input_materials)
        
        return traceability_ratio * quality_multiplier
    
    def _calculate_supplier_verification_score(self, node: TransparencyNode) -> float:
        """Calculate supplier verification score."""
        if not node.input_materials:
            return 1.0 if node.company_type == 'originator' else 0.5
        
        # Check verification status of suppliers
        verified_suppliers = sum(
            1 for material in node.input_materials
            if material.get('supplier_verified', False)
        )
        
        total_suppliers = len(set(
            material.get('supplier_company_id')
            for material in node.input_materials
            if material.get('supplier_company_id')
        ))
        
        if total_suppliers == 0:
            return 0.0
        
        verification_ratio = verified_suppliers / total_suppliers
        
        # Bonus for certification alignment
        cert_alignment_bonus = self._calculate_certification_alignment_bonus(node)
        
        return min(1.0, verification_ratio + cert_alignment_bonus)
    
    def _calculate_process_documentation_score(self, node: TransparencyNode) -> float:
        """Calculate process documentation score."""
        score = 0.0
        
        # Base score from data completeness
        score += node.data_completeness_score * 0.6
        
        # Bonus for specific documentation types
        if node.has_origin_data:
            score += 0.2
        
        if node.has_geographic_coordinates:
            score += 0.1
        
        if node.has_certifications:
            score += 0.1
        
        return min(1.0, score)
    
    def _calculate_traceability_quality(self, input_materials: List[Dict[str, Any]]) -> float:
        """Calculate quality multiplier for traceability."""
        if not input_materials:
            return 1.0
        
        quality_scores = []
        
        for material in input_materials:
            material_quality = 0.5  # Base quality
            
            # Bonus for detailed material information
            if material.get('material_type'):
                material_quality += 0.1
            
            if material.get('percentage_contribution'):
                material_quality += 0.1
            
            if material.get('quality_grade'):
                material_quality += 0.1
            
            if material.get('harvest_date') or material.get('production_date'):
                material_quality += 0.1
            
            if material.get('certifications'):
                material_quality += 0.1
            
            quality_scores.append(min(1.0, material_quality))
        
        return sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
    
    def _calculate_certification_alignment_bonus(self, node: TransparencyNode) -> float:
        """Calculate bonus for certification alignment across supply chain."""
        if not node.input_materials or not node.has_certifications:
            return 0.0
        
        # Check if input materials have compatible certifications
        aligned_materials = sum(
            1 for material in node.input_materials
            if self._has_compatible_certifications(material, node)
        )
        
        total_materials = len(node.input_materials)
        alignment_ratio = aligned_materials / total_materials if total_materials > 0 else 0.0
        
        return alignment_ratio * 0.2  # Max 20% bonus
    
    def _has_compatible_certifications(
        self, 
        material: Dict[str, Any], 
        node: TransparencyNode
    ) -> bool:
        """Check if material has certifications compatible with node."""
        material_certs = set(material.get('certifications', []))
        
        # For simplicity, assume compatibility if there's any overlap
        # In practice, this would involve more sophisticated certification mapping
        return len(material_certs) > 0 and node.has_certifications
    
    def apply_degradation_factor(self, node: TransparencyNode) -> None:
        """Apply degradation factor to scores."""
        if node.degradation_factor < 1.0:
            node.base_ttm_score *= node.degradation_factor
            node.base_ttp_score *= node.degradation_factor
            
            logger.debug(
                f"Applied degradation factor {node.degradation_factor:.3f} to PO {node.po_id}"
            )

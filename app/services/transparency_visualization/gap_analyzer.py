"""
Transparency gap analysis engine.

This service is responsible for identifying and analyzing transparency gaps
in the supply chain, determining their severity and impact.
"""
from typing import List, Dict, Any, Tuple
from uuid import UUID
from sqlalchemy.orm import Session

from app.services.transparency_engine.domain.models import TransparencyNode
from app.core.logging import get_logger
from .models.gap_models import GapType, GapSeverity, GapAnalysis

logger = get_logger(__name__)


class TransparencyGapAnalyzer:
    """
    Analyzes transparency gaps and identifies improvement opportunities.
    
    This service focuses solely on gap analysis logic, making it:
    - Highly testable (no visualization dependencies)
    - Reusable across different visualization contexts
    - Easy to extend with new gap types
    """
    
    def __init__(self, db: Session):
        self.db = db
        
        # Gap analysis thresholds
        self.TRANSPARENCY_THRESHOLDS = {
            "critical": 0.3,
            "high": 0.5,
            "medium": 0.7,
            "good": 0.85
        }
        
        # Gap type configurations
        self.GAP_TYPE_CONFIGS = {
            GapType.MISSING_ORIGIN_DATA: {
                "weight": 0.8,
                "ttm_impact": 0.4,
                "ttp_impact": 0.8
            },
            GapType.MISSING_INPUT_MATERIAL: {
                "weight": 0.7,
                "ttm_impact": 0.7,
                "ttp_impact": 0.5
            },
            GapType.LOW_CONFIDENCE: {
                "weight": 0.6,
                "ttm_impact": 0.3,
                "ttp_impact": 0.3
            },
            GapType.INCOMPLETE_CERTIFICATIONS: {
                "weight": 0.4,
                "ttm_impact": 0.2,
                "ttp_impact": 0.2
            },
            GapType.MISSING_GEOGRAPHIC_DATA: {
                "weight": 0.5,
                "ttm_impact": 0.3,
                "ttp_impact": 0.4
            },
            GapType.WEAK_TRACEABILITY_LINK: {
                "weight": 0.6,
                "ttm_impact": 0.5,
                "ttp_impact": 0.4
            }
        }
    
    def analyze_transparency_gaps(
        self, 
        transparency_nodes: List[TransparencyNode]
    ) -> List[GapAnalysis]:
        """
        Analyze transparency gaps across all nodes.
        
        Args:
            transparency_nodes: List of transparency nodes to analyze
            
        Returns:
            List of gap analysis results
        """
        gaps = []
        
        for node in transparency_nodes:
            node_gaps = self._analyze_node_gaps(node)
            gaps.extend(node_gaps)
        
        # Sort by severity and impact
        gaps.sort(key=lambda g: (g.severity.value, g.impact_score), reverse=True)
        
        logger.info(f"Analyzed {len(transparency_nodes)} nodes, found {len(gaps)} gaps")
        return gaps
    
    def _analyze_node_gaps(self, node: TransparencyNode) -> List[GapAnalysis]:
        """Analyze gaps for a single node."""
        gaps = []
        
        # Check for missing origin data
        if not self._has_origin_data(node):
            gaps.append(self._create_gap_analysis(
                node, GapType.MISSING_ORIGIN_DATA, "Missing origin data"
            ))
        
        # Check for missing input materials
        if not self._has_input_materials(node):
            gaps.append(self._create_gap_analysis(
                node, GapType.MISSING_INPUT_MATERIAL, "Missing input material links"
            ))
        
        # Check confidence level
        if node.confidence_level < 0.7:
            gaps.append(self._create_gap_analysis(
                node, GapType.LOW_CONFIDENCE, f"Low confidence level: {node.confidence_level:.2f}"
            ))
        
        # Check for incomplete certifications
        if not self._has_complete_certifications(node):
            gaps.append(self._create_gap_analysis(
                node, GapType.INCOMPLETE_CERTIFICATIONS, "Incomplete sustainability certifications"
            ))
        
        # Check for missing geographic data
        if not self._has_geographic_data(node):
            gaps.append(self._create_gap_analysis(
                node, GapType.MISSING_GEOGRAPHIC_DATA, "Missing geographic coordinates"
            ))
        
        return gaps
    
    def _create_gap_analysis(
        self, 
        node: TransparencyNode, 
        gap_type: GapType, 
        description: str
    ) -> GapAnalysis:
        """Create a gap analysis result."""
        severity = self._determine_gap_severity(node, gap_type)
        impact_score = self._calculate_gap_impact(node, gap_type)
        improvement_potential = self._calculate_improvement_potential(node, gap_type)
        
        return GapAnalysis(
            gap_id=f"{node.po_id}_{gap_type.value}",
            node_id=str(node.po_id),
            gap_type=gap_type,
            severity=severity,
            description=description,
            impact_score=impact_score,
            improvement_potential=improvement_potential,
            affected_metrics=self._get_affected_metrics(gap_type),
            suggested_actions=self._get_suggested_actions(gap_type)
        )
    
    def _determine_gap_severity(self, node: TransparencyNode, gap_type: GapType) -> GapSeverity:
        """Determine the severity of a gap based on node context."""
        config = self.GAP_TYPE_CONFIGS[gap_type]
        weight = config["weight"]
        
        # Base severity on transparency scores and gap weight
        min_score = min(node.ttm_score, node.ttp_score)
        
        if min_score < 0.3 or weight > 0.7:
            return GapSeverity.CRITICAL
        elif min_score < 0.5 or weight > 0.6:
            return GapSeverity.HIGH
        elif min_score < 0.7 or weight > 0.4:
            return GapSeverity.MEDIUM
        else:
            return GapSeverity.LOW
    
    def _calculate_gap_impact(self, node: TransparencyNode, gap_type: GapType) -> float:
        """Calculate the impact score of a gap."""
        config = self.GAP_TYPE_CONFIGS[gap_type]
        
        # Weight by node quantity and gap type impact
        quantity_factor = min(node.quantity / 1000.0, 1.0)  # Normalize quantity
        gap_weight = config["weight"]
        
        return quantity_factor * gap_weight * 100  # Scale to 0-100
    
    def _calculate_improvement_potential(
        self, 
        node: TransparencyNode, 
        gap_type: GapType
    ) -> Tuple[float, float]:
        """Calculate improvement potential for TTM and TTP scores."""
        config = self.GAP_TYPE_CONFIGS[gap_type]
        
        ttm_potential = config["ttm_impact"] * (1.0 - node.ttm_score)
        ttp_potential = config["ttp_impact"] * (1.0 - node.ttp_score)
        
        return ttm_potential, ttp_potential
    
    def _has_origin_data(self, node: TransparencyNode) -> bool:
        """Check if node has origin data."""
        return (
            hasattr(node, 'origin_data') and 
            node.origin_data is not None and
            len(node.origin_data) > 0
        )
    
    def _has_input_materials(self, node: TransparencyNode) -> bool:
        """Check if node has input materials linked."""
        return (
            hasattr(node, 'input_materials') and 
            node.input_materials is not None and
            len(node.input_materials) > 0
        )
    
    def _has_complete_certifications(self, node: TransparencyNode) -> bool:
        """Check if node has complete certifications."""
        return (
            hasattr(node, 'certifications') and 
            node.certifications is not None and
            len(node.certifications) > 0
        )
    
    def _has_geographic_data(self, node: TransparencyNode) -> bool:
        """Check if node has geographic data."""
        return (
            hasattr(node, 'geographic_coordinates') and 
            node.geographic_coordinates is not None
        )
    
    def _get_affected_metrics(self, gap_type: GapType) -> List[str]:
        """Get list of metrics affected by this gap type."""
        config = self.GAP_TYPE_CONFIGS[gap_type]
        metrics = []
        
        if config["ttm_impact"] > 0:
            metrics.append("ttm_score")
        if config["ttp_impact"] > 0:
            metrics.append("ttp_score")
        
        return metrics
    
    def _get_suggested_actions(self, gap_type: GapType) -> List[str]:
        """Get suggested actions for addressing this gap type."""
        action_map = {
            GapType.MISSING_ORIGIN_DATA: [
                "Contact suppliers to provide harvest dates",
                "Collect farm identification information",
                "Verify geographic coordinates"
            ],
            GapType.MISSING_INPUT_MATERIAL: [
                "Identify input material sources",
                "Establish supplier relationships",
                "Create purchase order linkages"
            ],
            GapType.LOW_CONFIDENCE: [
                "Verify data sources",
                "Request additional documentation",
                "Implement data validation processes"
            ],
            GapType.INCOMPLETE_CERTIFICATIONS: [
                "Request certification documents",
                "Verify certification validity",
                "Update certification records"
            ],
            GapType.MISSING_GEOGRAPHIC_DATA: [
                "Collect GPS coordinates",
                "Verify location accuracy",
                "Update geographic records"
            ],
            GapType.WEAK_TRACEABILITY_LINK: [
                "Strengthen supplier relationships",
                "Improve data collection processes",
                "Implement verification protocols"
            ]
        }
        
        return action_map.get(gap_type, ["Review and improve data quality"])


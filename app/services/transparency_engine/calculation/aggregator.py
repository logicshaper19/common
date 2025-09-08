"""
Score aggregation for transparency calculations.
"""
from typing import List, Dict, Any
from ..domain.models import TransparencyPath, TransparencyNode
from app.core.logging import get_logger

logger = get_logger(__name__)


class ScoreAggregator:
    """Aggregates transparency scores across paths and nodes."""
    
    def select_primary_path(self, paths: List[TransparencyPath]) -> TransparencyPath:
        """
        Select the primary path for transparency calculation.
        
        Args:
            paths: List of transparency paths
            
        Returns:
            Primary path to use for final scoring
        """
        if not paths:
            return TransparencyPath()
        
        if len(paths) == 1:
            return paths[0]
        
        # Score each path and select the best one
        path_scores = []
        for path in paths:
            score = self._calculate_path_score(path)
            path_scores.append((score, path))
        
        # Sort by score (descending) and select the best
        path_scores.sort(key=lambda x: x[0], reverse=True)
        
        primary_path = path_scores[0][1]
        logger.debug(f"Selected primary path with score {path_scores[0][0]:.3f}")
        
        return primary_path
    
    def aggregate_path_scores(self, path: TransparencyPath) -> Dict[str, float]:
        """
        Aggregate scores across all nodes in a path.
        
        Args:
            path: TransparencyPath to aggregate
            
        Returns:
            Dictionary with aggregated scores
        """
        if not path.nodes:
            return {
                'ttm_score': 0.0,
                'ttp_score': 0.0,
                'confidence_level': 0.0
            }
        
        # Calculate weighted averages based on node importance
        total_weight = 0.0
        weighted_ttm = 0.0
        weighted_ttp = 0.0
        weighted_confidence = 0.0
        
        for i, node in enumerate(path.nodes):
            # Calculate node weight (closer to end of chain = higher weight)
            node_weight = self._calculate_node_weight(node, i, len(path.nodes))
            
            # Update weighted scores
            weighted_ttm += node.base_ttm_score * node_weight
            weighted_ttp += node.base_ttp_score * node_weight
            weighted_confidence += node.confidence_level * node_weight
            total_weight += node_weight
        
        # Normalize by total weight
        if total_weight > 0:
            final_ttm = weighted_ttm / total_weight
            final_ttp = weighted_ttp / total_weight
            final_confidence = weighted_confidence / total_weight
        else:
            final_ttm = final_ttp = final_confidence = 0.0
        
        # Apply path-level adjustments
        final_ttm = self._apply_path_adjustments(final_ttm, path, 'ttm')
        final_ttp = self._apply_path_adjustments(final_ttp, path, 'ttp')
        
        # Update path scores
        path.path_ttm_score = final_ttm
        path.path_ttp_score = final_ttp
        path.path_confidence = final_confidence
        
        return {
            'ttm_score': final_ttm,
            'ttp_score': final_ttp,
            'confidence_level': final_confidence
        }
    
    def _calculate_path_score(self, path: TransparencyPath) -> float:
        """Calculate overall score for a path to determine priority."""
        if not path.nodes:
            return 0.0
        
        # Base score from average node scores
        avg_ttm = sum(node.base_ttm_score for node in path.nodes) / len(path.nodes)
        avg_ttp = sum(node.base_ttp_score for node in path.nodes) / len(path.nodes)
        avg_confidence = sum(node.confidence_level for node in path.nodes) / len(path.nodes)
        
        base_score = (avg_ttm + avg_ttp) / 2
        
        # Adjustments
        confidence_multiplier = 0.5 + (avg_confidence * 0.5)  # 0.5 to 1.0
        
        # Penalty for cycles
        cycle_penalty = 0.9 if path.has_cycles else 1.0
        
        # Bonus for path completeness
        completeness_bonus = min(1.2, 1.0 + (len(path.nodes) * 0.02))
        
        final_score = base_score * confidence_multiplier * cycle_penalty * completeness_bonus
        
        return min(1.0, final_score)
    
    def _calculate_node_weight(self, node: TransparencyNode, position: int, total_nodes: int) -> float:
        """
        Calculate weight for a node in the aggregation.
        
        Args:
            node: TransparencyNode
            position: Position in the path (0 = first)
            total_nodes: Total number of nodes in path
            
        Returns:
            Weight for this node
        """
        # Base weight increases towards the end of the chain
        position_weight = 0.5 + (position / max(1, total_nodes - 1)) * 0.5
        
        # Adjust based on node characteristics
        quality_multiplier = 1.0
        
        # Higher weight for nodes with more complete data
        if node.data_completeness_score > 0.8:
            quality_multiplier *= 1.2
        elif node.data_completeness_score < 0.3:
            quality_multiplier *= 0.8
        
        # Higher weight for certified nodes
        if node.has_certifications:
            quality_multiplier *= 1.1
        
        # Lower weight for circular nodes
        if node.is_circular:
            quality_multiplier *= 0.7
        
        return position_weight * quality_multiplier
    
    def _apply_path_adjustments(
        self, 
        score: float, 
        path: TransparencyPath, 
        score_type: str
    ) -> float:
        """Apply path-level adjustments to scores."""
        adjusted_score = score
        
        # Penalty for cycles
        if path.has_cycles:
            cycle_penalty = 0.95 - (len(path.cycle_break_points) * 0.05)
            adjusted_score *= max(0.7, cycle_penalty)
        
        # Bonus for complete traceability
        if len(path.nodes) > 3:  # Deep supply chain
            completeness_bonus = 1.05
            adjusted_score *= completeness_bonus
        
        # Score-type specific adjustments
        if score_type == 'ttm':
            # TTM benefits more from end-of-chain data quality
            if path.nodes:
                end_node = path.nodes[-1]
                if end_node.has_origin_data and end_node.has_geographic_coordinates:
                    adjusted_score *= 1.1
        
        elif score_type == 'ttp':
            # TTP benefits more from input material traceability
            traceable_nodes = sum(
                1 for node in path.nodes 
                if node.input_materials or node.company_type == 'originator'
            )
            if traceable_nodes > len(path.nodes) * 0.8:
                adjusted_score *= 1.1
        
        return min(1.0, max(0.0, adjusted_score))

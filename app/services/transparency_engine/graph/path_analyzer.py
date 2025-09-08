"""
Path analysis for transparency calculations.
"""
from typing import List, Dict, Any, Optional
from ..domain.models import TransparencyPath, TransparencyNode
from app.core.logging import get_logger

logger = get_logger(__name__)


class PathAnalyzer:
    """Analyzes transparency paths for insights and optimization."""
    
    def analyze_path_quality(self, path: TransparencyPath) -> Dict[str, Any]:
        """
        Analyze the quality characteristics of a transparency path.
        
        Args:
            path: TransparencyPath to analyze
            
        Returns:
            Dictionary with path quality metrics
        """
        if not path.nodes:
            return {
                'quality_score': 0.0,
                'completeness': 0.0,
                'reliability': 0.0,
                'issues': ['Empty path']
            }
        
        analysis = {
            'quality_score': 0.0,
            'completeness': 0.0,
            'reliability': 0.0,
            'depth': len(path.nodes),
            'has_cycles': path.has_cycles,
            'cycle_count': len(path.cycle_break_points),
            'issues': [],
            'strengths': [],
            'recommendations': []
        }
        
        # Calculate completeness
        analysis['completeness'] = self._calculate_path_completeness(path)
        
        # Calculate reliability
        analysis['reliability'] = self._calculate_path_reliability(path)
        
        # Overall quality score
        analysis['quality_score'] = (analysis['completeness'] + analysis['reliability']) / 2
        
        # Identify issues and strengths
        analysis['issues'] = self._identify_path_issues(path)
        analysis['strengths'] = self._identify_path_strengths(path)
        analysis['recommendations'] = self._generate_path_recommendations(path, analysis)
        
        return analysis
    
    def find_weakest_links(self, path: TransparencyPath, limit: int = 3) -> List[Dict[str, Any]]:
        """
        Find the weakest links in a transparency path.
        
        Args:
            path: TransparencyPath to analyze
            limit: Maximum number of weak links to return
            
        Returns:
            List of weak link analyses
        """
        if not path.nodes:
            return []
        
        # Score each node
        node_scores = []
        for i, node in enumerate(path.nodes):
            score = (node.base_ttm_score + node.base_ttp_score) / 2
            weakness_score = 1.0 - score  # Higher = weaker
            
            node_scores.append({
                'node': node,
                'position': i,
                'weakness_score': weakness_score,
                'transparency_score': score,
                'issues': self._identify_node_issues(node)
            })
        
        # Sort by weakness (highest first) and return top N
        node_scores.sort(key=lambda x: x['weakness_score'], reverse=True)
        
        return node_scores[:limit]
    
    def calculate_improvement_potential(self, path: TransparencyPath) -> Dict[str, Any]:
        """
        Calculate the improvement potential for a transparency path.
        
        Args:
            path: TransparencyPath to analyze
            
        Returns:
            Dictionary with improvement potential analysis
        """
        if not path.nodes:
            return {'total_potential': 0.0, 'improvements': []}
        
        improvements = []
        total_potential = 0.0
        
        for i, node in enumerate(path.nodes):
            node_potential = self._calculate_node_improvement_potential(node)
            if node_potential['potential'] > 0.1:  # Significant improvement possible
                improvements.append({
                    'node_position': i,
                    'po_id': str(node.po_id),
                    'po_number': node.po_number,
                    'current_score': (node.base_ttm_score + node.base_ttp_score) / 2,
                    'potential_score': node_potential['potential_score'],
                    'improvement': node_potential['potential'],
                    'actions': node_potential['actions']
                })
                total_potential += node_potential['potential']
        
        return {
            'total_potential': total_potential / len(path.nodes),
            'improvements': improvements,
            'priority_actions': self._prioritize_improvements(improvements)
        }
    
    def _calculate_path_completeness(self, path: TransparencyPath) -> float:
        """Calculate completeness score for a path."""
        if not path.nodes:
            return 0.0
        
        completeness_scores = []
        for node in path.nodes:
            node_completeness = 0.0
            
            # Data completeness
            node_completeness += node.data_completeness_score * 0.4
            
            # Origin data presence
            if node.has_origin_data:
                node_completeness += 0.2
            
            # Geographic coordinates
            if node.has_geographic_coordinates:
                node_completeness += 0.2
            
            # Certifications
            if node.has_certifications:
                node_completeness += 0.2
            
            completeness_scores.append(min(1.0, node_completeness))
        
        return sum(completeness_scores) / len(completeness_scores)
    
    def _calculate_path_reliability(self, path: TransparencyPath) -> float:
        """Calculate reliability score for a path."""
        if not path.nodes:
            return 0.0
        
        reliability_scores = []
        for node in path.nodes:
            node_reliability = node.confidence_level
            
            # Penalty for circular references
            if node.is_circular:
                node_reliability *= 0.8
            
            # Bonus for certifications (third-party verification)
            if node.has_certifications:
                node_reliability *= 1.1
            
            reliability_scores.append(min(1.0, node_reliability))
        
        # Path-level adjustments
        path_reliability = sum(reliability_scores) / len(reliability_scores)
        
        # Penalty for cycles in the path
        if path.has_cycles:
            cycle_penalty = 0.95 - (len(path.cycle_break_points) * 0.05)
            path_reliability *= max(0.7, cycle_penalty)
        
        return min(1.0, path_reliability)
    
    def _identify_path_issues(self, path: TransparencyPath) -> List[str]:
        """Identify issues in a transparency path."""
        issues = []
        
        if path.has_cycles:
            issues.append(f"Circular references detected ({len(path.cycle_break_points)} cycles)")
        
        if len(path.nodes) < 2:
            issues.append("Very short supply chain - limited traceability")
        
        # Check for data gaps
        nodes_with_poor_data = sum(
            1 for node in path.nodes if node.data_completeness_score < 0.3
        )
        if nodes_with_poor_data > len(path.nodes) * 0.5:
            issues.append("Significant data gaps throughout supply chain")
        
        # Check for low confidence
        low_confidence_nodes = sum(
            1 for node in path.nodes if node.confidence_level < 0.4
        )
        if low_confidence_nodes > len(path.nodes) * 0.3:
            issues.append("Low confidence in data quality")
        
        # Check for missing certifications
        uncertified_nodes = sum(
            1 for node in path.nodes if not node.has_certifications
        )
        if uncertified_nodes == len(path.nodes):
            issues.append("No certifications found in supply chain")
        
        return issues
    
    def _identify_path_strengths(self, path: TransparencyPath) -> List[str]:
        """Identify strengths in a transparency path."""
        strengths = []
        
        if not path.has_cycles:
            strengths.append("No circular references detected")
        
        # Check for high data completeness
        complete_nodes = sum(
            1 for node in path.nodes if node.data_completeness_score > 0.8
        )
        if complete_nodes > len(path.nodes) * 0.7:
            strengths.append("High data completeness throughout supply chain")
        
        # Check for certifications
        certified_nodes = sum(
            1 for node in path.nodes if node.has_certifications
        )
        if certified_nodes > len(path.nodes) * 0.5:
            strengths.append("Good certification coverage")
        
        # Check for geographic data
        geo_nodes = sum(
            1 for node in path.nodes if node.has_geographic_coordinates
        )
        if geo_nodes > len(path.nodes) * 0.6:
            strengths.append("Good geographic traceability")
        
        # Check for deep traceability
        if len(path.nodes) > 4:
            strengths.append("Deep supply chain traceability")
        
        return strengths
    
    def _generate_path_recommendations(
        self, 
        path: TransparencyPath, 
        analysis: Dict[str, Any]
    ) -> List[str]:
        """Generate recommendations for improving a path."""
        recommendations = []
        
        if analysis['completeness'] < 0.6:
            recommendations.append("Focus on improving data completeness across all suppliers")
        
        if analysis['reliability'] < 0.6:
            recommendations.append("Implement data verification processes")
        
        if path.has_cycles:
            recommendations.append("Resolve circular references in supply chain")
        
        # Specific recommendations based on issues
        for issue in analysis['issues']:
            if "data gaps" in issue:
                recommendations.append("Implement supplier data collection program")
            elif "certifications" in issue:
                recommendations.append("Encourage suppliers to obtain relevant certifications")
            elif "confidence" in issue:
                recommendations.append("Establish data verification and audit processes")
        
        return recommendations
    
    def _identify_node_issues(self, node: TransparencyNode) -> List[str]:
        """Identify issues with a specific node."""
        issues = []
        
        if node.data_completeness_score < 0.3:
            issues.append("Poor data completeness")
        
        if not node.has_origin_data:
            issues.append("Missing origin data")
        
        if not node.has_geographic_coordinates:
            issues.append("Missing geographic coordinates")
        
        if not node.has_certifications:
            issues.append("No certifications")
        
        if node.confidence_level < 0.4:
            issues.append("Low data confidence")
        
        if node.is_circular:
            issues.append("Part of circular reference")
        
        return issues
    
    def _calculate_node_improvement_potential(self, node: TransparencyNode) -> Dict[str, Any]:
        """Calculate improvement potential for a single node."""
        current_score = (node.base_ttm_score + node.base_ttp_score) / 2
        potential_score = current_score
        actions = []
        
        # Potential improvements
        if not node.has_origin_data:
            potential_score += 0.15
            actions.append("Add origin data")
        
        if not node.has_geographic_coordinates:
            potential_score += 0.10
            actions.append("Add geographic coordinates")
        
        if not node.has_certifications:
            potential_score += 0.20
            actions.append("Obtain relevant certifications")
        
        if node.data_completeness_score < 0.8:
            potential_improvement = (0.8 - node.data_completeness_score) * 0.15
            potential_score += potential_improvement
            actions.append("Complete missing data fields")
        
        potential_score = min(1.0, potential_score)
        potential = potential_score - current_score
        
        return {
            'potential_score': potential_score,
            'potential': potential,
            'actions': actions
        }
    
    def _prioritize_improvements(self, improvements: List[Dict[str, Any]]) -> List[str]:
        """Prioritize improvement actions."""
        # Sort by improvement potential
        improvements.sort(key=lambda x: x['improvement'], reverse=True)
        
        priority_actions = []
        for improvement in improvements[:3]:  # Top 3
            priority_actions.extend(improvement['actions'])
        
        # Remove duplicates while preserving order
        seen = set()
        unique_actions = []
        for action in priority_actions:
            if action not in seen:
                seen.add(action)
                unique_actions.append(action)
        
        return unique_actions

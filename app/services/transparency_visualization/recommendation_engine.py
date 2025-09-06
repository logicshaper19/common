"""
Improvement recommendation engine.

This service generates actionable improvement recommendations based on gap analysis.
It replaces the 150-line monster method with a clean, testable, and extensible system.
"""
from typing import List, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from .models.gap_models import GapAnalysis, ImprovementRecommendation, RecommendationPriority

logger = get_logger(__name__)


class ImprovementRecommendationEngine:
    """
    Generates actionable improvement recommendations based on gap analysis.
    
    This service is designed to be:
    - Highly configurable (business rules can be easily modified)
    - Extensible (new recommendation types can be added easily)
    - Testable (pure business logic with no external dependencies)
    - Maintainable (clear separation of concerns)
    """
    
    def __init__(self, db: Session):
        self.db = db
        
        # Recommendation configurations
        self.RECOMMENDATION_CONFIGS = {
            "origin_data": {
                "priority": RecommendationPriority.HIGH,
                "implementation_effort": "medium",
                "timeline": "2-4 weeks",
                "ttm_impact_multiplier": 0.4,
                "ttp_impact_multiplier": 0.8
            },
            "input_materials": {
                "priority": RecommendationPriority.HIGH,
                "implementation_effort": "high",
                "timeline": "4-8 weeks",
                "ttm_impact_multiplier": 0.7,
                "ttp_impact_multiplier": 0.5
            },
            "certifications": {
                "priority": RecommendationPriority.MEDIUM,
                "implementation_effort": "low",
                "timeline": "1-2 weeks",
                "ttm_impact_multiplier": 0.2,
                "ttp_impact_multiplier": 0.2
            },
            "geographic_data": {
                "priority": RecommendationPriority.MEDIUM,
                "implementation_effort": "low",
                "timeline": "1-2 weeks",
                "ttm_impact_multiplier": 0.3,
                "ttp_impact_multiplier": 0.4
            },
            "confidence_improvement": {
                "priority": RecommendationPriority.MEDIUM,
                "implementation_effort": "medium",
                "timeline": "2-3 weeks",
                "ttm_impact_multiplier": 0.3,
                "ttp_impact_multiplier": 0.3
            }
        }
    
    def generate_recommendations(
        self, 
        gap_analyses: List[GapAnalysis]
    ) -> List[ImprovementRecommendation]:
        """
        Generate actionable improvement recommendations from gap analyses.
        
        Args:
            gap_analyses: List of gap analysis results
            
        Returns:
            List of improvement recommendations
        """
        if not gap_analyses:
            return []
        
        # Group gaps by category
        gap_categories = self._group_gaps_by_category(gap_analyses)
        
        # Generate recommendations for each category
        recommendations = []
        for category, gaps in gap_categories.items():
            category_recommendations = self._create_category_recommendations(category, gaps)
            recommendations.extend(category_recommendations)
        
        # Add strategic recommendations
        strategic_recommendations = self._create_strategic_recommendations(gap_analyses)
        recommendations.extend(strategic_recommendations)
        
        # Prioritize and sort recommendations
        recommendations = self._prioritize_recommendations(recommendations)
        
        logger.info(f"Generated {len(recommendations)} recommendations from {len(gap_analyses)} gaps")
        return recommendations
    
    def _group_gaps_by_category(self, gap_analyses: List[GapAnalysis]) -> Dict[str, List[GapAnalysis]]:
        """Group gaps by their category for recommendation generation."""
        categories = {}
        
        for gap in gap_analyses:
            category = self._map_gap_type_to_category(gap.gap_type)
            if category not in categories:
                categories[category] = []
            categories[category].append(gap)
        
        return categories
    
    def _map_gap_type_to_category(self, gap_type) -> str:
        """Map gap type to recommendation category."""
        mapping = {
            "missing_origin_data": "origin_data",
            "missing_input_material": "input_materials",
            "incomplete_certifications": "certifications",
            "missing_geographic_data": "geographic_data",
            "low_confidence": "confidence_improvement",
            "weak_traceability_link": "input_materials"
        }
        return mapping.get(gap_type.value, "general_improvement")
    
    def _create_category_recommendations(
        self, 
        category: str, 
        gaps: List[GapAnalysis]
    ) -> List[ImprovementRecommendation]:
        """Create recommendations for a specific gap category."""
        config = self.RECOMMENDATION_CONFIGS.get(category, {})
        
        if not config:
            return []
        
        # Calculate aggregated impact
        total_impact = sum(gap.impact_score for gap in gaps)
        ttm_impact = sum(gap.improvement_potential[0] for gap in gaps)
        ttp_impact = sum(gap.improvement_potential[1] for gap in gaps)
        
        # Create the recommendation
        recommendation = ImprovementRecommendation(
            recommendation_id=f"rec_{category}_{len(gaps)}_gaps",
            category=category,
            priority=config["priority"],
            title=self._get_recommendation_title(category, len(gaps)),
            description=self._get_recommendation_description(category, len(gaps)),
            expected_ttm_impact=ttm_impact * config["ttm_impact_multiplier"],
            expected_ttp_impact=ttp_impact * config["ttp_impact_multiplier"],
            implementation_effort=config["implementation_effort"],
            timeline=config["timeline"],
            actions=self._get_recommendation_actions(category),
            affected_gaps=[gap.gap_id for gap in gaps],
            success_metrics=self._get_success_metrics(category)
        )
        
        return [recommendation]
    
    def _create_strategic_recommendations(
        self, 
        gap_analyses: List[GapAnalysis]
    ) -> List[ImprovementRecommendation]:
        """Create strategic recommendations based on overall gap patterns."""
        recommendations = []
        
        # Analyze gap patterns
        gap_counts = self._analyze_gap_patterns(gap_analyses)
        
        # Create strategic recommendations based on patterns
        if gap_counts["critical"] > 5:
            recommendations.append(self._create_strategic_recommendation(
                "critical_gap_reduction",
                "Address Critical Transparency Gaps",
                "Focus on reducing critical gaps that significantly impact transparency scores",
                gap_counts["critical"]
            ))
        
        if gap_counts["missing_origin_data"] > 3:
            recommendations.append(self._create_strategic_recommendation(
                "origin_data_program",
                "Implement Origin Data Collection Program",
                "Establish systematic approach to collecting origin data across supply chain",
                gap_counts["missing_origin_data"]
            ))
        
        if gap_counts["missing_input_material"] > 3:
            recommendations.append(self._create_strategic_recommendation(
                "traceability_program",
                "Enhance Supply Chain Traceability",
                "Strengthen traceability links throughout the supply chain",
                gap_counts["missing_input_material"]
            ))
        
        return recommendations
    
    def _create_strategic_recommendation(
        self, 
        rec_id: str, 
        title: str, 
        description: str, 
        gap_count: int
    ) -> ImprovementRecommendation:
        """Create a strategic recommendation."""
        return ImprovementRecommendation(
            recommendation_id=f"strategic_{rec_id}",
            category="strategic",
            priority=RecommendationPriority.HIGH,
            title=title,
            description=f"{description} (affects {gap_count} gaps)",
            expected_ttm_impact=gap_count * 0.1,
            expected_ttp_impact=gap_count * 0.15,
            implementation_effort="high",
            timeline="8-12 weeks",
            actions=self._get_strategic_actions(rec_id),
            success_metrics=["gap_reduction", "transparency_score_improvement"]
        )
    
    def _analyze_gap_patterns(self, gap_analyses: List[GapAnalysis]) -> Dict[str, int]:
        """Analyze patterns in gap data."""
        patterns = {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
            "missing_origin_data": 0,
            "missing_input_material": 0,
            "low_confidence": 0
        }
        
        for gap in gap_analyses:
            patterns[gap.severity.value] += 1
            patterns[gap.gap_type.value] += 1
        
        return patterns
    
    def _prioritize_recommendations(
        self, 
        recommendations: List[ImprovementRecommendation]
    ) -> List[ImprovementRecommendation]:
        """Prioritize recommendations based on impact and effort."""
        def priority_score(rec: ImprovementRecommendation) -> float:
            impact = rec.expected_ttm_impact + rec.expected_ttp_impact
            effort_multiplier = {"low": 1.0, "medium": 0.7, "high": 0.4}
            effort = effort_multiplier.get(rec.implementation_effort, 0.5)
            return impact * effort
        
        recommendations.sort(key=priority_score, reverse=True)
        return recommendations
    
    def _get_recommendation_title(self, category: str, gap_count: int) -> str:
        """Get recommendation title based on category and gap count."""
        titles = {
            "origin_data": f"Add Origin Data ({gap_count} gaps)",
            "input_materials": f"Link Input Materials ({gap_count} gaps)",
            "certifications": f"Complete Certifications ({gap_count} gaps)",
            "geographic_data": f"Add Geographic Data ({gap_count} gaps)",
            "confidence_improvement": f"Improve Data Confidence ({gap_count} gaps)"
        }
        return titles.get(category, f"Address {category} ({gap_count} gaps)")
    
    def _get_recommendation_description(self, category: str, gap_count: int) -> str:
        """Get recommendation description based on category."""
        descriptions = {
            "origin_data": f"Add origin data for {gap_count} purchase orders to improve plantation-level transparency",
            "input_materials": f"Link input materials for {gap_count} purchase orders to establish supply chain traceability",
            "certifications": f"Complete sustainability certifications for {gap_count} purchase orders",
            "geographic_data": f"Add geographic coordinates for {gap_count} purchase orders",
            "confidence_improvement": f"Improve data confidence for {gap_count} purchase orders"
        }
        return descriptions.get(category, f"Address {category} issues for {gap_count} purchase orders")
    
    def _get_recommendation_actions(self, category: str) -> List[str]:
        """Get specific actions for a recommendation category."""
        actions = {
            "origin_data": [
                "Contact suppliers to provide harvest dates",
                "Collect farm identification information",
                "Verify geographic coordinates",
                "Update purchase order records"
            ],
            "input_materials": [
                "Identify input material sources",
                "Establish supplier relationships",
                "Create purchase order linkages",
                "Verify material flow documentation"
            ],
            "certifications": [
                "Request certification documents",
                "Verify certification validity",
                "Update certification records",
                "Implement certification tracking"
            ],
            "geographic_data": [
                "Collect GPS coordinates",
                "Verify location accuracy",
                "Update geographic records",
                "Implement location validation"
            ],
            "confidence_improvement": [
                "Verify data sources",
                "Request additional documentation",
                "Implement data validation processes",
                "Establish data quality standards"
            ]
        }
        return actions.get(category, ["Review and improve data quality"])
    
    def _get_strategic_actions(self, rec_id: str) -> List[str]:
        """Get strategic actions based on recommendation type."""
        actions = {
            "critical_gap_reduction": [
                "Prioritize critical gaps for immediate attention",
                "Allocate resources for gap resolution",
                "Implement gap tracking system",
                "Establish gap resolution timeline"
            ],
            "origin_data_program": [
                "Develop origin data collection framework",
                "Train suppliers on data requirements",
                "Implement data validation processes",
                "Create origin data dashboard"
            ],
            "traceability_program": [
                "Map complete supply chain network",
                "Establish traceability standards",
                "Implement tracking systems",
                "Create traceability reporting"
            ]
        }
        return actions.get(rec_id, ["Develop strategic improvement plan"])
    
    def _get_success_metrics(self, category: str) -> List[str]:
        """Get success metrics for a recommendation category."""
        metrics = {
            "origin_data": ["origin_data_completion_rate", "ttp_score_improvement"],
            "input_materials": ["traceability_link_count", "ttm_score_improvement"],
            "certifications": ["certification_completion_rate", "compliance_score"],
            "geographic_data": ["geographic_data_coverage", "location_accuracy"],
            "confidence_improvement": ["data_confidence_score", "validation_rate"]
        }
        return metrics.get(category, ["overall_transparency_improvement"])


"""
Transparency Calculation Service

Focused service for complex algorithmic calculations only.
This service handles genuinely complex operations that require
specialized algorithms and external system integration.
"""
import os
from datetime import datetime
from typing import Dict, Any, List
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.config import settings
from app.models.purchase_order import PurchaseOrder


class TransparencyScore:
    """Data class for transparency calculation results."""
    
    def __init__(self, company_id: UUID, mill_percentage: float, 
                 plantation_percentage: float, overall_score: float, 
                 calculated_at: datetime):
        self.company_id = company_id
        self.mill_percentage = mill_percentage
        self.plantation_percentage = plantation_percentage
        self.overall_score = overall_score
        self.calculated_at = calculated_at


class TransparencyCalculationService:
    """
    Focused on complex algorithmic calculations only.
    
    This service handles:
    - Complex SQL queries with business logic
    - Sophisticated algorithms for transparency scoring
    - Supply chain degradation calculations
    - External system integration for data gathering
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.degradation_factor = settings.transparency_degradation_factor
    
    def mark_for_recalculation(self, po_id: UUID) -> None:
        """
        Simple operation - mark PO for recalculation.
        
        This is just a flag update, not complex calculation.
        """
        # This is just a flag update, not complex calculation
        po = self.db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
        if po:
            po.transparency_needs_recalc = True
    
    def calculate_supply_chain_transparency(self, company_id: UUID) -> TransparencyScore:
        """
        Complex algorithmic calculation - genuine service territory.
        
        This method performs sophisticated calculations that require:
        - Complex SQL queries
        - Business algorithms
        - External data integration
        """
        
        # Complex SQL with business logic
        transparency_data = self._execute_complex_transparency_query(company_id)
        
        # Complex business algorithms
        mill_score = self._calculate_mill_transparency_score(transparency_data)
        plantation_score = self._calculate_plantation_transparency_score(transparency_data)
        
        # Apply complex degradation algorithms
        adjusted_scores = self._apply_supply_chain_degradation(mill_score, plantation_score)
        
        return TransparencyScore(
            company_id=company_id,
            mill_percentage=adjusted_scores['mill'],
            plantation_percentage=adjusted_scores['plantation'],
            overall_score=adjusted_scores['overall'],
            calculated_at=datetime.utcnow()
        )
    
    def _execute_complex_transparency_query(self, company_id: UUID) -> Dict[str, Any]:
        """
        Execute complex SQL query for transparency data.
        
        This is a genuine service operation - complex SQL with business logic.
        """
        query = text("""
            WITH supply_chain_data AS (
                SELECT 
                    po.id as po_id,
                    po.buyer_company_id,
                    po.seller_company_id,
                    po.quantity,
                    po.confirmed_quantity,
                    po.status,
                    po.created_at,
                    po.confirmed_at,
                    -- Complex business logic in SQL
                    CASE 
                        WHEN po.status = 'confirmed' AND po.confirmed_quantity = po.quantity 
                        THEN 1.0
                        WHEN po.status = 'confirmed' AND po.confirmed_quantity < po.quantity 
                        THEN 0.8
                        ELSE 0.5
                    END as fulfillment_score,
                    -- Traceability scoring
                    CASE 
                        WHEN po.origin_data IS NOT NULL 
                        THEN COALESCE((po.origin_data->>'traceability_score')::float, 0.7)
                        ELSE 0.3
                    END as traceability_score
                FROM purchase_orders po
                WHERE po.buyer_company_id = :company_id
                   OR po.seller_company_id = :company_id
            ),
            aggregated_scores AS (
                SELECT 
                    buyer_company_id,
                    AVG(fulfillment_score) as avg_fulfillment,
                    AVG(traceability_score) as avg_traceability,
                    COUNT(*) as total_pos,
                    COUNT(CASE WHEN status = 'confirmed' THEN 1 END) as confirmed_pos
                FROM supply_chain_data
                GROUP BY buyer_company_id
            )
            SELECT 
                avg_fulfillment,
                avg_traceability,
                total_pos,
                confirmed_pos,
                CASE 
                    WHEN total_pos > 0 THEN confirmed_pos::float / total_pos
                    ELSE 0
                END as confirmation_rate
            FROM aggregated_scores
            WHERE buyer_company_id = :company_id
        """)
        
        result = self.db.execute(query, {"company_id": company_id}).fetchone()
        
        if result:
            return {
                'fulfillment_score': float(result.avg_fulfillment or 0),
                'traceability_score': float(result.avg_traceability or 0),
                'total_pos': int(result.total_pos or 0),
                'confirmed_pos': int(result.confirmed_pos or 0),
                'confirmation_rate': float(result.confirmation_rate or 0)
            }
        else:
            return {
                'fulfillment_score': 0.0,
                'traceability_score': 0.0,
                'total_pos': 0,
                'confirmed_pos': 0,
                'confirmation_rate': 0.0
            }
    
    def _calculate_mill_transparency_score(self, data: Dict[str, Any]) -> float:
        """
        Complex algorithm for mill transparency scoring.
        
        This is genuine service territory - sophisticated business algorithms.
        """
        # Complex business algorithm
        base_score = data['fulfillment_score'] * 0.4 + data['traceability_score'] * 0.6
        
        # Apply volume weighting
        volume_factor = min(1.0, data['total_pos'] / 10.0)  # More POs = higher confidence
        
        # Apply confirmation rate bonus
        confirmation_bonus = data['confirmation_rate'] * 0.1
        
        # Final calculation
        mill_score = (base_score * volume_factor) + confirmation_bonus
        
        return min(1.0, max(0.0, mill_score))
    
    def _calculate_plantation_transparency_score(self, data: Dict[str, Any]) -> float:
        """
        Complex algorithm for plantation transparency scoring.
        
        This is genuine service territory - sophisticated business algorithms.
        """
        # Different algorithm for plantation scoring
        base_score = data['traceability_score'] * 0.7 + data['fulfillment_score'] * 0.3
        
        # Apply supply chain depth factor
        depth_factor = 0.8  # Default for single-tier supply chain
        
        # Apply certification bonus (would integrate with external systems)
        certification_bonus = 0.1  # Placeholder for external certification data
        
        # Final calculation
        plantation_score = (base_score * depth_factor) + certification_bonus
        
        return min(1.0, max(0.0, plantation_score))
    
    def _apply_supply_chain_degradation(self, mill_score: float, plantation_score: float) -> Dict[str, float]:
        """
        Apply complex supply chain degradation algorithms.
        
        This is genuine service territory - sophisticated business algorithms.
        """
        # Complex degradation calculation
        degradation_factor = self.degradation_factor
        
        # Apply degradation based on supply chain complexity
        mill_degraded = mill_score * degradation_factor
        plantation_degraded = plantation_score * (degradation_factor ** 2)  # Double degradation for plantation
        
        # Calculate overall score with weighted average
        overall_score = (mill_degraded * 0.6) + (plantation_degraded * 0.4)
        
        return {
            'mill': mill_degraded,
            'plantation': plantation_degraded,
            'overall': overall_score
        }
    
    def get_transparency_insights(self, company_id: UUID) -> Dict[str, Any]:
        """
        Generate insights and recommendations based on transparency data.
        
        This is genuine service territory - complex analysis and recommendations.
        """
        data = self._execute_complex_transparency_query(company_id)
        score = self.calculate_supply_chain_transparency(company_id)
        
        # Generate insights
        insights = []
        
        if score.overall_score < 0.5:
            insights.append("Low transparency score - consider improving traceability")
        
        if data['confirmation_rate'] < 0.8:
            insights.append("Low confirmation rate - review supplier relationships")
        
        if data['traceability_score'] < 0.6:
            insights.append("Poor traceability - implement better origin tracking")
        
        return {
            'score': score,
            'insights': insights,
            'recommendations': self._generate_recommendations(score, data)
        }
    
    def _generate_recommendations(self, score: TransparencyScore, data: Dict[str, Any]) -> List[str]:
        """Generate specific recommendations based on analysis."""
        recommendations = []
        
        if score.mill_percentage < 0.7:
            recommendations.append("Improve mill-level transparency through better documentation")
        
        if score.plantation_percentage < 0.5:
            recommendations.append("Enhance plantation traceability with GPS tracking and certifications")
        
        if data['total_pos'] < 5:
            recommendations.append("Increase transaction volume for better data quality")
        
        return recommendations

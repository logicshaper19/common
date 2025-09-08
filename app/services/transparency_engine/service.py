"""
Main transparency calculation engine service.
"""
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.purchase_order import PurchaseOrder
from app.services.purchase_order import PurchaseOrderService
from app.core.logging import get_logger
from app.core.performance_cache import get_performance_cache
from app.core.performance_monitoring import get_performance_monitor

from .domain.models import (
    TransparencyNode, 
    TransparencyPath, 
    TransparencyResult,
    ImprovementSuggestion
)
from .domain.enums import GraphTraversalMode, CycleHandlingStrategy
from .graph import GraphTraversal, CycleDetector
from .calculation import ScoreCalculator, ConfidenceCalculator, ScoreAggregator

logger = get_logger(__name__)


class TransparencyCalculationEngine:
    """
    Enhanced transparency calculation engine with modular architecture.
    
    This service orchestrates the various components to calculate transparency
    scores using graph traversal, cycle detection, and sophisticated scoring algorithms.
    """
    
    def __init__(
        self, 
        db: Session,
        max_depth: int = 10,
        traversal_mode: GraphTraversalMode = GraphTraversalMode.DEPTH_FIRST,
        cycle_strategy: CycleHandlingStrategy = CycleHandlingStrategy.DEGRADATION
    ):
        """Initialize transparency calculation engine."""
        self.db = db
        self.po_service = PurchaseOrderService(db)
        
        # Initialize components
        self.graph_traversal = GraphTraversal(
            db, max_depth, traversal_mode, cycle_strategy
        )
        self.cycle_detector = CycleDetector()
        self.score_calculator = ScoreCalculator()
        self.confidence_calculator = ConfidenceCalculator()
        self.score_aggregator = ScoreAggregator()
        
        # Performance monitoring
        self.cache = get_performance_cache()
        self.monitor = get_performance_monitor()
    
    def calculate_transparency_scores(
        self, 
        po_id: UUID,
        use_cache: bool = True
    ) -> TransparencyResult:
        """
        Calculate comprehensive transparency scores for a purchase order.
        
        Args:
            po_id: Purchase order UUID
            use_cache: Whether to use cached results
            
        Returns:
            Complete transparency calculation result
        """
        with self.monitor.track_operation("transparency_calculation"):
            # Check cache first
            cache_key = f"transparency_scores_{po_id}"
            if use_cache and self.cache:
                cached_result = self.cache.get(cache_key)
                if cached_result:
                    logger.debug(f"Using cached transparency scores for PO {po_id}")
                    return cached_result
            
            logger.info(f"Calculating transparency scores for PO {po_id}")
            
            # Step 1: Traverse the supply chain graph
            paths = self.graph_traversal.traverse_from_po(
                po_id,
                self._create_transparency_node,
                self._get_po_with_details
            )
            
            if not paths:
                logger.warning(f"No paths found for PO {po_id}")
                return self._create_empty_result(po_id)
            
            # Step 2: Calculate scores for each node in each path
            for path in paths:
                for node in path.nodes:
                    self.score_calculator.calculate_base_scores(node)
                    self.score_calculator.apply_degradation_factor(node)
            
            # Step 3: Calculate confidence levels
            for path in paths:
                for node in path.nodes:
                    node.confidence_level = self.confidence_calculator.calculate_confidence(node)
            
            # Step 4: Aggregate scores across paths
            primary_path = self.score_aggregator.select_primary_path(paths)
            final_scores = self.score_aggregator.aggregate_path_scores(primary_path)
            
            # Step 5: Calculate additional metrics
            traced_percentage = self._calculate_traceability_coverage(paths)
            circular_refs = len([p for p in paths if p.has_cycles])
            
            # Step 6: Create result
            result = TransparencyResult(
                po_id=po_id,
                ttm_score=final_scores['ttm_score'],
                ttp_score=final_scores['ttp_score'],
                confidence_level=final_scores['confidence_level'],
                traced_percentage=traced_percentage,
                calculation_timestamp=datetime.utcnow(),
                total_nodes_analyzed=sum(len(p.nodes) for p in paths),
                circular_references_detected=circular_refs,
                primary_path=primary_path,
                alternative_paths=[p for p in paths if p != primary_path]
            )
            
            # Cache result
            if use_cache and self.cache:
                self.cache.set(cache_key, result, ttl=3600)  # 1 hour cache
            
            logger.info(
                f"Transparency calculation complete for PO {po_id}: "
                f"TTM={result.ttm_score:.3f}, TTP={result.ttp_score:.3f}, "
                f"Confidence={result.confidence_level:.3f}"
            )
            
            return result
    
    def detect_circular_references(self, po_id: UUID) -> List[UUID]:
        """
        Detect circular references in the supply chain.
        
        Args:
            po_id: Purchase order UUID to start detection from
            
        Returns:
            List of PO IDs involved in circular references
        """
        cycles = self.cycle_detector.detect_cycles(
            po_id,
            self._get_input_materials_for_po
        )
        
        # Flatten cycles to get unique PO IDs
        circular_pos = set()
        for cycle in cycles:
            circular_pos.update(cycle)
        
        return list(circular_pos)
    
    def get_transparency_improvement_suggestions(
        self, 
        po_id: UUID
    ) -> List[ImprovementSuggestion]:
        """
        Get suggestions for improving transparency scores.
        
        Args:
            po_id: Purchase order UUID
            
        Returns:
            List of improvement suggestions
        """
        # Calculate current scores
        result = self.calculate_transparency_scores(po_id)
        
        suggestions = []
        
        # Analyze primary path for improvement opportunities
        if result.primary_path:
            suggestions.extend(self._analyze_path_for_improvements(result.primary_path))
        
        # Check for data gaps
        suggestions.extend(self._identify_data_gaps(result))
        
        # Check for certification opportunities
        suggestions.extend(self._identify_certification_opportunities(result))
        
        # Sort by priority and impact
        suggestions.sort(
            key=lambda s: (
                {"high": 0, "medium": 1, "low": 2}[s.priority],
                -s.impact_estimate
            )
        )
        
        return suggestions
    
    def _create_transparency_node(self, po_data: Dict[str, Any], depth: int) -> TransparencyNode:
        """Create a TransparencyNode from PO data."""
        node = TransparencyNode(
            po_id=UUID(str(po_data['id'])),
            po_number=po_data['po_number'],
            company_id=UUID(str(po_data['seller_company']['id'])),
            company_type=po_data['seller_company']['company_type'],
            product_id=UUID(str(po_data['product']['id'])),
            product_category=po_data['product']['category'],
            quantity=po_data['quantity'],
            unit=po_data['unit'],
            depth=depth
        )
        
        # Extract transparency factors
        confirmation_data = po_data.get('confirmation_data', {})
        
        node.has_origin_data = bool(confirmation_data.get('origin_data'))
        node.has_geographic_coordinates = bool(
            confirmation_data.get('origin_data', {}).get('geographic_coordinates')
        )
        
        certifications = confirmation_data.get('origin_data', {}).get('certifications', [])
        node.has_certifications = len(certifications) > 0
        node.certification_count = len(certifications)
        
        # Count high-value certifications (simplified)
        high_value_certs = ['RSPO', 'NDPE', 'Rainforest Alliance', 'Organic']
        node.high_value_cert_count = sum(
            1 for cert in certifications if cert in high_value_certs
        )
        
        # Calculate data completeness score
        node.data_completeness_score = self._calculate_data_completeness(confirmation_data)
        
        # Extract input materials
        node.input_materials = confirmation_data.get('transformation_data', {}).get('input_materials', [])
        
        return node
    
    def _get_po_with_details(self, po_id: UUID) -> Optional[Dict[str, Any]]:
        """Get PO with all details needed for transparency calculation."""
        try:
            po = self.po_service.get_purchase_order_with_details(str(po_id))
            if not po:
                return None
            
            return {
                'id': po.id,
                'po_number': po.po_number,
                'quantity': po.quantity,
                'unit': po.unit,
                'seller_company': {
                    'id': po.seller_company['id'],
                    'company_type': po.seller_company.get('company_type', 'unknown')
                },
                'buyer_company': {
                    'id': po.buyer_company['id'],
                    'company_type': po.buyer_company.get('company_type', 'unknown')
                },
                'product': {
                    'id': po.product['id'],
                    'name': po.product.get('name', ''),
                    'category': po.product.get('category', 'unknown')
                },
                'confirmation_data': po.confirmation_data or {}
            }
        except Exception as e:
            logger.error(f"Error getting PO details for {po_id}: {e}")
            return None
    
    def _get_input_materials_for_po(self, po_id: UUID) -> List[Dict[str, Any]]:
        """Get input materials for a PO (for cycle detection)."""
        po_data = self._get_po_with_details(po_id)
        if not po_data:
            return []
        
        confirmation_data = po_data.get('confirmation_data', {})
        transformation_data = confirmation_data.get('transformation_data', {})
        return transformation_data.get('input_materials', [])
    
    def _calculate_data_completeness(self, confirmation_data: Dict[str, Any]) -> float:
        """Calculate data completeness score."""
        total_fields = 0
        filled_fields = 0
        
        # Check origin data fields
        origin_data = confirmation_data.get('origin_data', {})
        if origin_data:
            origin_fields = [
                'geographic_coordinates', 'certifications', 'harvest_date',
                'quality_grade', 'processing_method'
            ]
            total_fields += len(origin_fields)
            filled_fields += sum(1 for field in origin_fields if origin_data.get(field))
        
        # Check transformation data fields
        transformation_data = confirmation_data.get('transformation_data', {})
        if transformation_data:
            transform_fields = [
                'input_materials', 'processing_method', 'quality_control',
                'facility_certifications'
            ]
            total_fields += len(transform_fields)
            filled_fields += sum(1 for field in transform_fields if transformation_data.get(field))
        
        return filled_fields / total_fields if total_fields > 0 else 0.0
    
    def _create_empty_result(self, po_id: UUID) -> TransparencyResult:
        """Create empty result when no data is available."""
        return TransparencyResult(
            po_id=po_id,
            ttm_score=0.0,
            ttp_score=0.0,
            confidence_level=0.0,
            traced_percentage=0.0,
            calculation_timestamp=datetime.utcnow(),
            total_nodes_analyzed=0,
            circular_references_detected=0,
            data_gaps_identified=1,
            critical_gaps=["No supply chain data available"]
        )
    
    def _calculate_traceability_coverage(self, paths: List[TransparencyPath]) -> float:
        """Calculate percentage of supply chain that is traceable."""
        if not paths:
            return 0.0
        
        # Use the primary path for coverage calculation
        primary_path = max(paths, key=lambda p: len(p.nodes))
        
        if not primary_path.nodes:
            return 0.0
        
        # Calculate based on nodes with sufficient data
        traceable_nodes = sum(
            1 for node in primary_path.nodes
            if node.data_completeness_score > 0.5
        )
        
        return traceable_nodes / len(primary_path.nodes)
    
    def _analyze_path_for_improvements(self, path: TransparencyPath) -> List[ImprovementSuggestion]:
        """Analyze a path for improvement opportunities."""
        suggestions = []
        
        for node in path.nodes:
            if node.data_completeness_score < 0.5:
                suggestions.append(ImprovementSuggestion(
                    category="data_completeness",
                    priority="high",
                    description=f"Improve data completeness for PO {node.po_number}",
                    impact_estimate=0.2,
                    effort_estimate="medium",
                    affected_nodes=[node.po_id],
                    specific_actions=[
                        "Complete missing origin data fields",
                        "Add geographic coordinates",
                        "Upload required certifications"
                    ]
                ))
        
        return suggestions
    
    def _identify_data_gaps(self, result: TransparencyResult) -> List[ImprovementSuggestion]:
        """Identify data gaps in the transparency calculation."""
        suggestions = []
        
        if result.traced_percentage < 0.8:
            suggestions.append(ImprovementSuggestion(
                category="traceability_coverage",
                priority="high",
                description="Improve supply chain traceability coverage",
                impact_estimate=0.3,
                effort_estimate="high",
                specific_actions=[
                    "Engage with suppliers to complete data",
                    "Implement supplier onboarding program",
                    "Establish data collection standards"
                ]
            ))
        
        return suggestions
    
    def _identify_certification_opportunities(self, result: TransparencyResult) -> List[ImprovementSuggestion]:
        """Identify certification opportunities."""
        suggestions = []
        
        if result.primary_path:
            uncertified_nodes = [
                node for node in result.primary_path.nodes
                if not node.has_certifications
            ]
            
            if uncertified_nodes:
                suggestions.append(ImprovementSuggestion(
                    category="certifications",
                    priority="medium",
                    description="Add certifications to improve transparency",
                    impact_estimate=0.15,
                    effort_estimate="medium",
                    affected_nodes=[node.po_id for node in uncertified_nodes],
                    specific_actions=[
                        "Pursue RSPO certification",
                        "Obtain environmental certifications",
                        "Document existing quality standards"
                    ]
                ))
        
        return suggestions

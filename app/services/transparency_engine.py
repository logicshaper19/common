"""
Enhanced transparency calculation engine with recursive graph traversal and cycle detection.
"""
from typing import Optional, List, Dict, Any, Set, Tuple
from uuid import UUID
from datetime import datetime, timedelta
from decimal import Decimal
from dataclasses import dataclass, field
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models.purchase_order import PurchaseOrder
from app.models.company import Company
from app.models.product import Product
from app.services.purchase_order import PurchaseOrderService
from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class TransparencyNode:
    """Represents a node in the transparency calculation graph."""
    po_id: UUID
    po_number: str
    company_id: UUID
    company_type: str
    product_id: UUID
    product_category: str
    quantity: Decimal
    unit: str
    
    # Transparency factors
    has_origin_data: bool = False
    has_geographic_coordinates: bool = False
    has_certifications: bool = False
    certification_count: int = 0
    high_value_cert_count: int = 0
    data_completeness_score: float = 0.0
    
    # Input materials
    input_materials: List[Dict[str, Any]] = field(default_factory=list)
    
    # Calculated scores
    base_ttm_score: float = 0.0
    base_ttp_score: float = 0.0
    weighted_ttm_score: float = 0.0
    weighted_ttp_score: float = 0.0
    confidence_level: float = 0.0
    
    # Graph traversal metadata
    depth: int = 0
    visited_at: Optional[datetime] = None
    is_circular: bool = False
    degradation_factor: float = 1.0


@dataclass
class TransparencyPath:
    """Represents a path through the supply chain graph."""
    nodes: List[TransparencyNode] = field(default_factory=list)
    total_weight: float = 0.0
    path_ttm_score: float = 0.0
    path_ttp_score: float = 0.0
    path_confidence: float = 0.0
    has_cycles: bool = False
    cycle_break_points: List[UUID] = field(default_factory=list)


@dataclass
class TransparencyResult:
    """Complete transparency calculation result."""
    po_id: UUID
    ttm_score: float
    ttp_score: float
    confidence_level: float
    traced_percentage: float
    untraced_percentage: float
    
    # Graph analysis
    total_nodes: int
    max_depth: int
    circular_references: List[UUID]
    degradation_applied: float
    
    # Detailed breakdown
    paths: List[TransparencyPath]
    node_details: List[TransparencyNode]
    calculation_metadata: Dict[str, Any]
    
    # Timestamps
    calculated_at: datetime
    calculation_duration_ms: float


class TransparencyCalculationEngine:
    """
    Enhanced transparency calculation engine with recursive graph traversal.
    
    This engine implements sophisticated algorithms for calculating transparency scores
    through complex supply chain networks with proper handling of cycles, degradation
    factors, and confidence levels.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.po_service = PurchaseOrderService(db)
        
        # Configuration constants
        self.MAX_DEPTH = 20
        self.DEGRADATION_FACTOR_PER_STEP = 0.95  # 5% degradation per transformation
        self.CYCLE_DETECTION_TIMEOUT_MS = 5000  # 5 seconds max for cycle detection
        
        # Transparency weights for different factors
        self.TRANSPARENCY_WEIGHTS = {
            "origin_data": 0.30,
            "geographic_coordinates": 0.20,
            "certifications": 0.25,
            "input_materials": 0.15,
            "company_type": 0.10
        }
        
        # Company type scoring
        self.COMPANY_TYPE_SCORES = {
            "originator": 1.0,    # Highest transparency potential
            "processor": 0.8,     # Good transparency with processing data
            "brand": 0.6          # Lower transparency, more aggregated
        }
        
        # Product category scoring
        self.PRODUCT_CATEGORY_SCORES = {
            "raw_material": 1.0,      # Highest transparency potential
            "processed_material": 0.8, # Good transparency with processing info
            "finished_product": 0.6    # Lower transparency, more complex
        }
        
        # High-value certifications for enhanced scoring
        self.HIGH_VALUE_CERTIFICATIONS = {
            "RSPO", "NDPE", "ISPO", "MSPO", "RTRS", "ISCC",
            "Rainforest Alliance", "Organic", "Fair Trade"
        }
    
    def calculate_transparency(
        self,
        po_id: UUID,
        force_recalculation: bool = False,
        include_detailed_analysis: bool = True
    ) -> TransparencyResult:
        """
        Calculate comprehensive transparency scores for a purchase order.
        
        Args:
            po_id: Purchase order UUID
            force_recalculation: Force recalculation even if cached
            include_detailed_analysis: Include detailed path and node analysis
            
        Returns:
            Complete transparency calculation result
        """
        start_time = datetime.utcnow()
        
        logger.info(
            "Starting enhanced transparency calculation",
            po_id=str(po_id),
            force_recalculation=force_recalculation
        )
        
        try:
            # Initialize calculation state
            visited_nodes: Set[UUID] = set()
            calculation_stack: List[UUID] = []
            all_nodes: Dict[UUID, TransparencyNode] = {}
            all_paths: List[TransparencyPath] = []
            circular_references: List[UUID] = []
            
            # Perform recursive graph traversal
            root_node = self._traverse_graph_recursive(
                po_id,
                visited_nodes,
                calculation_stack,
                all_nodes,
                all_paths,
                circular_references,
                depth=0
            )
            
            if not root_node:
                raise ValueError(f"Could not analyze purchase order {po_id}")
            
            # Calculate final transparency scores
            final_ttm, final_ttp, confidence = self._calculate_final_scores(
                root_node, all_paths, all_nodes
            )
            
            # Calculate traced vs untraced percentages
            traced_percentage, untraced_percentage = self._calculate_traceability_coverage(
                all_paths, all_nodes
            )
            
            # Apply degradation factors
            degradation_applied = self._calculate_degradation_factor(root_node.depth)
            final_ttm *= degradation_applied
            final_ttp *= degradation_applied
            
            # Calculate duration
            end_time = datetime.utcnow()
            duration_ms = (end_time - start_time).total_seconds() * 1000
            
            # Build result
            result = TransparencyResult(
                po_id=po_id,
                ttm_score=min(final_ttm, 1.0),
                ttp_score=min(final_ttp, 1.0),
                confidence_level=confidence,
                traced_percentage=traced_percentage,
                untraced_percentage=untraced_percentage,
                total_nodes=len(all_nodes),
                max_depth=max((node.depth for node in all_nodes.values()), default=0),
                circular_references=circular_references,
                degradation_applied=degradation_applied,
                paths=all_paths if include_detailed_analysis else [],
                node_details=list(all_nodes.values()) if include_detailed_analysis else [],
                calculation_metadata={
                    "algorithm_version": "2.0",
                    "max_depth_limit": self.MAX_DEPTH,
                    "degradation_factor": self.DEGRADATION_FACTOR_PER_STEP,
                    "weights_used": self.TRANSPARENCY_WEIGHTS,
                    "cycles_detected": len(circular_references),
                    "paths_analyzed": len(all_paths)
                },
                calculated_at=end_time,
                calculation_duration_ms=duration_ms
            )
            
            logger.info(
                "Enhanced transparency calculation completed",
                po_id=str(po_id),
                ttm_score=result.ttm_score,
                ttp_score=result.ttp_score,
                confidence=result.confidence_level,
                duration_ms=duration_ms,
                total_nodes=result.total_nodes,
                cycles_detected=len(circular_references)
            )
            
            return result

        except Exception as e:
            logger.error(
                "Enhanced transparency calculation failed",
                po_id=str(po_id),
                error=str(e)
            )
            raise

    def _traverse_graph_recursive(
        self,
        po_id: UUID,
        visited_nodes: Set[UUID],
        calculation_stack: List[UUID],
        all_nodes: Dict[UUID, TransparencyNode],
        all_paths: List[TransparencyPath],
        circular_references: List[UUID],
        depth: int = 0,
        contribution_weight: float = 1.0
    ) -> Optional[TransparencyNode]:
        """
        Recursively traverse the supply chain graph with cycle detection.

        Args:
            po_id: Current purchase order ID
            visited_nodes: Set of already visited nodes
            calculation_stack: Current calculation stack for cycle detection
            all_nodes: Dictionary of all analyzed nodes
            all_paths: List of all discovered paths
            circular_references: List of detected circular references
            depth: Current depth in the graph
            contribution_weight: Weight contribution from parent nodes

        Returns:
            TransparencyNode for the current PO or None if invalid
        """
        # Check depth limit
        if depth >= self.MAX_DEPTH:
            logger.warning(
                "Maximum depth reached in transparency calculation",
                po_id=str(po_id),
                depth=depth
            )
            return None

        # Detect circular references
        if po_id in calculation_stack:
            logger.warning(
                "Circular reference detected in supply chain",
                po_id=str(po_id),
                stack_depth=len(calculation_stack)
            )
            circular_references.append(po_id)

            # Create a circular node marker
            circular_node = TransparencyNode(
                po_id=po_id,
                po_number="CIRCULAR_REF",
                company_id=UUID('00000000-0000-0000-0000-000000000000'),
                company_type="unknown",
                product_id=UUID('00000000-0000-0000-0000-000000000000'),
                product_category="unknown",
                quantity=Decimal('0'),
                unit="",
                is_circular=True,
                depth=depth
            )
            return circular_node

        # Check if already processed (but not circular)
        if po_id in visited_nodes:
            return all_nodes.get(po_id)

        # Add to calculation stack for cycle detection
        calculation_stack.append(po_id)

        try:
            # Get purchase order with details
            po = self._get_po_with_details(po_id)
            if not po:
                logger.warning(
                    "Purchase order not found during transparency calculation",
                    po_id=str(po_id)
                )
                return None

            # Create transparency node
            node = self._create_transparency_node(po, depth)

            # Mark as visited
            visited_nodes.add(po_id)
            all_nodes[po_id] = node

            # Process input materials recursively
            if node.input_materials:
                for input_material in node.input_materials:
                    source_po_id = input_material.get("source_po_id")
                    if source_po_id:
                        try:
                            source_po_uuid = UUID(source_po_id)
                            contribution = input_material.get("percentage_contribution", 0) / 100.0
                            weighted_contribution = contribution_weight * contribution

                            # Recursive call
                            child_node = self._traverse_graph_recursive(
                                source_po_uuid,
                                visited_nodes,
                                calculation_stack,
                                all_nodes,
                                all_paths,
                                circular_references,
                                depth + 1,
                                weighted_contribution
                            )

                            if child_node and not child_node.is_circular:
                                # Update node scores based on child contributions
                                self._update_node_scores_from_child(
                                    node, child_node, contribution
                                )

                        except (ValueError, TypeError) as e:
                            logger.warning(
                                "Invalid source PO ID in input materials",
                                po_id=str(po_id),
                                source_po_id=source_po_id,
                                error=str(e)
                            )

            # Calculate base scores for this node
            self._calculate_base_scores(node)

            # Calculate confidence level
            node.confidence_level = self._calculate_node_confidence(node)

            return node

        finally:
            # Remove from calculation stack
            if calculation_stack and calculation_stack[-1] == po_id:
                calculation_stack.pop()

    def _get_po_with_details(self, po_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Get purchase order with all related details.

        Args:
            po_id: Purchase order UUID

        Returns:
            Dictionary with PO details or None if not found
        """
        try:
            po = self.db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
            if not po:
                return None

            # Get related company
            company = self.db.query(Company).filter(Company.id == po.seller_company_id).first()

            # Get related product
            product = self.db.query(Product).filter(Product.id == po.product_id).first()

            # Extract geographic coordinates and certifications from origin_data
            origin_data = po.origin_data or {}
            geographic_coordinates = origin_data.get("coordinates")
            certifications = origin_data.get("certifications", [])

            return {
                "id": po.id,
                "po_number": po.po_number,
                "seller_company_id": po.seller_company_id,
                "product_id": po.product_id,
                "quantity": po.quantity,
                "unit": po.unit,
                "origin_data": origin_data,
                "geographic_coordinates": geographic_coordinates,
                "certifications": certifications,
                "input_materials": po.input_materials or [],
                "company": {
                    "id": company.id if company else None,
                    "company_type": company.company_type if company else "unknown"
                },
                "product": {
                    "id": product.id if product else None,
                    "category": product.category if product else "unknown"
                }
            }

        except Exception as e:
            logger.error(
                "Error fetching PO details",
                po_id=str(po_id),
                error=str(e)
            )
            return None

    def _create_transparency_node(self, po_data: Dict[str, Any], depth: int) -> TransparencyNode:
        """
        Create a transparency node from purchase order data.

        Args:
            po_data: Purchase order data dictionary
            depth: Current depth in the graph

        Returns:
            TransparencyNode instance
        """
        # Extract basic information
        company_type = po_data.get("company", {}).get("company_type", "unknown")
        product_category = po_data.get("product", {}).get("category", "unknown")

        # Analyze transparency factors
        has_origin_data = bool(po_data.get("origin_data"))
        has_geographic_coordinates = bool(po_data.get("geographic_coordinates"))
        certifications = po_data.get("certifications") or []
        has_certifications = len(certifications) > 0

        # Count high-value certifications
        high_value_cert_count = sum(
            1 for cert in certifications
            if cert in self.HIGH_VALUE_CERTIFICATIONS
        )

        # Calculate data completeness score
        completeness_factors = [
            has_origin_data,
            has_geographic_coordinates,
            has_certifications,
            bool(po_data.get("quantity")),
            bool(po_data.get("unit")),
            company_type != "unknown",
            product_category != "unknown"
        ]
        data_completeness_score = sum(completeness_factors) / len(completeness_factors)

        # Create node
        node = TransparencyNode(
            po_id=po_data["id"],
            po_number=po_data["po_number"],
            company_id=po_data["seller_company_id"],
            company_type=company_type,
            product_id=po_data["product_id"],
            product_category=product_category,
            quantity=po_data["quantity"],
            unit=po_data["unit"],
            has_origin_data=has_origin_data,
            has_geographic_coordinates=has_geographic_coordinates,
            has_certifications=has_certifications,
            certification_count=len(certifications),
            high_value_cert_count=high_value_cert_count,
            data_completeness_score=data_completeness_score,
            input_materials=po_data.get("input_materials", []),
            depth=depth,
            visited_at=datetime.utcnow()
        )

        return node

    def _calculate_base_scores(self, node: TransparencyNode) -> None:
        """
        Calculate base TTM and TTP scores for a node.

        Args:
            node: TransparencyNode to calculate scores for
        """
        # Company type contribution
        company_score = self.COMPANY_TYPE_SCORES.get(node.company_type, 0.0)

        # Product category contribution
        product_score = self.PRODUCT_CATEGORY_SCORES.get(node.product_category, 0.0)

        # Origin data contribution
        origin_score = 1.0 if node.has_origin_data else 0.0

        # Geographic coordinates contribution
        geo_score = 1.0 if node.has_geographic_coordinates else 0.0

        # Certification contribution
        cert_base_score = 1.0 if node.has_certifications else 0.0
        cert_quality_bonus = min(node.high_value_cert_count * 0.1, 0.3)  # Max 30% bonus
        cert_score = min(cert_base_score + cert_quality_bonus, 1.0)

        # Input materials contribution (higher if has input materials)
        input_score = 1.0 if node.input_materials else 0.5

        # Calculate TTM (Transparency to Mill) - focuses on processing transparency
        node.base_ttm_score = (
            self.TRANSPARENCY_WEIGHTS["company_type"] * company_score +
            self.TRANSPARENCY_WEIGHTS["origin_data"] * origin_score +
            self.TRANSPARENCY_WEIGHTS["geographic_coordinates"] * geo_score +
            self.TRANSPARENCY_WEIGHTS["input_materials"] * input_score +
            0.15 * (1.0 if node.company_type in ["processor", "originator"] else 0.5)
        )

        # Calculate TTP (Transparency to Plantation) - focuses on origin transparency
        plantation_bonus = 0.2 if node.company_type == "originator" else 0.0
        node.base_ttp_score = (
            self.TRANSPARENCY_WEIGHTS["origin_data"] * origin_score +
            self.TRANSPARENCY_WEIGHTS["geographic_coordinates"] * geo_score +
            self.TRANSPARENCY_WEIGHTS["certifications"] * cert_score +
            self.TRANSPARENCY_WEIGHTS["company_type"] * company_score +
            plantation_bonus
        )

        # Ensure scores are within bounds
        node.base_ttm_score = min(node.base_ttm_score, 1.0)
        node.base_ttp_score = min(node.base_ttp_score, 1.0)

    def _update_node_scores_from_child(
        self,
        parent_node: TransparencyNode,
        child_node: TransparencyNode,
        contribution_weight: float
    ) -> None:
        """
        Update parent node scores based on child node contributions.

        Args:
            parent_node: Parent node to update
            child_node: Child node providing contribution
            contribution_weight: Weight of child's contribution (0.0 to 1.0)
        """
        # Apply degradation factor for transformation
        degradation = self._calculate_degradation_factor(1)  # One step degradation

        # Update weighted scores
        child_ttm_contribution = child_node.base_ttm_score * contribution_weight * degradation
        child_ttp_contribution = child_node.base_ttp_score * contribution_weight * degradation

        parent_node.weighted_ttm_score += child_ttm_contribution
        parent_node.weighted_ttp_score += child_ttp_contribution

    def _calculate_node_confidence(self, node: TransparencyNode) -> float:
        """
        Calculate confidence level for a node based on data completeness.

        Args:
            node: TransparencyNode to calculate confidence for

        Returns:
            Confidence level between 0.0 and 1.0
        """
        # Base confidence from data completeness
        base_confidence = node.data_completeness_score

        # Bonus for high-value certifications
        cert_bonus = min(node.high_value_cert_count * 0.05, 0.15)  # Max 15% bonus

        # Bonus for origin data quality
        origin_bonus = 0.1 if node.has_origin_data and node.has_geographic_coordinates else 0.0

        # Company type reliability factor
        company_reliability = {
            "originator": 1.0,
            "processor": 0.9,
            "brand": 0.8
        }.get(node.company_type, 0.7)

        # Calculate final confidence
        confidence = (base_confidence + cert_bonus + origin_bonus) * company_reliability

        return min(confidence, 1.0)

    def _calculate_final_scores(
        self,
        root_node: TransparencyNode,
        all_paths: List[TransparencyPath],
        all_nodes: Dict[UUID, TransparencyNode]
    ) -> Tuple[float, float, float]:
        """
        Calculate final TTM and TTP scores with confidence level.

        Args:
            root_node: Root node of the calculation
            all_paths: All discovered paths
            all_nodes: All analyzed nodes

        Returns:
            Tuple of (final_ttm, final_ttp, confidence)
        """
        if not all_nodes:
            return 0.0, 0.0, 0.0

        # Calculate weighted averages across all nodes
        total_weight = 0.0
        weighted_ttm = 0.0
        weighted_ttp = 0.0
        weighted_confidence = 0.0

        for node in all_nodes.values():
            if node.is_circular:
                continue

            # Weight by inverse depth (closer nodes have more weight)
            node_weight = 1.0 / (node.depth + 1)
            total_weight += node_weight

            # Combine base scores with weighted scores from children
            final_node_ttm = max(node.base_ttm_score, node.weighted_ttm_score)
            final_node_ttp = max(node.base_ttp_score, node.weighted_ttp_score)

            weighted_ttm += final_node_ttm * node_weight
            weighted_ttp += final_node_ttp * node_weight
            weighted_confidence += node.confidence_level * node_weight

        if total_weight == 0:
            return 0.0, 0.0, 0.0

        final_ttm = weighted_ttm / total_weight
        final_ttp = weighted_ttp / total_weight
        final_confidence = weighted_confidence / total_weight

        return final_ttm, final_ttp, final_confidence

    def _calculate_traceability_coverage(
        self,
        all_paths: List[TransparencyPath],
        all_nodes: Dict[UUID, TransparencyNode]
    ) -> Tuple[float, float]:
        """
        Calculate traced vs untraced material percentages.

        Args:
            all_paths: All discovered paths
            all_nodes: All analyzed nodes

        Returns:
            Tuple of (traced_percentage, untraced_percentage)
        """
        if not all_nodes:
            return 0.0, 100.0

        total_materials = 0.0
        traced_materials = 0.0

        for node in all_nodes.values():
            if node.is_circular:
                continue

            material_quantity = float(node.quantity) if node.quantity else 0.0
            total_materials += material_quantity

            # Consider material traced if it has sufficient transparency data
            if (node.has_origin_data or node.has_geographic_coordinates or
                node.has_certifications or node.input_materials):
                traced_materials += material_quantity

        if total_materials == 0:
            return 0.0, 100.0

        traced_percentage = (traced_materials / total_materials) * 100
        untraced_percentage = 100.0 - traced_percentage

        return traced_percentage, untraced_percentage

    def _calculate_degradation_factor(self, depth: int) -> float:
        """
        Calculate degradation factor based on supply chain depth.

        Args:
            depth: Depth in the supply chain

        Returns:
            Degradation factor between 0.0 and 1.0
        """
        if depth == 0:
            return 1.0

        # Apply degradation factor for each transformation step
        degradation = self.DEGRADATION_FACTOR_PER_STEP ** depth

        # Ensure minimum degradation doesn't go below 0.1 (10%)
        return max(degradation, 0.1)

    def detect_circular_references(self, po_id: UUID) -> List[UUID]:
        """
        Detect circular references in the supply chain graph.

        Args:
            po_id: Starting purchase order ID

        Returns:
            List of PO IDs involved in circular references
        """
        visited = set()
        recursion_stack = set()
        circular_refs = []

        def dfs(current_po_id: UUID) -> bool:
            if current_po_id in recursion_stack:
                circular_refs.append(current_po_id)
                return True

            if current_po_id in visited:
                return False

            visited.add(current_po_id)
            recursion_stack.add(current_po_id)

            # Get input materials
            po_data = self._get_po_with_details(current_po_id)
            if po_data and po_data.get("input_materials"):
                for input_material in po_data["input_materials"]:
                    source_po_id = input_material.get("source_po_id")
                    if source_po_id:
                        try:
                            source_uuid = UUID(source_po_id)
                            if dfs(source_uuid):
                                return True
                        except (ValueError, TypeError):
                            continue

            recursion_stack.remove(current_po_id)
            return False

        dfs(po_id)
        return circular_refs

    def get_transparency_improvement_suggestions(
        self,
        result: TransparencyResult
    ) -> List[Dict[str, Any]]:
        """
        Generate improvement suggestions based on transparency analysis.

        Args:
            result: TransparencyResult from calculation

        Returns:
            List of improvement suggestions
        """
        suggestions = []

        # Analyze TTM score
        if result.ttm_score < 0.7:
            suggestions.append({
                "category": "mill_transparency",
                "priority": "high",
                "description": "Improve mill-level transparency by linking more input materials",
                "expected_impact": 0.2,
                "implementation_effort": "medium"
            })

        # Analyze TTP score
        if result.ttp_score < 0.6:
            suggestions.append({
                "category": "plantation_transparency",
                "priority": "high",
                "description": "Enhance plantation-level transparency with more origin data",
                "expected_impact": 0.25,
                "implementation_effort": "high"
            })

        # Analyze confidence level
        if result.confidence_level < 0.8:
            suggestions.append({
                "category": "data_quality",
                "priority": "medium",
                "description": "Improve data completeness and quality across the supply chain",
                "expected_impact": 0.15,
                "implementation_effort": "low"
            })

        # Analyze circular references
        if result.circular_references:
            suggestions.append({
                "category": "data_integrity",
                "priority": "high",
                "description": f"Resolve {len(result.circular_references)} circular references in supply chain data",
                "expected_impact": 0.1,
                "implementation_effort": "medium"
            })

        # Analyze traceability coverage
        if result.untraced_percentage > 30:
            suggestions.append({
                "category": "traceability_coverage",
                "priority": "medium",
                "description": f"Improve traceability for {result.untraced_percentage:.1f}% of untraced materials",
                "expected_impact": 0.3,
                "implementation_effort": "high"
            })

        return suggestions

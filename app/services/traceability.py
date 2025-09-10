"""
Supply chain traceability calculation service.
"""
from typing import Optional, List, Dict, Any, Tuple, Set
from uuid import UUID
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import func
from dataclasses import dataclass
from enum import Enum

from app.models.purchase_order import PurchaseOrder
from app.models.company import Company
from app.models.product import Product
from app.services.purchase_order import PurchaseOrderService
from app.services.deterministic_transparency import DeterministicTransparencyService
from app.core.logging import get_logger

logger = get_logger(__name__)


class TransparencyLevel(str, Enum):
    """Transparency levels for scoring."""
    MILL = "mill"
    PLANTATION = "plantation"


@dataclass
class TraceabilityMetrics:
    """Metrics for traceability analysis."""
    total_nodes: int
    max_depth_reached: int
    mill_nodes: int
    plantation_nodes: int
    origin_data_nodes: int
    certified_nodes: int
    geographic_data_nodes: int
    input_material_links: int
    transparency_to_mill: float
    transparency_to_plantation: float
    calculation_timestamp: datetime


@dataclass
class TransparencyFactors:
    """Factors that contribute to transparency scoring."""
    has_origin_data: bool = False
    has_geographic_coordinates: bool = False
    has_certifications: bool = False
    certification_count: int = 0
    has_harvest_date: bool = False
    has_farm_identification: bool = False
    has_input_materials: bool = False
    input_material_count: int = 0
    company_type_score: float = 0.0
    product_category_score: float = 0.0
    data_completeness_score: float = 0.0
    certification_quality_score: float = 0.0


class TraceabilityCalculationService:
    """Service for calculating supply chain traceability and transparency scores."""
    
    def __init__(self, db: Session):
        self.db = db
        self.po_service = PurchaseOrderService(db)
        
        # Transparency scoring weights
        self.TRANSPARENCY_WEIGHTS = {
            "origin_data": 0.30,
            "geographic_coordinates": 0.25,
            "certifications": 0.20,
            "input_materials": 0.15,
            "company_type": 0.10
        }
        
        # Company type scoring
        self.COMPANY_TYPE_SCORES = {
            "originator": 1.0,  # Highest transparency potential
            "processor": 0.8,   # Good transparency potential
            "brand": 0.6,       # Lower transparency potential
            "trader": 0.4       # Lowest transparency potential
        }
        
        # Product category scoring
        self.PRODUCT_CATEGORY_SCORES = {
            "raw_material": 1.0,    # Highest traceability value
            "processed": 0.8,       # Good traceability value
            "finished_good": 0.6    # Lower traceability value
        }
        
        # High-value certifications for scoring
        self.HIGH_VALUE_CERTIFICATIONS = {
            "RSPO", "NDPE", "ISPO", "MSPO", "RTRS", "ISCC", 
            "Rainforest Alliance", "Organic", "Fair Trade"
        }
    
    def calculate_transparency_scores(self, purchase_order_id: UUID) -> TraceabilityMetrics:
        """
        Calculate comprehensive transparency scores for a purchase order.
        
        Args:
            purchase_order_id: Purchase order UUID
            
        Returns:
            Traceability metrics with transparency scores
        """
        logger.info("Starting transparency calculation", po_id=str(purchase_order_id))
        
        # Get the root purchase order
        root_po = self.po_service.get_purchase_order_with_details(str(purchase_order_id))
        if not root_po:
            raise ValueError(f"Purchase order {purchase_order_id} not found")
        
        # Perform comprehensive traceability analysis
        traceability_data = self._analyze_supply_chain(purchase_order_id)
        
        # Calculate transparency scores
        ttm_score = self._calculate_transparency_to_mill(traceability_data)
        ttp_score = self._calculate_transparency_to_plantation(traceability_data)
        
        # Create metrics object
        metrics = TraceabilityMetrics(
            total_nodes=traceability_data["total_nodes"],
            max_depth_reached=traceability_data["max_depth"],
            mill_nodes=traceability_data["mill_nodes"],
            plantation_nodes=traceability_data["plantation_nodes"],
            origin_data_nodes=traceability_data["origin_data_nodes"],
            certified_nodes=traceability_data["certified_nodes"],
            geographic_data_nodes=traceability_data["geographic_data_nodes"],
            input_material_links=traceability_data["input_material_links"],
            transparency_to_mill=ttm_score,
            transparency_to_plantation=ttp_score,
            calculation_timestamp=datetime.utcnow()
        )
        
        logger.info(
            "Transparency calculation completed",
            po_id=str(purchase_order_id),
            ttm_score=ttm_score,
            ttp_score=ttp_score,
            total_nodes=metrics.total_nodes
        )
        
        return metrics
    
    def _analyze_supply_chain(self, purchase_order_id: UUID, max_depth: int = 10) -> Dict[str, Any]:
        """
        Perform comprehensive supply chain analysis.
        
        Args:
            purchase_order_id: Root purchase order ID
            max_depth: Maximum depth to analyze
            
        Returns:
            Dictionary with supply chain analysis data
        """
        visited = set()
        analysis_data = {
            "total_nodes": 0,
            "max_depth": 0,
            "mill_nodes": 0,
            "plantation_nodes": 0,
            "origin_data_nodes": 0,
            "certified_nodes": 0,
            "geographic_data_nodes": 0,
            "input_material_links": 0,
            "nodes": [],
            "transparency_factors": []
        }
        
        def analyze_recursive(po_id: UUID, current_level: int, contribution_weight: float = 1.0):
            if current_level >= max_depth or po_id in visited:
                return
            
            visited.add(po_id)
            analysis_data["max_depth"] = max(analysis_data["max_depth"], current_level)
            analysis_data["total_nodes"] += 1
            
            # Get purchase order details
            po = self.po_service.get_purchase_order_with_details(str(po_id))
            if not po:
                return
            
            # Analyze this node
            node_factors = self._analyze_node_transparency(po)
            node_factors.company_type_score = self.COMPANY_TYPE_SCORES.get(
                po.seller_company.get("company_type", ""), 0.0
            )
            node_factors.product_category_score = self.PRODUCT_CATEGORY_SCORES.get(
                po.product.get("category", ""), 0.0
            )
            
            # Weight the factors by contribution
            weighted_factors = self._weight_transparency_factors(node_factors, contribution_weight)
            analysis_data["transparency_factors"].append(weighted_factors)
            
            # Count specific node types
            company_type = po.seller_company.get("company_type", "")
            if company_type == "processor":
                analysis_data["mill_nodes"] += 1
            elif company_type == "originator":
                analysis_data["plantation_nodes"] += 1
            
            if node_factors.has_origin_data:
                analysis_data["origin_data_nodes"] += 1
            if node_factors.has_certifications:
                analysis_data["certified_nodes"] += 1
            if node_factors.has_geographic_coordinates:
                analysis_data["geographic_data_nodes"] += 1
            
            # Store node data
            analysis_data["nodes"].append({
                "po_id": po_id,
                "level": current_level,
                "company_type": company_type,
                "product_category": po.product.get("category", ""),
                "transparency_factors": node_factors,
                "contribution_weight": contribution_weight
            })
            
            # Recursively analyze input materials
            if po.input_materials:
                analysis_data["input_material_links"] += len(po.input_materials)
                for input_material in po.input_materials:
                    source_po_id_str = input_material["source_po_id"]

                    # Handle both string and UUID formats
                    try:
                        if isinstance(source_po_id_str, str):
                            source_po_id = UUID(source_po_id_str)
                        elif hasattr(source_po_id_str, 'hex'):  # It's already a UUID
                            source_po_id = source_po_id_str
                        else:
                            # Try to convert to string first, then to UUID
                            source_po_id = UUID(str(source_po_id_str))
                    except (ValueError, TypeError) as e:
                        logger.warning(
                            "Invalid source_po_id format",
                            source_po_id=source_po_id_str,
                            type=type(source_po_id_str).__name__,
                            error=str(e)
                        )
                        continue

                    contribution = input_material.get("percentage_contribution", 0) / 100.0
                    weighted_contribution = contribution_weight * contribution

                    analyze_recursive(source_po_id, current_level + 1, weighted_contribution)
        
        # Start analysis from root
        analyze_recursive(purchase_order_id, 0)
        
        return analysis_data
    
    def _analyze_node_transparency(self, po) -> TransparencyFactors:
        """
        Analyze transparency factors for a single purchase order node.
        
        Args:
            po: Purchase order with details
            
        Returns:
            Transparency factors for the node
        """
        factors = TransparencyFactors()
        
        # Analyze origin data
        if po.origin_data:
            factors.has_origin_data = True
            
            # Check for geographic coordinates
            if "geographic_coordinates" in po.origin_data:
                coords = po.origin_data["geographic_coordinates"]
                if isinstance(coords, dict) and "latitude" in coords and "longitude" in coords:
                    factors.has_geographic_coordinates = True
            
            # Check for certifications
            if "certifications" in po.origin_data:
                certs = po.origin_data["certifications"]
                if isinstance(certs, list) and len(certs) > 0:
                    factors.has_certifications = True
                    factors.certification_count = len(certs)
                    
                    # Calculate certification quality score
                    high_value_certs = sum(1 for cert in certs if cert in self.HIGH_VALUE_CERTIFICATIONS)
                    factors.certification_quality_score = min(high_value_certs / 3.0, 1.0)  # Max score with 3+ high-value certs
            
            # Check for harvest date
            if "harvest_date" in po.origin_data and po.origin_data["harvest_date"]:
                factors.has_harvest_date = True
            
            # Check for farm identification
            if "farm_identification" in po.origin_data and po.origin_data["farm_identification"]:
                factors.has_farm_identification = True
        
        # Analyze input materials
        if po.input_materials:
            factors.has_input_materials = True
            factors.input_material_count = len(po.input_materials)
        
        # Calculate data completeness score
        completeness_factors = [
            factors.has_origin_data,
            factors.has_geographic_coordinates,
            factors.has_certifications,
            factors.has_harvest_date,
            factors.has_farm_identification,
            factors.has_input_materials
        ]
        factors.data_completeness_score = sum(completeness_factors) / len(completeness_factors)
        
        return factors
    
    def _weight_transparency_factors(self, factors: TransparencyFactors, weight: float) -> TransparencyFactors:
        """Apply contribution weight to transparency factors."""
        weighted_factors = TransparencyFactors()
        
        # Apply weight to boolean factors (convert to weighted scores)
        weighted_factors.has_origin_data = factors.has_origin_data
        weighted_factors.has_geographic_coordinates = factors.has_geographic_coordinates
        weighted_factors.has_certifications = factors.has_certifications
        weighted_factors.has_harvest_date = factors.has_harvest_date
        weighted_factors.has_farm_identification = factors.has_farm_identification
        weighted_factors.has_input_materials = factors.has_input_materials
        
        # Apply weight to numeric factors
        weighted_factors.certification_count = factors.certification_count
        weighted_factors.input_material_count = factors.input_material_count
        weighted_factors.company_type_score = factors.company_type_score * weight
        weighted_factors.product_category_score = factors.product_category_score * weight
        weighted_factors.data_completeness_score = factors.data_completeness_score * weight
        weighted_factors.certification_quality_score = factors.certification_quality_score * weight
        
        return weighted_factors

    def _calculate_transparency_to_mill(self, traceability_data: Dict[str, Any]) -> float:
        """
        Calculate Transparency to Mill (TTM) score.

        TTM measures how well we can trace back to processing facilities (mills).

        Args:
            traceability_data: Supply chain analysis data

        Returns:
            TTM score between 0.0 and 1.0
        """
        if traceability_data["total_nodes"] == 0:
            return 0.0

        # Base score from mill presence
        mill_coverage = min(traceability_data["mill_nodes"] / max(traceability_data["total_nodes"], 1), 1.0)

        # Input material linkage score
        linkage_score = min(traceability_data["input_material_links"] / max(traceability_data["total_nodes"], 1), 1.0)

        # Data completeness score (weighted average of all nodes)
        total_completeness = sum(
            factors.data_completeness_score
            for factors in traceability_data["transparency_factors"]
        )
        completeness_score = total_completeness / max(len(traceability_data["transparency_factors"]), 1)

        # Company type score (weighted average)
        total_company_score = sum(
            factors.company_type_score
            for factors in traceability_data["transparency_factors"]
        )
        company_score = total_company_score / max(len(traceability_data["transparency_factors"]), 1)

        # Geographic data coverage
        geographic_coverage = min(
            traceability_data["geographic_data_nodes"] / max(traceability_data["total_nodes"], 1),
            1.0
        )

        # Calculate weighted TTM score
        ttm_score = (
            self.TRANSPARENCY_WEIGHTS["origin_data"] * completeness_score +
            self.TRANSPARENCY_WEIGHTS["geographic_coordinates"] * geographic_coverage +
            self.TRANSPARENCY_WEIGHTS["input_materials"] * linkage_score +
            self.TRANSPARENCY_WEIGHTS["company_type"] * company_score +
            0.15 * mill_coverage  # Mill-specific weight
        )

        return min(ttm_score, 1.0)

    def _calculate_transparency_to_plantation(self, traceability_data: Dict[str, Any]) -> float:
        """
        Calculate Transparency to Plantation (TTP) score.

        TTP measures how well we can trace back to the original source (plantations).

        Args:
            traceability_data: Supply chain analysis data

        Returns:
            TTP score between 0.0 and 1.0
        """
        if traceability_data["total_nodes"] == 0:
            return 0.0

        # Base score from plantation presence
        plantation_coverage = min(
            traceability_data["plantation_nodes"] / max(traceability_data["total_nodes"], 1),
            1.0
        )

        # Origin data coverage
        origin_coverage = min(
            traceability_data["origin_data_nodes"] / max(traceability_data["total_nodes"], 1),
            1.0
        )

        # Certification coverage
        certification_coverage = min(
            traceability_data["certified_nodes"] / max(traceability_data["total_nodes"], 1),
            1.0
        )

        # Geographic data coverage
        geographic_coverage = min(
            traceability_data["geographic_data_nodes"] / max(traceability_data["total_nodes"], 1),
            1.0
        )

        # Certification quality score (weighted average)
        total_cert_quality = sum(
            factors.certification_quality_score
            for factors in traceability_data["transparency_factors"]
        )
        cert_quality_score = total_cert_quality / max(len(traceability_data["transparency_factors"]), 1)

        # Supply chain depth bonus (deeper chains get higher scores)
        depth_bonus = min(traceability_data["max_depth"] / 5.0, 0.2)  # Max 20% bonus for depth >= 5

        # Calculate weighted TTP score
        ttp_score = (
            self.TRANSPARENCY_WEIGHTS["origin_data"] * origin_coverage +
            self.TRANSPARENCY_WEIGHTS["geographic_coordinates"] * geographic_coverage +
            self.TRANSPARENCY_WEIGHTS["certifications"] * (certification_coverage + cert_quality_score) / 2 +
            0.20 * plantation_coverage +  # Plantation-specific weight
            depth_bonus
        )

        return min(ttp_score, 1.0)

    def update_transparency_scores(self, purchase_order_id: UUID) -> TraceabilityMetrics:
        """
        Calculate transparency metrics for a purchase order.

        SINGLE SOURCE OF TRUTH: Uses deterministic transparency based on explicit user-created links.
        No fallbacks, no algorithmic guessing, 100% auditable.

        Args:
            purchase_order_id: Purchase order UUID

        Returns:
            Traceability metrics based on deterministic calculation
        """
        # Get the purchase order
        po = self.db.query(PurchaseOrder).filter(PurchaseOrder.id == purchase_order_id).first()
        if not po:
            raise ValueError(f"Purchase order {purchase_order_id} not found")

        # SINGLE SOURCE OF TRUTH: Deterministic transparency calculation
        deterministic_service = DeterministicTransparencyService(self.db)
        deterministic_metrics = deterministic_service.get_company_transparency_metrics(
            company_id=po.buyer_company_id,
            refresh_data=True  # Refresh for accurate calculation
        )

        # Simple, auditable percentages
        mill_percentage = deterministic_metrics.transparency_to_mill_percentage
        plantation_percentage = deterministic_metrics.transparency_to_plantation_percentage

        logger.info(
            "Transparency metrics calculated (SINGLE SOURCE OF TRUTH)",
            po_id=str(purchase_order_id),
            mill_percentage=mill_percentage,
            plantation_percentage=plantation_percentage,
            total_volume=float(deterministic_metrics.total_volume),
            traced_pos=deterministic_metrics.traced_purchase_orders,
            total_pos=deterministic_metrics.total_purchase_orders,
            method="deterministic_single_source_of_truth"
        )

        # Create TraceabilityMetrics for return compatibility
        return TraceabilityMetrics(
            purchase_order_id=purchase_order_id,
            transparency_to_mill=mill_percentage / 100.0,  # Convert to 0-1 scale for compatibility
            transparency_to_plantation=plantation_percentage / 100.0,  # Convert to 0-1 scale for compatibility
            calculation_timestamp=deterministic_metrics.calculation_timestamp,
            total_nodes=deterministic_metrics.total_purchase_orders,
            traced_nodes=deterministic_metrics.traced_purchase_orders,
            max_depth=1,  # Deterministic is single-level
            circular_references=[],  # No circular references in deterministic system
            data_completeness_score=1.0,  # Always complete - based on explicit user actions
            confidence_level=1.0  # Always 100% confidence - based on explicit user actions
        )

    def bulk_update_transparency_scores(
        self,
        company_id: Optional[UUID] = None,
        max_age_hours: int = 24
    ) -> Dict[str, Any]:
        """
        Bulk update transparency scores for purchase orders.

        Args:
            company_id: Optional company ID to filter by
            max_age_hours: Only update scores older than this many hours

        Returns:
            Summary of bulk update operation
        """
        # Build query for purchase orders that need score updates
        query = self.db.query(PurchaseOrder).filter(
            PurchaseOrder.status.in_(["confirmed", "in_transit", "delivered"])
        )

        # Filter by company if specified
        if company_id:
            query = query.filter(
                (PurchaseOrder.buyer_company_id == company_id) |
                (PurchaseOrder.seller_company_id == company_id)
            )

        # Filter by age of last calculation
        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
        query = query.filter(
            (PurchaseOrder.transparency_calculated_at.is_(None)) |
            (PurchaseOrder.transparency_calculated_at < cutoff_time)
        )

        purchase_orders = query.all()

        updated_count = 0
        error_count = 0
        results = []

        logger.info(
            "Starting bulk transparency score update",
            total_pos=len(purchase_orders),
            company_id=str(company_id) if company_id else None
        )

        for po in purchase_orders:
            try:
                metrics = self.update_transparency_scores(po.id)
                results.append({
                    "po_id": str(po.id),
                    "po_number": po.po_number,
                    "ttm_score": metrics.transparency_to_mill,
                    "ttp_score": metrics.transparency_to_plantation,
                    "status": "updated"
                })
                updated_count += 1

            except Exception as e:
                logger.error(
                    "Failed to update transparency scores",
                    po_id=str(po.id),
                    error=str(e)
                )
                results.append({
                    "po_id": str(po.id),
                    "po_number": po.po_number,
                    "status": "error",
                    "error": str(e)
                })
                error_count += 1

        summary = {
            "total_processed": len(purchase_orders),
            "updated_count": updated_count,
            "error_count": error_count,
            "results": results,
            "timestamp": datetime.utcnow().isoformat()
        }

        logger.info(
            "Bulk transparency score update completed",
            **{k: v for k, v in summary.items() if k != "results"}
        )

        return summary

    def get_transparency_analytics(self, company_id: UUID) -> Dict[str, Any]:
        """
        Get transparency analytics for a company.

        Args:
            company_id: Company UUID

        Returns:
            Transparency analytics data
        """
        # Query purchase orders for the company
        pos = self.db.query(PurchaseOrder).filter(
            (PurchaseOrder.buyer_company_id == company_id) |
            (PurchaseOrder.seller_company_id == company_id)
        ).filter(
            PurchaseOrder.transparency_to_mill.isnot(None)
        ).all()

        if not pos:
            return {
                "total_purchase_orders": 0,
                "average_ttm_score": 0.0,
                "average_ttp_score": 0.0,
                "transparency_distribution": {},
                "improvement_opportunities": []
            }

        # Calculate analytics
        ttm_scores = [float(po.transparency_to_mill) for po in pos if po.transparency_to_mill]
        ttp_scores = [float(po.transparency_to_plantation) for po in pos if po.transparency_to_plantation]

        avg_ttm = sum(ttm_scores) / len(ttm_scores) if ttm_scores else 0.0
        avg_ttp = sum(ttp_scores) / len(ttp_scores) if ttp_scores else 0.0

        # Transparency distribution
        distribution = {
            "high_transparency": len([s for s in ttp_scores if s >= 0.8]),
            "medium_transparency": len([s for s in ttp_scores if 0.5 <= s < 0.8]),
            "low_transparency": len([s for s in ttp_scores if s < 0.5])
        }

        # Improvement opportunities
        opportunities = []
        if avg_ttm < 0.7:
            opportunities.append("Improve mill-level traceability by linking more input materials")
        if avg_ttp < 0.6:
            opportunities.append("Enhance plantation-level transparency with more origin data")

        low_transparency_count = distribution["low_transparency"]
        if low_transparency_count > len(pos) * 0.3:
            opportunities.append("Focus on improving transparency for low-scoring purchase orders")

        return {
            "total_purchase_orders": len(pos),
            "average_ttm_score": round(avg_ttm, 3),
            "average_ttp_score": round(avg_ttp, 3),
            "transparency_distribution": distribution,
            "improvement_opportunities": opportunities,
            "last_updated": datetime.utcnow().isoformat()
        }

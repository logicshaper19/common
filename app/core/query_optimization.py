"""
Database query optimization utilities for complex transparency calculations.
"""
from typing import List, Dict, Any, Optional, Tuple, Set
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session, joinedload, selectinload, contains_eager
from sqlalchemy import and_, or_, func, text, select, case
from sqlalchemy.sql import Select

from app.models.purchase_order import PurchaseOrder
from app.models.company import Company
from app.models.product import Product
# BusinessRelationship model removed - using simple relationship checking instead
from app.core.logging import get_logger
from app.core.input_validation import safe_execute_query, validate_sql_query_params

logger = get_logger(__name__)


class QueryOptimizer:
    """
    Database query optimization utilities for complex transparency calculations.
    
    Features:
    - Optimized graph traversal queries
    - Batch loading strategies
    - Query result caching
    - Index usage optimization
    - Query performance monitoring
    """
    
    def __init__(self, db: Session):
        self.db = db
        self._query_cache: Dict[str, Any] = {}
    
    def get_po_graph_optimized(
        self,
        root_po_ids: List[UUID],
        max_depth: int = 10,
        include_transparency_scores: bool = True
    ) -> Dict[UUID, Dict[str, Any]]:
        """
        Optimized purchase order graph traversal for transparency calculations.
        
        Args:
            root_po_ids: Starting purchase order IDs
            max_depth: Maximum traversal depth
            include_transparency_scores: Whether to include cached transparency scores
            
        Returns:
            Dictionary mapping PO IDs to their data and relationships
        """
        po_graph = {}
        visited = set()
        current_level = set(root_po_ids)
        
        for depth in range(max_depth):
            if not current_level:
                break
            
            # Batch load current level POs with optimized joins
            pos = self._batch_load_pos_with_relationships(
                list(current_level),
                include_transparency_scores
            )
            
            next_level = set()
            
            for po in pos:
                if po.id in visited:
                    continue
                
                visited.add(po.id)
                
                # Extract input material PO IDs
                input_po_ids = []
                if po.input_materials:
                    for material in po.input_materials:
                        if "source_po_id" in material:
                            input_po_ids.append(UUID(material["source_po_id"]))
                
                po_graph[po.id] = {
                    "po": po,
                    "input_po_ids": input_po_ids,
                    "depth": depth,
                    "transparency_to_mill": po.transparency_to_mill,
                    "transparency_to_plantation": po.transparency_to_plantation,
                    "transparency_calculated_at": po.transparency_calculated_at
                }
                
                # Add input POs to next level
                for input_po_id in input_po_ids:
                    if input_po_id not in visited:
                        next_level.add(input_po_id)
            
            current_level = next_level
        
        logger.debug(
            "PO graph traversal completed",
            root_pos=len(root_po_ids),
            total_pos=len(po_graph),
            max_depth_reached=depth
        )
        
        return po_graph
    
    def _batch_load_pos_with_relationships(
        self,
        po_ids: List[UUID],
        include_transparency_scores: bool = True
    ) -> List[PurchaseOrder]:
        """
        Batch load purchase orders with optimized joins.
        
        Args:
            po_ids: Purchase order IDs to load
            include_transparency_scores: Whether to include transparency data
            
        Returns:
            List of PurchaseOrder objects with relationships loaded
        """
        query = (
            self.db.query(PurchaseOrder)
            .options(
                joinedload(PurchaseOrder.buyer_company),
                joinedload(PurchaseOrder.seller_company),
                joinedload(PurchaseOrder.product)
            )
            .filter(PurchaseOrder.id.in_(po_ids))
        )
        
        if include_transparency_scores:
            # Only load POs with recent transparency calculations
            query = query.filter(
                or_(
                    PurchaseOrder.transparency_calculated_at.is_(None),
                    PurchaseOrder.transparency_calculated_at >= datetime.utcnow().replace(hour=0, minute=0, second=0)
                )
            )
        
        return query.all()
    
    def get_company_po_summary_optimized(
        self,
        company_id: UUID,
        status_filter: Optional[List[str]] = None,
        date_range: Optional[Tuple[datetime, datetime]] = None
    ) -> Dict[str, Any]:
        """
        Optimized company purchase order summary query.
        
        Args:
            company_id: Company ID
            status_filter: Optional status filter
            date_range: Optional date range filter
            
        Returns:
            Summary statistics for company's purchase orders
        """
        # Base query with optimized aggregations
        base_query = self.db.query(PurchaseOrder).filter(
            or_(
                PurchaseOrder.buyer_company_id == company_id,
                PurchaseOrder.seller_company_id == company_id
            )
        )
        
        if status_filter:
            base_query = base_query.filter(PurchaseOrder.status.in_(status_filter))
        
        if date_range:
            start_date, end_date = date_range
            base_query = base_query.filter(
                and_(
                    PurchaseOrder.created_at >= start_date,
                    PurchaseOrder.created_at <= end_date
                )
            )
        
        # Optimized aggregation query
        summary_query = (
            self.db.query(
                func.count(PurchaseOrder.id).label('total_pos'),
                func.count(
                    case([(PurchaseOrder.buyer_company_id == company_id, 1)])
                ).label('as_buyer'),
                func.count(
                    case([(PurchaseOrder.seller_company_id == company_id, 1)])
                ).label('as_seller'),
                func.sum(PurchaseOrder.quantity).label('total_quantity'),
                func.avg(PurchaseOrder.transparency_to_mill).label('avg_ttm'),
                func.avg(PurchaseOrder.transparency_to_plantation).label('avg_ttp'),
                func.count(
                    case([(PurchaseOrder.transparency_calculated_at.isnot(None), 1)])
                ).label('transparency_calculated_count')
            )
            .filter(base_query.whereclause)
        ).first()
        
        # Status breakdown query
        status_breakdown = (
            self.db.query(
                PurchaseOrder.status,
                func.count(PurchaseOrder.id).label('count')
            )
            .filter(base_query.whereclause)
            .group_by(PurchaseOrder.status)
        ).all()
        
        return {
            "total_pos": summary_query.total_pos or 0,
            "as_buyer": summary_query.as_buyer or 0,
            "as_seller": summary_query.as_seller or 0,
            "total_quantity": float(summary_query.total_quantity or 0),
            "average_transparency_to_mill": float(summary_query.avg_ttm or 0),
            "average_transparency_to_plantation": float(summary_query.avg_ttp or 0),
            "transparency_calculated_count": summary_query.transparency_calculated_count or 0,
            "status_breakdown": {
                status: count for status, count in status_breakdown
            }
        }
    
    def get_transparency_calculation_candidates(
        self,
        limit: int = 100,
        priority_companies: Optional[List[UUID]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get purchase orders that need transparency calculation, optimized for batch processing.
        
        Args:
            limit: Maximum number of POs to return
            priority_companies: Companies to prioritize
            
        Returns:
            List of PO data for transparency calculation
        """
        # Base query for POs needing calculation
        base_query = (
            self.db.query(PurchaseOrder)
            .filter(
                and_(
                    PurchaseOrder.status == 'confirmed',
                    or_(
                        PurchaseOrder.transparency_calculated_at.is_(None),
                        PurchaseOrder.transparency_calculated_at < PurchaseOrder.updated_at
                    )
                )
            )
            .options(
                joinedload(PurchaseOrder.buyer_company),
                joinedload(PurchaseOrder.seller_company),
                joinedload(PurchaseOrder.product)
            )
        )
        
        # Prioritize certain companies
        if priority_companies:
            priority_query = base_query.filter(
                or_(
                    PurchaseOrder.buyer_company_id.in_(priority_companies),
                    PurchaseOrder.seller_company_id.in_(priority_companies)
                )
            ).limit(limit // 2)
            
            regular_query = base_query.filter(
                and_(
                    PurchaseOrder.buyer_company_id.notin_(priority_companies),
                    PurchaseOrder.seller_company_id.notin_(priority_companies)
                )
            ).limit(limit // 2)
            
            pos = priority_query.all() + regular_query.all()
        else:
            pos = base_query.order_by(PurchaseOrder.created_at.desc()).limit(limit).all()
        
        # Convert to calculation format
        candidates = []
        for po in pos:
            candidates.append({
                "po_id": po.id,
                "po_number": po.po_number,
                "buyer_company_id": po.buyer_company_id,
                "seller_company_id": po.seller_company_id,
                "product_id": po.product_id,
                "input_materials": po.input_materials or [],
                "origin_data": po.origin_data or {},
                "last_calculated": po.transparency_calculated_at,
                "priority_score": self._calculate_priority_score(po, priority_companies)
            })
        
        # Sort by priority score
        candidates.sort(key=lambda x: x["priority_score"], reverse=True)
        
        return candidates
    
    def _calculate_priority_score(
        self,
        po: PurchaseOrder,
        priority_companies: Optional[List[UUID]] = None
    ) -> float:
        """Calculate priority score for transparency calculation."""
        score = 0.0
        
        # Base score from age (newer = higher priority)
        days_old = (datetime.utcnow() - po.created_at).days
        score += max(0, 30 - days_old)  # Max 30 points for age
        
        # Priority company bonus
        if priority_companies:
            if po.buyer_company_id in priority_companies or po.seller_company_id in priority_companies:
                score += 50
        
        # Never calculated bonus
        if po.transparency_calculated_at is None:
            score += 20
        
        # Large quantity bonus
        if po.quantity and po.quantity > 1000:
            score += 10
        
        return score
    
    def get_supply_chain_network_optimized(
        self,
        company_ids: List[UUID],
        relationship_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Optimized supply chain network query for visualization.
        
        Args:
            company_ids: Company IDs to include in network
            relationship_types: Optional relationship type filter
            
        Returns:
            Network data with nodes and edges
        """
        # Get companies with optimized loading
        companies_query = (
            self.db.query(Company)
            .filter(Company.id.in_(company_ids))
        )
        companies = {c.id: c for c in companies_query.all()}
        
        # Get business relationships
        relationships_query = (
            self.db.query(BusinessRelationship)
            .filter(
                and_(
                    BusinessRelationship.status == 'active',
                    or_(
                        BusinessRelationship.buyer_company_id.in_(company_ids),
                        BusinessRelationship.seller_company_id.in_(company_ids)
                    )
                )
            )
        )
        
        if relationship_types:
            relationships_query = relationships_query.filter(
                BusinessRelationship.relationship_type.in_(relationship_types)
            )
        
        relationships = relationships_query.all()
        
        # Get PO statistics for edges
        po_stats_query = (
            self.db.query(
                PurchaseOrder.buyer_company_id,
                PurchaseOrder.seller_company_id,
                func.count(PurchaseOrder.id).label('po_count'),
                func.sum(PurchaseOrder.quantity).label('total_quantity'),
                func.avg(PurchaseOrder.transparency_to_mill).label('avg_transparency')
            )
            .filter(
                and_(
                    PurchaseOrder.status.in_(['confirmed', 'delivered']),
                    or_(
                        PurchaseOrder.buyer_company_id.in_(company_ids),
                        PurchaseOrder.seller_company_id.in_(company_ids)
                    )
                )
            )
            .group_by(PurchaseOrder.buyer_company_id, PurchaseOrder.seller_company_id)
        ).all()
        
        # Build network structure
        nodes = []
        edges = []
        
        for company in companies.values():
            nodes.append({
                "id": str(company.id),
                "name": company.name,
                "type": company.company_type,
                "created_at": company.created_at.isoformat()
            })
        
        # Create edges from relationships and PO stats
        po_stats_map = {
            (stat.buyer_company_id, stat.seller_company_id): stat
            for stat in po_stats_query
        }
        
        for rel in relationships:
            edge_key = (rel.buyer_company_id, rel.seller_company_id)
            po_stat = po_stats_map.get(edge_key)
            
            edges.append({
                "source": str(rel.buyer_company_id),
                "target": str(rel.seller_company_id),
                "relationship_type": rel.relationship_type,
                "established_at": rel.established_at.isoformat(),
                "po_count": po_stat.po_count if po_stat else 0,
                "total_quantity": float(po_stat.total_quantity or 0) if po_stat else 0,
                "average_transparency": float(po_stat.avg_transparency or 0) if po_stat else 0
            })
        
        return {
            "nodes": nodes,
            "edges": edges,
            "metrics": {
                "total_companies": len(nodes),
                "total_relationships": len(edges),
                "network_density": len(edges) / (len(nodes) * (len(nodes) - 1) / 2) if len(nodes) > 1 else 0
            }
        }
    
    def execute_raw_optimized_query(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute raw SQL query with optimization hints and security validation.

        Args:
            query: Raw SQL query
            params: Query parameters

        Returns:
            Query results as list of dictionaries
        """
        try:
            # Use safe query execution with parameter validation
            result = safe_execute_query(self.db, query, params)
            columns = result.keys()
            return [dict(zip(columns, row)) for row in result.fetchall()]
        except Exception as e:
            logger.error("Raw query execution failed", query=query[:100], error=str(e))
            raise
    
    def clear_query_cache(self):
        """Clear internal query cache."""
        self._query_cache.clear()
        logger.debug("Query cache cleared")

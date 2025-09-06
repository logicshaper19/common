"""
Purchase order traceability service.

This module handles supply chain tracing operations, building
traceability trees and tracking material flows.
"""

from typing import Dict, Any, List, Optional, Set
from uuid import UUID
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_

from app.models.purchase_order import PurchaseOrder
from app.schemas.purchase_order import (
    TraceabilityRequest, 
    TraceabilityResponse, 
    TraceabilityNode
)
from app.core.logging import get_logger
from .repository import PurchaseOrderRepository
from .exceptions import PurchaseOrderTraceabilityError

logger = get_logger(__name__)


class TraceabilityService:
    """Handles supply chain tracing operations."""
    
    def __init__(self, db: Session):
        self.db = db
        self.repository = PurchaseOrderRepository(db)
    
    def trace_supply_chain(self, request: TraceabilityRequest) -> TraceabilityResponse:
        """
        Trace supply chain for a purchase order.
        
        Args:
            request: Traceability request with parameters
            
        Returns:
            Complete traceability response
            
        Raises:
            PurchaseOrderTraceabilityError: If tracing fails
        """
        try:
            logger.info(
                "Starting supply chain tracing",
                po_id=str(request.po_id),
                max_depth=request.max_depth,
                direction=request.direction
            )
            
            # Get the root purchase order
            root_po = self.repository.get_by_id_or_raise(request.po_id)
            
            # Build traceability tree
            if request.direction == "upstream":
                tree = self._build_upstream_tree(root_po, request.max_depth)
            elif request.direction == "downstream":
                tree = self._build_downstream_tree(root_po, request.max_depth)
            else:  # both
                upstream_tree = self._build_upstream_tree(root_po, request.max_depth)
                downstream_tree = self._build_downstream_tree(root_po, request.max_depth)
                tree = self._merge_trees(upstream_tree, downstream_tree, root_po)
            
            # Calculate summary statistics
            summary = self._calculate_traceability_summary(tree)
            
            response = TraceabilityResponse(
                po_id=request.po_id,
                direction=request.direction,
                max_depth=request.max_depth,
                tree=tree,
                summary=summary,
                generated_at=logger.info("Supply chain tracing completed successfully")
            )
            
            logger.info(
                "Supply chain tracing completed successfully",
                po_id=str(request.po_id),
                total_nodes=summary.get("total_nodes", 0),
                max_depth_reached=summary.get("max_depth_reached", 0)
            )
            
            return response
            
        except Exception as e:
            logger.error(
                "Failed to trace supply chain",
                po_id=str(request.po_id),
                error=str(e)
            )
            raise PurchaseOrderTraceabilityError(
                "Failed to trace supply chain",
                po_id=request.po_id,
                trace_operation="full_trace"
            )
    
    def get_traceability_data(
        self, 
        po_id: UUID, 
        max_depth: int = 5
    ) -> Dict[str, Any]:
        """
        Get simplified traceability data for a purchase order.
        
        Args:
            po_id: Purchase order ID
            max_depth: Maximum depth to trace
            
        Returns:
            Simplified traceability data
        """
        try:
            # Create a simple request
            request = TraceabilityRequest(
                po_id=po_id,
                direction="both",
                max_depth=max_depth
            )
            
            # Get full traceability
            response = self.trace_supply_chain(request)
            
            # Return simplified format
            return {
                "po_id": str(po_id),
                "total_nodes": response.summary.get("total_nodes", 0),
                "upstream_nodes": response.summary.get("upstream_nodes", 0),
                "downstream_nodes": response.summary.get("downstream_nodes", 0),
                "max_depth_reached": response.summary.get("max_depth_reached", 0),
                "tree": response.tree.model_dump() if response.tree else None
            }
            
        except Exception as e:
            logger.error(
                "Failed to get traceability data",
                po_id=str(po_id),
                error=str(e)
            )
            raise PurchaseOrderTraceabilityError(
                "Failed to get traceability data",
                po_id=po_id,
                trace_operation="simple_trace"
            )
    
    def get_upstream_materials(self, po_id: UUID) -> List[TraceabilityNode]:
        """
        Get upstream materials for a purchase order.
        
        Args:
            po_id: Purchase order ID
            
        Returns:
            List of upstream material nodes
        """
        try:
            root_po = self.repository.get_by_id_or_raise(po_id)
            upstream_tree = self._build_upstream_tree(root_po, max_depth=3)
            
            # Flatten tree to get all upstream nodes
            upstream_nodes = []
            self._flatten_tree_nodes(upstream_tree, upstream_nodes)
            
            return upstream_nodes
            
        except Exception as e:
            logger.error(
                "Failed to get upstream materials",
                po_id=str(po_id),
                error=str(e)
            )
            raise PurchaseOrderTraceabilityError(
                "Failed to get upstream materials",
                po_id=po_id,
                trace_operation="upstream_materials"
            )
    
    def _build_upstream_tree(
        self, 
        root_po: PurchaseOrder, 
        max_depth: int,
        current_depth: int = 0,
        visited: Optional[Set[UUID]] = None
    ) -> TraceabilityNode:
        """
        Build upstream traceability tree.
        
        Args:
            root_po: Root purchase order
            max_depth: Maximum depth to traverse
            current_depth: Current depth in traversal
            visited: Set of visited PO IDs to prevent cycles
            
        Returns:
            Traceability node with upstream tree
        """
        if visited is None:
            visited = set()
        
        # Prevent infinite loops
        if root_po.id in visited or current_depth >= max_depth:
            return self._create_node_from_po(root_po, current_depth, [])
        
        visited.add(root_po.id)
        
        # Find upstream purchase orders (input materials)
        upstream_pos = self._find_upstream_pos(root_po)
        
        # Recursively build upstream nodes
        upstream_nodes = []
        for upstream_po in upstream_pos:
            if upstream_po.id not in visited:
                upstream_node = self._build_upstream_tree(
                    upstream_po, max_depth, current_depth + 1, visited.copy()
                )
                upstream_nodes.append(upstream_node)
        
        return self._create_node_from_po(root_po, current_depth, upstream_nodes)
    
    def _build_downstream_tree(
        self, 
        root_po: PurchaseOrder, 
        max_depth: int,
        current_depth: int = 0,
        visited: Optional[Set[UUID]] = None
    ) -> TraceabilityNode:
        """
        Build downstream traceability tree.
        
        Args:
            root_po: Root purchase order
            max_depth: Maximum depth to traverse
            current_depth: Current depth in traversal
            visited: Set of visited PO IDs to prevent cycles
            
        Returns:
            Traceability node with downstream tree
        """
        if visited is None:
            visited = set()
        
        # Prevent infinite loops
        if root_po.id in visited or current_depth >= max_depth:
            return self._create_node_from_po(root_po, current_depth, [])
        
        visited.add(root_po.id)
        
        # Find downstream purchase orders (where this PO's output is used as input)
        downstream_pos = self._find_downstream_pos(root_po)
        
        # Recursively build downstream nodes
        downstream_nodes = []
        for downstream_po in downstream_pos:
            if downstream_po.id not in visited:
                downstream_node = self._build_downstream_tree(
                    downstream_po, max_depth, current_depth + 1, visited.copy()
                )
                downstream_nodes.append(downstream_node)
        
        return self._create_node_from_po(root_po, current_depth, downstream_nodes)
    
    def _find_upstream_pos(self, po: PurchaseOrder) -> List[PurchaseOrder]:
        """
        Find upstream purchase orders that supply materials to this PO.
        
        Args:
            po: Purchase order to find upstream for
            
        Returns:
            List of upstream purchase orders
        """
        upstream_pos = []
        
        # Check input_materials for references to other POs
        if po.input_materials:
            # Extract PO IDs from input materials
            # This depends on how input_materials is structured
            po_ids = self._extract_po_ids_from_input_materials(po.input_materials)
            
            if po_ids:
                upstream_pos = self.db.query(PurchaseOrder).filter(
                    PurchaseOrder.id.in_(po_ids)
                ).all()
        
        return upstream_pos
    
    def _find_downstream_pos(self, po: PurchaseOrder) -> List[PurchaseOrder]:
        """
        Find downstream purchase orders that use this PO's output as input.
        
        Args:
            po: Purchase order to find downstream for
            
        Returns:
            List of downstream purchase orders
        """
        # This is a simplified implementation
        # In practice, you'd need to search for POs that reference this PO in their input_materials
        
        # For now, return empty list as this requires complex JSON querying
        # In a real implementation, you might use PostgreSQL JSON operators
        return []
    
    def _extract_po_ids_from_input_materials(self, input_materials: Dict[str, Any]) -> List[UUID]:
        """
        Extract purchase order IDs from input materials data.
        
        Args:
            input_materials: Input materials data structure
            
        Returns:
            List of extracted PO IDs
        """
        po_ids = []
        
        # This depends on your input_materials structure
        # Example implementation:
        if isinstance(input_materials, dict):
            for material in input_materials.get("materials", []):
                if isinstance(material, dict) and "source_po_id" in material:
                    try:
                        po_id = UUID(material["source_po_id"])
                        po_ids.append(po_id)
                    except (ValueError, TypeError):
                        continue
        
        return po_ids
    
    def _create_node_from_po(
        self, 
        po: PurchaseOrder, 
        depth: int, 
        children: List[TraceabilityNode]
    ) -> TraceabilityNode:
        """
        Create a traceability node from a purchase order.
        
        Args:
            po: Purchase order
            depth: Depth in the tree
            children: Child nodes
            
        Returns:
            Traceability node
        """
        return TraceabilityNode(
            po_id=po.id,
            po_number=po.po_number,
            buyer_company_id=po.buyer_company_id,
            seller_company_id=po.seller_company_id,
            product_id=po.product_id,
            quantity=po.quantity,
            unit=po.unit,
            status=po.status,
            depth=depth,
            children=children,
            created_at=po.created_at,
            origin_data=po.origin_data,
            composition=po.composition
        )
    
    def _merge_trees(
        self, 
        upstream_tree: TraceabilityNode,
        downstream_tree: TraceabilityNode,
        root_po: PurchaseOrder
    ) -> TraceabilityNode:
        """
        Merge upstream and downstream trees into a single tree.
        
        Args:
            upstream_tree: Upstream traceability tree
            downstream_tree: Downstream traceability tree
            root_po: Root purchase order
            
        Returns:
            Merged traceability tree
        """
        # Create root node
        root_node = self._create_node_from_po(root_po, 0, [])
        
        # Add upstream children (with negative depths)
        upstream_children = upstream_tree.children
        for child in upstream_children:
            child.depth = -(child.depth + 1)  # Make depths negative for upstream
        
        # Add downstream children (with positive depths)
        downstream_children = downstream_tree.children
        for child in downstream_children:
            child.depth = child.depth + 1  # Increment depths for downstream
        
        # Combine children
        root_node.children = upstream_children + downstream_children
        
        return root_node
    
    def _calculate_traceability_summary(self, tree: TraceabilityNode) -> Dict[str, Any]:
        """
        Calculate summary statistics for traceability tree.
        
        Args:
            tree: Traceability tree
            
        Returns:
            Summary statistics
        """
        total_nodes = 0
        upstream_nodes = 0
        downstream_nodes = 0
        max_depth_reached = 0
        
        def count_nodes(node: TraceabilityNode):
            nonlocal total_nodes, upstream_nodes, downstream_nodes, max_depth_reached
            
            total_nodes += 1
            max_depth_reached = max(max_depth_reached, abs(node.depth))
            
            if node.depth < 0:
                upstream_nodes += 1
            elif node.depth > 0:
                downstream_nodes += 1
            
            for child in node.children:
                count_nodes(child)
        
        count_nodes(tree)
        
        return {
            "total_nodes": total_nodes,
            "upstream_nodes": upstream_nodes,
            "downstream_nodes": downstream_nodes,
            "max_depth_reached": max_depth_reached
        }
    
    def _flatten_tree_nodes(
        self, 
        tree: TraceabilityNode, 
        nodes: List[TraceabilityNode]
    ) -> None:
        """
        Flatten tree into a list of nodes.
        
        Args:
            tree: Traceability tree
            nodes: List to append nodes to
        """
        nodes.append(tree)
        for child in tree.children:
            self._flatten_tree_nodes(child, nodes)

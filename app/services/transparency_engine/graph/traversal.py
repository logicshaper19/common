"""
Graph traversal for transparency calculation.
"""
from typing import Optional, List, Dict, Any, Set
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session

from ..domain.models import TransparencyNode, TransparencyPath
from ..domain.enums import GraphTraversalMode, CycleHandlingStrategy
from .cycle_detector import CycleDetector
from app.core.logging import get_logger

logger = get_logger(__name__)


class GraphTraversal:
    """Handles graph traversal for transparency calculations."""
    
    def __init__(
        self, 
        db: Session,
        max_depth: int = 10,
        traversal_mode: GraphTraversalMode = GraphTraversalMode.DEPTH_FIRST,
        cycle_strategy: CycleHandlingStrategy = CycleHandlingStrategy.DEGRADATION
    ):
        """Initialize graph traversal."""
        self.db = db
        self.max_depth = max_depth
        self.traversal_mode = traversal_mode
        self.cycle_strategy = cycle_strategy
        self.cycle_detector = CycleDetector()
        
        # Traversal state
        self.visited_nodes: Set[UUID] = set()
        self.current_path: List[UUID] = []
        self.all_paths: List[TransparencyPath] = []
    
    def traverse_from_po(
        self, 
        po_id: UUID,
        node_factory_func,
        get_po_details_func
    ) -> List[TransparencyPath]:
        """
        Traverse the supply chain graph starting from a purchase order.
        
        Args:
            po_id: Starting purchase order ID
            node_factory_func: Function to create TransparencyNode from PO data
            get_po_details_func: Function to get PO details by ID
            
        Returns:
            List of transparency paths found
        """
        # Reset traversal state
        self.visited_nodes.clear()
        self.current_path.clear()
        self.all_paths.clear()
        
        # Start traversal
        if self.traversal_mode == GraphTraversalMode.DEPTH_FIRST:
            self._traverse_depth_first(po_id, 0, node_factory_func, get_po_details_func)
        elif self.traversal_mode == GraphTraversalMode.BREADTH_FIRST:
            self._traverse_breadth_first(po_id, node_factory_func, get_po_details_func)
        else:
            self._traverse_weighted(po_id, node_factory_func, get_po_details_func)
        
        return self.all_paths
    
    def _traverse_depth_first(
        self,
        po_id: UUID,
        depth: int,
        node_factory_func,
        get_po_details_func,
        current_path: Optional[TransparencyPath] = None
    ) -> None:
        """Depth-first traversal implementation."""
        if depth > self.max_depth:
            logger.warning(f"Max depth {self.max_depth} reached for PO {po_id}")
            return
        
        # Check for cycles
        if po_id in self.current_path:
            self._handle_cycle(po_id, current_path)
            return
        
        # Get PO details
        po_data = get_po_details_func(po_id)
        if not po_data:
            logger.warning(f"Could not retrieve PO data for {po_id}")
            return
        
        # Create transparency node
        node = node_factory_func(po_data, depth)
        node.visited_at = datetime.utcnow()
        
        # Add to current path
        self.current_path.append(po_id)
        self.visited_nodes.add(po_id)
        
        # Initialize or update current path
        if current_path is None:
            current_path = TransparencyPath()
            self.all_paths.append(current_path)
        
        current_path.nodes.append(node)
        
        # Get input materials (child nodes)
        input_materials = po_data.get('input_materials', [])
        
        if not input_materials:
            # Leaf node - path is complete
            logger.debug(f"Leaf node reached at PO {po_id}, depth {depth}")
        else:
            # Continue traversal for each input material
            for material in input_materials:
                source_po_id = material.get('source_po_id')
                if source_po_id:
                    try:
                        source_uuid = UUID(str(source_po_id))
                        
                        # Create new path branch for multiple inputs
                        if len(input_materials) > 1:
                            branch_path = TransparencyPath()
                            branch_path.nodes = current_path.nodes.copy()
                            self.all_paths.append(branch_path)
                            self._traverse_depth_first(
                                source_uuid, depth + 1, 
                                node_factory_func, get_po_details_func, 
                                branch_path
                            )
                        else:
                            self._traverse_depth_first(
                                source_uuid, depth + 1,
                                node_factory_func, get_po_details_func,
                                current_path
                            )
                    except (ValueError, TypeError) as e:
                        logger.error(f"Invalid source PO ID {source_po_id}: {e}")
        
        # Remove from current path (backtrack)
        self.current_path.pop()
    
    def _traverse_breadth_first(
        self,
        start_po_id: UUID,
        node_factory_func,
        get_po_details_func
    ) -> None:
        """Breadth-first traversal implementation."""
        from collections import deque
        
        # Queue of (po_id, depth, path_index)
        queue = deque([(start_po_id, 0, 0)])
        
        # Initialize first path
        first_path = TransparencyPath()
        self.all_paths.append(first_path)
        
        while queue:
            po_id, depth, path_index = queue.popleft()
            
            if depth > self.max_depth:
                continue
            
            if po_id in self.visited_nodes:
                continue
            
            # Get PO details
            po_data = get_po_details_func(po_id)
            if not po_data:
                continue
            
            # Create node
            node = node_factory_func(po_data, depth)
            node.visited_at = datetime.utcnow()
            
            # Add to appropriate path
            if path_index < len(self.all_paths):
                self.all_paths[path_index].nodes.append(node)
            
            self.visited_nodes.add(po_id)
            
            # Add input materials to queue
            input_materials = po_data.get('input_materials', [])
            for i, material in enumerate(input_materials):
                source_po_id = material.get('source_po_id')
                if source_po_id:
                    try:
                        source_uuid = UUID(str(source_po_id))
                        
                        # Create new path for additional inputs
                        if i > 0:
                            new_path = TransparencyPath()
                            new_path.nodes = self.all_paths[path_index].nodes.copy()
                            self.all_paths.append(new_path)
                            new_path_index = len(self.all_paths) - 1
                        else:
                            new_path_index = path_index
                        
                        queue.append((source_uuid, depth + 1, new_path_index))
                    except (ValueError, TypeError) as e:
                        logger.error(f"Invalid source PO ID {source_po_id}: {e}")
    
    def _traverse_weighted(
        self,
        start_po_id: UUID,
        node_factory_func,
        get_po_details_func
    ) -> None:
        """Weighted traversal prioritizing by quantity/importance."""
        import heapq
        
        # Priority queue of (-weight, po_id, depth, path_index)
        # Using negative weight for max-heap behavior
        heap = [(-1.0, start_po_id, 0, 0)]
        
        # Initialize first path
        first_path = TransparencyPath()
        self.all_paths.append(first_path)
        
        while heap:
            neg_weight, po_id, depth, path_index = heapq.heappop(heap)
            weight = -neg_weight
            
            if depth > self.max_depth:
                continue
            
            if po_id in self.visited_nodes:
                continue
            
            # Get PO details
            po_data = get_po_details_func(po_id)
            if not po_data:
                continue
            
            # Create node
            node = node_factory_func(po_data, depth)
            node.visited_at = datetime.utcnow()
            
            # Add to appropriate path
            if path_index < len(self.all_paths):
                self.all_paths[path_index].nodes.append(node)
                self.all_paths[path_index].total_weight += weight
            
            self.visited_nodes.add(po_id)
            
            # Add input materials to heap with weights
            input_materials = po_data.get('input_materials', [])
            for i, material in enumerate(input_materials):
                source_po_id = material.get('source_po_id')
                material_weight = float(material.get('percentage_contribution', 0)) / 100.0
                
                if source_po_id and material_weight > 0:
                    try:
                        source_uuid = UUID(str(source_po_id))
                        
                        # Create new path for additional inputs
                        if i > 0:
                            new_path = TransparencyPath()
                            new_path.nodes = self.all_paths[path_index].nodes.copy()
                            new_path.total_weight = self.all_paths[path_index].total_weight
                            self.all_paths.append(new_path)
                            new_path_index = len(self.all_paths) - 1
                        else:
                            new_path_index = path_index
                        
                        heapq.heappush(heap, (
                            -material_weight, source_uuid, depth + 1, new_path_index
                        ))
                    except (ValueError, TypeError) as e:
                        logger.error(f"Invalid source PO ID {source_po_id}: {e}")
    
    def _handle_cycle(self, po_id: UUID, current_path: Optional[TransparencyPath]) -> None:
        """Handle circular reference detection."""
        if current_path:
            current_path.has_cycles = True
            current_path.cycle_break_points.append(po_id)
        
        if self.cycle_strategy == CycleHandlingStrategy.BREAK_AT_FIRST:
            logger.warning(f"Cycle detected at PO {po_id}, breaking traversal")
            return
        elif self.cycle_strategy == CycleHandlingStrategy.DEGRADATION:
            logger.warning(f"Cycle detected at PO {po_id}, applying degradation")
            # Apply degradation factor to subsequent calculations
            if current_path and current_path.nodes:
                for node in current_path.nodes:
                    node.degradation_factor *= 0.8  # 20% degradation
        else:
            logger.warning(f"Cycle detected at PO {po_id}, using weighted average")
            # Implementation for weighted average strategy would go here

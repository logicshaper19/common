"""
Cycle detection for supply chain graphs.
"""
from typing import List, Set, Dict, Optional
from uuid import UUID
from sqlalchemy.orm import Session

from app.core.logging import get_logger

logger = get_logger(__name__)


class CycleDetector:
    """Detects circular references in supply chain graphs."""
    
    def __init__(self):
        """Initialize cycle detector."""
        self.visited: Set[UUID] = set()
        self.recursion_stack: Set[UUID] = set()
        self.cycles_found: List[List[UUID]] = []
    
    def detect_cycles(
        self, 
        start_po_id: UUID,
        get_input_materials_func
    ) -> List[List[UUID]]:
        """
        Detect all cycles in the supply chain graph.
        
        Args:
            start_po_id: Starting purchase order ID
            get_input_materials_func: Function to get input materials for a PO
            
        Returns:
            List of cycles, where each cycle is a list of PO IDs
        """
        # Reset state
        self.visited.clear()
        self.recursion_stack.clear()
        self.cycles_found.clear()
        
        # Start DFS from the given PO
        self._dfs_cycle_detection(start_po_id, [], get_input_materials_func)
        
        return self.cycles_found
    
    def _dfs_cycle_detection(
        self,
        po_id: UUID,
        current_path: List[UUID],
        get_input_materials_func
    ) -> bool:
        """
        Depth-first search for cycle detection.
        
        Args:
            po_id: Current purchase order ID
            current_path: Current path in the traversal
            get_input_materials_func: Function to get input materials
            
        Returns:
            True if a cycle is detected from this node
        """
        # Mark current node as visited and add to recursion stack
        self.visited.add(po_id)
        self.recursion_stack.add(po_id)
        current_path.append(po_id)
        
        # Get input materials for this PO
        try:
            input_materials = get_input_materials_func(po_id)
            
            for material in input_materials:
                source_po_id = material.get('source_po_id')
                if not source_po_id:
                    continue
                
                try:
                    source_uuid = UUID(str(source_po_id))
                    
                    # If the source PO is in the current recursion stack, we found a cycle
                    if source_uuid in self.recursion_stack:
                        cycle_start_index = current_path.index(source_uuid)
                        cycle = current_path[cycle_start_index:] + [source_uuid]
                        self.cycles_found.append(cycle)
                        
                        logger.warning(
                            f"Cycle detected: {' -> '.join(str(po) for po in cycle)}"
                        )
                        return True
                    
                    # If not visited, continue DFS
                    elif source_uuid not in self.visited:
                        if self._dfs_cycle_detection(
                            source_uuid, current_path.copy(), get_input_materials_func
                        ):
                            return True
                
                except (ValueError, TypeError) as e:
                    logger.error(f"Invalid source PO ID {source_po_id}: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Error getting input materials for PO {po_id}: {e}")
        
        # Remove from recursion stack before returning
        self.recursion_stack.discard(po_id)
        if current_path and current_path[-1] == po_id:
            current_path.pop()
        
        return False
    
    def find_shortest_cycle(
        self,
        start_po_id: UUID,
        get_input_materials_func
    ) -> Optional[List[UUID]]:
        """
        Find the shortest cycle starting from a given PO.
        
        Args:
            start_po_id: Starting purchase order ID
            get_input_materials_func: Function to get input materials
            
        Returns:
            Shortest cycle as list of PO IDs, or None if no cycle found
        """
        cycles = self.detect_cycles(start_po_id, get_input_materials_func)
        
        if not cycles:
            return None
        
        # Return the shortest cycle
        return min(cycles, key=len)
    
    def analyze_cycle_impact(
        self,
        cycle: List[UUID],
        get_po_details_func
    ) -> Dict[str, any]:
        """
        Analyze the impact of a detected cycle.
        
        Args:
            cycle: List of PO IDs forming a cycle
            get_po_details_func: Function to get PO details
            
        Returns:
            Analysis of cycle impact
        """
        if not cycle:
            return {}
        
        analysis = {
            "cycle_length": len(cycle) - 1,  # Subtract 1 because last element repeats first
            "total_quantity": 0.0,
            "companies_involved": set(),
            "product_categories": set(),
            "severity": "low"
        }
        
        try:
            # Analyze each PO in the cycle (excluding the repeated last element)
            for po_id in cycle[:-1]:
                po_details = get_po_details_func(po_id)
                if po_details:
                    # Accumulate quantities
                    quantity = po_details.get('quantity', 0)
                    if quantity:
                        analysis["total_quantity"] += float(quantity)
                    
                    # Track companies and products
                    if 'seller_company' in po_details:
                        analysis["companies_involved"].add(
                            po_details['seller_company'].get('id')
                        )
                    if 'buyer_company' in po_details:
                        analysis["companies_involved"].add(
                            po_details['buyer_company'].get('id')
                        )
                    
                    if 'product' in po_details:
                        analysis["product_categories"].add(
                            po_details['product'].get('category')
                        )
            
            # Convert sets to lists for JSON serialization
            analysis["companies_involved"] = list(analysis["companies_involved"])
            analysis["product_categories"] = list(analysis["product_categories"])
            
            # Determine severity
            if analysis["cycle_length"] <= 2:
                analysis["severity"] = "high"  # Direct circular dependency
            elif analysis["cycle_length"] <= 4:
                analysis["severity"] = "medium"
            else:
                analysis["severity"] = "low"
            
            # Add recommendations
            analysis["recommendations"] = self._get_cycle_recommendations(analysis)
        
        except Exception as e:
            logger.error(f"Error analyzing cycle impact: {e}")
            analysis["error"] = str(e)
        
        return analysis
    
    def _get_cycle_recommendations(self, analysis: Dict[str, any]) -> List[str]:
        """Get recommendations for resolving cycles."""
        recommendations = []
        
        if analysis["severity"] == "high":
            recommendations.extend([
                "Immediate attention required - direct circular dependency detected",
                "Review business relationships between involved companies",
                "Consider breaking the cycle by finding alternative suppliers"
            ])
        elif analysis["severity"] == "medium":
            recommendations.extend([
                "Review supply chain structure for optimization opportunities",
                "Consider consolidating suppliers to reduce complexity"
            ])
        else:
            recommendations.extend([
                "Monitor for potential supply chain risks",
                "Document the circular relationship for future reference"
            ])
        
        if len(analysis["companies_involved"]) <= 2:
            recommendations.append(
                "Consider establishing clear supplier-buyer hierarchy"
            )
        
        if analysis["total_quantity"] > 1000:  # Arbitrary threshold
            recommendations.append(
                "High-volume cycle detected - prioritize resolution"
            )
        
        return recommendations
    
    def get_cycle_breaking_suggestions(
        self,
        cycle: List[UUID],
        get_po_details_func
    ) -> List[Dict[str, any]]:
        """
        Get suggestions for breaking a cycle.
        
        Args:
            cycle: List of PO IDs forming a cycle
            get_po_details_func: Function to get PO details
            
        Returns:
            List of suggestions for breaking the cycle
        """
        suggestions = []
        
        if len(cycle) <= 1:
            return suggestions
        
        # Analyze each edge in the cycle for breaking potential
        for i in range(len(cycle) - 1):
            current_po = cycle[i]
            next_po = cycle[i + 1]
            
            try:
                current_details = get_po_details_func(current_po)
                next_details = get_po_details_func(next_po)
                
                if current_details and next_details:
                    suggestion = {
                        "break_point": f"{current_po} -> {next_po}",
                        "current_po": str(current_po),
                        "next_po": str(next_po),
                        "feasibility": "medium",
                        "impact": "medium",
                        "actions": []
                    }
                    
                    # Analyze feasibility based on quantities and relationships
                    current_qty = float(current_details.get('quantity', 0))
                    next_qty = float(next_details.get('quantity', 0))
                    
                    if current_qty < next_qty * 0.1:  # Small quantity
                        suggestion["feasibility"] = "high"
                        suggestion["actions"].append("Low quantity - easy to replace")
                    
                    # Check if there are alternative suppliers
                    current_product = current_details.get('product', {})
                    if current_product:
                        suggestion["actions"].append(
                            f"Find alternative supplier for {current_product.get('name', 'product')}"
                        )
                    
                    suggestions.append(suggestion)
            
            except Exception as e:
                logger.error(f"Error analyzing break point {current_po} -> {next_po}: {e}")
        
        # Sort by feasibility (high first)
        feasibility_order = {"high": 0, "medium": 1, "low": 2}
        suggestions.sort(key=lambda x: feasibility_order.get(x["feasibility"], 3))
        
        return suggestions

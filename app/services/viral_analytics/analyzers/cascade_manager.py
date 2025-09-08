"""
Cascade node management service.

This module manages viral cascade node operations including creation,
updates, and hierarchy management for viral growth tracking.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc

from app.models.viral_analytics import ViralCascadeNode, SupplierInvitation
from app.models.company import Company
from app.core.logging import get_logger
from ..models.enums import InvitationStatus, CascadeNodeType, ViralChampionTier
from ..services.query_service import AnalyticsQueryService

logger = get_logger(__name__)


class CascadeNodeManager:
    """Manages viral cascade node operations."""
    
    def __init__(self, db: Session, query_service: AnalyticsQueryService):
        self.db = db
        self.query_service = query_service
    
    def create_or_update_cascade_node(
        self,
        company_id: int,
        parent_company_id: Optional[int] = None
    ) -> ViralCascadeNode:
        """
        Create or update a cascade node for a company.
        
        Args:
            company_id: ID of company for the node
            parent_company_id: Optional parent company ID
            
        Returns:
            ViralCascadeNode instance
        """
        logger.info(
            "Creating or updating cascade node",
            company_id=company_id,
            parent_company_id=parent_company_id
        )
        
        # Check if node already exists
        existing_node = self.db.query(ViralCascadeNode).filter(
            ViralCascadeNode.company_id == company_id
        ).first()
        
        if existing_node:
            # Update existing node
            self._update_existing_node(existing_node, parent_company_id)
            return existing_node
        else:
            # Create new node
            return self._create_new_node(company_id, parent_company_id)
    
    def update_cascade_node_metrics(
        self,
        company_id: int,
        force_recalculation: bool = False
    ) -> None:
        """
        Update metrics for a cascade node.
        
        Args:
            company_id: ID of company to update
            force_recalculation: Whether to force full recalculation
        """
        logger.info(
            "Updating cascade node metrics",
            company_id=company_id,
            force_recalculation=force_recalculation
        )
        
        node = self.db.query(ViralCascadeNode).filter(
            ViralCascadeNode.company_id == company_id
        ).first()
        
        if not node:
            logger.warning("Cascade node not found for metrics update", company_id=company_id)
            return
        
        # Calculate invitation metrics
        invitation_metrics = self._calculate_invitation_metrics(company_id)
        
        # Update node with new metrics
        node.total_invitations_sent = invitation_metrics["total_sent"]
        node.total_invitations_accepted = invitation_metrics["total_accepted"]
        node.viral_coefficient = invitation_metrics["viral_coefficient"]
        node.updated_at = datetime.utcnow()
        
        # Update depth if needed
        if force_recalculation or node.depth is None:
            node.depth = self._calculate_node_depth(node)
        
        self.db.commit()
        
        logger.info(
            "Cascade node metrics updated",
            company_id=company_id,
            viral_coefficient=node.viral_coefficient,
            total_invitations=node.total_invitations_sent
        )
    
    def update_viral_metrics(
        self,
        company_id: int,
        viral_coefficient: float,
        total_invitations_sent: int,
        total_invitations_accepted: int
    ) -> None:
        """
        Update viral metrics for a cascade node.
        
        Args:
            company_id: ID of company
            viral_coefficient: New viral coefficient
            total_invitations_sent: Total invitations sent
            total_invitations_accepted: Total invitations accepted
        """
        node = self.db.query(ViralCascadeNode).filter(
            ViralCascadeNode.company_id == company_id
        ).first()
        
        if not node:
            # Create node if it doesn't exist
            node = self.create_or_update_cascade_node(company_id)
        
        node.viral_coefficient = viral_coefficient
        node.total_invitations_sent = total_invitations_sent
        node.total_invitations_accepted = total_invitations_accepted
        node.updated_at = datetime.utcnow()
        
        self.db.commit()
        
        logger.info(
            "Viral metrics updated for cascade node",
            company_id=company_id,
            viral_coefficient=viral_coefficient
        )
    
    def get_cascade_hierarchy(
        self,
        root_company_id: int,
        max_depth: int = 10
    ) -> Dict[int, List[ViralCascadeNode]]:
        """
        Get cascade hierarchy starting from a root company.
        
        Args:
            root_company_id: Root company ID
            max_depth: Maximum depth to retrieve
            
        Returns:
            Dictionary mapping depth to list of nodes
        """
        hierarchy_data = self.query_service.get_cascade_hierarchy_data(
            root_company_id, max_depth
        )
        
        # Convert to ViralCascadeNode objects
        hierarchy = {}
        for level, nodes_data in hierarchy_data.items():
            hierarchy[level] = []
            for node_data in nodes_data:
                # Create a mock ViralCascadeNode object with the data
                # In a real implementation, you'd query the actual objects
                node = ViralCascadeNode(
                    id=node_data["id"],
                    company_id=node_data["company_id"],
                    parent_cascade_node_id=node_data["parent_id"],
                    depth=node_data["depth"],
                    total_invitations_sent=node_data["invitations_sent"],
                    total_invitations_accepted=node_data["invitations_accepted"],
                    viral_coefficient=node_data["viral_coefficient"],
                    created_at=node_data["created_at"]
                )
                hierarchy[level].append(node)
        
        return hierarchy
    
    def identify_viral_champions(
        self,
        min_viral_coefficient: float = 1.5,
        min_invitations: int = 10,
        timeframe_days: int = 30
    ) -> List[ViralCascadeNode]:
        """
        Identify viral champions based on performance criteria.
        
        Args:
            min_viral_coefficient: Minimum viral coefficient threshold
            min_invitations: Minimum number of invitations sent
            timeframe_days: Days to look back for activity
            
        Returns:
            List of viral champion nodes
        """
        cutoff_date = datetime.utcnow() - timedelta(days=timeframe_days)
        
        champions = self.db.query(ViralCascadeNode).filter(
            and_(
                ViralCascadeNode.viral_coefficient >= min_viral_coefficient,
                ViralCascadeNode.total_invitations_sent >= min_invitations,
                ViralCascadeNode.updated_at >= cutoff_date
            )
        ).order_by(desc(ViralCascadeNode.viral_coefficient)).all()
        
        logger.info(
            "Identified viral champions",
            champion_count=len(champions),
            min_viral_coefficient=min_viral_coefficient,
            min_invitations=min_invitations
        )
        
        return champions
    
    def get_node_descendants(
        self,
        node_id: int,
        max_depth: int = 5
    ) -> List[ViralCascadeNode]:
        """
        Get all descendant nodes from a parent node.
        
        Args:
            node_id: Parent node ID
            max_depth: Maximum depth to traverse
            
        Returns:
            List of descendant nodes
        """
        descendants = []
        current_level = [node_id]
        depth = 0
        
        while current_level and depth < max_depth:
            next_level = []
            
            for parent_id in current_level:
                children = self.db.query(ViralCascadeNode).filter(
                    ViralCascadeNode.parent_cascade_node_id == parent_id
                ).all()
                
                descendants.extend(children)
                next_level.extend([child.id for child in children])
            
            current_level = next_level
            depth += 1
        
        return descendants
    
    def calculate_node_influence_score(
        self,
        node_id: int
    ) -> float:
        """
        Calculate influence score for a cascade node.
        
        Args:
            node_id: Node ID to calculate score for
            
        Returns:
            Influence score (0-100)
        """
        node = self.db.query(ViralCascadeNode).filter(
            ViralCascadeNode.id == node_id
        ).first()
        
        if not node:
            return 0.0
        
        # Get descendant count
        descendants = self.get_node_descendants(node_id)
        descendant_count = len(descendants)
        
        # Calculate influence score based on multiple factors
        viral_score = min(node.viral_coefficient / 3.0, 1.0) * 30  # Max 30 points
        invitation_score = min(node.total_invitations_sent / 50.0, 1.0) * 25  # Max 25 points
        conversion_score = (
            node.total_invitations_accepted / max(node.total_invitations_sent, 1)
        ) * 20  # Max 20 points
        network_score = min(descendant_count / 20.0, 1.0) * 15  # Max 15 points
        depth_score = min(node.depth / 5.0, 1.0) * 10  # Max 10 points
        
        total_score = viral_score + invitation_score + conversion_score + network_score + depth_score
        
        return min(total_score, 100.0)
    
    def get_cascade_statistics(
        self,
        root_company_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get comprehensive cascade statistics.
        
        Args:
            root_company_id: Optional root company filter
            
        Returns:
            Dictionary with cascade statistics
        """
        query = self.db.query(ViralCascadeNode)
        
        if root_company_id:
            # Get all nodes in the cascade starting from root
            hierarchy = self.get_cascade_hierarchy(root_company_id)
            node_ids = []
            for level_nodes in hierarchy.values():
                node_ids.extend([node.id for node in level_nodes])
            
            if node_ids:
                query = query.filter(ViralCascadeNode.id.in_(node_ids))
            else:
                # No nodes found, return empty stats
                return self._empty_cascade_stats()
        
        nodes = query.all()
        
        if not nodes:
            return self._empty_cascade_stats()
        
        # Calculate statistics
        total_nodes = len(nodes)
        total_invitations = sum(node.total_invitations_sent for node in nodes)
        total_accepted = sum(node.total_invitations_accepted for node in nodes)
        
        viral_coefficients = [node.viral_coefficient for node in nodes if node.viral_coefficient]
        avg_viral_coefficient = sum(viral_coefficients) / len(viral_coefficients) if viral_coefficients else 0
        
        depths = [node.depth for node in nodes if node.depth is not None]
        max_depth = max(depths) if depths else 0
        avg_depth = sum(depths) / len(depths) if depths else 0
        
        # Count nodes by type
        node_types = {}
        for node in nodes:
            has_parent = node.parent_cascade_node_id is not None
            has_children = any(n.parent_cascade_node_id == node.id for n in nodes)
            node_type = CascadeNodeType.determine_node_type(has_parent, has_children)
            node_types[node_type.value] = node_types.get(node_type.value, 0) + 1
        
        return {
            "total_nodes": total_nodes,
            "total_invitations_sent": total_invitations,
            "total_invitations_accepted": total_accepted,
            "overall_conversion_rate": total_accepted / total_invitations if total_invitations > 0 else 0,
            "average_viral_coefficient": avg_viral_coefficient,
            "max_depth": max_depth,
            "average_depth": avg_depth,
            "node_type_distribution": node_types,
            "viral_nodes_count": len([n for n in nodes if n.viral_coefficient and n.viral_coefficient > 1.0])
        }
    
    def _create_new_node(
        self,
        company_id: int,
        parent_company_id: Optional[int]
    ) -> ViralCascadeNode:
        """Create a new cascade node."""
        # Find parent node if parent company specified
        parent_node_id = None
        depth = 0
        
        if parent_company_id:
            parent_node = self.db.query(ViralCascadeNode).filter(
                ViralCascadeNode.company_id == parent_company_id
            ).first()
            
            if parent_node:
                parent_node_id = parent_node.id
                depth = (parent_node.depth or 0) + 1
        
        # Calculate initial metrics
        invitation_metrics = self._calculate_invitation_metrics(company_id)
        
        # Create new node
        node = ViralCascadeNode(
            company_id=company_id,
            parent_cascade_node_id=parent_node_id,
            depth=depth,
            total_invitations_sent=invitation_metrics["total_sent"],
            total_invitations_accepted=invitation_metrics["total_accepted"],
            viral_coefficient=invitation_metrics["viral_coefficient"],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        self.db.add(node)
        self.db.commit()
        self.db.refresh(node)
        
        logger.info(
            "Created new cascade node",
            company_id=company_id,
            node_id=node.id,
            depth=depth
        )
        
        return node
    
    def _update_existing_node(
        self,
        node: ViralCascadeNode,
        parent_company_id: Optional[int]
    ) -> None:
        """Update an existing cascade node."""
        # Update parent if specified and different
        if parent_company_id:
            parent_node = self.db.query(ViralCascadeNode).filter(
                ViralCascadeNode.company_id == parent_company_id
            ).first()
            
            if parent_node and parent_node.id != node.parent_cascade_node_id:
                node.parent_cascade_node_id = parent_node.id
                node.depth = (parent_node.depth or 0) + 1
        
        # Update metrics
        invitation_metrics = self._calculate_invitation_metrics(node.company_id)
        node.total_invitations_sent = invitation_metrics["total_sent"]
        node.total_invitations_accepted = invitation_metrics["total_accepted"]
        node.viral_coefficient = invitation_metrics["viral_coefficient"]
        node.updated_at = datetime.utcnow()
        
        self.db.commit()
        
        logger.info(
            "Updated existing cascade node",
            company_id=node.company_id,
            node_id=node.id
        )
    
    def _calculate_invitation_metrics(self, company_id: int) -> Dict[str, Any]:
        """Calculate invitation metrics for a company."""
        # Get total invitations sent
        total_sent = self.db.query(func.count(SupplierInvitation.id)).filter(
            SupplierInvitation.inviting_company_id == company_id
        ).scalar() or 0
        
        # Get total accepted
        total_accepted = self.db.query(func.count(SupplierInvitation.id)).filter(
            and_(
                SupplierInvitation.inviting_company_id == company_id,
                SupplierInvitation.status == InvitationStatus.ACCEPTED.value
            )
        ).scalar() or 0
        
        # Calculate viral coefficient (simplified version)
        viral_coefficient = total_accepted / max(total_sent, 1) * 2  # Simplified calculation
        
        return {
            "total_sent": total_sent,
            "total_accepted": total_accepted,
            "viral_coefficient": viral_coefficient
        }
    
    def _calculate_node_depth(self, node: ViralCascadeNode) -> int:
        """Calculate depth of a node in the cascade."""
        if not node.parent_cascade_node_id:
            return 0
        
        parent = self.db.query(ViralCascadeNode).filter(
            ViralCascadeNode.id == node.parent_cascade_node_id
        ).first()
        
        if not parent:
            return 0
        
        return (parent.depth or 0) + 1
    
    def _empty_cascade_stats(self) -> Dict[str, Any]:
        """Return empty cascade statistics."""
        return {
            "total_nodes": 0,
            "total_invitations_sent": 0,
            "total_invitations_accepted": 0,
            "overall_conversion_rate": 0,
            "average_viral_coefficient": 0,
            "max_depth": 0,
            "average_depth": 0,
            "node_type_distribution": {},
            "viral_nodes_count": 0
        }

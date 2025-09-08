"""
Visualization data generator for viral analytics.

This module generates structured data for viral analytics visualizations
including onboarding chains, network graphs, and dashboard metrics.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from app.models.viral_analytics import (
    ViralCascadeNode,
    SupplierInvitation,
    OnboardingProgress
)
from app.models.company import Company
from app.core.logging import get_logger
from ..models.visualization_data import (
    OnboardingChainVisualization, OnboardingChainNode, NetworkGraphData,
    NetworkGraphNode, NetworkGraphEdge, DashboardMetricsData
)
from ..models.enums import OnboardingStage, InvitationStatus, CascadeNodeType, AnalyticsTimeframe
from ..services.query_service import AnalyticsQueryService

logger = get_logger(__name__)


class VisualizationGenerator:
    """Generates data for viral analytics visualizations."""
    
    def __init__(self, db: Session, query_service: AnalyticsQueryService):
        self.db = db
        self.query_service = query_service
    
    def generate_onboarding_chain_visualization(
        self,
        root_company_id: int,
        max_depth: int = 5,
        timeframe_days: int = 90
    ) -> OnboardingChainVisualization:
        """
        Generate onboarding chain visualization data.
        
        Args:
            root_company_id: Root company for the chain
            max_depth: Maximum depth to visualize
            timeframe_days: Days to look back for data
            
        Returns:
            OnboardingChainVisualization instance
        """
        logger.info(
            "Generating onboarding chain visualization",
            root_company_id=root_company_id,
            max_depth=max_depth
        )
        
        # Get cascade hierarchy
        hierarchy_data = self.query_service.get_cascade_hierarchy_data(
            root_company_id, max_depth
        )
        
        # Get root company info
        root_company = self.db.query(Company).filter(Company.id == root_company_id).first()
        root_company_name = root_company.name if root_company else f"Company {root_company_id}"
        
        # Build chain nodes
        nodes = []
        level_widths = {}
        
        for level, level_nodes in hierarchy_data.items():
            level_widths[level] = len(level_nodes)
            
            for node_data in level_nodes:
                chain_node = self._create_chain_node(node_data, level)
                nodes.append(chain_node)
        
        # Calculate chain metrics
        chain_metrics = self._calculate_chain_metrics(nodes)
        
        return OnboardingChainVisualization(
            root_company_id=root_company_id,
            root_company_name=root_company_name,
            nodes=nodes,
            total_levels=len(hierarchy_data),
            total_nodes=len(nodes),
            chain_viral_coefficient=chain_metrics["viral_coefficient"],
            chain_conversion_rate=chain_metrics["conversion_rate"],
            chain_completion_rate=chain_metrics["completion_rate"],
            level_widths=level_widths,
            max_width=max(level_widths.values()) if level_widths else 0,
            generation_timestamp=datetime.utcnow(),
            timeframe_days=timeframe_days
        )
    
    def generate_network_graph_data(
        self,
        center_company_id: Optional[int] = None,
        max_nodes: int = 100,
        timeframe: AnalyticsTimeframe = AnalyticsTimeframe.LAST_30_DAYS
    ) -> NetworkGraphData:
        """
        Generate network graph visualization data.
        
        Args:
            center_company_id: Optional center node for the graph
            max_nodes: Maximum number of nodes to include
            timeframe: Time period for data
            
        Returns:
            NetworkGraphData instance
        """
        logger.info(
            "Generating network graph data",
            center_company_id=center_company_id,
            max_nodes=max_nodes
        )
        
        time_filter = self._get_time_filter(timeframe)
        
        # Get network connections
        connections_query = self.db.query(
            SupplierInvitation.inviting_company_id,
            SupplierInvitation.accepting_company_id,
            SupplierInvitation.created_at,
            SupplierInvitation.accepted_at
        ).filter(
            and_(
                SupplierInvitation.status == InvitationStatus.ACCEPTED.value,
                SupplierInvitation.accepting_company_id.isnot(None)
            )
        )
        
        if time_filter:
            connections_query = connections_query.filter(
                SupplierInvitation.accepted_at >= time_filter
            )
        
        connections = connections_query.limit(max_nodes * 2).all()
        
        # Get unique companies
        company_ids = set()
        for inviting_id, accepting_id, _, _ in connections:
            company_ids.add(inviting_id)
            if accepting_id:
                company_ids.add(accepting_id)
        
        # Limit nodes if necessary
        if len(company_ids) > max_nodes:
            # Prioritize companies with more connections
            company_connection_counts = {}
            for inviting_id, accepting_id, _, _ in connections:
                company_connection_counts[inviting_id] = company_connection_counts.get(inviting_id, 0) + 1
                if accepting_id:
                    company_connection_counts[accepting_id] = company_connection_counts.get(accepting_id, 0) + 1
            
            # Keep top connected companies
            top_companies = sorted(
                company_connection_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:max_nodes]
            
            company_ids = {company_id for company_id, _ in top_companies}
        
        # Generate nodes
        nodes = self._generate_graph_nodes(list(company_ids))
        
        # Generate edges
        edges = self._generate_graph_edges(connections, company_ids)
        
        # Calculate graph metrics
        total_nodes = len(nodes)
        total_edges = len(edges)
        
        max_possible_edges = total_nodes * (total_nodes - 1) if total_nodes > 1 else 0
        network_density = total_edges / max_possible_edges if max_possible_edges > 0 else 0
        
        # Simplified clustering coefficient calculation
        clustering_coefficient = self._calculate_simple_clustering(nodes, edges)
        
        return NetworkGraphData(
            nodes=nodes,
            edges=edges,
            total_nodes=total_nodes,
            total_edges=total_edges,
            network_density=network_density,
            clustering_coefficient=clustering_coefficient,
            layout_algorithm="force_directed",
            zoom_level=1.0,
            center_node_id=str(center_company_id) if center_company_id else None,
            generation_timestamp=datetime.utcnow(),
            timeframe_days=AnalyticsTimeframe.get_days(timeframe)
        )
    
    def prepare_metrics_dashboard_data(
        self,
        timeframe: AnalyticsTimeframe = AnalyticsTimeframe.LAST_30_DAYS
    ) -> DashboardMetricsData:
        """
        Prepare comprehensive metrics data for dashboard.
        
        Args:
            timeframe: Time period for metrics
            
        Returns:
            DashboardMetricsData instance
        """
        logger.info("Preparing dashboard metrics data", timeframe=timeframe.value)
        
        time_filter = self._get_time_filter(timeframe)
        timeframe_days = AnalyticsTimeframe.get_days(timeframe)
        
        # Get KPI metrics
        kpi_metrics = self._calculate_kpi_metrics(time_filter)
        
        # Get growth metrics
        growth_metrics = self._calculate_growth_metrics(timeframe_days)
        
        # Get top performers
        top_performers = self._get_top_performers(timeframe_days)
        
        # Get timeline data
        timeline_data = self._get_timeline_data(timeframe_days)
        
        # Get network health metrics
        network_health = self._calculate_network_health_metrics(time_filter)
        
        return DashboardMetricsData(
            # KPIs
            total_network_size=kpi_metrics["total_network_size"],
            total_invitations_sent=kpi_metrics["total_invitations_sent"],
            total_invitations_accepted=kpi_metrics["total_invitations_accepted"],
            overall_viral_coefficient=kpi_metrics["overall_viral_coefficient"],
            overall_conversion_rate=kpi_metrics["overall_conversion_rate"],
            
            # Growth metrics
            daily_growth_rate=growth_metrics["daily_growth_rate"],
            weekly_growth_rate=growth_metrics["weekly_growth_rate"],
            monthly_growth_rate=growth_metrics["monthly_growth_rate"],
            
            # Top performers
            top_viral_champions=top_performers["viral_champions"],
            fastest_growing_cascades=top_performers["growing_cascades"],
            most_active_inviters=top_performers["active_inviters"],
            
            # Timeline data
            growth_timeline=timeline_data["growth"],
            conversion_timeline=timeline_data["conversion"],
            
            # Network health
            network_health_score=network_health["health_score"],
            cascade_survival_rate=network_health["cascade_survival_rate"],
            average_cascade_depth=network_health["average_cascade_depth"],
            
            # Metadata
            generation_timestamp=datetime.utcnow(),
            timeframe_days=timeframe_days
        )
    
    def _create_chain_node(self, node_data: Dict[str, Any], level: int) -> OnboardingChainNode:
        """Create an onboarding chain node from data."""
        company_id = node_data["company_id"]
        
        # Get onboarding progress
        onboarding = self.db.query(OnboardingProgress).filter(
            OnboardingProgress.company_id == company_id
        ).first()
        
        current_stage = OnboardingStage.INVITED
        stage_completion = 0.0
        completion_date = None
        
        if onboarding:
            current_stage = OnboardingStage(onboarding.current_stage)
            stage_completion = onboarding.stage_completion_percentage or 0.0
            if current_stage == OnboardingStage.ACTIVE_SUPPLIER:
                completion_date = onboarding.updated_at
        
        # Determine node type
        has_parent = node_data.get("parent_id") is not None
        has_children = False  # Would need to check in hierarchy data
        node_type = CascadeNodeType.determine_node_type(has_parent, has_children)
        
        # Check if viral champion
        viral_coefficient = node_data.get("viral_coefficient", 0)
        is_viral_champion = viral_coefficient > 1.5 and node_data.get("invitations_sent", 0) >= 10
        
        # Calculate performance score
        performance_score = min(viral_coefficient * 30 + stage_completion * 70, 100)
        
        return OnboardingChainNode(
            node_id=str(company_id),
            company_name=node_data["company_name"],
            company_id=company_id,
            level=level,
            parent_id=str(node_data["parent_id"]) if node_data.get("parent_id") else None,
            children_ids=[],  # Would need to populate from hierarchy
            current_stage=current_stage,
            stage_completion_percentage=stage_completion,
            invitation_date=node_data["created_at"],
            acceptance_date=None,  # Would need to get from invitation data
            completion_date=completion_date,
            invitations_sent=node_data.get("invitations_sent", 0),
            invitations_accepted=node_data.get("invitations_accepted", 0),
            conversion_rate=node_data.get("invitations_accepted", 0) / max(node_data.get("invitations_sent", 1), 1),
            node_type=node_type,
            is_viral_champion=is_viral_champion,
            performance_score=performance_score
        )
    
    def _calculate_chain_metrics(self, nodes: List[OnboardingChainNode]) -> Dict[str, float]:
        """Calculate overall chain metrics."""
        if not nodes:
            return {"viral_coefficient": 0.0, "conversion_rate": 0.0, "completion_rate": 0.0}
        
        total_invitations = sum(node.invitations_sent for node in nodes)
        total_accepted = sum(node.invitations_accepted for node in nodes)
        completed_nodes = len([node for node in nodes if node.current_stage == OnboardingStage.ACTIVE_SUPPLIER])
        
        conversion_rate = total_accepted / total_invitations if total_invitations > 0 else 0
        completion_rate = completed_nodes / len(nodes) if nodes else 0
        
        # Calculate average viral coefficient
        viral_coefficients = [
            node.invitations_accepted / max(node.invitations_sent, 1) 
            for node in nodes if node.invitations_sent > 0
        ]
        avg_viral_coefficient = sum(viral_coefficients) / len(viral_coefficients) if viral_coefficients else 0
        
        return {
            "viral_coefficient": avg_viral_coefficient,
            "conversion_rate": conversion_rate,
            "completion_rate": completion_rate
        }
    
    def _generate_graph_nodes(self, company_ids: List[int]) -> List[NetworkGraphNode]:
        """Generate network graph nodes."""
        nodes = []
        
        # Get company and cascade data
        companies_data = self.db.query(
            Company.id,
            Company.name,
            ViralCascadeNode.viral_coefficient,
            ViralCascadeNode.total_invitations_sent,
            ViralCascadeNode.total_invitations_accepted
        ).outerjoin(
            ViralCascadeNode, Company.id == ViralCascadeNode.company_id
        ).filter(Company.id.in_(company_ids)).all()
        
        for company_id, company_name, viral_coeff, invitations_sent, invitations_accepted in companies_data:
            # Calculate node properties
            viral_coefficient = float(viral_coeff or 0)
            invitations_sent = invitations_sent or 0
            invitations_accepted = invitations_accepted or 0
            
            # Node size based on activity
            size = min(10 + (invitations_sent * 0.5), 50)
            
            # Node color based on viral coefficient
            if viral_coefficient > 2.0:
                color = "#ff4444"  # Red for high viral
            elif viral_coefficient > 1.0:
                color = "#ff8844"  # Orange for viral
            elif viral_coefficient > 0.5:
                color = "#ffaa44"  # Yellow for moderate
            else:
                color = "#4488ff"  # Blue for low
            
            # Performance score
            performance_score = min(viral_coefficient * 30 + (invitations_accepted / max(invitations_sent, 1)) * 70, 100)
            
            node = NetworkGraphNode(
                id=str(company_id),
                label=company_name or f"Company {company_id}",
                company_id=company_id,
                size=size,
                color=color,
                shape="circle",
                invitations_sent=invitations_sent,
                invitations_accepted=invitations_accepted,
                viral_coefficient=viral_coefficient,
                performance_score=performance_score
            )
            
            nodes.append(node)
        
        return nodes
    
    def _generate_graph_edges(
        self, 
        connections: List[tuple], 
        valid_company_ids: set
    ) -> List[NetworkGraphEdge]:
        """Generate network graph edges."""
        edges = []
        
        for inviting_id, accepting_id, created_at, accepted_at in connections:
            if accepting_id and inviting_id in valid_company_ids and accepting_id in valid_company_ids:
                # Calculate edge properties
                relationship_strength = 1.0  # Could be based on interaction frequency
                
                edge = NetworkGraphEdge(
                    source=str(inviting_id),
                    target=str(accepting_id),
                    weight=relationship_strength,
                    color="#888888",
                    width=2.0,
                    invitation_date=created_at,
                    acceptance_date=accepted_at,
                    relationship_strength=relationship_strength
                )
                
                edges.append(edge)
        
        return edges
    
    def _get_time_filter(self, timeframe: AnalyticsTimeframe) -> Optional[datetime]:
        """Get datetime filter for timeframe."""
        if timeframe == AnalyticsTimeframe.ALL_TIME:
            return None
        
        days = AnalyticsTimeframe.get_days(timeframe)
        return datetime.utcnow() - timedelta(days=days)
    
    def _calculate_kpi_metrics(self, time_filter: Optional[datetime]) -> Dict[str, Any]:
        """Calculate KPI metrics."""
        # Implementation would calculate actual KPIs
        return {
            "total_network_size": 0,
            "total_invitations_sent": 0,
            "total_invitations_accepted": 0,
            "overall_viral_coefficient": 0.0,
            "overall_conversion_rate": 0.0
        }
    
    def _calculate_growth_metrics(self, timeframe_days: int) -> Dict[str, float]:
        """Calculate growth metrics."""
        # Implementation would calculate actual growth rates
        return {
            "daily_growth_rate": 0.0,
            "weekly_growth_rate": 0.0,
            "monthly_growth_rate": 0.0
        }
    
    def _get_top_performers(self, timeframe_days: int) -> Dict[str, List[Dict[str, Any]]]:
        """Get top performers data."""
        # Implementation would get actual top performers
        return {
            "viral_champions": [],
            "growing_cascades": [],
            "active_inviters": []
        }
    
    def _get_timeline_data(self, timeframe_days: int) -> Dict[str, List[Dict[str, Any]]]:
        """Get timeline data for charts."""
        # Implementation would get actual timeline data
        return {
            "growth": [],
            "conversion": []
        }
    
    def _calculate_network_health_metrics(self, time_filter: Optional[datetime]) -> Dict[str, float]:
        """Calculate network health metrics."""
        # Implementation would calculate actual network health
        return {
            "health_score": 0.0,
            "cascade_survival_rate": 0.0,
            "average_cascade_depth": 0.0
        }
    
    def _calculate_simple_clustering(
        self, 
        nodes: List[NetworkGraphNode], 
        edges: List[NetworkGraphEdge]
    ) -> float:
        """Calculate simplified clustering coefficient."""
        # Simplified implementation
        if len(nodes) < 3:
            return 0.0
        
        # Build adjacency for clustering calculation
        adjacency = {}
        for node in nodes:
            adjacency[node.id] = set()
        
        for edge in edges:
            adjacency[edge.source].add(edge.target)
            adjacency[edge.target].add(edge.source)
        
        # Calculate clustering coefficient
        total_coefficient = 0
        node_count = 0
        
        for node_id, neighbors in adjacency.items():
            if len(neighbors) < 2:
                continue
            
            triangles = 0
            possible_triangles = len(neighbors) * (len(neighbors) - 1) // 2
            
            neighbor_list = list(neighbors)
            for i in range(len(neighbor_list)):
                for j in range(i + 1, len(neighbor_list)):
                    if neighbor_list[j] in adjacency.get(neighbor_list[i], set()):
                        triangles += 1
            
            if possible_triangles > 0:
                total_coefficient += triangles / possible_triangles
                node_count += 1
        
        return total_coefficient / node_count if node_count > 0 else 0

"""
Network analysis service for viral analytics.

This module analyzes network structure and effects, identifying viral patterns,
champions, and growth hotspots in the supplier network.
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc
from collections import defaultdict
import math

from app.models.viral_analytics import ViralCascadeNode, SupplierInvitation
from app.models.company import Company
from app.core.logging import get_logger
from ..models.enums import InvitationStatus, ViralChampionTier, AnalyticsTimeframe
from ..services.query_service import AnalyticsQueryService

logger = get_logger(__name__)


class NetworkAnalyzer:
    """Analyzes network structure and viral effects."""
    
    def __init__(self, db: Session, query_service: AnalyticsQueryService):
        self.db = db
        self.query_service = query_service
    
    def analyze_network_structure(
        self,
        timeframe: AnalyticsTimeframe = AnalyticsTimeframe.LAST_30_DAYS
    ) -> Dict[str, Any]:
        """
        Analyze overall network structure and properties.
        
        Args:
            timeframe: Time period for analysis
            
        Returns:
            Dictionary with network structure analysis
        """
        logger.info("Analyzing network structure", timeframe=timeframe.value)
        
        time_filter = self._get_time_filter(timeframe)
        
        # Get all active connections (accepted invitations)
        connections_query = self.db.query(
            SupplierInvitation.inviting_company_id,
            SupplierInvitation.accepting_company_id
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
        
        connections = connections_query.all()
        
        # Build network graph
        network_graph = self._build_network_graph(connections)
        
        # Calculate network metrics
        total_nodes = len(network_graph)
        total_edges = len(connections)
        
        # Calculate connected components
        connected_components = self._find_connected_components(network_graph)
        largest_component_size = max(len(component) for component in connected_components) if connected_components else 0
        
        # Calculate network density
        max_possible_edges = total_nodes * (total_nodes - 1) if total_nodes > 1 else 0
        network_density = total_edges / max_possible_edges if max_possible_edges > 0 else 0
        
        # Calculate clustering coefficient
        clustering_coefficient = self._calculate_clustering_coefficient(network_graph)
        
        # Calculate average path length
        average_path_length = self._calculate_average_path_length(network_graph)
        
        # Calculate network diameter
        network_diameter = self._calculate_network_diameter(network_graph)
        
        return {
            "total_nodes": total_nodes,
            "total_edges": total_edges,
            "connected_components_count": len(connected_components),
            "largest_component_size": largest_component_size,
            "network_density": network_density,
            "clustering_coefficient": clustering_coefficient,
            "average_path_length": average_path_length,
            "network_diameter": network_diameter,
            "analysis_timestamp": datetime.utcnow().isoformat(),
            "timeframe": timeframe.value
        }
    
    def get_viral_champions(
        self,
        limit: int = 20,
        timeframe: AnalyticsTimeframe = AnalyticsTimeframe.LAST_30_DAYS
    ) -> List[Dict[str, Any]]:
        """
        Identify viral champions based on network performance.
        
        Args:
            limit: Maximum number of champions to return
            timeframe: Time period for analysis
            
        Returns:
            List of viral champion data
        """
        logger.info("Identifying viral champions", limit=limit, timeframe=timeframe.value)
        
        time_filter = self._get_time_filter(timeframe)
        
        # Get cascade nodes with metrics
        query = self.db.query(
            ViralCascadeNode,
            Company.name.label('company_name')
        ).join(
            Company, ViralCascadeNode.company_id == Company.id
        ).filter(
            ViralCascadeNode.viral_coefficient > 1.0
        )
        
        if time_filter:
            query = query.filter(ViralCascadeNode.updated_at >= time_filter)
        
        results = query.order_by(desc(ViralCascadeNode.viral_coefficient)).limit(limit * 2).all()
        
        # Calculate champion scores and tiers
        champions = []
        viral_coefficients = [node.viral_coefficient for node, _ in results if node.viral_coefficient]
        
        for node, company_name in results:
            # Calculate percentile ranking
            percentile = self._calculate_percentile(node.viral_coefficient, viral_coefficients)
            
            # Determine champion tier
            tier = ViralChampionTier.determine_tier(percentile)
            
            # Calculate influence score
            influence_score = self._calculate_influence_score(node)
            
            champion_data = {
                "company_id": node.company_id,
                "company_name": company_name,
                "viral_coefficient": float(node.viral_coefficient or 0),
                "total_invitations_sent": node.total_invitations_sent,
                "total_invitations_accepted": node.total_invitations_accepted,
                "cascade_depth": node.depth or 0,
                "champion_tier": tier.value,
                "percentile_ranking": percentile,
                "influence_score": influence_score,
                "last_updated": node.updated_at.isoformat()
            }
            
            champions.append(champion_data)
        
        # Sort by influence score and return top performers
        champions.sort(key=lambda x: x["influence_score"], reverse=True)
        return champions[:limit]
    
    def get_growth_hotspots(
        self,
        limit: int = 10,
        timeframe: AnalyticsTimeframe = AnalyticsTimeframe.LAST_7_DAYS
    ) -> List[Dict[str, Any]]:
        """
        Identify growth hotspots in the network.
        
        Args:
            limit: Maximum number of hotspots to return
            timeframe: Time period for analysis
            
        Returns:
            List of growth hotspot data
        """
        logger.info("Identifying growth hotspots", limit=limit, timeframe=timeframe.value)
        
        time_filter = self._get_time_filter(timeframe)
        
        # Get recent invitation activity
        activity_query = self.db.query(
            SupplierInvitation.inviting_company_id,
            Company.name.label('company_name'),
            func.count(SupplierInvitation.id).label('recent_invitations'),
            func.count(
                func.case([(SupplierInvitation.status == InvitationStatus.ACCEPTED.value, 1)])
            ).label('recent_acceptances')
        ).join(
            Company, SupplierInvitation.inviting_company_id == Company.id
        )
        
        if time_filter:
            activity_query = activity_query.filter(
                SupplierInvitation.created_at >= time_filter
            )
        
        activity_results = activity_query.group_by(
            SupplierInvitation.inviting_company_id, Company.name
        ).having(
            func.count(SupplierInvitation.id) >= 3  # Minimum activity threshold
        ).order_by(desc(func.count(SupplierInvitation.id))).limit(limit * 2).all()
        
        # Calculate growth scores
        hotspots = []
        for company_id, company_name, recent_invitations, recent_acceptances in activity_results:
            # Get cascade node for additional metrics
            cascade_node = self.db.query(ViralCascadeNode).filter(
                ViralCascadeNode.company_id == company_id
            ).first()
            
            # Calculate growth score
            conversion_rate = recent_acceptances / recent_invitations if recent_invitations > 0 else 0
            viral_coefficient = cascade_node.viral_coefficient if cascade_node else 0
            
            growth_score = (
                recent_invitations * 0.4 +  # Activity volume
                conversion_rate * 30 +      # Conversion quality
                viral_coefficient * 20 +    # Viral potential
                recent_acceptances * 0.6    # Success count
            )
            
            hotspot_data = {
                "company_id": company_id,
                "company_name": company_name,
                "recent_invitations": recent_invitations,
                "recent_acceptances": recent_acceptances,
                "conversion_rate": conversion_rate,
                "viral_coefficient": float(viral_coefficient or 0),
                "growth_score": growth_score,
                "cascade_depth": cascade_node.depth if cascade_node else 0
            }
            
            hotspots.append(hotspot_data)
        
        # Sort by growth score and return top hotspots
        hotspots.sort(key=lambda x: x["growth_score"], reverse=True)
        return hotspots[:limit]
    
    def calculate_network_density(
        self,
        timeframe: AnalyticsTimeframe = AnalyticsTimeframe.LAST_30_DAYS
    ) -> float:
        """
        Calculate network density for the specified timeframe.
        
        Args:
            timeframe: Time period for analysis
            
        Returns:
            Network density value (0-1)
        """
        time_filter = self._get_time_filter(timeframe)
        
        # Get unique companies in network
        companies_query = self.db.query(
            SupplierInvitation.inviting_company_id.label('company_id')
        ).union(
            self.db.query(
                SupplierInvitation.accepting_company_id.label('company_id')
            ).filter(SupplierInvitation.accepting_company_id.isnot(None))
        )
        
        if time_filter:
            companies_query = companies_query.filter(
                SupplierInvitation.created_at >= time_filter
            )
        
        unique_companies = companies_query.distinct().count()
        
        # Get total connections
        connections_query = self.db.query(SupplierInvitation).filter(
            SupplierInvitation.status == InvitationStatus.ACCEPTED.value
        )
        
        if time_filter:
            connections_query = connections_query.filter(
                SupplierInvitation.accepted_at >= time_filter
            )
        
        total_connections = connections_query.count()
        
        # Calculate density
        max_possible_connections = unique_companies * (unique_companies - 1)
        density = total_connections / max_possible_connections if max_possible_connections > 0 else 0
        
        return density
    
    def find_influence_clusters(
        self,
        min_cluster_size: int = 5,
        timeframe: AnalyticsTimeframe = AnalyticsTimeframe.LAST_30_DAYS
    ) -> List[Dict[str, Any]]:
        """
        Find clusters of influential companies in the network.
        
        Args:
            min_cluster_size: Minimum size for a cluster
            timeframe: Time period for analysis
            
        Returns:
            List of influence cluster data
        """
        logger.info("Finding influence clusters", min_cluster_size=min_cluster_size)
        
        time_filter = self._get_time_filter(timeframe)
        
        # Get network connections
        connections_query = self.db.query(
            SupplierInvitation.inviting_company_id,
            SupplierInvitation.accepting_company_id
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
        
        connections = connections_query.all()
        
        # Build network graph
        network_graph = self._build_network_graph(connections)
        
        # Find connected components (clusters)
        connected_components = self._find_connected_components(network_graph)
        
        # Filter and analyze clusters
        clusters = []
        for i, component in enumerate(connected_components):
            if len(component) >= min_cluster_size:
                # Calculate cluster metrics
                cluster_metrics = self._analyze_cluster(component, network_graph)
                
                cluster_data = {
                    "cluster_id": i,
                    "size": len(component),
                    "companies": list(component),
                    "total_connections": cluster_metrics["total_connections"],
                    "density": cluster_metrics["density"],
                    "average_viral_coefficient": cluster_metrics["avg_viral_coefficient"],
                    "influence_score": cluster_metrics["influence_score"]
                }
                
                clusters.append(cluster_data)
        
        # Sort by influence score
        clusters.sort(key=lambda x: x["influence_score"], reverse=True)
        
        return clusters
    
    def _get_time_filter(self, timeframe: AnalyticsTimeframe) -> Optional[datetime]:
        """Get datetime filter for timeframe."""
        if timeframe == AnalyticsTimeframe.ALL_TIME:
            return None
        
        days = AnalyticsTimeframe.get_days(timeframe)
        return datetime.utcnow() - timedelta(days=days)
    
    def _build_network_graph(self, connections: List[Tuple[int, int]]) -> Dict[int, set]:
        """Build network graph from connections."""
        graph = defaultdict(set)
        
        for inviting_id, accepting_id in connections:
            if accepting_id:  # Ensure accepting_id is not None
                graph[inviting_id].add(accepting_id)
                graph[accepting_id].add(inviting_id)  # Undirected graph
        
        return dict(graph)
    
    def _find_connected_components(self, graph: Dict[int, set]) -> List[set]:
        """Find connected components in the graph."""
        visited = set()
        components = []
        
        for node in graph:
            if node not in visited:
                component = set()
                self._dfs(graph, node, visited, component)
                components.append(component)
        
        return components
    
    def _dfs(self, graph: Dict[int, set], node: int, visited: set, component: set):
        """Depth-first search for connected components."""
        visited.add(node)
        component.add(node)
        
        for neighbor in graph.get(node, set()):
            if neighbor not in visited:
                self._dfs(graph, neighbor, visited, component)
    
    def _calculate_clustering_coefficient(self, graph: Dict[int, set]) -> float:
        """Calculate clustering coefficient of the network."""
        if len(graph) < 3:
            return 0.0
        
        total_coefficient = 0
        node_count = 0
        
        for node in graph:
            neighbors = graph[node]
            if len(neighbors) < 2:
                continue
            
            # Count triangles
            triangles = 0
            possible_triangles = len(neighbors) * (len(neighbors) - 1) // 2
            
            for neighbor1 in neighbors:
                for neighbor2 in neighbors:
                    if neighbor1 < neighbor2 and neighbor2 in graph.get(neighbor1, set()):
                        triangles += 1
            
            if possible_triangles > 0:
                total_coefficient += triangles / possible_triangles
                node_count += 1
        
        return total_coefficient / node_count if node_count > 0 else 0
    
    def _calculate_average_path_length(self, graph: Dict[int, set]) -> float:
        """Calculate average path length in the network."""
        if len(graph) < 2:
            return 0.0
        
        total_distance = 0
        path_count = 0
        
        nodes = list(graph.keys())
        for i, start_node in enumerate(nodes):
            # BFS to find shortest paths
            distances = self._bfs_distances(graph, start_node)
            
            for j in range(i + 1, len(nodes)):
                end_node = nodes[j]
                if end_node in distances:
                    total_distance += distances[end_node]
                    path_count += 1
        
        return total_distance / path_count if path_count > 0 else 0
    
    def _calculate_network_diameter(self, graph: Dict[int, set]) -> int:
        """Calculate network diameter (longest shortest path)."""
        if len(graph) < 2:
            return 0
        
        max_distance = 0
        
        for start_node in graph:
            distances = self._bfs_distances(graph, start_node)
            if distances:
                max_distance = max(max_distance, max(distances.values()))
        
        return max_distance
    
    def _bfs_distances(self, graph: Dict[int, set], start_node: int) -> Dict[int, int]:
        """BFS to find shortest distances from start node."""
        distances = {start_node: 0}
        queue = [start_node]
        
        while queue:
            current = queue.pop(0)
            current_distance = distances[current]
            
            for neighbor in graph.get(current, set()):
                if neighbor not in distances:
                    distances[neighbor] = current_distance + 1
                    queue.append(neighbor)
        
        return distances
    
    def _calculate_percentile(self, value: float, values: List[float]) -> float:
        """Calculate percentile ranking of a value."""
        if not values:
            return 0.0
        
        sorted_values = sorted(values)
        rank = sum(1 for v in sorted_values if v <= value)
        return rank / len(sorted_values)
    
    def _calculate_influence_score(self, node: ViralCascadeNode) -> float:
        """Calculate influence score for a cascade node."""
        viral_score = min(node.viral_coefficient / 3.0, 1.0) * 40 if node.viral_coefficient else 0
        invitation_score = min(node.total_invitations_sent / 50.0, 1.0) * 30
        conversion_score = (
            node.total_invitations_accepted / max(node.total_invitations_sent, 1)
        ) * 20
        depth_score = min((node.depth or 0) / 5.0, 1.0) * 10
        
        return viral_score + invitation_score + conversion_score + depth_score
    
    def _analyze_cluster(self, component: set, graph: Dict[int, set]) -> Dict[str, Any]:
        """Analyze metrics for a cluster."""
        # Count internal connections
        total_connections = 0
        for node in component:
            for neighbor in graph.get(node, set()):
                if neighbor in component:
                    total_connections += 1
        
        total_connections //= 2  # Undirected graph, so divide by 2
        
        # Calculate cluster density
        max_connections = len(component) * (len(component) - 1) // 2
        density = total_connections / max_connections if max_connections > 0 else 0
        
        # Get viral coefficients for cluster members
        viral_coefficients = []
        for company_id in component:
            node = self.db.query(ViralCascadeNode).filter(
                ViralCascadeNode.company_id == company_id
            ).first()
            if node and node.viral_coefficient:
                viral_coefficients.append(node.viral_coefficient)
        
        avg_viral_coefficient = sum(viral_coefficients) / len(viral_coefficients) if viral_coefficients else 0
        
        # Calculate influence score
        influence_score = (
            len(component) * 0.3 +           # Size factor
            density * 50 +                   # Density factor
            avg_viral_coefficient * 20       # Viral factor
        )
        
        return {
            "total_connections": total_connections,
            "density": density,
            "avg_viral_coefficient": avg_viral_coefficient,
            "influence_score": influence_score
        }

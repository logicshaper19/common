"""
Logistics and Delivery Management Functions
Handles delivery tracking, transportation, and fulfillment operations.
"""
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta, date
from dataclasses import dataclass
import logging
from enum import Enum

from .certification_cache import cached, performance_tracked
from .secure_query_builder import (
    SecureQueryBuilder, QueryOperator, execute_secure_query, SecureQueryError
)

logger = logging.getLogger(__name__)

class DeliveryStatus(Enum):
    PENDING = "pending"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    FAILED = "failed"

class TransportationType(Enum):
    TRUCK = "truck"
    SHIP = "ship"
    RAIL = "rail"
    PIPELINE = "pipeline"
    MULTIMODAL = "multimodal"

@dataclass
class DeliveryInfo:
    """Delivery tracking information."""
    purchase_order_id: str
    po_number: str
    delivery_status: str
    delivery_date: date
    delivery_location: str
    delivered_at: Optional[datetime]
    delivery_confirmed_by: Optional[str]
    delivery_notes: Optional[str]
    buyer_company: str
    seller_company: str
    product_name: str
    quantity: float
    unit: str
    days_until_delivery: Optional[int]
    is_overdue: bool
    tracking_updates: List[Dict[str, Any]] = None

@dataclass
class ShipmentInfo:
    """Shipment and transportation details."""
    id: str
    purchase_order_id: str
    shipment_reference: str
    transportation_type: str
    carrier_name: Optional[str]
    origin_location: str
    destination_location: str
    estimated_departure: Optional[datetime]
    actual_departure: Optional[datetime]
    estimated_arrival: Optional[datetime]
    actual_arrival: Optional[datetime]
    current_status: str
    tracking_number: Optional[str]
    route_details: List[Dict[str, Any]]
    cargo_details: Dict[str, Any]
    estimated_cost: Optional[float]

@dataclass
class LogisticsAnalytics:
    """Logistics performance analytics."""
    total_deliveries: int
    on_time_delivery_rate: float
    average_delivery_time_days: float
    pending_deliveries: int
    overdue_deliveries: int
    delivery_performance_by_route: Dict[str, Dict[str, float]]
    carrier_performance: Dict[str, Dict[str, Any]]
    cost_analytics: Dict[str, float]
    geographic_distribution: Dict[str, int]

@dataclass
class InventoryMovement:
    """Inventory movement and warehouse operations."""
    id: str
    batch_id: str
    movement_type: str  # 'inbound', 'outbound', 'transfer', 'adjustment'
    warehouse_location: str
    quantity: float
    unit: str
    movement_date: datetime
    reference_document: Optional[str]  # PO number, transfer order, etc.
    operator: str
    notes: Optional[str]
    before_quantity: float
    after_quantity: float
    product_name: str
    batch_transparency_score: float

class LogisticsManager:
    """Logistics and delivery management functions."""
    
    def __init__(self, db_connection):
        self.db = db_connection
    
    @cached(ttl=120)  # 2-minute cache for real-time delivery data
    @performance_tracked
    def get_deliveries(
        self,
        company_id: Optional[str] = None,
        delivery_status: Optional[str] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        overdue_only: bool = False,
        pending_confirmation: bool = False,
        role_filter: Optional[str] = None,  # 'buyer', 'seller', or None
        limit: int = 50
    ) -> Tuple[List[DeliveryInfo], Dict[str, Any]]:
        """
        Get delivery tracking information with status and performance metrics.
        
        Args:
            company_id: Filter by specific company
            delivery_status: Filter by delivery status
            date_from: Start date for delivery date range
            date_to: End date for delivery date range
            overdue_only: Show only overdue deliveries
            pending_confirmation: Show only deliveries awaiting confirmation
            role_filter: Filter by company role ('buyer', 'seller')
            limit: Maximum results to return
            
        Returns:
            Tuple of (delivery list, performance metrics)
        """
        try:
            # Use secure query builder to prevent SQL injection
            builder = SecureQueryBuilder()
            builder.select([
                'po.id as purchase_order_id', 'po.po_number', 'po.delivery_status',
                'po.delivery_date', 'po.delivery_location', 'po.delivered_at',
                'po.delivery_confirmed_by', 'po.delivery_notes',
                'bc.name as buyer_company', 'sc.name as seller_company',
                'p.name as product_name', 'po.quantity', 'po.unit',
                'u.full_name as confirmed_by_name',
                'DATEDIFF(po.delivery_date, CURDATE()) as days_until_delivery'
            ], 'purchase_orders', 'po')
            
            builder.join('companies bc', 'po.buyer_company_id = bc.id')
            builder.join('companies sc', 'po.seller_company_id = sc.id')
            builder.join('products p', 'po.product_id = p.id')
            builder.join('users u', 'po.delivery_confirmed_by = u.id', 'LEFT JOIN')
            builder.where('po.delivery_date', QueryOperator.IS_NOT_NULL)
            
            if company_id and role_filter:
                if role_filter == 'buyer':
                    builder.where('po.buyer_company_id', QueryOperator.EQUALS, company_id)
                elif role_filter == 'seller':
                    builder.where('po.seller_company_id', QueryOperator.EQUALS, company_id)
            elif company_id:
                builder.where_raw('(po.buyer_company_id = %s OR po.seller_company_id = %s)', [company_id, company_id])
            
            if delivery_status:
                builder.where('po.delivery_status', QueryOperator.EQUALS, delivery_status)
            
            if date_from:
                builder.where('po.delivery_date', QueryOperator.GREATER_EQUAL, date_from)
            
            if date_to:
                builder.where('po.delivery_date', QueryOperator.LESS_EQUAL, date_to)
            
            if overdue_only:
                builder.where_raw('po.delivery_date < CURDATE()', [])
                builder.where('po.delivery_status', QueryOperator.NOT_EQUALS, 'delivered')
            
            if pending_confirmation:
                builder.where('po.delivery_status', QueryOperator.EQUALS, 'in_transit')
                builder.where('po.delivered_at', QueryOperator.IS_NULL)
            
            builder.order_by('po.delivery_date', 'ASC')
            builder.limit(limit)
            
            query, params = builder.build()
            results = execute_secure_query(self.db, query, params)
            
            deliveries = []
            on_time_count = 0
            overdue_count = 0
            total_delivery_time = 0
            delivered_count = 0
            
            for row in results:
                days_until_delivery = row['days_until_delivery']
                is_overdue = (
                    days_until_delivery < 0 and 
                    row['delivery_status'] != 'delivered'
                )
                
                if is_overdue:
                    overdue_count += 1
                
                # Calculate delivery performance
                if row['delivery_status'] == 'delivered' and row['delivered_at']:
                    delivered_count += 1
                    actual_delivery_date = row['delivered_at'].date()
                    scheduled_date = row['delivery_date']
                    delivery_time = (actual_delivery_date - scheduled_date).days
                    total_delivery_time += delivery_time
                    
                    if delivery_time <= 0:  # On time or early
                        on_time_count += 1
                
                # Get tracking updates (simplified - would integrate with tracking systems)
                tracking_updates = self._get_tracking_updates(row['purchase_order_id'])
                
                delivery = DeliveryInfo(
                    purchase_order_id=row['purchase_order_id'],
                    po_number=row['po_number'],
                    delivery_status=row['delivery_status'],
                    delivery_date=row['delivery_date'],
                    delivery_location=row['delivery_location'],
                    delivered_at=row['delivered_at'],
                    delivery_confirmed_by=row['confirmed_by_name'],
                    delivery_notes=row['delivery_notes'],
                    buyer_company=row['buyer_company'],
                    seller_company=row['seller_company'],
                    product_name=row['product_name'],
                    quantity=float(row['quantity']),
                    unit=row['unit'],
                    days_until_delivery=days_until_delivery,
                    is_overdue=is_overdue,
                    tracking_updates=tracking_updates
                )
                deliveries.append(delivery)
            
            # Calculate performance metrics
            on_time_rate = (on_time_count / delivered_count * 100) if delivered_count > 0 else 100
            avg_delivery_time = total_delivery_time / delivered_count if delivered_count > 0 else 0
            
            # Get status distribution
            status_distribution = self._get_delivery_status_distribution(company_id, role_filter)
            
            metadata = {
                'total_deliveries': len(deliveries),
                'on_time_delivery_rate': round(on_time_rate, 2),
                'average_delivery_time_days': round(avg_delivery_time, 1),
                'overdue_deliveries': overdue_count,
                'pending_deliveries': len([d for d in deliveries if d.delivery_status == 'pending']),
                'in_transit_deliveries': len([d for d in deliveries if d.delivery_status == 'in_transit']),
                'status_distribution': status_distribution,
                'filters_applied': {
                    'company_id': company_id,
                    'role_filter': role_filter,
                    'delivery_status': delivery_status,
                    'date_range': [date_from, date_to] if date_from or date_to else None
                }
            }
            
            return deliveries, metadata
            
        except (SecureQueryError, Exception) as e:
            logger.error(f"Error getting deliveries", exc_info=True)
            return [], {'error': 'Failed to retrieve deliveries', 'total_deliveries': 0}
    
    @cached(ttl=300)  # 5-minute cache for shipment data
    @performance_tracked
    def get_shipments(
        self,
        company_id: Optional[str] = None,
        transportation_type: Optional[str] = None,
        carrier_name: Optional[str] = None,
        route: Optional[str] = None,
        status: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        limit: int = 30
    ) -> Tuple[List[ShipmentInfo], Dict[str, Any]]:
        """
        Get shipment and transportation tracking information.
        
        Args:
            company_id: Filter by company
            transportation_type: Filter by transport method
            carrier_name: Filter by carrier
            route: Filter by origin-destination route
            status: Filter by shipment status
            date_from: Start date for shipment period
            date_to: End date for shipment period
            limit: Maximum results to return
            
        Returns:
            Tuple of (shipment list, transportation analytics)
        """
        try:
            # Note: This would typically integrate with transportation management systems
            # For now, we'll simulate shipment data based on purchase orders
            
            # Use secure query builder to prevent SQL injection
            builder = SecureQueryBuilder()
            builder.select([
                'po.id as purchase_order_id', 'po.po_number',
                'po.delivery_date', 'po.delivery_location', 'po.delivery_status',
                'bc.name as buyer_company', 'bc.address_city as buyer_city',
                'sc.name as seller_company', 'sc.address_city as seller_city',
                'p.name as product_name', 'po.quantity', 'po.unit',
                'po.created_at', 'po.confirmed_at'
            ], 'purchase_orders', 'po')
            
            builder.join('companies bc', 'po.buyer_company_id = bc.id')
            builder.join('companies sc', 'po.seller_company_id = sc.id')
            builder.join('products p', 'po.product_id = p.id')
            builder.where('po.status', QueryOperator.IN, ['confirmed', 'in_transit', 'delivered'])
            
            if company_id:
                builder.where_raw('(po.buyer_company_id = %s OR po.seller_company_id = %s)', [company_id, company_id])
            
            if status:
                # Map delivery status to shipment status
                status_mapping = {
                    'confirmed': 'preparing',
                    'in_transit': 'in_transit',
                    'delivered': 'delivered'
                }
                delivery_status = {v: k for k, v in status_mapping.items()}.get(status)
                if delivery_status:
                    builder.where('po.delivery_status', QueryOperator.EQUALS, delivery_status)
            
            if date_from:
                builder.where('po.delivery_date', QueryOperator.GREATER_EQUAL, date_from.date())
            
            if date_to:
                builder.where('po.delivery_date', QueryOperator.LESS_EQUAL, date_to.date())
            
            builder.order_by('po.delivery_date', 'DESC')
            builder.limit(limit)
            
            query, params = builder.build()
            results = execute_secure_query(self.db, query, params)
            
            shipments = []
            transportation_modes = {}
            carrier_performance = {}
            
            for row in results:
                # Simulate shipment data (in real implementation, this would come from TMS)
                transportation_type = self._determine_transportation_type(
                    row['seller_city'], row['buyer_city'], row['product_name']
                )
                
                carrier_name = self._assign_carrier(transportation_type, row['quantity'])
                
                # Generate route details
                route_details = self._generate_route_details(
                    row['seller_city'], row['buyer_city'], transportation_type
                )
                
                # Calculate timing
                estimated_departure = row['confirmed_at'] + timedelta(days=1) if row['confirmed_at'] else None
                estimated_arrival = datetime.combine(row['delivery_date'], datetime.min.time()) if row['delivery_date'] else None
                
                shipment = ShipmentInfo(
                    id=f"SHIP-{row['po_number']}-001",
                    purchase_order_id=row['purchase_order_id'],
                    shipment_reference=f"REF-{row['po_number']}",
                    transportation_type=transportation_type,
                    carrier_name=carrier_name,
                    origin_location=row['seller_city'] or "Origin",
                    destination_location=row['buyer_city'] or row['delivery_location'],
                    estimated_departure=estimated_departure,
                    actual_departure=estimated_departure if row['delivery_status'] != 'confirmed' else None,
                    estimated_arrival=estimated_arrival,
                    actual_arrival=estimated_arrival if row['delivery_status'] == 'delivered' else None,
                    current_status=self._map_delivery_to_shipment_status(row['delivery_status']),
                    tracking_number=f"TRK-{row['po_number'][:6]}-{hash(row['po_number']) % 10000:04d}",
                    route_details=route_details,
                    cargo_details={
                        'product': row['product_name'],
                        'quantity': float(row['quantity']),
                        'unit': row['unit'],
                        'special_handling': self._get_special_handling_requirements(row['product_name'])
                    },
                    estimated_cost=self._estimate_shipping_cost(
                        transportation_type, float(row['quantity']), len(route_details)
                    )
                )
                shipments.append(shipment)
                
                # Track analytics
                transportation_modes[transportation_type] = transportation_modes.get(transportation_type, 0) + 1
                
                if carrier_name not in carrier_performance:
                    carrier_performance[carrier_name] = {'shipments': 0, 'on_time': 0, 'total_cost': 0}
                carrier_performance[carrier_name]['shipments'] += 1
                carrier_performance[carrier_name]['total_cost'] += shipment.estimated_cost or 0
                
                if row['delivery_status'] == 'delivered':
                    carrier_performance[carrier_name]['on_time'] += 1
            
            # Calculate carrier performance rates
            for carrier in carrier_performance:
                total = carrier_performance[carrier]['shipments']
                on_time = carrier_performance[carrier]['on_time']
                carrier_performance[carrier]['on_time_rate'] = (on_time / total * 100) if total > 0 else 0
                carrier_performance[carrier]['avg_cost'] = (
                    carrier_performance[carrier]['total_cost'] / total if total > 0 else 0
                )
            
            metadata = {
                'total_shipments': len(shipments),
                'transportation_distribution': transportation_modes,
                'carrier_performance': carrier_performance,
                'route_analytics': self._analyze_routes(shipments),
                'cost_summary': {
                    'total_estimated_cost': sum(s.estimated_cost or 0 for s in shipments),
                    'average_cost_per_shipment': sum(s.estimated_cost or 0 for s in shipments) / len(shipments) if shipments else 0
                },
                'filters_applied': {
                    'company_id': company_id,
                    'transportation_type': transportation_type,
                    'carrier_name': carrier_name
                }
            }
            
            return shipments, metadata
            
        except (SecureQueryError, Exception) as e:
            logger.error(f"Error getting shipments", exc_info=True)
            return [], {'error': 'Failed to retrieve shipments', 'total_shipments': 0}
    
    @cached(ttl=180)  # 3-minute cache for inventory movements
    @performance_tracked
    def get_inventory_movements(
        self,
        company_id: Optional[str] = None,
        warehouse_location: Optional[str] = None,
        movement_type: Optional[str] = None,
        product_name: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        limit: int = 50
    ) -> Tuple[List[InventoryMovement], Dict[str, Any]]:
        """
        Get inventory movement and warehouse operations tracking.
        
        Args:
            company_id: Filter by company
            warehouse_location: Filter by warehouse
            movement_type: Filter by movement type
            product_name: Filter by product
            date_from: Start date for movements
            date_to: End date for movements
            limit: Maximum results to return
            
        Returns:
            Tuple of (movement list, warehouse analytics)
        """
        try:
            # This would typically integrate with warehouse management systems
            # For now, simulate based on batch movements and purchase orders
            
            # Use secure query builder to prevent SQL injection
            builder = SecureQueryBuilder()
            builder.select([
                'b.batch_id', 'b.company_id', 'b.quantity', 'b.status',
                'b.created_at', 'b.updated_at',
                'c.name as company_name', 'c.address_city as warehouse_location',
                'p.name as product_name', 'p.default_unit as unit',
                'b.transparency_score',
                'po.po_number as reference_document'
            ], 'batches', 'b')
            
            builder.join('companies c', 'b.company_id = c.id')
            builder.join('products p', 'b.product_id = p.id')
            builder.join('purchase_orders po', "b.batch_id LIKE CONCAT('%', po.po_number, '%')", 'LEFT JOIN')
            
            if company_id:
                builder.where('b.company_id', QueryOperator.EQUALS, company_id)
            
            if warehouse_location:
                builder.where('c.address_city', QueryOperator.LIKE, warehouse_location)
            
            if product_name:
                builder.where('p.name', QueryOperator.LIKE, product_name)
            
            if date_from:
                builder.where('b.updated_at', QueryOperator.GREATER_EQUAL, date_from)
            
            if date_to:
                builder.where('b.updated_at', QueryOperator.LESS_EQUAL, date_to)
            
            builder.order_by('b.updated_at', 'DESC')
            builder.limit(limit)
            
            query, params = builder.build()
            results = execute_secure_query(self.db, query, params)
            
            movements = []
            movement_types = {}
            warehouse_activity = {}
            
            for row in results:
                # Simulate movement data based on batch status changes
                movement_type_sim = self._determine_movement_type(row['status'])
                
                # Simulate quantity changes
                before_quantity = float(row['quantity']) * 1.1  # Simulate previous quantity
                after_quantity = float(row['quantity'])
                
                movement = InventoryMovement(
                    id=f"MOV-{row['batch_id'][:8]}-{hash(str(row['updated_at'])) % 1000:03d}",
                    batch_id=row['batch_id'],
                    movement_type=movement_type_sim,
                    warehouse_location=row['warehouse_location'] or 'Main Warehouse',
                    quantity=abs(before_quantity - after_quantity),
                    unit=row['unit'],
                    movement_date=row['updated_at'],
                    reference_document=row['reference_document'],
                    operator='System',  # Would track actual user
                    notes=f"Batch status changed to {row['status']}",
                    before_quantity=before_quantity,
                    after_quantity=after_quantity,
                    product_name=row['product_name'],
                    batch_transparency_score=float(row['transparency_score']) if row['transparency_score'] else 0
                )
                movements.append(movement)
                
                # Track analytics
                movement_types[movement_type_sim] = movement_types.get(movement_type_sim, 0) + 1
                
                warehouse = movement.warehouse_location
                if warehouse not in warehouse_activity:
                    warehouse_activity[warehouse] = {'movements': 0, 'total_quantity': 0}
                warehouse_activity[warehouse]['movements'] += 1
                warehouse_activity[warehouse]['total_quantity'] += movement.quantity
            
            metadata = {
                'total_movements': len(movements),
                'movement_type_distribution': movement_types,
                'warehouse_activity': warehouse_activity,
                'quantity_summary': {
                    'total_quantity_moved': sum(m.quantity for m in movements),
                    'avg_movement_size': sum(m.quantity for m in movements) / len(movements) if movements else 0
                },
                'transparency_analytics': {
                    'avg_transparency_score': sum(m.batch_transparency_score for m in movements) / len(movements) if movements else 0,
                    'high_transparency_movements': len([m for m in movements if m.batch_transparency_score >= 80])
                }
            }
            
            return movements, metadata
            
        except (SecureQueryError, Exception) as e:
            logger.error(f"Error getting inventory movements", exc_info=True)
            return [], {'error': 'Failed to retrieve inventory movements', 'total_movements': 0}
    
    @cached(ttl=600)  # 10-minute cache for logistics analytics
    @performance_tracked
    def get_logistics_analytics(
        self,
        company_id: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        include_forecasting: bool = False
    ) -> Tuple[LogisticsAnalytics, Dict[str, Any]]:
        """
        Get comprehensive logistics performance analytics and KPIs.
        
        Args:
            company_id: Focus on specific company
            date_from: Start date for analytics period
            date_to: End date for analytics period
            include_forecasting: Include predictive analytics
            
        Returns:
            Tuple of (analytics object, additional insights)
        """
        try:
            # Set default date range
            if not date_to:
                date_to = datetime.now()
            if not date_from:
                date_from = date_to - timedelta(days=90)
            
            # Get delivery performance data
            deliveries, delivery_meta = self.get_deliveries(
                company_id=company_id,
                date_from=date_from.date(),
                date_to=date_to.date(),
                limit=200
            )
            
            # Get shipment data
            shipments, shipment_meta = self.get_shipments(
                company_id=company_id,
                date_from=date_from,
                date_to=date_to,
                limit=100
            )
            
            # Calculate route performance
            route_performance = {}
            for shipment in shipments:
                route_key = f"{shipment.origin_location} → {shipment.destination_location}"
                if route_key not in route_performance:
                    route_performance[route_key] = {
                        'shipments': 0,
                        'avg_cost': 0,
                        'on_time_rate': 0,
                        'total_cost': 0
                    }
                
                route_performance[route_key]['shipments'] += 1
                route_performance[route_key]['total_cost'] += shipment.estimated_cost or 0
                
                if shipment.current_status == 'delivered':
                    # Simulate on-time calculation
                    route_performance[route_key]['on_time_rate'] += 1
            
            # Calculate averages for routes
            for route in route_performance:
                total_shipments = route_performance[route]['shipments']
                route_performance[route]['avg_cost'] = (
                    route_performance[route]['total_cost'] / total_shipments if total_shipments > 0 else 0
                )
                route_performance[route]['on_time_rate'] = (
                    route_performance[route]['on_time_rate'] / total_shipments * 100 if total_shipments > 0 else 0
                )
            
            # Geographic distribution
            geographic_dist = {}
            for delivery in deliveries:
                location = delivery.delivery_location.split(',')[0] if ',' in delivery.delivery_location else delivery.delivery_location
                geographic_dist[location] = geographic_dist.get(location, 0) + 1
            
            analytics = LogisticsAnalytics(
                total_deliveries=delivery_meta.get('total_deliveries', 0),
                on_time_delivery_rate=delivery_meta.get('on_time_delivery_rate', 0),
                average_delivery_time_days=delivery_meta.get('average_delivery_time_days', 0),
                pending_deliveries=delivery_meta.get('pending_deliveries', 0),
                overdue_deliveries=delivery_meta.get('overdue_deliveries', 0),
                delivery_performance_by_route=route_performance,
                carrier_performance=shipment_meta.get('carrier_performance', {}),
                cost_analytics=shipment_meta.get('cost_summary', {}),
                geographic_distribution=geographic_dist
            )
            
            # Generate insights and recommendations
            insights = self._generate_logistics_insights(analytics, deliveries, shipments)
            
            # Forecasting (if requested)
            forecasting_data = {}
            if include_forecasting:
                forecasting_data = self._generate_logistics_forecasting(deliveries, shipments)
            
            metadata = {
                'analysis_period': {
                    'from': date_from.isoformat(),
                    'to': date_to.isoformat(),
                    'days': (date_to - date_from).days
                },
                'key_insights': insights,
                'performance_score': self._calculate_logistics_performance_score(analytics),
                'forecasting': forecasting_data,
                'recommendations': self._generate_logistics_recommendations(analytics)
            }
            
            return analytics, metadata
            
        except Exception as e:
            logger.error(f"Error generating logistics analytics: {str(e)}")
            return LogisticsAnalytics(0, 0, 0, 0, 0, {}, {}, {}, {}), {'error': str(e)}
    
    # Helper methods
    
    def _get_tracking_updates(self, purchase_order_id: str) -> List[Dict[str, Any]]:
        """Get tracking updates for a purchase order."""
        # Simulate tracking updates (would integrate with tracking APIs)
        return [
            {
                'timestamp': datetime.now() - timedelta(days=2),
                'status': 'picked_up',
                'location': 'Origin Warehouse',
                'description': 'Package picked up by carrier'
            },
            {
                'timestamp': datetime.now() - timedelta(days=1),
                'status': 'in_transit',
                'location': 'Distribution Center',
                'description': 'Package in transit'
            }
        ]
    
    def _get_delivery_status_distribution(self, company_id: Optional[str], role_filter: Optional[str]) -> Dict[str, int]:
        """Get distribution of delivery statuses."""
        try:
            query = """
                SELECT delivery_status, COUNT(*) as count
                FROM purchase_orders po
                WHERE po.delivery_date IS NOT NULL
            """
            params = []
            
            if company_id and role_filter:
                if role_filter == 'buyer':
                    query += " AND po.buyer_company_id = %s"
                    params.append(company_id)
                elif role_filter == 'seller':
                    query += " AND po.seller_company_id = %s"
                    params.append(company_id)
            elif company_id:
                query += " AND (po.buyer_company_id = %s OR po.seller_company_id = %s)"
                params.extend([company_id, company_id])
            
            query += " GROUP BY delivery_status"
            
            cursor = self.db.cursor(dictionary=True)
            cursor.execute(query, params)
            results = cursor.fetchall()
            
            return {row['delivery_status']: row['count'] for row in results}
            
        except Exception:
            return {}
    
    def _determine_transportation_type(self, origin: str, destination: str, product: str) -> str:
        """Determine transportation type based on origin, destination, and product."""
        # Simplified logic - would use more sophisticated routing in practice
        if origin and destination:
            if 'oil' in product.lower() and origin != destination:
                return 'ship'  # Palm oil often shipped by tanker
            elif origin == destination:
                return 'truck'  # Local delivery
            else:
                return 'multimodal'  # International shipments
        return 'truck'
    
    def _assign_carrier(self, transportation_type: str, quantity: float) -> str:
        """Assign carrier based on transportation type and quantity."""
        carriers = {
            'truck': ['Local Transport Co.', 'Regional Freight', 'Express Delivery'],
            'ship': ['Global Shipping Lines', 'Ocean Freight Corp', 'Maritime Transport'],
            'multimodal': ['Integrated Logistics', 'Global Supply Chain', 'Multi-Modal Express']
        }
        
        carrier_list = carriers.get(transportation_type, ['General Transport'])
        # Simple selection based on quantity (larger quantities get specialized carriers)
        if quantity > 100:
            return carrier_list[0] if len(carrier_list) > 0 else 'General Transport'
        else:
            return carrier_list[-1] if len(carrier_list) > 0 else 'General Transport'
    
    def _generate_route_details(self, origin: str, destination: str, transport_type: str) -> List[Dict[str, Any]]:
        """Generate route details for shipment."""
        if transport_type == 'ship':
            return [
                {'step': 1, 'location': origin, 'type': 'origin_port'},
                {'step': 2, 'location': 'International Waters', 'type': 'transit'},
                {'step': 3, 'location': destination, 'type': 'destination_port'}
            ]
        else:
            return [
                {'step': 1, 'location': origin, 'type': 'pickup'},
                {'step': 2, 'location': destination, 'type': 'delivery'}
            ]
    
    def _map_delivery_to_shipment_status(self, delivery_status: str) -> str:
        """Map delivery status to shipment status."""
        mapping = {
            'pending': 'preparing',
            'in_transit': 'in_transit',
            'delivered': 'delivered',
            'failed': 'failed'
        }
        return mapping.get(delivery_status, 'unknown')
    
    def _get_special_handling_requirements(self, product_name: str) -> List[str]:
        """Get special handling requirements for product."""
        requirements = []
        product_lower = product_name.lower()
        
        if 'oil' in product_lower:
            requirements.extend(['temperature_controlled', 'liquid_handling'])
        if 'organic' in product_lower:
            requirements.append('organic_segregation')
        if 'fresh' in product_lower:
            requirements.append('perishable_handling')
        
        return requirements
    
    def _estimate_shipping_cost(self, transport_type: str, quantity: float, route_complexity: int) -> float:
        """Estimate shipping cost based on transport type and quantity."""
        base_costs = {
            'truck': 50,
            'ship': 200,
            'rail': 75,
            'multimodal': 150
        }
        
        base_cost = base_costs.get(transport_type, 100)
        quantity_factor = min(quantity / 10, 10)  # Economies of scale
        complexity_factor = route_complexity * 0.2
        
        return base_cost * quantity_factor * (1 + complexity_factor)
    
    def _analyze_routes(self, shipments: List[ShipmentInfo]) -> Dict[str, Any]:
        """Analyze route performance from shipments."""
        routes = {}
        for shipment in shipments:
            route = f"{shipment.origin_location} → {shipment.destination_location}"
            if route not in routes:
                routes[route] = {'count': 0, 'avg_cost': 0, 'total_cost': 0}
            
            routes[route]['count'] += 1
            routes[route]['total_cost'] += shipment.estimated_cost or 0
        
        for route in routes:
            count = routes[route]['count']
            routes[route]['avg_cost'] = routes[route]['total_cost'] / count if count > 0 else 0
        
        return routes
    
    def _determine_movement_type(self, batch_status: str) -> str:
        """Determine inventory movement type from batch status."""
        status_mapping = {
            'available': 'inbound',
            'reserved': 'outbound',
            'allocated': 'transfer',
            'processed': 'outbound'
        }
        return status_mapping.get(batch_status, 'adjustment')
    
    def _generate_logistics_insights(
        self, 
        analytics: LogisticsAnalytics, 
        deliveries: List[DeliveryInfo], 
        shipments: List[ShipmentInfo]
    ) -> List[str]:
        """Generate key insights from logistics data."""
        insights = []
        
        if analytics.on_time_delivery_rate < 80:
            insights.append(f"On-time delivery rate ({analytics.on_time_delivery_rate:.1f}%) below target - review carrier performance")
        
        if analytics.overdue_deliveries > 0:
            insights.append(f"{analytics.overdue_deliveries} deliveries are overdue - immediate attention required")
        
        if analytics.average_delivery_time_days > 7:
            insights.append(f"Average delivery time ({analytics.average_delivery_time_days:.1f} days) exceeds benchmark")
        
        # Carrier performance insights
        best_carrier = max(analytics.carrier_performance.items(), 
                          key=lambda x: x[1].get('on_time_rate', 0)) if analytics.carrier_performance else None
        if best_carrier:
            insights.append(f"Best performing carrier: {best_carrier[0]} ({best_carrier[1]['on_time_rate']:.1f}% on-time)")
        
        return insights
    
    def _generate_logistics_forecasting(
        self, 
        deliveries: List[DeliveryInfo], 
        shipments: List[ShipmentInfo]
    ) -> Dict[str, Any]:
        """Generate logistics forecasting data."""
        # Simplified forecasting based on historical trends
        recent_deliveries = len([d for d in deliveries if d.delivery_date >= date.today() - timedelta(days=30)])
        
        return {
            'monthly_delivery_forecast': recent_deliveries * 1.1,  # 10% growth assumption
            'capacity_utilization': min(recent_deliveries / 100 * 100, 100),  # Assume 100 delivery capacity
            'peak_season_adjustment': 1.2 if date.today().month in [11, 12] else 1.0
        }
    
    def _calculate_logistics_performance_score(self, analytics: LogisticsAnalytics) -> float:
        """Calculate overall logistics performance score."""
        # Weighted scoring
        on_time_score = min(analytics.on_time_delivery_rate, 100)
        efficiency_score = max(100 - analytics.average_delivery_time_days * 5, 0)
        
        # Penalty for overdue deliveries
        overdue_penalty = analytics.overdue_deliveries * 5
        
        overall_score = (on_time_score * 0.6 + efficiency_score * 0.4) - overdue_penalty
        return max(min(overall_score, 100), 0)
    
    def _generate_logistics_recommendations(self, analytics: LogisticsAnalytics) -> List[str]:
        """Generate actionable logistics recommendations."""
        recommendations = []
        
        if analytics.on_time_delivery_rate < 85:
            recommendations.append("Implement carrier performance monitoring and penalties for delays")
        
        if analytics.overdue_deliveries > 5:
            recommendations.append("Establish proactive delivery exception management process")
        
        if analytics.average_delivery_time_days > 5:
            recommendations.append("Optimize delivery routes and consider regional distribution centers")
        
        # Cost optimization
        total_cost = analytics.cost_analytics.get('total_estimated_cost', 0)
        if total_cost > 100000:  # Arbitrary threshold
            recommendations.append("Negotiate volume discounts with carriers for cost optimization")
        
        if not recommendations:
            recommendations.append("Maintain current logistics performance and explore optimization opportunities")
        
        return recommendations

# Convenience functions

def create_logistics_manager(db_connection) -> LogisticsManager:
    """Create logistics manager instance."""
    return LogisticsManager(db_connection)

def get_urgent_deliveries(db_connection, company_id: str) -> List[DeliveryInfo]:
    """Quick function to get urgent deliveries needing attention."""
    manager = LogisticsManager(db_connection)
    deliveries, _ = manager.get_deliveries(
        company_id=company_id,
        overdue_only=True
    )
    pending_confirmation, _ = manager.get_deliveries(
        company_id=company_id,
        pending_confirmation=True
    )
    return deliveries + pending_confirmation

def track_shipment(db_connection, po_number: str) -> Optional[ShipmentInfo]:
    """Quick function to track a specific shipment by PO number."""
    manager = LogisticsManager(db_connection)
    shipments, _ = manager.get_shipments(limit=100)
    
    for shipment in shipments:
        if po_number in shipment.shipment_reference:
            return shipment
    return None

"""
Certification Management Functions
Atomic, composable functions for AI assistant certification management scenarios.
"""
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import logging
from enum import Enum

from .secure_query_builder import (
    SecureQueryBuilder, QueryOperator, execute_secure_query,
    build_certification_query, build_batch_search_query, SecureQueryError
)
from .input_validator import (
    InputValidator, ValidationError, ValidationRule, ValidatorType,
    validate_certification_params, validate_batch_search_params,
    validate_purchase_order_params, validate_farm_location_params,
    validate_company_info_params
)
from .database_manager import SecureDatabaseManager, get_database_manager

logger = logging.getLogger(__name__)

class CertificationType(Enum):
    RSPO = "RSPO"
    MSPO = "MSPO"
    ORGANIC = "Organic"
    RAINFOREST_ALLIANCE = "Rainforest Alliance"
    FAIR_TRADE = "Fair Trade"

class ComplianceStatus(Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    FAILED = "failed"
    EXEMPT = "exempt"

class BatchStatus(Enum):
    AVAILABLE = "available"
    RESERVED = "reserved"
    ALLOCATED = "allocated"
    PROCESSED = "processed"

class OrderStatus(Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    FULFILLED = "fulfilled"
    CANCELLED = "cancelled"

@dataclass
class CertificationInfo:
    """Certificate information with expiry tracking."""
    id: str
    company_id: str
    company_name: str
    location_id: Optional[str]
    location_name: Optional[str]
    certification_type: str
    expiry_date: datetime
    issue_date: datetime
    issuing_authority: str
    compliance_status: str
    days_until_expiry: int
    needs_renewal: bool
    renewal_cost_estimate: Optional[str] = None
    renewal_contact: Optional[str] = None

@dataclass
class BatchInfo:
    """Inventory batch information."""
    batch_id: str
    company_id: str
    company_name: str
    product_id: str
    product_name: str
    product_type: str
    quantity: float
    status: str
    transparency_score: float
    created_at: datetime
    expiry_date: Optional[datetime]
    farm_location: Optional[str] = None
    certifications: List[str] = None

@dataclass
class PurchaseOrderInfo:
    """Purchase order information with buyer/seller details."""
    id: str
    po_number: str
    buyer_company_id: str
    buyer_company_name: str
    buyer_company_type: str
    seller_company_id: str
    seller_company_name: str
    seller_company_type: str
    product_id: str
    product_name: str
    quantity: float
    status: str
    created_at: datetime
    value_estimate: Optional[float] = None

@dataclass
class FarmLocation:
    """Farm location with GPS and certification data."""
    id: str
    name: str
    company_id: str
    company_name: str
    latitude: float
    longitude: float
    registration_number: str
    certifications: List[str]
    compliance_status: str
    farm_size_hectares: Optional[float] = None
    specialization: Optional[str] = None
    eudr_compliant: bool = False

@dataclass
class CompanyInfo:
    """Company information with statistics."""
    id: str
    name: str
    company_type: str
    location: str
    transparency_score: float
    total_batches: int
    active_orders: int
    certifications_count: int
    expiring_certificates: int
    compliance_score: float
    contact_email: Optional[str] = None
    created_at: Optional[datetime] = None

class CertificationManager:
    """Main class for certification management functions."""
    
    def __init__(self, db_connection=None, db_manager: SecureDatabaseManager = None):
        """Initialize with database connection or manager."""
        if db_manager:
            self.db_manager = db_manager
            self.db = None  # Use manager instead
        else:
            self.db = db_connection  # Backward compatibility
            self.db_manager = None
        self.validator = InputValidator()
    
    def get_certifications(
        self, 
        company_id: Optional[str] = None,
        certification_type: Optional[str] = None,
        expires_within_days: Optional[int] = 30,
        compliance_status: Optional[str] = None,
        location_id: Optional[str] = None
    ) -> Tuple[List[CertificationInfo], Dict[str, Any]]:
        """
        Get certificate expiry alerts, farm certifications, and compliance status.
        
        Args:
            company_id: Filter by specific company
            certification_type: Filter by certification type (RSPO, MSPO, etc.)
            expires_within_days: Show certificates expiring within N days (default 30)
            compliance_status: Filter by compliance status
            location_id: Filter by specific farm location
            
        Returns:
            Tuple of (certification list, metadata dict with counts and alerts)
        """
        try:
            # Validate input parameters
            params = {
                'company_id': company_id,
                'certification_type': certification_type,
                'expires_within_days': expires_within_days,
                'compliance_status': compliance_status,
                'location_id': location_id
            }
            
            # Remove None values for validation
            params = {k: v for k, v in params.items() if v is not None}
            
            try:
                validated_params = validate_certification_params(params)
                company_id = validated_params.get('company_id')
                certification_type = validated_params.get('certification_type')
                expires_within_days = validated_params.get('expires_within_days', 30)
                compliance_status = validated_params.get('compliance_status')
                location_id = validated_params.get('location_id')
            except ValidationError as e:
                logger.warning(f"Input validation failed: {str(e)}")
                return [], {'error': 'Invalid input parameters', 'validation_error': str(e)}
            # Use secure query builder to prevent SQL injection
            query, params = build_certification_query(
                company_id=company_id,
                certification_type=certification_type,
                expires_within_days=expires_within_days,
                compliance_status=compliance_status,
                location_id=location_id,
                limit=1000  # Safe limit
            )
            
            # Use secure database manager if available
            if self.db_manager:
                results = self.db_manager.execute_query(query, params, fetch_all=True)
            else:
                results = execute_secure_query(self.db, query, params)
            
            certifications = []
            expiring_count = 0
            expired_count = 0
            
            for row in results:
                days_until_expiry = row['days_until_expiry']
                needs_renewal = days_until_expiry <= 90  # 90-day renewal window
                
                if days_until_expiry <= 0:
                    expired_count += 1
                elif days_until_expiry <= (expires_within_days or 30):
                    expiring_count += 1
                
                # Get renewal information
                renewal_info = self._get_renewal_info(row['certification_type'])
                
                cert = CertificationInfo(
                    id=row['id'],
                    company_id=row['company_id'],
                    company_name=row['company_name'],
                    location_id=row['location_id'],
                    location_name=row['location_name'],
                    certification_type=row['certification_type'],
                    expiry_date=row['expiry_date'],
                    issue_date=row['issue_date'],
                    issuing_authority=row['issuing_authority'],
                    compliance_status=row['compliance_status'],
                    days_until_expiry=days_until_expiry,
                    needs_renewal=needs_renewal,
                    renewal_cost_estimate=renewal_info.get('cost'),
                    renewal_contact=renewal_info.get('contact')
                )
                certifications.append(cert)
            
            metadata = {
                'total_certificates': len(certifications),
                'expiring_soon': expiring_count,
                'expired': expired_count,
                'needs_attention': expiring_count + expired_count,
                'filter_applied': {
                    'company_id': company_id,
                    'certification_type': certification_type,
                    'expires_within_days': expires_within_days,
                    'compliance_status': compliance_status
                }
            }
            
            return certifications, metadata
            
        except (SecureQueryError, ValidationError, Exception) as e:
            logger.error(f"Error in get_certifications", exc_info=True)
            return [], {'error': 'Failed to retrieve certifications', 'total_certificates': 0}
    
    def search_batches(
        self,
        product_name: Optional[str] = None,
        product_type: Optional[str] = None,
        status: Optional[str] = None,
        company_id: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        min_quantity: Optional[float] = None,
        min_transparency_score: Optional[float] = None,
        certification_required: Optional[str] = None,
        limit: int = 100
    ) -> Tuple[List[BatchInfo], Dict[str, Any]]:
        """
        Find inventory by product, status, date range with advanced filtering.
        
        Args:
            product_name: Search by product name (partial match)
            product_type: Filter by product type (FFB, CPO, RBDPO, etc.)
            status: Filter by batch status
            company_id: Filter by company
            date_from: Start date for batch creation
            date_to: End date for batch creation
            min_quantity: Minimum quantity threshold
            min_transparency_score: Minimum transparency score
            certification_required: Require specific certification
            limit: Maximum results to return
            
        Returns:
            Tuple of (batch list, metadata dict with aggregations)
        """
        try:
            # Validate input parameters
            params = {
                'product_name': product_name,
                'product_type': product_type,
                'status': status,
                'company_id': company_id,
                'min_quantity': min_quantity,
                'min_transparency_score': min_transparency_score,
                'certification_required': certification_required,
                'limit': limit
            }
            
            # Remove None values for validation
            params = {k: v for k, v in params.items() if v is not None}
            
            try:
                validated_params = validate_batch_search_params(params)
                product_name = validated_params.get('product_name')
                product_type = validated_params.get('product_type')
                status = validated_params.get('status')
                company_id = validated_params.get('company_id')
                min_quantity = validated_params.get('min_quantity')
                min_transparency_score = validated_params.get('min_transparency_score')
                certification_required = validated_params.get('certification_required')
                limit = validated_params.get('limit', 100)
            except ValidationError as e:
                logger.warning(f"Input validation failed: {str(e)}")
                return [], {'error': 'Invalid input parameters', 'validation_error': str(e)}
            
            # Validate date parameters separately (not in schema yet)
            if date_from and not isinstance(date_from, datetime):
                logger.warning(f"Invalid date_from parameter: {date_from}")
                return [], {'error': 'Invalid date_from parameter'}
            
            if date_to and not isinstance(date_to, datetime):
                logger.warning(f"Invalid date_to parameter: {date_to}")
                return [], {'error': 'Invalid date_to parameter'}
            # Use secure query builder to prevent SQL injection
            builder = SecureQueryBuilder()
            builder.select([
                'b.batch_id', 'b.company_id', 'c.name as company_name',
                'b.product_id', 'p.name as product_name', 'p.product_type',
                'b.quantity', 'b.status', 'b.transparency_score',
                'b.created_at', 'b.expiry_date',
                'l.name as farm_location',
                'GROUP_CONCAT(DISTINCT l.certifications) as certifications'
            ], 'batches', 'b')
            
            builder.join('companies c', 'b.company_id = c.id')
            builder.join('products p', 'b.product_id = p.id')
            builder.join('locations l', 'c.id = l.company_id AND l.is_farm_location = 1', 'LEFT JOIN')
            
            if product_name:
                builder.where('p.name', QueryOperator.LIKE, product_name)
                
            if product_type:
                builder.where('p.product_type', QueryOperator.EQUALS, product_type)
                
            if status:
                builder.where('b.status', QueryOperator.EQUALS, status)
                
            if company_id:
                builder.where('b.company_id', QueryOperator.EQUALS, company_id)
                
            if date_from:
                builder.where('b.created_at', QueryOperator.GREATER_EQUAL, date_from)
                
            if date_to:
                builder.where('b.created_at', QueryOperator.LESS_EQUAL, date_to)
                
            if min_quantity:
                builder.where('b.quantity', QueryOperator.GREATER_EQUAL, min_quantity)
                
            if min_transparency_score:
                builder.where('b.transparency_score', QueryOperator.GREATER_EQUAL, min_transparency_score)
                
            if certification_required:
                builder.where('l.certifications', QueryOperator.LIKE, certification_required)
            
            builder.where_raw('1=1 GROUP BY b.batch_id', [])
            builder.order_by('b.transparency_score', 'DESC')
            builder.order_by('b.created_at', 'DESC')
            builder.limit(limit)
            
            query, params = builder.build()
            results = execute_secure_query(self.db, query, params)
            
            batches = []
            total_quantity = 0
            avg_transparency = 0
            
            for row in results:
                certifications = row['certifications'].split(',') if row['certifications'] else []
                
                batch = BatchInfo(
                    batch_id=row['batch_id'],
                    company_id=row['company_id'],
                    company_name=row['company_name'],
                    product_id=row['product_id'],
                    product_name=row['product_name'],
                    product_type=row['product_type'],
                    quantity=row['quantity'],
                    status=row['status'],
                    transparency_score=row['transparency_score'],
                    created_at=row['created_at'],
                    expiry_date=row['expiry_date'],
                    farm_location=row['farm_location'],
                    certifications=certifications
                )
                batches.append(batch)
                total_quantity += row['quantity']
                avg_transparency += row['transparency_score']
            
            if batches:
                avg_transparency = avg_transparency / len(batches)
            
            # Get summary statistics
            summary_query = """
                SELECT 
                    COUNT(*) as total_matching,
                    SUM(quantity) as total_quantity,
                    AVG(transparency_score) as avg_transparency,
                    p.product_type,
                    COUNT(*) as type_count
                FROM batches b
                JOIN products p ON b.product_id = p.id
                WHERE 1=1
            """
            
            if filters:
                summary_query += " AND " + " AND ".join(filters[:-1])  # Exclude limit
                
            summary_query += " GROUP BY p.product_type"
            
            cursor.execute(summary_query, params[:-1])  # Exclude limit param
            summary_results = cursor.fetchall()
            
            metadata = {
                'total_batches': len(batches),
                'total_quantity': total_quantity,
                'average_transparency_score': round(avg_transparency, 2),
                'product_type_breakdown': summary_results,
                'filters_applied': {
                    'product_name': product_name,
                    'product_type': product_type,
                    'status': status,
                    'date_range': [date_from, date_to] if date_from or date_to else None
                }
            }
            
            return batches, metadata
            
        except (SecureQueryError, ValidationError, Exception) as e:
            logger.error(f"Error in search_batches", exc_info=True)
            return [], {'error': 'Failed to search batches', 'total_batches': 0}
    
    def get_purchase_orders(
        self,
        company_id: Optional[str] = None,
        role_filter: Optional[str] = None,  # 'buyer', 'seller', or None for both
        status: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        product_type: Optional[str] = None,
        min_value: Optional[float] = None,
        limit: int = 50
    ) -> Tuple[List[PurchaseOrderInfo], Dict[str, Any]]:
        """
        Get recent purchase orders with buyer/seller role filtering.
        
        Args:
            company_id: Filter by specific company
            role_filter: Filter by role ('buyer', 'seller', or None for both)
            status: Filter by order status
            date_from: Start date for order creation
            date_to: End date for order creation
            product_type: Filter by product type
            min_value: Minimum order value
            limit: Maximum results to return
            
        Returns:
            Tuple of (purchase order list, metadata dict with analytics)
        """
        try:
            # Validate input parameters
            params = {
                'company_id': company_id,
                'role_filter': role_filter,
                'status': status,
                'product_type': product_type,
                'min_value': min_value,
                'limit': limit
            }
            
            # Remove None values for validation
            params = {k: v for k, v in params.items() if v is not None}
            
            try:
                validated_params = validate_purchase_order_params(params)
                company_id = validated_params.get('company_id')
                role_filter = validated_params.get('role_filter')
                status = validated_params.get('status')
                product_type = validated_params.get('product_type')
                min_value = validated_params.get('min_value')
                limit = validated_params.get('limit', 50)
            except ValidationError as e:
                logger.warning(f"Input validation failed: {str(e)}")
                return [], {'error': 'Invalid input parameters', 'validation_error': str(e)}
            
            # Validate date parameters separately
            if date_from and not isinstance(date_from, datetime):
                logger.warning(f"Invalid date_from parameter: {date_from}")
                return [], {'error': 'Invalid date_from parameter'}
            
            if date_to and not isinstance(date_to, datetime):
                logger.warning(f"Invalid date_to parameter: {date_to}")
                return [], {'error': 'Invalid date_to parameter'}
            # Use secure query builder to prevent SQL injection
            builder = SecureQueryBuilder()
            builder.select([
                'po.id', 'po.po_number',
                'po.buyer_company_id', 'bc.name as buyer_company_name', 'bc.company_type as buyer_company_type',
                'po.seller_company_id', 'sc.name as seller_company_name', 'sc.company_type as seller_company_type',
                'po.product_id', 'p.name as product_name', 'p.product_type',
                'po.quantity', 'po.status', 'po.created_at'
            ], 'purchase_orders', 'po')
            
            builder.join('companies bc', 'po.buyer_company_id = bc.id')
            builder.join('companies sc', 'po.seller_company_id = sc.id')
            builder.join('products p', 'po.product_id = p.id')
            
            if company_id and role_filter:
                if role_filter == 'buyer':
                    builder.where('po.buyer_company_id', QueryOperator.EQUALS, company_id)
                elif role_filter == 'seller':
                    builder.where('po.seller_company_id', QueryOperator.EQUALS, company_id)
            elif company_id:
                builder.where_raw('(po.buyer_company_id = %s OR po.seller_company_id = %s)', [company_id, company_id])
                
            if status:
                builder.where('po.status', QueryOperator.EQUALS, status)
                
            if date_from:
                builder.where('po.created_at', QueryOperator.GREATER_EQUAL, date_from)
                
            if date_to:
                builder.where('po.created_at', QueryOperator.LESS_EQUAL, date_to)
                
            if product_type:
                builder.where('p.product_type', QueryOperator.EQUALS, product_type)
            
            builder.order_by('po.created_at', 'DESC')
            builder.limit(limit)
            
            query, params = builder.build()
            results = execute_secure_query(self.db, query, params)
            
            purchase_orders = []
            total_volume = 0
            
            for row in results:
                # Estimate order value (simplified calculation)
                value_estimate = self._estimate_order_value(row['product_type'], row['quantity'])
                
                po = PurchaseOrderInfo(
                    id=row['id'],
                    po_number=row['po_number'],
                    buyer_company_id=row['buyer_company_id'],
                    buyer_company_name=row['buyer_company_name'],
                    buyer_company_type=row['buyer_company_type'],
                    seller_company_id=row['seller_company_id'],
                    seller_company_name=row['seller_company_name'],
                    seller_company_type=row['seller_company_type'],
                    product_id=row['product_id'],
                    product_name=row['product_name'],
                    quantity=row['quantity'],
                    status=row['status'],
                    created_at=row['created_at'],
                    value_estimate=value_estimate
                )
                purchase_orders.append(po)
                total_volume += row['quantity']
            
            # Get status distribution
            status_query = """
                SELECT status, COUNT(*) as count
                FROM purchase_orders po
                WHERE 1=1
            """
            if filters:
                status_query += " AND " + " AND ".join(filters[:-1])  # Exclude limit
            status_query += " GROUP BY status"
            
            cursor.execute(status_query, params[:-1])  # Exclude limit param
            status_distribution = {row['status']: row['count'] for row in cursor.fetchall()}
            
            metadata = {
                'total_orders': len(purchase_orders),
                'total_volume': total_volume,
                'status_distribution': status_distribution,
                'role_perspective': role_filter,
                'estimated_total_value': sum(po.value_estimate or 0 for po in purchase_orders),
                'filters_applied': {
                    'company_id': company_id,
                    'role_filter': role_filter,
                    'status': status,
                    'product_type': product_type
                }
            }
            
            return purchase_orders, metadata
            
        except (SecureQueryError, ValidationError, Exception) as e:
            logger.error(f"Error in get_purchase_orders", exc_info=True)
            return [], {'error': 'Failed to retrieve purchase orders', 'total_orders': 0}
    
    def get_farm_locations(
        self,
        company_id: Optional[str] = None,
        certification_type: Optional[str] = None,
        compliance_status: Optional[str] = None,
        within_radius_km: Optional[Tuple[float, float, float]] = None,  # (lat, lng, radius)
        eudr_compliant_only: bool = False,
        min_farm_size: Optional[float] = None
    ) -> Tuple[List[FarmLocation], Dict[str, Any]]:
        """
        Get farm data with GPS coordinates and certifications.
        
        Args:
            company_id: Filter by specific company
            certification_type: Filter by certification type
            compliance_status: Filter by compliance status
            within_radius_km: Tuple of (latitude, longitude, radius_km) for geographic filtering
            eudr_compliant_only: Show only EUDR compliant farms
            min_farm_size: Minimum farm size in hectares
            
        Returns:
            Tuple of (farm location list, metadata dict with geographic analytics)
        """
        try:
            # Validate input parameters
            params = {
                'company_id': company_id,
                'certification_type': certification_type,
                'compliance_status': compliance_status,
                'eudr_compliant_only': eudr_compliant_only,
                'min_farm_size': min_farm_size
            }
            
            # Remove None values for validation
            params = {k: v for k, v in params.items() if v is not None}
            
            try:
                validated_params = validate_farm_location_params(params)
                company_id = validated_params.get('company_id')
                certification_type = validated_params.get('certification_type')
                compliance_status = validated_params.get('compliance_status')
                eudr_compliant_only = validated_params.get('eudr_compliant_only', False)
                min_farm_size = validated_params.get('min_farm_size')
            except ValidationError as e:
                logger.warning(f"Input validation failed: {str(e)}")
                return [], {'error': 'Invalid input parameters', 'validation_error': str(e)}
            
            # Validate geographic radius separately
            if within_radius_km:
                try:
                    if (not isinstance(within_radius_km, (list, tuple)) or 
                        len(within_radius_km) != 3):
                        raise ValueError("within_radius_km must be a tuple of (lat, lng, radius)")
                    
                    lat, lng, radius = within_radius_km
                    
                    # Validate coordinates using input validator
                    coord_validator = ValidationRule('coordinates', ValidatorType.COORDINATES)
                    self.validator.validate_field('coordinates', [lat, lng], coord_validator)
                    
                    # Validate radius
                    if not isinstance(radius, (int, float)) or radius <= 0 or radius > 1000:
                        raise ValueError("Radius must be between 0 and 1000 km")
                        
                except (ValueError, ValidationError) as e:
                    logger.warning(f"Invalid geographic radius parameter: {str(e)}")
                    return [], {'error': 'Invalid geographic radius parameter'}
            # Use secure query builder to prevent SQL injection
            builder = SecureQueryBuilder()
            builder.select([
                'l.id', 'l.name', 'l.company_id', 'c.name as company_name',
                'l.latitude', 'l.longitude', 'l.registration_number',
                'l.certifications', 'l.compliance_status'
            ], 'locations', 'l')
            
            builder.join('companies c', 'l.company_id = c.id')
            builder.where('l.is_farm_location', QueryOperator.EQUALS, 1)
            builder.where('l.latitude', QueryOperator.IS_NOT_NULL)
            builder.where('l.longitude', QueryOperator.IS_NOT_NULL)
            
            if company_id:
                builder.where('l.company_id', QueryOperator.EQUALS, company_id)
                
            if certification_type:
                builder.where('l.certifications', QueryOperator.LIKE, certification_type)
                
            if compliance_status:
                builder.where('l.compliance_status', QueryOperator.EQUALS, compliance_status)
                
            if eudr_compliant_only:
                builder.where('l.compliance_status', QueryOperator.EQUALS, 'verified')
                builder.where_raw('l.latitude != 0 AND l.longitude != 0', [])
            
            # Geographic filtering using bounding box (safer than complex calculations)
            if within_radius_km:
                lat, lng, radius = within_radius_km
                if abs(lat) < 0.001:  # Prevent division by zero
                    lat = 0.001 if lat >= 0 else -0.001
                
                # Simplified bounding box calculation
                lat_offset = min(radius / 111.0, 1.0)  # Cap at 1 degree
                lng_offset = min(radius / (111.0 * abs(lat)), 1.0)  # Cap at 1 degree
                
                builder.where('l.latitude', QueryOperator.BETWEEN, [lat - lat_offset, lat + lat_offset])
                builder.where('l.longitude', QueryOperator.BETWEEN, [lng - lng_offset, lng + lng_offset])
            
            builder.order_by('l.name', 'ASC')
            
            query, params = builder.build()
            results = execute_secure_query(self.db, query, params)
            
            farm_locations = []
            certification_counts = {}
            
            for row in results:
                certifications = row['certifications'].split(',') if row['certifications'] else []
                
                # Count certifications
                for cert in certifications:
                    cert = cert.strip()
                    certification_counts[cert] = certification_counts.get(cert, 0) + 1
                
                # Determine EUDR compliance
                eudr_compliant = (
                    row['compliance_status'] == 'verified' and
                    row['latitude'] != 0 and row['longitude'] != 0
                )
                
                farm = FarmLocation(
                    id=row['id'],
                    name=row['name'],
                    company_id=row['company_id'],
                    company_name=row['company_name'],
                    latitude=round(row['latitude'], 6),  # Privacy rounding
                    longitude=round(row['longitude'], 6),
                    registration_number=row['registration_number'],
                    certifications=certifications,
                    compliance_status=row['compliance_status'],
                    eudr_compliant=eudr_compliant
                )
                farm_locations.append(farm)
            
            # Geographic analytics
            if farm_locations:
                lats = [f.latitude for f in farm_locations]
                lngs = [f.longitude for f in farm_locations]
                geographic_center = {
                    'center_latitude': sum(lats) / len(lats),
                    'center_longitude': sum(lngs) / len(lngs),
                    'latitude_range': [min(lats), max(lats)],
                    'longitude_range': [min(lngs), max(lngs)]
                }
            else:
                geographic_center = {}
            
            metadata = {
                'total_farms': len(farm_locations),
                'eudr_compliant_count': sum(1 for f in farm_locations if f.eudr_compliant),
                'certification_distribution': certification_counts,
                'compliance_distribution': {
                    status: sum(1 for f in farm_locations if f.compliance_status == status)
                    for status in ['pending', 'verified', 'failed', 'exempt']
                },
                'geographic_analytics': geographic_center,
                'filters_applied': {
                    'company_id': company_id,
                    'certification_type': certification_type,
                    'compliance_status': compliance_status,
                    'eudr_compliant_only': eudr_compliant_only
                }
            }
            
            return farm_locations, metadata
            
        except (SecureQueryError, ValidationError, Exception) as e:
            logger.error(f"Error in get_farm_locations", exc_info=True)
            return [], {'error': 'Failed to retrieve farm locations', 'total_farms': 0}
    
    def get_company_info(
        self,
        company_id: Optional[str] = None,
        company_type: Optional[str] = None,
        min_transparency_score: Optional[float] = None,
        include_statistics: bool = True,
        include_contact_info: bool = False
    ) -> Tuple[List[CompanyInfo], Dict[str, Any]]:
        """
        Get company details, statistics, and contact information.
        
        Args:
            company_id: Get info for specific company
            company_type: Filter by company type
            min_transparency_score: Minimum transparency score threshold
            include_statistics: Include operational statistics
            include_contact_info: Include contact information (if authorized)
            
        Returns:
            Tuple of (company info list, metadata dict with industry analytics)
        """
        try:
            # Validate input parameters
            params = {
                'company_id': company_id,
                'company_type': company_type,
                'min_transparency_score': min_transparency_score,
                'include_statistics': include_statistics,
                'include_contact_info': include_contact_info
            }
            
            # Remove None values for validation
            params = {k: v for k, v in params.items() if v is not None}
            
            try:
                validated_params = validate_company_info_params(params)
                company_id = validated_params.get('company_id')
                company_type = validated_params.get('company_type')
                min_transparency_score = validated_params.get('min_transparency_score')
                include_statistics = validated_params.get('include_statistics', True)
                include_contact_info = validated_params.get('include_contact_info', False)
            except ValidationError as e:
                logger.warning(f"Input validation failed: {str(e)}")
                return [], {'error': 'Invalid input parameters', 'validation_error': str(e)}
            # Use secure query builder to prevent SQL injection
            builder = SecureQueryBuilder()
            builder.select([
                'c.id', 'c.name', 'c.company_type', 'c.location', 
                'c.transparency_score', 'c.created_at'
            ], 'companies', 'c')
            
            if company_id:
                builder.where('c.id', QueryOperator.EQUALS, company_id)
                
            if company_type:
                builder.where('c.company_type', QueryOperator.EQUALS, company_type)
                
            if min_transparency_score:
                builder.where('c.transparency_score', QueryOperator.GREATER_EQUAL, min_transparency_score)
            
            builder.order_by('c.transparency_score', 'DESC')
            builder.order_by('c.name', 'ASC')
            
            query, params = builder.build()
            results = execute_secure_query(self.db, query, params)
            
            companies = []
            
            for row in results:
                company_stats = {}
                
                if include_statistics:
                    company_stats = self._get_company_statistics(row['id'])
                
                contact_email = None
                if include_contact_info:
                    contact_email = self._get_company_contact(row['id'])
                
                company = CompanyInfo(
                    id=row['id'],
                    name=row['name'],
                    company_type=row['company_type'],
                    location=row['location'],
                    transparency_score=row['transparency_score'],
                    total_batches=company_stats.get('total_batches', 0),
                    active_orders=company_stats.get('active_orders', 0),
                    certifications_count=company_stats.get('certifications_count', 0),
                    expiring_certificates=company_stats.get('expiring_certificates', 0),
                    compliance_score=company_stats.get('compliance_score', 0.0),
                    contact_email=contact_email,
                    created_at=row['created_at']
                )
                companies.append(company)
            
            # Industry analytics
            type_distribution = {}
            transparency_stats = []
            
            for company in companies:
                company_type = company.company_type
                type_distribution[company_type] = type_distribution.get(company_type, 0) + 1
                transparency_stats.append(company.transparency_score)
            
            metadata = {
                'total_companies': len(companies),
                'company_type_distribution': type_distribution,
                'transparency_analytics': {
                    'average_score': sum(transparency_stats) / len(transparency_stats) if transparency_stats else 0,
                    'median_score': sorted(transparency_stats)[len(transparency_stats)//2] if transparency_stats else 0,
                    'top_performers': len([s for s in transparency_stats if s >= 90]),
                    'needs_improvement': len([s for s in transparency_stats if s < 70])
                },
                'filters_applied': {
                    'company_id': company_id,
                    'company_type': company_type,
                    'min_transparency_score': min_transparency_score
                }
            }
            
            return companies, metadata
            
        except (SecureQueryError, ValidationError, Exception) as e:
            logger.error(f"Error in get_company_info", exc_info=True)
            return [], {'error': 'Failed to retrieve company info', 'total_companies': 0}
    
    # Helper methods
    
    def _get_renewal_info(self, certification_type: str) -> Dict[str, str]:
        """Get renewal contact and cost information for certification types."""
        renewal_data = {
            'RSPO': {
                'contact': 'certification@rspo.org',
                'cost': '$3,000-8,000',
                'lead_time': '90 days'
            },
            'MSPO': {
                'contact': 'MSPO board',
                'cost': 'RM5,000-15,000',
                'lead_time': '60 days'
            },
            'Organic': {
                'contact': 'certifying body',
                'cost': 'Varies by certifier',
                'lead_time': '120 days'
            },
            'Rainforest Alliance': {
                'contact': 'RA certification team',
                'cost': '$2,000-6,000',
                'lead_time': '90 days'
            }
        }
        return renewal_data.get(certification_type, {})
    
    def _estimate_order_value(self, product_type: str, quantity: float) -> float:
        """Estimate order value based on product type and quantity."""
        # Simplified pricing estimates (USD per MT)
        price_estimates = {
            'FFB': 250,
            'CPO': 800,
            'RBDPO': 850,
            'Palm Kernel': 400,
            'Olein': 900,
            'Stearin': 750
        }
        base_price = price_estimates.get(product_type, 600)
        return base_price * quantity
    
    def _get_company_statistics(self, company_id: str) -> Dict[str, Any]:
        """Get operational statistics for a company."""
        try:
            cursor = self.db.cursor(dictionary=True)
            
            # Get batch count
            cursor.execute(
                "SELECT COUNT(*) as count FROM batches WHERE company_id = %s",
                (company_id,)
            )
            total_batches = cursor.fetchone()['count']
            
            # Get active orders
            cursor.execute("""
                SELECT COUNT(*) as count FROM purchase_orders 
                WHERE (buyer_company_id = %s OR seller_company_id = %s) 
                AND status IN ('pending', 'confirmed')
            """, (company_id, company_id))
            active_orders = cursor.fetchone()['count']
            
            # Get certifications count
            cursor.execute("""
                SELECT COUNT(*) as count FROM documents d
                JOIN locations l ON d.company_id = l.company_id
                WHERE d.company_id = %s AND d.document_category = 'certificate'
            """, (company_id,))
            certifications_count = cursor.fetchone()['count']
            
            # Get expiring certificates
            cursor.execute("""
                SELECT COUNT(*) as count FROM documents 
                WHERE company_id = %s AND document_category = 'certificate'
                AND DATEDIFF(expiry_date, NOW()) <= 30
            """, (company_id,))
            expiring_certificates = cursor.fetchone()['count']
            
            # Calculate compliance score (simplified)
            compliance_score = max(0, 100 - (expiring_certificates * 10))
            
            return {
                'total_batches': total_batches,
                'active_orders': active_orders,
                'certifications_count': certifications_count,
                'expiring_certificates': expiring_certificates,
                'compliance_score': float(compliance_score)
            }
            
        except Exception as e:
            logger.error(f"Error getting company statistics: {str(e)}")
            return {}
    
    def _get_company_contact(self, company_id: str) -> Optional[str]:
        """Get company contact information if authorized."""
        try:
            cursor = self.db.cursor(dictionary=True)
            cursor.execute("""
                SELECT email FROM users 
                WHERE company_id = %s AND role IN ('admin', 'manager')
                LIMIT 1
            """, (company_id,))
            result = cursor.fetchone()
            return result['email'] if result else None
            
        except Exception as e:
            logger.error(f"Error getting company contact: {str(e)}")
            return None

# Convenience functions for AI assistant usage

def init_certification_manager(db_connection) -> CertificationManager:
    """Initialize certification manager with database connection."""
    return CertificationManager(db_connection)

def check_renewal_dates(
    db_connection, 
    days_ahead: int = 30
) -> Tuple[List[CertificationInfo], int]:
    """Quick function to check certificates expiring within specified days."""
    manager = CertificationManager(db_connection)
    certifications, metadata = manager.get_certifications(expires_within_days=days_ahead)
    return certifications, metadata.get('needs_attention', 0)

def find_available_inventory(
    db_connection,
    product_type: str,
    min_quantity: float = 0,
    certification_required: Optional[str] = None
) -> List[BatchInfo]:
    """Quick function to find available inventory matching criteria."""
    manager = CertificationManager(db_connection)
    batches, _ = manager.search_batches(
        product_type=product_type,
        status='available',
        min_quantity=min_quantity,
        certification_required=certification_required
    )
    return batches

def get_company_dashboard(
    db_connection,
    company_id: str
) -> Dict[str, Any]:
    """Get comprehensive dashboard data for a company."""
    manager = CertificationManager(db_connection)
    
    company_info, _ = manager.get_company_info(company_id=company_id, include_statistics=True)
    certifications, cert_meta = manager.get_certifications(company_id=company_id)
    farm_locations, farm_meta = manager.get_farm_locations(company_id=company_id)
    purchase_orders, po_meta = manager.get_purchase_orders(company_id=company_id, limit=10)
    
    return {
        'company': company_info[0] if company_info else None,
        'certifications': {
            'data': certifications,
            'summary': cert_meta
        },
        'farm_locations': {
            'data': farm_locations,
            'summary': farm_meta
        },
        'recent_orders': {
            'data': purchase_orders,
            'summary': po_meta
        }
    }

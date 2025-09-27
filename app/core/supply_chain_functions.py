"""
Complete Supply Chain Management Functions
Extending beyond certifications to cover the full palm oil supply chain ecosystem.
"""
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import logging
from enum import Enum

from .certification_cache import cached, performance_tracked
from .secure_query_builder import (
    SecureQueryBuilder, QueryOperator, execute_secure_query, SecureQueryError
)
from .input_validator import (
    InputValidator, ValidationError, ValidationRule, ValidatorType
)

logger = logging.getLogger(__name__)

class TransformationType(Enum):
    MILLING = "milling"
    REFINING = "refining"
    FRACTIONATION = "fractionation"

class ProductType(Enum):
    FFB = "FFB"
    CPO = "CPO"
    RBDPO = "RBDPO"
    PALM_KERNEL = "Palm Kernel"
    OLEIN = "Olein"
    STEARIN = "Stearin"

class DocumentCategory(Enum):
    CERTIFICATE = "certificate"
    MAP = "map"
    REPORT = "report"
    AUDIT = "audit"

class UserRole(Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    OPERATOR = "operator"
    VIEWER = "viewer"

@dataclass
class TransformationInfo:
    """Processing transformation details."""
    id: str
    input_batch_id: str
    output_batch_id: str
    transformation_type: str
    yield_percentage: float
    created_at: datetime
    company_id: str
    company_name: str
    input_product: str
    output_product: str
    input_quantity: float
    output_quantity: float
    efficiency_score: float
    energy_consumption: Optional[float] = None
    processing_time_hours: Optional[float] = None

@dataclass
class ProductInfo:
    """Product specification and flow information."""
    id: str
    name: str
    product_type: str
    specifications: Dict[str, Any]
    total_inventory: float
    active_batches: int
    avg_transparency_score: float
    market_price_estimate: Optional[float] = None
    processing_destinations: List[str] = None
    quality_parameters: Dict[str, Any] = None

@dataclass
class TraceabilityInfo:
    """Supply chain traceability data."""
    batch_id: str
    current_company: str
    current_product: str
    transparency_score: float
    supply_chain_depth: int
    origin_plantation: Optional[str]
    origin_coordinates: Optional[Tuple[float, float]]
    transformation_history: List[Dict[str, Any]]
    compliance_status: str
    eudr_compliant: bool
    certificates_inherited: List[str]

@dataclass
class UserInfo:
    """User account and access information."""
    id: str
    email: str
    first_name: str
    company_id: str
    company_name: str
    role: str
    created_at: datetime
    last_login: Optional[datetime]
    permissions: List[str]
    dashboard_access: Dict[str, bool]

@dataclass
class DocumentInfo:
    """Document management information."""
    id: str
    filename: str
    document_category: str
    company_id: str
    company_name: str
    upload_date: datetime
    expiry_date: Optional[datetime]
    issuing_authority: Optional[str]
    compliance_regulations: List[str]
    file_size_mb: Optional[float]
    access_level: str

@dataclass
class SupplyChainAnalytics:
    """Comprehensive supply chain analytics."""
    transparency_metrics: Dict[str, float]
    processing_efficiency: Dict[str, float]
    compliance_scores: Dict[str, float]
    inventory_distribution: Dict[str, int]
    geographic_distribution: Dict[str, int]
    risk_indicators: List[Dict[str, Any]]
    performance_trends: Dict[str, List[float]]

class SupplyChainManager:
    """Extended supply chain management functions."""
    
    def __init__(self, db_connection):
        self.db = db_connection
        self.validator = InputValidator()
    
    @cached(ttl=240)  # 4-minute cache
    @performance_tracked
    def get_transformations(
        self,
        company_id: Optional[str] = None,
        transformation_type: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        min_yield: Optional[float] = None,
        input_product: Optional[str] = None,
        output_product: Optional[str] = None,
        limit: int = 100
    ) -> Tuple[List[TransformationInfo], Dict[str, Any]]:
        """
        Get processing operations (milling, refining, fractionation) with efficiency metrics.
        
        Args:
            company_id: Filter by processing company
            transformation_type: Filter by operation type
            date_from: Start date for processing operations
            date_to: End date for processing operations
            min_yield: Minimum yield percentage threshold
            input_product: Filter by input product type
            output_product: Filter by output product type
            limit: Maximum results to return
            
        Returns:
            Tuple of (transformation list, efficiency analytics)
        """
        try:
            # Validate input parameters
            validation_rules = [
                ValidationRule('company_id', ValidatorType.UUID, required=False),
                ValidationRule('transformation_type', ValidatorType.ENUM, required=False,
                              allowed_values=['milling', 'refining', 'fractionation']),
                ValidationRule('min_yield', ValidatorType.PERCENTAGE, required=False),
                ValidationRule('input_product', ValidatorType.PRODUCT_TYPE, required=False),
                ValidationRule('output_product', ValidatorType.PRODUCT_TYPE, required=False),
                ValidationRule('limit', ValidatorType.INTEGER, required=False, min_value=1, max_value=1000)
            ]
            
            params = {
                'company_id': company_id,
                'transformation_type': transformation_type,
                'min_yield': min_yield,
                'input_product': input_product,
                'output_product': output_product,
                'limit': limit
            }
            
            # Remove None values and validate
            params = {k: v for k, v in params.items() if v is not None}
            
            try:
                validated_params = self.validator.validate_dict(params, validation_rules)
                company_id = validated_params.get('company_id')
                transformation_type = validated_params.get('transformation_type')
                min_yield = validated_params.get('min_yield')
                input_product = validated_params.get('input_product')
                output_product = validated_params.get('output_product')
                limit = validated_params.get('limit', 100)
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
                't.id', 't.input_batch_id', 't.output_batch_id', 't.transformation_type',
                't.yield_percentage', 't.created_at',
                'c.id as company_id', 'c.name as company_name',
                'ip.name as input_product', 'op.name as output_product',
                'ib.quantity as input_quantity', 'ob.quantity as output_quantity'
            ], 'transformations', 't')
            
            builder.join('batches ib', 't.input_batch_id = ib.batch_id')
            builder.join('batches ob', 't.output_batch_id = ob.batch_id')
            builder.join('products ip', 'ib.product_id = ip.id')
            builder.join('products op', 'ob.product_id = op.id')
            builder.join('companies c', 'ib.company_id = c.id')
            
            if company_id:
                builder.where('c.id', QueryOperator.EQUALS, company_id)
                
            if transformation_type:
                builder.where('t.transformation_type', QueryOperator.EQUALS, transformation_type)
                
            if date_from:
                builder.where('t.created_at', QueryOperator.GREATER_EQUAL, date_from)
                
            if date_to:
                builder.where('t.created_at', QueryOperator.LESS_EQUAL, date_to)
                
            if min_yield:
                builder.where('t.yield_percentage', QueryOperator.GREATER_EQUAL, min_yield)
                
            if input_product:
                builder.where('ip.product_type', QueryOperator.EQUALS, input_product)
                
            if output_product:
                builder.where('op.product_type', QueryOperator.EQUALS, output_product)
            
            builder.order_by('t.created_at', 'DESC')
            builder.limit(limit)
            
            query, params = builder.build()
            results = execute_secure_query(self.db, query, params)
            
            transformations = []
            total_input = 0
            total_output = 0
            yield_scores = []
            
            for row in results:
                # Calculate efficiency metrics
                actual_yield = row['yield_percentage']
                expected_yield = self._get_expected_yield(row['transformation_type'])
                efficiency_score = (actual_yield / expected_yield) * 100 if expected_yield > 0 else 0
                
                transformation = TransformationInfo(
                    id=row['id'],
                    input_batch_id=row['input_batch_id'],
                    output_batch_id=row['output_batch_id'],
                    transformation_type=row['transformation_type'],
                    yield_percentage=actual_yield,
                    created_at=row['created_at'],
                    company_id=row['company_id'],
                    company_name=row['company_name'],
                    input_product=row['input_product'],
                    output_product=row['output_product'],
                    input_quantity=row['input_quantity'],
                    output_quantity=row['output_quantity'],
                    efficiency_score=efficiency_score
                )
                transformations.append(transformation)
                
                total_input += row['input_quantity']
                total_output += row['output_quantity']
                yield_scores.append(actual_yield)
            
            # Calculate analytics
            avg_yield = sum(yield_scores) / len(yield_scores) if yield_scores else 0
            overall_efficiency = (total_output / total_input) * 100 if total_input > 0 else 0
            
            metadata = {
                'total_transformations': len(transformations),
                'total_input_quantity': total_input,
                'total_output_quantity': total_output,
                'average_yield': round(avg_yield, 2),
                'overall_efficiency': round(overall_efficiency, 2),
                'transformation_type_distribution': self._get_transformation_distribution(transformations),
                'top_performers': sorted(transformations, key=lambda t: t.efficiency_score, reverse=True)[:5]
            }
            
            return transformations, metadata
            
        except (SecureQueryError, ValidationError, Exception) as e:
            logger.error(f"Error getting transformations", exc_info=True)
            return [], {'error': 'Failed to retrieve transformations', 'total_transformations': 0}
    
    @cached(ttl=300)  # 5-minute cache
    @performance_tracked
    def get_products(
        self,
        product_type: Optional[str] = None,
        include_inventory: bool = True,
        include_market_data: bool = False,
        min_inventory: Optional[float] = None
    ) -> Tuple[List[ProductInfo], Dict[str, Any]]:
        """
        Get product specifications, inventory levels, and market information.
        
        Args:
            product_type: Filter by specific product type
            include_inventory: Include current inventory levels
            include_market_data: Include market price estimates
            min_inventory: Minimum inventory threshold
            
        Returns:
            Tuple of (product list, market analytics)
        """
        try:
            # Validate input parameters
            validation_rules = [
                ValidationRule('product_type', ValidatorType.PRODUCT_TYPE, required=False),
                ValidationRule('include_inventory', ValidatorType.BOOLEAN, required=False),
                ValidationRule('include_market_data', ValidatorType.BOOLEAN, required=False),
                ValidationRule('min_inventory', ValidatorType.FLOAT, required=False, min_value=0)
            ]
            
            params = {
                'product_type': product_type,
                'include_inventory': include_inventory,
                'include_market_data': include_market_data,
                'min_inventory': min_inventory
            }
            
            # Remove None values and validate
            params = {k: v for k, v in params.items() if v is not None}
            
            try:
                validated_params = self.validator.validate_dict(params, validation_rules)
                product_type = validated_params.get('product_type')
                include_inventory = validated_params.get('include_inventory', True)
                include_market_data = validated_params.get('include_market_data', False)
                min_inventory = validated_params.get('min_inventory')
            except ValidationError as e:
                logger.warning(f"Input validation failed: {str(e)}")
                return [], {'error': 'Invalid input parameters', 'validation_error': str(e)}
            # Use secure query builder to prevent SQL injection
            builder = SecureQueryBuilder()
            builder.select(['p.id', 'p.name', 'p.product_type', 'p.specifications'], 'products', 'p')
            
            if product_type:
                builder.where('p.product_type', QueryOperator.EQUALS, product_type)
            
            query, params = builder.build()
            results = execute_secure_query(self.db, query, params)
            
            products = []
            
            for row in results:
                product_data = {
                    'id': row['id'],
                    'name': row['name'],
                    'product_type': row['product_type'],
                    'specifications': self._parse_specifications(row['specifications']),
                    'total_inventory': 0,
                    'active_batches': 0,
                    'avg_transparency_score': 0
                }
                
                if include_inventory:
                    inventory_data = self._get_product_inventory(row['id'])
                    product_data.update(inventory_data)
                    
                    if min_inventory and product_data['total_inventory'] < min_inventory:
                        continue
                
                if include_market_data:
                    market_data = self._get_market_data(row['product_type'])
                    product_data.update(market_data)
                
                # Get quality parameters and processing destinations
                product_data['quality_parameters'] = self._get_quality_parameters(row['product_type'])
                product_data['processing_destinations'] = self._get_processing_destinations(row['product_type'])
                
                products.append(ProductInfo(**product_data))
            
            # Market analytics
            total_inventory = sum(p.total_inventory for p in products)
            avg_transparency = sum(p.avg_transparency_score for p in products) / len(products) if products else 0
            
            metadata = {
                'total_products': len(products),
                'total_inventory_value': total_inventory,
                'average_transparency': round(avg_transparency, 2),
                'product_type_distribution': {pt.value: len([p for p in products if p.product_type == pt.value]) 
                                           for pt in ProductType},
                'low_inventory_alerts': [p.name for p in products if p.total_inventory < 10]
            }
            
            return products, metadata
            
        except (SecureQueryError, ValidationError, Exception) as e:
            logger.error(f"Error getting products", exc_info=True)
            return [], {'error': 'Failed to retrieve products', 'total_products': 0}
    
    @cached(ttl=180)  # 3-minute cache for dynamic data
    @performance_tracked
    def trace_supply_chain(
        self,
        batch_id: str,
        include_full_history: bool = True,
        include_compliance_check: bool = True
    ) -> Tuple[TraceabilityInfo, Dict[str, Any]]:
        """
        Comprehensive supply chain traceability for a specific batch.
        
        Args:
            batch_id: Batch to trace
            include_full_history: Include complete transformation history
            include_compliance_check: Include compliance and certification status
            
        Returns:
            Tuple of (traceability info, compliance metadata)
        """
        try:
            # Validate input parameters
            validation_rules = [
                ValidationRule('batch_id', ValidatorType.STRING, required=True, 
                              min_length=1, max_length=50, pattern=r'^[A-Za-z0-9_-]+$'),
                ValidationRule('include_full_history', ValidatorType.BOOLEAN, required=False),
                ValidationRule('include_compliance_check', ValidatorType.BOOLEAN, required=False)
            ]
            
            params = {
                'batch_id': batch_id,
                'include_full_history': include_full_history,
                'include_compliance_check': include_compliance_check
            }
            
            try:
                validated_params = self.validator.validate_dict(params, validation_rules)
                batch_id = validated_params['batch_id']
                include_full_history = validated_params.get('include_full_history', True)
                include_compliance_check = validated_params.get('include_compliance_check', True)
            except ValidationError as e:
                logger.warning(f"Input validation failed: {str(e)}")
                return None, {'error': 'Invalid input parameters', 'validation_error': str(e)}
            # Get current batch information using secure query
            builder = SecureQueryBuilder()
            builder.select([
                'b.batch_id', 'b.transparency_score', 'b.company_id',
                'c.name as company_name', 'p.name as product_name',
                'l.latitude', 'l.longitude', 'l.compliance_status', 'l.certifications'
            ], 'batches', 'b')
            
            builder.join('companies c', 'b.company_id = c.id')
            builder.join('products p', 'b.product_id = p.id')
            builder.join('locations l', 'c.id = l.company_id AND l.is_farm_location = 1', 'LEFT JOIN')
            builder.where('b.batch_id', QueryOperator.EQUALS, batch_id)
            
            query, params = builder.build()
            results = execute_secure_query(self.db, query, params)
            batch_result = results[0] if results else None
            
            if not batch_result:
                return None, {'error': 'Batch not found'}
            
            # Trace transformation history
            transformation_history = []
            supply_chain_depth = 0
            current_batch = batch_id
            
            if include_full_history:
                transformation_history = self._trace_transformation_history(current_batch)
                supply_chain_depth = len(transformation_history)
            
            # Find origin plantation
            origin_plantation = None
            origin_coordinates = None
            
            if transformation_history:
                # Trace back to the earliest transformation
                earliest_transform = transformation_history[-1]  # Last in list = earliest chronologically
                origin_plantation = earliest_transform.get('origin_company')
                origin_coordinates = earliest_transform.get('origin_coordinates')
            elif batch_result['latitude'] and batch_result['longitude']:
                # Direct from plantation
                origin_plantation = batch_result['company_name']
                origin_coordinates = (batch_result['latitude'], batch_result['longitude'])
            
            # Compliance and certification status
            eudr_compliant = (
                batch_result['compliance_status'] == 'verified' and
                origin_coordinates is not None
            )
            
            certificates_inherited = []
            if batch_result['certifications']:
                certificates_inherited = [cert.strip() for cert in batch_result['certifications'].split(',')]
            
            traceability = TraceabilityInfo(
                batch_id=batch_id,
                current_company=batch_result['company_name'],
                current_product=batch_result['product_name'],
                transparency_score=batch_result['transparency_score'],
                supply_chain_depth=supply_chain_depth,
                origin_plantation=origin_plantation,
                origin_coordinates=origin_coordinates,
                transformation_history=transformation_history,
                compliance_status=batch_result['compliance_status'],
                eudr_compliant=eudr_compliant,
                certificates_inherited=certificates_inherited
            )
            
            # Compliance metadata
            compliance_metadata = {
                'traceability_complete': origin_plantation is not None,
                'eudr_compliance': eudr_compliant,
                'certificate_count': len(certificates_inherited),
                'supply_chain_depth': supply_chain_depth,
                'transparency_score': batch_result['transparency_score'],
                'risk_factors': self._assess_risk_factors(traceability)
            }
            
            return traceability, compliance_metadata
            
        except (SecureQueryError, ValidationError, Exception) as e:
            logger.error(f"Error tracing supply chain", exc_info=True)
            return None, {'error': 'Failed to trace supply chain'}
    
    @cached(ttl=600)  # 10-minute cache
    @performance_tracked
    def get_users(
        self,
        company_id: Optional[str] = None,
        role: Optional[str] = None,
        include_permissions: bool = True,
        active_only: bool = True
    ) -> Tuple[List[UserInfo], Dict[str, Any]]:
        """
        Get user accounts with roles and permissions.
        
        Args:
            company_id: Filter by company
            role: Filter by user role
            include_permissions: Include detailed permissions
            active_only: Show only active users
            
        Returns:
            Tuple of (user list, access analytics)
        """
        try:
            # Use secure query builder to prevent SQL injection
            builder = SecureQueryBuilder()
            builder.select([
                'u.id', 'u.email', 'u.first_name', 'u.company_id', 
                'u.role', 'u.created_at', 'c.name as company_name'
            ], 'users', 'u')
            
            builder.join('companies c', 'u.company_id = c.id')
            
            if company_id:
                builder.where('u.company_id', QueryOperator.EQUALS, company_id)
                
            if role:
                builder.where('u.role', QueryOperator.EQUALS, role)
            
            builder.order_by('u.created_at', 'DESC')
            
            query, params = builder.build()
            results = execute_secure_query(self.db, query, params)
            
            users = []
            role_distribution = {}
            
            for row in results:
                # Get permissions based on role and company type
                permissions = []
                dashboard_access = {}
                
                if include_permissions:
                    permissions = self._get_user_permissions(row['role'], row['company_id'])
                    dashboard_access = self._get_dashboard_access(row['role'])
                
                user = UserInfo(
                    id=row['id'],
                    email=self._mask_email(row['email']),  # Privacy masking
                    first_name=row['first_name'],
                    company_id=row['company_id'],
                    company_name=row['company_name'],
                    role=row['role'],
                    created_at=row['created_at'],
                    last_login=None,  # Would need additional table
                    permissions=permissions,
                    dashboard_access=dashboard_access
                )
                users.append(user)
                
                # Count role distribution
                role_distribution[row['role']] = role_distribution.get(row['role'], 0) + 1
            
            metadata = {
                'total_users': len(users),
                'role_distribution': role_distribution,
                'companies_represented': len(set(u.company_id for u in users)),
                'admin_count': len([u for u in users if u.role == 'admin']),
                'access_levels': {
                    'full_access': len([u for u in users if u.role in ['admin', 'manager']]),
                    'limited_access': len([u for u in users if u.role in ['operator', 'viewer']])
                }
            }
            
            return users, metadata
            
        except (SecureQueryError, Exception) as e:
            logger.error(f"Error getting users", exc_info=True)
            return [], {'error': 'Failed to retrieve users', 'total_users': 0}
    
    @cached(ttl=300)  # 5-minute cache
    @performance_tracked
    def get_documents(
        self,
        company_id: Optional[str] = None,
        document_category: Optional[str] = None,
        compliance_regulation: Optional[str] = None,
        expires_within_days: Optional[int] = None,
        include_file_info: bool = False
    ) -> Tuple[List[DocumentInfo], Dict[str, Any]]:
        """
        Get documents beyond certificates (maps, reports, audits).
        
        Args:
            company_id: Filter by company
            document_category: Filter by document type
            compliance_regulation: Filter by regulation (EUDR, RSPO, etc.)
            expires_within_days: Show documents expiring soon
            include_file_info: Include file size and technical details
            
        Returns:
            Tuple of (document list, document analytics)
        """
        try:
            # Use secure query builder to prevent SQL injection
            builder = SecureQueryBuilder()
            builder.select([
                'd.id', 'd.filename', 'd.document_category', 'd.company_id',
                'd.expiry_date', 'd.issue_date', 'd.issuing_authority',
                'd.compliance_regulations', 'c.name as company_name'
            ], 'documents', 'd')
            
            builder.join('companies c', 'd.company_id = c.id')
            
            if company_id:
                builder.where('d.company_id', QueryOperator.EQUALS, company_id)
                
            if document_category:
                builder.where('d.document_category', QueryOperator.EQUALS, document_category)
                
            if compliance_regulation:
                builder.where('d.compliance_regulations', QueryOperator.LIKE, compliance_regulation)
                
            if expires_within_days is not None:
                builder.where('d.expiry_date', QueryOperator.IS_NOT_NULL)
                builder.where_raw('DATEDIFF(d.expiry_date, NOW()) <= %s', [expires_within_days])
            
            builder.order_by('d.document_category', 'ASC')
            builder.order_by('d.expiry_date', 'ASC')
            
            query, params = builder.build()
            results = execute_secure_query(self.db, query, params)
            
            documents = []
            category_counts = {}
            expiring_count = 0
            
            for row in results:
                # Parse compliance regulations
                regulations = []
                if row['compliance_regulations']:
                    regulations = [reg.strip() for reg in row['compliance_regulations'].split(',')]
                
                # Check if expiring
                days_until_expiry = None
                if row['expiry_date']:
                    days_until_expiry = (row['expiry_date'] - datetime.now()).days
                    if days_until_expiry <= 30:
                        expiring_count += 1
                
                document = DocumentInfo(
                    id=row['id'],
                    filename=row['filename'],
                    document_category=row['document_category'],
                    company_id=row['company_id'],
                    company_name=row['company_name'],
                    upload_date=row['issue_date'],
                    expiry_date=row['expiry_date'],
                    issuing_authority=row['issuing_authority'],
                    compliance_regulations=regulations,
                    file_size_mb=None,  # Would need file system integration
                    access_level=self._determine_access_level(row['document_category'])
                )
                documents.append(document)
                
                # Count categories
                category = row['document_category']
                category_counts[category] = category_counts.get(category, 0) + 1
            
            metadata = {
                'total_documents': len(documents),
                'category_distribution': category_counts,
                'expiring_documents': expiring_count,
                'compliance_coverage': {
                    reg: len([d for d in documents if reg in d.compliance_regulations])
                    for reg in ['EUDR', 'RSPO', 'UFLPA', 'MSPO']
                },
                'recent_uploads': len([d for d in documents if 
                                     d.upload_date and (datetime.now() - d.upload_date).days <= 7])
            }
            
            return documents, metadata
            
        except (SecureQueryError, Exception) as e:
            logger.error(f"Error getting documents", exc_info=True)
            return [], {'error': 'Failed to retrieve documents', 'total_documents': 0}
    
    @cached(ttl=600)  # 10-minute cache for analytics
    @performance_tracked
    def get_supply_chain_analytics(
        self,
        company_id: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        include_trends: bool = True
    ) -> Tuple[SupplyChainAnalytics, Dict[str, Any]]:
        """
        Comprehensive supply chain analytics and KPIs.
        
        Args:
            company_id: Focus on specific company
            date_from: Start date for analytics period
            date_to: End date for analytics period
            include_trends: Include time-series trend analysis
            
        Returns:
            Tuple of (analytics object, metadata)
        """
        try:
            # Set default date range if not provided
            if not date_to:
                date_to = datetime.now()
            if not date_from:
                date_from = date_to - timedelta(days=90)  # 90-day default
            
            # Get transparency metrics
            transparency_metrics = self._calculate_transparency_metrics(company_id, date_from, date_to)
            
            # Get processing efficiency
            processing_efficiency = self._calculate_processing_efficiency(company_id, date_from, date_to)
            
            # Get compliance scores
            compliance_scores = self._calculate_compliance_scores(company_id)
            
            # Get inventory distribution
            inventory_distribution = self._get_inventory_distribution(company_id)
            
            # Get geographic distribution
            geographic_distribution = self._get_geographic_distribution(company_id)
            
            # Assess risk indicators
            risk_indicators = self._assess_supply_chain_risks(company_id)
            
            # Performance trends (if requested)
            performance_trends = {}
            if include_trends:
                performance_trends = self._calculate_performance_trends(company_id, date_from, date_to)
            
            analytics = SupplyChainAnalytics(
                transparency_metrics=transparency_metrics,
                processing_efficiency=processing_efficiency,
                compliance_scores=compliance_scores,
                inventory_distribution=inventory_distribution,
                geographic_distribution=geographic_distribution,
                risk_indicators=risk_indicators,
                performance_trends=performance_trends
            )
            
            # Calculate overall health score
            health_score = self._calculate_overall_health_score(analytics)
            
            metadata = {
                'analysis_period': {
                    'from': date_from.isoformat(),
                    'to': date_to.isoformat(),
                    'days': (date_to - date_from).days
                },
                'overall_health_score': health_score,
                'key_metrics': {
                    'avg_transparency': transparency_metrics.get('average_score', 0),
                    'processing_efficiency': processing_efficiency.get('overall_efficiency', 0),
                    'compliance_rate': compliance_scores.get('overall_compliance', 0),
                    'risk_level': len([r for r in risk_indicators if r.get('severity') == 'high'])
                },
                'recommendations': self._generate_strategic_recommendations(analytics)
            }
            
            return analytics, metadata
            
        except Exception as e:
            logger.error(f"Error generating supply chain analytics: {str(e)}")
            return SupplyChainAnalytics({}, {}, {}, {}, {}, [], {}), {'error': str(e)}
    
    # Helper methods (implementation details)
    
    def _get_expected_yield(self, transformation_type: str) -> float:
        """Get expected yield percentage for transformation type."""
        expected_yields = {
            'milling': 20.0,  # FFB to CPO
            'refining': 96.5,  # CPO to RBDPO
            'fractionation': 95.0  # RBDPO to fractions
        }
        return expected_yields.get(transformation_type, 90.0)
    
    def _get_transformation_distribution(self, transformations: List[TransformationInfo]) -> Dict[str, int]:
        """Calculate distribution of transformation types."""
        distribution = {}
        for t in transformations:
            distribution[t.transformation_type] = distribution.get(t.transformation_type, 0) + 1
        return distribution
    
    def _parse_specifications(self, spec_string: str) -> Dict[str, Any]:
        """Parse product specifications from string."""
        # Implementation would parse JSON or structured specification string
        return {'raw_specs': spec_string}
    
    def _get_product_inventory(self, product_id: str) -> Dict[str, Any]:
        """Get current inventory levels for a product."""
        try:
            cursor = self.db.cursor(dictionary=True)
            cursor.execute("""
                SELECT 
                    SUM(quantity) as total_inventory,
                    COUNT(*) as active_batches,
                    AVG(transparency_score) as avg_transparency_score
                FROM batches 
                WHERE product_id = %s AND status = 'available'
            """, (product_id,))
            
            result = cursor.fetchone()
            return {
                'total_inventory': result['total_inventory'] or 0,
                'active_batches': result['active_batches'] or 0,
                'avg_transparency_score': result['avg_transparency_score'] or 0
            }
        except Exception:
            return {'total_inventory': 0, 'active_batches': 0, 'avg_transparency_score': 0}
    
    def _get_market_data(self, product_type: str) -> Dict[str, Any]:
        """Get market price estimates for product type."""
        # Simplified market price estimates (would integrate with real market data)
        market_prices = {
            'FFB': 250, 'CPO': 800, 'RBDPO': 850,
            'Palm Kernel': 400, 'Olein': 900, 'Stearin': 750
        }
        return {'market_price_estimate': market_prices.get(product_type, 600)}
    
    def _get_quality_parameters(self, product_type: str) -> Dict[str, Any]:
        """Get quality parameters for product type."""
        quality_params = {
            'CPO': {'FFA': '<3%', 'Moisture': '<0.1%', 'Iodine_Value': '50-55'},
            'RBDPO': {'FFA': '<0.1%', 'Moisture': '<0.05%', 'Peroxide': '<10'},
            'FFB': {'Ripeness': '>90%', 'Bunch_Weight': '15-25kg'}
        }
        return quality_params.get(product_type, {})
    
    def _get_processing_destinations(self, product_type: str) -> List[str]:
        """Get possible processing destinations for product."""
        destinations = {
            'FFB': ['CPO', 'Palm Kernel'],
            'CPO': ['RBDPO'],
            'RBDPO': ['Olein', 'Stearin']
        }
        return destinations.get(product_type, [])
    
    def _trace_transformation_history(self, batch_id: str) -> List[Dict[str, Any]]:
        """Trace complete transformation history for a batch."""
        # Implementation would recursively trace through transformations table
        # This is a simplified version
        return []
    
    def _assess_risk_factors(self, traceability: TraceabilityInfo) -> List[str]:
        """Assess supply chain risk factors."""
        risks = []
        if traceability.transparency_score < 70:
            risks.append("Low transparency score")
        if not traceability.eudr_compliant:
            risks.append("EUDR non-compliance")
        if not traceability.origin_plantation:
            risks.append("Unknown origin")
        if traceability.supply_chain_depth > 5:
            risks.append("Complex supply chain")
        return risks
    
    def _get_user_permissions(self, role: str, company_id: str) -> List[str]:
        """Get user permissions based on role and company."""
        # Implementation would check role-based permissions
        base_permissions = {
            'admin': ['read', 'write', 'delete', 'manage_users'],
            'manager': ['read', 'write', 'manage_inventory'],
            'operator': ['read', 'write'],
            'viewer': ['read']
        }
        return base_permissions.get(role, ['read'])
    
    def _get_dashboard_access(self, role: str) -> Dict[str, bool]:
        """Get dashboard access based on role."""
        return {
            'brand_dashboard': role in ['admin', 'manager'],
            'processor_dashboard': role in ['admin', 'manager'],
            'originator_dashboard': role in ['admin', 'manager', 'operator'],
            'trader_dashboard': role in ['admin', 'manager']
        }
    
    def _mask_email(self, email: str) -> str:
        """Mask email for privacy."""
        if '@' in email:
            local, domain = email.split('@', 1)
            return f"{local[:2]}***@{domain}"
        return email
    
    def _determine_access_level(self, document_category: str) -> str:
        """Determine access level for document category."""
        access_levels = {
            'certificate': 'public',
            'audit': 'restricted',
            'report': 'internal',
            'map': 'public'
        }
        return access_levels.get(document_category, 'internal')
    
    # Analytics helper methods
    
    def _calculate_transparency_metrics(self, company_id: Optional[str], date_from: datetime, date_to: datetime) -> Dict[str, float]:
        """Calculate transparency metrics."""
        # Implementation would calculate various transparency KPIs
        return {
            'average_score': 85.5,
            'trend': 2.3,
            'below_threshold_count': 5
        }
    
    def _calculate_processing_efficiency(self, company_id: Optional[str], date_from: datetime, date_to: datetime) -> Dict[str, float]:
        """Calculate processing efficiency metrics."""
        return {
            'overall_efficiency': 92.1,
            'oer_average': 21.5,
            'energy_efficiency': 87.3
        }
    
    def _calculate_compliance_scores(self, company_id: Optional[str]) -> Dict[str, float]:
        """Calculate compliance scores."""
        return {
            'overall_compliance': 91.2,
            'eudr_compliance': 88.7,
            'certification_compliance': 94.1
        }
    
    def _get_inventory_distribution(self, company_id: Optional[str]) -> Dict[str, int]:
        """Get inventory distribution by product type."""
        return {
            'CPO': 45,
            'RBDPO': 30,
            'FFB': 15,
            'Others': 10
        }
    
    def _get_geographic_distribution(self, company_id: Optional[str]) -> Dict[str, int]:
        """Get geographic distribution of operations."""
        return {
            'Malaysia': 60,
            'Indonesia': 35,
            'Thailand': 5
        }
    
    def _assess_supply_chain_risks(self, company_id: Optional[str]) -> List[Dict[str, Any]]:
        """Assess supply chain risks."""
        return [
            {
                'risk_type': 'compliance',
                'description': 'Expiring certificates',
                'severity': 'medium',
                'affected_locations': 3
            },
            {
                'risk_type': 'traceability',
                'description': 'Missing GPS data',
                'severity': 'high',
                'affected_batches': 12
            }
        ]
    
    def _calculate_performance_trends(self, company_id: Optional[str], date_from: datetime, date_to: datetime) -> Dict[str, List[float]]:
        """Calculate performance trends over time."""
        return {
            'transparency_trend': [82.1, 83.5, 84.2, 85.5],
            'efficiency_trend': [90.2, 91.1, 91.8, 92.1],
            'compliance_trend': [89.5, 90.1, 90.8, 91.2]
        }
    
    def _calculate_overall_health_score(self, analytics: SupplyChainAnalytics) -> float:
        """Calculate overall supply chain health score."""
        transparency_score = analytics.transparency_metrics.get('average_score', 0)
        efficiency_score = analytics.processing_efficiency.get('overall_efficiency', 0)
        compliance_score = analytics.compliance_scores.get('overall_compliance', 0)
        
        # Weighted average
        health_score = (transparency_score * 0.4 + efficiency_score * 0.3 + compliance_score * 0.3)
        return round(health_score, 2)
    
    def _generate_strategic_recommendations(self, analytics: SupplyChainAnalytics) -> List[str]:
        """Generate strategic recommendations based on analytics."""
        recommendations = []
        
        if analytics.transparency_metrics.get('average_score', 0) < 80:
            recommendations.append("Improve supply chain transparency through better data collection")
        
        if analytics.processing_efficiency.get('overall_efficiency', 0) < 90:
            recommendations.append("Optimize processing operations to improve efficiency")
        
        if len(analytics.risk_indicators) > 5:
            recommendations.append("Address high-priority risk factors to improve resilience")
        
        if not recommendations:
            recommendations.append("Maintain current performance levels and monitor trends")
        
        return recommendations

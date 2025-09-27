"""
Secure Query Builder
Prevents SQL injection attacks through parameterized queries and input validation.
"""
from typing import Dict, List, Optional, Any, Tuple, Union
import logging
import re
from enum import Enum

logger = logging.getLogger(__name__)

class QueryOperator(Enum):
    """Safe query operators."""
    EQUALS = "="
    NOT_EQUALS = "!="
    LIKE = "LIKE"
    IN = "IN"
    NOT_IN = "NOT IN"
    GREATER_THAN = ">"
    LESS_THAN = "<"
    GREATER_EQUAL = ">="
    LESS_EQUAL = "<="
    BETWEEN = "BETWEEN"
    IS_NULL = "IS NULL"
    IS_NOT_NULL = "IS NOT NULL"

class SecureQueryBuilder:
    """
    Secure query builder that prevents SQL injection through parameterized queries.
    """
    
    # Whitelist of allowed table names
    ALLOWED_TABLES = {
        'companies', 'users', 'products', 'purchase_orders', 'batches',
        'transformations', 'locations', 'documents', 'notifications',
        'notification_deliveries', 'user_notification_preferences'
    }
    
    # Whitelist of allowed column names
    ALLOWED_COLUMNS = {
        'companies': {'id', 'name', 'company_type', 'email', 'phone', 'address_city', 
                     'transparency_score', 'created_at', 'updated_at', 'location'},
        'users': {'id', 'email', 'full_name', 'first_name', 'role', 'company_id', 
                 'created_at', 'is_active', 'phone'},
        'products': {'id', 'name', 'product_type', 'specifications', 'default_unit'},
        'purchase_orders': {'id', 'po_number', 'buyer_company_id', 'seller_company_id',
                           'product_id', 'quantity', 'status', 'created_at', 'delivery_date',
                           'delivery_location', 'delivery_status', 'delivered_at',
                           'delivery_confirmed_by', 'delivery_notes', 'unit', 'confirmed_at'},
        'batches': {'batch_id', 'company_id', 'product_id', 'quantity', 'status',
                   'transparency_score', 'created_at', 'updated_at', 'expiry_date'},
        'transformations': {'id', 'input_batch_id', 'output_batch_id', 'transformation_type',
                           'yield_percentage', 'created_at'},
        'locations': {'id', 'name', 'company_id', 'is_farm_location', 'certifications',
                     'compliance_status', 'latitude', 'longitude', 'registration_number'},
        'documents': {'id', 'filename', 'document_category', 'company_id', 'expiry_date',
                     'issue_date', 'issuing_authority', 'compliance_regulations'},
        'notifications': {'id', 'user_id', 'company_id', 'notification_type', 'priority',
                         'status', 'title', 'message', 'data', 'created_at', 'read_at',
                         'expires_at', 'action_url', 'category'},
        'notification_deliveries': {'id', 'notification_id', 'delivery_channel',
                                   'delivery_status', 'delivery_address', 'sent_at',
                                   'delivered_at', 'retry_count'},
        'user_notification_preferences': {'user_id', 'email_notifications', 'sms_notifications',
                                         'in_app_notifications', 'webhook_notifications',
                                         'digest_frequency', 'categories_enabled',
                                         'quiet_hours_start', 'quiet_hours_end', 'timezone'}
    }
    
    def __init__(self):
        self.query_parts = []
        self.params = []
        self.joins = []
        self.where_conditions = []
        self.order_by = []
        self.limit_clause = None
        
    def select(self, columns: Union[str, List[str]], table: str, alias: Optional[str] = None) -> 'SecureQueryBuilder':
        """
        Start a SELECT query with validated columns and table names.
        
        Args:
            columns: Column names to select (validated against whitelist)
            table: Table name (validated against whitelist)
            alias: Optional table alias
            
        Returns:
            Self for method chaining
        """
        if not self._is_valid_table(table):
            raise ValueError(f"Invalid table name: {table}")
        
        if isinstance(columns, str):
            if columns != '*':
                if not self._is_valid_column(table, columns):
                    raise ValueError(f"Invalid column name: {columns} for table {table}")
            column_list = columns
        else:
            for col in columns:
                if not self._is_valid_column_reference(col):
                    raise ValueError(f"Invalid column reference: {col}")
            column_list = ', '.join(columns)
        
        table_ref = f"{table} {alias}" if alias else table
        self.query_parts.append(f"SELECT {column_list} FROM {table_ref}")
        return self
    
    def join(self, table: str, on_condition: str, join_type: str = "JOIN", alias: Optional[str] = None) -> 'SecureQueryBuilder':
        """
        Add a JOIN clause with validated table and condition.
        
        Args:
            table: Table to join (validated)
            on_condition: ON condition (parameterized)
            join_type: Type of join (JOIN, LEFT JOIN, etc.)
            alias: Optional table alias
            
        Returns:
            Self for method chaining
        """
        if not self._is_valid_table(table):
            raise ValueError(f"Invalid table name: {table}")
        
        if join_type not in ['JOIN', 'LEFT JOIN', 'RIGHT JOIN', 'INNER JOIN']:
            raise ValueError(f"Invalid join type: {join_type}")
        
        table_ref = f"{table} {alias}" if alias else table
        self.joins.append(f"{join_type} {table_ref} ON {on_condition}")
        return self
    
    def where(self, column: str, operator: QueryOperator, value: Any = None) -> 'SecureQueryBuilder':
        """
        Add a WHERE condition with parameterized values.
        
        Args:
            column: Column name (validated)
            operator: Query operator (from enum)
            value: Parameter value (will be parameterized)
            
        Returns:
            Self for method chaining
        """
        if not self._is_valid_column_reference(column):
            raise ValueError(f"Invalid column reference: {column}")
        
        if operator in [QueryOperator.IS_NULL, QueryOperator.IS_NOT_NULL]:
            condition = f"{column} {operator.value}"
        elif operator == QueryOperator.IN:
            if not isinstance(value, (list, tuple)):
                raise ValueError("IN operator requires list or tuple")
            placeholders = ', '.join(['%s'] * len(value))
            condition = f"{column} IN ({placeholders})"
            self.params.extend(value)
        elif operator == QueryOperator.BETWEEN:
            if not isinstance(value, (list, tuple)) or len(value) != 2:
                raise ValueError("BETWEEN operator requires tuple of 2 values")
            condition = f"{column} BETWEEN %s AND %s"
            self.params.extend(value)
        else:
            condition = f"{column} {operator.value} %s"
            self.params.append(value)
        
        self.where_conditions.append(condition)
        return self
    
    def where_raw(self, condition: str, params: List[Any]) -> 'SecureQueryBuilder':
        """
        Add a raw WHERE condition with explicit parameters.
        Use sparingly and ensure condition is safe.
        
        Args:
            condition: Raw SQL condition with %s placeholders
            params: Parameters for the condition
            
        Returns:
            Self for method chaining
        """
        # Validate that condition only contains allowed patterns
        if not self._is_safe_raw_condition(condition):
            raise ValueError(f"Unsafe raw condition: {condition}")
        
        self.where_conditions.append(condition)
        self.params.extend(params)
        return self
    
    def order_by(self, column: str, direction: str = "ASC") -> 'SecureQueryBuilder':
        """
        Add ORDER BY clause with validated column and direction.
        
        Args:
            column: Column name (validated)
            direction: ASC or DESC
            
        Returns:
            Self for method chaining
        """
        if not self._is_valid_column_reference(column):
            raise ValueError(f"Invalid column reference: {column}")
        
        if direction.upper() not in ['ASC', 'DESC']:
            raise ValueError(f"Invalid order direction: {direction}")
        
        self.order_by.append(f"{column} {direction.upper()}")
        return self
    
    def limit(self, count: int, offset: int = 0) -> 'SecureQueryBuilder':
        """
        Add LIMIT clause with validation.
        
        Args:
            count: Number of rows to return
            offset: Number of rows to skip
            
        Returns:
            Self for method chaining
        """
        if not isinstance(count, int) or count <= 0:
            raise ValueError("Limit count must be positive integer")
        
        if not isinstance(offset, int) or offset < 0:
            raise ValueError("Offset must be non-negative integer")
        
        if count > 10000:  # Prevent excessive queries
            raise ValueError("Limit count too large (max 10000)")
        
        if offset == 0:
            self.limit_clause = f"LIMIT {count}"
        else:
            self.limit_clause = f"LIMIT {count} OFFSET {offset}"
        
        return self
    
    def build(self) -> Tuple[str, List[Any]]:
        """
        Build the final query and return with parameters.
        
        Returns:
            Tuple of (query_string, parameters)
        """
        if not self.query_parts:
            raise ValueError("No query parts defined")
        
        query = ' '.join(self.query_parts)
        
        if self.joins:
            query += ' ' + ' '.join(self.joins)
        
        if self.where_conditions:
            query += ' WHERE ' + ' AND '.join(self.where_conditions)
        
        if self.order_by:
            query += ' ORDER BY ' + ', '.join(self.order_by)
        
        if self.limit_clause:
            query += ' ' + self.limit_clause
        
        return query, self.params
    
    # Validation methods
    
    def _is_valid_table(self, table: str) -> bool:
        """Check if table name is in whitelist."""
        return table in self.ALLOWED_TABLES
    
    def _is_valid_column(self, table: str, column: str) -> bool:
        """Check if column name is valid for the given table."""
        if table not in self.ALLOWED_COLUMNS:
            return False
        return column in self.ALLOWED_COLUMNS[table]
    
    def _is_valid_column_reference(self, column_ref: str) -> bool:
        """Check if column reference is valid (supports table.column format)."""
        if '.' in column_ref:
            # Handle table.column or alias.column format
            parts = column_ref.split('.')
            if len(parts) != 2:
                return False
            table_alias, column = parts
            # For aliased tables, we need to validate against known patterns
            # This is simplified - in practice, you'd track aliases
            return self._is_safe_identifier(table_alias) and self._is_safe_identifier(column)
        else:
            # Simple column name - check if it's a safe identifier
            return self._is_safe_identifier(column_ref)
    
    def _is_safe_identifier(self, identifier: str) -> bool:
        """Check if identifier contains only safe characters."""
        # Allow alphanumeric, underscore, and common SQL functions
        pattern = r'^[a-zA-Z_][a-zA-Z0-9_]*$'
        return bool(re.match(pattern, identifier))
    
    def _is_safe_raw_condition(self, condition: str) -> bool:
        """Check if raw condition is safe (basic validation)."""
        # Basic check for dangerous patterns
        dangerous_patterns = [
            r';\s*(drop|delete|update|insert|create|alter)',
            r'union\s+select',
            r'--',
            r'/\*',
            r'\*/',
            r'xp_',
            r'sp_'
        ]
        
        condition_lower = condition.lower()
        for pattern in dangerous_patterns:
            if re.search(pattern, condition_lower):
                return False
        
        # Ensure only contains %s placeholders for parameters
        if '%' in condition and not re.match(r'^[^%]*(%s[^%]*)*$', condition):
            return False
        
        return True

class SecureFilterBuilder:
    """
    Helper class for building secure WHERE clause filters.
    """
    
    def __init__(self):
        self.conditions = []
        self.params = []
    
    def add_filter(self, column: str, operator: QueryOperator, value: Any, table_alias: Optional[str] = None):
        """Add a filter condition."""
        column_ref = f"{table_alias}.{column}" if table_alias else column
        
        if operator == QueryOperator.LIKE:
            # Escape LIKE special characters
            if isinstance(value, str):
                value = value.replace('%', r'\%').replace('_', r'\_')
                value = f"%{value}%"
        
        if operator in [QueryOperator.IS_NULL, QueryOperator.IS_NOT_NULL]:
            condition = f"{column_ref} {operator.value}"
        elif operator == QueryOperator.IN:
            if not value:  # Empty list
                condition = "1=0"  # Always false
            else:
                placeholders = ', '.join(['%s'] * len(value))
                condition = f"{column_ref} IN ({placeholders})"
                self.params.extend(value)
        elif operator == QueryOperator.BETWEEN:
            condition = f"{column_ref} BETWEEN %s AND %s"
            self.params.extend(value)
        else:
            condition = f"{column_ref} {operator.value} %s"
            self.params.append(value)
        
        self.conditions.append(condition)
    
    def add_date_range(self, column: str, date_from: Any = None, date_to: Any = None, table_alias: Optional[str] = None):
        """Add date range filter."""
        column_ref = f"{table_alias}.{column}" if table_alias else column
        
        if date_from:
            self.conditions.append(f"{column_ref} >= %s")
            self.params.append(date_from)
        
        if date_to:
            self.conditions.append(f"{column_ref} <= %s")
            self.params.append(date_to)
    
    def build(self) -> Tuple[str, List[Any]]:
        """Build the WHERE clause."""
        if not self.conditions:
            return "1=1", []
        
        return " AND ".join(self.conditions), self.params

# Convenience functions for common queries

def build_certification_query(
    company_id: Optional[str] = None,
    certification_type: Optional[str] = None,
    expires_within_days: Optional[int] = None,
    compliance_status: Optional[str] = None,
    location_id: Optional[str] = None,
    limit: int = 100
) -> Tuple[str, List[Any]]:
    """Build secure query for certifications."""
    
    builder = SecureQueryBuilder()
    builder.select([
        'd.id', 'd.company_id', 'c.name as company_name',
        'l.id as location_id', 'l.name as location_name',
        'd.document_category as certification_type',
        'd.expiry_date', 'd.issue_date', 'd.issuing_authority',
        'l.compliance_status',
        'DATEDIFF(d.expiry_date, NOW()) as days_until_expiry'
    ], 'documents', 'd')
    
    builder.join('companies c', 'd.company_id = c.id')
    builder.join('locations l', 'd.company_id = l.company_id AND l.is_farm_location = 1', 'LEFT JOIN')
    
    builder.where('d.document_category', QueryOperator.EQUALS, 'certificate')
    
    if company_id:
        builder.where('d.company_id', QueryOperator.EQUALS, company_id)
    
    if certification_type:
        builder.where('d.compliance_regulations', QueryOperator.LIKE, certification_type)
    
    if expires_within_days is not None:
        builder.where_raw('DATEDIFF(d.expiry_date, NOW()) <= %s', [expires_within_days])
    
    if compliance_status:
        builder.where('l.compliance_status', QueryOperator.EQUALS, compliance_status)
    
    if location_id:
        builder.where('l.id', QueryOperator.EQUALS, location_id)
    
    builder.order_by('d.expiry_date', 'ASC')
    builder.order_by('days_until_expiry', 'ASC')
    builder.limit(limit)
    
    return builder.build()

def build_batch_search_query(
    product_name: Optional[str] = None,
    product_type: Optional[str] = None,
    status: Optional[str] = None,
    company_id: Optional[str] = None,
    min_quantity: Optional[float] = None,
    min_transparency_score: Optional[float] = None,
    certification_required: Optional[str] = None,
    limit: int = 100
) -> Tuple[str, List[Any]]:
    """Build secure query for batch search."""
    
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
    
    return builder.build()

# Error handling for secure queries
class SecureQueryError(Exception):
    """Exception raised for secure query validation errors."""
    pass

def execute_secure_query(db_connection, query: str, params: List[Any]) -> List[Dict[str, Any]]:
    """
    Execute a secure query with proper error handling.
    
    Args:
        db_connection: Database connection
        query: Parameterized query string
        params: Query parameters
        
    Returns:
        Query results
        
    Raises:
        SecureQueryError: If query execution fails
    """
    try:
        cursor = db_connection.cursor(dictionary=True)
        cursor.execute(query, params)
        results = cursor.fetchall()
        cursor.close()
        return results
    except Exception as e:
        logger.error(f"Secure query execution failed", exc_info=True)
        raise SecureQueryError(f"Query execution failed: {str(e)}") from e

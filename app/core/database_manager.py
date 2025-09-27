"""
Database Connection Management System
Implements connection pooling, transaction management, and monitoring.
"""
from typing import Dict, List, Optional, Any, ContextManager
import logging
import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta
import mysql.connector
from mysql.connector import pooling, Error
import os
from enum import Enum

logger = logging.getLogger(__name__)

class ConnectionState(Enum):
    """Connection states for monitoring."""
    ACTIVE = "active"
    IDLE = "idle"
    CLOSED = "closed"
    ERROR = "error"

@dataclass
class DatabaseConfig:
    """Database configuration with security settings."""
    host: str
    database: str
    user: str
    password: str
    port: int = 3306
    charset: str = 'utf8mb4'
    autocommit: bool = False
    
    # Connection pool settings
    pool_name: str = 'supply_chain_pool'
    pool_size: int = 10
    max_overflow: int = 20
    pool_reset_session: bool = True
    
    # Security settings
    ssl_disabled: bool = False
    ssl_ca: Optional[str] = None
    ssl_cert: Optional[str] = None
    ssl_key: Optional[str] = None
    
    # Timeout settings
    connection_timeout: int = 30
    query_timeout: int = 300
    pool_timeout: int = 30
    
    # Retry settings
    max_retries: int = 3
    retry_delay: float = 1.0
    
    @classmethod
    def from_env(cls) -> 'DatabaseConfig':
        """Create config from environment variables."""
        return cls(
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', '3306')),
            database=os.getenv('DB_NAME', 'supply_chain'),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', ''),
            pool_size=int(os.getenv('DB_POOL_SIZE', '10')),
            max_overflow=int(os.getenv('DB_MAX_OVERFLOW', '20')),
            connection_timeout=int(os.getenv('DB_CONNECTION_TIMEOUT', '30')),
            query_timeout=int(os.getenv('DB_QUERY_TIMEOUT', '300')),
            ssl_disabled=os.getenv('DB_SSL_DISABLED', 'false').lower() == 'true',
            ssl_ca=os.getenv('DB_SSL_CA'),
            ssl_cert=os.getenv('DB_SSL_CERT'),
            ssl_key=os.getenv('DB_SSL_KEY')
        )

@dataclass
class ConnectionMetrics:
    """Connection pool metrics for monitoring."""
    pool_name: str
    pool_size: int
    active_connections: int
    idle_connections: int
    total_connections_created: int
    total_connections_closed: int
    total_queries_executed: int
    average_query_time: float
    error_count: int
    last_error: Optional[str]
    last_error_time: Optional[datetime]
    uptime_seconds: float

class SecureDatabaseManager:
    """
    Secure database connection manager with pooling and monitoring.
    """
    
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.pool = None
        self.metrics = ConnectionMetrics(
            pool_name=config.pool_name,
            pool_size=config.pool_size,
            active_connections=0,
            idle_connections=0,
            total_connections_created=0,
            total_connections_closed=0,
            total_queries_executed=0,
            average_query_time=0.0,
            error_count=0,
            last_error=None,
            last_error_time=None,
            uptime_seconds=0
        )
        self.start_time = datetime.now()
        self.query_times = []
        self.max_query_time_samples = 1000
        self._lock = threading.Lock()
        self._initialize_pool()
    
    def _initialize_pool(self):
        """Initialize the connection pool with security settings."""
        try:
            pool_config = {
                'pool_name': self.config.pool_name,
                'pool_size': self.config.pool_size,
                'pool_reset_session': self.config.pool_reset_session,
                'host': self.config.host,
                'port': self.config.port,
                'database': self.config.database,
                'user': self.config.user,
                'password': self.config.password,
                'charset': self.config.charset,
                'autocommit': self.config.autocommit,
                'connection_timeout': self.config.connection_timeout,
                'use_unicode': True,
                'sql_mode': 'STRICT_TRANS_TABLES,NO_ZERO_DATE,NO_ZERO_IN_DATE,ERROR_FOR_DIVISION_BY_ZERO',
            }
            
            # Add SSL configuration if provided
            if not self.config.ssl_disabled:
                ssl_config = {}
                if self.config.ssl_ca:
                    ssl_config['ssl_ca'] = self.config.ssl_ca
                if self.config.ssl_cert:
                    ssl_config['ssl_cert'] = self.config.ssl_cert
                if self.config.ssl_key:
                    ssl_config['ssl_key'] = self.config.ssl_key
                
                if ssl_config:
                    pool_config['ssl'] = ssl_config
                else:
                    pool_config['ssl_disabled'] = False
            else:
                pool_config['ssl_disabled'] = True
            
            self.pool = pooling.MySQLConnectionPool(**pool_config)
            logger.info(f"Database connection pool '{self.config.pool_name}' initialized successfully")
            
        except Error as e:
            logger.error(f"Failed to initialize database pool: {str(e)}")
            self._record_error(f"Pool initialization failed: {str(e)}")
            raise
    
    @contextmanager
    def get_connection(self) -> ContextManager:
        """
        Get a database connection from the pool with automatic cleanup.
        
        Yields:
            Database connection with automatic transaction management
        """
        connection = None
        start_time = time.time()
        
        try:
            # Get connection from pool with timeout
            connection = self._get_pooled_connection()
            
            with self._lock:
                self.metrics.active_connections += 1
                self.metrics.total_connections_created += 1
            
            # Ensure connection is healthy
            if not self._is_connection_healthy(connection):
                connection.close()
                connection = self._get_pooled_connection()
            
            yield connection
            
            # Commit transaction if autocommit is disabled
            if not self.config.autocommit and connection.is_connected():
                connection.commit()
                
        except Error as e:
            # Rollback on error
            if connection and connection.is_connected() and not self.config.autocommit:
                try:
                    connection.rollback()
                except Error:
                    pass  # Ignore rollback errors
            
            self._record_error(f"Database error: {str(e)}")
            logger.error(f"Database operation failed: {str(e)}")
            raise
            
        except Exception as e:
            # Handle non-database errors
            if connection and connection.is_connected() and not self.config.autocommit:
                try:
                    connection.rollback()
                except Error:
                    pass
            
            self._record_error(f"Unexpected error: {str(e)}")
            logger.error(f"Unexpected error in database operation: {str(e)}")
            raise
            
        finally:
            # Clean up connection
            if connection:
                try:
                    if connection.is_connected():
                        connection.close()
                except Error as e:
                    logger.warning(f"Error closing connection: {str(e)}")
                
                with self._lock:
                    self.metrics.active_connections = max(0, self.metrics.active_connections - 1)
                    self.metrics.total_connections_closed += 1
            
            # Record query time
            query_time = time.time() - start_time
            self._record_query_time(query_time)
    
    def _get_pooled_connection(self):
        """Get connection from pool with retry logic."""
        last_exception = None
        
        for attempt in range(self.config.max_retries):
            try:
                return self.pool.get_connection(timeout=self.config.pool_timeout)
            
            except Error as e:
                last_exception = e
                if attempt < self.config.max_retries - 1:
                    logger.warning(f"Connection attempt {attempt + 1} failed, retrying: {str(e)}")
                    time.sleep(self.config.retry_delay * (attempt + 1))
                else:
                    logger.error(f"All connection attempts failed: {str(e)}")
        
        raise last_exception
    
    def _is_connection_healthy(self, connection) -> bool:
        """Check if connection is healthy and responsive."""
        try:
            if not connection.is_connected():
                return False
            
            # Test with a simple query
            cursor = connection.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            cursor.close()
            
            return result is not None
            
        except Error:
            return False
    
    def execute_query(
        self, 
        query: str, 
        params: Optional[tuple] = None,
        fetch_one: bool = False,
        fetch_all: bool = True
    ) -> Any:
        """
        Execute a query safely with connection management.
        
        Args:
            query: SQL query to execute
            params: Query parameters
            fetch_one: Return single row
            fetch_all: Return all rows
            
        Returns:
            Query results
        """
        start_time = time.time()
        
        with self.get_connection() as connection:
            cursor = None
            try:
                cursor = connection.cursor(dictionary=True)
                
                # Set query timeout
                connection.cmd_query_timeout = self.config.query_timeout
                
                cursor.execute(query, params or ())
                
                with self._lock:
                    self.metrics.total_queries_executed += 1
                
                if fetch_one:
                    return cursor.fetchone()
                elif fetch_all:
                    return cursor.fetchall()
                else:
                    return cursor.rowcount
                    
            finally:
                if cursor:
                    cursor.close()
                
                query_time = time.time() - start_time
                self._record_query_time(query_time)
    
    def execute_transaction(self, operations: List[Dict[str, Any]]) -> bool:
        """
        Execute multiple operations in a transaction.
        
        Args:
            operations: List of {'query': str, 'params': tuple} operations
            
        Returns:
            True if all operations succeeded
        """
        with self.get_connection() as connection:
            cursor = None
            try:
                cursor = connection.cursor()
                
                # Explicitly begin transaction
                connection.start_transaction()
                
                for operation in operations:
                    query = operation['query']
                    params = operation.get('params', ())
                    cursor.execute(query, params)
                
                connection.commit()
                
                with self._lock:
                    self.metrics.total_queries_executed += len(operations)
                
                return True
                
            except Error as e:
                connection.rollback()
                self._record_error(f"Transaction failed: {str(e)}")
                logger.error(f"Transaction failed: {str(e)}")
                return False
                
            finally:
                if cursor:
                    cursor.close()
    
    def get_metrics(self) -> ConnectionMetrics:
        """Get current connection pool metrics."""
        with self._lock:
            # Update runtime metrics
            uptime = (datetime.now() - self.start_time).total_seconds()
            
            # Get current pool status
            try:
                pool_size = self.pool.pool_size if self.pool else 0
                # Note: actual active/idle counts would need pool introspection
                # This is simplified for the example
                active_connections = self.metrics.active_connections
                idle_connections = max(0, pool_size - active_connections)
                
                return ConnectionMetrics(
                    pool_name=self.metrics.pool_name,
                    pool_size=pool_size,
                    active_connections=active_connections,
                    idle_connections=idle_connections,
                    total_connections_created=self.metrics.total_connections_created,
                    total_connections_closed=self.metrics.total_connections_closed,
                    total_queries_executed=self.metrics.total_queries_executed,
                    average_query_time=self.metrics.average_query_time,
                    error_count=self.metrics.error_count,
                    last_error=self.metrics.last_error,
                    last_error_time=self.metrics.last_error_time,
                    uptime_seconds=uptime
                )
                
            except Exception as e:
                logger.warning(f"Error getting pool metrics: {str(e)}")
                return self.metrics
    
    def health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check."""
        health_status = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'issues': []
        }
        
        try:
            # Test connection
            with self.get_connection() as connection:
                cursor = connection.cursor()
                cursor.execute("SELECT 1 as health_check")
                result = cursor.fetchone()
                cursor.close()
                
                if not result:
                    health_status['status'] = 'unhealthy'
                    health_status['issues'].append('Database query test failed')
            
            # Check metrics
            metrics = self.get_metrics()
            
            # Check error rate
            if metrics.error_count > 0:
                error_rate = metrics.error_count / max(metrics.total_queries_executed, 1)
                if error_rate > 0.05:  # 5% error rate threshold
                    health_status['status'] = 'degraded'
                    health_status['issues'].append(f'High error rate: {error_rate:.2%}')
            
            # Check average query time
            if metrics.average_query_time > 5.0:  # 5 second threshold
                health_status['status'] = 'degraded'
                health_status['issues'].append(f'High average query time: {metrics.average_query_time:.2f}s')
            
            # Check pool utilization
            if metrics.pool_size > 0:
                utilization = metrics.active_connections / metrics.pool_size
                if utilization > 0.9:  # 90% utilization threshold
                    health_status['status'] = 'degraded'
                    health_status['issues'].append(f'High pool utilization: {utilization:.1%}')
            
            health_status['metrics'] = metrics.__dict__
            
        except Exception as e:
            health_status['status'] = 'unhealthy'
            health_status['issues'].append(f'Health check failed: {str(e)}')
            logger.error(f"Database health check failed: {str(e)}")
        
        return health_status
    
    def _record_error(self, error_message: str):
        """Record error for metrics."""
        with self._lock:
            self.metrics.error_count += 1
            self.metrics.last_error = error_message
            self.metrics.last_error_time = datetime.now()
    
    def _record_query_time(self, query_time: float):
        """Record query execution time for metrics."""
        with self._lock:
            self.query_times.append(query_time)
            
            # Keep only recent samples
            if len(self.query_times) > self.max_query_time_samples:
                self.query_times = self.query_times[-self.max_query_time_samples:]
            
            # Update average
            if self.query_times:
                self.metrics.average_query_time = sum(self.query_times) / len(self.query_times)
    
    def close_pool(self):
        """Close the connection pool and cleanup resources."""
        try:
            if self.pool:
                # Note: mysql.connector.pooling doesn't have a direct close method
                # In practice, you'd implement proper cleanup based on your pool implementation
                logger.info(f"Connection pool '{self.config.pool_name}' closed")
                self.pool = None
                
        except Exception as e:
            logger.error(f"Error closing connection pool: {str(e)}")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close_pool()

# Connection factory and management

_db_manager_instance = None
_db_manager_lock = threading.Lock()

def get_database_manager(config: Optional[DatabaseConfig] = None) -> SecureDatabaseManager:
    """
    Get database manager singleton instance.
    
    Args:
        config: Database configuration (only used for first initialization)
        
    Returns:
        Database manager instance
    """
    global _db_manager_instance
    
    with _db_manager_lock:
        if _db_manager_instance is None:
            if config is None:
                config = DatabaseConfig.from_env()
            _db_manager_instance = SecureDatabaseManager(config)
        
        return _db_manager_instance

def close_database_manager():
    """Close the global database manager instance."""
    global _db_manager_instance
    
    with _db_manager_lock:
        if _db_manager_instance:
            _db_manager_instance.close_pool()
            _db_manager_instance = None

# Convenience functions for backward compatibility

def get_secure_connection():
    """Get a secure database connection (backward compatibility)."""
    manager = get_database_manager()
    return manager.get_connection()

def execute_secure_query(query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
    """Execute a secure query (backward compatibility)."""
    manager = get_database_manager()
    return manager.execute_query(query, params, fetch_all=True)

# Database migration and schema management

class DatabaseMigrator:
    """Handle database migrations and schema management."""
    
    def __init__(self, db_manager: SecureDatabaseManager):
        self.db_manager = db_manager
    
    def create_migration_table(self):
        """Create migrations tracking table."""
        query = """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version VARCHAR(255) PRIMARY KEY,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            description TEXT,
            checksum VARCHAR(64)
        ) ENGINE=InnoDB
        """
        
        self.db_manager.execute_query(query, fetch_all=False)
    
    def apply_migration(self, version: str, description: str, sql: str) -> bool:
        """Apply a database migration."""
        import hashlib
        
        try:
            # Check if migration already applied
            check_query = "SELECT version FROM schema_migrations WHERE version = %s"
            result = self.db_manager.execute_query(check_query, (version,), fetch_one=True)
            
            if result:
                logger.info(f"Migration {version} already applied")
                return True
            
            # Calculate checksum
            checksum = hashlib.sha256(sql.encode()).hexdigest()
            
            # Apply migration in transaction
            operations = [
                {'query': sql},
                {
                    'query': 'INSERT INTO schema_migrations (version, description, checksum) VALUES (%s, %s, %s)',
                    'params': (version, description, checksum)
                }
            ]
            
            success = self.db_manager.execute_transaction(operations)
            
            if success:
                logger.info(f"Migration {version} applied successfully")
            else:
                logger.error(f"Migration {version} failed")
            
            return success
            
        except Exception as e:
            logger.error(f"Error applying migration {version}: {str(e)}")
            return False

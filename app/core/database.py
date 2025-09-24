"""
Database configuration and session management with performance optimization.
"""
from sqlalchemy import create_engine, event, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool, QueuePool
from sqlalchemy.engine import Engine
import time
import logging

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Database performance configuration
DATABASE_CONFIG = {
    "pool_size": settings.database_pool_size,  # Number of connections to maintain in pool
    "max_overflow": settings.database_max_overflow,  # Additional connections beyond pool_size
    "pool_timeout": settings.database_pool_timeout,  # Seconds to wait for connection
    "pool_recycle": 3600,  # Recycle connections after 1 hour
    "pool_pre_ping": True,  # Validate connections before use
    "echo": settings.debug,  # Log SQL queries in debug mode
    "echo_pool": settings.debug,  # Log connection pool events
}

# Create database engine with performance optimization
connect_args = {}
engine_kwargs = DATABASE_CONFIG.copy()

if "sqlite" in settings.database_url:
    # SQLite-specific configuration
    connect_args = {"check_same_thread": False}
    engine_kwargs = {
        "poolclass": StaticPool,
        "echo": settings.debug,
        "echo_pool": settings.debug,
    }
else:
    # PostgreSQL-specific configuration (including Neon)
    # Use SSL only for production/remote databases, disable for local development
    if "localhost" in settings.database_url or "127.0.0.1" in settings.database_url:
        connect_args = {
            "sslmode": "disable",
            "connect_timeout": 10,
        }
    else:
        connect_args = {
            "sslmode": "require",
            "connect_timeout": 10,
        }
    engine_kwargs.update({
        "poolclass": QueuePool,
        "pool_pre_ping": True,  # Validate connections before use
        "pool_recycle": 3600,   # Recycle connections after 1 hour
    })
    
    # Neon-specific optimizations
    if "neon.tech" in settings.database_url:
        connect_args.update({
            "channel_binding": "require",
        })
        # Reduce pool size for Neon's connection limits
        engine_kwargs.update({
            "pool_size": min(settings.database_pool_size, 5),
            "max_overflow": min(settings.database_max_overflow, 10),
        })
        logger.info("Neon database pool configuration applied")

engine = create_engine(
    settings.database_url,
    connect_args=connect_args,
    **engine_kwargs
)

# Database performance monitoring
@event.listens_for(Engine, "before_cursor_execute")
def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """Log slow queries for performance monitoring."""
    context._query_start_time = time.time()


@event.listens_for(Engine, "after_cursor_execute")
def receive_after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """Log query execution time."""
    total = time.time() - context._query_start_time

    # Log slow queries (> 1 second)
    if total > 1.0:
        logger.warning(
            "Slow query detected",
            duration=total,
            statement=statement[:200] + "..." if len(statement) > 200 else statement
        )
    elif settings.debug and total > 0.1:
        # Log moderately slow queries in debug mode
        logger.debug(
            "Query executed",
            duration=total,
            statement=statement[:100] + "..." if len(statement) > 100 else statement
        )


# SQLite performance optimization
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Optimize SQLite performance with pragmas."""
    if "sqlite" in settings.database_url:
        cursor = dbapi_connection.cursor()
        # Enable WAL mode for better concurrency
        cursor.execute("PRAGMA journal_mode=WAL")
        # Increase cache size (in KB)
        cursor.execute("PRAGMA cache_size=10000")
        # Enable foreign key constraints
        cursor.execute("PRAGMA foreign_keys=ON")
        # Optimize synchronous mode
        cursor.execute("PRAGMA synchronous=NORMAL")
        # Set temp store to memory
        cursor.execute("PRAGMA temp_store=MEMORY")
        cursor.close()


# Create session factory with optimized configuration
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False  # Keep objects accessible after commit
)

# Create declarative base for models
Base = declarative_base()


def get_db():
    """
    Dependency to get database session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def init_db():
    """
    Initialize database tables.
    """
    try:
        # Import all models to ensure they are registered
        from app.models import company, user, product, purchase_order, audit_event

        # Create all tables
        Base.metadata.create_all(bind=engine)

    except ImportError as e:
        # For now, just create the base tables that exist
        Base.metadata.create_all(bind=engine)

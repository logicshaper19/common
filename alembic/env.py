from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
import os
import sys

# Add your project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import your database models here
# from your_app.models import Base  # Import your SQLAlchemy Base

# This is the Alembic Config object
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set up database URL from environment
def get_database_url():
    # Use environment-specific database URL
    env = os.getenv('ENVIRONMENT', 'development')
    
    database_urls = {
        'production': os.getenv('PROD_DATABASE_URL', 'postgresql://elisha@localhost:5432/common_db'),
        'development': os.getenv('DEV_DATABASE_URL', 'postgresql://elisha@localhost:5432/common_dev'),
        'testing': os.getenv('TEST_DATABASE_URL', 'postgresql://elisha@localhost:5432/common_test')
    }
    
    return database_urls.get(env, database_urls['development'])

# Set the database URL
config.set_main_option('sqlalchemy.url', get_database_url())

# Add your model's MetaData object here for 'autogenerate' support
target_metadata = None  # Replace with your Base.metadata if you have SQLAlchemy models


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

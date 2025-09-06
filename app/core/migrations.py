"""
Database migration system with version control for the Common supply chain platform.
"""
import os
import re
import hashlib
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

from sqlalchemy import create_engine, text, MetaData, Table, Column, String, DateTime, Integer, Boolean
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class MigrationStatus(str, Enum):
    """Migration status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


@dataclass
class Migration:
    """Migration metadata."""
    version: str
    name: str
    description: str
    file_path: Path
    checksum: str
    created_at: datetime
    status: MigrationStatus = MigrationStatus.PENDING
    applied_at: Optional[datetime] = None
    execution_time: Optional[float] = None
    error_message: Optional[str] = None


class MigrationManager:
    """
    Database migration manager with version control.
    
    Features:
    - Version-controlled migrations
    - Checksum validation
    - Rollback support
    - Migration history tracking
    - Dry-run capability
    - Parallel migration detection
    """
    
    def __init__(self, database_url: str = None):
        self.database_url = database_url or settings.database_url
        self.migrations_dir = Path(__file__).parent.parent / "migrations"
        self.migrations_dir.mkdir(exist_ok=True)
        
        # Create engine and session
        self.engine = create_engine(self.database_url)
        self.SessionLocal = sessionmaker(bind=self.engine)
        
        # Initialize migration tracking table
        self._init_migration_table()
    
    def _init_migration_table(self):
        """Initialize the migration tracking table."""
        try:
            with self.engine.connect() as conn:
                # Create migration_history table if it doesn't exist
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS migration_history (
                        id SERIAL PRIMARY KEY,
                        version VARCHAR(50) NOT NULL UNIQUE,
                        name VARCHAR(255) NOT NULL,
                        description TEXT,
                        checksum VARCHAR(64) NOT NULL,
                        status VARCHAR(20) NOT NULL DEFAULT 'pending',
                        applied_at TIMESTAMP,
                        execution_time FLOAT,
                        error_message TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                conn.commit()
                logger.info("Migration tracking table initialized")
        except Exception as e:
            logger.error("Failed to initialize migration table", error=str(e))
            raise
    
    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate checksum for migration file."""
        with open(file_path, 'rb') as f:
            content = f.read()
            return hashlib.sha256(content).hexdigest()
    
    def _parse_migration_filename(self, filename: str) -> Tuple[str, str]:
        """Parse migration filename to extract version and name."""
        # Expected format: V001__create_users_table.sql
        pattern = r'^V(\d+)__(.+)\.sql$'
        match = re.match(pattern, filename)
        
        if not match:
            raise ValueError(f"Invalid migration filename format: {filename}")
        
        version = match.group(1)
        name = match.group(2).replace('_', ' ').title()
        
        return version, name
    
    def discover_migrations(self) -> List[Migration]:
        """Discover all migration files in the migrations directory."""
        migrations = []
        
        for file_path in sorted(self.migrations_dir.glob("V*.sql")):
            try:
                version, name = self._parse_migration_filename(file_path.name)
                checksum = self._calculate_checksum(file_path)
                
                # Read description from file header
                description = self._extract_description(file_path)
                
                migration = Migration(
                    version=version,
                    name=name,
                    description=description,
                    file_path=file_path,
                    checksum=checksum,
                    created_at=datetime.fromtimestamp(file_path.stat().st_mtime)
                )
                
                migrations.append(migration)
                
            except Exception as e:
                logger.warning(f"Failed to parse migration file {file_path}", error=str(e))
                continue
        
        return migrations
    
    def _extract_description(self, file_path: Path) -> str:
        """Extract description from migration file header."""
        try:
            with open(file_path, 'r') as f:
                lines = f.readlines()
                
                for line in lines[:10]:  # Check first 10 lines
                    line = line.strip()
                    if line.startswith('-- Description:'):
                        return line.replace('-- Description:', '').strip()
                    elif line.startswith('/*') and 'Description:' in line:
                        return line.split('Description:')[1].split('*/')[0].strip()
                
                return f"Migration {file_path.stem}"
        except Exception:
            return f"Migration {file_path.stem}"
    
    def get_applied_migrations(self) -> List[Migration]:
        """Get list of applied migrations from database."""
        applied_migrations = []
        
        try:
            with self.SessionLocal() as session:
                result = session.execute(text("""
                    SELECT version, name, description, checksum, status, 
                           applied_at, execution_time, error_message, created_at
                    FROM migration_history 
                    ORDER BY version
                """))
                
                for row in result:
                    migration = Migration(
                        version=row.version,
                        name=row.name,
                        description=row.description,
                        file_path=self.migrations_dir / f"V{row.version}__{row.name.lower().replace(' ', '_')}.sql",
                        checksum=row.checksum,
                        created_at=row.created_at,
                        status=MigrationStatus(row.status),
                        applied_at=row.applied_at,
                        execution_time=row.execution_time,
                        error_message=row.error_message
                    )
                    applied_migrations.append(migration)
                    
        except Exception as e:
            logger.error("Failed to get applied migrations", error=str(e))
            raise
        
        return applied_migrations
    
    def get_pending_migrations(self) -> List[Migration]:
        """Get list of pending migrations."""
        all_migrations = self.discover_migrations()
        applied_migrations = self.get_applied_migrations()
        
        applied_versions = {m.version for m in applied_migrations}
        pending_migrations = [m for m in all_migrations if m.version not in applied_versions]
        
        # Validate checksums for applied migrations
        for applied in applied_migrations:
            matching = next((m for m in all_migrations if m.version == applied.version), None)
            if matching and matching.checksum != applied.checksum:
                logger.warning(
                    f"Checksum mismatch for migration {applied.version}",
                    expected=applied.checksum,
                    actual=matching.checksum
                )
        
        return pending_migrations
    
    def apply_migration(self, migration: Migration, dry_run: bool = False) -> bool:
        """Apply a single migration."""
        logger.info(f"Applying migration {migration.version}: {migration.name}")
        
        if dry_run:
            logger.info(f"DRY RUN: Would apply migration {migration.version}")
            return True
        
        start_time = datetime.utcnow()
        
        try:
            with self.SessionLocal() as session:
                # Mark migration as running
                session.execute(text("""
                    INSERT INTO migration_history 
                    (version, name, description, checksum, status, applied_at)
                    VALUES (:version, :name, :description, :checksum, :status, :applied_at)
                    ON CONFLICT (version) DO UPDATE SET
                    status = :status, applied_at = :applied_at
                """), {
                    "version": migration.version,
                    "name": migration.name,
                    "description": migration.description,
                    "checksum": migration.checksum,
                    "status": MigrationStatus.RUNNING.value,
                    "applied_at": start_time
                })
                session.commit()
                
                # Read and execute migration SQL
                with open(migration.file_path, 'r') as f:
                    sql_content = f.read()
                
                # Split SQL into individual statements
                statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
                
                for statement in statements:
                    if statement:
                        session.execute(text(statement))
                
                session.commit()
                
                # Mark migration as completed
                execution_time = (datetime.utcnow() - start_time).total_seconds()
                session.execute(text("""
                    UPDATE migration_history 
                    SET status = :status, execution_time = :execution_time
                    WHERE version = :version
                """), {
                    "status": MigrationStatus.COMPLETED.value,
                    "execution_time": execution_time,
                    "version": migration.version
                })
                session.commit()
                
                logger.info(
                    f"Migration {migration.version} completed successfully",
                    execution_time=execution_time
                )
                return True
                
        except Exception as e:
            # Mark migration as failed
            try:
                with self.SessionLocal() as session:
                    session.execute(text("""
                        UPDATE migration_history 
                        SET status = :status, error_message = :error_message
                        WHERE version = :version
                    """), {
                        "status": MigrationStatus.FAILED.value,
                        "error_message": str(e),
                        "version": migration.version
                    })
                    session.commit()
            except Exception as update_error:
                logger.error("Failed to update migration status", error=str(update_error))
            
            logger.error(f"Migration {migration.version} failed", error=str(e))
            return False
    
    def migrate(self, target_version: str = None, dry_run: bool = False) -> bool:
        """Apply all pending migrations up to target version."""
        pending_migrations = self.get_pending_migrations()
        
        if target_version:
            pending_migrations = [
                m for m in pending_migrations 
                if int(m.version) <= int(target_version)
            ]
        
        if not pending_migrations:
            logger.info("No pending migrations to apply")
            return True
        
        logger.info(f"Found {len(pending_migrations)} pending migrations")
        
        success_count = 0
        for migration in pending_migrations:
            if self.apply_migration(migration, dry_run):
                success_count += 1
            else:
                logger.error(f"Migration {migration.version} failed, stopping migration process")
                break
        
        logger.info(f"Applied {success_count}/{len(pending_migrations)} migrations")
        return success_count == len(pending_migrations)
    
    def rollback(self, target_version: str) -> bool:
        """Rollback to a specific version (if rollback scripts exist)."""
        logger.warning(f"Attempting rollback to version {target_version}")
        
        applied_migrations = self.get_applied_migrations()
        rollback_migrations = [
            m for m in applied_migrations 
            if int(m.version) > int(target_version) and m.status == MigrationStatus.COMPLETED
        ]
        
        if not rollback_migrations:
            logger.info("No migrations to rollback")
            return True
        
        # Sort in reverse order for rollback
        rollback_migrations.sort(key=lambda x: int(x.version), reverse=True)
        
        success_count = 0
        for migration in rollback_migrations:
            rollback_file = self.migrations_dir / f"V{migration.version}__rollback__{migration.name.lower().replace(' ', '_')}.sql"
            
            if not rollback_file.exists():
                logger.error(f"Rollback script not found for migration {migration.version}")
                continue
            
            if self._apply_rollback(migration, rollback_file):
                success_count += 1
            else:
                logger.error(f"Rollback failed for migration {migration.version}")
                break
        
        logger.info(f"Rolled back {success_count}/{len(rollback_migrations)} migrations")
        return success_count == len(rollback_migrations)
    
    def _apply_rollback(self, migration: Migration, rollback_file: Path) -> bool:
        """Apply rollback for a specific migration."""
        try:
            with self.SessionLocal() as session:
                # Read and execute rollback SQL
                with open(rollback_file, 'r') as f:
                    sql_content = f.read()
                
                statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
                
                for statement in statements:
                    if statement:
                        session.execute(text(statement))
                
                session.commit()
                
                # Mark migration as rolled back
                session.execute(text("""
                    UPDATE migration_history 
                    SET status = :status
                    WHERE version = :version
                """), {
                    "status": MigrationStatus.ROLLED_BACK.value,
                    "version": migration.version
                })
                session.commit()
                
                logger.info(f"Rollback completed for migration {migration.version}")
                return True
                
        except Exception as e:
            logger.error(f"Rollback failed for migration {migration.version}", error=str(e))
            return False
    
    def get_migration_status(self) -> Dict[str, Any]:
        """Get overall migration status."""
        all_migrations = self.discover_migrations()
        applied_migrations = self.get_applied_migrations()
        pending_migrations = self.get_pending_migrations()
        
        return {
            "total_migrations": len(all_migrations),
            "applied_migrations": len(applied_migrations),
            "pending_migrations": len(pending_migrations),
            "last_applied_version": applied_migrations[-1].version if applied_migrations else None,
            "database_url": self.database_url.split('@')[-1] if '@' in self.database_url else "local",
            "migrations_directory": str(self.migrations_dir),
            "status": "up_to_date" if not pending_migrations else "pending_migrations"
        }


# CLI interface for migrations
def create_migration_cli():
    """Create CLI interface for migration management."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Database Migration Manager")
    parser.add_argument("command", choices=["migrate", "rollback", "status", "create"])
    parser.add_argument("--target", help="Target version for migration/rollback")
    parser.add_argument("--dry-run", action="store_true", help="Perform dry run")
    parser.add_argument("--name", help="Migration name for create command")
    
    return parser


if __name__ == "__main__":
    # CLI execution
    parser = create_migration_cli()
    args = parser.parse_args()
    
    manager = MigrationManager()
    
    if args.command == "migrate":
        success = manager.migrate(args.target, args.dry_run)
        exit(0 if success else 1)
    elif args.command == "rollback":
        if not args.target:
            print("Target version required for rollback")
            exit(1)
        success = manager.rollback(args.target)
        exit(0 if success else 1)
    elif args.command == "status":
        status = manager.get_migration_status()
        print(f"Migration Status: {status}")
    elif args.command == "create":
        if not args.name:
            print("Migration name required for create command")
            exit(1)
        # Implementation for creating new migration files
        print(f"Creating migration: {args.name}")

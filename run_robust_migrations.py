#!/usr/bin/env python3
"""
Robust Migration Runner

This script demonstrates the robust migration system with comprehensive
error handling, rollback capabilities, and status reporting.
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.robust_migrations import get_migration_manager, run_migrations, get_migration_status
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


async def main():
    """Main migration runner."""
    print("🚀 Common Supply Chain Platform - Robust Migration System")
    print("=" * 60)
    
    try:
        # Initialize migration manager
        print("📋 Initializing migration manager...")
        manager = await get_migration_manager()
        print("✅ Migration manager initialized successfully")
        
        # Get current migration status
        print("\n📊 Current Migration Status:")
        print("-" * 30)
        status = await get_migration_status()
        
        print(f"Total migrations: {status['total_migrations']}")
        print(f"Pending migrations: {status['pending_migrations']}")
        
        if status['status_counts']:
            print("\nStatus breakdown:")
            for status_name, count in status['status_counts'].items():
                print(f"  {status_name}: {count}")
        
        if status['recent_migrations']:
            print("\nRecent migrations:")
            for migration in status['recent_migrations'][:5]:
                print(f"  {migration['version']}: {migration['name']} ({migration['status']})")
        
        # Check if there are pending migrations
        if status['pending_migrations'] == 0:
            print("\n✅ No pending migrations. Database is up to date!")
            return
        
        # Run pending migrations
        print(f"\n🔄 Running {status['pending_migrations']} pending migrations...")
        print("-" * 50)
        
        results = await run_migrations()
        
        # Report results
        print("\n📈 Migration Results:")
        print("-" * 20)
        
        successful = 0
        failed = 0
        
        for i, result in enumerate(results, 1):
            if result.success:
                print(f"✅ Migration {i}: SUCCESS ({result.execution_time:.2f}s)")
                if result.rows_affected > 0:
                    print(f"   Rows affected: {result.rows_affected}")
                if result.backup_created:
                    print(f"   Backup created: Yes")
                if result.rollback_available:
                    print(f"   Rollback available: Yes")
                successful += 1
            else:
                print(f"❌ Migration {i}: FAILED ({result.execution_time:.2f}s)")
                print(f"   Error: {result.error_message}")
                if result.rollback_available:
                    print(f"   Rollback available: Yes")
                failed += 1
        
        print(f"\n📊 Summary:")
        print(f"  Successful: {successful}")
        print(f"  Failed: {failed}")
        print(f"  Total: {len(results)}")
        
        if failed > 0:
            print(f"\n⚠️  {failed} migration(s) failed. Check the logs for details.")
            sys.exit(1)
        else:
            print(f"\n🎉 All migrations completed successfully!")
        
        # Show final status
        print(f"\n📊 Final Migration Status:")
        print("-" * 30)
        final_status = await get_migration_status()
        print(f"Total migrations: {final_status['total_migrations']}")
        print(f"Pending migrations: {final_status['pending_migrations']}")
        
        if final_status['status_counts']:
            print("\nStatus breakdown:")
            for status_name, count in final_status['status_counts'].items():
                print(f"  {status_name}: {count}")
        
    except Exception as e:
        logger.error(f"Migration process failed: {e}")
        print(f"\n❌ Migration process failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

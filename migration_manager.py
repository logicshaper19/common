# migration_manager.py
import os
import subprocess
import sys
from datetime import datetime

class MigrationManager:
    """Manage database migrations across environments"""
    
    def __init__(self):
        self.environments = {
            'dev': 'DEV_DATABASE_URL',
            'test': 'TEST_DATABASE_URL', 
            'prod': 'PROD_DATABASE_URL'
        }
    
    def create_migration(self, message, auto=True):
        """Create a new migration"""
        print(f"📝 Creating migration: {message}")
        
        if auto:
            # Auto-generate migration by comparing models to database
            cmd = f'alembic revision --autogenerate -m "{message}"'
        else:
            # Create empty migration file
            cmd = f'alembic revision -m "{message}"'
        
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Migration created successfully")
            print(result.stdout)
        else:
            print("❌ Migration creation failed")
            print(result.stderr)
            return False
        
        return True
    
    def apply_migrations(self, environment='dev', revision='head'):
        """Apply migrations to specified environment"""
        print(f"🚀 Applying migrations to {environment} environment...")
        
        # Set environment variable
        if environment in self.environments:
            os.environ['ENVIRONMENT'] = environment
        
        cmd = f'alembic upgrade {revision}'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ Migrations applied to {environment}")
            print(result.stdout)
        else:
            print(f"❌ Migration failed for {environment}")
            print(result.stderr)
            return False
        
        return True
    
    def rollback_migration(self, environment='dev', steps=1):
        """Rollback migrations"""
        print(f"↩️  Rolling back {steps} migration(s) in {environment}...")
        
        os.environ['ENVIRONMENT'] = environment
        cmd = f'alembic downgrade -{steps}'
        
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ Rollback completed for {environment}")
            print(result.stdout)
        else:
            print(f"❌ Rollback failed for {environment}")
            print(result.stderr)
            return False
        
        return True
    
    def show_current_revision(self, environment='dev'):
        """Show current migration revision"""
        os.environ['ENVIRONMENT'] = environment
        cmd = 'alembic current'
        
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"📍 Current revision in {environment}:")
            print(result.stdout)
        else:
            print(f"❌ Could not get current revision for {environment}")
            print(result.stderr)
    
    def show_migration_history(self):
        """Show migration history"""
        cmd = 'alembic history --verbose'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("📜 Migration History:")
            print(result.stdout)
        else:
            print("❌ Could not get migration history")
            print(result.stderr)
    
    def sync_all_environments(self):
        """Sync all environments to latest migration"""
        print("🔄 Syncing all environments...")
        
        for env in ['dev', 'test', 'prod']:
            print(f"\n--- Syncing {env} ---")
            if not self.apply_migrations(env):
                print(f"❌ Failed to sync {env}")
                return False
        
        print("✅ All environments synced!")
        return True

# Command-line interface
if __name__ == "__main__":
    manager = MigrationManager()
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python migration_manager.py create 'migration message'")
        print("  python migration_manager.py apply [env] [revision]")
        print("  python migration_manager.py rollback [env] [steps]")
        print("  python migration_manager.py current [env]")
        print("  python migration_manager.py history")
        print("  python migration_manager.py sync-all")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == 'create':
        message = sys.argv[2] if len(sys.argv) > 2 else 'New migration'
        manager.create_migration(message)
    
    elif command == 'apply':
        env = sys.argv[2] if len(sys.argv) > 2 else 'dev'
        revision = sys.argv[3] if len(sys.argv) > 3 else 'head'
        manager.apply_migrations(env, revision)
    
    elif command == 'rollback':
        env = sys.argv[2] if len(sys.argv) > 2 else 'dev'
        steps = int(sys.argv[3]) if len(sys.argv) > 3 else 1
        manager.rollback_migration(env, steps)
    
    elif command == 'current':
        env = sys.argv[2] if len(sys.argv) > 2 else 'dev'
        manager.show_current_revision(env)
    
    elif command == 'history':
        manager.show_migration_history()
    
    elif command == 'sync-all':
        manager.sync_all_environments()
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

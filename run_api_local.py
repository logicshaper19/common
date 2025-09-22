#!/usr/bin/env python3
"""
Local API Runner
===============

This script runs the FastAPI application locally without Docker.
It uses the local PostgreSQL database we just set up.
"""

import os
import sys
import subprocess
from pathlib import Path

def load_env_file(env_file=".env.local"):
    """Load environment variables from .env.local file."""
    if os.path.exists(env_file):
        print(f"📝 Loading environment from {env_file}")
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value
        print("✅ Environment variables loaded")
    else:
        print(f"⚠️  Environment file {env_file} not found")

def check_dependencies():
    """Check if required dependencies are installed."""
    print("🔍 Checking dependencies...")
    required_packages = [
        'fastapi',
        'uvicorn',
        'sqlalchemy',
        'psycopg2',
        'alembic'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package}")
    
    if missing_packages:
        print(f"\n❌ Missing packages: {', '.join(missing_packages)}")
        print("Install them with: pip3 install -r requirements.txt")
        return False
    
    print("✅ All dependencies are available")
    return True

def run_database_migrations():
    """Run database migrations."""
    print("🗄️  Running database migrations...")
    try:
        # Set environment for migrations
        os.environ['PYTHONPATH'] = str(Path.cwd())
        
        # Run alembic migrations
        result = subprocess.run([
            'python3', '-m', 'alembic', 'upgrade', 'head'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Database migrations completed successfully")
            return True
        else:
            print(f"❌ Migration failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Migration error: {e}")
        return False

def start_api_server():
    """Start the FastAPI server."""
    print("🚀 Starting FastAPI server...")
    print("=" * 50)
    print("Server will be available at: http://127.0.0.1:8000")
    print("API docs will be available at: http://127.0.0.1:8000/docs")
    print("Press Ctrl+C to stop the server")
    print("=" * 50)
    
    try:
        # Start uvicorn server
        subprocess.run([
            'python3', '-m', 'uvicorn',
            'app.main:app',
            '--host', '127.0.0.1',
            '--port', '8000',
            '--reload',
            '--log-level', 'info'
        ])
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Server error: {e}")
        return False
    
    return True

def main():
    """Main function."""
    print("🚀 Local API Server Setup")
    print("=" * 50)
    
    # Load environment variables
    load_env_file()
    
    # Check dependencies
    if not check_dependencies():
        return False
    
    # Run migrations
    if not run_database_migrations():
        print("⚠️  Migrations failed, but continuing...")
    
    # Start server
    return start_api_server()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)


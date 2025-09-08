#!/usr/bin/env python3
"""
Simple migration runner for SQL files.
"""

import os
import sys
from sqlalchemy import create_engine, text

# Database URL
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://common_user:common_password@localhost:5432/common_db")

def run_migration(sql_file_path):
    """Run a SQL migration file."""
    if not os.path.exists(sql_file_path):
        print(f"❌ Migration file not found: {sql_file_path}")
        return False
    
    try:
        # Create engine
        engine = create_engine(DATABASE_URL)
        
        # Read SQL file
        with open(sql_file_path, 'r') as f:
            sql_content = f.read()
        
        print(f"🔄 Running migration: {sql_file_path}")
        
        # Execute SQL
        with engine.connect() as conn:
            # Split by semicolon and execute each statement
            statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
            
            for i, statement in enumerate(statements):
                if statement:
                    print(f"   Executing statement {i+1}/{len(statements)}...")
                    conn.execute(text(statement))
            
            conn.commit()
        
        print(f"✅ Migration completed successfully: {sql_file_path}")
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        return False

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python run_migration.py <sql_file_path>")
        sys.exit(1)
    
    sql_file = sys.argv[1]
    success = run_migration(sql_file)
    sys.exit(0 if success else 1)

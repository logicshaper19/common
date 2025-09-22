#!/usr/bin/env python3
"""
Simple database initialization using the existing app setup.
"""
import os
import sys

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

# Set environment variables for the database
os.environ['DATABASE_URL'] = 'postgresql://postgres:test@localhost:5433/common_test'

from app.core.database import engine, Base

def init_database():
    """Initialize the database with all tables."""
    print("🔧 Initializing database...")
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully")
    
    # Import and run the seed data service
    from app.services.seed_data import seed_initial_data_sync
    print("🌱 Seeding initial data...")
    seed_initial_data_sync()
    print("✅ Initial data seeded successfully")

if __name__ == "__main__":
    init_database()





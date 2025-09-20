#!/usr/bin/env python3
"""
Initialize the database with tables and seed data.
"""
import asyncio
import os
import sys

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.core.database import engine
from app.core.database import Base

async def init_database():
    """Initialize the database with all tables."""
    print("🔧 Initializing database...")
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    print("✅ Database tables created successfully")
    
    # Import and run the seed data service
    from app.services.seed_data import seed_initial_data
    print("🌱 Seeding initial data...")
    await seed_initial_data()
    print("✅ Initial data seeded successfully")

if __name__ == "__main__":
    asyncio.run(init_database())


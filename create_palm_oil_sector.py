#!/usr/bin/env python3
"""
Create palm oil sector
"""
import sys
import os
sys.path.append('/Users/elisha/common')

from app.core.database import SessionLocal
from app.models.sector import Sector
from uuid import uuid4

def create_palm_oil_sector():
    """Create palm oil sector"""
    
    print("🌴 Creating palm oil sector...")
    
    db = SessionLocal()
    
    try:
        # Check if palm oil sector already exists
        existing_sector = db.query(Sector).filter(Sector.id == 'palm_oil').first()
        if existing_sector:
            print("✅ Palm oil sector already exists")
            return
        
        # Create palm oil sector
        sector = Sector(
            id='palm_oil',
            name='Palm Oil',
            description='Palm oil supply chain including plantations, mills, refineries, and trading',
            is_active=True,
            regulatory_focus=['EUDR', 'NDPE', 'RSPO', 'ISPO'],
            compliance_rules={
                'origin_data_required': True,
                'traceability_required': True,
                'certification_required': True,
                'geographic_restrictions': ['Southeast Asia', 'West Africa', 'Latin America']
            }
        )
        
        db.add(sector)
        db.commit()
        
        print("✅ Palm oil sector created successfully")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_palm_oil_sector()

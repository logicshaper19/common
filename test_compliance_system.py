#!/usr/bin/env python3
"""
Test script for the compliance system.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, text
from app.core.config import settings
from app.services.compliance import ComplianceService
from app.schemas.compliance import ComplianceReportRequest
from uuid import UUID

# Create database connection
engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def test_compliance_data():
    """Test compliance data mapping."""
    db = SessionLocal()
    
    try:
        print("🧪 Testing compliance data mapping...")
        
        # Get a sample purchase order
        result = db.execute(text("""
            SELECT id, po_number, buyer_company_id, seller_company_id, product_id
            FROM purchase_orders 
            WHERE status = 'confirmed' 
            LIMIT 1
        """))
        
        po_data = result.fetchone()
        if not po_data:
            print("❌ No confirmed purchase orders found")
            return
        
        po_id = po_data[0]
        print(f"📋 Testing with PO: {po_data[1]} (ID: {po_id})")
        
        # Test compliance service
        print("\n1. Testing compliance service...")
        try:
            compliance_service = ComplianceService(db)
            print(f"✅ Compliance service initialized successfully")
            
            # Test basic functionality
            print(f"   - Service type: {type(compliance_service).__name__}")
            
        except Exception as e:
            print(f"❌ Compliance service failed: {e}")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
    finally:
        db.close()

def test_hs_codes():
    """Test HS codes functionality."""
    db = SessionLocal()
    
    try:
        print("\n🔍 Testing HS codes...")
        
        # Get HS codes
        result = db.execute(text("""
            SELECT code, description, regulation_applicable
            FROM hs_codes 
            WHERE 'EUDR' = ANY(regulation_applicable)
            LIMIT 5
        """))
        
        hs_codes = result.fetchall()
        print(f"✅ Found {len(hs_codes)} EUDR-applicable HS codes:")
        
        for code, description, regulations in hs_codes:
            print(f"   - {code}: {description} ({', '.join(regulations)})")
        
    except Exception as e:
        print(f"❌ HS codes test failed: {e}")
    finally:
        db.close()

def test_compliance_templates():
    """Test compliance templates."""
    db = SessionLocal()
    
    try:
        print("\n📄 Testing compliance templates...")
        
        # Get templates
        result = db.execute(text("""
            SELECT name, regulation_type, version, is_active
            FROM compliance_templates
            ORDER BY regulation_type
        """))
        
        templates = result.fetchall()
        print(f"✅ Found {len(templates)} compliance templates:")
        
        for name, regulation_type, version, is_active in templates:
            status = "Active" if is_active else "Inactive"
            print(f"   - {name} ({regulation_type} v{version}) - {status}")
        
    except Exception as e:
        print(f"❌ Templates test failed: {e}")
    finally:
        db.close()

def main():
    """Main test function."""
    print("🚀 Testing compliance system...")
    
    test_hs_codes()
    test_compliance_templates()
    test_compliance_data()
    
    print("\n✅ Compliance system test completed!")

if __name__ == "__main__":
    main()

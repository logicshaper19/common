#!/usr/bin/env python3
"""
Test script to verify compliance system fixes.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from uuid import uuid4
from decimal import Decimal
from datetime import date, datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models.user import User
from app.models.company import Company
from app.models.product import Product
from app.models.purchase_order import PurchaseOrder
from app.core.auth import get_password_hash
from app.services.compliance import (
    ComplianceService, ComplianceDataMapper, ComplianceTemplateEngine,
    PurchaseOrderNotFoundError, CompanyNotFoundError, ProductNotFoundError,
    ComplianceDataError, RiskAssessmentError, MassBalanceError, ValidationError
)
from app.schemas.compliance import ComplianceReportRequest


def test_compliance_fixes():
    """Test all compliance system fixes."""
    print("🧪 Testing Compliance System Fixes")
    print("=" * 50)
    
    # Create test database
    engine = create_engine("postgresql://elisha@localhost:5432/common_test")
    
    # Add batch_id column if it doesn't exist
    from sqlalchemy import text
    try:
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'purchase_orders' 
                AND column_name = 'batch_id'
            """))
            
            if not result.fetchone():
                conn.execute(text("ALTER TABLE purchase_orders ADD COLUMN batch_id UUID REFERENCES batches(id)"))
                conn.commit()
                print("Added batch_id column to purchase_orders table")
    except Exception as e:
        print(f"Error adding batch_id column: {e}")
    
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    with TestingSessionLocal() as db:
        try:
            # Test 1: Create test data
            print("\n1. Creating test data...")
            test_data = create_test_data(db)
            print("✅ Test data created successfully")
            
            # Test 2: Test data validation
            print("\n2. Testing data validation...")
            test_data_validation()
            print("✅ Data validation tests passed")
            
            # Test 3: Test error handling
            print("\n3. Testing error handling...")
            test_error_handling(db)
            print("✅ Error handling tests passed")
            
            # Test 4: Test dependency injection
            print("\n4. Testing dependency injection...")
            test_dependency_injection(db)
            print("✅ Dependency injection tests passed")
            
            # Test 5: Test template engine
            print("\n5. Testing template engine...")
            test_template_engine(db)
            print("✅ Template engine tests passed")
            
            # Test 6: Test data mapper
            print("\n6. Testing data mapper...")
            test_data_mapper(db, test_data)
            print("✅ Data mapper tests passed")
            
            # Test 7: Test full compliance service
            print("\n7. Testing full compliance service...")
            test_compliance_service(db, test_data)
            print("✅ Compliance service tests passed")
            
            print("\n🎉 All compliance system fixes verified successfully!")
            
        except Exception as e:
            print(f"\n❌ Test failed: {e}")
            raise
        finally:
            # Cleanup
            db.rollback()


def create_test_data(db):
    """Create test data for compliance tests."""
    # Create test company with unique email
    company_id = uuid4()
    company = Company(
        id=company_id,
        name=f"Test Compliance Company {company_id}",
        company_type="brand",
        email=f"test-{company_id}@compliance.com",
        website="http://test.com",
        address_street="123 Test St",
        phone="123-456-7890",
        country="Testland"
    )
    db.add(company)
    db.flush()
    
    # Create test user
    user_id = uuid4()
    user = User(
        id=user_id,
        full_name=f"Test User {user_id}",
        email=f"test-{user_id}@example.com",
        hashed_password=get_password_hash("TestPass123!"),
        role="admin",
        company_id=company.id
    )
    db.add(user)
    db.flush()
    
    # Create test product
    product_id = uuid4()
    product = Product(
        id=product_id,
        name=f"Test Product {product_id}",
        common_product_id=f"TEST-PROD-{product_id}",
        category="raw_material",
        default_unit="kg",
        material_breakdown=[{"material": "test_material", "percentage": 100.0}],
        hs_code="1511.10.00"
    )
    db.add(product)
    db.flush()
    
    # Create test purchase order
    po_id = uuid4()
    po = PurchaseOrder(
        id=po_id,
        po_number=f"TEST-PO-{po_id}",
        buyer_company_id=company.id,
        seller_company_id=company.id,
        product_id=product.id,
        quantity=Decimal("1000.0"),
        unit="kg",
        unit_price=Decimal("10.0"),
        total_amount=Decimal("10000.0"),
        delivery_date=date.today(),
        delivery_location="Test Location",
        status="confirmed"
    )
    db.add(po)
    db.commit()
    
    return {
        "user": user,
        "company": company,
        "product": product,
        "purchase_order": po
    }


def test_data_validation():
    """Test data validation functionality."""
    from app.services.compliance.validators import get_data_validator
    
    validator = get_data_validator()
    
    # Test risk score validation
    assert validator.validate_risk_score(0.5) == Decimal('0.5')
    assert validator.validate_risk_score(0.0) == Decimal('0.0')
    assert validator.validate_risk_score(1.0) == Decimal('1.0')
    
    # Test invalid risk scores
    try:
        validator.validate_risk_score(-0.1)
        assert False, "Should have raised ValidationError"
    except ValidationError:
        pass
    
    try:
        validator.validate_risk_score(1.1)
        assert False, "Should have raised ValidationError"
    except ValidationError:
        pass
    
    # Test HS code validation
    assert validator.validate_hs_code("1511.10.00") == "1511.10.00"
    assert validator.validate_hs_code("1511.10") == "1511.10"
    
    # Test invalid HS codes
    try:
        validator.validate_hs_code("")
        assert False, "Should have raised ValidationError"
    except ValidationError:
        pass
    
    try:
        validator.validate_hs_code("invalid")
        assert False, "Should have raised ValidationError"
    except ValidationError:
        pass


def test_error_handling(db):
    """Test error handling with custom exceptions."""
    data_mapper = ComplianceDataMapper(db)
    
    # Test PO not found
    try:
        data_mapper.map_po_to_eudr_data(uuid4())
        assert False, "Should have raised PurchaseOrderNotFoundError"
    except PurchaseOrderNotFoundError:
        pass
    
    # Test invalid PO ID format
    try:
        data_mapper.map_po_to_eudr_data("invalid-uuid")
        assert False, "Should have raised ComplianceDataError"
    except ComplianceDataError:
        pass


def test_dependency_injection(db):
    """Test dependency injection functionality."""
    # Test with default dependencies
    service1 = ComplianceService(db)
    assert service1.db == db
    assert service1.data_mapper is not None
    assert service1.template_engine is not None
    
    # Test with custom dependencies
    custom_data_mapper = ComplianceDataMapper(db)
    custom_template_engine = ComplianceTemplateEngine(db)
    
    service2 = ComplianceService(
        db=db,
        data_mapper=custom_data_mapper,
        template_engine=custom_template_engine
    )
    
    assert service2.db == db
    assert service2.data_mapper == custom_data_mapper
    assert service2.template_engine == custom_template_engine


def test_template_engine(db):
    """Test template engine functionality."""
    # Create a new session for template engine tests
    from sqlalchemy.orm import sessionmaker
    engine = create_engine("postgresql://elisha@localhost:5432/common_test")
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    with TestingSessionLocal() as fresh_db:
        template_engine = ComplianceTemplateEngine(fresh_db)
        
        # Test template retrieval
        template = template_engine._get_template('EUDR')
        assert template is not None
        assert hasattr(template, 'render')
        
        # Test report generation
        eudr_data = {
            'operator': {'name': 'Test Company'},
            'product': {'hs_code': '1511.10.00', 'description': 'Test Product'},
            'supply_chain': [],
            'risk_assessment': {'deforestation_risk': Decimal('0.5')},
            'trace_path': 'Test Path',
            'trace_depth': 1,
            'generated_at': datetime.now()
        }
        
        report_content = template_engine.generate_eudr_report(eudr_data)
        assert isinstance(report_content, bytes)
        assert b'EUDR_Report' in report_content
        assert b'Test Company' in report_content


def test_data_mapper(db, test_data):
    """Test data mapper functionality."""
    # Create a new session for data mapper tests
    from sqlalchemy.orm import sessionmaker
    engine = create_engine("postgresql://elisha@localhost:5432/common_test")
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    with TestingSessionLocal() as fresh_db:
        # Create test data in the fresh session
        fresh_test_data = create_test_data(fresh_db)
        
        data_mapper = ComplianceDataMapper(fresh_db)
        po = fresh_test_data["purchase_order"]
        
        # Test EUDR data mapping
        eudr_data = data_mapper.map_po_to_eudr_data(po.id)
        print(f"Company name: {eudr_data.operator.name}")
        assert "Test Compliance Company" in eudr_data.operator.name
        assert eudr_data.product.hs_code == "1511.10.00"
        assert eudr_data.product.quantity == Decimal("1.0")  # Default quantity
        
        # Test RSPO data mapping
        rspo_data = data_mapper.map_po_to_rspo_data(po.id)
        assert rspo_data.certification.certificate_number is None  # No certification data in test
        assert rspo_data.certification.certification_type is None
        
        # Test data sanitization
        from app.services.compliance.validators import get_template_sanitizer
        sanitizer = get_template_sanitizer()
        
        test_data = {"name": "<script>alert('xss')</script>"}
        sanitized = sanitizer.sanitize_template_data(test_data)
        assert "&lt;script&gt;" in sanitized["name"]


def test_compliance_service(db, test_data):
    """Test full compliance service functionality."""
    # Create a new session for compliance service tests
    from sqlalchemy.orm import sessionmaker
    engine = create_engine("postgresql://elisha@localhost:5432/common_test")
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    with TestingSessionLocal() as fresh_db:
        # Create test data in the fresh session
        fresh_test_data = create_test_data(fresh_db)
        
        # Initialize service with dependency injection
        data_mapper = ComplianceDataMapper(fresh_db)
        template_engine = ComplianceTemplateEngine(fresh_db)
        service = ComplianceService(
            db=fresh_db,
            data_mapper=data_mapper,
            template_engine=template_engine
        )
        
        po = fresh_test_data["purchase_order"]
        
        # Test EUDR report generation
        request = ComplianceReportRequest(
            po_id=po.id,
            regulation_type="EUDR",
            include_risk_assessment=True,
            include_mass_balance=True
        )
        
        response = service.generate_compliance_report(request)
        assert response.regulation_type == "EUDR"
        assert response.po_id == po.id
        assert response.status == "GENERATED"
        assert response.report_id is not None
        
        # Test RSPO report generation
        request.regulation_type = "RSPO"
        response = service.generate_compliance_report(request)
        assert response.regulation_type == "RSPO"
        assert response.po_id == po.id
        assert response.status == "GENERATED"
        
        # Test invalid regulation type
        try:
            request.regulation_type = "INVALID"
            service.generate_compliance_report(request)
            assert False, "Should have raised ComplianceDataError"
        except ComplianceDataError:
            pass


if __name__ == "__main__":
    test_compliance_fixes()

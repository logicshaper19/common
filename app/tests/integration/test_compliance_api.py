"""
Integration tests for compliance API endpoints.
"""
import pytest
import httpx
from uuid import uuid4
from decimal import Decimal
from datetime import date, datetime

from app.main import app
from app.core.database import get_db, Base, engine
from app.models.user import User
from app.models.company import Company
from app.models.product import Product
from app.models.purchase_order import PurchaseOrder
from app.core.auth import get_password_hash
from sqlalchemy.orm import sessionmaker

# Use the PostgreSQL test database URL from conftest
SQLALCHEMY_DATABASE_URL = "postgresql://elisha@localhost:5432/common_test"
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="module")
def setup_compliance_db():
    """Set up and tear down the test database for compliance tests."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session_compliance():
    """Provide a transactional scope for a test."""
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="module")
def client_compliance():
    """Provide a test client for FastAPI application."""
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()
    app.dependency_overrides[get_db] = override_get_db
    with httpx.Client(app=app, base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture(scope="module")
def test_compliance_data(db_session_compliance):
    """Create test data for compliance tests."""
    # Create test company
    company = Company(
        id=uuid4(),
        name="Compliance Test Company",
        company_type="brand",
        email="compliance@example.com",
        website="http://compliance.com",
        address="123 Compliance St",
        phone_number="123-456-7890",
        country="Complianceland",
        registration_date=date.today(),
        registration_number="COMP123",
        tax_id="TAX123"
    )
    db_session_compliance.add(company)
    db_session_compliance.flush()
    
    # Create test user
    user = User(
        id=uuid4(),
        full_name="Compliance Test User",
        email="compliance_user@example.com",
        hashed_password=get_password_hash("CompliancePass123!"),
        role="admin",
        company_id=company.id
    )
    db_session_compliance.add(user)
    db_session_compliance.flush()
    
    # Create test product
    product = Product(
        id=uuid4(),
        name="Compliance Test Product",
        common_product_id="COMP-PROD-001",
        company_id=company.id,
        category="raw_material",
        default_unit="kg",
        material_breakdown=[{"material": "test_material", "percentage": 100.0}],
        hs_code="1511.10.00",
        certification_number="CERT123",
        certification_type="RSPO",
        certification_expiry=date.today()
    )
    db_session_compliance.add(product)
    db_session_compliance.flush()
    
    # Create test purchase order
    po = PurchaseOrder(
        id=uuid4(),
        po_number="COMP-PO-001",
        buyer_company_id=company.id,
        seller_company_id=company.id,  # Same company for simplicity
        product_id=product.id,
        quantity=Decimal("1000.0"),
        unit="kg",
        price_per_unit=Decimal("10.0"),
        currency="USD",
        issue_date=date.today(),
        delivery_date=date.today(),
        status="confirmed"
    )
    db_session_compliance.add(po)
    db_session_compliance.commit()
    
    return {
        "user": user,
        "company": company,
        "product": product,
        "purchase_order": po
    }


@pytest.mark.integration
def test_generate_eudr_report_success(client_compliance, test_compliance_data):
    """Test successful EUDR report generation."""
    user = test_compliance_data["user"]
    po = test_compliance_data["purchase_order"]
    
    # Authenticate user
    login_payload = {"username": user.email, "password": "CompliancePass123!"}
    response = client_compliance.post("/api/v1/auth/token", json=login_payload)
    assert response.status_code == 200
    token = response.json()["access_token"]
    
    # Generate EUDR report
    report_payload = {
        "po_id": str(po.id),
        "regulation_type": "EUDR",
        "include_risk_assessment": True,
        "include_mass_balance": True
    }
    
    response = client_compliance.post(
        "/api/v1/compliance/reports/generate",
        json=report_payload,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["regulation_type"] == "EUDR"
    assert data["po_id"] == str(po.id)
    assert "report_id" in data
    assert "download_url" in data
    assert data["status"] == "GENERATED"


@pytest.mark.integration
def test_generate_rspo_report_success(client_compliance, test_compliance_data):
    """Test successful RSPO report generation."""
    user = test_compliance_data["user"]
    po = test_compliance_data["purchase_order"]
    
    # Authenticate user
    login_payload = {"username": user.email, "password": "CompliancePass123!"}
    response = client_compliance.post("/api/v1/auth/token", json=login_payload)
    assert response.status_code == 200
    token = response.json()["access_token"]
    
    # Generate RSPO report
    report_payload = {
        "po_id": str(po.id),
        "regulation_type": "RSPO",
        "include_risk_assessment": True,
        "include_mass_balance": True
    }
    
    response = client_compliance.post(
        "/api/v1/compliance/reports/generate",
        json=report_payload,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["regulation_type"] == "RSPO"
    assert data["po_id"] == str(po.id)
    assert "report_id" in data
    assert "download_url" in data
    assert data["status"] == "GENERATED"


@pytest.mark.integration
def test_generate_report_invalid_po_id(client_compliance, test_compliance_data):
    """Test report generation with invalid PO ID."""
    user = test_compliance_data["user"]
    
    # Authenticate user
    login_payload = {"username": user.email, "password": "CompliancePass123!"}
    response = client_compliance.post("/api/v1/auth/token", json=login_payload)
    assert response.status_code == 200
    token = response.json()["access_token"]
    
    # Generate report with invalid PO ID
    report_payload = {
        "po_id": str(uuid4()),  # Non-existent PO
        "regulation_type": "EUDR",
        "include_risk_assessment": True,
        "include_mass_balance": True
    }
    
    response = client_compliance.post(
        "/api/v1/compliance/reports/generate",
        json=report_payload,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.integration
def test_generate_report_invalid_regulation_type(client_compliance, test_compliance_data):
    """Test report generation with invalid regulation type."""
    user = test_compliance_data["user"]
    po = test_compliance_data["purchase_order"]
    
    # Authenticate user
    login_payload = {"username": user.email, "password": "CompliancePass123!"}
    response = client_compliance.post("/api/v1/auth/token", json=login_payload)
    assert response.status_code == 200
    token = response.json()["access_token"]
    
    # Generate report with invalid regulation type
    report_payload = {
        "po_id": str(po.id),
        "regulation_type": "INVALID",
        "include_risk_assessment": True,
        "include_mass_balance": True
    }
    
    response = client_compliance.post(
        "/api/v1/compliance/reports/generate",
        json=report_payload,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 400
    assert "unsupported regulation type" in response.json()["detail"].lower()


@pytest.mark.integration
def test_generate_report_missing_authentication(client_compliance, test_compliance_data):
    """Test report generation without authentication."""
    po = test_compliance_data["purchase_order"]
    
    # Generate report without authentication
    report_payload = {
        "po_id": str(po.id),
        "regulation_type": "EUDR",
        "include_risk_assessment": True,
        "include_mass_balance": True
    }
    
    response = client_compliance.post(
        "/api/v1/compliance/reports/generate",
        json=report_payload
    )
    
    assert response.status_code == 401


@pytest.mark.integration
def test_list_compliance_reports(client_compliance, test_compliance_data):
    """Test listing compliance reports."""
    user = test_compliance_data["user"]
    po = test_compliance_data["purchase_order"]
    
    # Authenticate user
    login_payload = {"username": user.email, "password": "CompliancePass123!"}
    response = client_compliance.post("/api/v1/auth/token", json=login_payload)
    assert response.status_code == 200
    token = response.json()["access_token"]
    
    # First generate a report
    report_payload = {
        "po_id": str(po.id),
        "regulation_type": "EUDR",
        "include_risk_assessment": True,
        "include_mass_balance": True
    }
    
    response = client_compliance.post(
        "/api/v1/compliance/reports/generate",
        json=report_payload,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    
    # List reports
    response = client_compliance.get(
        "/api/v1/compliance/reports",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "reports" in data
    assert len(data["reports"]) >= 1


@pytest.mark.integration
def test_get_compliance_report_by_id(client_compliance, test_compliance_data):
    """Test getting a specific compliance report by ID."""
    user = test_compliance_data["user"]
    po = test_compliance_data["purchase_order"]
    
    # Authenticate user
    login_payload = {"username": user.email, "password": "CompliancePass123!"}
    response = client_compliance.post("/api/v1/auth/token", json=login_payload)
    assert response.status_code == 200
    token = response.json()["access_token"]
    
    # Generate a report
    report_payload = {
        "po_id": str(po.id),
        "regulation_type": "EUDR",
        "include_risk_assessment": True,
        "include_mass_balance": True
    }
    
    response = client_compliance.post(
        "/api/v1/compliance/reports/generate",
        json=report_payload,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    report_id = response.json()["report_id"]
    
    # Get the report by ID
    response = client_compliance.get(
        f"/api/v1/compliance/reports/{report_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == report_id
    assert data["regulation_type"] == "EUDR"
    assert data["po_id"] == str(po.id)


@pytest.mark.integration
def test_download_compliance_report(client_compliance, test_compliance_data):
    """Test downloading a compliance report."""
    user = test_compliance_data["user"]
    po = test_compliance_data["purchase_order"]
    
    # Authenticate user
    login_payload = {"username": user.email, "password": "CompliancePass123!"}
    response = client_compliance.post("/api/v1/auth/token", json=login_payload)
    assert response.status_code == 200
    token = response.json()["access_token"]
    
    # Generate a report
    report_payload = {
        "po_id": str(po.id),
        "regulation_type": "EUDR",
        "include_risk_assessment": True,
        "include_mass_balance": True
    }
    
    response = client_compliance.post(
        "/api/v1/compliance/reports/generate",
        json=report_payload,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    report_id = response.json()["report_id"]
    
    # Download the report
    response = client_compliance.get(
        f"/api/v1/compliance/reports/{report_id}/download",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/xml"
    assert b"EUDR_Report" in response.content


@pytest.mark.integration
def test_compliance_report_performance(client_compliance, test_compliance_data):
    """Test compliance report generation performance."""
    import time
    
    user = test_compliance_data["user"]
    po = test_compliance_data["purchase_order"]
    
    # Authenticate user
    login_payload = {"username": user.email, "password": "CompliancePass123!"}
    response = client_compliance.post("/api/v1/auth/token", json=login_payload)
    assert response.status_code == 200
    token = response.json()["access_token"]
    
    # Measure report generation time
    report_payload = {
        "po_id": str(po.id),
        "regulation_type": "EUDR",
        "include_risk_assessment": True,
        "include_mass_balance": True
    }
    
    start_time = time.time()
    response = client_compliance.post(
        "/api/v1/compliance/reports/generate",
        json=report_payload,
        headers={"Authorization": f"Bearer {token}"}
    )
    end_time = time.time()
    
    assert response.status_code == 200
    generation_time = end_time - start_time
    
    # Assert that report generation takes less than 5 seconds
    assert generation_time < 5.0, f"Report generation took {generation_time:.2f} seconds, expected < 5.0"

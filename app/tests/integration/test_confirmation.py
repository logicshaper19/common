"""
Tests for purchase order confirmation system.
"""
import pytest
from decimal import Decimal
from datetime import date, datetime, timedelta
from uuid import uuid4
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.services.confirmation import ConfirmationService
from app.schemas.confirmation import (
    ConfirmationInterfaceType,
    PurchaseOrderConfirmation,
    OriginDataCapture,
    TransformationDataCapture,
    GeographicCoordinates,
    InputMaterialLink,
    InputMaterialValidationRequest,
    OriginDataValidationRequest
)
from app.schemas.purchase_order import PurchaseOrderCreate, PurchaseOrderStatus
from app.models.company import Company
from app.models.product import Product
from app.models.purchase_order import PurchaseOrder

# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_confirmation.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
Base.metadata.create_all(bind=engine)


@pytest.fixture(autouse=True)
def clean_db():
    """Clean database before each test."""
    # Drop all tables and recreate them
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture
def db_session():
    """Get database session for testing."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def sample_companies(db_session: Session):
    """Create sample companies for testing."""
    companies = {}

    # Create originator company
    companies["originator"] = Company(
        id=uuid4(),
        name="Palm Plantation Co",
        company_type="originator",
        email="plantation@example.com"
    )

    # Create processor company
    companies["processor"] = Company(
        id=uuid4(),
        name="Palm Processing Ltd",
        company_type="processor",
        email="processor@example.com"
    )

    # Create brand company
    companies["brand"] = Company(
        id=uuid4(),
        name="Consumer Brand Inc",
        company_type="brand",
        email="brand@example.com"
    )

    for company in companies.values():
        db_session.add(company)

    db_session.commit()

    for company in companies.values():
        db_session.refresh(company)

    return companies


@pytest.fixture
def sample_products(db_session: Session):
    """Create sample products for testing."""
    products = {}

    # Fresh Fruit Bunches (raw material)
    products["ffb"] = Product(
        id=uuid4(),
        common_product_id="FFB-001",
        name="Fresh Fruit Bunches (FFB)",
        description="Fresh palm fruit bunches harvested from oil palm trees",
        category="raw_material",
        can_have_composition=False,
        material_breakdown=None,
        default_unit="KGM",
        hs_code="1207.10.00",
        origin_data_requirements={
            "required_fields": ["plantation_coordinates", "harvest_date", "plantation_certification"],
            "optional_fields": ["variety", "age_of_trees", "yield_per_hectare"]
        }
    )

    # Crude Palm Oil (processed)
    products["cpo"] = Product(
        id=uuid4(),
        common_product_id="CPO-001",
        name="Crude Palm Oil (CPO)",
        description="Unrefined palm oil extracted from fresh fruit bunches",
        category="processed",
        can_have_composition=True,
        material_breakdown={"palm_oil": 100.0},
        default_unit="KGM",
        hs_code="1511.10.00",
        origin_data_requirements={
            "required_fields": ["mill_location", "extraction_date", "ffb_source"],
            "optional_fields": ["free_fatty_acid", "moisture_content", "impurities"]
        }
    )

    # Palm Kernel Oil (processed)
    products["pko"] = Product(
        id=uuid4(),
        common_product_id="PKO-001",
        name="Palm Kernel Oil (PKO)",
        description="Oil extracted from palm kernels",
        category="processed",
        can_have_composition=True,
        material_breakdown={"palm_kernel_oil": 100.0},
        default_unit="KGM",
        hs_code="1513.21.00",
        origin_data_requirements={
            "required_fields": ["mill_location", "extraction_date", "kernel_source"],
            "optional_fields": ["free_fatty_acid", "moisture_content", "iodine_value"]
        }
    )

    # Palm Oil Blend (finished good)
    products["blend"] = Product(
        id=uuid4(),
        common_product_id="BLEND-001",
        name="Palm Oil Blend (80/20)",
        description="Blend of 80% palm oil and 20% palm kernel oil",
        category="finished_good",
        can_have_composition=True,
        material_breakdown={"palm_oil": 80.0, "palm_kernel_oil": 20.0},
        default_unit="KGM",
        hs_code="1511.90.00",
        origin_data_requirements={
            "required_fields": ["blending_facility", "blend_date", "component_sources"],
            "optional_fields": ["blend_ratio_verification", "quality_parameters"]
        }
    )

    for product in products.values():
        db_session.add(product)

    db_session.commit()

    for product in products.values():
        db_session.refresh(product)

    return products


class TestConfirmationInterfaceDetermination:
    """Test confirmation interface determination logic."""
    
    def test_originator_company_gets_origin_interface(self, db_session, sample_companies, sample_products):
        """Test that originator companies get origin data interface."""
        confirmation_service = ConfirmationService(db_session)

        # Use the existing originator company from fixtures
        originator = sample_companies["originator"]

        # Create purchase order with originator as seller
        po = PurchaseOrder(
            po_number="PO-TEST-001",
            buyer_company_id=sample_companies["processor"].id,
            seller_company_id=originator.id,
            product_id=sample_products["cpo"].id,
            quantity=Decimal("1000.0"),
            unit_price=Decimal("850.00"),
            total_amount=Decimal("850000.00"),
            unit="KGM",
            delivery_date=date.today() + timedelta(days=30),
            delivery_location="Test Location",
            status="draft"
        )
        db_session.add(po)
        db_session.commit()

        # Test interface determination
        interface_response = confirmation_service.determine_confirmation_interface(
            po.id, originator.id
        )

        assert interface_response.interface_type == ConfirmationInterfaceType.ORIGIN_DATA_INTERFACE
        assert interface_response.seller_company_type == "originator"
        assert "geographic_coordinates" in interface_response.required_fields
        assert "certifications" in interface_response.required_fields
    
    def test_processor_company_gets_transformation_interface(self, db_session, sample_companies, sample_products):
        """Test that processor companies get transformation interface."""
        confirmation_service = ConfirmationService(db_session)
        
        # Create purchase order with processor as seller
        po = PurchaseOrder(
            po_number="PO-TEST-002",
            buyer_company_id=sample_companies["brand"].id,
            seller_company_id=sample_companies["processor"].id,
            product_id=sample_products["blend"].id,
            quantity=Decimal("500.0"),
            unit_price=Decimal("900.00"),
            total_amount=Decimal("450000.00"),
            unit="KGM",
            delivery_date=date.today() + timedelta(days=30),
            delivery_location="Test Location",
            status="draft"
        )
        db_session.add(po)
        db_session.commit()
        
        # Test interface determination
        interface_response = confirmation_service.determine_confirmation_interface(
            po.id, sample_companies["processor"].id
        )
        
        assert interface_response.interface_type == ConfirmationInterfaceType.TRANSFORMATION_INTERFACE
        assert interface_response.seller_company_type == "processor"
        assert "input_materials" in interface_response.required_fields
        assert "transformation_process" in interface_response.required_fields
    
    def test_raw_material_gets_origin_interface_regardless_of_company(self, db_session, sample_companies, sample_products):
        """Test that raw materials always get origin interface regardless of company type."""
        confirmation_service = ConfirmationService(db_session)
        
        # Create purchase order with processor selling raw material
        po = PurchaseOrder(
            po_number="PO-TEST-003",
            buyer_company_id=sample_companies["brand"].id,
            seller_company_id=sample_companies["processor"].id,
            product_id=sample_products["ffb"].id,  # Raw material
            quantity=Decimal("2000.0"),
            unit_price=Decimal("300.00"),
            total_amount=Decimal("600000.00"),
            unit="KGM",
            delivery_date=date.today() + timedelta(days=30),
            delivery_location="Test Location",
            status="draft"
        )
        db_session.add(po)
        db_session.commit()
        
        # Test interface determination
        interface_response = confirmation_service.determine_confirmation_interface(
            po.id, sample_companies["processor"].id
        )
        
        assert interface_response.interface_type == ConfirmationInterfaceType.ORIGIN_DATA_INTERFACE
        assert interface_response.product_category == "raw_material"
    
    def test_access_control_only_seller_can_get_interface(self, db_session, sample_companies, sample_products):
        """Test that only seller company can access confirmation interface."""
        confirmation_service = ConfirmationService(db_session)
        
        # Create purchase order
        po = PurchaseOrder(
            po_number="PO-TEST-004",
            buyer_company_id=sample_companies["brand"].id,
            seller_company_id=sample_companies["processor"].id,
            product_id=sample_products["cpo"].id,
            quantity=Decimal("1000.0"),
            unit_price=Decimal("850.00"),
            total_amount=Decimal("850000.00"),
            unit="KGM",
            delivery_date=date.today() + timedelta(days=30),
            delivery_location="Test Location",
            status="draft"
        )
        db_session.add(po)
        db_session.commit()
        
        # Test that buyer cannot access interface
        with pytest.raises(Exception) as exc_info:
            confirmation_service.determine_confirmation_interface(
                po.id, sample_companies["brand"].id
            )
        assert "Only the seller company can confirm" in str(exc_info.value)


class TestOriginDataValidation:
    """Test origin data validation."""
    
    def test_valid_origin_data_passes_validation(self, db_session, sample_companies, sample_products):
        """Test that valid origin data passes validation."""
        confirmation_service = ConfirmationService(db_session)
        
        # Create purchase order
        po = PurchaseOrder(
            po_number="PO-TEST-005",
            buyer_company_id=sample_companies["processor"].id,
            seller_company_id=sample_companies["originator"].id,
            product_id=sample_products["ffb"].id,
            quantity=Decimal("1000.0"),
            unit_price=Decimal("300.00"),
            total_amount=Decimal("300000.00"),
            unit="KGM",
            delivery_date=date.today() + timedelta(days=30),
            delivery_location="Test Location",
            status="draft"
        )
        db_session.add(po)
        db_session.commit()
        
        # Create valid origin data
        origin_data = OriginDataCapture(
            geographic_coordinates=GeographicCoordinates(
                latitude=2.5,
                longitude=101.5,
                accuracy_meters=10.0
            ),
            certifications=["RSPO", "NDPE"],
            harvest_date=date.today() - timedelta(days=7),
            farm_identification="FARM-001",
            batch_number="BATCH-2024-001"
        )
        
        # Validate origin data
        request = OriginDataValidationRequest(
            purchase_order_id=po.id,
            origin_data=origin_data
        )
        
        validation_response = confirmation_service.validate_origin_data(
            request, sample_companies["originator"].id
        )
        
        assert validation_response.is_valid
        assert len(validation_response.errors) == 0
        assert validation_response.compliance_status["overall"] in ["fully_compliant", "partially_compliant"]
    
    def test_invalid_coordinates_fail_validation(self, db_session, sample_companies, sample_products):
        """Test that invalid coordinates fail validation."""
        confirmation_service = ConfirmationService(db_session)
        
        # Create purchase order
        po = PurchaseOrder(
            po_number="PO-TEST-006",
            buyer_company_id=sample_companies["processor"].id,
            seller_company_id=sample_companies["originator"].id,
            product_id=sample_products["ffb"].id,
            quantity=Decimal("1000.0"),
            unit_price=Decimal("300.00"),
            total_amount=Decimal("300000.00"),
            unit="KGM",
            delivery_date=date.today() + timedelta(days=30),
            delivery_location="Test Location",
            status="draft"
        )
        db_session.add(po)
        db_session.commit()
        
        # Create origin data with future harvest date (invalid)
        origin_data = OriginDataCapture(
            geographic_coordinates=GeographicCoordinates(
                latitude=2.5,
                longitude=101.5
            ),
            certifications=["RSPO"],
            harvest_date=date.today() + timedelta(days=1),  # Future date
            farm_identification="FARM-001"
        )
        
        # Validate origin data
        request = OriginDataValidationRequest(
            purchase_order_id=po.id,
            origin_data=origin_data
        )
        
        validation_response = confirmation_service.validate_origin_data(
            request, sample_companies["originator"].id
        )
        
        assert not validation_response.is_valid
        assert any("future" in error.lower() for error in validation_response.errors)


class TestInputMaterialValidation:
    """Test input material validation."""
    
    def test_valid_input_materials_pass_validation(self, db_session, sample_companies, sample_products):
        """Test that valid input materials pass validation."""
        confirmation_service = ConfirmationService(db_session)
        
        # Create source purchase orders
        source_po1 = PurchaseOrder(
            po_number="PO-SOURCE-001",
            buyer_company_id=sample_companies["processor"].id,
            seller_company_id=sample_companies["originator"].id,
            product_id=sample_products["cpo"].id,
            quantity=Decimal("800.0"),
            unit_price=Decimal("850.00"),
            total_amount=Decimal("680000.00"),
            unit="KGM",
            delivery_date=date.today() + timedelta(days=30),
            delivery_location="Test Location",
            status="confirmed"
        )
        
        source_po2 = PurchaseOrder(
            po_number="PO-SOURCE-002",
            buyer_company_id=sample_companies["processor"].id,
            seller_company_id=sample_companies["originator"].id,
            product_id=sample_products["pko"].id,
            quantity=Decimal("200.0"),
            unit_price=Decimal("1200.00"),
            total_amount=Decimal("240000.00"),
            unit="KGM",
            delivery_date=date.today() + timedelta(days=30),
            delivery_location="Test Location",
            status="confirmed"
        )
        
        db_session.add_all([source_po1, source_po2])
        db_session.commit()
        
        # Create target purchase order
        target_po = PurchaseOrder(
            po_number="PO-TARGET-001",
            buyer_company_id=sample_companies["brand"].id,
            seller_company_id=sample_companies["processor"].id,
            product_id=sample_products["blend"].id,
            quantity=Decimal("1000.0"),
            unit_price=Decimal("900.00"),
            total_amount=Decimal("900000.00"),
            unit="KGM",
            delivery_date=date.today() + timedelta(days=30),
            delivery_location="Test Location",
            status="draft"
        )
        db_session.add(target_po)
        db_session.commit()
        
        # Create valid input materials (80% CPO, 20% PKO)
        input_materials = [
            InputMaterialLink(
                source_po_id=source_po1.id,
                quantity_used=Decimal("800.0"),
                percentage_contribution=80.0,
                transformation_notes="Primary palm oil component"
            ),
            InputMaterialLink(
                source_po_id=source_po2.id,
                quantity_used=Decimal("200.0"),
                percentage_contribution=20.0,
                transformation_notes="Palm kernel oil component"
            )
        ]
        
        # Validate input materials
        request = InputMaterialValidationRequest(
            purchase_order_id=target_po.id,
            input_materials=input_materials
        )
        
        validation_response = confirmation_service.validate_input_materials(
            request, sample_companies["processor"].id
        )
        
        assert validation_response.is_valid
        assert len(validation_response.errors) == 0
        assert validation_response.total_quantity_requested == Decimal("1000.0")
    
    def test_invalid_percentage_sum_fails_validation(self, db_session, sample_companies, sample_products):
        """Test that input materials with invalid percentage sum fail validation."""
        confirmation_service = ConfirmationService(db_session)
        
        # Create source purchase order
        source_po = PurchaseOrder(
            po_number="PO-SOURCE-003",
            buyer_company_id=sample_companies["processor"].id,
            seller_company_id=sample_companies["originator"].id,
            product_id=sample_products["cpo"].id,
            quantity=Decimal("1000.0"),
            unit_price=Decimal("850.00"),
            total_amount=Decimal("850000.00"),
            unit="KGM",
            delivery_date=date.today() + timedelta(days=30),
            delivery_location="Test Location",
            status="confirmed"
        )
        db_session.add(source_po)
        db_session.commit()
        
        # Create target purchase order
        target_po = PurchaseOrder(
            po_number="PO-TARGET-002",
            buyer_company_id=sample_companies["brand"].id,
            seller_company_id=sample_companies["processor"].id,
            product_id=sample_products["blend"].id,
            quantity=Decimal("1000.0"),
            unit_price=Decimal("900.00"),
            total_amount=Decimal("900000.00"),
            unit="KGM",
            delivery_date=date.today() + timedelta(days=30),
            delivery_location="Test Location",
            status="draft"
        )
        db_session.add(target_po)
        db_session.commit()
        
        # Create input materials with invalid percentage sum (only 90%)
        input_materials = [
            InputMaterialLink(
                source_po_id=source_po.id,
                quantity_used=Decimal("900.0"),
                percentage_contribution=90.0,  # Only 90%, should be 100%
                transformation_notes="Incomplete composition"
            )
        ]
        
        # Validate input materials
        request = InputMaterialValidationRequest(
            purchase_order_id=target_po.id,
            input_materials=input_materials
        )
        
        validation_response = confirmation_service.validate_input_materials(
            request, sample_companies["processor"].id
        )
        
        assert not validation_response.is_valid
        assert any("100%" in error for error in validation_response.errors)


class TestPurchaseOrderConfirmation:
    """Test purchase order confirmation with different interfaces."""

    def test_confirm_with_origin_data_interface(self, db_session, sample_companies, sample_products):
        """Test confirming purchase order with origin data interface."""
        confirmation_service = ConfirmationService(db_session)

        # Create purchase order with originator as seller
        po = PurchaseOrder(
            po_number="PO-CONFIRM-001",
            buyer_company_id=sample_companies["processor"].id,
            seller_company_id=sample_companies["originator"].id,
            product_id=sample_products["ffb"].id,
            quantity=Decimal("1000.0"),
            unit_price=Decimal("300.00"),
            total_amount=Decimal("300000.00"),
            unit="KGM",
            delivery_date=date.today() + timedelta(days=30),
            delivery_location="Test Location",
            status="draft"
        )
        db_session.add(po)
        db_session.commit()

        # Create confirmation data with origin data
        confirmation_data = PurchaseOrderConfirmation(
            confirmed_quantity=Decimal("1000.0"),
            confirmation_notes="Fresh fruit bunches confirmed for delivery",
            origin_data=OriginDataCapture(
                geographic_coordinates=GeographicCoordinates(
                    latitude=2.5,
                    longitude=101.5,
                    accuracy_meters=5.0
                ),
                certifications=["RSPO", "NDPE"],
                harvest_date=date.today() - timedelta(days=3),
                farm_identification="FARM-KAL-001",
                batch_number="HARVEST-2024-001"
            )
        )

        # Confirm purchase order
        confirmation_response = confirmation_service.confirm_purchase_order(
            po.id,
            confirmation_data,
            sample_companies["originator"].id
        )

        assert confirmation_response.confirmation_status == "confirmed"
        assert confirmation_response.interface_type == ConfirmationInterfaceType.ORIGIN_DATA_INTERFACE
        assert len(confirmation_response.next_steps) > 0

        # Verify purchase order was updated
        db_session.refresh(po)
        assert po.status == "confirmed"
        assert po.origin_data is not None
        assert "geographic_coordinates" in po.origin_data

    def test_confirm_with_transformation_interface(self, db_session, sample_companies, sample_products):
        """Test confirming purchase order with transformation interface."""
        confirmation_service = ConfirmationService(db_session)

        # Create source purchase orders
        source_po1 = PurchaseOrder(
            po_number="PO-SOURCE-TRANS-001",
            buyer_company_id=sample_companies["processor"].id,
            seller_company_id=sample_companies["originator"].id,
            product_id=sample_products["cpo"].id,
            quantity=Decimal("800.0"),
            unit_price=Decimal("850.00"),
            total_amount=Decimal("680000.00"),
            unit="KGM",
            delivery_date=date.today() + timedelta(days=30),
            delivery_location="Test Location",
            status="confirmed"
        )

        source_po2 = PurchaseOrder(
            po_number="PO-SOURCE-TRANS-002",
            buyer_company_id=sample_companies["processor"].id,
            seller_company_id=sample_companies["originator"].id,
            product_id=sample_products["pko"].id,
            quantity=Decimal("200.0"),
            unit_price=Decimal("1200.00"),
            total_amount=Decimal("240000.00"),
            unit="KGM",
            delivery_date=date.today() + timedelta(days=30),
            delivery_location="Test Location",
            status="confirmed"
        )

        db_session.add_all([source_po1, source_po2])
        db_session.commit()

        # Create target purchase order
        target_po = PurchaseOrder(
            po_number="PO-CONFIRM-TRANS-001",
            buyer_company_id=sample_companies["brand"].id,
            seller_company_id=sample_companies["processor"].id,
            product_id=sample_products["blend"].id,
            quantity=Decimal("1000.0"),
            unit_price=Decimal("900.00"),
            total_amount=Decimal("900000.00"),
            unit="KGM",
            delivery_date=date.today() + timedelta(days=30),
            delivery_location="Test Location",
            status="draft"
        )
        db_session.add(target_po)
        db_session.commit()

        # Create confirmation data with transformation data
        confirmation_data = PurchaseOrderConfirmation(
            confirmed_quantity=Decimal("1000.0"),
            confirmed_composition={"palm_oil": 80.0, "palm_kernel_oil": 20.0},
            confirmation_notes="Blend processed and ready for shipment",
            transformation_data=TransformationDataCapture(
                input_materials=[
                    InputMaterialLink(
                        source_po_id=source_po1.id,
                        quantity_used=Decimal("800.0"),
                        percentage_contribution=80.0,
                        transformation_notes="Primary palm oil component"
                    ),
                    InputMaterialLink(
                        source_po_id=source_po2.id,
                        quantity_used=Decimal("200.0"),
                        percentage_contribution=20.0,
                        transformation_notes="Palm kernel oil component"
                    )
                ],
                transformation_process="Blending of refined palm oil and palm kernel oil",
                facility_location="Processing Plant A",
                processing_date=date.today(),
                yield_percentage=100.0
            )
        )

        # Confirm purchase order
        confirmation_response = confirmation_service.confirm_purchase_order(
            target_po.id,
            confirmation_data,
            sample_companies["processor"].id
        )

        assert confirmation_response.confirmation_status == "confirmed"
        assert confirmation_response.interface_type == ConfirmationInterfaceType.TRANSFORMATION_INTERFACE

        # Verify purchase order was updated
        db_session.refresh(target_po)
        assert target_po.status == "confirmed"
        assert target_po.input_materials is not None
        assert len(target_po.input_materials) == 2
        assert target_po.composition == {"palm_oil": 80.0, "palm_kernel_oil": 20.0}

    def test_confirm_fails_with_wrong_interface_data(self, db_session, sample_companies, sample_products):
        """Test that confirmation fails when wrong interface data is provided."""
        confirmation_service = ConfirmationService(db_session)

        # Create purchase order that requires origin data interface
        po = PurchaseOrder(
            po_number="PO-FAIL-001",
            buyer_company_id=sample_companies["processor"].id,
            seller_company_id=sample_companies["originator"].id,
            product_id=sample_products["ffb"].id,
            quantity=Decimal("1000.0"),
            unit_price=Decimal("300.00"),
            total_amount=Decimal("300000.00"),
            unit="KGM",
            delivery_date=date.today() + timedelta(days=30),
            delivery_location="Test Location",
            status="draft"
        )
        db_session.add(po)
        db_session.commit()

        # Try to confirm with transformation data (wrong interface)
        confirmation_data = PurchaseOrderConfirmation(
            confirmed_quantity=Decimal("1000.0"),
            transformation_data=TransformationDataCapture(
                input_materials=[
                    InputMaterialLink(
                        source_po_id=uuid4(),
                        quantity_used=Decimal("1000.0"),
                        percentage_contribution=100.0
                    )
                ],
                transformation_process="Invalid for this interface"
            )
        )

        # Confirmation should fail
        with pytest.raises(Exception) as exc_info:
            confirmation_service.confirm_purchase_order(
                po.id,
                confirmation_data,
                sample_companies["originator"].id
            )
        assert "Origin data is required" in str(exc_info.value)

    def test_only_seller_can_confirm_purchase_order(self, db_session, sample_companies, sample_products):
        """Test that only seller company can confirm purchase order."""
        confirmation_service = ConfirmationService(db_session)

        # Create purchase order
        po = PurchaseOrder(
            po_number="PO-ACCESS-001",
            buyer_company_id=sample_companies["brand"].id,
            seller_company_id=sample_companies["processor"].id,
            product_id=sample_products["cpo"].id,
            quantity=Decimal("1000.0"),
            unit_price=Decimal("850.00"),
            total_amount=Decimal("850000.00"),
            unit="KGM",
            delivery_date=date.today() + timedelta(days=30),
            delivery_location="Test Location",
            status="draft"
        )
        db_session.add(po)
        db_session.commit()

        # Create basic confirmation data
        confirmation_data = PurchaseOrderConfirmation(
            confirmed_quantity=Decimal("1000.0"),
            confirmation_notes="Attempting to confirm as buyer"
        )

        # Buyer should not be able to confirm
        with pytest.raises(Exception) as exc_info:
            confirmation_service.confirm_purchase_order(
                po.id,
                confirmation_data,
                sample_companies["brand"].id  # Buyer trying to confirm
            )
        assert "Only the seller company can confirm" in str(exc_info.value)

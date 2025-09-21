"""
Unit tests for compliance services.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from uuid import uuid4, UUID
from decimal import Decimal
from datetime import datetime, date

from app.services.compliance import (
    ComplianceService, ComplianceDataMapper, ComplianceTemplateEngine,
    PurchaseOrderNotFoundError, CompanyNotFoundError, ProductNotFoundError,
    ComplianceDataError, RiskAssessmentError, MassBalanceError, ValidationError
)
from app.schemas.compliance import ComplianceReportRequest, EUDRReportData, RSPOReportData


class TestComplianceDataMapper:
    """Test cases for ComplianceDataMapper."""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        return Mock()
    
    @pytest.fixture
    def data_mapper(self, mock_db):
        """Create ComplianceDataMapper instance."""
        return ComplianceDataMapper(mock_db)
    
    @pytest.fixture
    def sample_po_data(self):
        """Sample purchase order data."""
        po_id = uuid4()
        company_id = uuid4()
        product_id = uuid4()
        
        po = Mock()
        po.id = po_id
        po.buyer_company_id = company_id
        po.seller_company_id = uuid4()
        po.product_id = product_id
        po.quantity = Decimal('1000.0')
        po.unit = 'kg'
        
        buyer_company = Mock()
        buyer_company.id = company_id
        buyer_company.name = 'Test Company'
        buyer_company.registration_number = 'REG123'
        buyer_company.address = '123 Test St'
        buyer_company.country = 'Testland'
        buyer_company.tax_id = 'TAX123'
        buyer_company.location_coordinates = {'lat': 1.0, 'lng': 2.0}
        
        seller_company = Mock()
        seller_company.id = uuid4()
        seller_company.name = 'Seller Company'
        seller_company.company_type = 'mill_processor'
        seller_company.address = '456 Seller St'
        seller_company.location_coordinates = {'lat': 3.0, 'lng': 4.0}
        
        product = Mock()
        product.id = product_id
        product.name = 'Test Product'
        product.hs_code = '1511.10.00'
        product.quantity = Decimal('1000.0')
        product.default_unit = 'kg'
        product.certification_number = 'CERT123'
        product.certification_expiry = date.today()
        product.certification_type = 'RSPO'
        product.certification_body = 'RSPO Body'
        
        po.buyer_company = buyer_company
        po.seller_company = seller_company
        po.product = product
        
        return {
            'po': po,
            'po_id': po_id,
            'company_id': company_id,
            'product_id': product_id
        }
    
    def test_map_po_to_eudr_data_success(self, data_mapper, mock_db, sample_po_data):
        """Test successful EUDR data mapping."""
        # Setup
        po_data = sample_po_data
        mock_db.query.return_value.options.return_value.filter.return_value.first.return_value = po_data['po']
        
        # Execute
        result = data_mapper.map_po_to_eudr_data(po_data['po_id'])
        
        # Assert
        assert isinstance(result, EUDRReportData)
        assert result.operator.name == 'Test Company'
        assert result.product.hs_code == '1511.10.00'
        assert result.product.quantity == Decimal('1000.0')
        assert len(result.supply_chain) == 2
        assert result.trace_depth == 2
    
    def test_map_po_to_eudr_data_po_not_found(self, data_mapper, mock_db):
        """Test EUDR mapping when PO is not found."""
        # Setup
        po_id = uuid4()
        mock_db.query.return_value.options.return_value.filter.return_value.first.return_value = None
        
        # Execute & Assert
        with pytest.raises(PurchaseOrderNotFoundError):
            data_mapper.map_po_to_eudr_data(po_id)
    
    def test_map_po_to_rspo_data_success(self, data_mapper, mock_db, sample_po_data):
        """Test successful RSPO data mapping."""
        # Setup
        po_data = sample_po_data
        mock_db.query.return_value.options.return_value.filter.return_value.first.return_value = po_data['po']
        
        # Execute
        result = data_mapper.map_po_to_rspo_data(po_data['po_id'])
        
        # Assert
        assert isinstance(result, RSPOReportData)
        assert result.certification.certificate_number == 'CERT123'
        assert result.certification.certification_type == 'RSPO'
        assert result.mass_balance.input_quantity == Decimal('0.0')
        assert result.mass_balance.output_quantity == Decimal('0.0')
    
    def test_validate_risk_score_valid(self, data_mapper):
        """Test risk score validation with valid values."""
        # Test valid scores
        assert data_mapper.validator.validate_risk_score(0.0) == Decimal('0.0')
        assert data_mapper.validator.validate_risk_score(0.5) == Decimal('0.5')
        assert data_mapper.validator.validate_risk_score(1.0) == Decimal('1.0')
    
    def test_validate_risk_score_invalid(self, data_mapper):
        """Test risk score validation with invalid values."""
        # Test invalid scores
        with pytest.raises(ValidationError):
            data_mapper.validator.validate_risk_score(-0.1)
        
        with pytest.raises(ValidationError):
            data_mapper.validator.validate_risk_score(1.1)
        
        with pytest.raises(ValidationError):
            data_mapper.validator.validate_risk_score('invalid')


class TestComplianceTemplateEngine:
    """Test cases for ComplianceTemplateEngine."""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        return Mock()
    
    @pytest.fixture
    def template_engine(self, mock_db):
        """Create ComplianceTemplateEngine instance."""
        return ComplianceTemplateEngine(mock_db)
    
    def test_get_template_eudr_success(self, template_engine, mock_db):
        """Test successful EUDR template retrieval."""
        # Setup
        template_record = Mock()
        template_record.template_content = '<?xml version="1.0"?><EUDR_Report></EUDR_Report>'
        mock_db.query.return_value.filter.return_value.first.return_value = template_record
        
        # Execute
        template = template_engine._get_template('EUDR')
        
        # Assert
        assert template is not None
        assert hasattr(template, 'render')
    
    def test_get_template_not_found(self, template_engine, mock_db):
        """Test template retrieval when not found in database."""
        # Setup
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Execute
        template = template_engine._get_template('EUDR')
        
        # Assert
        assert template is not None
        assert hasattr(template, 'render')
    
    def test_generate_eudr_report_success(self, template_engine):
        """Test successful EUDR report generation."""
        # Setup
        eudr_data = {
            'operator': {'name': 'Test Company'},
            'product': {'hs_code': '1511.10.00', 'description': 'Test Product'},
            'supply_chain': [],
            'risk_assessment': {'deforestation_risk': Decimal('0.5')},
            'trace_path': 'Test Path',
            'trace_depth': 1,
            'generated_at': datetime.now()
        }
        
        # Execute
        result = template_engine.generate_eudr_report(eudr_data)
        
        # Assert
        assert isinstance(result, bytes)
        assert b'EUDR_Report' in result
        assert b'Test Company' in result
    
    def test_generate_rspo_report_success(self, template_engine):
        """Test successful RSPO report generation."""
        # Setup
        rspo_data = {
            'certification': {'certificate_number': 'CERT123'},
            'supply_chain': [],
            'mass_balance': {'input_quantity': Decimal('1000.0')},
            'sustainability': {'ghg_emissions': Decimal('0.0')},
            'trace_path': 'Test Path',
            'trace_depth': 1,
            'generated_at': datetime.now()
        }
        
        # Execute
        result = template_engine.generate_rspo_report(rspo_data)
        
        # Assert
        assert isinstance(result, bytes)
        assert b'RSPO_Report' in result
        assert b'CERT123' in result


class TestComplianceService:
    """Test cases for ComplianceService."""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        return Mock()
    
    @pytest.fixture
    def mock_data_mapper(self):
        """Mock ComplianceDataMapper."""
        return Mock()
    
    @pytest.fixture
    def mock_template_engine(self):
        """Mock ComplianceTemplateEngine."""
        return Mock()
    
    @pytest.fixture
    def compliance_service(self, mock_db, mock_data_mapper, mock_template_engine):
        """Create ComplianceService instance."""
        return ComplianceService(
            db=mock_db,
            data_mapper=mock_data_mapper,
            template_engine=mock_template_engine
        )
    
    @pytest.fixture
    def sample_request(self):
        """Sample compliance report request."""
        return ComplianceReportRequest(
            po_id=uuid4(),
            regulation_type='EUDR',
            include_risk_assessment=True,
            include_mass_balance=True
        )
    
    def test_generate_compliance_report_eudr_success(self, compliance_service, sample_request, mock_data_mapper, mock_template_engine, mock_db):
        """Test successful EUDR compliance report generation."""
        # Setup
        eudr_data = Mock()
        eudr_data.operator = Mock()
        eudr_data.product = Mock()
        eudr_data.supply_chain = []
        eudr_data.risk_assessment = Mock()
        eudr_data.trace_path = 'Test Path'
        eudr_data.trace_depth = 1
        eudr_data.generated_at = datetime.now()
        
        mock_data_mapper.map_po_to_eudr_data.return_value = eudr_data
        mock_template_engine.generate_eudr_report.return_value = b'<EUDR_Report></EUDR_Report>'
        
        # Mock database operations
        template = Mock()
        template.id = uuid4()
        mock_db.query.return_value.filter.return_value.first.return_value = template
        
        po = Mock()
        po.buyer_company_id = uuid4()
        mock_db.query.return_value.filter.return_value.first.return_value = po
        
        # Mock report creation
        report = Mock()
        report.id = uuid4()
        report.generated_at = datetime.now()
        report.file_size = 100
        report.status = 'GENERATED'
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None
        
        # Execute
        result = compliance_service.generate_compliance_report(sample_request)
        
        # Assert
        assert result.regulation_type == 'EUDR'
        assert result.po_id == sample_request.po_id
        assert result.status == 'GENERATED'
        mock_data_mapper.map_po_to_eudr_data.assert_called_once_with(sample_request.po_id)
        mock_template_engine.generate_eudr_report.assert_called_once()
    
    def test_generate_compliance_report_rspo_success(self, compliance_service, mock_data_mapper, mock_template_engine, mock_db):
        """Test successful RSPO compliance report generation."""
        # Setup
        request = ComplianceReportRequest(
            po_id=uuid4(),
            regulation_type='RSPO',
            include_risk_assessment=True,
            include_mass_balance=True
        )
        
        rspo_data = Mock()
        rspo_data.certification = Mock()
        rspo_data.supply_chain = []
        rspo_data.mass_balance = Mock()
        rspo_data.sustainability = Mock()
        rspo_data.trace_path = 'Test Path'
        rspo_data.trace_depth = 1
        rspo_data.generated_at = datetime.now()
        
        mock_data_mapper.map_po_to_rspo_data.return_value = rspo_data
        mock_template_engine.generate_rspo_report.return_value = b'<RSPO_Report></RSPO_Report>'
        
        # Mock database operations
        template = Mock()
        template.id = uuid4()
        mock_db.query.return_value.filter.return_value.first.return_value = template
        
        po = Mock()
        po.buyer_company_id = uuid4()
        mock_db.query.return_value.filter.return_value.first.return_value = po
        
        # Mock report creation
        report = Mock()
        report.id = uuid4()
        report.generated_at = datetime.now()
        report.file_size = 100
        report.status = 'GENERATED'
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None
        
        # Execute
        result = compliance_service.generate_compliance_report(request)
        
        # Assert
        assert result.regulation_type == 'RSPO'
        assert result.po_id == request.po_id
        assert result.status == 'GENERATED'
        mock_data_mapper.map_po_to_rspo_data.assert_called_once_with(request.po_id)
        mock_template_engine.generate_rspo_report.assert_called_once()
    
    def test_generate_compliance_report_invalid_regulation_type(self, compliance_service):
        """Test compliance report generation with invalid regulation type."""
        # Setup
        request = ComplianceReportRequest(
            po_id=uuid4(),
            regulation_type='INVALID',
            include_risk_assessment=True,
            include_mass_balance=True
        )
        
        # Execute & Assert
        with pytest.raises(ComplianceDataError):
            compliance_service.generate_compliance_report(request)
    
    def test_validate_request_missing_po_id(self, compliance_service):
        """Test request validation with missing PO ID."""
        # Setup
        request = ComplianceReportRequest(
            po_id=None,  # Invalid
            regulation_type='EUDR',
            include_risk_assessment=True,
            include_mass_balance=True
        )
        
        # Execute & Assert
        with pytest.raises(ComplianceDataError):
            compliance_service._validate_request(request)
    
    def test_validate_request_missing_regulation_type(self, compliance_service):
        """Test request validation with missing regulation type."""
        # Setup
        request = ComplianceReportRequest(
            po_id=uuid4(),
            regulation_type=None,  # Invalid
            include_risk_assessment=True,
            include_mass_balance=True
        )
        
        # Execute & Assert
        with pytest.raises(ComplianceDataError):
            compliance_service._validate_request(request)


class TestDataValidator:
    """Test cases for DataValidator."""
    
    @pytest.fixture
    def validator(self):
        """Create DataValidator instance."""
        return DataValidator()
    
    def test_validate_risk_score_valid(self, validator):
        """Test risk score validation with valid values."""
        assert validator.validate_risk_score(0.0) == Decimal('0.0')
        assert validator.validate_risk_score(0.5) == Decimal('0.5')
        assert validator.validate_risk_score(1.0) == Decimal('1.0')
        assert validator.validate_risk_score('0.7') == Decimal('0.7')
    
    def test_validate_risk_score_invalid(self, validator):
        """Test risk score validation with invalid values."""
        with pytest.raises(ValidationError):
            validator.validate_risk_score(-0.1)
        
        with pytest.raises(ValidationError):
            validator.validate_risk_score(1.1)
        
        with pytest.raises(ValidationError):
            validator.validate_risk_score('invalid')
    
    def test_validate_hs_code_valid(self, validator):
        """Test HS code validation with valid codes."""
        assert validator.validate_hs_code('1511.10.00') == '1511.10.00'
        assert validator.validate_hs_code('1511.10') == '1511.10'
        assert validator.validate_hs_code('151110') == '151110'
    
    def test_validate_hs_code_invalid(self, validator):
        """Test HS code validation with invalid codes."""
        with pytest.raises(ValidationError):
            validator.validate_hs_code('')
        
        with pytest.raises(ValidationError):
            validator.validate_hs_code('invalid')
        
        with pytest.raises(ValidationError):
            validator.validate_hs_code('123')
    
    def test_validate_quantity_valid(self, validator):
        """Test quantity validation with valid values."""
        assert validator.validate_quantity(100.0, 'test_quantity') == Decimal('100.0')
        assert validator.validate_quantity('50.5', 'test_quantity') == Decimal('50.5')
        assert validator.validate_quantity(Decimal('25.0'), 'test_quantity') == Decimal('25.0')
    
    def test_validate_quantity_invalid(self, validator):
        """Test quantity validation with invalid values."""
        with pytest.raises(ValidationError):
            validator.validate_quantity(0, 'test_quantity')
        
        with pytest.raises(ValidationError):
            validator.validate_quantity(-10, 'test_quantity')
        
        with pytest.raises(ValidationError):
            validator.validate_quantity('invalid', 'test_quantity')

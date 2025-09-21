"""
Unit tests for transformation template engines.

This module provides comprehensive unit tests for all template engines
following the modular architecture and SOLID principles.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from decimal import Decimal
from datetime import datetime, date
from uuid import uuid4

from app.models.transformation import TransformationType
from app.services.transformation.templates import (
    create_template_engine,
    create_plantation_template_engine,
    create_mill_template_engine,
    create_refinery_template_engine,
    create_manufacturer_template_engine
)
from app.services.transformation.templates.plantation_template import PlantationTemplateEngine
from app.services.transformation.templates.mill_template import MillTemplateEngine
from app.services.transformation.templates.refinery_template import RefineryTemplateEngine
from app.services.transformation.templates.manufacturer_template import ManufacturerTemplateEngine
from app.services.transformation.templates.orchestrator import TransformationTemplateOrchestrator
from app.services.transformation.exceptions import TemplateGenerationError, ValidationError


class TestPlantationTemplateEngine:
    """Test cases for PlantationTemplateEngine."""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        return Mock()
    
    @pytest.fixture
    def plantation_engine(self, mock_db):
        """Create PlantationTemplateEngine instance."""
        return PlantationTemplateEngine(mock_db)
    
    def test_get_template_harvest_success(self, plantation_engine):
        """Test successful template generation for harvest transformation."""
        # Arrange
        transformation_type = TransformationType.HARVEST
        company_type = "plantation_grower"
        input_batch_data = {
            "id": str(uuid4()),
            "product_id": str(uuid4()),
            "quantity": 1000.0,
            "unit": "kg"
        }
        
        # Act
        template = plantation_engine.get_template(
            transformation_type=transformation_type,
            company_type=company_type,
            input_batch_data=input_batch_data
        )
        
        # Assert
        assert template is not None
        assert template["transformation_type"] == "harvest"
        assert template["company_type"] == "plantation_grower"
        assert "role_specific_data" in template
        assert "plantation_data" in template["role_specific_data"]
        assert "quality_metrics" in template["role_specific_data"]
        assert "process_parameters" in template["role_specific_data"]
        assert "efficiency_metrics" in template["role_specific_data"]
        assert "location_data" in template["role_specific_data"]
        assert "weather_conditions" in template["role_specific_data"]
        assert "certifications" in template["role_specific_data"]
        assert "compliance_data" in template["role_specific_data"]
        assert "output_batch_suggestion" in template
    
    def test_get_template_wrong_transformation_type(self, plantation_engine):
        """Test template generation with wrong transformation type."""
        # Arrange
        transformation_type = TransformationType.MILLING
        company_type = "plantation_grower"
        
        # Act
        template = plantation_engine.get_template(
            transformation_type=transformation_type,
            company_type=company_type
        )
        
        # Assert
        assert template is not None
        assert template["transformation_type"] == "milling"
        assert "role_specific_data" not in template or not template["role_specific_data"]
    
    def test_get_template_invalid_company_type(self, plantation_engine):
        """Test template generation with invalid company type."""
        # Arrange
        transformation_type = TransformationType.HARVEST
        company_type = "invalid_type"
        
        # Act & Assert
        with pytest.raises(TemplateGenerationError):
            plantation_engine.get_template(
                transformation_type=transformation_type,
                company_type=company_type
            )
    
    def test_get_template_invalid_facility_id(self, plantation_engine):
        """Test template generation with invalid facility ID."""
        # Arrange
        transformation_type = TransformationType.HARVEST
        company_type = "plantation_grower"
        facility_id = "invalid-facility-id"
        
        # Act & Assert
        with pytest.raises(TemplateGenerationError):
            plantation_engine.get_template(
                transformation_type=transformation_type,
                company_type=company_type,
                facility_id=facility_id
            )
    
    def test_plantation_harvest_data_structure(self, plantation_engine):
        """Test plantation harvest data structure."""
        # Arrange
        input_batch_data = {
            "id": str(uuid4()),
            "product_id": str(uuid4()),
            "quantity": 1000.0,
            "unit": "kg"
        }
        
        # Act
        harvest_data = plantation_engine._get_plantation_harvest_data(input_batch_data, {})
        
        # Assert
        assert "harvest_date" in harvest_data
        assert "harvest_method" in harvest_data
        assert "fruit_bunches_harvested" in harvest_data
        assert "estimated_oil_yield" in harvest_data
        assert "harvest_team_size" in harvest_data
        assert "harvest_duration_hours" in harvest_data
        assert "fruit_ripeness_percentage" in harvest_data
        assert "harvest_efficiency" in harvest_data
        assert "equipment_used" in harvest_data
        assert "harvest_notes" in harvest_data
        assert "quality_grade" in harvest_data
        assert "sustainability_practices" in harvest_data
    
    def test_quality_metrics_structure(self, plantation_engine):
        """Test quality metrics structure."""
        # Act
        quality_metrics = plantation_engine._get_harvest_quality_metrics({})
        
        # Assert
        assert "moisture_content" in quality_metrics
        assert "ffa_content" in quality_metrics
        assert "color_grade" in quality_metrics
        assert "purity_percentage" in quality_metrics
        assert "oil_content_percentage" in quality_metrics
        assert "kernel_content_percentage" in quality_metrics
        assert "mesocarp_content_percentage" in quality_metrics
        assert "shell_content_percentage" in quality_metrics
        assert "fresh_fruit_bunch_quality" in quality_metrics
        assert "oil_extraction_potential" in quality_metrics


class TestMillTemplateEngine:
    """Test cases for MillTemplateEngine."""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        return Mock()
    
    @pytest.fixture
    def mill_engine(self, mock_db):
        """Create MillTemplateEngine instance."""
        return MillTemplateEngine(mock_db)
    
    def test_get_template_milling_success(self, mill_engine):
        """Test successful template generation for milling transformation."""
        # Arrange
        transformation_type = TransformationType.MILLING
        company_type = "mill_processor"
        input_batch_data = {
            "id": str(uuid4()),
            "product_id": str(uuid4()),
            "quantity": 1000.0,
            "unit": "kg"
        }
        
        # Act
        template = mill_engine.get_template(
            transformation_type=transformation_type,
            company_type=company_type,
            input_batch_data=input_batch_data
        )
        
        # Assert
        assert template is not None
        assert template["transformation_type"] == "milling"
        assert template["company_type"] == "mill_processor"
        assert "role_specific_data" in template
        assert "mill_data" in template["role_specific_data"]
        assert "quality_metrics" in template["role_specific_data"]
        assert "process_parameters" in template["role_specific_data"]
        assert "efficiency_metrics" in template["role_specific_data"]
        assert "location_data" in template["role_specific_data"]
        assert "weather_conditions" in template["role_specific_data"]
        assert "certifications" in template["role_specific_data"]
        assert "compliance_data" in template["role_specific_data"]
        assert "output_batch_suggestion" in template
    
    def test_mill_processing_data_structure(self, mill_engine):
        """Test mill processing data structure."""
        # Arrange
        input_batch_data = {
            "id": str(uuid4()),
            "product_id": str(uuid4()),
            "quantity": 1000.0,
            "unit": "kg"
        }
        
        # Act
        mill_data = mill_engine._get_mill_processing_data(input_batch_data, {})
        
        # Assert
        assert "processing_date" in mill_data
        assert "processing_method" in mill_data
        assert "fresh_fruit_bunches_processed" in mill_data
        assert "crude_palm_oil_produced" in mill_data
        assert "palm_kernel_produced" in mill_data
        assert "processing_capacity_tonnes_per_hour" in mill_data
        assert "extraction_rate_percentage" in mill_data
        assert "sterilization_time_minutes" in mill_data
        assert "threshing_efficiency_percentage" in mill_data
        assert "pressing_pressure_bar" in mill_data
        assert "oil_clarification_method" in mill_data
        assert "equipment_used" in mill_data
        assert "processing_notes" in mill_data
        assert "quality_grade" in mill_data
        assert "sustainability_practices" in mill_data


class TestRefineryTemplateEngine:
    """Test cases for RefineryTemplateEngine."""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        return Mock()
    
    @pytest.fixture
    def refinery_engine(self, mock_db):
        """Create RefineryTemplateEngine instance."""
        return RefineryTemplateEngine(mock_db)
    
    def test_get_template_refining_success(self, refinery_engine):
        """Test successful template generation for refining transformation."""
        # Arrange
        transformation_type = TransformationType.REFINING
        company_type = "refinery_crusher"
        input_batch_data = {
            "id": str(uuid4()),
            "product_id": str(uuid4()),
            "quantity": 1000.0,
            "unit": "kg"
        }
        
        # Act
        template = refinery_engine.get_template(
            transformation_type=transformation_type,
            company_type=company_type,
            input_batch_data=input_batch_data
        )
        
        # Assert
        assert template is not None
        assert template["transformation_type"] == "refining"
        assert template["company_type"] == "refinery_crusher"
        assert "role_specific_data" in template
        assert "refinery_data" in template["role_specific_data"]
        assert "quality_metrics" in template["role_specific_data"]
        assert "process_parameters" in template["role_specific_data"]
        assert "efficiency_metrics" in template["role_specific_data"]
        assert "location_data" in template["role_specific_data"]
        assert "weather_conditions" in template["role_specific_data"]
        assert "certifications" in template["role_specific_data"]
        assert "compliance_data" in template["role_specific_data"]
        assert "output_batch_suggestion" in template
    
    def test_refinery_processing_data_structure(self, refinery_engine):
        """Test refinery processing data structure."""
        # Arrange
        input_batch_data = {
            "id": str(uuid4()),
            "product_id": str(uuid4()),
            "quantity": 1000.0,
            "unit": "kg"
        }
        
        # Act
        refinery_data = refinery_engine._get_refinery_processing_data(input_batch_data, {})
        
        # Assert
        assert "processing_date" in refinery_data
        assert "processing_method" in refinery_data
        assert "crude_palm_oil_input" in refinery_data
        assert "refined_palm_oil_output" in refinery_data
        assert "refining_loss_percentage" in refinery_data
        assert "processing_capacity_tonnes_per_day" in refinery_data
        assert "refining_efficiency_percentage" in refinery_data
        assert "degumming_method" in refinery_data
        assert "neutralization_method" in refinery_data
        assert "bleaching_method" in refinery_data
        assert "deodorization_method" in refinery_data
        assert "fractionation_method" in refinery_data
        assert "equipment_used" in refinery_data
        assert "processing_notes" in refinery_data
        assert "quality_grade" in refinery_data
        assert "sustainability_practices" in refinery_data


class TestManufacturerTemplateEngine:
    """Test cases for ManufacturerTemplateEngine."""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        return Mock()
    
    @pytest.fixture
    def manufacturer_engine(self, mock_db):
        """Create ManufacturerTemplateEngine instance."""
        return ManufacturerTemplateEngine(mock_db)
    
    def test_get_template_manufacturing_success(self, manufacturer_engine):
        """Test successful template generation for manufacturing transformation."""
        # Arrange
        transformation_type = TransformationType.MANUFACTURING
        company_type = "manufacturer"
        input_batch_data = {
            "id": str(uuid4()),
            "product_id": str(uuid4()),
            "quantity": 1000.0,
            "unit": "kg"
        }
        
        # Act
        template = manufacturer_engine.get_template(
            transformation_type=transformation_type,
            company_type=company_type,
            input_batch_data=input_batch_data
        )
        
        # Assert
        assert template is not None
        assert template["transformation_type"] == "manufacturing"
        assert template["company_type"] == "manufacturer"
        assert "role_specific_data" in template
        assert "manufacturer_data" in template["role_specific_data"]
        assert "quality_metrics" in template["role_specific_data"]
        assert "process_parameters" in template["role_specific_data"]
        assert "efficiency_metrics" in template["role_specific_data"]
        assert "location_data" in template["role_specific_data"]
        assert "weather_conditions" in template["role_specific_data"]
        assert "certifications" in template["role_specific_data"]
        assert "compliance_data" in template["role_specific_data"]
        assert "output_batch_suggestion" in template
    
    def test_manufacturer_processing_data_structure(self, manufacturer_engine):
        """Test manufacturer processing data structure."""
        # Arrange
        input_batch_data = {
            "id": str(uuid4()),
            "product_id": str(uuid4()),
            "quantity": 1000.0,
            "unit": "kg"
        }
        
        # Act
        manufacturer_data = manufacturer_engine._get_manufacturer_processing_data(input_batch_data, {})
        
        # Assert
        assert "processing_date" in manufacturer_data
        assert "processing_method" in manufacturer_data
        assert "refined_oil_input" in manufacturer_data
        assert "finished_products_output" in manufacturer_data
        assert "processing_loss_percentage" in manufacturer_data
        assert "processing_capacity_tonnes_per_day" in manufacturer_data
        assert "manufacturing_efficiency_percentage" in manufacturer_data
        assert "formulation_method" in manufacturer_data
        assert "mixing_method" in manufacturer_data
        assert "packaging_method" in manufacturer_data
        assert "quality_control_method" in manufacturer_data
        assert "equipment_used" in manufacturer_data
        assert "processing_notes" in manufacturer_data
        assert "product_grade" in manufacturer_data
        assert "sustainability_practices" in manufacturer_data


class TestTransformationTemplateOrchestrator:
    """Test cases for TransformationTemplateOrchestrator."""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        return Mock()
    
    @pytest.fixture
    def orchestrator(self, mock_db):
        """Create TransformationTemplateOrchestrator instance."""
        return TransformationTemplateOrchestrator(mock_db)
    
    def test_get_template_plantation_success(self, orchestrator):
        """Test successful template generation for plantation through orchestrator."""
        # Arrange
        transformation_type = TransformationType.HARVEST
        company_type = "plantation_grower"
        input_batch_data = {
            "id": str(uuid4()),
            "product_id": str(uuid4()),
            "quantity": 1000.0,
            "unit": "kg"
        }
        
        # Act
        template = orchestrator.get_template(
            transformation_type=transformation_type,
            company_type=company_type,
            input_batch_data=input_batch_data
        )
        
        # Assert
        assert template is not None
        assert template["transformation_type"] == "harvest"
        assert template["company_type"] == "plantation_grower"
        assert "orchestration_metadata" in template
        assert "generated_by" in template["orchestration_metadata"]
        assert "generation_timestamp" in template["orchestration_metadata"]
        assert "template_version" in template["orchestration_metadata"]
        assert "orchestrator_version" in template["orchestration_metadata"]
    
    def test_get_template_invalid_company_type(self, orchestrator):
        """Test template generation with invalid company type through orchestrator."""
        # Arrange
        transformation_type = TransformationType.HARVEST
        company_type = "invalid_type"
        
        # Act & Assert
        with pytest.raises(TemplateGenerationError):
            orchestrator.get_template(
                transformation_type=transformation_type,
                company_type=company_type
            )
    
    def test_get_available_company_types(self, orchestrator):
        """Test getting available company types."""
        # Act
        company_types = orchestrator.get_available_company_types()
        
        # Assert
        assert isinstance(company_types, list)
        assert "plantation_grower" in company_types
        assert "mill_processor" in company_types
        assert "refinery_crusher" in company_types
        assert "manufacturer" in company_types
    
    def test_get_engine_info(self, orchestrator):
        """Test getting engine information."""
        # Act
        engine_info = orchestrator.get_engine_info()
        
        # Assert
        assert "available_engines" in engine_info
        assert "total_engines" in engine_info
        assert "orchestrator_version" in engine_info
        assert engine_info["total_engines"] == 4
    
    def test_validate_company_type(self, orchestrator):
        """Test company type validation."""
        # Act & Assert
        assert orchestrator.validate_company_type("plantation_grower") is True
        assert orchestrator.validate_company_type("mill_processor") is True
        assert orchestrator.validate_company_type("refinery_crusher") is True
        assert orchestrator.validate_company_type("manufacturer") is True
        assert orchestrator.validate_company_type("invalid_type") is False
    
    def test_get_supported_transformation_types(self, orchestrator):
        """Test getting supported transformation types."""
        # Act & Assert
        plantation_types = orchestrator.get_supported_transformation_types("plantation_grower")
        assert TransformationType.HARVEST in plantation_types
        
        mill_types = orchestrator.get_supported_transformation_types("mill_processor")
        assert TransformationType.MILLING in mill_types
        
        refinery_types = orchestrator.get_supported_transformation_types("refinery_crusher")
        assert TransformationType.REFINING in refinery_types
        
        manufacturer_types = orchestrator.get_supported_transformation_types("manufacturer")
        assert TransformationType.MANUFACTURING in manufacturer_types
        
        invalid_types = orchestrator.get_supported_transformation_types("invalid_type")
        assert invalid_types == []
    
    def test_get_template_metadata(self, orchestrator):
        """Test getting template metadata."""
        # Act
        metadata = orchestrator.get_template_metadata("plantation_grower")
        
        # Assert
        assert "company_type" in metadata
        assert "engine_class" in metadata
        assert "supported_transformation_types" in metadata
        assert "template_capabilities" in metadata
        assert metadata["company_type"] == "plantation_grower"
        assert "PlantationTemplateEngine" in metadata["engine_class"]


class TestTemplateEngineFactory:
    """Test cases for template engine factory functions."""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        return Mock()
    
    def test_create_template_engine(self, mock_db):
        """Test creating template engine through factory."""
        # Act
        engine = create_template_engine(mock_db)
        
        # Assert
        assert isinstance(engine, TransformationTemplateOrchestrator)
    
    def test_create_plantation_template_engine(self):
        """Test creating plantation template engine through factory."""
        # Act
        engine = create_plantation_template_engine()
        
        # Assert
        assert isinstance(engine, PlantationTemplateEngine)
    
    def test_create_mill_template_engine(self):
        """Test creating mill template engine through factory."""
        # Act
        engine = create_mill_template_engine()
        
        # Assert
        assert isinstance(engine, MillTemplateEngine)
    
    def test_create_refinery_template_engine(self):
        """Test creating refinery template engine through factory."""
        # Act
        engine = create_refinery_template_engine()
        
        # Assert
        assert isinstance(engine, RefineryTemplateEngine)
    
    def test_create_manufacturer_template_engine(self):
        """Test creating manufacturer template engine through factory."""
        # Act
        engine = create_manufacturer_template_engine()
        
        # Assert
        assert isinstance(engine, ManufacturerTemplateEngine)


class TestTemplateEngineIntegration:
    """Integration tests for template engines."""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        return Mock()
    
    def test_end_to_end_template_generation(self, mock_db):
        """Test end-to-end template generation for all transformation types."""
        # Arrange
        orchestrator = create_template_engine(mock_db)
        input_batch_data = {
            "id": str(uuid4()),
            "product_id": str(uuid4()),
            "quantity": 1000.0,
            "unit": "kg"
        }
        
        # Test all transformation types
        test_cases = [
            (TransformationType.HARVEST, "plantation_grower"),
            (TransformationType.MILLING, "mill_processor"),
            (TransformationType.REFINING, "refinery_crusher"),
            (TransformationType.MANUFACTURING, "manufacturer")
        ]
        
        for transformation_type, company_type in test_cases:
            # Act
            template = orchestrator.get_template(
                transformation_type=transformation_type,
                company_type=company_type,
                input_batch_data=input_batch_data
            )
            
            # Assert
            assert template is not None
            assert template["transformation_type"] == transformation_type.value
            assert template["company_type"] == company_type
            assert "role_specific_data" in template
            assert "output_batch_suggestion" in template
            assert "orchestration_metadata" in template
    
    def test_template_consistency_across_engines(self, mock_db):
        """Test that templates are consistent across different engines."""
        # Arrange
        orchestrator = create_template_engine(mock_db)
        input_batch_data = {
            "id": str(uuid4()),
            "product_id": str(uuid4()),
            "quantity": 1000.0,
            "unit": "kg"
        }
        
        # Act - Generate templates multiple times
        templates = []
        for _ in range(3):
            template = orchestrator.get_template(
                transformation_type=TransformationType.HARVEST,
                company_type="plantation_grower",
                input_batch_data=input_batch_data
            )
            templates.append(template)
        
        # Assert - Templates should be consistent
        for i in range(1, len(templates)):
            assert templates[i]["transformation_type"] == templates[0]["transformation_type"]
            assert templates[i]["company_type"] == templates[0]["company_type"]
            assert "role_specific_data" in templates[i]
            assert "output_batch_suggestion" in templates[i]

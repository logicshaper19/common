"""
Origin data confirmation strategy.

Handles confirmation for originators and raw materials.
"""
from typing import Dict, Any, List
from datetime import datetime, date

from ..domain.models import (
    ConfirmationContext,
    InterfaceConfig,
    ValidationResult,
    GeographicCoordinates
)
from ..domain.enums import CertificationType
from .base import ConfirmationStrategy


class OriginDataStrategy(ConfirmationStrategy):
    """Strategy for origin data confirmation interface."""
    
    def get_interface_config(
        self, 
        context: ConfirmationContext,
        product: Dict[str, Any]
    ) -> InterfaceConfig:
        """Get configuration for origin data interface."""
        return InterfaceConfig(
            required_fields=[
                "geographic_coordinates",
                "certifications"
            ],
            optional_fields=[
                "harvest_date",
                "farm_identification", 
                "batch_number",
                "quality_parameters"
            ],
            validation_rules={
                "coordinates_required": True,
                "certifications_min": 0,
                "harvest_date_max_age_days": 365,
                "quality_parameters_schema": product.get("origin_data_requirements", {})
            },
            ui_config={
                "show_map_picker": True,
                "show_certification_selector": True,
                "show_harvest_date": product.get("category") == "raw_material",
                "show_quality_parameters": True,
                "certification_options": [cert.value for cert in CertificationType]
            }
        )
    
    def validate_confirmation_data(
        self,
        confirmation_data: Dict[str, Any],
        context: ConfirmationContext
    ) -> List[ValidationResult]:
        """Validate origin data confirmation."""
        results = []
        
        # Validate required fields
        config = self.get_interface_config(context, {})
        results.extend(
            self._validate_required_fields(confirmation_data, config.required_fields)
        )
        
        # Validate geographic coordinates
        if "geographic_coordinates" in confirmation_data:
            coord_results = self._validate_coordinates(
                confirmation_data["geographic_coordinates"]
            )
            results.extend(coord_results)
        
        # Validate certifications
        if "certifications" in confirmation_data:
            cert_results = self._validate_certifications(
                confirmation_data["certifications"]
            )
            results.extend(cert_results)
        
        # Validate harvest date
        if "harvest_date" in confirmation_data and confirmation_data["harvest_date"]:
            harvest_results = self._validate_harvest_date(
                confirmation_data["harvest_date"]
            )
            results.extend(harvest_results)
        
        return results
    
    def process_confirmation(
        self,
        confirmation_data: Dict[str, Any],
        context: ConfirmationContext
    ) -> Dict[str, Any]:
        """Process origin data confirmation."""
        update_data = {
            "status": "confirmed"
        }
        
        # Process origin data
        origin_data = {}
        
        if "geographic_coordinates" in confirmation_data:
            coords = confirmation_data["geographic_coordinates"]
            origin_data["geographic_coordinates"] = {
                "latitude": coords["latitude"],
                "longitude": coords["longitude"],
                "accuracy_meters": coords.get("accuracy_meters"),
                "elevation_meters": coords.get("elevation_meters")
            }
        
        if "certifications" in confirmation_data:
            origin_data["certifications"] = confirmation_data["certifications"]
        
        if "harvest_date" in confirmation_data:
            harvest_date = confirmation_data["harvest_date"]
            if isinstance(harvest_date, date):
                origin_data["harvest_date"] = harvest_date.isoformat()
            else:
                origin_data["harvest_date"] = harvest_date
        
        # Add optional fields
        for field in ["farm_identification", "batch_number", "quality_parameters"]:
            if field in confirmation_data:
                origin_data[field] = confirmation_data[field]
        
        update_data["origin_data"] = origin_data
        
        # Update confirmed quantity if provided
        if "confirmed_quantity" in confirmation_data:
            update_data["quantity"] = confirmation_data["confirmed_quantity"]
        
        return update_data
    
    def get_next_steps(
        self,
        context: ConfirmationContext
    ) -> List[str]:
        """Get next steps for origin data confirmation."""
        return [
            "Upload required compliance documents (RSPO certificates, environmental permits)",
            "Verify geographic coordinates accuracy",
            "Complete quality parameter documentation",
            "Await buyer acceptance of confirmed order"
        ]
    
    def get_document_requirements(
        self,
        context: ConfirmationContext
    ) -> List[Dict[str, Any]]:
        """Get document requirements for origin data interface."""
        return [
            {
                "name": "RSPO Certificate",
                "description": "Valid RSPO certification document",
                "file_types": ["pdf", "jpg", "png"],
                "is_required": True,
                "max_size_mb": 10
            },
            {
                "name": "Environmental Permit",
                "description": "Environmental compliance permit",
                "file_types": ["pdf"],
                "is_required": True,
                "max_size_mb": 5
            },
            {
                "name": "Quality Certificate",
                "description": "Product quality certification",
                "file_types": ["pdf", "jpg", "png"],
                "is_required": False,
                "max_size_mb": 5
            }
        ]
    
    def _validate_coordinates(
        self, 
        coords: Dict[str, Any]
    ) -> List[ValidationResult]:
        """Validate geographic coordinates."""
        results = []
        
        try:
            # Create coordinates object for validation
            geo_coords = GeographicCoordinates(
                latitude=coords.get("latitude"),
                longitude=coords.get("longitude"),
                accuracy_meters=coords.get("accuracy_meters"),
                elevation_meters=coords.get("elevation_meters")
            )
            
            # Check precision
            if not geo_coords.is_precise():
                results.append(
                    ValidationResult.warning(
                        message="GPS coordinates have low accuracy. Consider improving precision.",
                        field="geographic_coordinates",
                        suggestions=["Use a more precise GPS device", "Take multiple readings"]
                    )
                )
            
            results.append(
                ValidationResult.success("Geographic coordinates are valid")
            )
            
        except (ValueError, TypeError) as e:
            results.append(
                ValidationResult.error(
                    message=f"Invalid coordinates: {str(e)}",
                    field="geographic_coordinates",
                    code="INVALID_COORDINATES"
                )
            )
        
        return results
    
    def _validate_certifications(
        self, 
        certifications: List[str]
    ) -> List[ValidationResult]:
        """Validate certifications."""
        results = []
        
        if not isinstance(certifications, list):
            results.append(
                ValidationResult.error(
                    message="Certifications must be a list",
                    field="certifications",
                    code="INVALID_TYPE"
                )
            )
            return results
        
        valid_certs = {cert.value for cert in CertificationType}
        invalid_certs = [cert for cert in certifications if cert not in valid_certs]
        
        if invalid_certs:
            results.append(
                ValidationResult.warning(
                    message=f"Unknown certifications: {', '.join(invalid_certs)}",
                    field="certifications",
                    suggestions=["Use standard certification names", "Contact support for new certifications"]
                )
            )
        
        if len(certifications) == 0:
            results.append(
                ValidationResult.warning(
                    message="No certifications provided. Consider adding relevant certifications.",
                    field="certifications",
                    suggestions=["Add RSPO certification", "Add environmental certifications"]
                )
            )
        
        return results
    
    def _validate_harvest_date(
        self, 
        harvest_date: Any
    ) -> List[ValidationResult]:
        """Validate harvest date."""
        results = []
        
        try:
            if isinstance(harvest_date, str):
                harvest_date = datetime.fromisoformat(harvest_date).date()
            elif not isinstance(harvest_date, date):
                raise ValueError("Invalid date format")
            
            # Check if date is not in the future
            if harvest_date > date.today():
                results.append(
                    ValidationResult.error(
                        message="Harvest date cannot be in the future",
                        field="harvest_date",
                        code="FUTURE_DATE"
                    )
                )
            
            # Check if date is not too old (1 year)
            days_old = (date.today() - harvest_date).days
            if days_old > 365:
                results.append(
                    ValidationResult.warning(
                        message=f"Harvest date is {days_old} days old. Very old harvest dates may affect quality.",
                        field="harvest_date"
                    )
                )
            
            if not results:
                results.append(
                    ValidationResult.success("Harvest date is valid")
                )
                
        except (ValueError, TypeError) as e:
            results.append(
                ValidationResult.error(
                    message=f"Invalid harvest date: {str(e)}",
                    field="harvest_date",
                    code="INVALID_DATE"
                )
            )
        
        return results

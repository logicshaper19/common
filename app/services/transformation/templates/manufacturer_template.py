"""
Manufacturer-specific transformation template engine.

This module provides templates and data for manufacturer processing transformations,
following the single responsibility principle.
"""
from typing import Dict, Any, Optional
from datetime import datetime, date
from decimal import Decimal

from app.models.transformation import TransformationType
from .base import BaseTemplateEngine
from app.services.transformation.config.industry_standards import get_standards_for_company_type, RegionType


class ManufacturerTemplateEngine(BaseTemplateEngine):
    """Template engine for manufacturer processing transformations."""
    
    def _get_role_specific_data(
        self, 
        transformation_type: TransformationType, 
        company_type: str,
        input_batch_data: Optional[Dict]
    ) -> Dict[str, Any]:
        """Get manufacturer-specific data for manufacturing transformations."""
        if transformation_type != TransformationType.MANUFACTURING:
            return {}
        
        # Get industry standards for manufacturer
        standards = get_standards_for_company_type(company_type, RegionType.SOUTHEAST_ASIA)
        
        return {
            "role_specific_data": {
                "manufacturer_data": self._get_manufacturer_processing_data(input_batch_data, standards),
                "quality_metrics": self._get_manufacturing_quality_metrics(standards),
                "process_parameters": self._get_manufacturing_process_parameters(standards),
                "efficiency_metrics": self._get_manufacturing_efficiency_metrics(standards),
                "location_data": self._get_manufacturer_location_data(),
                "weather_conditions": self._get_manufacturing_weather_conditions(),
                "certifications": self._get_manufacturing_certifications(),
                "compliance_data": self._get_manufacturing_compliance_data()
            },
            "output_batch_suggestion": self.create_output_batch_suggestion(
                transformation_type, input_batch_data, company_type
            )
        }
    
    def _get_manufacturer_processing_data(
        self, 
        input_batch_data: Optional[Dict], 
        standards: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get manufacturer processing-specific data."""
        input_quantity = input_batch_data.get('quantity', Decimal('1000')) if input_batch_data else Decimal('1000')
        
        # Use standards or defaults
        efficiency_standards = standards.get('efficiency', {})
        yield_min = efficiency_standards.get('yield_min', Decimal('95.0'))
        yield_max = efficiency_standards.get('yield_max', Decimal('98.0'))
        average_yield = (yield_min + yield_max) / 2
        
        return {
            "processing_date": date.today().isoformat(),
            "processing_method": "formulation_and_packaging",
            "refined_oil_input": float(input_quantity),
            "finished_products_output": float(input_batch_data.get('quantity', Decimal('1000')) * average_yield / 100),
            "processing_loss_percentage": float(100 - average_yield),
            "processing_capacity_tonnes_per_day": 50.0,
            "manufacturing_efficiency_percentage": float(average_yield),
            "formulation_method": "batch_formulation",
            "mixing_method": "high_shear_mixing",
            "packaging_method": "aseptic_packaging",
            "quality_control_method": "in_line_testing",
            "equipment_used": [
                "formulation_tank",
                "high_shear_mixer",
                "homogenizer",
                "filling_machine",
                "packaging_line",
                "quality_control_lab"
            ],
            "processing_notes": "Premium beauty product formulation with optimal quality control",
            "product_grade": "Premium Grade",
            "sustainability_practices": [
                "renewable_energy_usage",
                "waste_minimization",
                "sustainable_packaging",
                "carbon_neutral_operations"
            ]
        }
    
    def _get_manufacturing_quality_metrics(self, standards: Dict[str, Any]) -> Dict[str, Any]:
        """Get quality metrics for manufacturing transformation."""
        quality_standards = standards.get('quality', {})
        
        return {
            "moisture_content": float(quality_standards.get('moisture_max', Decimal('0.02'))),
            "ffa_content": float(quality_standards.get('ffa_max', Decimal('0.05'))),
            "iodine_value": float(quality_standards.get('iodine_min', Decimal('53.0'))),
            "peroxide_value": float(quality_standards.get('peroxide_max', Decimal('0.5'))),
            "color_grade": quality_standards.get('color_grades', ['A1', 'A2'])[0],
            "purity_percentage": float(quality_standards.get('min_purity', Decimal('99.8'))),
            "ph_level": 6.5,
            "viscosity_cp": 35.0,
            "density_kg_per_m3": 920.0,
            "free_fatty_acid_percentage": 0.05,
            "unsaponifiable_matter_percentage": 0.2,
            "microbial_count_cfu_per_g": 10,
            "heavy_metals_ppm": 0.1,
            "pesticide_residues_ppm": 0.01
        }
    
    def _get_manufacturing_process_parameters(self, standards: Dict[str, Any]) -> Dict[str, Any]:
        """Get process parameters for manufacturing transformation."""
        process_standards = standards.get('process', {})
        
        return {
            "temperature": float(process_standards.get('temp_min', Decimal('180.0'))),
            "pressure": float(process_standards.get('pressure_min', Decimal('1.0'))),
            "duration_hours": float(process_standards.get('duration_min', Decimal('4.0'))),
            "energy_consumed": float(process_standards.get('energy_min', Decimal('200.0'))),
            "mixing_speed_rpm": 1500.0,
            "homogenization_pressure_bar": 200.0,
            "filling_temperature": 60.0,
            "packaging_temperature": 25.0,
            "chemical_additives": [
                "antioxidants",
                "preservatives",
                "emulsifiers",
                "vitamin_e",
                "natural_extracts"
            ],
            "process_control_parameters": {
                "ph_level": 6.5,
                "viscosity_cp": 35.0,
                "density_kg_per_m3": 920.0,
                "particle_size_microns": 5.0,
                "turbidity_ntu": 1.0
            }
        }
    
    def _get_manufacturing_efficiency_metrics(self, standards: Dict[str, Any]) -> Dict[str, Any]:
        """Get efficiency metrics for manufacturing transformation."""
        efficiency_standards = standards.get('efficiency', {})
        
        return {
            "yield_percentage": float(efficiency_standards.get('yield_min', Decimal('95.0'))),
            "waste_percentage": float(efficiency_standards.get('waste_max', Decimal('1.0'))),
            "energy_efficiency": 90.0,
            "water_efficiency": 95.0,
            "processing_time_hours": float(efficiency_standards.get('time_min', Decimal('4.0'))),
            "equipment_utilization": 95.0,
            "formulation_efficiency": 98.0,
            "packaging_efficiency": 97.0,
            "overall_efficiency": 95.0
        }
    
    def _get_manufacturer_location_data(self) -> Dict[str, Any]:
        """Get location data for manufacturer facility."""
        return {
            "facility_name": "Beauty Products Manufacturing Plant",
            "address": "Manufacturing Complex, Industrial Park",
            "city": "Shah Alam",
            "state_province": "Selangor",
            "country": "MY",
            "postal_code": "40000",
            "latitude": 3.0733,
            "longitude": 101.5185,
            "elevation_meters": 15.0,
            "facility_size_hectares": 3.0,
            "processing_capacity_tonnes_per_day": 50.0,
            "operating_hours_per_day": 16.0,
            "facility_age_years": 5,
            "last_major_upgrade": "2024",
            "clean_room_class": "ISO_8",
            "storage_capacity_tonnes": 1000.0
        }
    
    def _get_manufacturing_weather_conditions(self) -> Dict[str, Any]:
        """Get weather conditions during manufacturing."""
        return {
            "temperature_celsius": 25.0,  # Controlled environment
            "humidity_percentage": 50.0,  # Controlled environment
            "rainfall_mm": 0.0,
            "wind_speed_kmh": 0.0,  # Indoor facility
            "weather_condition": "controlled",
            "uv_index": 0.0,  # Indoor facility
            "visibility_km": 10.0,
            "atmospheric_pressure_hpa": 1013.25
        }
    
    def _get_manufacturing_certifications(self) -> list:
        """Get certifications relevant to manufacturing."""
        return [
            {
                "certification_type": "RSPO Mass Balance",
                "certification_body": "RSPO",
                "certificate_number": "RSPO-MB-2024-MFG-001",
                "issue_date": date.today().isoformat(),
                "expiry_date": date.today().replace(year=date.today().year + 1).isoformat(),
                "is_valid": True,
                "scope": "manufacturing"
            },
            {
                "certification_type": "ISCC EU",
                "certification_body": "ISCC",
                "certificate_number": "ISCC-EU-2024-MFG-001",
                "issue_date": date.today().isoformat(),
                "expiry_date": date.today().replace(year=date.today().year + 1).isoformat(),
                "is_valid": True,
                "scope": "sustainability"
            },
            {
                "certification_type": "HACCP",
                "certification_body": "SIRIM",
                "certificate_number": "HACCP-2024-MFG-001",
                "issue_date": date.today().isoformat(),
                "expiry_date": date.today().replace(year=date.today().year + 1).isoformat(),
                "is_valid": True,
                "scope": "food_safety"
            },
            {
                "certification_type": "ISO 22716",
                "certification_body": "SIRIM",
                "certificate_number": "ISO-22716-2024-MFG-001",
                "issue_date": date.today().isoformat(),
                "expiry_date": date.today().replace(year=date.today().year + 1).isoformat(),
                "is_valid": True,
                "scope": "cosmetics_gmp"
            },
            {
                "certification_type": "Halal",
                "certification_body": "JAKIM",
                "certificate_number": "HALAL-2024-MFG-001",
                "issue_date": date.today().isoformat(),
                "expiry_date": date.today().replace(year=date.today().year + 1).isoformat(),
                "is_valid": True,
                "scope": "halal_compliance"
            }
        ]
    
    def _get_manufacturing_compliance_data(self) -> Dict[str, Any]:
        """Get compliance data for manufacturing."""
        return {
            "regulatory_compliance": {
                "malaysian_palm_oil_board": {
                    "license_number": "MPOB-LIC-2024-MFG-001",
                    "compliance_status": "compliant",
                    "last_inspection": date.today().isoformat(),
                    "next_inspection": date.today().replace(month=date.today().month + 3).isoformat()
                },
                "environmental_protection": {
                    "effluent_treatment_plant": "operational",
                    "air_emission_control": "compliant",
                    "waste_management_system": "certified",
                    "environmental_impact_assessment": "approved",
                    "carbon_footprint_monitoring": "implemented"
                },
                "food_safety": {
                    "haccp_certification": "valid",
                    "halal_certification": "valid",
                    "kosher_certification": "valid",
                    "gmp_compliance": "certified",
                    "fsms_certification": "valid"
                },
                "cosmetics_regulation": {
                    "npra_registration": "valid",
                    "cosmetics_gmp": "certified",
                    "product_safety_assessment": "completed",
                    "ingredient_approval": "valid"
                }
            },
            "sustainability_metrics": {
                "carbon_footprint_kg_co2_per_tonne": 1.0,
                "water_usage_liters_per_tonne": 1000,
                "energy_usage_kwh_per_tonne": 200,
                "waste_generated_kg_per_tonne": 10,
                "recycling_percentage": 98.0,
                "renewable_energy_percentage": 50.0,
                "sustainable_packaging_percentage": 80.0
            },
            "quality_management": {
                "iso_9001_certification": "valid",
                "iso_14001_certification": "valid",
                "iso_22716_certification": "valid",
                "quality_control_laboratory": "accredited",
                "traceability_system": "implemented",
                "batch_tracking": "automated",
                "quality_audit_frequency": "monthly"
            }
        }

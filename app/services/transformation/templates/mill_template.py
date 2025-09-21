"""
Mill-specific transformation template engine.

This module provides templates and data for mill processing transformations,
following the single responsibility principle.
"""
from typing import Dict, Any, Optional
from datetime import datetime, date
from decimal import Decimal

from app.models.transformation import TransformationType
from .base import BaseTemplateEngine
from app.services.transformation.config.industry_standards import get_standards_for_company_type, RegionType


class MillTemplateEngine(BaseTemplateEngine):
    """Template engine for mill processing transformations."""
    
    def _get_role_specific_data(
        self, 
        transformation_type: TransformationType, 
        company_type: str,
        input_batch_data: Optional[Dict]
    ) -> Dict[str, Any]:
        """Get mill-specific data for milling transformations."""
        if transformation_type != TransformationType.MILLING:
            return {}
        
        # Get industry standards for mill
        standards = get_standards_for_company_type(company_type, RegionType.SOUTHEAST_ASIA)
        
        return {
            "role_specific_data": {
                "mill_data": self._get_mill_processing_data(input_batch_data, standards),
                "quality_metrics": self._get_milling_quality_metrics(standards),
                "process_parameters": self._get_milling_process_parameters(standards),
                "efficiency_metrics": self._get_milling_efficiency_metrics(standards),
                "location_data": self._get_mill_location_data(),
                "weather_conditions": self._get_milling_weather_conditions(),
                "certifications": self._get_milling_certifications(),
                "compliance_data": self._get_milling_compliance_data()
            },
            "output_batch_suggestion": self.create_output_batch_suggestion(
                transformation_type, input_batch_data, company_type
            )
        }
    
    def _get_mill_processing_data(
        self, 
        input_batch_data: Optional[Dict], 
        standards: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get mill processing-specific data."""
        input_quantity = input_batch_data.get('quantity', Decimal('1000')) if input_batch_data else Decimal('1000')
        
        # Use standards or defaults
        efficiency_standards = standards.get('efficiency', {})
        yield_min = efficiency_standards.get('yield_min', Decimal('18.0'))
        yield_max = efficiency_standards.get('yield_max', Decimal('25.0'))
        average_yield = (yield_min + yield_max) / 2
        
        return {
            "processing_date": date.today().isoformat(),
            "processing_method": "mechanical_extraction",
            "fresh_fruit_bunches_processed": float(input_quantity),
            "crude_palm_oil_produced": float(input_quantity * average_yield / 100),
            "palm_kernel_produced": float(input_quantity * Decimal('5.0') / 100),
            "processing_capacity_tonnes_per_hour": 25.0,
            "extraction_rate_percentage": float(average_yield),
            "sterilization_time_minutes": 90,
            "threshing_efficiency_percentage": 95.0,
            "pressing_pressure_bar": 2.5,
            "oil_clarification_method": "centrifugal_separation",
            "equipment_used": [
                "sterilizer",
                "thresher", 
                "press",
                "clarifier",
                "kernel_separator"
            ],
            "processing_notes": "Standard mechanical extraction process with optimal efficiency",
            "quality_grade": "Grade A CPO",
            "sustainability_practices": [
                "waste_heat_recovery",
                "water_recycling",
                "biogas_generation",
                "zero_waste_to_landfill"
            ]
        }
    
    def _get_milling_quality_metrics(self, standards: Dict[str, Any]) -> Dict[str, Any]:
        """Get quality metrics for milling transformation."""
        quality_standards = standards.get('quality', {})
        
        return {
            "moisture_content": float(quality_standards.get('moisture_max', Decimal('0.1'))),
            "ffa_content": float(quality_standards.get('ffa_max', Decimal('4.0'))),
            "iodine_value": float(quality_standards.get('iodine_min', Decimal('52.0'))),
            "color_grade": quality_standards.get('color_grades', ['A2', 'B1'])[0],
            "purity_percentage": float(quality_standards.get('min_purity', Decimal('98.0'))),
            "peroxide_value": 2.0,
            "deterioration_of_bleachability_index": 2.5,
            "carotene_content": 500.0,
            "tocopherol_content": 600.0,
            "free_fatty_acid_percentage": 4.0,
            "unsaponifiable_matter_percentage": 0.5
        }
    
    def _get_milling_process_parameters(self, standards: Dict[str, Any]) -> Dict[str, Any]:
        """Get process parameters for milling transformation."""
        process_standards = standards.get('process', {})
        
        return {
            "temperature": float(process_standards.get('temp_min', Decimal('90.0'))),
            "pressure": float(process_standards.get('pressure_min', Decimal('2.0'))),
            "duration_hours": float(process_standards.get('duration_min', Decimal('6.0'))),
            "energy_consumed": float(process_standards.get('energy_min', Decimal('150.0'))),
            "water_used": 500.0,
            "steam_pressure_bar": 3.0,
            "sterilization_temperature": 130.0,
            "threshing_speed_rpm": 1200.0,
            "pressing_pressure_bar": 2.5,
            "clarification_temperature": 95.0,
            "chemical_additives": ["phosphoric_acid", "bleaching_earth"],
            "process_control_parameters": {
                "ph_level": 5.5,
                "viscosity_cp": 45.0,
                "density_kg_per_m3": 920.0
            }
        }
    
    def _get_milling_efficiency_metrics(self, standards: Dict[str, Any]) -> Dict[str, Any]:
        """Get efficiency metrics for milling transformation."""
        efficiency_standards = standards.get('efficiency', {})
        
        return {
            "yield_percentage": float(efficiency_standards.get('yield_min', Decimal('22.0'))),
            "waste_percentage": float(efficiency_standards.get('waste_max', Decimal('8.0'))),
            "energy_efficiency": 80.0,
            "water_efficiency": 85.0,
            "processing_time_hours": float(efficiency_standards.get('time_min', Decimal('6.0'))),
            "equipment_utilization": 90.0,
            "oil_extraction_efficiency": 95.0,
            "kernel_recovery_efficiency": 85.0,
            "overall_efficiency": 87.5
        }
    
    def _get_mill_location_data(self) -> Dict[str, Any]:
        """Get location data for mill facility."""
        return {
            "facility_name": "Palm Oil Processing Mill",
            "address": "Industrial Zone, Mill Complex",
            "city": "Port Klang",
            "state_province": "Selangor",
            "country": "MY",
            "postal_code": "42000",
            "latitude": 3.0000,
            "longitude": 101.4000,
            "elevation_meters": 10.0,
            "facility_size_hectares": 5.0,
            "processing_capacity_tonnes_per_day": 600.0,
            "operating_hours_per_day": 24.0,
            "facility_age_years": 8,
            "last_major_upgrade": "2022"
        }
    
    def _get_milling_weather_conditions(self) -> Dict[str, Any]:
        """Get weather conditions during milling."""
        return {
            "temperature_celsius": 30.0,
            "humidity_percentage": 85.0,
            "rainfall_mm": 0.0,
            "wind_speed_kmh": 20.0,
            "weather_condition": "partly_cloudy",
            "uv_index": 6.0,
            "visibility_km": 8.0,
            "atmospheric_pressure_hpa": 1010.0
        }
    
    def _get_milling_certifications(self) -> list:
        """Get certifications relevant to mill processing."""
        return [
            {
                "certification_type": "RSPO Mass Balance",
                "certification_body": "RSPO",
                "certificate_number": "RSPO-MB-2024-MILL-001",
                "issue_date": date.today().isoformat(),
                "expiry_date": date.today().replace(year=date.today().year + 1).isoformat(),
                "is_valid": True,
                "scope": "mill_processing"
            },
            {
                "certification_type": "ISCC EU",
                "certification_body": "ISCC",
                "certificate_number": "ISCC-EU-2024-MILL-001",
                "issue_date": date.today().isoformat(),
                "expiry_date": date.today().replace(year=date.today().year + 1).isoformat(),
                "is_valid": True,
                "scope": "sustainability"
            },
            {
                "certification_type": "HACCP",
                "certification_body": "SIRIM",
                "certificate_number": "HACCP-2024-MILL-001",
                "issue_date": date.today().isoformat(),
                "expiry_date": date.today().replace(year=date.today().year + 1).isoformat(),
                "is_valid": True,
                "scope": "food_safety"
            }
        ]
    
    def _get_milling_compliance_data(self) -> Dict[str, Any]:
        """Get compliance data for mill processing."""
        return {
            "regulatory_compliance": {
                "malaysian_palm_oil_board": {
                    "license_number": "MPOB-LIC-2024-MILL-001",
                    "compliance_status": "compliant",
                    "last_inspection": date.today().isoformat(),
                    "next_inspection": date.today().replace(month=date.today().month + 3).isoformat()
                },
                "environmental_protection": {
                    "effluent_treatment_plant": "operational",
                    "air_emission_control": "compliant",
                    "waste_management_system": "certified",
                    "environmental_impact_assessment": "approved"
                },
                "food_safety": {
                    "haccp_certification": "valid",
                    "halal_certification": "valid",
                    "kosher_certification": "valid",
                    "gmp_compliance": "certified"
                }
            },
            "sustainability_metrics": {
                "carbon_footprint_kg_co2_per_tonne": 1.2,
                "water_usage_liters_per_tonne": 3000,
                "energy_usage_kwh_per_tonne": 150,
                "waste_generated_kg_per_tonne": 50,
                "recycling_percentage": 90.0,
                "biogas_generation_m3_per_day": 5000
            },
            "quality_management": {
                "iso_9001_certification": "valid",
                "quality_control_laboratory": "accredited",
                "traceability_system": "implemented",
                "batch_tracking": "automated"
            }
        }

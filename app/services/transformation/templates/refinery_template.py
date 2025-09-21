"""
Refinery-specific transformation template engine.

This module provides templates and data for refinery processing transformations,
following the single responsibility principle.
"""
from typing import Dict, Any, Optional
from datetime import datetime, date
from decimal import Decimal

from app.models.transformation import TransformationType
from .base import BaseTemplateEngine
from app.services.transformation.config.industry_standards import get_standards_for_company_type, RegionType


class RefineryTemplateEngine(BaseTemplateEngine):
    """Template engine for refinery processing transformations."""
    
    def _get_role_specific_data(
        self, 
        transformation_type: TransformationType, 
        company_type: str,
        input_batch_data: Optional[Dict]
    ) -> Dict[str, Any]:
        """Get refinery-specific data for refining transformations."""
        if transformation_type != TransformationType.REFINING:
            return {}
        
        # Get industry standards for refinery
        standards = get_standards_for_company_type(company_type, RegionType.SOUTHEAST_ASIA)
        
        return {
            "role_specific_data": {
                "refinery_data": self._get_refinery_processing_data(input_batch_data, standards),
                "quality_metrics": self._get_refining_quality_metrics(standards),
                "process_parameters": self._get_refining_process_parameters(standards),
                "efficiency_metrics": self._get_refining_efficiency_metrics(standards),
                "location_data": self._get_refinery_location_data(),
                "weather_conditions": self._get_refining_weather_conditions(),
                "certifications": self._get_refining_certifications(),
                "compliance_data": self._get_refining_compliance_data()
            },
            "output_batch_suggestion": self.create_output_batch_suggestion(
                transformation_type, input_batch_data, company_type
            )
        }
    
    def _get_refinery_processing_data(
        self, 
        input_batch_data: Optional[Dict], 
        standards: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get refinery processing-specific data."""
        input_quantity = input_batch_data.get('quantity', Decimal('1000')) if input_batch_data else Decimal('1000')
        
        # Use standards or defaults
        efficiency_standards = standards.get('efficiency', {})
        yield_min = efficiency_standards.get('yield_min', Decimal('95.0'))
        yield_max = efficiency_standards.get('yield_max', Decimal('98.0'))
        average_yield = (yield_min + yield_max) / 2
        
        return {
            "processing_date": date.today().isoformat(),
            "processing_method": "physical_chemical_refining",
            "crude_palm_oil_input": float(input_quantity),
            "refined_palm_oil_output": float(input_quantity * average_yield / 100),
            "refining_loss_percentage": float(100 - average_yield),
            "processing_capacity_tonnes_per_day": 200.0,
            "refining_efficiency_percentage": float(average_yield),
            "degumming_method": "acid_degumming",
            "neutralization_method": "caustic_neutralization",
            "bleaching_method": "adsorption_bleaching",
            "deodorization_method": "steam_distillation",
            "fractionation_method": "dry_fractionation",
            "equipment_used": [
                "degumming_tank",
                "neutralization_vessel",
                "bleaching_earth_mixer",
                "deodorizer",
                "fractionation_crystallizer",
                "filter_press"
            ],
            "processing_notes": "Complete physical-chemical refining process with optimal yield",
            "quality_grade": "RBD Palm Oil",
            "sustainability_practices": [
                "waste_heat_recovery",
                "steam_condensate_recovery",
                "effluent_treatment",
                "energy_optimization"
            ]
        }
    
    def _get_refining_quality_metrics(self, standards: Dict[str, Any]) -> Dict[str, Any]:
        """Get quality metrics for refining transformation."""
        quality_standards = standards.get('quality', {})
        
        return {
            "moisture_content": float(quality_standards.get('moisture_max', Decimal('0.05'))),
            "ffa_content": float(quality_standards.get('ffa_max', Decimal('0.1'))),
            "iodine_value": float(quality_standards.get('iodine_min', Decimal('53.0'))),
            "peroxide_value": float(quality_standards.get('peroxide_max', Decimal('2.0'))),
            "color_grade": quality_standards.get('color_grades', ['A1', 'A2'])[0],
            "purity_percentage": float(quality_standards.get('min_purity', Decimal('99.5'))),
            "deterioration_of_bleachability_index": 1.0,
            "carotene_content": 50.0,
            "tocopherol_content": 400.0,
            "free_fatty_acid_percentage": 0.1,
            "unsaponifiable_matter_percentage": 0.3,
            "soap_content_ppm": 5.0,
            "phosphorus_content_ppm": 2.0
        }
    
    def _get_refining_process_parameters(self, standards: Dict[str, Any]) -> Dict[str, Any]:
        """Get process parameters for refining transformation."""
        process_standards = standards.get('process', {})
        
        return {
            "temperature": float(process_standards.get('temp_min', Decimal('220.0'))),
            "pressure": float(process_standards.get('pressure_min', Decimal('0.3'))),
            "duration_hours": float(process_standards.get('duration_min', Decimal('8.0'))),
            "energy_consumed": float(process_standards.get('energy_min', Decimal('300.0'))),
            "steam_consumption_kg_per_tonne": 50.0,
            "degumming_temperature": 80.0,
            "neutralization_temperature": 90.0,
            "bleaching_temperature": 110.0,
            "deodorization_temperature": 250.0,
            "deodorization_pressure": 0.1,
            "fractionation_temperature": 25.0,
            "chemical_additives": [
                "phosphoric_acid",
                "caustic_soda",
                "bleaching_earth",
                "citric_acid"
            ],
            "process_control_parameters": {
                "ph_level": 6.0,
                "viscosity_cp": 40.0,
                "density_kg_per_m3": 915.0,
                "flash_point_celsius": 300.0
            }
        }
    
    def _get_refining_efficiency_metrics(self, standards: Dict[str, Any]) -> Dict[str, Any]:
        """Get efficiency metrics for refining transformation."""
        efficiency_standards = standards.get('efficiency', {})
        
        return {
            "yield_percentage": float(efficiency_standards.get('yield_min', Decimal('96.0'))),
            "waste_percentage": float(efficiency_standards.get('waste_max', Decimal('2.0'))),
            "energy_efficiency": 75.0,
            "water_efficiency": 80.0,
            "processing_time_hours": float(efficiency_standards.get('time_min', Decimal('8.0'))),
            "equipment_utilization": 85.0,
            "refining_efficiency": 96.0,
            "fractionation_efficiency": 90.0,
            "overall_efficiency": 88.5
        }
    
    def _get_refinery_location_data(self) -> Dict[str, Any]:
        """Get location data for refinery facility."""
        return {
            "facility_name": "Palm Oil Refinery Plant",
            "address": "Refinery Complex, Industrial Area",
            "city": "Johor Bahru",
            "state_province": "Johor",
            "country": "MY",
            "postal_code": "80000",
            "latitude": 1.4927,
            "longitude": 103.7414,
            "elevation_meters": 5.0,
            "facility_size_hectares": 10.0,
            "processing_capacity_tonnes_per_day": 200.0,
            "operating_hours_per_day": 24.0,
            "facility_age_years": 12,
            "last_major_upgrade": "2023",
            "port_access": "direct_port_access",
            "storage_capacity_tonnes": 5000.0
        }
    
    def _get_refining_weather_conditions(self) -> Dict[str, Any]:
        """Get weather conditions during refining."""
        return {
            "temperature_celsius": 32.0,
            "humidity_percentage": 90.0,
            "rainfall_mm": 0.0,
            "wind_speed_kmh": 25.0,
            "weather_condition": "partly_cloudy",
            "uv_index": 7.0,
            "visibility_km": 6.0,
            "atmospheric_pressure_hpa": 1008.0
        }
    
    def _get_refining_certifications(self) -> list:
        """Get certifications relevant to refinery processing."""
        return [
            {
                "certification_type": "RSPO Mass Balance",
                "certification_body": "RSPO",
                "certificate_number": "RSPO-MB-2024-REF-001",
                "issue_date": date.today().isoformat(),
                "expiry_date": date.today().replace(year=date.today().year + 1).isoformat(),
                "is_valid": True,
                "scope": "refinery_processing"
            },
            {
                "certification_type": "ISCC EU",
                "certification_body": "ISCC",
                "certificate_number": "ISCC-EU-2024-REF-001",
                "issue_date": date.today().isoformat(),
                "expiry_date": date.today().replace(year=date.today().year + 1).isoformat(),
                "is_valid": True,
                "scope": "sustainability"
            },
            {
                "certification_type": "HACCP",
                "certification_body": "SIRIM",
                "certificate_number": "HACCP-2024-REF-001",
                "issue_date": date.today().isoformat(),
                "expiry_date": date.today().replace(year=date.today().year + 1).isoformat(),
                "is_valid": True,
                "scope": "food_safety"
            },
            {
                "certification_type": "Halal",
                "certification_body": "JAKIM",
                "certificate_number": "HALAL-2024-REF-001",
                "issue_date": date.today().isoformat(),
                "expiry_date": date.today().replace(year=date.today().year + 1).isoformat(),
                "is_valid": True,
                "scope": "halal_compliance"
            }
        ]
    
    def _get_refining_compliance_data(self) -> Dict[str, Any]:
        """Get compliance data for refinery processing."""
        return {
            "regulatory_compliance": {
                "malaysian_palm_oil_board": {
                    "license_number": "MPOB-LIC-2024-REF-001",
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
                }
            },
            "sustainability_metrics": {
                "carbon_footprint_kg_co2_per_tonne": 2.5,
                "water_usage_liters_per_tonne": 2000,
                "energy_usage_kwh_per_tonne": 300,
                "waste_generated_kg_per_tonne": 20,
                "recycling_percentage": 95.0,
                "renewable_energy_percentage": 30.0
            },
            "quality_management": {
                "iso_9001_certification": "valid",
                "iso_14001_certification": "valid",
                "quality_control_laboratory": "accredited",
                "traceability_system": "implemented",
                "batch_tracking": "automated",
                "quality_audit_frequency": "monthly"
            }
        }

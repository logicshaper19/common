"""
Plantation-specific transformation template engine.

This module provides templates and data for plantation harvest transformations,
following the single responsibility principle.
"""
from typing import Dict, Any, Optional
from datetime import datetime, date
from decimal import Decimal

from app.models.transformation import TransformationType
from .base import BaseTemplateEngine
from app.services.transformation.config.industry_standards import get_standards_for_company_type, RegionType


class PlantationTemplateEngine(BaseTemplateEngine):
    """Template engine for plantation harvest transformations."""
    
    def _get_role_specific_data(
        self, 
        transformation_type: TransformationType, 
        company_type: str,
        input_batch_data: Optional[Dict]
    ) -> Dict[str, Any]:
        """Get plantation-specific data for harvest transformations."""
        if transformation_type != TransformationType.HARVEST:
            return {}
        
        # Get industry standards for plantation
        standards = get_standards_for_company_type(company_type, RegionType.SOUTHEAST_ASIA)
        
        return {
            "role_specific_data": {
                "plantation_data": self._get_plantation_harvest_data(input_batch_data, standards),
                "quality_metrics": self._get_harvest_quality_metrics(standards),
                "process_parameters": self._get_harvest_process_parameters(standards),
                "efficiency_metrics": self._get_harvest_efficiency_metrics(standards),
                "location_data": self._get_plantation_location_data(),
                "weather_conditions": self._get_harvest_weather_conditions(),
                "certifications": self._get_harvest_certifications(),
                "compliance_data": self._get_harvest_compliance_data()
            },
            "output_batch_suggestion": self.create_output_batch_suggestion(
                transformation_type, input_batch_data, company_type
            )
        }
    
    def _get_plantation_harvest_data(
        self, 
        input_batch_data: Optional[Dict], 
        standards: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get plantation harvest-specific data."""
        # Calculate harvest metrics based on input batch
        input_quantity = input_batch_data.get('quantity', Decimal('1000')) if input_batch_data else Decimal('1000')
        
        # Use standards or defaults
        efficiency_standards = standards.get('efficiency', {})
        yield_min = efficiency_standards.get('yield_min', Decimal('15.0'))
        yield_max = efficiency_standards.get('yield_max', Decimal('25.0'))
        average_yield = (yield_min + yield_max) / 2
        
        return {
            "harvest_date": date.today().isoformat(),
            "harvest_method": "manual_harvesting",
            "fruit_bunches_harvested": float(input_quantity),
            "estimated_oil_yield": float(input_quantity * average_yield / 100),
            "harvest_team_size": 8,
            "harvest_duration_hours": 6.0,
            "fruit_ripeness_percentage": 85.0,
            "harvest_efficiency": 90.0,
            "equipment_used": ["harvesting_knife", "collection_baskets", "transport_cart"],
            "harvest_notes": "Fresh fruit bunches harvested at optimal ripeness",
            "quality_grade": "Grade A",
            "sustainability_practices": [
                "zero_burning_policy",
                "integrated_pest_management",
                "soil_conservation"
            ]
        }
    
    def _get_harvest_quality_metrics(self, standards: Dict[str, Any]) -> Dict[str, Any]:
        """Get quality metrics for harvest transformation."""
        quality_standards = standards.get('quality', {})
        
        return {
            "moisture_content": float(quality_standards.get('moisture_max', Decimal('12.0'))),
            "ffa_content": float(quality_standards.get('ffa_max', Decimal('3.5'))),
            "color_grade": quality_standards.get('color_grades', ['A1', 'A2'])[0],
            "purity_percentage": float(quality_standards.get('min_purity', Decimal('95.0'))),
            "oil_content_percentage": 22.5,
            "kernel_content_percentage": 5.0,
            "mesocarp_content_percentage": 70.0,
            "shell_content_percentage": 2.5,
            "fresh_fruit_bunch_quality": "excellent",
            "oil_extraction_potential": "high"
        }
    
    def _get_harvest_process_parameters(self, standards: Dict[str, Any]) -> Dict[str, Any]:
        """Get process parameters for harvest transformation."""
        process_standards = standards.get('process', {})
        
        return {
            "temperature": float(process_standards.get('temp_min', Decimal('25.0'))),
            "humidity": 75.0,
            "duration_hours": float(process_standards.get('duration_min', Decimal('4.0'))),
            "energy_consumed": 10.0,
            "harvest_time_start": "06:00",
            "harvest_time_end": "12:00",
            "weather_conditions": "favorable",
            "soil_conditions": "optimal",
            "pest_incidence": "low",
            "disease_incidence": "none"
        }
    
    def _get_harvest_efficiency_metrics(self, standards: Dict[str, Any]) -> Dict[str, Any]:
        """Get efficiency metrics for harvest transformation."""
        efficiency_standards = standards.get('efficiency', {})
        
        return {
            "yield_percentage": float(efficiency_standards.get('yield_min', Decimal('20.0'))),
            "waste_percentage": float(efficiency_standards.get('waste_max', Decimal('3.0'))),
            "energy_efficiency": 85.0,
            "water_efficiency": 90.0,
            "processing_time_hours": float(efficiency_standards.get('time_min', Decimal('4.0'))),
            "labor_efficiency": 88.0,
            "equipment_utilization": 92.0,
            "overall_efficiency": 87.5
        }
    
    def _get_plantation_location_data(self) -> Dict[str, Any]:
        """Get location data for plantation facility."""
        return {
            "facility_name": "Green Acres Plantation",
            "address": "Plantation Road, Estate Area",
            "city": "Kuala Lumpur",
            "state_province": "Selangor",
            "country": "MY",
            "postal_code": "40000",
            "latitude": 3.1390,
            "longitude": 101.6869,
            "elevation_meters": 50.0,
            "soil_type": "tropical_red_soil",
            "plantation_size_hectares": 500.0,
            "planting_year": 2015,
            "palm_variety": "Tenera",
            "planting_density_per_hectare": 148
        }
    
    def _get_harvest_weather_conditions(self) -> Dict[str, Any]:
        """Get weather conditions during harvest."""
        return {
            "temperature_celsius": 28.0,
            "humidity_percentage": 80.0,
            "rainfall_mm": 0.0,  # No rain during harvest
            "wind_speed_kmh": 15.0,
            "weather_condition": "sunny",
            "uv_index": 8.0,
            "visibility_km": 10.0,
            "atmospheric_pressure_hpa": 1013.25
        }
    
    def _get_harvest_certifications(self) -> list:
        """Get certifications relevant to plantation harvest."""
        return [
            {
                "certification_type": "RSPO Mass Balance",
                "certification_body": "RSPO",
                "certificate_number": "RSPO-MB-2024-PLANT-001",
                "issue_date": date.today().isoformat(),
                "expiry_date": date.today().replace(year=date.today().year + 1).isoformat(),
                "is_valid": True,
                "scope": "plantation_operations"
            },
            {
                "certification_type": "MSPO",
                "certification_body": "Malaysian Palm Oil Board",
                "certificate_number": "MSPO-2024-PLANT-001",
                "issue_date": date.today().isoformat(),
                "expiry_date": date.today().replace(year=date.today().year + 1).isoformat(),
                "is_valid": True,
                "scope": "malaysian_standards"
            },
            {
                "certification_type": "Rainforest Alliance",
                "certification_body": "Rainforest Alliance",
                "certificate_number": "RA-2024-PLANT-001",
                "issue_date": date.today().isoformat(),
                "expiry_date": date.today().replace(year=date.today().year + 1).isoformat(),
                "is_valid": True,
                "scope": "sustainable_agriculture"
            }
        ]
    
    def _get_harvest_compliance_data(self) -> Dict[str, Any]:
        """Get compliance data for plantation harvest."""
        return {
            "regulatory_compliance": {
                "malaysian_palm_oil_board": {
                    "license_number": "MPOB-LIC-2024-001",
                    "compliance_status": "compliant",
                    "last_inspection": date.today().isoformat(),
                    "next_inspection": date.today().replace(month=date.today().month + 6).isoformat()
                },
                "environmental_protection": {
                    "environmental_impact_assessment": "approved",
                    "waste_management_plan": "implemented",
                    "water_usage_permit": "valid",
                    "air_emissions_permit": "valid"
                }
            },
            "sustainability_metrics": {
                "carbon_footprint_kg_co2_per_tonne": 0.8,
                "water_usage_liters_per_tonne": 5000,
                "energy_usage_kwh_per_tonne": 50,
                "waste_generated_kg_per_tonne": 200,
                "recycling_percentage": 85.0
            },
            "social_compliance": {
                "labor_standards": "compliant",
                "worker_safety": "excellent",
                "community_engagement": "active",
                "local_employment_percentage": 95.0
            }
        }

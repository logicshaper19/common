"""
Transformation templates for role-specific data pre-filling.

This module provides templates and default values for each transformation type
based on company type and industry standards.
"""
from typing import Dict, Any, Optional, List
from datetime import datetime, date
from decimal import Decimal
from app.models.transformation import TransformationType
from app.core.unified_po_config import get_config


class TransformationTemplateEngine:
    """Engine for generating transformation templates and suggestions."""
    
    def __init__(self):
        self.config = get_config()
    
    def get_transformation_template(
        self, 
        transformation_type: TransformationType, 
        company_type: str,
        input_batch_data: Optional[Dict] = None,
        facility_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get a comprehensive transformation template for a specific company type.
        
        Args:
            transformation_type: The type of transformation
            company_type: The company type (plantation_grower, mill_processor, etc.)
            input_batch_data: Optional input batch data for inheritance
            facility_id: Optional facility ID for facility-specific defaults
            
        Returns:
            Complete transformation template with role-specific data
        """
        base_template = self._get_base_template(transformation_type, company_type, facility_id)
        
        # Add role-specific data based on transformation type
        if transformation_type == TransformationType.HARVEST:
            base_template.update(self._get_plantation_template(input_batch_data))
        elif transformation_type == TransformationType.MILLING:
            base_template.update(self._get_mill_template(input_batch_data))
        elif transformation_type == TransformationType.REFINING:
            base_template.update(self._get_refinery_template(input_batch_data))
        elif transformation_type == TransformationType.MANUFACTURING:
            base_template.update(self._get_manufacturer_template(input_batch_data))
        
        return base_template
    
    def _get_base_template(
        self, 
        transformation_type: TransformationType, 
        company_type: str,
        facility_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get base transformation template."""
        return {
            "transformation_type": transformation_type,
            "facility_id": facility_id or f"{company_type.upper()}-001",
            "process_description": self._get_default_process_description(transformation_type),
            "start_time": datetime.utcnow(),
            "status": "planned",
            "validation_status": "pending",
            "quality_metrics": self._get_default_quality_metrics(transformation_type),
            "process_parameters": self._get_default_process_parameters(transformation_type),
            "efficiency_metrics": self._get_default_efficiency_metrics(transformation_type),
            "certifications": self._get_default_certifications(company_type),
            "compliance_data": self._get_default_compliance_data(company_type),
            "location_coordinates": self._get_default_location_coordinates(),
            "weather_conditions": self._get_default_weather_conditions(transformation_type)
        }
    
    def _get_plantation_template(self, input_batch_data: Optional[Dict] = None) -> Dict[str, Any]:
        """Get plantation-specific template for harvest transformations."""
        return {
            "plantation_data": {
                "farm_id": "FARM-001",
                "farm_name": "Main Plantation",
                "gps_coordinates": {
                    "latitude": 3.1390,
                    "longitude": 101.6869,
                    "accuracy_meters": 10
                },
                "field_id": "FIELD-001",
                "harvest_date": date.today(),
                "harvest_method": "manual",
                "yield_per_hectare": Decimal("20.5"),
                "total_hectares": Decimal("100.0"),
                "ffb_quality_grade": "A",
                "moisture_content": Decimal("25.0"),
                "free_fatty_acid": Decimal("3.5"),
                "labor_hours": Decimal("8.0"),
                "equipment_used": ["harvesting_knife", "collection_baskets"],
                "fuel_consumed": Decimal("5.0"),
                "certifications": ["RSPO", "MSPO"],
                "sustainability_metrics": {
                    "carbon_footprint": "low",
                    "water_usage": "efficient",
                    "pesticide_usage": "minimal"
                }
            }
        }
    
    def _get_mill_template(self, input_batch_data: Optional[Dict] = None) -> Dict[str, Any]:
        """Get mill-specific template for milling transformations."""
        return {
            "mill_data": {
                "extraction_rate": Decimal("22.5"),  # OER - Oil Extraction Rate
                "processing_capacity": Decimal("50.0"),  # MT/hour
                "processing_time_hours": Decimal("8.0"),
                "ffb_quantity": input_batch_data.get("quantity", Decimal("1000.0")) if input_batch_data else Decimal("1000.0"),
                "ffb_quality_grade": "A",
                "ffb_moisture_content": Decimal("25.0"),
                "cpo_quantity": Decimal("225.0"),  # Calculated from OER
                "cpo_quality_grade": "A",
                "cpo_ffa_content": Decimal("3.5"),
                "cpo_moisture_content": Decimal("0.1"),
                "kernel_quantity": Decimal("50.0"),
                "oil_content_input": Decimal("25.0"),
                "oil_content_output": Decimal("95.0"),
                "extraction_efficiency": Decimal("90.0"),
                "energy_consumed": Decimal("150.0"),  # kWh
                "water_consumed": Decimal("2.5"),  # m³
                "steam_consumed": Decimal("0.8"),  # MT
                "equipment_used": ["sterilizer", "thresher", "press", "clarifier"],
                "maintenance_status": {
                    "last_maintenance": "2024-01-15",
                    "next_maintenance": "2024-04-15",
                    "condition": "excellent"
                }
            }
        }
    
    def _get_refinery_template(self, input_batch_data: Optional[Dict] = None) -> Dict[str, Any]:
        """Get refinery-specific template for refining transformations."""
        return {
            "refinery_data": {
                "process_type": "refining",
                "input_oil_quantity": input_batch_data.get("quantity", Decimal("1000.0")) if input_batch_data else Decimal("1000.0"),
                "input_oil_type": "CPO",
                "input_oil_quality": {
                    "ffa_content": "3.5%",
                    "moisture_content": "0.1%",
                    "color_grade": "A"
                },
                "output_olein_quantity": Decimal("600.0"),
                "output_stearin_quantity": Decimal("350.0"),
                "output_other_quantity": Decimal("50.0"),
                "iv_value": Decimal("52.0"),  # Iodine Value
                "melting_point": Decimal("24.0"),
                "solid_fat_content": {
                    "at_10c": "65%",
                    "at_20c": "45%",
                    "at_30c": "15%"
                },
                "color_grade": "A",
                "refining_loss": Decimal("2.0"),
                "fractionation_yield_olein": Decimal("60.0"),
                "fractionation_yield_stearin": Decimal("35.0"),
                "temperature_profile": {
                    "degumming": "80°C",
                    "neutralization": "90°C",
                    "bleaching": "110°C",
                    "deodorization": "240°C"
                },
                "pressure_profile": {
                    "degumming": "1.0 bar",
                    "neutralization": "1.2 bar",
                    "bleaching": "0.8 bar",
                    "deodorization": "0.1 bar"
                },
                "energy_consumed": Decimal("200.0"),  # kWh
                "water_consumed": Decimal("5.0"),  # m³
                "chemicals_used": {
                    "phosphoric_acid": "2.0 kg",
                    "caustic_soda": "5.0 kg",
                    "bleaching_earth": "10.0 kg"
                }
            }
        }
    
    def _get_manufacturer_template(self, input_batch_data: Optional[Dict] = None) -> Dict[str, Any]:
        """Get manufacturer-specific template for manufacturing transformations."""
        return {
            "manufacturer_data": {
                "product_type": "soap",
                "product_name": "Premium Palm Oil Soap",
                "product_grade": "A",
                "recipe_ratios": {
                    "palm_oil": 0.6,
                    "coconut_oil": 0.3,
                    "palm_kernel_oil": 0.1
                },
                "total_recipe_quantity": Decimal("1000.0"),
                "recipe_unit": "kg",
                "input_materials": [
                    {"material": "refined_palm_oil", "quantity": 600, "unit": "kg"},
                    {"material": "coconut_oil", "quantity": 300, "unit": "kg"},
                    {"material": "palm_kernel_oil", "quantity": 100, "unit": "kg"}
                ],
                "output_quantity": Decimal("950.0"),
                "output_unit": "kg",
                "production_lot_number": f"LOT-{datetime.now().strftime('%Y%m%d')}-001",
                "packaging_type": "bar",
                "packaging_quantity": Decimal("100.0"),
                "quality_control_tests": {
                    "ph_level": "9.5",
                    "moisture_content": "8.0%",
                    "fatty_acid_profile": "balanced"
                },
                "quality_parameters": {
                    "hardness": "excellent",
                    "lather": "rich",
                    "cleansing_power": "high"
                },
                "batch_testing_results": {
                    "microbial_count": "within_limits",
                    "heavy_metals": "below_threshold",
                    "allergen_testing": "negative"
                },
                "production_line": "Line-01",
                "production_shift": "Day",
                "production_speed": Decimal("50.0"),  # units/hour
                "energy_consumed": Decimal("100.0"),  # kWh
                "water_consumed": Decimal("2.0"),  # m³
                "waste_generated": Decimal("50.0")  # kg
            }
        }
    
    def _get_default_process_description(self, transformation_type: TransformationType) -> str:
        """Get default process description based on transformation type."""
        descriptions = {
            TransformationType.HARVEST: "Harvest fresh fruit bunches from palm plantation",
            TransformationType.MILLING: "Extract crude palm oil from fresh fruit bunches",
            TransformationType.REFINING: "Refine crude palm oil into refined palm oil",
            TransformationType.MANUFACTURING: "Manufacture finished products from refined palm oil"
        }
        return descriptions.get(transformation_type, "Process raw materials into finished products")
    
    def _get_default_quality_metrics(self, transformation_type: TransformationType) -> Dict[str, Any]:
        """Get default quality metrics based on transformation type."""
        quality_metrics = {
            TransformationType.HARVEST: {
                "ffb_quality_grade": "A",
                "moisture_content": "25%",
                "free_fatty_acid": "3.5%",
                "oil_content": "25%"
            },
            TransformationType.MILLING: {
                "extraction_rate": "22.5%",
                "cpo_ffa_content": "3.5%",
                "cpo_moisture_content": "0.1%",
                "oil_clarity": "excellent"
            },
            TransformationType.REFINING: {
                "iv_value": "52.0",
                "melting_point": "24°C",
                "color_grade": "A",
                "refining_loss": "2.0%"
            },
            TransformationType.MANUFACTURING: {
                "ph_level": "9.5",
                "moisture_content": "8.0%",
                "hardness": "excellent",
                "lather_quality": "rich"
            }
        }
        return quality_metrics.get(transformation_type, {})
    
    def _get_default_process_parameters(self, transformation_type: TransformationType) -> Dict[str, Any]:
        """Get default process parameters based on transformation type."""
        parameters = {
            TransformationType.HARVEST: {
                "harvest_method": "manual",
                "harvest_time": "early_morning",
                "transportation": "immediate"
            },
            TransformationType.MILLING: {
                "sterilization_time": "90 minutes",
                "sterilization_temp": "130°C",
                "pressing_pressure": "400 bar"
            },
            TransformationType.REFINING: {
                "degumming_temp": "80°C",
                "neutralization_temp": "90°C",
                "bleaching_temp": "110°C",
                "deodorization_temp": "240°C"
            },
            TransformationType.MANUFACTURING: {
                "mixing_time": "30 minutes",
                "mixing_temp": "70°C",
                "cooling_time": "2 hours"
            }
        }
        return parameters.get(transformation_type, {})
    
    def _get_default_efficiency_metrics(self, transformation_type: TransformationType) -> Dict[str, Any]:
        """Get default efficiency metrics based on transformation type."""
        efficiency = {
            TransformationType.HARVEST: {
                "yield_per_hectare": "20.5 MT",
                "labor_efficiency": "high",
                "fuel_efficiency": "optimal"
            },
            TransformationType.MILLING: {
                "extraction_efficiency": "90%",
                "energy_efficiency": "optimal",
                "water_efficiency": "efficient"
            },
            TransformationType.REFINING: {
                "refining_efficiency": "98%",
                "fractionation_efficiency": "95%",
                "energy_efficiency": "high"
            },
            TransformationType.MANUFACTURING: {
                "production_efficiency": "95%",
                "waste_reduction": "minimal",
                "quality_consistency": "excellent"
            }
        }
        return efficiency.get(transformation_type, {})
    
    def _get_default_certifications(self, company_type: str) -> List[str]:
        """Get default certifications based on company type."""
        certifications = {
            "plantation_grower": ["RSPO", "MSPO", "ISCC"],
            "mill_processor": ["RSPO", "MSPO", "ISO 14001"],
            "refinery_crusher": ["RSPO", "MSPO", "ISO 9001"],
            "manufacturer": ["RSPO", "MSPO", "HALAL", "KOSHER"]
        }
        return certifications.get(company_type, ["RSPO"])
    
    def _get_default_compliance_data(self, company_type: str) -> Dict[str, Any]:
        """Get default compliance data based on company type."""
        compliance = {
            "plantation_grower": {
                "rspo_status": "certified",
                "mspo_status": "certified",
                "environmental_compliance": "excellent",
                "social_compliance": "excellent"
            },
            "mill_processor": {
                "rspo_status": "certified",
                "mspo_status": "certified",
                "environmental_compliance": "excellent",
                "food_safety": "excellent"
            },
            "refinery_crusher": {
                "rspo_status": "certified",
                "mspo_status": "certified",
                "environmental_compliance": "excellent",
                "food_safety": "excellent"
            },
            "manufacturer": {
                "rspo_status": "certified",
                "mspo_status": "certified",
                "halal_certification": "certified",
                "kosher_certification": "certified"
            }
        }
        return compliance.get(company_type, {"rspo_status": "certified"})
    
    def _get_default_location_coordinates(self) -> Dict[str, float]:
        """Get default location coordinates (Malaysia center)."""
        return {
            "latitude": 3.1390,
            "longitude": 101.6869,
            "accuracy_meters": 10
        }
    
    def _get_default_weather_conditions(self, transformation_type: TransformationType) -> Dict[str, Any]:
        """Get default weather conditions based on transformation type."""
        if transformation_type == TransformationType.HARVEST:
            return {
                "temperature": "28°C",
                "humidity": "85%",
                "rainfall": "none",
                "wind_speed": "5 km/h"
            }
        return {
            "temperature": "25°C",
            "humidity": "60%",
            "conditions": "optimal"
        }
    
    def create_output_batch_suggestion(
        self, 
        transformation_type: TransformationType, 
        input_batch_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create output batch suggestion based on transformation type and input."""
        base_quantity = input_batch_data.get("quantity", 1000.0)
        
        # Calculate output quantity based on transformation type and typical yields
        output_quantities = {
            TransformationType.HARVEST: base_quantity,  # FFB quantity
            TransformationType.MILLING: base_quantity * 0.225,  # 22.5% OER
            TransformationType.REFINING: base_quantity * 0.98,  # 2% refining loss
            TransformationType.MANUFACTURING: base_quantity * 0.95  # 5% manufacturing loss
        }
        
        output_quantity = output_quantities.get(transformation_type, base_quantity * 0.9)
        
        return {
            "batch_id": f"OUT-{transformation_type.value}-{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "quantity": float(output_quantity),
            "unit": input_batch_data.get("unit", "kg"),
            "quality_grade": "A",
            "production_date": date.today(),
            "expiry_date": self._calculate_expiry_date(transformation_type),
            "location_name": "Processing Facility",
            "batch_metadata": {
                "created_from_transformation": True,
                "transformation_type": transformation_type.value,
                "input_batch_id": input_batch_data.get("batch_id"),
                "yield_percentage": (output_quantity / base_quantity * 100) if base_quantity > 0 else 0
            }
        }
    
    def _calculate_expiry_date(self, transformation_type: TransformationType) -> date:
        """Calculate expiry date based on transformation type."""
        from datetime import timedelta
        
        expiry_days = {
            TransformationType.HARVEST: 7,  # FFB expires quickly
            TransformationType.MILLING: 365,  # CPO has longer shelf life
            TransformationType.REFINING: 730,  # Refined oil has longest shelf life
            TransformationType.MANUFACTURING: 1095  # Finished products have longest shelf life
        }
        
        days = expiry_days.get(transformation_type, 365)
        return date.today() + timedelta(days=days)

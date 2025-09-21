"""
Industry standards configuration for transformation templates.

This module provides configurable industry standards and business rules
for different transformation types and company types.
"""
from typing import Dict, Any, List
from decimal import Decimal
from dataclasses import dataclass, field
from enum import Enum


class IndustryType(Enum):
    """Industry types for different standards."""
    PALM_OIL = "palm_oil"
    SOYBEAN = "soybean"
    COCONUT = "coconut"
    GENERAL_AGRICULTURE = "general_agriculture"


class RegionType(Enum):
    """Regional standards for different geographical areas."""
    SOUTHEAST_ASIA = "southeast_asia"
    SOUTH_AMERICA = "south_america"
    AFRICA = "africa"
    EUROPE = "europe"
    NORTH_AMERICA = "north_america"


@dataclass
class QualityStandards:
    """Quality standards for different transformation types."""
    
    # Palm Oil Standards
    palm_oil_cpo_ffa_max: Decimal = field(default_factory=lambda: Decimal("5.0"))
    palm_oil_cpo_moisture_max: Decimal = field(default_factory=lambda: Decimal("0.1"))
    palm_oil_cpo_iodine_min: Decimal = field(default_factory=lambda: Decimal("50.0"))
    palm_oil_cpo_iodine_max: Decimal = field(default_factory=lambda: Decimal("55.0"))
    
    # Refined Oil Standards
    refined_oil_ffa_max: Decimal = field(default_factory=lambda: Decimal("0.1"))
    refined_oil_moisture_max: Decimal = field(default_factory=lambda: Decimal("0.05"))
    refined_oil_peroxide_max: Decimal = field(default_factory=lambda: Decimal("2.0"))
    
    # Color Grade Standards
    color_grades: List[str] = field(default_factory=lambda: ["A1", "A2", "B1", "B2", "C1", "C2"])
    
    # Purity Standards
    min_purity_percentage: Decimal = field(default_factory=lambda: Decimal("95.0"))


@dataclass
class ProcessStandards:
    """Process standards for different transformation types."""
    
    # Temperature Ranges (Celsius)
    plantation_harvest_temp_min: Decimal = field(default_factory=lambda: Decimal("25.0"))
    plantation_harvest_temp_max: Decimal = field(default_factory=lambda: Decimal("35.0"))
    mill_processing_temp_min: Decimal = field(default_factory=lambda: Decimal("80.0"))
    mill_processing_temp_max: Decimal = field(default_factory=lambda: Decimal("100.0"))
    refinery_processing_temp_min: Decimal = field(default_factory=lambda: Decimal("200.0"))
    refinery_processing_temp_max: Decimal = field(default_factory=lambda: Decimal("250.0"))
    
    # Pressure Ranges (Bar)
    mill_processing_pressure_min: Decimal = field(default_factory=lambda: Decimal("1.0"))
    mill_processing_pressure_max: Decimal = field(default_factory=lambda: Decimal("3.0"))
    refinery_processing_pressure_min: Decimal = field(default_factory=lambda: Decimal("0.1"))
    refinery_processing_pressure_max: Decimal = field(default_factory=lambda: Decimal("0.5"))
    
    # Duration Ranges (Hours)
    plantation_harvest_duration_min: Decimal = field(default_factory=lambda: Decimal("1.0"))
    plantation_harvest_duration_max: Decimal = field(default_factory=lambda: Decimal("8.0"))
    mill_processing_duration_min: Decimal = field(default_factory=lambda: Decimal("2.0"))
    mill_processing_duration_max: Decimal = field(default_factory=lambda: Decimal("12.0"))
    refinery_processing_duration_min: Decimal = field(default_factory=lambda: Decimal("4.0"))
    refinery_processing_duration_max: Decimal = field(default_factory=lambda: Decimal("24.0"))
    
    # Energy Consumption (kWh per tonne)
    mill_energy_consumption_min: Decimal = field(default_factory=lambda: Decimal("50.0"))
    mill_energy_consumption_max: Decimal = field(default_factory=lambda: Decimal("200.0"))
    refinery_energy_consumption_min: Decimal = field(default_factory=lambda: Decimal("100.0"))
    refinery_energy_consumption_max: Decimal = field(default_factory=lambda: Decimal("400.0"))


@dataclass
class EfficiencyStandards:
    """Efficiency standards for different transformation types."""
    
    # Yield Ranges (Percentage)
    plantation_harvest_yield_min: Decimal = field(default_factory=lambda: Decimal("15.0"))
    plantation_harvest_yield_max: Decimal = field(default_factory=lambda: Decimal("25.0"))
    mill_extraction_yield_min: Decimal = field(default_factory=lambda: Decimal("18.0"))
    mill_extraction_yield_max: Decimal = field(default_factory=lambda: Decimal("25.0"))
    refinery_yield_min: Decimal = field(default_factory=lambda: Decimal("95.0"))
    refinery_yield_max: Decimal = field(default_factory=lambda: Decimal("98.0"))
    
    # Waste Ranges (Percentage)
    plantation_waste_max: Decimal = field(default_factory=lambda: Decimal("5.0"))
    mill_waste_max: Decimal = field(default_factory=lambda: Decimal("10.0"))
    refinery_waste_max: Decimal = field(default_factory=lambda: Decimal("3.0"))
    
    # Processing Time (Hours)
    plantation_harvest_time_min: Decimal = field(default_factory=lambda: Decimal("2.0"))
    plantation_harvest_time_max: Decimal = field(default_factory=lambda: Decimal("6.0"))
    mill_processing_time_min: Decimal = field(default_factory=lambda: Decimal("4.0"))
    mill_processing_time_max: Decimal = field(default_factory=lambda: Decimal("8.0"))
    refinery_processing_time_min: Decimal = field(default_factory=lambda: Decimal("6.0"))
    refinery_processing_time_max: Decimal = field(default_factory=lambda: Decimal("12.0"))


@dataclass
class CertificationStandards:
    """Certification standards for different regions and industries."""
    
    # RSPO Standards
    rspo_certification_types: List[str] = field(default_factory=lambda: [
        "RSPO Identity Preserved",
        "RSPO Segregated", 
        "RSPO Mass Balance",
        "RSPO Book & Claim"
    ])
    
    # ISCC Standards
    iscc_certification_types: List[str] = field(default_factory=lambda: [
        "ISCC EU",
        "ISCC Plus",
        "ISCC CORSIA"
    ])
    
    # Organic Standards
    organic_certification_types: List[str] = field(default_factory=lambda: [
        "USDA Organic",
        "EU Organic",
        "JAS Organic",
        "NOP Organic"
    ])
    
    # Sustainability Standards
    sustainability_certification_types: List[str] = field(default_factory=lambda: [
        "Rainforest Alliance",
        "UTZ Certified",
        "Fair Trade",
        "MSC Certified"
    ])


@dataclass
class RegionalStandards:
    """Regional standards for different geographical areas."""
    
    # Southeast Asia (Malaysia, Indonesia, Thailand)
    southeast_asia: Dict[str, Any] = field(default_factory=lambda: {
        "climate": "tropical",
        "harvest_season": "year_round",
        "average_temperature": Decimal("28.0"),
        "average_humidity": Decimal("80.0"),
        "common_certifications": ["RSPO", "ISCC", "MSPO"],
        "regulatory_requirements": ["Malaysian Palm Oil Board", "Indonesian Palm Oil Board"]
    })
    
    # South America (Brazil, Colombia, Ecuador)
    south_america: Dict[str, Any] = field(default_factory=lambda: {
        "climate": "tropical_subtropical",
        "harvest_season": "seasonal",
        "average_temperature": Decimal("26.0"),
        "average_humidity": Decimal("75.0"),
        "common_certifications": ["RSPO", "ISCC", "Rainforest Alliance"],
        "regulatory_requirements": ["Brazilian Ministry of Agriculture", "Colombian Agricultural Institute"]
    })
    
    # Africa (Nigeria, Ghana, Côte d'Ivoire)
    africa: Dict[str, Any] = field(default_factory=lambda: {
        "climate": "tropical",
        "harvest_season": "seasonal",
        "average_temperature": Decimal("27.0"),
        "average_humidity": Decimal("70.0"),
        "common_certifications": ["RSPO", "Fair Trade", "Rainforest Alliance"],
        "regulatory_requirements": ["National Agricultural Research Institutes"]
    })


@dataclass
class IndustryStandardsConfig:
    """Main configuration class for industry standards."""
    
    quality: QualityStandards = field(default_factory=QualityStandards)
    process: ProcessStandards = field(default_factory=ProcessStandards)
    efficiency: EfficiencyStandards = field(default_factory=EfficiencyStandards)
    certification: CertificationStandards = field(default_factory=CertificationStandards)
    regional: RegionalStandards = field(default_factory=RegionalStandards)
    
    def get_standards_for_region(self, region: RegionType) -> Dict[str, Any]:
        """Get standards for a specific region."""
        return getattr(self.regional, region.value, {})
    
    def get_quality_standards_for_industry(self, industry: IndustryType) -> Dict[str, Any]:
        """Get quality standards for a specific industry."""
        if industry == IndustryType.PALM_OIL:
            return {
                "ffa_max": self.quality.palm_oil_cpo_ffa_max,
                "moisture_max": self.quality.palm_oil_cpo_moisture_max,
                "iodine_min": self.quality.palm_oil_cpo_iodine_min,
                "iodine_max": self.quality.palm_oil_cpo_iodine_max,
                "color_grades": self.quality.color_grades,
                "min_purity": self.quality.min_purity_percentage
            }
        return {}
    
    def get_process_standards_for_transformation(self, transformation_type: str) -> Dict[str, Any]:
        """Get process standards for a specific transformation type."""
        if transformation_type == "harvest":
            return {
                "temp_min": self.process.plantation_harvest_temp_min,
                "temp_max": self.process.plantation_harvest_temp_max,
                "duration_min": self.process.plantation_harvest_duration_min,
                "duration_max": self.process.plantation_harvest_duration_max
            }
        elif transformation_type == "milling":
            return {
                "temp_min": self.process.mill_processing_temp_min,
                "temp_max": self.process.mill_processing_temp_max,
                "pressure_min": self.process.mill_processing_pressure_min,
                "pressure_max": self.process.mill_processing_pressure_max,
                "duration_min": self.process.mill_processing_duration_min,
                "duration_max": self.process.mill_processing_duration_max,
                "energy_min": self.process.mill_energy_consumption_min,
                "energy_max": self.process.mill_energy_consumption_max
            }
        elif transformation_type == "refining":
            return {
                "temp_min": self.process.refinery_processing_temp_min,
                "temp_max": self.process.refinery_processing_temp_max,
                "pressure_min": self.process.refinery_processing_pressure_min,
                "pressure_max": self.process.refinery_processing_pressure_max,
                "duration_min": self.process.refinery_processing_duration_min,
                "duration_max": self.process.refinery_processing_duration_max,
                "energy_min": self.process.refinery_energy_consumption_min,
                "energy_max": self.process.refinery_energy_consumption_max
            }
        return {}
    
    def get_efficiency_standards_for_transformation(self, transformation_type: str) -> Dict[str, Any]:
        """Get efficiency standards for a specific transformation type."""
        if transformation_type == "harvest":
            return {
                "yield_min": self.efficiency.plantation_harvest_yield_min,
                "yield_max": self.efficiency.plantation_harvest_yield_max,
                "waste_max": self.efficiency.plantation_waste_max,
                "time_min": self.efficiency.plantation_harvest_time_min,
                "time_max": self.efficiency.plantation_harvest_time_max
            }
        elif transformation_type == "milling":
            return {
                "yield_min": self.efficiency.mill_extraction_yield_min,
                "yield_max": self.efficiency.mill_extraction_yield_max,
                "waste_max": self.efficiency.mill_waste_max,
                "time_min": self.efficiency.mill_processing_time_min,
                "time_max": self.efficiency.mill_processing_time_max
            }
        elif transformation_type == "refining":
            return {
                "yield_min": self.efficiency.refinery_yield_min,
                "yield_max": self.efficiency.refinery_yield_max,
                "waste_max": self.efficiency.refinery_waste_max,
                "time_min": self.efficiency.refinery_processing_time_min,
                "time_max": self.efficiency.refinery_processing_time_max
            }
        return {}


# Global configuration instance
industry_standards = IndustryStandardsConfig()


def get_industry_standards() -> IndustryStandardsConfig:
    """Get the global industry standards configuration."""
    return industry_standards


def get_standards_for_company_type(company_type: str, region: RegionType = RegionType.SOUTHEAST_ASIA) -> Dict[str, Any]:
    """Get standards for a specific company type and region."""
    config = get_industry_standards()
    
    # Map company types to transformation types
    transformation_mapping = {
        "plantation_grower": "harvest",
        "mill_processor": "milling", 
        "refinery_crusher": "refining",
        "manufacturer": "manufacturing"
    }
    
    transformation_type = transformation_mapping.get(company_type)
    if not transformation_type:
        return {}
    
    standards = {
        "quality": config.get_quality_standards_for_industry(IndustryType.PALM_OIL),
        "process": config.get_process_standards_for_transformation(transformation_type),
        "efficiency": config.get_efficiency_standards_for_transformation(transformation_type),
        "regional": config.get_standards_for_region(region),
        "certification": {
            "types": config.certification.rspo_certification_types + 
                   config.certification.iscc_certification_types +
                   config.certification.organic_certification_types +
                   config.certification.sustainability_certification_types
        }
    }
    
    return standards

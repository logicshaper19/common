"""
Enums and constants for origin validation.

This module contains all enumeration types used throughout the origin
validation system, extracted from the original monolithic service.
"""

from enum import Enum


class CertificationBody(str, Enum):
    """Recognized certification bodies for palm oil supply chain."""
    RSPO = "RSPO"  # Roundtable on Sustainable Palm Oil
    NDPE = "NDPE"  # No Deforestation, No Peat, No Exploitation
    ISPO = "ISPO"  # Indonesian Sustainable Palm Oil
    MSPO = "MSPO"  # Malaysian Sustainable Palm Oil
    RTRS = "RTRS"  # Round Table on Responsible Soy
    ISCC = "ISCC"  # International Sustainability and Carbon Certification
    SAN = "SAN"    # Sustainable Agriculture Network
    UTZ = "UTZ"    # UTZ Certified
    RAINFOREST_ALLIANCE = "Rainforest Alliance"
    ORGANIC = "Organic"
    FAIR_TRADE = "Fair Trade"
    NON_GMO = "Non-GMO"
    SUSTAINABLE = "Sustainable"
    TRACEABLE = "Traceable"

    @classmethod
    def get_description(cls, certification: 'CertificationBody') -> str:
        """Get human-readable description for certification body."""
        descriptions = {
            cls.RSPO: "Roundtable on Sustainable Palm Oil - Global standard for sustainable palm oil",
            cls.NDPE: "No Deforestation, No Peat, No Exploitation - Environmental protection standard",
            cls.ISPO: "Indonesian Sustainable Palm Oil - Indonesian national standard",
            cls.MSPO: "Malaysian Sustainable Palm Oil - Malaysian national standard",
            cls.RTRS: "Round Table on Responsible Soy - Responsible soy production standard",
            cls.ISCC: "International Sustainability and Carbon Certification - EU recognized standard",
            cls.SAN: "Sustainable Agriculture Network - Biodiversity conservation standard",
            cls.UTZ: "UTZ Certified - Sustainable farming standard",
            cls.RAINFOREST_ALLIANCE: "Rainforest Alliance - Environmental and social sustainability",
            cls.ORGANIC: "Organic certification - Chemical-free production",
            cls.FAIR_TRADE: "Fair Trade certification - Ethical trading practices",
            cls.NON_GMO: "Non-GMO certification - Non-genetically modified organisms",
            cls.SUSTAINABLE: "General sustainability certification",
            cls.TRACEABLE: "Traceability certification - Supply chain transparency"
        }
        return descriptions.get(certification, f"Certification: {certification.value}")

    @classmethod
    def get_high_value_certifications(cls) -> set['CertificationBody']:
        """Get set of high-value certifications for quality scoring."""
        return {
            cls.RSPO,
            cls.NDPE,
            cls.ISPO,
            cls.MSPO,
            cls.RAINFOREST_ALLIANCE,
            cls.ORGANIC,
            cls.FAIR_TRADE
        }


class PalmOilRegion(str, Enum):
    """Major palm oil producing regions with geographic boundaries."""
    SOUTHEAST_ASIA = "Southeast Asia"
    WEST_AFRICA = "West Africa"
    CENTRAL_AFRICA = "Central Africa"
    SOUTH_AMERICA = "South America"
    CENTRAL_AMERICA = "Central America"
    OCEANIA = "Oceania"

    @classmethod
    def get_description(cls, region: 'PalmOilRegion') -> str:
        """Get detailed description for palm oil region."""
        descriptions = {
            cls.SOUTHEAST_ASIA: "Indonesia, Malaysia, Thailand, Philippines - Major global producers",
            cls.WEST_AFRICA: "Nigeria, Ghana, Ivory Coast, Cameroon - Growing production region",
            cls.CENTRAL_AFRICA: "Democratic Republic of Congo, Gabon - Emerging production",
            cls.SOUTH_AMERICA: "Colombia, Ecuador, Brazil - Expanding cultivation",
            cls.CENTRAL_AMERICA: "Guatemala, Honduras, Costa Rica - Small-scale production",
            cls.OCEANIA: "Papua New Guinea, Solomon Islands - Island nation production"
        }
        return descriptions.get(region, f"Region: {region.value}")

    @classmethod
    def get_major_producers(cls, region: 'PalmOilRegion') -> list[str]:
        """Get list of major producing countries in region."""
        producers = {
            cls.SOUTHEAST_ASIA: ["Indonesia", "Malaysia", "Thailand", "Philippines"],
            cls.WEST_AFRICA: ["Nigeria", "Ghana", "Ivory Coast", "Cameroon"],
            cls.CENTRAL_AFRICA: ["Democratic Republic of Congo", "Gabon"],
            cls.SOUTH_AMERICA: ["Colombia", "Ecuador", "Brazil"],
            cls.CENTRAL_AMERICA: ["Guatemala", "Honduras", "Costa Rica"],
            cls.OCEANIA: ["Papua New Guinea", "Solomon Islands"]
        }
        return producers.get(region, [])


class ComplianceStatus(str, Enum):
    """Overall compliance status for origin data."""
    EXCELLENT = "excellent"
    GOOD = "good"
    ACCEPTABLE = "acceptable"
    NEEDS_IMPROVEMENT = "needs_improvement"
    NON_COMPLIANT = "non_compliant"

    @classmethod
    def from_quality_score(cls, score: float) -> 'ComplianceStatus':
        """Determine compliance status from quality score."""
        if score >= 0.9:
            return cls.EXCELLENT
        elif score >= 0.8:
            return cls.GOOD
        elif score >= 0.7:
            return cls.ACCEPTABLE
        elif score >= 0.5:
            return cls.NEEDS_IMPROVEMENT
        else:
            return cls.NON_COMPLIANT

    @classmethod
    def get_description(cls, status: 'ComplianceStatus') -> str:
        """Get description for compliance status."""
        descriptions = {
            cls.EXCELLENT: "Exceeds all requirements with high-quality data",
            cls.GOOD: "Meets all requirements with good data quality",
            cls.ACCEPTABLE: "Meets minimum requirements",
            cls.NEEDS_IMPROVEMENT: "Some requirements not met, improvement needed",
            cls.NON_COMPLIANT: "Significant compliance issues requiring attention"
        }
        return descriptions.get(status, f"Status: {status.value}")


class ValidationSeverity(str, Enum):
    """Severity levels for validation messages."""
    ERROR = "error"
    WARNING = "warning"
    SUGGESTION = "suggestion"
    INFO = "info"


class AccuracyLevel(str, Enum):
    """GPS accuracy levels for coordinate validation."""
    EXCELLENT = "excellent"  # <= 5m
    GOOD = "good"           # <= 20m
    MODERATE = "moderate"   # <= 50m
    LOW = "low"            # <= 100m
    POOR = "poor"          # > 100m

    @classmethod
    def from_accuracy_meters(cls, accuracy_meters: float) -> 'AccuracyLevel':
        """Determine accuracy level from meters."""
        if accuracy_meters <= 5:
            return cls.EXCELLENT
        elif accuracy_meters <= 20:
            return cls.GOOD
        elif accuracy_meters <= 50:
            return cls.MODERATE
        elif accuracy_meters <= 100:
            return cls.LOW
        else:
            return cls.POOR

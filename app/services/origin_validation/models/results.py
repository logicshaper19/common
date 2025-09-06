"""
Result data classes for origin validation.

This module contains all result data structures returned by the validation
system, providing a clean interface for validation outcomes.
"""

from dataclasses import dataclass
from typing import Dict, Any, List, Optional
from .enums import ComplianceStatus, PalmOilRegion


@dataclass
class OriginDataValidationResult:
    """Comprehensive origin data validation result."""
    is_valid: bool
    coordinate_validation: Dict[str, Any]
    certification_validation: Dict[str, Any]
    harvest_date_validation: Dict[str, Any]
    regional_compliance: Dict[str, Any]
    quality_score: float
    errors: List[str]
    warnings: List[str]
    suggestions: List[str]
    compliance_status: str

    def __post_init__(self):
        """Validate result data after initialization."""
        if not 0 <= self.quality_score <= 1:
            raise ValueError("Quality score must be between 0 and 1")
        
        if self.compliance_status not in [status.value for status in ComplianceStatus]:
            raise ValueError(f"Invalid compliance status: {self.compliance_status}")

    @property
    def has_errors(self) -> bool:
        """Check if validation has any errors."""
        return len(self.errors) > 0

    @property
    def has_warnings(self) -> bool:
        """Check if validation has any warnings."""
        return len(self.warnings) > 0

    @property
    def total_issues(self) -> int:
        """Get total number of issues (errors + warnings)."""
        return len(self.errors) + len(self.warnings)

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the validation result."""
        return {
            "is_valid": self.is_valid,
            "quality_score": self.quality_score,
            "compliance_status": self.compliance_status,
            "issues_count": {
                "errors": len(self.errors),
                "warnings": len(self.warnings),
                "suggestions": len(self.suggestions)
            },
            "validation_areas": {
                "coordinates": self.coordinate_validation.get("is_valid", False),
                "certifications": self.certification_validation.get("is_valid", False),
                "harvest_date": self.harvest_date_validation.get("is_valid", False),
                "regional_compliance": self.regional_compliance.get("is_valid", False)
            }
        }


@dataclass
class ValidationMessage:
    """Individual validation message with severity and context."""
    message: str
    severity: str  # error, warning, suggestion, info
    field: Optional[str] = None
    code: Optional[str] = None
    context: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        """Validate message data after initialization."""
        valid_severities = ["error", "warning", "suggestion", "info"]
        if self.severity not in valid_severities:
            raise ValueError(f"Invalid severity: {self.severity}")


@dataclass
class CoordinateValidationResult:
    """Result of coordinate validation."""
    is_valid: bool
    detected_region: Optional[PalmOilRegion]
    accuracy_level: str
    elevation_valid: bool
    messages: List[ValidationMessage]
    metadata: Dict[str, Any]

    @property
    def has_region(self) -> bool:
        """Check if coordinates are within a known palm oil region."""
        return self.detected_region is not None

    @property
    def accuracy_score(self) -> float:
        """Get accuracy score based on GPS precision."""
        accuracy_scores = {
            "excellent": 1.0,
            "good": 0.9,
            "moderate": 0.7,
            "low": 0.5,
            "poor": 0.3
        }
        return accuracy_scores.get(self.accuracy_level, 0.0)


@dataclass
class CertificationValidationResult:
    """Result of certification validation."""
    is_valid: bool
    recognized_certifications: List[str]
    unrecognized_certifications: List[str]
    quality_score: float
    regional_compliance: bool
    messages: List[ValidationMessage]
    metadata: Dict[str, Any]

    @property
    def recognition_rate(self) -> float:
        """Get percentage of recognized certifications."""
        total = len(self.recognized_certifications) + len(self.unrecognized_certifications)
        if total == 0:
            return 0.0
        return len(self.recognized_certifications) / total

    @property
    def has_high_value_certs(self) -> bool:
        """Check if any high-value certifications are present."""
        from .enums import CertificationBody
        high_value = CertificationBody.get_high_value_certifications()
        return any(cert in [hv.value for hv in high_value] for cert in self.recognized_certifications)


@dataclass
class HarvestDateValidationResult:
    """Result of harvest date validation."""
    is_valid: bool
    date_provided: bool
    freshness_score: float
    seasonal_compliance: bool
    messages: List[ValidationMessage]
    metadata: Dict[str, Any]

    @property
    def is_fresh(self) -> bool:
        """Check if harvest is considered fresh (high freshness score)."""
        return self.freshness_score >= 0.8


@dataclass
class RegionalComplianceResult:
    """Result of regional compliance validation."""
    is_valid: bool
    region: Optional[str]
    compliance_score: float
    compliance_level: str
    requirements_met: List[str]
    requirements_missing: List[str]
    messages: List[ValidationMessage]
    metadata: Dict[str, Any]

    @property
    def compliance_rate(self) -> float:
        """Get percentage of requirements met."""
        total = len(self.requirements_met) + len(self.requirements_missing)
        if total == 0:
            return 1.0
        return len(self.requirements_met) / total

    @property
    def is_compliant(self) -> bool:
        """Check if region is compliant based on compliance level."""
        if self.compliance_level == "mandatory":
            return len(self.requirements_missing) == 0
        elif self.compliance_level == "recommended":
            return self.compliance_score >= 0.7
        else:  # optional
            return True

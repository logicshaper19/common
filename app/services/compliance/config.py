"""
Configuration for compliance services.
"""
from decimal import Decimal
from typing import Dict, Any
from pydantic import BaseModel, Field


class RiskAssessmentConfig(BaseModel):
    """Configuration for risk assessment calculations."""
    
    # Risk factors
    plantation_risk_factor: Decimal = Field(default=Decimal('0.3'), description="Risk factor for plantation companies")
    mill_risk_factor: Decimal = Field(default=Decimal('0.2'), description="Risk factor for mill companies")
    trace_depth_risk_factor: Decimal = Field(default=Decimal('0.1'), description="Risk factor for trace depth")
    max_risk_score: Decimal = Field(default=Decimal('1.0'), description="Maximum risk score")
    
    # Traceability scoring
    plantation_traceability_bonus: Decimal = Field(default=Decimal('0.4'), description="Bonus for tracing to plantation")
    mill_traceability_bonus: Decimal = Field(default=Decimal('0.3'), description="Bonus for tracing to mill")
    depth_traceability_bonus: Decimal = Field(default=Decimal('0.3'), description="Bonus for trace depth")
    max_traceability_score: Decimal = Field(default=Decimal('1.0'), description="Maximum traceability score")
    
    # Risk thresholds
    low_risk_threshold: Decimal = Field(default=Decimal('0.3'), description="Low risk threshold")
    medium_risk_threshold: Decimal = Field(default=Decimal('0.6'), description="Medium risk threshold")
    high_risk_threshold: Decimal = Field(default=Decimal('0.8'), description="High risk threshold")


class MassBalanceConfig(BaseModel):
    """Configuration for mass balance calculations."""
    
    # Yield calculations
    min_yield_percentage: Decimal = Field(default=Decimal('0.0'), description="Minimum yield percentage")
    max_yield_percentage: Decimal = Field(default=Decimal('100.0'), description="Maximum yield percentage")
    default_yield_percentage: Decimal = Field(default=Decimal('85.0'), description="Default yield percentage")
    
    # Waste calculations
    min_waste_percentage: Decimal = Field(default=Decimal('0.0'), description="Minimum waste percentage")
    max_waste_percentage: Decimal = Field(default=Decimal('100.0'), description="Maximum waste percentage")
    
    # Validation
    max_yield_waste_sum: Decimal = Field(default=Decimal('100.0'), description="Maximum sum of yield and waste percentages")


class ComplianceConfig(BaseModel):
    """Main compliance configuration."""
    
    # Risk assessment
    risk_assessment: RiskAssessmentConfig = Field(default_factory=RiskAssessmentConfig)
    
    # Mass balance
    mass_balance: MassBalanceConfig = Field(default_factory=MassBalanceConfig)
    
    # Template settings
    template_cache_size: int = Field(default=128, description="Template cache size")
    template_cache_ttl: int = Field(default=3600, description="Template cache TTL in seconds")
    
    # Report settings
    max_report_size: int = Field(default=10 * 1024 * 1024, description="Maximum report size in bytes")
    report_timeout: int = Field(default=300, description="Report generation timeout in seconds")
    
    # Security settings
    sanitize_template_data: bool = Field(default=True, description="Sanitize template data")
    max_supply_chain_depth: int = Field(default=20, description="Maximum supply chain depth")
    
    # Default values
    default_hs_code: str = Field(default="1511.10.00", description="Default HS code for palm oil")
    default_risk_score: Decimal = Field(default=Decimal('0.0'), description="Default risk score")
    
    def get_risk_config(self) -> RiskAssessmentConfig:
        """Get risk assessment configuration."""
        return self.risk_assessment
    
    def get_mass_balance_config(self) -> MassBalanceConfig:
        """Get mass balance configuration."""
        return self.mass_balance


# Global configuration instance
compliance_config = ComplianceConfig()


def get_compliance_config() -> ComplianceConfig:
    """Get the global compliance configuration."""
    return compliance_config


def update_compliance_config(config_dict: Dict[str, Any]) -> None:
    """Update compliance configuration with new values."""
    global compliance_config
    compliance_config = ComplianceConfig(**config_dict)

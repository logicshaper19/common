"""
Template engine for generating compliance reports with caching and error handling.
"""
import os
from pathlib import Path
from typing import Optional, Dict, Any
from functools import lru_cache
from jinja2 import Environment, DictLoader, Template, TemplateNotFound, TemplateError
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.core.logging import get_logger
from app.models.compliance import ComplianceTemplate
from app.services.compliance.exceptions import TemplateNotFoundError, ComplianceDataError
from app.services.compliance.config import get_compliance_config
from app.services.compliance.validators import get_template_sanitizer

logger = get_logger(__name__)


class ComplianceTemplateEngine:
    """Template engine for generating compliance reports with caching and error handling."""
    
    def __init__(self, db: Session):
        self.db = db
        self.sanitizer = get_template_sanitizer()
        self.config = get_compliance_config()
        
        # Initialize Jinja2 environment
        self.jinja_env = Environment(
            loader=DictLoader({}),
            autoescape=True,  # Enable auto-escaping for security
            trim_blocks=True,
            lstrip_blocks=True
        )
    
    @lru_cache(maxsize=128)
    def _get_template(self, regulation_type: str) -> Template:
        """Get template for regulation type with caching."""
        try:
            logger.info("Loading template", regulation_type=regulation_type)
            
            # Try to get template from database first
            template_record = self.db.query(ComplianceTemplate).filter(
                ComplianceTemplate.regulation_type == regulation_type,
                ComplianceTemplate.is_active == True
            ).first()
            
            if template_record:
                template_content = template_record.template_content
                logger.info("Template loaded from database", regulation_type=regulation_type)
            else:
                # Fall back to default template
                template_content = self._get_default_template(regulation_type)
                logger.info("Template loaded from defaults", regulation_type=regulation_type)
            
            # Create Jinja2 template
            template = self.jinja_env.from_string(template_content)
            return template
            
        except SQLAlchemyError as e:
            logger.error("Database error loading template", regulation_type=regulation_type, error=str(e))
            raise ComplianceDataError(f"Failed to load template from database: {e}", original_error=e)
        except TemplateError as e:
            logger.error("Template parsing error", regulation_type=regulation_type, error=str(e))
            raise TemplateNotFoundError(f"Invalid template for {regulation_type}: {e}")
        except Exception as e:
            logger.error("Unexpected error loading template", regulation_type=regulation_type, error=str(e))
            raise TemplateNotFoundError(f"Failed to load template for {regulation_type}: {e}")
    
    def _get_default_template(self, regulation_type: str) -> str:
        """Get default template for regulation type."""
        # Try to load from file first
        template_path = Path(f"app/templates/compliance/{regulation_type.lower()}.xml")
        if template_path.exists():
            try:
                return template_path.read_text(encoding='utf-8')
            except Exception as e:
                logger.warning("Failed to load template file", path=str(template_path), error=str(e))
        
        # Fall back to hardcoded templates
        if regulation_type == 'EUDR':
            return self._get_eudr_template()
        elif regulation_type == 'RSPO':
            return self._get_rspo_template()
        else:
            raise TemplateNotFoundError(f"No template available for regulation type: {regulation_type}")
    
    def _get_eudr_template(self) -> str:
        """Get default EUDR template."""
        return """<?xml version="1.0" encoding="UTF-8"?>
<EUDR_Report>
  <Header>
    <ReportType>EUDR Compliance Report</ReportType>
    <GeneratedAt>{{generated_at}}</GeneratedAt>
    <ReportVersion>1.0</ReportVersion>
  </Header>
  
  <Operator>
    <Name>{{operator.name}}</Name>
    <RegistrationNumber>{{operator.registration_number or 'N/A'}}</RegistrationNumber>
    <Address>{{operator.address or 'N/A'}}</Address>
    <Country>{{operator.country or 'N/A'}}</Country>
  </Operator>
  
  <Product>
    <HS_Code>{{product.hs_code}}</HS_Code>
    <Description>{{product.description}}</Description>
    <Quantity>{{product.quantity}}</Quantity>
    <Unit>{{product.unit}}</Unit>
  </Product>
  
  <SupplyChain>
    <TraceabilityPath>{{trace_path}}</TraceabilityPath>
    <TraceDepth>{{trace_depth}}</TraceDepth>
    <Steps>
      {% for step in supply_chain %}
      <Step>
        <CompanyName>{{step.company_name}}</CompanyName>
        <CompanyType>{{step.company_type}}</CompanyType>
        <Location>{{step.location or 'N/A'}}</Location>
        <Coordinates>{{step.coordinates or 'N/A'}}</Coordinates>
      </Step>
      {% endfor %}
    </Steps>
  </SupplyChain>
  
  <RiskAssessment>
    <DeforestationRisk>{{risk_assessment.deforestation_risk}}</DeforestationRisk>
    <ComplianceScore>{{risk_assessment.compliance_score}}</ComplianceScore>
    <TraceabilityScore>{{risk_assessment.traceability_score}}</TraceabilityScore>
  </RiskAssessment>
  
  <ComplianceDeclaration>
    <DueDiligencePerformed>Yes</DueDiligencePerformed>
    <RiskAssessmentCompleted>Yes</RiskAssessmentCompleted>
    <MitigationMeasuresImplemented>Yes</MitigationMeasuresImplemented>
  </ComplianceDeclaration>
</EUDR_Report>"""
    
    def _get_rspo_template(self) -> str:
        """Get default RSPO template."""
        return """<?xml version="1.0" encoding="UTF-8"?>
<RSPO_Report>
  <Header>
    <ReportType>RSPO Compliance Report</ReportType>
    <GeneratedAt>{{generated_at}}</GeneratedAt>
    <ReportVersion>1.0</ReportVersion>
  </Header>
  
  <Certification>
    <CertificateNumber>{{certification.certificate_number or 'N/A'}}</CertificateNumber>
    <ValidUntil>{{certification.valid_until or 'N/A'}}</ValidUntil>
    <CertificationType>{{certification.certification_type or 'N/A'}}</CertificationType>
  </Certification>
  
  <SupplyChain>
    <TraceabilityPath>{{trace_path}}</TraceabilityPath>
    <TraceDepth>{{trace_depth}}</TraceDepth>
    <Steps>
      {% for step in supply_chain %}
      <Step>
        <CompanyName>{{step.company_name}}</CompanyName>
        <CompanyType>{{step.company_type}}</CompanyType>
        <Location>{{step.location or 'N/A'}}</Location>
        <Coordinates>{{step.coordinates or 'N/A'}}</Coordinates>
      </Step>
      {% endfor %}
    </Steps>
  </SupplyChain>
  
  <MassBalance>
    <InputQuantity>{{mass_balance.input_quantity}}</InputQuantity>
    <OutputQuantity>{{mass_balance.output_quantity}}</OutputQuantity>
    <YieldPercentage>{{mass_balance.yield_percentage}}</YieldPercentage>
    <WastePercentage>{{mass_balance.waste_percentage}}</WastePercentage>
  </MassBalance>
  
  <Sustainability>
    <GHG_Emissions>{{sustainability.ghg_emissions or 'N/A'}}</GHG_Emissions>
    <WaterUsage>{{sustainability.water_usage or 'N/A'}}</WaterUsage>
    <EnergyConsumption>{{sustainability.energy_consumption or 'N/A'}}</EnergyConsumption>
  </Sustainability>
</RSPO_Report>"""
    
    def generate_eudr_report(self, eudr_data: Dict[str, Any]) -> bytes:
        """Generate EUDR compliance report with error handling."""
        try:
            logger.info("Generating EUDR report")
            
            # Get template
            template = self._get_template('EUDR')
            
            # Sanitize data before rendering
            sanitized_data = self.sanitizer.sanitize_template_data(eudr_data)
            
            # Render template
            rendered_content = template.render(**sanitized_data)
            
            # Convert to bytes
            report_bytes = rendered_content.encode('utf-8')
            
            # Validate report size
            if len(report_bytes) > self.config.max_report_size:
                logger.warning("Report size exceeds maximum", size=len(report_bytes), max_size=self.config.max_report_size)
            
            logger.info("EUDR report generated successfully", size=len(report_bytes))
            return report_bytes
            
        except TemplateError as e:
            logger.error("Template rendering error for EUDR", error=str(e))
            raise ComplianceDataError(f"Failed to render EUDR template: {e}", original_error=e)
        except Exception as e:
            logger.error("Unexpected error generating EUDR report", error=str(e))
            raise ComplianceDataError(f"Failed to generate EUDR report: {e}", original_error=e)
    
    def generate_rspo_report(self, rspo_data: Dict[str, Any]) -> bytes:
        """Generate RSPO compliance report with error handling."""
        try:
            logger.info("Generating RSPO report")
            
            # Get template
            template = self._get_template('RSPO')
            
            # Sanitize data before rendering
            sanitized_data = self.sanitizer.sanitize_template_data(rspo_data)
            
            # Render template
            rendered_content = template.render(**sanitized_data)
            
            # Convert to bytes
            report_bytes = rendered_content.encode('utf-8')
            
            # Validate report size
            if len(report_bytes) > self.config.max_report_size:
                logger.warning("Report size exceeds maximum", size=len(report_bytes), max_size=self.config.max_report_size)
            
            logger.info("RSPO report generated successfully", size=len(report_bytes))
            return report_bytes
            
        except TemplateError as e:
            logger.error("Template rendering error for RSPO", error=str(e))
            raise ComplianceDataError(f"Failed to render RSPO template: {e}", original_error=e)
        except Exception as e:
            logger.error("Unexpected error generating RSPO report", error=str(e))
            raise ComplianceDataError(f"Failed to generate RSPO report: {e}", original_error=e)
    
    def clear_template_cache(self) -> None:
        """Clear the template cache."""
        self._get_template.cache_clear()
        logger.info("Template cache cleared")
    
    def get_template_info(self, regulation_type: str) -> Dict[str, Any]:
        """Get information about a template."""
        try:
            template_record = self.db.query(ComplianceTemplate).filter(
                ComplianceTemplate.regulation_type == regulation_type,
                ComplianceTemplate.is_active == True
            ).first()
            
            if template_record:
                return {
                    'name': template_record.name,
                    'version': template_record.version,
                    'source': 'database',
                    'created_at': template_record.created_at,
                    'updated_at': template_record.updated_at
                }
            else:
                return {
                    'name': f'Default {regulation_type} Template',
                    'version': '1.0',
                    'source': 'default',
                    'created_at': None,
                    'updated_at': None
                }
        except Exception as e:
            logger.error("Failed to get template info", regulation_type=regulation_type, error=str(e))
            return {
                'name': f'Unknown {regulation_type} Template',
                'version': 'Unknown',
                'source': 'error',
                'created_at': None,
                'updated_at': None
            }

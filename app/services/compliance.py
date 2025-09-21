"""
Compliance services for EUDR, RSPO, and other regulatory reporting.
"""
from typing import Dict, List, Optional, Any, Tuple
from uuid import UUID
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy.orm import Session
from jinja2 import Environment, DictLoader, Template

from app.core.logging import get_logger
from app.models.compliance import ComplianceTemplate, ComplianceReport, RiskAssessment, MassBalanceCalculation, HSCode
from app.models.purchase_order import PurchaseOrder
from app.models.company import Company
from app.models.product import Product
from app.models.batch import Batch
from app.models.transformation import TransformationEvent
from app.schemas.compliance import (
    EUDRReportData, RSPOReportData, 
    EUDROperatorData, EUDRProductData, EUDRSupplyChainStep, EUDRRiskAssessment,
    RSPOCertificationData, RSPOMassBalance, RSPOSustainabilityMetrics,
    ComplianceReportRequest, ComplianceReportGenerationResponse
)

logger = get_logger(__name__)


class ComplianceDataMapper:
    """Maps existing data to compliance report formats."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def map_po_to_eudr_data(self, po_id: UUID) -> EUDRReportData:
        """Map purchase order data to EUDR report format."""
        # Get purchase order with related data
        po = self.db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
        if not po:
            raise ValueError(f"Purchase order {po_id} not found")
        
        # Get buyer company (operator)
        buyer_company = self.db.query(Company).filter(Company.id == po.buyer_company_id).first()
        operator_data = EUDROperatorData(
            name=buyer_company.name,
            registration_number=buyer_company.registration_number,
            address=buyer_company.address,
            country=buyer_company.country,
            tax_id=buyer_company.tax_id
        )
        
        # Get product data
        product = self.db.query(Product).filter(Product.id == po.product_id).first()
        product_data = EUDRProductData(
            hs_code=product.hs_code or "1511.10.00",  # Default palm oil HS code
            description=product.name,
            quantity=po.quantity,
            unit=po.unit
        )
        
        # Get supply chain trace
        supply_chain_steps = self._get_supply_chain_steps(po_id)
        
        # Calculate risk assessment
        risk_assessment = self._calculate_eudr_risk_assessment(po_id, supply_chain_steps)
        
        return EUDRReportData(
            operator=operator_data,
            product=product_data,
            supply_chain=supply_chain_steps,
            risk_assessment=risk_assessment,
            trace_path=self._build_trace_path(supply_chain_steps),
            trace_depth=len(supply_chain_steps),
            generated_at=datetime.now()
        )
    
    def map_po_to_rspo_data(self, po_id: UUID) -> RSPOReportData:
        """Map purchase order data to RSPO report format."""
        # Get purchase order with related data
        po = self.db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
        if not po:
            raise ValueError(f"Purchase order {po_id} not found")
        
        # Get product certification data
        product = self.db.query(Product).filter(Product.id == po.product_id).first()
        certification_data = RSPOCertificationData(
            certificate_number=product.certification_number,
            valid_until=product.certification_expiry,
            certification_type=product.certification_type,
            certification_body=product.certification_body
        )
        
        # Get supply chain trace
        supply_chain_steps = self._get_supply_chain_steps(po_id)
        
        # Calculate mass balance
        mass_balance = self._calculate_mass_balance(po_id)
        
        # Calculate sustainability metrics
        sustainability = self._calculate_sustainability_metrics(po_id)
        
        return RSPOReportData(
            certification=certification_data,
            supply_chain=supply_chain_steps,
            mass_balance=mass_balance,
            sustainability=sustainability,
            trace_path=self._build_trace_path(supply_chain_steps),
            trace_depth=len(supply_chain_steps),
            generated_at=datetime.now()
        )
    
    def _get_supply_chain_steps(self, po_id: UUID) -> List[EUDRSupplyChainStep]:
        """Get supply chain steps for a purchase order."""
        # This would use your existing supply_chain_traceability view
        # For now, we'll create a simplified version
        
        po = self.db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
        steps = []
        
        # Add buyer (operator)
        buyer_company = self.db.query(Company).filter(Company.id == po.buyer_company_id).first()
        steps.append(EUDRSupplyChainStep(
            company_name=buyer_company.name,
            company_type=buyer_company.company_type,
            location=buyer_company.address,
            coordinates=self._parse_coordinates(buyer_company.location_coordinates),
            step_order=1
        ))
        
        # Add seller
        seller_company = self.db.query(Company).filter(Company.id == po.seller_company_id).first()
        steps.append(EUDRSupplyChainStep(
            company_name=seller_company.name,
            company_type=seller_company.company_type,
            location=seller_company.address,
            coordinates=self._parse_coordinates(seller_company.location_coordinates),
            step_order=2
        ))
        
        # TODO: Add more steps from supply_chain_traceability view
        # This would require implementing the recursive CTE query
        
        return steps
    
    def _calculate_eudr_risk_assessment(self, po_id: UUID, supply_chain_steps: List[EUDRSupplyChainStep]) -> EUDRRiskAssessment:
        """Calculate EUDR risk assessment."""
        # Basic risk scoring based on available data
        deforestation_risk = Decimal('0.0')
        compliance_score = Decimal('1.0')
        traceability_score = Decimal('0.0')
        
        # Check if traced to plantation
        has_plantation = any(step.company_type == 'plantation_grower' for step in supply_chain_steps)
        if has_plantation:
            deforestation_risk += Decimal('0.3')
            traceability_score += Decimal('0.4')
        
        # Check if traced to mill
        has_mill = any(step.company_type == 'mill_processor' for step in supply_chain_steps)
        if has_mill:
            deforestation_risk += Decimal('0.2')
            traceability_score += Decimal('0.3')
        
        # Check trace depth
        trace_depth = len(supply_chain_steps)
        if trace_depth > 2:
            traceability_score += Decimal('0.3')
        else:
            deforestation_risk += Decimal('0.2')
        
        # Cap scores
        deforestation_risk = min(deforestation_risk, Decimal('1.0'))
        traceability_score = min(traceability_score, Decimal('1.0'))
        compliance_score = Decimal('1.0') - deforestation_risk
        
        return EUDRRiskAssessment(
            deforestation_risk=deforestation_risk,
            compliance_score=compliance_score,
            traceability_score=traceability_score,
            risk_factors={
                'has_plantation': has_plantation,
                'has_mill': has_mill,
                'trace_depth': trace_depth,
                'risk_factors': ['deforestation', 'supply_chain_complexity']
            }
        )
    
    def _calculate_mass_balance(self, po_id: UUID) -> RSPOMassBalance:
        """Calculate mass balance from transformation events."""
        # Get transformation events for this PO
        transformations = self.db.query(TransformationEvent).filter(
            TransformationEvent.input_batches.contains([str(po_id)])
        ).all()
        
        total_input = Decimal('0.0')
        total_output = Decimal('0.0')
        
        for transformation in transformations:
            total_input += transformation.total_input_quantity or Decimal('0.0')
            total_output += transformation.total_output_quantity or Decimal('0.0')
        
        # Calculate percentages
        if total_input > 0:
            yield_percentage = (total_output / total_input) * 100
            waste_percentage = 100 - yield_percentage
        else:
            yield_percentage = Decimal('0.0')
            waste_percentage = Decimal('0.0')
        
        return RSPOMassBalance(
            input_quantity=total_input,
            output_quantity=total_output,
            yield_percentage=yield_percentage,
            waste_percentage=waste_percentage
        )
    
    def _calculate_sustainability_metrics(self, po_id: UUID) -> RSPOSustainabilityMetrics:
        """Calculate sustainability metrics."""
        # Placeholder implementation
        # In a real system, this would calculate actual metrics
        return RSPOSustainabilityMetrics(
            ghg_emissions=Decimal('0.0'),  # Would be calculated from actual data
            water_usage=Decimal('0.0'),    # Would be calculated from actual data
            energy_consumption=Decimal('0.0')  # Would be calculated from actual data
        )
    
    def _build_trace_path(self, supply_chain_steps: List[EUDRSupplyChainStep]) -> str:
        """Build trace path string."""
        return " -> ".join([f"{step.company_name} ({step.company_type})" for step in supply_chain_steps])
    
    def _parse_coordinates(self, coordinates_data: Optional[Dict]) -> Optional[Dict[str, float]]:
        """Parse coordinates from JSONB data."""
        if not coordinates_data:
            return None
        
        if isinstance(coordinates_data, dict):
            return {
                'latitude': float(coordinates_data.get('lat', 0.0)),
                'longitude': float(coordinates_data.get('lng', 0.0))
            }
        
        return None


class ComplianceTemplateEngine:
    """Template engine for generating compliance reports."""
    
    def __init__(self, db: Session):
        self.db = db
        self.data_mapper = ComplianceDataMapper(db)
        self.jinja_env = Environment(loader=DictLoader({}))
    
    def generate_eudr_report(self, po_id: UUID) -> bytes:
        """Generate EUDR compliance report."""
        # Get template
        template = self._get_template('EUDR')
        
        # Map data
        eudr_data = self.data_mapper.map_po_to_eudr_data(po_id)
        
        # Render template
        rendered_content = template.render(
            operator=eudr_data.operator,
            product=eudr_data.product,
            supply_chain=eudr_data.supply_chain,
            risk_assessment=eudr_data.risk_assessment,
            trace_path=eudr_data.trace_path,
            trace_depth=eudr_data.trace_depth,
            generated_at=eudr_data.generated_at
        )
        
        # Convert to PDF (placeholder)
        return self._convert_to_pdf(rendered_content)
    
    def generate_rspo_report(self, po_id: UUID) -> bytes:
        """Generate RSPO compliance report."""
        # Get template
        template = self._get_template('RSPO')
        
        # Map data
        rspo_data = self.data_mapper.map_po_to_rspo_data(po_id)
        
        # Render template
        rendered_content = template.render(
            certification=rspo_data.certification,
            supply_chain=rspo_data.supply_chain,
            mass_balance=rspo_data.mass_balance,
            sustainability=rspo_data.sustainability,
            trace_path=rspo_data.trace_path,
            trace_depth=rspo_data.trace_depth,
            generated_at=rspo_data.generated_at
        )
        
        # Convert to PDF (placeholder)
        return self._convert_to_pdf(rendered_content)
    
    def _get_template(self, regulation_type: str) -> Template:
        """Get template for regulation type."""
        # Get template from database
        template_record = self.db.query(ComplianceTemplate).filter(
            ComplianceTemplate.regulation_type == regulation_type,
            ComplianceTemplate.is_active == True
        ).first()
        
        if not template_record:
            # Use default template
            template_content = self._get_default_template(regulation_type)
        else:
            template_content = template_record.template_content
        
        return self.jinja_env.from_string(template_content)
    
    def _get_default_template(self, regulation_type: str) -> str:
        """Get default template for regulation type."""
        if regulation_type == 'EUDR':
            return """
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
</EUDR_Report>
            """
        elif regulation_type == 'RSPO':
            return """
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
</RSPO_Report>
            """
        else:
            raise ValueError(f"Unknown regulation type: {regulation_type}")
    
    def _convert_to_pdf(self, content: str) -> bytes:
        """Convert rendered content to PDF."""
        # Placeholder implementation
        # In a real system, this would use a PDF generation library like WeasyPrint or ReportLab
        return content.encode('utf-8')


class ComplianceService:
    """Main compliance service for generating reports."""
    
    def __init__(self, db: Session):
        self.db = db
        self.template_engine = ComplianceTemplateEngine(db)
    
    def generate_compliance_report(self, request: ComplianceReportRequest) -> ComplianceReportGenerationResponse:
        """Generate a compliance report."""
        # Generate report based on regulation type
        if request.regulation_type == 'EUDR':
            report_content = self.template_engine.generate_eudr_report(request.po_id)
        elif request.regulation_type == 'RSPO':
            report_content = self.template_engine.generate_rspo_report(request.po_id)
        else:
            raise ValueError(f"Unsupported regulation type: {request.regulation_type}")
        
        # Save report to database
        report = ComplianceReport(
            company_id=self._get_company_id_from_po(request.po_id),
            template_id=self._get_template_id(request.regulation_type),
            po_id=request.po_id,
            report_data=request.custom_data or {},
            file_size=len(report_content),
            status='GENERATED'
        )
        
        self.db.add(report)
        self.db.commit()
        
        return ComplianceReportGenerationResponse(
            report_id=report.id,
            po_id=request.po_id,
            regulation_type=request.regulation_type,
            generated_at=report.generated_at,
            file_size=report.file_size,
            download_url=f"/api/v1/compliance/reports/{report.id}/download",
            status=report.status
        )
    
    def _get_company_id_from_po(self, po_id: UUID) -> UUID:
        """Get company ID from purchase order."""
        po = self.db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
        return po.buyer_company_id
    
    def _get_template_id(self, regulation_type: str) -> UUID:
        """Get template ID for regulation type."""
        template = self.db.query(ComplianceTemplate).filter(
            ComplianceTemplate.regulation_type == regulation_type,
            ComplianceTemplate.is_active == True
        ).first()
        
        if not template:
            # Create default template
            template = ComplianceTemplate(
                name=f"Default {regulation_type} Template",
                regulation_type=regulation_type,
                version="1.0",
                template_content=self.template_engine._get_default_template(regulation_type),
                is_active=True
            )
            self.db.add(template)
            self.db.commit()
        
        return template.id

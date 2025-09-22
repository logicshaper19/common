#!/usr/bin/env python3
"""
Script to populate compliance data for testing.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from app.core.database import Base
from app.models.compliance import HSCode, ComplianceTemplate
from app.core.config import settings

# Create database connection
engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def populate_hs_codes():
    """Populate HS codes for palm oil products."""
    db = SessionLocal()
    
    try:
        # Check if HS codes already exist
        existing_count = db.query(HSCode).count()
        if existing_count > 0:
            print(f"HS codes already exist ({existing_count} records). Skipping...")
            return
        
        # Insert additional HS codes
        hs_codes_data = [
            {
                'code': '1511.10.00',
                'description': 'Crude palm oil',
                'category': 'Vegetable oils',
                'regulation_applicable': ['EUDR', 'RSPO', 'ISCC']
            },
            {
                'code': '1511.90.00',
                'description': 'Other palm oil',
                'category': 'Vegetable oils',
                'regulation_applicable': ['EUDR', 'RSPO', 'ISCC']
            },
            {
                'code': '1513.11.00',
                'description': 'Crude palm kernel oil',
                'category': 'Vegetable oils',
                'regulation_applicable': ['EUDR', 'RSPO', 'ISCC']
            },
            {
                'code': '1513.19.00',
                'description': 'Other palm kernel oil',
                'category': 'Vegetable oils',
                'regulation_applicable': ['EUDR', 'RSPO', 'ISCC']
            },
            {
                'code': '1516.20.00',
                'description': 'Palm oil and its fractions',
                'category': 'Vegetable oils',
                'regulation_applicable': ['EUDR', 'RSPO', 'ISCC']
            },
            {
                'code': '1516.20.10',
                'description': 'Palm oil, crude',
                'category': 'Vegetable oils',
                'regulation_applicable': ['EUDR', 'RSPO', 'ISCC']
            },
            {
                'code': '1516.20.90',
                'description': 'Palm oil, other',
                'category': 'Vegetable oils',
                'regulation_applicable': ['EUDR', 'RSPO', 'ISCC']
            },
            {
                'code': '2306.50.00',
                'description': 'Palm kernel cake',
                'category': 'Animal feed',
                'regulation_applicable': ['RSPO', 'ISCC']
            },
            {
                'code': '2306.60.00',
                'description': 'Palm kernel meal',
                'category': 'Animal feed',
                'regulation_applicable': ['RSPO', 'ISCC']
            }
        ]
        
        for hs_data in hs_codes_data:
            hs_code = HSCode(**hs_data)
            db.add(hs_code)
        
        db.commit()
        print(f"✅ Added {len(hs_codes_data)} HS codes")
        
    except Exception as e:
        print(f"❌ Error populating HS codes: {e}")
        db.rollback()
    finally:
        db.close()

def populate_compliance_templates():
    """Populate default compliance templates."""
    db = SessionLocal()
    
    try:
        # Check if templates already exist
        existing_count = db.query(ComplianceTemplate).count()
        if existing_count > 0:
            print(f"Compliance templates already exist ({existing_count} records). Skipping...")
            return
        
        # EUDR Template
        eudr_template = ComplianceTemplate(
            name="Default EUDR Template",
            regulation_type="EUDR",
            version="1.0",
            template_content="""
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
            """,
            is_active=True
        )
        
        # RSPO Template
        rspo_template = ComplianceTemplate(
            name="Default RSPO Template",
            regulation_type="RSPO",
            version="1.0",
            template_content="""
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
            """,
            is_active=True
        )
        
        db.add(eudr_template)
        db.add(rspo_template)
        db.commit()
        
        print("✅ Added compliance templates (EUDR, RSPO)")
        
    except Exception as e:
        print(f"❌ Error populating compliance templates: {e}")
        db.rollback()
    finally:
        db.close()

def update_products_with_hs_codes():
    """Update existing products with HS codes."""
    db = SessionLocal()
    
    try:
        from app.models.product import Product
        
        # Get products without HS codes
        products_without_hs = db.query(Product).filter(Product.hs_code.is_(None)).all()
        
        if not products_without_hs:
            print("All products already have HS codes. Skipping...")
            return
        
        # Assign default palm oil HS code
        default_hs_code = "1511.10.00"  # Crude palm oil
        
        for product in products_without_hs:
            product.hs_code = default_hs_code
            product.hs_description = "Crude palm oil"
        
        db.commit()
        print(f"✅ Updated {len(products_without_hs)} products with HS codes")
        
    except Exception as e:
        print(f"❌ Error updating products with HS codes: {e}")
        db.rollback()
    finally:
        db.close()

def main():
    """Main function to populate compliance data."""
    print("🚀 Populating compliance data...")
    
    print("\n1. Populating HS codes...")
    populate_hs_codes()
    
    print("\n2. Populating compliance templates...")
    populate_compliance_templates()
    
    print("\n3. Updating products with HS codes...")
    update_products_with_hs_codes()
    
    print("\n✅ Compliance data population completed!")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Simple script to populate compliance data without complex imports.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, text
from app.core.config import settings

# Create database connection
engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def populate_hs_codes():
    """Populate HS codes for palm oil products."""
    db = SessionLocal()
    
    try:
        # Check if HS codes already exist
        result = db.execute(text("SELECT COUNT(*) FROM hs_codes"))
        existing_count = result.scalar()
        
        if existing_count > 0:
            print(f"HS codes already exist ({existing_count} records). Skipping...")
            return
        
        # Insert additional HS codes
        hs_codes_data = [
            ('1511.10.00', 'Crude palm oil', 'Vegetable oils', ['EUDR', 'RSPO', 'ISCC']),
            ('1511.90.00', 'Other palm oil', 'Vegetable oils', ['EUDR', 'RSPO', 'ISCC']),
            ('1513.11.00', 'Crude palm kernel oil', 'Vegetable oils', ['EUDR', 'RSPO', 'ISCC']),
            ('1513.19.00', 'Other palm kernel oil', 'Vegetable oils', ['EUDR', 'RSPO', 'ISCC']),
            ('1516.20.00', 'Palm oil and its fractions', 'Vegetable oils', ['EUDR', 'RSPO', 'ISCC']),
            ('1516.20.10', 'Palm oil, crude', 'Vegetable oils', ['EUDR', 'RSPO', 'ISCC']),
            ('1516.20.90', 'Palm oil, other', 'Vegetable oils', ['EUDR', 'RSPO', 'ISCC']),
            ('2306.50.00', 'Palm kernel cake', 'Animal feed', ['RSPO', 'ISCC']),
            ('2306.60.00', 'Palm kernel meal', 'Animal feed', ['RSPO', 'ISCC'])
        ]
        
        for code, description, category, regulations in hs_codes_data:
            db.execute(text("""
                INSERT INTO hs_codes (code, description, category, regulation_applicable)
                VALUES (:code, :description, :category, :regulations)
            """), {
                'code': code,
                'description': description,
                'category': category,
                'regulations': regulations
            })
        
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
        result = db.execute(text("SELECT COUNT(*) FROM compliance_templates"))
        existing_count = result.scalar()
        
        if existing_count > 0:
            print(f"Compliance templates already exist ({existing_count} records). Skipping...")
            return
        
        # EUDR Template
        eudr_template = """
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
        
        # RSPO Template
        rspo_template = """
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
        
        # Insert templates
        db.execute(text("""
            INSERT INTO compliance_templates (name, regulation_type, version, template_content, is_active)
            VALUES ('Default EUDR Template', 'EUDR', '1.0', :eudr_template, true)
        """), {'eudr_template': eudr_template})
        
        db.execute(text("""
            INSERT INTO compliance_templates (name, regulation_type, version, template_content, is_active)
            VALUES ('Default RSPO Template', 'RSPO', '1.0', :rspo_template, true)
        """), {'rspo_template': rspo_template})
        
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
        # Get products without HS codes
        result = db.execute(text("SELECT COUNT(*) FROM products WHERE hs_code IS NULL"))
        products_without_hs = result.scalar()
        
        if products_without_hs == 0:
            print("All products already have HS codes. Skipping...")
            return
        
        # Assign default palm oil HS code
        default_hs_code = "1511.10.00"  # Crude palm oil
        
        db.execute(text("""
            UPDATE products 
            SET hs_code = :hs_code, hs_description = :hs_description
            WHERE hs_code IS NULL
        """), {
            'hs_code': default_hs_code,
            'hs_description': 'Crude palm oil'
        })
        
        db.commit()
        print(f"✅ Updated {products_without_hs} products with HS codes")
        
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

"""
Data mapping service for compliance reports.
"""
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from decimal import Decimal
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import SQLAlchemyError

from app.core.logging import get_logger
from app.models.purchase_order import PurchaseOrder
from app.models.company import Company
from app.models.product import Product
from app.models.batch import Batch
from app.models.transformation import TransformationEvent
from app.schemas.compliance import (
    EUDRReportData, RSPOReportData,
    EUDROperatorData, EUDRProductData, EUDRSupplyChainStep, EUDRRiskAssessment,
    RSPOCertificationData, RSPOMassBalance, RSPOSustainabilityMetrics
)
from app.services.compliance.exceptions import (
    PurchaseOrderNotFoundError, CompanyNotFoundError, ProductNotFoundError,
    ComplianceDataError, RiskAssessmentError, MassBalanceError
)
from app.services.compliance.validators import get_data_validator, get_template_sanitizer
from app.services.compliance.config import get_compliance_config

logger = get_logger(__name__)


class ComplianceDataMapper:
    """Maps existing data to compliance report formats with proper error handling."""
    
    def __init__(self, db: Session):
        self.db = db
        self.validator = get_data_validator()
        self.sanitizer = get_template_sanitizer()
        self.config = get_compliance_config()
    
    def map_po_to_eudr_data(self, po_id: UUID) -> EUDRReportData:
        """Map purchase order data to EUDR report format with error handling."""
        try:
            logger.info("Mapping PO to EUDR data", po_id=str(po_id))
            
            # Get purchase order with related data using eager loading
            po = self._get_purchase_order_with_relations(po_id)
            
            # Get operator data
            operator_data = self._get_operator_data(po.buyer_company_id)
            
            # Get product data
            product_data = self._get_product_data(po.product_id)
            
            # Get supply chain steps
            supply_chain_steps = self._get_supply_chain_steps(po_id)
            
            # Calculate risk assessment
            risk_assessment = self._calculate_eudr_risk_assessment(po_id, supply_chain_steps)
            
            # Sanitize data before creating response
            sanitized_data = self.sanitizer.sanitize_template_data({
                'operator': operator_data,
                'product': product_data,
                'supply_chain': supply_chain_steps,
                'risk_assessment': risk_assessment
            })
            
            eudr_data = EUDRReportData(
                operator=sanitized_data['operator'],
                product=sanitized_data['product'],
                supply_chain=sanitized_data['supply_chain'],
                risk_assessment=sanitized_data['risk_assessment'],
                trace_path=self._build_trace_path(supply_chain_steps),
                trace_depth=len(supply_chain_steps),
                generated_at=datetime.now()
            )
            
            logger.info("EUDR data mapped successfully", po_id=str(po_id))
            return eudr_data
            
        except (PurchaseOrderNotFoundError, CompanyNotFoundError, ProductNotFoundError) as e:
            logger.error("Data not found for EUDR mapping", po_id=str(po_id), error=str(e))
            raise
        except SQLAlchemyError as e:
            logger.error("Database error during EUDR mapping", po_id=str(po_id), error=str(e))
            raise ComplianceDataError(f"Failed to retrieve data for EUDR mapping: {e}", original_error=e)
        except Exception as e:
            logger.error("Unexpected error during EUDR mapping", po_id=str(po_id), error=str(e))
            raise ComplianceDataError(f"Unexpected error during EUDR mapping: {e}", original_error=e)
    
    def map_po_to_rspo_data(self, po_id: UUID) -> RSPOReportData:
        """Map purchase order data to RSPO report format with error handling."""
        try:
            logger.info("Mapping PO to RSPO data", po_id=str(po_id))
            
            # Get purchase order with related data
            po = self._get_purchase_order_with_relations(po_id)
            
            # Get product certification data
            certification_data = self._get_certification_data(po.product_id)
            
            # Get supply chain steps
            supply_chain_steps = self._get_supply_chain_steps(po_id)
            
            # Calculate mass balance
            mass_balance = self._calculate_mass_balance(po_id)
            
            # Calculate sustainability metrics
            sustainability = self._calculate_sustainability_metrics(po_id)
            
            # Sanitize data before creating response
            sanitized_data = self.sanitizer.sanitize_template_data({
                'certification': certification_data,
                'supply_chain': supply_chain_steps,
                'mass_balance': mass_balance,
                'sustainability': sustainability
            })
            
            rspo_data = RSPOReportData(
                certification=sanitized_data['certification'],
                supply_chain=sanitized_data['supply_chain'],
                mass_balance=sanitized_data['mass_balance'],
                sustainability=sanitized_data['sustainability'],
                trace_path=self._build_trace_path(supply_chain_steps),
                trace_depth=len(supply_chain_steps),
                generated_at=datetime.now()
            )
            
            logger.info("RSPO data mapped successfully", po_id=str(po_id))
            return rspo_data
            
        except (PurchaseOrderNotFoundError, CompanyNotFoundError, ProductNotFoundError) as e:
            logger.error("Data not found for RSPO mapping", po_id=str(po_id), error=str(e))
            raise
        except SQLAlchemyError as e:
            logger.error("Database error during RSPO mapping", po_id=str(po_id), error=str(e))
            raise ComplianceDataError(f"Failed to retrieve data for RSPO mapping: {e}", original_error=e)
        except Exception as e:
            logger.error("Unexpected error during RSPO mapping", po_id=str(po_id), error=str(e))
            raise ComplianceDataError(f"Unexpected error during RSPO mapping: {e}", original_error=e)
    
    def _get_purchase_order_with_relations(self, po_id: UUID) -> PurchaseOrder:
        """Get purchase order with eager loaded relations."""
        po = self.db.query(PurchaseOrder).options(
            joinedload(PurchaseOrder.buyer_company),
            joinedload(PurchaseOrder.seller_company),
            joinedload(PurchaseOrder.product)
        ).filter(PurchaseOrder.id == po_id).first()
        
        if not po:
            raise PurchaseOrderNotFoundError(str(po_id))
        
        return po
    
    def _get_operator_data(self, company_id: UUID) -> EUDROperatorData:
        """Get operator data for EUDR report."""
        company = self.db.query(Company).filter(Company.id == company_id).first()
        if not company:
            raise CompanyNotFoundError(str(company_id))
        
        return EUDROperatorData(
            name=company.name or "Unknown Company",
            registration_number=getattr(company, 'registration_number', None),
            address=company.address_street or "Unknown Address",
            country=company.country,
            tax_id=getattr(company, 'tax_id', None)
        )
    
    def _get_product_data(self, product_id: UUID) -> EUDRProductData:
        """Get product data for EUDR report."""
        product = self.db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise ProductNotFoundError(str(product_id))
        
        # Validate HS code
        hs_code = product.hs_code or self.config.default_hs_code
        validated_hs_code = self.validator.validate_hs_code(hs_code)
        
        return EUDRProductData(
            hs_code=validated_hs_code,
            description=product.name or "Unknown Product",
            quantity=self.validator.validate_quantity(1.0, "quantity"),  # Default quantity
            unit=product.default_unit or "kg"
        )
    
    def _get_certification_data(self, product_id: UUID) -> RSPOCertificationData:
        """Get certification data for RSPO report."""
        product = self.db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise ProductNotFoundError(str(product_id))
        
        return RSPOCertificationData(
            certificate_number=getattr(product, 'certification_number', None),
            valid_until=getattr(product, 'certification_expiry', None),
            certification_type=getattr(product, 'certification_type', None),
            certification_body=getattr(product, 'certification_body', None)
        )
    
    def _get_supply_chain_steps(self, po_id: UUID) -> List[EUDRSupplyChainStep]:
        """Get supply chain steps for a purchase order."""
        try:
            po = self._get_purchase_order_with_relations(po_id)
            steps = []
            
            # Add buyer (operator)
            buyer_company = po.buyer_company
            steps.append(EUDRSupplyChainStep(
                company_name=buyer_company.name or "Unknown Company",
                company_type=buyer_company.company_type or "unknown",
                location=buyer_company.address_street or "Unknown Address",
                coordinates=self._parse_coordinates(getattr(buyer_company, 'location_coordinates', None)),
                step_order=1
            ))
            
            # Add seller
            seller_company = po.seller_company
            steps.append(EUDRSupplyChainStep(
                company_name=seller_company.name or "Unknown Company",
                company_type=seller_company.company_type or "unknown",
                location=seller_company.address_street or "Unknown Address",
                coordinates=self._parse_coordinates(getattr(seller_company, 'location_coordinates', None)),
                step_order=2
            ))
            
            # TODO: Add more steps from supply_chain_traceability view
            # This would require implementing the recursive CTE query
            
            return steps
            
        except Exception as e:
            logger.error("Failed to get supply chain steps", po_id=str(po_id), error=str(e))
            raise ComplianceDataError(f"Failed to get supply chain steps: {e}", original_error=e)
    
    def _calculate_eudr_risk_assessment(self, po_id: UUID, supply_chain_steps: List[EUDRSupplyChainStep]) -> EUDRRiskAssessment:
        """Calculate EUDR risk assessment with proper validation."""
        try:
            risk_config = self.config.get_risk_config()
            
            # Initialize risk scores
            deforestation_risk = Decimal('0.0')
            traceability_score = Decimal('0.0')
            
            # Check if traced to plantation
            has_plantation = any(step.company_type == 'plantation_grower' for step in supply_chain_steps)
            if has_plantation:
                deforestation_risk += risk_config.plantation_risk_factor
                traceability_score += risk_config.plantation_traceability_bonus
            
            # Check if traced to mill
            has_mill = any(step.company_type == 'mill_processor' for step in supply_chain_steps)
            if has_mill:
                deforestation_risk += risk_config.mill_risk_factor
                traceability_score += risk_config.mill_traceability_bonus
            
            # Check trace depth
            trace_depth = len(supply_chain_steps)
            validated_depth = self.validator.validate_supply_chain_depth(trace_depth)
            
            if validated_depth > 2:
                traceability_score += risk_config.depth_traceability_bonus
            else:
                deforestation_risk += risk_config.trace_depth_risk_factor
            
            # Cap scores to valid ranges
            deforestation_risk = min(deforestation_risk, risk_config.max_risk_score)
            traceability_score = min(traceability_score, risk_config.max_traceability_score)
            compliance_score = risk_config.max_risk_score - deforestation_risk
            
            # Validate final scores
            validated_deforestation_risk = self.validator.validate_risk_score(deforestation_risk)
            validated_compliance_score = self.validator.validate_risk_score(compliance_score)
            validated_traceability_score = self.validator.validate_risk_score(traceability_score)
            
            return EUDRRiskAssessment(
                deforestation_risk=validated_deforestation_risk,
                compliance_score=validated_compliance_score,
                traceability_score=validated_traceability_score,
                risk_factors={
                    'has_plantation': has_plantation,
                    'has_mill': has_mill,
                    'trace_depth': validated_depth,
                    'risk_factors': ['deforestation', 'supply_chain_complexity']
                }
            )
            
        except Exception as e:
            logger.error("Failed to calculate EUDR risk assessment", po_id=str(po_id), error=str(e))
            raise RiskAssessmentError(f"Failed to calculate risk assessment: {e}", risk_type="DEFORESTATION")
    
    def _calculate_mass_balance(self, po_id: UUID) -> RSPOMassBalance:
        """Calculate mass balance from transformation events with validation."""
        try:
            # Get transformation events for this PO
            transformations = self.db.query(TransformationEvent).filter(
                TransformationEvent.input_batches.contains([str(po_id)])
            ).all()
            
            total_input = Decimal('0.0')
            total_output = Decimal('0.0')
            
            for transformation in transformations:
                input_qty = transformation.total_input_quantity or Decimal('0.0')
                output_qty = transformation.total_output_quantity or Decimal('0.0')
                
                # Validate quantities
                validated_input = self.validator.validate_quantity(input_qty, "input_quantity")
                validated_output = self.validator.validate_quantity(output_qty, "output_quantity")
                
                total_input += validated_input
                total_output += validated_output
            
            # Calculate percentages with validation
            if total_input > 0:
                yield_percentage = (total_output / total_input) * 100
                waste_percentage = 100 - yield_percentage
                
                # Validate percentages
                validated_yield = self.validator.validate_yield_percentage(yield_percentage)
                validated_waste = self.validator.validate_waste_percentage(waste_percentage)
                
                # Validate sum doesn't exceed 100%
                self.validator.validate_yield_waste_sum(validated_yield, validated_waste)
            else:
                validated_yield = Decimal('0.0')
                validated_waste = Decimal('0.0')
            
            return RSPOMassBalance(
                input_quantity=total_input,
                output_quantity=total_output,
                yield_percentage=validated_yield,
                waste_percentage=validated_waste
            )
            
        except Exception as e:
            logger.error("Failed to calculate mass balance", po_id=str(po_id), error=str(e))
            raise MassBalanceError(f"Failed to calculate mass balance: {e}")
    
    def _calculate_sustainability_metrics(self, po_id: UUID) -> RSPOSustainabilityMetrics:
        """Calculate sustainability metrics (placeholder implementation)."""
        # Placeholder implementation
        # In a real system, this would calculate actual metrics from data
        return RSPOSustainabilityMetrics(
            ghg_emissions=Decimal('0.0'),
            water_usage=Decimal('0.0'),
            energy_consumption=Decimal('0.0')
        )
    
    def _build_trace_path(self, supply_chain_steps: List[EUDRSupplyChainStep]) -> str:
        """Build trace path string."""
        return " -> ".join([
            f"{step.company_name} ({step.company_type})" 
            for step in supply_chain_steps
        ])
    
    def _parse_coordinates(self, coordinates_data: Optional[Dict]) -> Optional[Dict[str, float]]:
        """Parse coordinates from JSONB data."""
        if not coordinates_data:
            return None
        
        if isinstance(coordinates_data, dict):
            try:
                return {
                    'latitude': float(coordinates_data.get('lat', 0.0)),
                    'longitude': float(coordinates_data.get('lng', 0.0))
                }
            except (ValueError, TypeError):
                return None
        
        return None

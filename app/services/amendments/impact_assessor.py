"""
Amendment impact assessment logic.
"""
from typing import Optional
from decimal import Decimal
from datetime import datetime, timezone

from app.models.purchase_order import PurchaseOrder
from app.schemas.amendment import AmendmentCreate
from app.services.amendments.domain.models import AmendmentImpactAssessment
from app.services.amendments.domain.enums import AmendmentImpact, AmendmentType
from app.core.logging import get_logger

logger = get_logger(__name__)


class AmendmentImpactAssessor:
    """Assesses the impact of proposed amendments."""
    
    def assess_amendment_impact(
        self,
        amendment_data: AmendmentCreate,
        purchase_order: PurchaseOrder
    ) -> Optional[AmendmentImpactAssessment]:
        """
        Assess the impact of a proposed amendment.
        
        Args:
            amendment_data: Amendment creation data
            purchase_order: Purchase order being amended
            
        Returns:
            Impact assessment or None if no significant impact
        """
        logger.info(
            "Assessing amendment impact",
            po_id=str(purchase_order.id),
            amendment_type=amendment_data.amendment_type.value
        )
        
        # Initialize impact assessment
        impact_level = AmendmentImpact.MINIMAL
        financial_impact = Decimal('0.00')
        delivery_impact_days = 0
        
        affects_pricing = False
        affects_delivery = False
        affects_quality = False
        affects_compliance = False
        
        risk_factors = []
        mitigation_actions = []
        
        # Analyze each change
        for change in amendment_data.changes:
            field_name = change.field_name
            old_value = change.old_value
            new_value = change.new_value
            
            if field_name == 'quantity':
                quantity_impact = self._assess_quantity_change(
                    old_value, new_value, purchase_order
                )
                financial_impact += quantity_impact['financial_impact']
                if quantity_impact['impact_level'].value > impact_level.value:
                    impact_level = quantity_impact['impact_level']
                affects_pricing = True
                risk_factors.extend(quantity_impact['risk_factors'])
                mitigation_actions.extend(quantity_impact['mitigation_actions'])
            
            elif field_name == 'unit_price':
                price_impact = self._assess_price_change(
                    old_value, new_value, purchase_order
                )
                financial_impact += price_impact['financial_impact']
                if price_impact['impact_level'].value > impact_level.value:
                    impact_level = price_impact['impact_level']
                affects_pricing = True
                risk_factors.extend(price_impact['risk_factors'])
                mitigation_actions.extend(price_impact['mitigation_actions'])
            
            elif field_name == 'delivery_date':
                delivery_impact = self._assess_delivery_date_change(
                    old_value, new_value, purchase_order
                )
                delivery_impact_days = delivery_impact['delivery_impact_days']
                if delivery_impact['impact_level'].value > impact_level.value:
                    impact_level = delivery_impact['impact_level']
                affects_delivery = True
                risk_factors.extend(delivery_impact['risk_factors'])
                mitigation_actions.extend(delivery_impact['mitigation_actions'])
            
            elif field_name == 'delivery_location':
                affects_delivery = True
                risk_factors.append("Delivery location change may affect logistics")
                mitigation_actions.append("Verify new delivery location accessibility")
            
            elif field_name == 'composition':
                affects_quality = True
                affects_compliance = True
                impact_level = AmendmentImpact.MODERATE
                risk_factors.append("Composition change may affect product quality")
                mitigation_actions.append("Review compliance requirements for new composition")
            
            elif field_name == 'quantity_received':
                quantity_received_impact = self._assess_quantity_received_adjustment(
                    old_value, new_value, purchase_order
                )
                financial_impact += quantity_received_impact['financial_impact']
                if quantity_received_impact['impact_level'].value > impact_level.value:
                    impact_level = quantity_received_impact['impact_level']
                affects_pricing = True
                risk_factors.extend(quantity_received_impact['risk_factors'])
                mitigation_actions.extend(quantity_received_impact['mitigation_actions'])
        
        # Create impact assessment
        assessment = AmendmentImpactAssessment(
            impact_level=impact_level,
            financial_impact=financial_impact if financial_impact != 0 else None,
            delivery_impact_days=delivery_impact_days if delivery_impact_days != 0 else None,
            affects_pricing=affects_pricing,
            affects_delivery=affects_delivery,
            affects_quality=affects_quality,
            affects_compliance=affects_compliance,
            risk_factors=risk_factors if risk_factors else None,
            mitigation_actions=mitigation_actions if mitigation_actions else None,
            assessed_at=datetime.now(timezone.utc),
            assessment_version="1.0"
        )
        
        logger.info(
            "Amendment impact assessed",
            po_id=str(purchase_order.id),
            impact_level=impact_level.value,
            financial_impact=str(financial_impact),
            delivery_impact_days=delivery_impact_days
        )
        
        return assessment
    
    def _assess_quantity_change(self, old_quantity, new_quantity, purchase_order):
        """Assess impact of quantity change."""
        old_qty = Decimal(str(old_quantity))
        new_qty = Decimal(str(new_quantity))
        unit_price = purchase_order.unit_price
        
        quantity_diff = new_qty - old_qty
        financial_impact = quantity_diff * unit_price
        
        # Determine impact level based on percentage change
        percentage_change = abs(quantity_diff / old_qty * 100)
        
        if percentage_change <= 5:
            impact_level = AmendmentImpact.MINIMAL
        elif percentage_change <= 15:
            impact_level = AmendmentImpact.MODERATE
        elif percentage_change <= 30:
            impact_level = AmendmentImpact.SIGNIFICANT
        else:
            impact_level = AmendmentImpact.CRITICAL
        
        risk_factors = []
        mitigation_actions = []
        
        if quantity_diff > 0:
            risk_factors.append("Increased quantity may affect supplier capacity")
            mitigation_actions.append("Confirm supplier can fulfill increased quantity")
        else:
            risk_factors.append("Decreased quantity may affect unit economics")
            mitigation_actions.append("Review impact on supplier minimum order requirements")
        
        return {
            'financial_impact': financial_impact,
            'impact_level': impact_level,
            'risk_factors': risk_factors,
            'mitigation_actions': mitigation_actions
        }
    
    def _assess_price_change(self, old_price, new_price, purchase_order):
        """Assess impact of price change."""
        old_price_decimal = Decimal(str(old_price))
        new_price_decimal = Decimal(str(new_price))
        quantity = purchase_order.quantity
        
        price_diff = new_price_decimal - old_price_decimal
        financial_impact = price_diff * quantity
        
        # Determine impact level based on percentage change
        percentage_change = abs(price_diff / old_price_decimal * 100)
        
        if percentage_change <= 2:
            impact_level = AmendmentImpact.MINIMAL
        elif percentage_change <= 10:
            impact_level = AmendmentImpact.MODERATE
        elif percentage_change <= 25:
            impact_level = AmendmentImpact.SIGNIFICANT
        else:
            impact_level = AmendmentImpact.CRITICAL
        
        risk_factors = []
        mitigation_actions = []
        
        if price_diff > 0:
            risk_factors.append("Price increase affects budget")
            mitigation_actions.append("Review budget impact and approval requirements")
        else:
            risk_factors.append("Price decrease may indicate quality concerns")
            mitigation_actions.append("Verify quality standards are maintained")
        
        return {
            'financial_impact': financial_impact,
            'impact_level': impact_level,
            'risk_factors': risk_factors,
            'mitigation_actions': mitigation_actions
        }
    
    def _assess_delivery_date_change(self, old_date, new_date, purchase_order):
        """Assess impact of delivery date change."""
        from datetime import date
        
        if isinstance(old_date, str):
            old_date = date.fromisoformat(old_date)
        if isinstance(new_date, str):
            new_date = date.fromisoformat(new_date)
        
        date_diff = (new_date - old_date).days
        
        # Determine impact level based on delay/advancement
        if abs(date_diff) <= 3:
            impact_level = AmendmentImpact.MINIMAL
        elif abs(date_diff) <= 14:
            impact_level = AmendmentImpact.MODERATE
        elif abs(date_diff) <= 30:
            impact_level = AmendmentImpact.SIGNIFICANT
        else:
            impact_level = AmendmentImpact.CRITICAL
        
        risk_factors = []
        mitigation_actions = []
        
        if date_diff > 0:
            risk_factors.append("Delivery delay may affect downstream operations")
            mitigation_actions.append("Notify affected stakeholders of delivery delay")
        else:
            risk_factors.append("Earlier delivery may require expedited logistics")
            mitigation_actions.append("Confirm readiness for earlier delivery")
        
        return {
            'delivery_impact_days': date_diff,
            'impact_level': impact_level,
            'risk_factors': risk_factors,
            'mitigation_actions': mitigation_actions
        }
    
    def _assess_quantity_received_adjustment(self, old_quantity, new_quantity, purchase_order):
        """Assess impact of quantity received adjustment."""
        if old_quantity is None:
            old_quantity = purchase_order.quantity
        
        old_qty = Decimal(str(old_quantity))
        new_qty = Decimal(str(new_quantity))
        unit_price = purchase_order.unit_price
        
        quantity_diff = new_qty - old_qty
        financial_impact = quantity_diff * unit_price
        
        # Determine impact level based on shortage/overage
        percentage_diff = abs(quantity_diff / old_qty * 100)
        
        if percentage_diff <= 2:
            impact_level = AmendmentImpact.MINIMAL
        elif percentage_diff <= 10:
            impact_level = AmendmentImpact.MODERATE
        elif percentage_diff <= 20:
            impact_level = AmendmentImpact.SIGNIFICANT
        else:
            impact_level = AmendmentImpact.CRITICAL
        
        risk_factors = []
        mitigation_actions = []
        
        if quantity_diff < 0:
            risk_factors.append("Quantity shortage may affect production plans")
            mitigation_actions.append("Assess impact on downstream operations")
        else:
            risk_factors.append("Quantity overage may require additional storage")
            mitigation_actions.append("Arrange appropriate storage for excess quantity")
        
        return {
            'financial_impact': financial_impact,
            'impact_level': impact_level,
            'risk_factors': risk_factors,
            'mitigation_actions': mitigation_actions
        }

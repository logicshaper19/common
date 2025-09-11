"""
Farm Compliance Service for EUDR/US Regulatory Requirements

This service handles farm-level compliance verification for EUDR and US regulations,
ensuring each farm meets all required standards for traceability and risk assessment.
"""
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models.location import Location
from app.models.batch_farm_contribution import BatchFarmContribution
from app.core.logging import get_logger

logger = get_logger(__name__)


class FarmComplianceService:
    """Service for managing farm-level regulatory compliance"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def verify_farm_eudr_compliance(self, farm_id: UUID) -> Dict[str, Any]:
        """
        Verify EUDR compliance for a specific farm
        
        Args:
            farm_id: ID of the farm to verify
            
        Returns:
            Dict with EUDR compliance verification result
        """
        farm = self.db.query(Location).filter(
            and_(
                Location.id == farm_id,
                Location.is_farm_location == True
            )
        ).first()
        
        if not farm:
            raise ValueError(f"Farm {farm_id} not found")
        
        compliance_checks = {
            "farm_id": str(farm_id),
            "farm_name": farm.name,
            "verification_date": datetime.utcnow().isoformat(),
            "eudr_checks": {}
        }
        
        # Check 1: Geolocation Present
        compliance_checks["eudr_checks"]["geolocation_present"] = self._check_geolocation_present(farm)
        
        # Check 2: Deforestation Risk Assessment
        compliance_checks["eudr_checks"]["deforestation_risk_low"] = self._check_deforestation_risk(farm)
        
        # Check 3: Legal Documentation
        compliance_checks["eudr_checks"]["legal_docs_valid"] = self._check_legal_documentation(farm)
        
        # Check 4: Due Diligence Statement
        compliance_checks["eudr_checks"]["due_diligence_statement"] = self._check_due_diligence_statement(farm)
        
        # Check 5: Land Use Change History
        compliance_checks["eudr_checks"]["land_use_change_history"] = self._check_land_use_change_history(farm)
        
        # Overall EUDR compliance status
        all_checks_passed = all(
            check["status"] == "pass" 
            for check in compliance_checks["eudr_checks"].values()
        )
        
        compliance_checks["eudr_compliance_status"] = "verified" if all_checks_passed else "failed"
        compliance_checks["overall_status"] = "verified" if all_checks_passed else "failed"
        
        # Update farm compliance status
        farm.compliance_status = compliance_checks["eudr_compliance_status"]
        farm.compliance_verification_date = datetime.utcnow()
        farm.last_compliance_check = datetime.utcnow()
        farm.next_compliance_check_due = datetime.utcnow() + timedelta(days=farm.compliance_check_frequency_days)
        
        self.db.commit()
        
        return compliance_checks
    
    def verify_farm_us_compliance(self, farm_id: UUID) -> Dict[str, Any]:
        """
        Verify US regulatory compliance for a specific farm
        
        Args:
            farm_id: ID of the farm to verify
            
        Returns:
            Dict with US compliance verification result
        """
        farm = self.db.query(Location).filter(
            and_(
                Location.id == farm_id,
                Location.is_farm_location == True
            )
        ).first()
        
        if not farm:
            raise ValueError(f"Farm {farm_id} not found")
        
        compliance_checks = {
            "farm_id": str(farm_id),
            "farm_name": farm.name,
            "verification_date": datetime.utcnow().isoformat(),
            "us_checks": {}
        }
        
        # Check 1: UFLPA Compliance (Forced Labor Risk)
        compliance_checks["us_checks"]["uflpa_compliance"] = self._check_uflpa_compliance(farm)
        
        # Check 2: CBP Documentation
        compliance_checks["us_checks"]["cbp_documentation"] = self._check_cbp_documentation(farm)
        
        # Check 3: Supply Chain Mapping
        compliance_checks["us_checks"]["supply_chain_mapping"] = self._check_supply_chain_mapping(farm)
        
        # Check 4: US Risk Assessment
        compliance_checks["us_checks"]["us_risk_assessment"] = self._check_us_risk_assessment(farm)
        
        # Overall US compliance status
        all_checks_passed = all(
            check["status"] == "pass" 
            for check in compliance_checks["us_checks"].values()
        )
        
        compliance_checks["us_compliance_status"] = "verified" if all_checks_passed else "failed"
        compliance_checks["overall_status"] = "verified" if all_checks_passed else "failed"
        
        return compliance_checks
    
    def get_farm_compliance_status(self, farm_id: UUID) -> Dict[str, Any]:
        """
        Get current compliance status for a farm
        
        Args:
            farm_id: ID of the farm
            
        Returns:
            Dict with current compliance status
        """
        farm = self.db.query(Location).filter(
            and_(
                Location.id == farm_id,
                Location.is_farm_location == True
            )
        ).first()
        
        if not farm:
            raise ValueError(f"Farm {farm_id} not found")
        
        return {
            "farm_id": str(farm_id),
            "farm_name": farm.name,
            "compliance_status": farm.compliance_status,
            "last_compliance_check": farm.last_compliance_check.isoformat() if farm.last_compliance_check else None,
            "next_compliance_check_due": farm.next_compliance_check_due.isoformat() if farm.next_compliance_check_due else None,
            "compliance_verification_date": farm.compliance_verification_date.isoformat() if farm.compliance_verification_date else None,
            "exemption_reason": farm.exemption_reason,
            "compliance_notes": farm.compliance_notes,
            "eudr_data": {
                "deforestation_cutoff_date": farm.deforestation_cutoff_date.isoformat() if farm.deforestation_cutoff_date else None,
                "land_use_change_history": farm.land_use_change_history,
                "legal_land_tenure_docs": farm.legal_land_tenure_docs,
                "due_diligence_statement": farm.due_diligence_statement,
                "risk_assessment_data": farm.risk_assessment_data
            },
            "us_data": {
                "uflpa_compliance_data": farm.uflpa_compliance_data,
                "cbp_documentation": farm.cbp_documentation,
                "supply_chain_mapping": farm.supply_chain_mapping,
                "us_risk_assessment": farm.us_risk_assessment
            }
        }
    
    def _check_geolocation_present(self, farm: Location) -> Dict[str, Any]:
        """Check if farm has required geolocation data"""
        has_coordinates = (
            farm.latitude is not None and 
            farm.longitude is not None and
            farm.accuracy_meters is not None and
            farm.accuracy_meters <= 1000  # EUDR requires accuracy within 1km
        )
        
        return {
            "status": "pass" if has_coordinates else "fail",
            "details": {
                "has_latitude": farm.latitude is not None,
                "has_longitude": farm.longitude is not None,
                "has_accuracy": farm.accuracy_meters is not None,
                "accuracy_acceptable": farm.accuracy_meters <= 1000 if farm.accuracy_meters else False,
                "coordinates": {
                    "latitude": float(farm.latitude) if farm.latitude else None,
                    "longitude": float(farm.longitude) if farm.longitude else None,
                    "accuracy_meters": float(farm.accuracy_meters) if farm.accuracy_meters else None
                }
            }
        }
    
    def _check_deforestation_risk(self, farm: Location) -> Dict[str, Any]:
        """Check deforestation risk for the farm"""
        # This would integrate with external APIs like Global Forest Watch
        # For now, return a basic check based on available data
        
        has_risk_data = farm.risk_assessment_data is not None
        has_cutoff_date = farm.deforestation_cutoff_date is not None
        cutoff_after_2020 = (
            farm.deforestation_cutoff_date >= date(2020, 12, 31) 
            if farm.deforestation_cutoff_date else False
        )
        
        return {
            "status": "pass" if (has_risk_data and has_cutoff_date and cutoff_after_2020) else "fail",
            "details": {
                "has_risk_assessment": has_risk_data,
                "has_cutoff_date": has_cutoff_date,
                "cutoff_after_2020": cutoff_after_2020,
                "risk_data": farm.risk_assessment_data,
                "cutoff_date": farm.deforestation_cutoff_date.isoformat() if farm.deforestation_cutoff_date else None
            }
        }
    
    def _check_legal_documentation(self, farm: Location) -> Dict[str, Any]:
        """Check legal documentation for the farm"""
        has_legal_docs = farm.legal_land_tenure_docs is not None and len(farm.legal_land_tenure_docs) > 0
        has_registration = farm.registration_number is not None
        
        return {
            "status": "pass" if (has_legal_docs and has_registration) else "fail",
            "details": {
                "has_legal_docs": has_legal_docs,
                "has_registration": has_registration,
                "legal_docs": farm.legal_land_tenure_docs,
                "registration_number": farm.registration_number
            }
        }
    
    def _check_due_diligence_statement(self, farm: Location) -> Dict[str, Any]:
        """Check EUDR due diligence statement"""
        has_due_diligence = farm.due_diligence_statement is not None and len(farm.due_diligence_statement) > 0
        
        return {
            "status": "pass" if has_due_diligence else "fail",
            "details": {
                "has_due_diligence": has_due_diligence,
                "due_diligence_data": farm.due_diligence_statement
            }
        }
    
    def _check_land_use_change_history(self, farm: Location) -> Dict[str, Any]:
        """Check land use change history"""
        has_history = farm.land_use_change_history is not None and len(farm.land_use_change_history) > 0
        
        return {
            "status": "pass" if has_history else "fail",
            "details": {
                "has_history": has_history,
                "land_use_history": farm.land_use_change_history
            }
        }
    
    def _check_uflpa_compliance(self, farm: Location) -> Dict[str, Any]:
        """Check UFLPA (forced labor) compliance"""
        has_uflpa_data = farm.uflpa_compliance_data is not None and len(farm.uflpa_compliance_data) > 0
        
        return {
            "status": "pass" if has_uflpa_data else "fail",
            "details": {
                "has_uflpa_data": has_uflpa_data,
                "uflpa_data": farm.uflpa_compliance_data
            }
        }
    
    def _check_cbp_documentation(self, farm: Location) -> Dict[str, Any]:
        """Check CBP documentation"""
        has_cbp_docs = farm.cbp_documentation is not None and len(farm.cbp_documentation) > 0
        
        return {
            "status": "pass" if has_cbp_docs else "fail",
            "details": {
                "has_cbp_docs": has_cbp_docs,
                "cbp_docs": farm.cbp_documentation
            }
        }
    
    def _check_supply_chain_mapping(self, farm: Location) -> Dict[str, Any]:
        """Check supply chain mapping"""
        has_mapping = farm.supply_chain_mapping is not None and len(farm.supply_chain_mapping) > 0
        
        return {
            "status": "pass" if has_mapping else "fail",
            "details": {
                "has_mapping": has_mapping,
                "supply_chain_mapping": farm.supply_chain_mapping
            }
        }
    
    def _check_us_risk_assessment(self, farm: Location) -> Dict[str, Any]:
        """Check US risk assessment"""
        has_assessment = farm.us_risk_assessment is not None and len(farm.us_risk_assessment) > 0
        
        return {
            "status": "pass" if has_assessment else "fail",
            "details": {
                "has_assessment": has_assessment,
                "us_risk_assessment": farm.us_risk_assessment
            }
        }

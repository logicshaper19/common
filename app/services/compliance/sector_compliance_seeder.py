"""
Sector Compliance Rules Seeder
Seeds compliance rules for different sectors following the project plan
"""
from typing import Dict, Any
from sqlalchemy.orm import Session
from app.models.sector import Sector
from app.core.logging import get_logger

logger = get_logger(__name__)


class SectorComplianceSeeder:
    """
    Seeds compliance rules configuration for sectors
    Following David's strategic insight to extend sectors configuration
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def seed_all_sectors(self) -> None:
        """Seed compliance rules for all supported sectors"""
        logger.info("Starting compliance rules seeding for all sectors")
        
        # Palm Oil - EUDR focused
        self.seed_palm_oil_compliance()
        
        # Apparel - UFLPA focused  
        self.seed_apparel_compliance()
        
        # Coffee - EUDR focused
        self.seed_coffee_compliance()
        
        # Soy - EUDR focused
        self.seed_soy_compliance()
        
        self.db.commit()
        logger.info("Completed compliance rules seeding for all sectors")
    
    def seed_palm_oil_compliance(self) -> None:
        """Seed palm oil sector compliance rules (already done in migration, but can update)"""
        palm_oil_rules = {
            "eudr": {
                "required_checks": [
                    "geolocation_present",
                    "deforestation_risk_low", 
                    "legal_docs_valid",
                    "supply_chain_mapped"
                ],
                "check_definitions": {
                    "geolocation_present": {
                        "description": "Verify that geographic coordinates are present for origin data",
                        "required_fields": ["latitude", "longitude"],
                        "precision_threshold": 0.001,
                        "mandatory": True,
                        "tier_applicability": [1, 2]  # Primary producers and mills
                    },
                    "deforestation_risk_low": {
                        "description": "Assess deforestation risk using external APIs",
                        "api_providers": ["global_forest_watch", "trase"],
                        "risk_threshold": "low",
                        "mandatory": True,
                        "cutoff_date": "2020-12-31"
                    },
                    "legal_docs_valid": {
                        "description": "Validate required legal documentation is present and valid",
                        "required_documents": ["eudr_due_diligence_statement", "legal_harvest_permit"],
                        "validity_check": True,
                        "mandatory": True
                    },
                    "supply_chain_mapped": {
                        "description": "Verify supply chain is mapped to mill level",
                        "traceability_level": "mill",
                        "mandatory": True,
                        "tier_applicability": [3, 4, 5]  # Traders and processors
                    }
                }
            },
            "rspo": {
                "required_checks": [
                    "rspo_certification_valid",
                    "chain_of_custody_maintained"
                ],
                "check_definitions": {
                    "rspo_certification_valid": {
                        "description": "Verify valid RSPO certification",
                        "certification_types": ["IP", "SG", "MB", "B&C"],
                        "mandatory": False,
                        "validity_check": True
                    },
                    "chain_of_custody_maintained": {
                        "description": "Verify RSPO chain of custody is maintained",
                        "documentation_required": ["rspo_certificate", "supply_chain_map"],
                        "mandatory": False
                    }
                }
            }
        }
        
        self._update_sector_compliance("palm_oil", palm_oil_rules)
    
    def seed_apparel_compliance(self) -> None:
        """Seed apparel sector compliance rules - UFLPA focused"""
        apparel_rules = {
            "uflpa": {
                "required_checks": [
                    "xinjiang_supply_chain_check",
                    "forced_labor_risk_assessment",
                    "supplier_verification_complete"
                ],
                "check_definitions": {
                    "xinjiang_supply_chain_check": {
                        "description": "Verify no supply chain connections to Xinjiang region",
                        "prohibited_regions": ["xinjiang"],
                        "supplier_mapping_required": True,
                        "mandatory": True
                    },
                    "forced_labor_risk_assessment": {
                        "description": "Assess forced labor risk in supply chain",
                        "risk_indicators": ["debt_bondage", "restricted_movement", "excessive_overtime"],
                        "third_party_audit_required": True,
                        "mandatory": True
                    },
                    "supplier_verification_complete": {
                        "description": "Complete supplier verification and documentation",
                        "required_documents": ["supplier_declaration", "audit_report"],
                        "documentation_retention_years": 5,
                        "mandatory": True
                    }
                }
            },
            "bci": {
                "required_checks": [
                    "bci_certification_valid",
                    "farmer_training_documented"
                ],
                "check_definitions": {
                    "bci_certification_valid": {
                        "description": "Verify valid Better Cotton Initiative certification",
                        "certification_type": "BCI",
                        "mandatory": False,
                        "validity_check": True
                    },
                    "farmer_training_documented": {
                        "description": "Document farmer training and capacity building",
                        "training_topics": ["sustainable_practices", "water_management", "pest_control"],
                        "mandatory": False
                    }
                }
            }
        }
        
        self._update_sector_compliance("apparel", apparel_rules)
    
    def seed_coffee_compliance(self) -> None:
        """Seed coffee sector compliance rules - EUDR focused"""
        coffee_rules = {
            "eudr": {
                "required_checks": [
                    "geolocation_present",
                    "deforestation_risk_low",
                    "legal_docs_valid",
                    "farm_size_documented"
                ],
                "check_definitions": {
                    "geolocation_present": {
                        "description": "Verify geographic coordinates for coffee farms",
                        "required_fields": ["latitude", "longitude"],
                        "precision_threshold": 0.001,
                        "mandatory": True,
                        "farm_polygon_required": True
                    },
                    "deforestation_risk_low": {
                        "description": "Assess deforestation risk for coffee production areas",
                        "api_providers": ["global_forest_watch"],
                        "risk_threshold": "low",
                        "mandatory": True,
                        "cutoff_date": "2020-12-31"
                    },
                    "legal_docs_valid": {
                        "description": "Validate legal documentation for coffee production",
                        "required_documents": ["eudr_due_diligence_statement", "farm_registration"],
                        "validity_check": True,
                        "mandatory": True
                    },
                    "farm_size_documented": {
                        "description": "Document farm size for area-based risk assessment",
                        "area_threshold_hectares": 4,
                        "polygon_required_above_threshold": True,
                        "mandatory": True
                    }
                }
            }
        }
        
        self._update_sector_compliance("coffee", coffee_rules)
    
    def seed_soy_compliance(self) -> None:
        """Seed soy sector compliance rules - EUDR focused"""
        soy_rules = {
            "eudr": {
                "required_checks": [
                    "geolocation_present",
                    "deforestation_risk_low",
                    "legal_docs_valid",
                    "soy_moratorium_compliance"
                ],
                "check_definitions": {
                    "geolocation_present": {
                        "description": "Verify geographic coordinates for soy production",
                        "required_fields": ["latitude", "longitude"],
                        "precision_threshold": 0.001,
                        "mandatory": True
                    },
                    "deforestation_risk_low": {
                        "description": "Assess deforestation risk for soy production areas",
                        "api_providers": ["global_forest_watch", "trase"],
                        "risk_threshold": "low",
                        "mandatory": True,
                        "cutoff_date": "2020-12-31"
                    },
                    "legal_docs_valid": {
                        "description": "Validate legal documentation for soy production",
                        "required_documents": ["eudr_due_diligence_statement", "land_use_permit"],
                        "validity_check": True,
                        "mandatory": True
                    },
                    "soy_moratorium_compliance": {
                        "description": "Verify compliance with Amazon Soy Moratorium",
                        "applicable_regions": ["amazon_biome"],
                        "moratorium_cutoff_date": "2006-07-24",
                        "mandatory": True
                    }
                }
            }
        }
        
        self._update_sector_compliance("soy", soy_rules)
    
    def _update_sector_compliance(self, sector_id: str, compliance_rules: Dict[str, Any]) -> None:
        """Update compliance rules for a specific sector"""
        sector = self.db.query(Sector).filter(Sector.id == sector_id).first()
        
        if not sector:
            logger.warning(f"Sector {sector_id} not found, skipping compliance rules seeding")
            return
        
        sector.compliance_rules = compliance_rules
        logger.info(f"Updated compliance rules for sector: {sector_id}")
    
    def get_sector_compliance_rules(self, sector_id: str, regulation: str = None) -> Dict[str, Any]:
        """Get compliance rules for a sector, optionally filtered by regulation"""
        sector = self.db.query(Sector).filter(Sector.id == sector_id).first()
        
        if not sector or not sector.compliance_rules:
            return {}
        
        if regulation:
            return sector.compliance_rules.get(regulation, {})
        
        return sector.compliance_rules

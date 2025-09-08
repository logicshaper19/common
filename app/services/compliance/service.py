"""
Compliance Service
Following the project plan: Build service that uses existing TransparencyCalculationService and TraceabilityService
"""
from typing import Dict, List, Any, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.po_compliance_result import POComplianceResult
from app.models.purchase_order import PurchaseOrder
from app.models.sector import Sector
from app.services.traceability import TraceabilityCalculationService
from app.services.transparency_engine import TransparencyCalculationEngine
from app.services.compliance.external_apis import DeforestationRiskAPI
from app.services.document_storage import DocumentStorageService
from app.core.logging import get_logger

logger = get_logger(__name__)


# Specific compliance exceptions for better error handling
class ComplianceServiceError(Exception):
    """Base exception for compliance service errors"""
    pass

class ComplianceEvaluationError(ComplianceServiceError):
    """Error during compliance evaluation"""
    pass

class ComplianceDataNotFoundError(ComplianceServiceError):
    """Required compliance data not found"""
    pass

class ComplianceRuleNotImplementedError(ComplianceServiceError):
    """Compliance rule not yet implemented"""
    pass


class ComplianceService:
    """
    Compliance service that uses existing TransparencyCalculationService and TraceabilityService.
    Following the project plan - DO NOT recreate their logic.
    """
    
    def __init__(self, db: Session):
        self.db = db
        # Use existing services - DO NOT recreate their logic
        self.transparency_service = TraceabilityCalculationService(db)
        self.transparency_engine = TransparencyCalculationEngine(db)
        self.document_service = DocumentStorageService(db)
    
    async def evaluate_po_compliance(self, po_id: UUID, regulation: str) -> List[POComplianceResult]:
        """
        1. Uses the existing transparency engine to get the supply chain graph.
        2. Applies the relevant rule set to each node in the graph.
        3. Saves results to `po_compliance_results`.
        
        Following the exact project plan implementation.
        """
        logger.info(
            "Starting PO compliance evaluation",
            po_id=str(po_id),
            regulation=regulation
        )
        
        try:
            # Get the supply chain graph for the PO USING EXISTING LOGIC
            transparency_result = await self.transparency_engine.calculate_transparency(
                po_id=po_id,
                force_recalculation=False,
                include_detailed_analysis=True
            )
            
            if not transparency_result or not transparency_result.nodes:
                logger.warning("No supply chain graph found for PO", po_id=str(po_id))
                return []
            
            # Get the rule set based on the PO's product/sector
            rule_set = self._get_rule_set_for_po(po_id, regulation)
            
            if not rule_set:
                logger.warning(
                    "No compliance rules found for PO",
                    po_id=str(po_id),
                    regulation=regulation
                )
                return []
            
            results = []
            for rule in rule_set:
                try:
                    # For each rule, evaluate it against the entire graph
                    result = await self._evaluate_rule(rule, transparency_result, po_id)
                    results.append(result)
                except Exception as e:
                    logger.error(
                        "Error evaluating compliance rule",
                        rule=rule,
                        po_id=str(po_id),
                        error=str(e)
                    )
                    # Create a failed result for this rule
                    failed_result = POComplianceResult(
                        po_id=po_id,
                        regulation=regulation,
                        check_name=rule,
                        status="fail",
                        evidence={"error": str(e), "timestamp": datetime.utcnow().isoformat()}
                    )
                    results.append(failed_result)
            
            # Save all results
            await self._save_compliance_results(po_id, regulation, results)
            
            logger.info(
                "PO compliance evaluation completed",
                po_id=str(po_id),
                regulation=regulation,
                rules_evaluated=len(rule_set),
                results_count=len(results)
            )
            
            return results
            
        except Exception as e:
            logger.error(
                "Error during PO compliance evaluation",
                po_id=str(po_id),
                regulation=regulation,
                error=str(e)
            )
            raise
    
    async def _evaluate_rule(self, rule: str, transparency_result, po_id: UUID) -> POComplianceResult:
        """
        This is where the specific rule logic lives.
        Following the project plan's rule implementations.
        """
        logger.debug(f"Evaluating rule: {rule} for PO: {po_id}")
        
        if rule == "geolocation_present":
            return await self._check_geolocation_present(transparency_result, po_id)
        elif rule == "deforestation_risk_low":
            return await self._check_deforestation_risk(transparency_result, po_id)
        elif rule == "legal_docs_valid":
            return await self._check_legal_docs_valid(transparency_result, po_id)
        elif rule == "supply_chain_mapped":
            return await self._check_supply_chain_mapped(transparency_result, po_id)
        elif rule == "rspo_certification_valid":
            return await self._check_rspo_certification_valid(transparency_result, po_id)
        elif rule == "chain_of_custody_maintained":
            return await self._check_chain_of_custody_maintained(transparency_result, po_id)
        else:
            # Unknown rule - log warning and return pending status
            logger.warning(f"Compliance rule '{rule}' not implemented yet")
            return POComplianceResult(
                po_id=po_id,
                regulation="unknown",
                check_name=rule,
                status="pending",
                evidence={"message": f"Rule '{rule}' not implemented yet"}
            )
    
    async def _check_geolocation_present(self, transparency_result, po_id: UUID) -> POComplianceResult:
        """Check if geolocation data is present in origin nodes"""
        evidence = {
            "nodes_checked": [],
            "nodes_with_coordinates": [],
            "nodes_without_coordinates": []
        }
        
        nodes_with_geo = 0
        total_origin_nodes = 0
        
        for node in transparency_result.nodes:
            if hasattr(node, 'origin_data') and node.origin_data:
                total_origin_nodes += 1
                evidence["nodes_checked"].append(str(node.po_id))
                
                # Check if coordinates are present
                if (hasattr(node.origin_data, 'geographic_coordinates') and 
                    node.origin_data.geographic_coordinates and
                    hasattr(node.origin_data.geographic_coordinates, 'latitude') and
                    hasattr(node.origin_data.geographic_coordinates, 'longitude')):
                    
                    nodes_with_geo += 1
                    evidence["nodes_with_coordinates"].append(str(node.po_id))
                else:
                    evidence["nodes_without_coordinates"].append(str(node.po_id))
        
        # Determine status
        if total_origin_nodes == 0:
            status = "warning"
            evidence["message"] = "No origin data nodes found"
        elif nodes_with_geo == total_origin_nodes:
            status = "pass"
            evidence["message"] = f"All {total_origin_nodes} origin nodes have geolocation data"
        elif nodes_with_geo > 0:
            status = "warning"
            evidence["message"] = f"{nodes_with_geo}/{total_origin_nodes} origin nodes have geolocation data"
        else:
            status = "fail"
            evidence["message"] = f"No origin nodes have geolocation data (0/{total_origin_nodes})"
        
        return POComplianceResult(
            po_id=po_id,
            regulation="eudr",
            check_name="geolocation_present",
            status=status,
            evidence=evidence
        )
    
    async def _check_deforestation_risk(self, transparency_result, po_id: UUID) -> POComplianceResult:
        """
        Leverages Clovis's API integration idea.
        Check deforestation risk using external APIs.
        """
        evidence = {
            "nodes_checked": [],
            "high_risk_nodes": [],
            "api_responses": []
        }
        
        high_risk_found = False
        
        for node in transparency_result.nodes:
            if (hasattr(node, 'origin_data') and node.origin_data and
                hasattr(node.origin_data, 'geographic_coordinates') and
                node.origin_data.geographic_coordinates):
                
                evidence["nodes_checked"].append(str(node.po_id))
                
                try:
                    # USE EXTERNAL API (Clovis's concept)
                    coordinates = [
                        float(node.origin_data.geographic_coordinates.latitude),
                        float(node.origin_data.geographic_coordinates.longitude)
                    ]
                    
                    risk_assessment = await DeforestationRiskAPI.check_coordinates(coordinates)
                    evidence["api_responses"].append({
                        "node_id": str(node.po_id),
                        "coordinates": coordinates,
                        "risk_level": risk_assessment.risk_level,
                        "confidence": risk_assessment.confidence
                    })
                    
                    if risk_assessment.high_risk:
                        high_risk_found = True
                        evidence["high_risk_nodes"].append({
                            "node_id": str(node.po_id),
                            "risk_details": risk_assessment.dict()
                        })
                        
                except Exception as e:
                    logger.error(f"Error checking deforestation risk for node {node.po_id}: {e}")
                    evidence["api_responses"].append({
                        "node_id": str(node.po_id),
                        "error": str(e)
                    })
        
        # Determine status
        if not evidence["nodes_checked"]:
            status = "warning"
            evidence["message"] = "No nodes with coordinates found for deforestation risk check"
        elif high_risk_found:
            status = "fail"
            evidence["message"] = f"High deforestation risk found in {len(evidence['high_risk_nodes'])} nodes"
        else:
            status = "pass"
            evidence["message"] = f"Low deforestation risk for all {len(evidence['nodes_checked'])} checked nodes"
        
        return POComplianceResult(
            po_id=po_id,
            regulation="eudr",
            check_name="deforestation_risk_low",
            status=status,
            evidence=evidence
        )
    
    async def _check_legal_docs_valid(self, transparency_result, po_id: UUID) -> POComplianceResult:
        """Check if required legal documents are present and valid"""
        evidence = {
            "required_documents": ["eudr_due_diligence_statement", "legal_harvest_permit"],
            "found_documents": [],
            "missing_documents": []
        }
        
        # Get documents for this PO
        documents = await self.document_service.get_documents_by_po(str(po_id))
        
        required_docs = evidence["required_documents"]
        found_docs = []
        
        for doc_type in required_docs:
            matching_docs = [d for d in documents if d.document_type == doc_type]
            if matching_docs:
                # Get the most recent document
                latest_doc = max(matching_docs, key=lambda d: d.created_at)
                found_docs.append(doc_type)
                evidence["found_documents"].append({
                    "document_type": doc_type,
                    "document_id": str(latest_doc.id),
                    "created_at": latest_doc.created_at.isoformat(),
                    "validation_status": latest_doc.validation_status
                })
            else:
                evidence["missing_documents"].append(doc_type)
        
        # Determine status
        if len(found_docs) == len(required_docs):
            status = "pass"
            evidence["message"] = "All required legal documents are present"
        elif len(found_docs) > 0:
            status = "warning"
            evidence["message"] = f"{len(found_docs)}/{len(required_docs)} required documents found"
        else:
            status = "fail"
            evidence["message"] = "No required legal documents found"
        
        return POComplianceResult(
            po_id=po_id,
            regulation="eudr",
            check_name="legal_docs_valid",
            status=status,
            evidence=evidence
        )
    
    async def _check_supply_chain_mapped(self, transparency_result, po_id: UUID) -> POComplianceResult:
        """Check if supply chain is properly mapped"""
        evidence = {
            "total_nodes": len(transparency_result.nodes),
            "max_depth": transparency_result.max_depth_reached,
            "mill_nodes": 0,
            "plantation_nodes": 0,
            "ttm_score": transparency_result.ttm_score,
            "ttp_score": transparency_result.ttp_score
        }
        
        # Count different node types
        for node in transparency_result.nodes:
            if hasattr(node, 'company_type'):
                if node.company_type in ['mill', 'processor']:
                    evidence["mill_nodes"] += 1
                elif node.company_type in ['plantation', 'farm']:
                    evidence["plantation_nodes"] += 1
        
        # Determine status based on transparency scores
        if transparency_result.ttm_score >= 0.8:
            status = "pass"
            evidence["message"] = f"Supply chain well mapped (TTM: {transparency_result.ttm_score:.2f})"
        elif transparency_result.ttm_score >= 0.5:
            status = "warning"
            evidence["message"] = f"Supply chain partially mapped (TTM: {transparency_result.ttm_score:.2f})"
        else:
            status = "fail"
            evidence["message"] = f"Supply chain poorly mapped (TTM: {transparency_result.ttm_score:.2f})"
        
        return POComplianceResult(
            po_id=po_id,
            regulation="eudr",
            check_name="supply_chain_mapped",
            status=status,
            evidence=evidence
        )
    
    async def _check_rspo_certification_valid(self, transparency_result, po_id: UUID) -> POComplianceResult:
        """Check RSPO certification validity"""
        # Placeholder implementation for RSPO checks
        return POComplianceResult(
            po_id=po_id,
            regulation="rspo",
            check_name="rspo_certification_valid",
            status="pending",
            evidence={"message": "RSPO certification check not yet implemented"}
        )
    
    async def _check_chain_of_custody_maintained(self, transparency_result, po_id: UUID) -> POComplianceResult:
        """Check chain of custody maintenance"""
        # Placeholder implementation for chain of custody checks
        return POComplianceResult(
            po_id=po_id,
            regulation="rspo",
            check_name="chain_of_custody_maintained",
            status="pending",
            evidence={"message": "Chain of custody check not yet implemented"}
        )
    
    def _get_rule_set_for_po(self, po_id: UUID, regulation: str) -> List[str]:
        """Get the rule set based on the PO's product/sector"""
        try:
            # Get PO and its sector
            po = self.db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
            if not po:
                raise ComplianceDataNotFoundError(f"Purchase order {po_id} not found")
            if not po.product:
                raise ComplianceDataNotFoundError(f"Product not found for purchase order {po_id}")
            
            # Get sector compliance rules
            sector = self.db.query(Sector).filter(Sector.id == po.product.sector_id).first()
            if not sector or not sector.compliance_rules:
                logger.warning(f"No compliance rules found for sector {po.product.sector_id}")
                return []
            
            # Extract rules for the specific regulation
            regulation_rules = sector.compliance_rules.get(regulation.lower(), {})
            required_checks = regulation_rules.get("required_checks", [])
            
            logger.info(
                "Retrieved compliance rules for PO",
                po_id=str(po_id),
                regulation=regulation,
                sector=po.product.sector_id,
                rules_count=len(required_checks)
            )
            
            return required_checks
            
        except Exception as e:
            logger.error(f"Error getting rule set for PO {po_id}: {e}")
            return []
    
    async def _save_compliance_results(self, po_id: UUID, regulation: str, results: List[POComplianceResult]) -> None:
        """Save all compliance results to the database"""
        try:
            for result in results:
                # Check if result already exists
                existing = self.db.query(POComplianceResult).filter(
                    and_(
                        POComplianceResult.po_id == po_id,
                        POComplianceResult.regulation == regulation,
                        POComplianceResult.check_name == result.check_name
                    )
                ).first()
                
                if existing:
                    # Update existing result
                    existing.status = result.status
                    existing.evidence = result.evidence
                    existing.updated_at = datetime.utcnow()
                else:
                    # Add new result
                    self.db.add(result)
            
            self.db.commit()
            logger.info(f"Saved {len(results)} compliance results for PO {po_id}")
            
        except Exception as e:
            logger.error(f"Error saving compliance results: {e}")
            self.db.rollback()
            raise
    
    def get_compliance_overview(self, po_id: UUID) -> Dict[str, Any]:
        """Get compliance overview for a PO (for API integration)"""
        try:
            results = self.db.query(POComplianceResult).filter(
                POComplianceResult.po_id == po_id
            ).all()
            
            if not results:
                return {}
            
            # Group by regulation
            overview = {}
            for result in results:
                if result.regulation not in overview:
                    overview[result.regulation] = {
                        "status": "pass",
                        "checks_passed": 0,
                        "total_checks": 0,
                        "checks": []
                    }
                
                reg_overview = overview[result.regulation]
                reg_overview["total_checks"] += 1
                
                if result.status == "pass":
                    reg_overview["checks_passed"] += 1
                elif result.status == "fail":
                    reg_overview["status"] = "fail"
                elif result.status == "warning" and reg_overview["status"] == "pass":
                    reg_overview["status"] = "warning"
                
                reg_overview["checks"].append({
                    "check_name": result.check_name,
                    "status": result.status,
                    "checked_at": result.checked_at.isoformat() if result.checked_at else None
                })
            
            return overview
            
        except Exception as e:
            logger.error(f"Error getting compliance overview for PO {po_id}: {e}")
            return {}

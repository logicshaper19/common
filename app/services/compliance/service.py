"""
Main compliance service for generating reports with dependency injection and error handling.
"""
from typing import Protocol, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.core.logging import get_logger
from app.models.compliance import ComplianceReport, ComplianceTemplate
from app.schemas.compliance import ComplianceReportRequest, ComplianceReportGenerationResponse
from app.services.compliance.exceptions import (
    ComplianceDataError, TemplateNotFoundError, PurchaseOrderNotFoundError
)
from app.services.compliance.data_mapper import ComplianceDataMapper
from app.services.compliance.template_engine import ComplianceTemplateEngine
from app.services.compliance.config import get_compliance_config

logger = get_logger(__name__)


class PurchaseOrderRepositoryProtocol(Protocol):
    """Protocol for purchase order repository."""
    
    def get_by_id(self, po_id: UUID) -> Optional[dict]:
        """Get purchase order by ID."""
        ...


class ComplianceReportRepositoryProtocol(Protocol):
    """Protocol for compliance report repository."""
    
    def create(self, report_data: dict) -> ComplianceReport:
        """Create a new compliance report."""
        ...


class ComplianceService:
    """Main compliance service with dependency injection and error handling."""
    
    def __init__(
        self, 
        db: Session,
        data_mapper: Optional[ComplianceDataMapper] = None,
        template_engine: Optional[ComplianceTemplateEngine] = None,
        po_repository: Optional[PurchaseOrderRepositoryProtocol] = None,
        report_repository: Optional[ComplianceReportRepositoryProtocol] = None
    ):
        self.db = db
        self.config = get_compliance_config()
        
        # Dependency injection with defaults
        self.data_mapper = data_mapper or ComplianceDataMapper(db)
        self.template_engine = template_engine or ComplianceTemplateEngine(db)
        self.po_repository = po_repository
        self.report_repository = report_repository
    
    def generate_compliance_report(self, request: ComplianceReportRequest) -> ComplianceReportGenerationResponse:
        """Generate a compliance report with proper error handling."""
        try:
            logger.info(
                "Generating compliance report",
                po_id=str(request.po_id),
                regulation_type=request.regulation_type
            )
            
            # Validate request
            self._validate_request(request)
            
            # Generate report based on regulation type
            if request.regulation_type == 'EUDR':
                report_content = self._generate_eudr_report(request)
            elif request.regulation_type == 'RSPO':
                report_content = self._generate_rspo_report(request)
            else:
                raise ComplianceDataError(f"Unsupported regulation type: {request.regulation_type}")
            
            # Save report to database
            report = self._save_report(request, report_content)
            
            # Create response
            response = ComplianceReportGenerationResponse(
                report_id=report.id,
                po_id=request.po_id,
                regulation_type=request.regulation_type,
                generated_at=report.generated_at,
                file_size=report.file_size,
                download_url=f"/api/v1/compliance/reports/{report.id}/download",
                status=report.status
            )
            
            logger.info(
                "Compliance report generated successfully",
                report_id=str(report.id),
                po_id=str(request.po_id),
                regulation_type=request.regulation_type
            )
            
            return response
            
        except (PurchaseOrderNotFoundError, TemplateNotFoundError) as e:
            logger.error("Data not found for compliance report", po_id=str(request.po_id), error=str(e))
            raise
        except SQLAlchemyError as e:
            logger.error("Database error during compliance report generation", po_id=str(request.po_id), error=str(e))
            raise ComplianceDataError(f"Database error during report generation: {e}", original_error=e)
        except Exception as e:
            logger.error("Unexpected error during compliance report generation", po_id=str(request.po_id), error=str(e))
            raise ComplianceDataError(f"Unexpected error during report generation: {e}", original_error=e)
    
    def _validate_request(self, request: ComplianceReportRequest) -> None:
        """Validate compliance report request."""
        if not request.po_id:
            raise ComplianceDataError("Purchase order ID is required")
        
        if not request.regulation_type:
            raise ComplianceDataError("Regulation type is required")
        
        if request.regulation_type not in ['EUDR', 'RSPO', 'ISCC']:
            raise ComplianceDataError(f"Unsupported regulation type: {request.regulation_type}")
    
    def _generate_eudr_report(self, request: ComplianceReportRequest) -> bytes:
        """Generate EUDR compliance report."""
        try:
            # Map data to EUDR format
            eudr_data = self.data_mapper.map_po_to_eudr_data(request.po_id)
            
            # Convert to dict for template rendering
            eudr_dict = {
                'operator': eudr_data.operator,
                'product': eudr_data.product,
                'supply_chain': eudr_data.supply_chain,
                'risk_assessment': eudr_data.risk_assessment,
                'trace_path': eudr_data.trace_path,
                'trace_depth': eudr_data.trace_depth,
                'generated_at': eudr_data.generated_at
            }
            
            # Generate report
            return self.template_engine.generate_eudr_report(eudr_dict)
            
        except Exception as e:
            logger.error("Failed to generate EUDR report", po_id=str(request.po_id), error=str(e))
            raise ComplianceDataError(f"Failed to generate EUDR report: {e}", original_error=e)
    
    def _generate_rspo_report(self, request: ComplianceReportRequest) -> bytes:
        """Generate RSPO compliance report."""
        try:
            # Map data to RSPO format
            rspo_data = self.data_mapper.map_po_to_rspo_data(request.po_id)
            
            # Convert to dict for template rendering
            rspo_dict = {
                'certification': rspo_data.certification,
                'supply_chain': rspo_data.supply_chain,
                'mass_balance': rspo_data.mass_balance,
                'sustainability': rspo_data.sustainability,
                'trace_path': rspo_data.trace_path,
                'trace_depth': rspo_data.trace_depth,
                'generated_at': rspo_data.generated_at
            }
            
            # Generate report
            return self.template_engine.generate_rspo_report(rspo_dict)
            
        except Exception as e:
            logger.error("Failed to generate RSPO report", po_id=str(request.po_id), error=str(e))
            raise ComplianceDataError(f"Failed to generate RSPO report: {e}", original_error=e)
    
    def _save_report(self, request: ComplianceReportRequest, report_content: bytes) -> ComplianceReport:
        """Save compliance report to database."""
        try:
            # Get template ID
            template_id = self._get_template_id(request.regulation_type)
            
            # Get company ID from PO
            company_id = self._get_company_id_from_po(request.po_id)
            
            # Create report
            report = ComplianceReport(
                company_id=company_id,
                template_id=template_id,
                po_id=request.po_id,
                report_data=request.custom_data or {},
                file_size=len(report_content),
                status='GENERATED'
            )
            
            self.db.add(report)
            self.db.commit()
            self.db.refresh(report)
            
            logger.info("Compliance report saved", report_id=str(report.id))
            return report
            
        except SQLAlchemyError as e:
            logger.error("Failed to save compliance report", po_id=str(request.po_id), error=str(e))
            self.db.rollback()
            raise ComplianceDataError(f"Failed to save compliance report: {e}", original_error=e)
    
    def _get_template_id(self, regulation_type: str) -> UUID:
        """Get template ID for regulation type."""
        try:
            template = self.db.query(ComplianceTemplate).filter(
                ComplianceTemplate.regulation_type == regulation_type,
                ComplianceTemplate.is_active == True
            ).first()
            
            if not template:
                # Create default template
                template = self._create_default_template(regulation_type)
            
            return template.id
            
        except SQLAlchemyError as e:
            logger.error("Failed to get template ID", regulation_type=regulation_type, error=str(e))
            raise ComplianceDataError(f"Failed to get template for {regulation_type}: {e}", original_error=e)
    
    def _create_default_template(self, regulation_type: str) -> ComplianceTemplate:
        """Create default template for regulation type."""
        try:
            template = ComplianceTemplate(
                name=f"Default {regulation_type} Template",
                regulation_type=regulation_type,
                version="1.0",
                template_content=self.template_engine._get_default_template(regulation_type),
                is_active=True
            )
            
            self.db.add(template)
            self.db.commit()
            self.db.refresh(template)
            
            logger.info("Default template created", regulation_type=regulation_type, template_id=str(template.id))
            return template
            
        except SQLAlchemyError as e:
            logger.error("Failed to create default template", regulation_type=regulation_type, error=str(e))
            self.db.rollback()
            raise ComplianceDataError(f"Failed to create default template for {regulation_type}: {e}", original_error=e)
    
    def _get_company_id_from_po(self, po_id: UUID) -> UUID:
        """Get company ID from purchase order."""
        try:
            from app.models.purchase_order import PurchaseOrder
            
            po = self.db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
            if not po:
                raise PurchaseOrderNotFoundError(str(po_id))
            
            return po.buyer_company_id
            
        except SQLAlchemyError as e:
            logger.error("Failed to get company ID from PO", po_id=str(po_id), error=str(e))
            raise ComplianceDataError(f"Failed to get company ID from purchase order: {e}", original_error=e)
    
    def get_report(self, report_id: UUID) -> Optional[ComplianceReport]:
        """Get compliance report by ID."""
        try:
            return self.db.query(ComplianceReport).filter(ComplianceReport.id == report_id).first()
        except SQLAlchemyError as e:
            logger.error("Failed to get compliance report", report_id=str(report_id), error=str(e))
            raise ComplianceDataError(f"Failed to get compliance report: {e}", original_error=e)
    
    def list_reports(self, company_id: Optional[UUID] = None, limit: int = 50) -> list[ComplianceReport]:
        """List compliance reports with optional filtering."""
        try:
            query = self.db.query(ComplianceReport)
            
            if company_id:
                query = query.filter(ComplianceReport.company_id == company_id)
            
            return query.limit(limit).all()
            
        except SQLAlchemyError as e:
            logger.error("Failed to list compliance reports", company_id=str(company_id) if company_id else None, error=str(e))
            raise ComplianceDataError(f"Failed to list compliance reports: {e}", original_error=e)
    
    def clear_caches(self) -> None:
        """Clear all caches."""
        self.template_engine.clear_template_cache()
        logger.info("All caches cleared")
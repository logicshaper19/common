"""
Compliance Reporting Service
Following the project plan: Build PDF reporting for compliance results
"""
import io
from typing import Dict, List, Any, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, black, red, green, orange
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

from app.models.po_compliance_result import POComplianceResult
from app.models.purchase_order import PurchaseOrder
from app.models.company import Company
from app.core.logging import get_logger

logger = get_logger(__name__)


class ComplianceReportGenerator:
    """
    Generate PDF compliance reports for purchase orders.
    Following the project plan's reporting requirements.
    """
    
    def __init__(self, db: Session):
        self.db = db
        
        # Report styling
        self.styles = getSampleStyleSheet()
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=TA_CENTER
        )
        self.heading_style = ParagraphStyle(
            'CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceAfter=12,
            textColor=HexColor('#2E86AB')
        )
        self.subheading_style = ParagraphStyle(
            'CustomSubHeading',
            parent=self.styles['Heading3'],
            fontSize=12,
            spaceAfter=8,
            textColor=HexColor('#A23B72')
        )
    
    def generate_po_compliance_report(self, po_id: UUID, regulations: Optional[List[str]] = None) -> bytes:
        """
        Generate a comprehensive compliance report for a purchase order.
        
        Args:
            po_id: Purchase order UUID
            regulations: Optional list of regulations to include (default: all)
            
        Returns:
            PDF report as bytes
        """
        logger.info(
            "Generating compliance report",
            po_id=str(po_id),
            regulations=regulations
        )
        
        try:
            # Get PO and compliance data
            po = self.db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
            if not po:
                raise ValueError(f"Purchase order {po_id} not found")
            
            # Get compliance results
            query = self.db.query(POComplianceResult).filter(POComplianceResult.po_id == po_id)
            if regulations:
                query = query.filter(POComplianceResult.regulation.in_(regulations))
            
            compliance_results = query.all()
            
            # Create PDF buffer
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(
                buffer,
                pagesize=A4,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18
            )
            
            # Build report content
            story = []
            
            # Title page
            story.extend(self._build_title_page(po))
            story.append(PageBreak())
            
            # Executive summary
            story.extend(self._build_executive_summary(po, compliance_results))
            story.append(Spacer(1, 20))
            
            # Detailed compliance results
            story.extend(self._build_detailed_results(compliance_results))
            story.append(Spacer(1, 20))
            
            # Supply chain overview
            story.extend(self._build_supply_chain_overview(po))
            story.append(Spacer(1, 20))
            
            # Recommendations
            story.extend(self._build_recommendations(compliance_results))
            
            # Build PDF
            doc.build(story)
            
            # Get PDF bytes
            pdf_bytes = buffer.getvalue()
            buffer.close()
            
            logger.info(
                "Compliance report generated successfully",
                po_id=str(po_id),
                report_size_bytes=len(pdf_bytes)
            )
            
            return pdf_bytes
            
        except Exception as e:
            logger.error(
                "Error generating compliance report",
                po_id=str(po_id),
                error=str(e)
            )
            raise
    
    def _build_title_page(self, po: PurchaseOrder) -> List:
        """Build the title page of the report"""
        story = []
        
        # Main title
        title = Paragraph("Supply Chain Compliance Report", self.title_style)
        story.append(title)
        story.append(Spacer(1, 30))
        
        # PO information table
        po_data = [
            ["Purchase Order", po.po_number],
            ["Buyer", po.buyer_company.name if po.buyer_company else "Unknown"],
            ["Seller", po.seller_company.name if po.seller_company else "Unknown"],
            ["Product", po.product.name if po.product else "Unknown"],
            ["Quantity", f"{po.quantity} {po.unit}" if po.quantity and po.unit else "N/A"],
            ["Status", po.status.title() if po.status else "Unknown"],
            ["Report Generated", datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")]
        ]
        
        po_table = Table(po_data, colWidths=[2*inch, 3*inch])
        po_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), HexColor('#F0F0F0')),
            ('TEXTCOLOR', (0, 0), (-1, -1), black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, black)
        ]))
        
        story.append(po_table)
        story.append(Spacer(1, 40))
        
        # Disclaimer
        disclaimer = Paragraph(
            "<b>Disclaimer:</b> This report is generated based on available data and automated compliance checks. "
            "It should be reviewed by compliance professionals and may require additional verification.",
            self.styles['Normal']
        )
        story.append(disclaimer)
        
        return story
    
    def _build_executive_summary(self, po: PurchaseOrder, compliance_results: List[POComplianceResult]) -> List:
        """Build executive summary section"""
        story = []
        
        story.append(Paragraph("Executive Summary", self.heading_style))
        
        if not compliance_results:
            story.append(Paragraph("No compliance checks have been performed for this purchase order.", self.styles['Normal']))
            return story
        
        # Group results by regulation
        by_regulation = {}
        for result in compliance_results:
            if result.regulation not in by_regulation:
                by_regulation[result.regulation] = []
            by_regulation[result.regulation].append(result)
        
        # Summary table
        summary_data = [["Regulation", "Total Checks", "Passed", "Failed", "Warnings", "Overall Status"]]
        
        for regulation, results in by_regulation.items():
            total = len(results)
            passed = len([r for r in results if r.status == "pass"])
            failed = len([r for r in results if r.status == "fail"])
            warnings = len([r for r in results if r.status == "warning"])
            
            # Determine overall status
            if failed > 0:
                overall_status = "FAIL"
                status_color = red
            elif warnings > 0:
                overall_status = "WARNING"
                status_color = orange
            else:
                overall_status = "PASS"
                status_color = green
            
            summary_data.append([
                regulation.upper(),
                str(total),
                str(passed),
                str(failed),
                str(warnings),
                overall_status
            ])
        
        summary_table = Table(summary_data, colWidths=[1.2*inch, 0.8*inch, 0.8*inch, 0.8*inch, 0.8*inch, 1*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), HexColor('#2E86AB')),
            ('TEXTCOLOR', (0, 0), (-1, 0), HexColor('#FFFFFF')),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, black)
        ]))
        
        story.append(summary_table)
        story.append(Spacer(1, 20))
        
        return story
    
    def _build_detailed_results(self, compliance_results: List[POComplianceResult]) -> List:
        """Build detailed compliance results section"""
        story = []
        
        story.append(Paragraph("Detailed Compliance Results", self.heading_style))
        
        if not compliance_results:
            story.append(Paragraph("No compliance results available.", self.styles['Normal']))
            return story
        
        # Group by regulation
        by_regulation = {}
        for result in compliance_results:
            if result.regulation not in by_regulation:
                by_regulation[result.regulation] = []
            by_regulation[result.regulation].append(result)
        
        for regulation, results in by_regulation.items():
            story.append(Paragraph(f"{regulation.upper()} Compliance", self.subheading_style))
            
            # Results table for this regulation
            results_data = [["Check Name", "Status", "Evidence Summary", "Checked At"]]
            
            for result in results:
                # Extract evidence summary
                evidence_summary = "No evidence"
                if result.evidence:
                    if isinstance(result.evidence, dict):
                        evidence_summary = result.evidence.get("message", "See detailed evidence")
                    else:
                        evidence_summary = str(result.evidence)[:100] + "..." if len(str(result.evidence)) > 100 else str(result.evidence)
                
                # Format checked_at
                checked_at = result.checked_at.strftime("%Y-%m-%d %H:%M") if result.checked_at else "Unknown"
                
                results_data.append([
                    result.check_name,
                    result.status.upper(),
                    evidence_summary,
                    checked_at
                ])
            
            results_table = Table(results_data, colWidths=[2*inch, 1*inch, 2.5*inch, 1.2*inch])
            results_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), HexColor('#A23B72')),
                ('TEXTCOLOR', (0, 0), (-1, 0), HexColor('#FFFFFF')),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 1, black),
                ('VALIGN', (0, 0), (-1, -1), 'TOP')
            ]))
            
            story.append(results_table)
            story.append(Spacer(1, 15))
        
        return story
    
    def _build_supply_chain_overview(self, po: PurchaseOrder) -> List:
        """Build supply chain overview section"""
        story = []
        
        story.append(Paragraph("Supply Chain Overview", self.heading_style))
        
        # Basic supply chain info
        overview_text = f"""
        This purchase order represents a transaction in the {po.product.sector.name if po.product and po.product.sector else 'unknown'} sector. 
        The transaction involves {po.quantity} {po.unit} of {po.product.name if po.product else 'unknown product'} 
        from {po.seller_company.name if po.seller_company else 'unknown seller'} 
        to {po.buyer_company.name if po.buyer_company else 'unknown buyer'}.
        """
        
        story.append(Paragraph(overview_text, self.styles['Normal']))
        story.append(Spacer(1, 10))
        
        # Origin data if available
        if po.origin_data:
            story.append(Paragraph("Origin Data Available:", self.subheading_style))
            
            origin_info = []
            if po.origin_data.get('geographic_coordinates'):
                coords = po.origin_data['geographic_coordinates']
                origin_info.append(f"Geographic Coordinates: {coords.get('latitude', 'N/A')}, {coords.get('longitude', 'N/A')}")
            
            if po.origin_data.get('harvest_date'):
                origin_info.append(f"Harvest Date: {po.origin_data['harvest_date']}")
            
            if po.origin_data.get('farm_identification'):
                origin_info.append(f"Farm ID: {po.origin_data['farm_identification']}")
            
            if origin_info:
                for info in origin_info:
                    story.append(Paragraph(f"• {info}", self.styles['Normal']))
            else:
                story.append(Paragraph("• Origin data structure present but no specific details available", self.styles['Normal']))
        else:
            story.append(Paragraph("No origin data available for this purchase order.", self.styles['Normal']))
        
        return story
    
    def _build_recommendations(self, compliance_results: List[POComplianceResult]) -> List:
        """Build recommendations section"""
        story = []
        
        story.append(Paragraph("Recommendations", self.heading_style))
        
        if not compliance_results:
            story.append(Paragraph("No recommendations available - no compliance checks performed.", self.styles['Normal']))
            return story
        
        # Analyze results for recommendations
        failed_checks = [r for r in compliance_results if r.status == "fail"]
        warning_checks = [r for r in compliance_results if r.status == "warning"]
        
        recommendations = []
        
        if failed_checks:
            recommendations.append("🔴 <b>Critical Actions Required:</b>")
            for check in failed_checks:
                recommendations.append(f"   • Address failed check: {check.check_name}")
        
        if warning_checks:
            recommendations.append("🟡 <b>Improvement Opportunities:</b>")
            for check in warning_checks:
                recommendations.append(f"   • Review warning for: {check.check_name}")
        
        if not failed_checks and not warning_checks:
            recommendations.append("✅ <b>All compliance checks passed!</b> Continue monitoring for ongoing compliance.")
        
        # General recommendations
        recommendations.extend([
            "",
            "<b>General Recommendations:</b>",
            "• Regularly update compliance documentation",
            "• Monitor regulatory changes in your sector",
            "• Implement continuous compliance monitoring",
            "• Train staff on compliance requirements"
        ])
        
        for rec in recommendations:
            story.append(Paragraph(rec, self.styles['Normal']))
            story.append(Spacer(1, 5))
        
        return story

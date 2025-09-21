"""
Services for transformation versioning and enhanced functionality.
"""
from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func

from app.core.logging import get_logger
from app.models.transformation_versioning import (
    TransformationEventVersion, QualityInheritanceRule, TransformationCost,
    TransformationProcessTemplate, RealTimeMonitoringEndpoint
)
from app.models.transformation import TransformationEvent
from app.schemas.transformation_versioning import (
    TransformationEventVersionCreate, TransformationEventVersionUpdate,
    QualityInheritanceRuleCreate, QualityInheritanceRuleUpdate,
    TransformationCostCreate, TransformationCostUpdate,
    TransformationProcessTemplateCreate, TransformationProcessTemplateUpdate,
    RealTimeMonitoringEndpointCreate, RealTimeMonitoringEndpointUpdate,
    QualityInheritanceCalculation, CostCalculationRequest, TemplateUsageRequest,
    MonitoringDataIngestion, VersionApprovalRequest, BatchQualityInheritanceRequest,
    CostSummaryResponse, TemplateMetricsResponse
)

logger = get_logger(__name__)


class TransformationVersioningService:
    """Service for managing transformation event versioning."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_version(
        self, 
        version_data: TransformationEventVersionCreate,
        user_id: UUID
    ) -> TransformationEventVersion:
        """Create a new version of a transformation event."""
        try:
            # Get the current version number
            current_version = self.db.query(func.max(TransformationEventVersion.version_number))\
                .filter(TransformationEventVersion.transformation_event_id == version_data.transformation_event_id)\
                .scalar() or 0
            
            version = TransformationEventVersion(
                transformation_event_id=version_data.transformation_event_id,
                version_number=current_version + 1,
                version_type=version_data.version_type,
                event_data=version_data.event_data,
                process_parameters=version_data.process_parameters,
                quality_metrics=version_data.quality_metrics,
                efficiency_metrics=version_data.efficiency_metrics,
                change_reason=version_data.change_reason,
                change_description=version_data.change_description,
                approval_required=version_data.approval_required,
                created_by_user_id=user_id
            )
            
            self.db.add(version)
            self.db.commit()
            self.db.refresh(version)
            
            logger.info(f"Created version {version.version_number} for transformation event {version_data.transformation_event_id}")
            return version
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating transformation version: {str(e)}")
            raise
    
    def get_versions(
        self, 
        transformation_event_id: UUID,
        limit: int = 50,
        offset: int = 0
    ) -> List[TransformationEventVersion]:
        """Get all versions for a transformation event."""
        return self.db.query(TransformationEventVersion)\
            .filter(TransformationEventVersion.transformation_event_id == transformation_event_id)\
            .order_by(desc(TransformationEventVersion.version_number))\
            .offset(offset)\
            .limit(limit)\
            .all()
    
    def get_version(self, version_id: UUID) -> Optional[TransformationEventVersion]:
        """Get a specific version by ID."""
        return self.db.query(TransformationEventVersion)\
            .filter(TransformationEventVersion.id == version_id)\
            .first()
    
    def update_version(
        self, 
        version_id: UUID, 
        update_data: TransformationEventVersionUpdate,
        user_id: UUID
    ) -> Optional[TransformationEventVersion]:
        """Update a transformation event version."""
        try:
            version = self.get_version(version_id)
            if not version:
                return None
            
            for field, value in update_data.dict(exclude_unset=True).items():
                setattr(version, field, value)
            
            if update_data.approval_status:
                version.approved_by_user_id = user_id
                version.approved_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(version)
            
            logger.info(f"Updated version {version.version_number} for transformation event {version.transformation_event_id}")
            return version
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating transformation version: {str(e)}")
            raise
    
    def approve_version(
        self, 
        version_id: UUID, 
        approval_data: VersionApprovalRequest,
        user_id: UUID
    ) -> Optional[TransformationEventVersion]:
        """Approve or reject a transformation event version."""
        try:
            version = self.get_version(version_id)
            if not version:
                return None
            
            version.approval_status = approval_data.approval_status
            version.approved_by_user_id = user_id
            version.approved_at = datetime.utcnow()
            
            if approval_data.approval_notes:
                version.change_description = approval_data.approval_notes
            
            self.db.commit()
            self.db.refresh(version)
            
            logger.info(f"Version {version.version_number} {approval_data.approval_status} for transformation event {version.transformation_event_id}")
            return version
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error approving transformation version: {str(e)}")
            raise


class QualityInheritanceService:
    """Service for managing quality inheritance rules and calculations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_rule(
        self, 
        rule_data: QualityInheritanceRuleCreate,
        user_id: UUID
    ) -> QualityInheritanceRule:
        """Create a new quality inheritance rule."""
        try:
            rule = QualityInheritanceRule(
                transformation_type=rule_data.transformation_type,
                input_quality_metric=rule_data.input_quality_metric,
                output_quality_metric=rule_data.output_quality_metric,
                inheritance_type=rule_data.inheritance_type,
                inheritance_formula=rule_data.inheritance_formula,
                degradation_factor=rule_data.degradation_factor,
                enhancement_factor=rule_data.enhancement_factor,
                is_active=rule_data.is_active,
                created_by_user_id=user_id
            )
            
            self.db.add(rule)
            self.db.commit()
            self.db.refresh(rule)
            
            logger.info(f"Created quality inheritance rule for {rule_data.transformation_type}")
            return rule
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating quality inheritance rule: {str(e)}")
            raise
    
    def get_rules(
        self, 
        transformation_type: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> List[QualityInheritanceRule]:
        """Get quality inheritance rules with optional filtering."""
        query = self.db.query(QualityInheritanceRule)
        
        if transformation_type:
            query = query.filter(QualityInheritanceRule.transformation_type == transformation_type)
        
        if is_active is not None:
            query = query.filter(QualityInheritanceRule.is_active == is_active)
        
        return query.all()
    
    def calculate_quality_inheritance(
        self, 
        calculation_data: QualityInheritanceCalculation
    ) -> Dict[str, Any]:
        """Calculate quality inheritance for a transformation."""
        try:
            rules = self.get_rules(
                transformation_type=calculation_data.transformation_type,
                is_active=True
            )
            
            output_quality = {}
            
            for rule in rules:
                input_value = calculation_data.input_quality.get(rule.input_quality_metric)
                if input_value is None:
                    continue
                
                # Calculate output value based on inheritance type
                if rule.inheritance_type == "direct":
                    output_value = input_value
                elif rule.inheritance_type == "degraded":
                    output_value = input_value * (rule.degradation_factor or 0.95)
                elif rule.inheritance_type == "enhanced":
                    output_value = input_value * (rule.enhancement_factor or 1.05)
                elif rule.inheritance_type == "calculated":
                    # For calculated, implement formula logic
                    # For now, use a simple degradation
                    output_value = input_value * 0.90
                else:
                    output_value = input_value
                
                output_quality[rule.output_quality_metric] = output_value
            
            logger.info(f"Calculated quality inheritance for {calculation_data.transformation_type}")
            return output_quality
            
        except Exception as e:
            logger.error(f"Error calculating quality inheritance: {str(e)}")
            raise


class TransformationCostService:
    """Service for managing transformation costs."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_cost(
        self, 
        cost_data: TransformationCostCreate,
        user_id: UUID
    ) -> TransformationCost:
        """Create a new transformation cost record."""
        try:
            total_cost = cost_data.quantity * cost_data.unit_cost
            
            cost = TransformationCost(
                transformation_event_id=cost_data.transformation_event_id,
                cost_category=cost_data.cost_category,
                cost_type=cost_data.cost_type,
                quantity=cost_data.quantity,
                unit=cost_data.unit,
                unit_cost=cost_data.unit_cost,
                total_cost=total_cost,
                currency=cost_data.currency,
                cost_breakdown=cost_data.cost_breakdown,
                supplier_id=cost_data.supplier_id,
                cost_center=cost_data.cost_center,
                created_by_user_id=user_id
            )
            
            self.db.add(cost)
            self.db.commit()
            self.db.refresh(cost)
            
            logger.info(f"Created cost record for transformation event {cost_data.transformation_event_id}")
            return cost
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating transformation cost: {str(e)}")
            raise
    
    def get_costs(
        self, 
        transformation_event_id: UUID,
        cost_category: Optional[str] = None
    ) -> List[TransformationCost]:
        """Get costs for a transformation event."""
        query = self.db.query(TransformationCost)\
            .filter(TransformationCost.transformation_event_id == transformation_event_id)
        
        if cost_category:
            query = query.filter(TransformationCost.cost_category == cost_category)
        
        return query.all()
    
    def get_cost_summary(self, transformation_event_id: UUID) -> CostSummaryResponse:
        """Get cost summary for a transformation event."""
        try:
            costs = self.get_costs(transformation_event_id)
            
            total_cost = sum(cost.total_cost for cost in costs)
            cost_by_category = {}
            cost_breakdown = {}
            
            for cost in costs:
                category = cost.cost_category.value
                if category not in cost_by_category:
                    cost_by_category[category] = 0
                cost_by_category[category] += cost.total_cost
                
                if cost.cost_breakdown:
                    cost_breakdown[category] = cost.cost_breakdown
            
            return CostSummaryResponse(
                transformation_event_id=transformation_event_id,
                total_cost=total_cost,
                cost_by_category=cost_by_category,
                cost_breakdown=cost_breakdown,
                currency=costs[0].currency if costs else "USD",
                calculated_at=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Error calculating cost summary: {str(e)}")
            raise


class TransformationProcessTemplateService:
    """Service for managing transformation process templates."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_template(
        self, 
        template_data: TransformationProcessTemplateCreate,
        user_id: UUID
    ) -> TransformationProcessTemplate:
        """Create a new transformation process template."""
        try:
            template = TransformationProcessTemplate(
                template_name=template_data.template_name,
                transformation_type=template_data.transformation_type,
                company_type=template_data.company_type,
                sector_id=template_data.sector_id,
                template_config=template_data.template_config,
                default_metrics=template_data.default_metrics,
                cost_estimates=template_data.cost_estimates,
                quality_standards=template_data.quality_standards,
                description=template_data.description,
                version=template_data.version,
                is_standard=template_data.is_standard,
                is_active=template_data.is_active,
                created_by_user_id=user_id
            )
            
            self.db.add(template)
            self.db.commit()
            self.db.refresh(template)
            
            logger.info(f"Created transformation process template: {template_data.template_name}")
            return template
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating transformation process template: {str(e)}")
            raise
    
    def get_templates(
        self, 
        transformation_type: Optional[str] = None,
        company_type: Optional[str] = None,
        is_active: Optional[bool] = None,
        is_standard: Optional[bool] = None
    ) -> List[TransformationProcessTemplate]:
        """Get transformation process templates with optional filtering."""
        query = self.db.query(TransformationProcessTemplate)
        
        if transformation_type:
            query = query.filter(TransformationProcessTemplate.transformation_type == transformation_type)
        
        if company_type:
            query = query.filter(TransformationProcessTemplate.company_type == company_type)
        
        if is_active is not None:
            query = query.filter(TransformationProcessTemplate.is_active == is_active)
        
        if is_standard is not None:
            query = query.filter(TransformationProcessTemplate.is_standard == is_standard)
        
        return query.all()
    
    def use_template(
        self, 
        usage_data: TemplateUsageRequest,
        user_id: UUID
    ) -> Dict[str, Any]:
        """Use a transformation process template."""
        try:
            template = self.db.query(TransformationProcessTemplate)\
                .filter(TransformationProcessTemplate.id == usage_data.template_id)\
                .first()
            
            if not template:
                raise ValueError("Template not found")
            
            # Update usage statistics
            template.usage_count += 1
            template.last_used_at = datetime.utcnow()
            
            self.db.commit()
            
            # Return template configuration with custom parameters
            result = {
                "template_id": template.id,
                "template_name": template.template_name,
                "transformation_type": template.transformation_type,
                "template_config": template.template_config,
                "default_metrics": template.default_metrics,
                "cost_estimates": template.cost_estimates,
                "quality_standards": template.quality_standards,
                "custom_parameters": usage_data.custom_parameters or {}
            }
            
            logger.info(f"Used template {template.template_name} for transformation event {usage_data.transformation_event_id}")
            return result
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error using transformation process template: {str(e)}")
            raise
    
    def get_template_metrics(self, template_id: UUID) -> TemplateMetricsResponse:
        """Get metrics for a transformation process template."""
        try:
            template = self.db.query(TransformationProcessTemplate)\
                .filter(TransformationProcessTemplate.id == template_id)\
                .first()
            
            if not template:
                raise ValueError("Template not found")
            
            # Calculate additional metrics (placeholder for now)
            return TemplateMetricsResponse(
                template_id=template.id,
                usage_count=template.usage_count,
                last_used_at=template.last_used_at,
                average_efficiency=None,  # Would need to calculate from actual usage
                success_rate=None,  # Would need to calculate from actual usage
                common_customizations=[]  # Would need to track customizations
            )
            
        except Exception as e:
            logger.error(f"Error getting template metrics: {str(e)}")
            raise


class RealTimeMonitoringService:
    """Service for managing real-time monitoring endpoints."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_endpoint(
        self, 
        endpoint_data: RealTimeMonitoringEndpointCreate,
        user_id: UUID
    ) -> RealTimeMonitoringEndpoint:
        """Create a new real-time monitoring endpoint."""
        try:
            endpoint = RealTimeMonitoringEndpoint(
                facility_id=endpoint_data.facility_id,
                company_id=endpoint_data.company_id,
                endpoint_name=endpoint_data.endpoint_name,
                endpoint_type=endpoint_data.endpoint_type,
                endpoint_url=endpoint_data.endpoint_url,
                data_format=endpoint_data.data_format,
                monitored_metrics=endpoint_data.monitored_metrics,
                update_frequency=endpoint_data.update_frequency,
                data_retention_days=endpoint_data.data_retention_days,
                auth_type=endpoint_data.auth_type,
                auth_config=endpoint_data.auth_config,
                is_active=endpoint_data.is_active,
                created_by_user_id=user_id
            )
            
            self.db.add(endpoint)
            self.db.commit()
            self.db.refresh(endpoint)
            
            logger.info(f"Created real-time monitoring endpoint: {endpoint_data.endpoint_name}")
            return endpoint
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating real-time monitoring endpoint: {str(e)}")
            raise
    
    def get_endpoints(
        self, 
        company_id: Optional[UUID] = None,
        facility_id: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> List[RealTimeMonitoringEndpoint]:
        """Get real-time monitoring endpoints with optional filtering."""
        query = self.db.query(RealTimeMonitoringEndpoint)
        
        if company_id:
            query = query.filter(RealTimeMonitoringEndpoint.company_id == company_id)
        
        if facility_id:
            query = query.filter(RealTimeMonitoringEndpoint.facility_id == facility_id)
        
        if is_active is not None:
            query = query.filter(RealTimeMonitoringEndpoint.is_active == is_active)
        
        return query.all()
    
    def ingest_monitoring_data(
        self, 
        data: MonitoringDataIngestion
    ) -> Dict[str, Any]:
        """Ingest real-time monitoring data."""
        try:
            endpoint = self.db.query(RealTimeMonitoringEndpoint)\
                .filter(RealTimeMonitoringEndpoint.id == data.endpoint_id)\
                .first()
            
            if not endpoint:
                raise ValueError("Monitoring endpoint not found")
            
            # Update endpoint status
            endpoint.last_data_received = data.timestamp
            endpoint.error_count = 0  # Reset error count on successful data ingestion
            
            self.db.commit()
            
            # Process the monitoring data (placeholder for now)
            result = {
                "endpoint_id": data.endpoint_id,
                "timestamp": data.timestamp,
                "metrics_processed": len(data.metrics_data),
                "data_quality_score": data.data_quality_score,
                "status": "success"
            }
            
            logger.info(f"Ingested monitoring data for endpoint {data.endpoint_id}")
            return result
            
        except Exception as e:
            # Update error count
            endpoint = self.db.query(RealTimeMonitoringEndpoint)\
                .filter(RealTimeMonitoringEndpoint.id == data.endpoint_id)\
                .first()
            
            if endpoint:
                endpoint.error_count += 1
                endpoint.last_error = str(e)
                self.db.commit()
            
            logger.error(f"Error ingesting monitoring data: {str(e)}")
            raise





"""
Transformation metrics service for comprehensive KPI tracking and analysis.
Based on industry-standard metrics for palm oil supply chain transformations.
"""
from datetime import datetime, date, timedelta
from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID
from decimal import Decimal

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, asc, text
from fastapi import HTTPException, status

from app.models.transformation import TransformationEvent
from app.models.transformation_metrics import (
    TransformationMetrics,
    IndustryBenchmark,
    KPISummary,
    PerformanceTrend
)
from app.schemas.transformation_metrics import (
    TransformationMetricsCollection,
    PlantationMetrics,
    MillMetrics,
    KernelCrusherMetrics,
    RefineryMetrics,
    ManufacturerMetrics,
    KPISummary as KPISummarySchema,
    IndustryBenchmark as IndustryBenchmarkSchema,
    MetricCategory,
    MetricImportance
)
from app.schemas.pagination import PaginatedResponse, EnhancedPaginatedResponse


class TransformationMetricsService:
    """Service for managing transformation metrics and KPIs."""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def create_transformation_metrics(
        self, 
        transformation_event_id: UUID,
        metrics_data: TransformationMetricsCollection,
        user_id: UUID
    ) -> Dict[str, Any]:
        """Create comprehensive metrics for a transformation event."""
        try:
            # Verify transformation event exists
            transformation = self.db.query(TransformationEvent).filter(
                TransformationEvent.id == transformation_event_id
            ).first()
            
            if not transformation:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Transformation event not found"
                )
            
            # Create metrics based on transformation type
            created_metrics = []
            
            if transformation.transformation_type.value == "HARVEST" and metrics_data.plantation_metrics:
                created_metrics.extend(
                    await self._create_plantation_metrics(transformation_event_id, metrics_data.plantation_metrics, user_id)
                )
            
            elif transformation.transformation_type.value == "MILLING" and metrics_data.mill_metrics:
                created_metrics.extend(
                    await self._create_mill_metrics(transformation_event_id, metrics_data.mill_metrics, user_id)
                )
            
            elif transformation.transformation_type.value == "CRUSHING" and metrics_data.kernel_crusher_metrics:
                created_metrics.extend(
                    await self._create_kernel_crusher_metrics(transformation_event_id, metrics_data.kernel_crusher_metrics, user_id)
                )
            
            elif transformation.transformation_type.value in ["REFINING", "FRACTIONATION"] and metrics_data.refinery_metrics:
                created_metrics.extend(
                    await self._create_refinery_metrics(transformation_event_id, metrics_data.refinery_metrics, user_id)
                )
            
            elif transformation.transformation_type.value in ["BLENDING", "MANUFACTURING"] and metrics_data.manufacturer_metrics:
                created_metrics.extend(
                    await self._create_manufacturer_metrics(transformation_event_id, metrics_data.manufacturer_metrics, user_id)
                )
            
            # Calculate performance scores
            performance_scores = await self._calculate_performance_scores(transformation_event_id)
            
            # Generate KPI summary
            kpi_summary = await self._generate_kpi_summary(transformation_event_id, performance_scores, user_id)
            
            self.db.commit()
            
            return {
                "message": "Transformation metrics created successfully",
                "transformation_event_id": transformation_event_id,
                "metrics_created": len(created_metrics),
                "performance_scores": performance_scores,
                "kpi_summary_id": kpi_summary.id
            }
            
        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create transformation metrics: {str(e)}"
            )
    
    async def _create_metrics_bulk(
        self,
        transformation_event_id: UUID,
        metrics_data: List[Dict[str, Any]],
        user_id: UUID
    ) -> List[TransformationMetrics]:
        """Generic method to create metrics in bulk to avoid N+1 queries."""
        metrics = []
        
        for metric_data in metrics_data:
            metric = TransformationMetrics(
                transformation_event_id=transformation_event_id,
                created_by_user_id=user_id,
                **metric_data
            )
            metrics.append(metric)
        
        # Bulk insert all metrics to avoid N+1 queries
        if metrics:
            self.db.bulk_save_objects(metrics)
        
        return metrics
    
    async def _create_plantation_metrics(
        self, 
        transformation_event_id: UUID, 
        plantation_data: PlantationMetrics, 
        user_id: UUID
    ) -> List[TransformationMetrics]:
        """Create plantation-specific metrics using bulk operations."""
        metrics_data = []
        
        # Critical KPIs
        metrics_data.extend([
            {
                "metric_name": "yield_per_hectare",
                "metric_category": MetricCategory.ECONOMIC,
                "importance": MetricImportance.CRITICAL,
                "value": plantation_data.yield_per_hectare,
                "unit": "tonnes/ha",
                "target_value": 25.0,
                "min_acceptable": 10.0,
                "max_acceptable": 35.0,
                "measurement_date": datetime.utcnow()
            },
            {
                "metric_name": "oer_potential",
                "metric_category": MetricCategory.QUALITY,
                "importance": MetricImportance.CRITICAL,
                "value": plantation_data.oer_potential,
                "unit": "%",
                "target_value": 25.0,
                "min_acceptable": 15.0,
                "max_acceptable": 25.0,
                "measurement_date": datetime.utcnow()
            },
            {
                "metric_name": "harvest_to_mill_time_hours",
                "metric_category": MetricCategory.QUALITY,
                "importance": MetricImportance.CRITICAL,
                "value": plantation_data.harvest_to_mill_time_hours,
                "unit": "hours",
                "target_value": 12.0,
                "min_acceptable": 0.0,
                "max_acceptable": 48.0,
                "measurement_date": datetime.utcnow()
            }
        ])
        
        # Quality metrics
        if plantation_data.moisture_content is not None:
            metrics_data.append({
                "metric_name": "moisture_content",
                "metric_category": MetricCategory.QUALITY,
                "importance": MetricImportance.HIGH,
                "value": plantation_data.moisture_content,
                "unit": "%",
                "target_value": 15.0,
                "min_acceptable": 10.0,
                "max_acceptable": 20.0,
                "measurement_date": datetime.utcnow()
            })
        
        if plantation_data.free_fatty_acid is not None:
            metrics_data.append({
                "metric_name": "free_fatty_acid",
                "metric_category": MetricCategory.QUALITY,
                "importance": MetricImportance.HIGH,
                "value": plantation_data.free_fatty_acid,
                "unit": "%",
                "target_value": 2.0,
                "min_acceptable": 0.0,
                "max_acceptable": 5.0,
                "measurement_date": datetime.utcnow()
            })
        
        # Sustainability metrics
        if plantation_data.water_usage is not None:
            metrics_data.append({
                "metric_name": "water_usage",
                "metric_category": MetricCategory.SUSTAINABILITY,
                "importance": MetricImportance.MEDIUM,
                "value": plantation_data.water_usage,
                "unit": "liters/ha",
                "target_value": 5000.0,
                "min_acceptable": 0.0,
                "max_acceptable": 10000.0,
                "measurement_date": datetime.utcnow()
            })
        
        return await self._create_metrics_bulk(transformation_event_id, metrics_data, user_id)
    
    async def _create_mill_metrics(
        self, 
        transformation_event_id: UUID, 
        mill_data: MillMetrics, 
        user_id: UUID
    ) -> List[TransformationMetrics]:
        """Create mill-specific metrics."""
        metrics = []
        
        # Critical KPIs
        metrics.append(TransformationMetrics(
            transformation_event_id=transformation_event_id,
            metric_name="oil_extraction_rate",
            metric_category=MetricCategory.ECONOMIC,
            importance=MetricImportance.CRITICAL,
            value=mill_data.oil_extraction_rate,
            unit="%",
            target_value=23.0,
            min_acceptable=18.0,
            max_acceptable=25.0,
            measurement_date=datetime.utcnow(),
            created_by_user_id=user_id
        ))
        
        metrics.append(TransformationMetrics(
            transformation_event_id=transformation_event_id,
            metric_name="cpo_ffa_level",
            metric_category=MetricCategory.QUALITY,
            importance=MetricImportance.CRITICAL,
            value=mill_data.cpo_ffa_level,
            unit="%",
            target_value=1.5,
            min_acceptable=0.0,
            max_acceptable=5.0,
            measurement_date=datetime.utcnow(),
            created_by_user_id=user_id
        ))
        
        metrics.append(TransformationMetrics(
            transformation_event_id=transformation_event_id,
            metric_name="nut_fibre_boiler_ratio",
            metric_category=MetricCategory.SUSTAINABILITY,
            importance=MetricImportance.CRITICAL,
            value=mill_data.nut_fibre_boiler_ratio,
            unit="%",
            target_value=95.0,
            min_acceptable=70.0,
            max_acceptable=100.0,
            measurement_date=datetime.utcnow(),
            created_by_user_id=user_id
        ))
        
        # Efficiency metrics
        if mill_data.uptime_percentage is not None:
            metrics.append(TransformationMetrics(
                transformation_event_id=transformation_event_id,
                metric_name="uptime_percentage",
                metric_category=MetricCategory.EFFICIENCY,
                importance=MetricImportance.HIGH,
                value=mill_data.uptime_percentage,
                unit="%",
                target_value=95.0,
                min_acceptable=80.0,
                max_acceptable=100.0,
                measurement_date=datetime.utcnow(),
                created_by_user_id=user_id
            ))
        
        # Resource usage metrics
        if mill_data.energy_consumption is not None:
            metrics.append(TransformationMetrics(
                transformation_event_id=transformation_event_id,
                metric_name="energy_consumption",
                metric_category=MetricCategory.SUSTAINABILITY,
                importance=MetricImportance.HIGH,
                value=mill_data.energy_consumption,
                unit="kWh/tonne",
                target_value=50.0,
                min_acceptable=0.0,
                max_acceptable=100.0,
                measurement_date=datetime.utcnow(),
                created_by_user_id=user_id
            ))
        
        # Bulk insert all metrics to avoid N+1 queries
        if metrics:
            self.db.bulk_save_objects(metrics)
        
        return metrics
    
    async def _create_kernel_crusher_metrics(
        self, 
        transformation_event_id: UUID, 
        kernel_data: KernelCrusherMetrics, 
        user_id: UUID
    ) -> List[TransformationMetrics]:
        """Create kernel crusher-specific metrics."""
        metrics = []
        
        # Critical KPIs
        metrics.append(TransformationMetrics(
            transformation_event_id=transformation_event_id,
            metric_name="kernel_oil_yield",
            metric_category=MetricCategory.ECONOMIC,
            importance=MetricImportance.CRITICAL,
            value=kernel_data.kernel_oil_yield,
            unit="%",
            target_value=48.0,
            min_acceptable=40.0,
            max_acceptable=50.0,
            measurement_date=datetime.utcnow(),
            created_by_user_id=user_id
        ))
        
        metrics.append(TransformationMetrics(
            transformation_event_id=transformation_event_id,
            metric_name="cake_residual_oil",
            metric_category=MetricCategory.EFFICIENCY,
            importance=MetricImportance.CRITICAL,
            value=kernel_data.cake_residual_oil,
            unit="%",
            target_value=4.0,
            min_acceptable=0.0,
            max_acceptable=8.0,
            measurement_date=datetime.utcnow(),
            created_by_user_id=user_id
        ))
        
        # Bulk insert all metrics to avoid N+1 queries
        if metrics:
            self.db.bulk_save_objects(metrics)
        
        return metrics
    
    async def _create_refinery_metrics(
        self, 
        transformation_event_id: UUID, 
        refinery_data: RefineryMetrics, 
        user_id: UUID
    ) -> List[TransformationMetrics]:
        """Create refinery-specific metrics."""
        metrics = []
        
        # Critical KPIs
        metrics.append(TransformationMetrics(
            transformation_event_id=transformation_event_id,
            metric_name="refining_loss",
            metric_category=MetricCategory.ECONOMIC,
            importance=MetricImportance.CRITICAL,
            value=refinery_data.refining_loss,
            unit="%",
            target_value=1.2,
            min_acceptable=0.0,
            max_acceptable=2.0,
            measurement_date=datetime.utcnow(),
            created_by_user_id=user_id
        ))
        
        metrics.append(TransformationMetrics(
            transformation_event_id=transformation_event_id,
            metric_name="olein_yield",
            metric_category=MetricCategory.ECONOMIC,
            importance=MetricImportance.CRITICAL,
            value=refinery_data.olein_yield,
            unit="%",
            target_value=80.0,
            min_acceptable=60.0,
            max_acceptable=85.0,
            measurement_date=datetime.utcnow(),
            created_by_user_id=user_id
        ))
        
        metrics.append(TransformationMetrics(
            transformation_event_id=transformation_event_id,
            metric_name="stearin_yield",
            metric_category=MetricCategory.ECONOMIC,
            importance=MetricImportance.CRITICAL,
            value=refinery_data.stearin_yield,
            unit="%",
            target_value=25.0,
            min_acceptable=15.0,
            max_acceptable=30.0,
            measurement_date=datetime.utcnow(),
            created_by_user_id=user_id
        ))
        
        metrics.append(TransformationMetrics(
            transformation_event_id=transformation_event_id,
            metric_name="iodine_value_consistency",
            metric_category=MetricCategory.QUALITY,
            importance=MetricImportance.CRITICAL,
            value=refinery_data.iodine_value_consistency,
            unit="±",
            target_value=0.2,
            min_acceptable=0.0,
            max_acceptable=1.0,
            measurement_date=datetime.utcnow(),
            created_by_user_id=user_id
        ))
        
        # Bulk insert all metrics to avoid N+1 queries
        if metrics:
            self.db.bulk_save_objects(metrics)
        
        return metrics
    
    async def _create_manufacturer_metrics(
        self, 
        transformation_event_id: UUID, 
        manufacturer_data: ManufacturerMetrics, 
        user_id: UUID
    ) -> List[TransformationMetrics]:
        """Create manufacturer-specific metrics."""
        metrics = []
        
        # Critical KPIs
        metrics.append(TransformationMetrics(
            transformation_event_id=transformation_event_id,
            metric_name="recipe_adherence_variance",
            metric_category=MetricCategory.QUALITY,
            importance=MetricImportance.CRITICAL,
            value=manufacturer_data.recipe_adherence_variance,
            unit="%",
            target_value=0.1,
            min_acceptable=0.0,
            max_acceptable=0.5,
            measurement_date=datetime.utcnow(),
            created_by_user_id=user_id
        ))
        
        metrics.append(TransformationMetrics(
            transformation_event_id=transformation_event_id,
            metric_name="production_line_efficiency",
            metric_category=MetricCategory.EFFICIENCY,
            importance=MetricImportance.CRITICAL,
            value=manufacturer_data.production_line_efficiency,
            unit="%",
            target_value=98.0,
            min_acceptable=80.0,
            max_acceptable=100.0,
            measurement_date=datetime.utcnow(),
            created_by_user_id=user_id
        ))
        
        metrics.append(TransformationMetrics(
            transformation_event_id=transformation_event_id,
            metric_name="product_waste_scrap_rate",
            metric_category=MetricCategory.SUSTAINABILITY,
            importance=MetricImportance.CRITICAL,
            value=manufacturer_data.product_waste_scrap_rate,
            unit="%",
            target_value=0.5,
            min_acceptable=0.0,
            max_acceptable=2.0,
            measurement_date=datetime.utcnow(),
            created_by_user_id=user_id
        ))
        
        # Bulk insert all metrics to avoid N+1 queries
        if metrics:
            self.db.bulk_save_objects(metrics)
        
        return metrics
    
    async def _calculate_performance_scores(self, transformation_event_id: UUID) -> Dict[str, float]:
        """Calculate performance scores for a transformation event."""
        try:
            # Use the database function to calculate scores
            result = self.db.execute(
                text("SELECT * FROM calculate_performance_scores(:event_id)"),
                {"event_id": str(transformation_event_id)}
            ).fetchone()
            
            return {
                "efficiency_score": float(result.efficiency_score) if result.efficiency_score else 0.0,
                "quality_score": float(result.quality_score) if result.quality_score else 0.0,
                "sustainability_score": float(result.sustainability_score) if result.sustainability_score else 0.0,
                "overall_score": float(result.overall_score) if result.overall_score else 0.0
            }
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to calculate performance scores: {str(e)}"
            )
    
    async def _generate_kpi_summary(
        self, 
        transformation_event_id: UUID, 
        performance_scores: Dict[str, float], 
        user_id: UUID
    ) -> KPISummary:
        """Generate KPI summary for a transformation event."""
        try:
            # Generate performance alerts
            alerts_result = self.db.execute(
                text("SELECT * FROM generate_performance_alerts(:event_id)"),
                {"event_id": str(transformation_event_id)}
            ).fetchall()
            
            alerts = [alert[0] for alert in alerts_result] if alerts_result else []
            
            # Generate recommendations based on performance
            recommendations = await self._generate_recommendations(transformation_event_id, performance_scores)
            
            # Create KPI summary
            kpi_summary = KPISummary(
                transformation_event_id=transformation_event_id,
                efficiency_score=performance_scores["efficiency_score"],
                quality_score=performance_scores["quality_score"],
                sustainability_score=performance_scores["sustainability_score"],
                overall_score=performance_scores["overall_score"],
                alerts=alerts,
                recommendations=recommendations,
                report_period=datetime.utcnow().strftime("%Y-Q%q"),
                calculated_by_user_id=user_id
            )
            
            self.db.add(kpi_summary)
            return kpi_summary
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate KPI summary: {str(e)}"
            )
    
    async def _generate_recommendations(
        self, 
        transformation_event_id: UUID, 
        performance_scores: Dict[str, float]
    ) -> List[str]:
        """Generate improvement recommendations based on performance scores."""
        recommendations = []
        
        # Efficiency recommendations
        if performance_scores["efficiency_score"] < 80:
            recommendations.append("Focus on improving process efficiency through better equipment utilization and workflow optimization")
        
        # Quality recommendations
        if performance_scores["quality_score"] < 85:
            recommendations.append("Implement stricter quality control measures and regular equipment calibration")
        
        # Sustainability recommendations
        if performance_scores["sustainability_score"] < 75:
            recommendations.append("Reduce resource consumption and implement waste reduction strategies")
        
        # Overall recommendations
        if performance_scores["overall_score"] < 70:
            recommendations.append("Conduct comprehensive process review and implement continuous improvement program")
        
        return recommendations
    
    async def get_transformation_metrics(
        self, 
        transformation_event_id: UUID
    ) -> List[TransformationMetrics]:
        """Get all metrics for a transformation event."""
        try:
            metrics = self.db.query(TransformationMetrics).filter(
                TransformationMetrics.transformation_event_id == transformation_event_id
            ).all()
            
            return metrics
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get transformation metrics: {str(e)}"
            )
    
    async def get_transformation_metrics_paginated(
        self, 
        transformation_event_id: UUID,
        page: int = 1,
        per_page: int = 20
    ) -> PaginatedResponse[TransformationMetrics]:
        """Get paginated metrics for a transformation event."""
        try:
            # Get total count
            total_count = self.db.query(TransformationMetrics).filter(
                TransformationMetrics.transformation_event_id == transformation_event_id
            ).count()
            
            # Get paginated results
            offset = (page - 1) * per_page
            metrics = self.db.query(TransformationMetrics).filter(
                TransformationMetrics.transformation_event_id == transformation_event_id
            ).offset(offset).limit(per_page).all()
            
            return PaginatedResponse.create(
                items=metrics,
                page=page,
                per_page=per_page,
                total_items=total_count
            )
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get paginated transformation metrics: {str(e)}"
            )
    
    async def get_performance_trends(
        self, 
        company_id: UUID,
        transformation_type: str,
        metric_name: str,
        period_days: int = 30
    ) -> List[Dict[str, Any]]:
        """Get performance trends for a specific metric."""
        try:
            start_date = datetime.utcnow() - timedelta(days=period_days)
            
            trends = self.db.query(PerformanceTrend).filter(
                PerformanceTrend.company_id == company_id,
                PerformanceTrend.transformation_type == transformation_type,
                PerformanceTrend.metric_name == metric_name,
                PerformanceTrend.period_start >= start_date
            ).order_by(PerformanceTrend.period_start).all()
            
            return [
                {
                    "period_start": trend.period_start.isoformat(),
                    "period_end": trend.period_end.isoformat(),
                    "average_value": float(trend.average_value),
                    "min_value": float(trend.min_value),
                    "max_value": float(trend.max_value),
                    "trend_direction": trend.trend_direction,
                    "trend_strength": float(trend.trend_strength) if trend.trend_strength else None,
                    "volatility_score": float(trend.volatility_score) if trend.volatility_score else None
                }
                for trend in trends
            ]
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get performance trends: {str(e)}"
            )
    
    async def get_performance_trends_paginated(
        self, 
        company_id: UUID,
        transformation_type: str,
        metric_name: str,
        period_days: int = 30,
        page: int = 1,
        per_page: int = 20
    ) -> PaginatedResponse[Dict[str, Any]]:
        """Get paginated performance trends for a specific metric."""
        try:
            start_date = datetime.utcnow() - timedelta(days=period_days)
            
            # Get total count
            total_count = self.db.query(PerformanceTrend).filter(
                PerformanceTrend.company_id == company_id,
                PerformanceTrend.transformation_type == transformation_type,
                PerformanceTrend.metric_name == metric_name,
                PerformanceTrend.period_start >= start_date
            ).count()
            
            # Get paginated results
            offset = (page - 1) * per_page
            trends = self.db.query(PerformanceTrend).filter(
                PerformanceTrend.company_id == company_id,
                PerformanceTrend.transformation_type == transformation_type,
                PerformanceTrend.metric_name == metric_name,
                PerformanceTrend.period_start >= start_date
            ).order_by(PerformanceTrend.period_start).offset(offset).limit(per_page).all()
            
            trend_data = [
                {
                    "period_start": trend.period_start.isoformat(),
                    "period_end": trend.period_end.isoformat(),
                    "average_value": float(trend.average_value),
                    "min_value": float(trend.min_value),
                    "max_value": float(trend.max_value),
                    "trend_direction": trend.trend_direction,
                    "trend_strength": float(trend.trend_strength) if trend.trend_strength else None,
                    "volatility_score": float(trend.volatility_score) if trend.volatility_score else None
                }
                for trend in trends
            ]
            
            return PaginatedResponse.create(
                items=trend_data,
                page=page,
                per_page=per_page,
                total_items=total_count
            )
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get paginated performance trends: {str(e)}"
            )
    
    async def get_industry_benchmarks(
        self, 
        transformation_type: str
    ) -> List[IndustryBenchmark]:
        """Get industry benchmarks for a transformation type."""
        try:
            benchmarks = self.db.query(IndustryBenchmark).filter(
                IndustryBenchmark.transformation_type == transformation_type,
                IndustryBenchmark.valid_from <= datetime.utcnow(),
                or_(
                    IndustryBenchmark.valid_to.is_(None),
                    IndustryBenchmark.valid_to > datetime.utcnow()
                )
            ).all()
            
            return benchmarks
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get industry benchmarks: {str(e)}"
            )
    
    async def get_industry_benchmarks_paginated(
        self, 
        transformation_type: str,
        page: int = 1,
        per_page: int = 20
    ) -> PaginatedResponse[IndustryBenchmark]:
        """Get paginated industry benchmarks for a transformation type."""
        try:
            # Get total count
            total_count = self.db.query(IndustryBenchmark).filter(
                IndustryBenchmark.transformation_type == transformation_type,
                IndustryBenchmark.valid_from <= datetime.utcnow(),
                or_(
                    IndustryBenchmark.valid_to.is_(None),
                    IndustryBenchmark.valid_to > datetime.utcnow()
                )
            ).count()
            
            # Get paginated results
            offset = (page - 1) * per_page
            benchmarks = self.db.query(IndustryBenchmark).filter(
                IndustryBenchmark.transformation_type == transformation_type,
                IndustryBenchmark.valid_from <= datetime.utcnow(),
                or_(
                    IndustryBenchmark.valid_to.is_(None),
                    IndustryBenchmark.valid_to > datetime.utcnow()
                )
            ).offset(offset).limit(per_page).all()
            
            return PaginatedResponse.create(
                items=benchmarks,
                page=page,
                per_page=per_page,
                total_items=total_count
            )
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get paginated industry benchmarks: {str(e)}"
            )
    
    async def list_transformation_events_paginated(
        self,
        company_id: Optional[UUID] = None,
        transformation_type: Optional[str] = None,
        status: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        page: int = 1,
        per_page: int = 20
    ) -> PaginatedResponse[Dict[str, Any]]:
        """List transformation events with filtering and pagination."""
        try:
            from app.models.transformation import TransformationEvent
            
            # Build query
            query = self.db.query(TransformationEvent)
            
            if company_id:
                query = query.filter(TransformationEvent.company_id == company_id)
            if transformation_type:
                query = query.filter(TransformationEvent.transformation_type == transformation_type)
            if status:
                query = query.filter(TransformationEvent.status == status)
            if start_date:
                query = query.filter(TransformationEvent.start_time >= start_date)
            if end_date:
                query = query.filter(TransformationEvent.start_time <= end_date)
            
            # Get total count
            total_count = query.count()
            
            # Get paginated results
            offset = (page - 1) * per_page
            events = query.order_by(TransformationEvent.start_time.desc()).offset(offset).limit(per_page).all()
            
            event_data = [
                {
                    "id": str(event.id),
                    "event_id": event.event_id,
                    "transformation_type": event.transformation_type.value,
                    "company_id": str(event.company_id),
                    "facility_id": event.facility_id,
                    "start_time": event.start_time.isoformat() if event.start_time else None,
                    "end_time": event.end_time.isoformat() if event.end_time else None,
                    "status": event.status.value,
                    "validation_status": event.validation_status.value,
                    "created_at": event.created_at.isoformat() if event.created_at else None
                }
                for event in events
            ]
            
            return PaginatedResponse.create(
                items=event_data,
                page=page,
                per_page=per_page,
                total_items=total_count
            )
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to list paginated transformation events: {str(e)}"
            )
    
    async def get_kpi_summary(
        self, 
        transformation_event_id: UUID
    ) -> Optional[KPISummary]:
        """Get KPI summary for a transformation event."""
        try:
            kpi_summary = self.db.query(KPISummary).filter(
                KPISummary.transformation_event_id == transformation_event_id
            ).first()
            
            return kpi_summary
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get KPI summary: {str(e)}"
            )

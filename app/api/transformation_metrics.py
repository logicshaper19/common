"""
Transformation metrics API endpoints for comprehensive KPI tracking and analysis.
Based on industry-standard metrics for palm oil supply chain transformations.
"""
from datetime import datetime, date
from typing import List, Optional, Dict, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.schemas.transformation_metrics import (
    TransformationMetricsCollection,
    PlantationMetrics,
    MillMetrics,
    KernelCrusherMetrics,
    RefineryMetrics,
    ManufacturerMetrics,
    KPISummary as KPISummarySchema,
    IndustryBenchmark as IndustryBenchmarkSchema
)
from app.schemas.pagination import PaginationParams, PaginatedResponse, EnhancedPaginatedResponse
from app.services.transformation_metrics import TransformationMetricsService
from app.core.permissions import require_permission

router = APIRouter(prefix="/transformation-metrics", tags=["transformation-metrics"])


@router.post("/{transformation_event_id}/metrics")
async def create_transformation_metrics(
    transformation_event_id: UUID,
    metrics_data: TransformationMetricsCollection,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create comprehensive metrics for a transformation event."""
    require_permission(current_user, "create_transformation_metrics")
    
    service = TransformationMetricsService(db)
    return await service.create_transformation_metrics(transformation_event_id, metrics_data, current_user.id)


@router.get("/{transformation_event_id}/metrics")
async def get_transformation_metrics(
    transformation_event_id: UUID,
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all metrics for a transformation event with pagination."""
    require_permission(current_user, "view_transformation_metrics")
    
    service = TransformationMetricsService(db)
    return await service.get_transformation_metrics_paginated(
        transformation_event_id, 
        pagination.page, 
        pagination.per_page
    )


@router.get("/{transformation_event_id}/kpi-summary")
async def get_kpi_summary(
    transformation_event_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get KPI summary for a transformation event."""
    require_permission(current_user, "view_transformation_metrics")
    
    service = TransformationMetricsService(db)
    return await service.get_kpi_summary(transformation_event_id)


@router.get("/performance-trends")
async def get_performance_trends(
    company_id: UUID = Query(..., description="Company ID"),
    transformation_type: str = Query(..., description="Transformation type"),
    metric_name: str = Query(..., description="Metric name"),
    period_days: int = Query(30, ge=1, le=365, description="Period in days"),
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get performance trends for a specific metric with pagination."""
    require_permission(current_user, "view_transformation_metrics")
    
    service = TransformationMetricsService(db)
    return await service.get_performance_trends_paginated(
        company_id, 
        transformation_type, 
        metric_name, 
        period_days,
        pagination.page,
        pagination.per_page
    )


@router.get("/industry-benchmarks")
async def get_industry_benchmarks(
    transformation_type: str = Query(..., description="Transformation type"),
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get industry benchmarks for a transformation type with pagination."""
    require_permission(current_user, "view_transformation_metrics")
    
    service = TransformationMetricsService(db)
    return await service.get_industry_benchmarks_paginated(
        transformation_type,
        pagination.page,
        pagination.per_page
    )


@router.get("/events")
async def list_transformation_events(
    company_id: Optional[UUID] = Query(None, description="Filter by company ID"),
    transformation_type: Optional[str] = Query(None, description="Filter by transformation type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    start_date: Optional[date] = Query(None, description="Filter by start date"),
    end_date: Optional[date] = Query(None, description="Filter by end date"),
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List transformation events with filtering and pagination."""
    require_permission(current_user, "view_transformation_metrics")
    
    service = TransformationMetricsService(db)
    return await service.list_transformation_events_paginated(
        company_id=company_id,
        transformation_type=transformation_type,
        status=status,
        start_date=start_date,
        end_date=end_date,
        page=pagination.page,
        per_page=pagination.per_page
    )


# Role-specific metrics endpoints
@router.post("/{transformation_event_id}/plantation-metrics")
async def add_plantation_metrics(
    transformation_event_id: UUID,
    plantation_metrics: PlantationMetrics,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add plantation-specific metrics to a transformation event."""
    require_permission(current_user, "create_transformation_metrics")
    
    service = TransformationMetricsService(db)
    metrics_data = TransformationMetricsCollection(
        transformation_event_id=transformation_event_id,
        plantation_metrics=plantation_metrics
    )
    return await service.create_transformation_metrics(transformation_event_id, metrics_data, current_user.id)


@router.post("/{transformation_event_id}/mill-metrics")
async def add_mill_metrics(
    transformation_event_id: UUID,
    mill_metrics: MillMetrics,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add mill-specific metrics to a transformation event."""
    require_permission(current_user, "create_transformation_metrics")
    
    service = TransformationMetricsService(db)
    metrics_data = TransformationMetricsCollection(
        transformation_event_id=transformation_event_id,
        mill_metrics=mill_metrics
    )
    return await service.create_transformation_metrics(transformation_event_id, metrics_data, current_user.id)


@router.post("/{transformation_event_id}/kernel-crusher-metrics")
async def add_kernel_crusher_metrics(
    transformation_event_id: UUID,
    kernel_crusher_metrics: KernelCrusherMetrics,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add kernel crusher-specific metrics to a transformation event."""
    require_permission(current_user, "create_transformation_metrics")
    
    service = TransformationMetricsService(db)
    metrics_data = TransformationMetricsCollection(
        transformation_event_id=transformation_event_id,
        kernel_crusher_metrics=kernel_crusher_metrics
    )
    return await service.create_transformation_metrics(transformation_event_id, metrics_data, current_user.id)


@router.post("/{transformation_event_id}/refinery-metrics")
async def add_refinery_metrics(
    transformation_event_id: UUID,
    refinery_metrics: RefineryMetrics,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add refinery-specific metrics to a transformation event."""
    require_permission(current_user, "create_transformation_metrics")
    
    service = TransformationMetricsService(db)
    metrics_data = TransformationMetricsCollection(
        transformation_event_id=transformation_event_id,
        refinery_metrics=refinery_metrics
    )
    return await service.create_transformation_metrics(transformation_event_id, metrics_data, current_user.id)


@router.post("/{transformation_event_id}/manufacturer-metrics")
async def add_manufacturer_metrics(
    transformation_event_id: UUID,
    manufacturer_metrics: ManufacturerMetrics,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add manufacturer-specific metrics to a transformation event."""
    require_permission(current_user, "create_transformation_metrics")
    
    service = TransformationMetricsService(db)
    metrics_data = TransformationMetricsCollection(
        transformation_event_id=transformation_event_id,
        manufacturer_metrics=manufacturer_metrics
    )
    return await service.create_transformation_metrics(transformation_event_id, metrics_data, current_user.id)


# Analytics and reporting endpoints
@router.get("/analytics/performance-dashboard")
async def get_performance_dashboard(
    company_id: Optional[UUID] = Query(None, description="Filter by company ID"),
    transformation_type: Optional[str] = Query(None, description="Filter by transformation type"),
    start_date: Optional[date] = Query(None, description="Start date for analytics"),
    end_date: Optional[date] = Query(None, description="End date for analytics"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get performance dashboard data."""
    require_permission(current_user, "view_transformation_metrics")
    
    # This would be implemented to return dashboard data
    return {
        "message": "Performance dashboard endpoint - implementation needed",
        "company_id": company_id,
        "transformation_type": transformation_type,
        "start_date": start_date,
        "end_date": end_date
    }


@router.get("/analytics/benchmark-comparison")
async def get_benchmark_comparison(
    company_id: UUID = Query(..., description="Company ID"),
    transformation_type: str = Query(..., description="Transformation type"),
    metric_name: str = Query(..., description="Metric name"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get benchmark comparison for a specific metric."""
    require_permission(current_user, "view_transformation_metrics")
    
    # This would be implemented to return benchmark comparison data
    return {
        "message": "Benchmark comparison endpoint - implementation needed",
        "company_id": company_id,
        "transformation_type": transformation_type,
        "metric_name": metric_name
    }


@router.get("/analytics/trend-analysis")
async def get_trend_analysis(
    company_id: UUID = Query(..., description="Company ID"),
    transformation_type: str = Query(..., description="Transformation type"),
    metric_name: str = Query(..., description="Metric name"),
    period_months: int = Query(12, ge=1, le=36, description="Period in months"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get trend analysis for a specific metric."""
    require_permission(current_user, "view_transformation_metrics")
    
    service = TransformationMetricsService(db)
    period_days = period_months * 30
    return await service.get_performance_trends(company_id, transformation_type, metric_name, period_days)


# Utility endpoints
@router.get("/metrics/definitions")
async def get_metric_definitions():
    """Get definitions and explanations of all available metrics."""
    return {
        "plantation_metrics": {
            "yield_per_hectare": {
                "description": "FFB yield per hectare (tonnes/ha)",
                "importance": "critical",
                "category": "economic",
                "target": 25.0,
                "range": "10.0-35.0"
            },
            "oer_potential": {
                "description": "Oil Extraction Rate potential (%)",
                "importance": "critical",
                "category": "quality",
                "target": 25.0,
                "range": "15.0-25.0"
            },
            "harvest_to_mill_time_hours": {
                "description": "Time from harvest to mill (hours)",
                "importance": "critical",
                "category": "quality",
                "target": 12.0,
                "range": "0.0-48.0"
            }
        },
        "mill_metrics": {
            "oil_extraction_rate": {
                "description": "Oil Extraction Rate (%)",
                "importance": "critical",
                "category": "economic",
                "target": 23.0,
                "range": "18.0-25.0"
            },
            "cpo_ffa_level": {
                "description": "CPO Free Fatty Acid level (%)",
                "importance": "critical",
                "category": "quality",
                "target": 1.5,
                "range": "0.0-5.0"
            },
            "nut_fibre_boiler_ratio": {
                "description": "Nut & Fibre to Boiler ratio (%)",
                "importance": "critical",
                "category": "sustainability",
                "target": 95.0,
                "range": "70.0-100.0"
            }
        },
        "refinery_metrics": {
            "refining_loss": {
                "description": "Refining loss (%)",
                "importance": "critical",
                "category": "economic",
                "target": 1.2,
                "range": "0.0-2.0"
            },
            "olein_yield": {
                "description": "Olein yield (%)",
                "importance": "critical",
                "category": "economic",
                "target": 80.0,
                "range": "60.0-85.0"
            },
            "stearin_yield": {
                "description": "Stearin yield (%)",
                "importance": "critical",
                "category": "economic",
                "target": 25.0,
                "range": "15.0-30.0"
            },
            "iodine_value_consistency": {
                "description": "IV consistency (±0.5)",
                "importance": "critical",
                "category": "quality",
                "target": 0.2,
                "range": "0.0-1.0"
            }
        },
        "manufacturer_metrics": {
            "recipe_adherence_variance": {
                "description": "Recipe adherence variance (%)",
                "importance": "critical",
                "category": "quality",
                "target": 0.1,
                "range": "0.0-0.5"
            },
            "production_line_efficiency": {
                "description": "Production line efficiency (%)",
                "importance": "critical",
                "category": "efficiency",
                "target": 98.0,
                "range": "80.0-100.0"
            },
            "product_waste_scrap_rate": {
                "description": "Product waste/scrap rate (%)",
                "importance": "critical",
                "category": "sustainability",
                "target": 0.5,
                "range": "0.0-2.0"
            }
        }
    }


@router.get("/benchmarks/industry-standards")
async def get_industry_standards():
    """Get industry standard values for all metrics."""
    return {
        "plantation_standards": {
            "yield_per_hectare": {"average": 18.2, "best_practice": 25.0, "min_acceptable": 10.0, "max_acceptable": 35.0},
            "oer_potential": {"average": 22.5, "best_practice": 25.0, "min_acceptable": 15.0, "max_acceptable": 25.0},
            "harvest_to_mill_time_hours": {"average": 24.0, "best_practice": 12.0, "min_acceptable": 0.0, "max_acceptable": 48.0}
        },
        "mill_standards": {
            "oil_extraction_rate": {"average": 21.0, "best_practice": 23.0, "min_acceptable": 18.0, "max_acceptable": 25.0},
            "cpo_ffa_level": {"average": 2.8, "best_practice": 1.5, "min_acceptable": 0.0, "max_acceptable": 5.0},
            "nut_fibre_boiler_ratio": {"average": 85.0, "best_practice": 95.0, "min_acceptable": 70.0, "max_acceptable": 100.0}
        },
        "kernel_crusher_standards": {
            "kernel_oil_yield": {"average": 46.0, "best_practice": 48.0, "min_acceptable": 40.0, "max_acceptable": 50.0},
            "cake_residual_oil": {"average": 6.0, "best_practice": 4.0, "min_acceptable": 0.0, "max_acceptable": 8.0}
        },
        "refinery_standards": {
            "refining_loss": {"average": 1.8, "best_practice": 1.2, "min_acceptable": 0.0, "max_acceptable": 2.0},
            "olein_yield": {"average": 75.0, "best_practice": 80.0, "min_acceptable": 60.0, "max_acceptable": 85.0},
            "stearin_yield": {"average": 22.0, "best_practice": 25.0, "min_acceptable": 15.0, "max_acceptable": 30.0},
            "iodine_value_consistency": {"average": 0.5, "best_practice": 0.2, "min_acceptable": 0.0, "max_acceptable": 1.0}
        },
        "manufacturer_standards": {
            "recipe_adherence_variance": {"average": 0.3, "best_practice": 0.1, "min_acceptable": 0.0, "max_acceptable": 0.5},
            "production_line_efficiency": {"average": 95.0, "best_practice": 98.0, "min_acceptable": 80.0, "max_acceptable": 100.0},
            "product_waste_scrap_rate": {"average": 1.2, "best_practice": 0.5, "min_acceptable": 0.0, "max_acceptable": 2.0}
        }
    }

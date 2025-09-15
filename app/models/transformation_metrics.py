"""
Transformation metrics models for comprehensive KPI tracking and analysis.
Based on industry-standard metrics for palm oil supply chain transformations.
"""
from sqlalchemy import Column, String, DateTime, ForeignKey, func, Numeric, Index, Enum as SQLEnum, Text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid
from enum import Enum
from datetime import datetime

from app.core.database import Base


class MetricCategory(str, Enum):
    """Category of metrics for grouping and analysis."""
    ECONOMIC = "economic"
    QUALITY = "quality"
    EFFICIENCY = "efficiency"
    SUSTAINABILITY = "sustainability"
    OPERATIONAL = "operational"


class MetricImportance(str, Enum):
    """Importance level of metrics for business operations."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TransformationMetrics(Base):
    """Stores detailed metrics for transformation events with industry benchmarking."""
    
    __tablename__ = "transformation_metrics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transformation_event_id = Column(UUID(as_uuid=True), ForeignKey("transformation_events.id"), nullable=False)
    
    # Metric identification
    metric_name = Column(String(100), nullable=False)
    metric_category = Column(SQLEnum(MetricCategory), nullable=False)
    importance = Column(SQLEnum(MetricImportance), nullable=False)
    
    # Metric values
    value = Column(Numeric(12, 4), nullable=False)
    unit = Column(String(20), nullable=False)
    target_value = Column(Numeric(12, 4))
    min_acceptable = Column(Numeric(12, 4))
    max_acceptable = Column(Numeric(12, 4))
    
    # Benchmarking
    industry_average = Column(Numeric(12, 4))
    best_practice = Column(Numeric(12, 4))
    performance_vs_benchmark = Column(Numeric(5, 2))  # Percentage
    
    # Context
    measurement_date = Column(DateTime(timezone=True), nullable=False)
    measurement_method = Column(String(100))  # How the metric was measured
    measurement_equipment = Column(String(100))  # Equipment used
    notes = Column(Text)
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Additional metadata
    additional_metadata = Column(JSONB)
    
    # Relationships
    transformation_event = relationship("TransformationEvent")
    created_by_user = relationship("User")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_transformation_metrics_event', 'transformation_event_id'),
        Index('idx_transformation_metrics_name', 'metric_name'),
        Index('idx_transformation_metrics_category', 'metric_category'),
        Index('idx_transformation_metrics_importance', 'importance'),
        Index('idx_transformation_metrics_date', 'measurement_date'),
    )


class IndustryBenchmark(Base):
    """Industry benchmark data for performance comparison."""
    
    __tablename__ = "industry_benchmarks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    metric_name = Column(String(100), nullable=False)
    transformation_type = Column(String(50), nullable=False)  # References transformation_type enum
    
    # Benchmark values
    industry_average = Column(Numeric(12, 4), nullable=False)
    best_practice = Column(Numeric(12, 4), nullable=False)
    minimum_acceptable = Column(Numeric(12, 4), nullable=False)
    maximum_acceptable = Column(Numeric(12, 4), nullable=False)
    
    # Benchmark metadata
    data_source = Column(String(255), nullable=False)
    sample_size = Column(Numeric(10, 0))
    region = Column(String(100))
    last_updated = Column(DateTime(timezone=True), server_default=func.now())
    
    # Validity period
    valid_from = Column(DateTime(timezone=True), nullable=False)
    valid_to = Column(DateTime(timezone=True))
    
    # Additional context
    notes = Column(Text)
    methodology = Column(Text)
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_industry_benchmarks_type', 'transformation_type'),
        Index('idx_industry_benchmarks_name', 'metric_name'),
        Index('idx_industry_benchmarks_validity', 'valid_from', 'valid_to'),
    )


class KPISummary(Base):
    """KPI summaries and performance scores for reporting."""
    
    __tablename__ = "kpi_summaries"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transformation_event_id = Column(UUID(as_uuid=True), ForeignKey("transformation_events.id"), nullable=False)
    
    # Performance scores
    efficiency_score = Column(Numeric(5, 2), nullable=False)
    quality_score = Column(Numeric(5, 2), nullable=False)
    sustainability_score = Column(Numeric(5, 2), nullable=False)
    overall_score = Column(Numeric(5, 2), nullable=False)
    
    # Benchmarking
    industry_average_score = Column(Numeric(5, 2))
    performance_vs_benchmark = Column(Numeric(5, 2))
    
    # Alerts and recommendations
    alerts = Column(JSONB)  # Array of alert messages
    recommendations = Column(JSONB)  # Array of recommendation messages
    
    # Report metadata
    report_period = Column(String(20), nullable=False)  # e.g., '2024-Q1'
    report_date = Column(DateTime(timezone=True), server_default=func.now())
    calculated_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Additional context
    notes = Column(Text)
    additional_metadata = Column(JSONB)
    
    # Relationships
    transformation_event = relationship("TransformationEvent")
    calculated_by_user = relationship("User")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_kpi_summaries_event', 'transformation_event_id'),
        Index('idx_kpi_summaries_period', 'report_period'),
        Index('idx_kpi_summaries_date', 'report_date'),
    )


class PerformanceTrend(Base):
    """Performance trend analysis over time."""
    
    __tablename__ = "performance_trends"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    facility_id = Column(String(100))
    transformation_type = Column(String(50), nullable=False)
    metric_name = Column(String(100), nullable=False)
    
    # Trend data
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)
    period_type = Column(String(20), nullable=False)  # 'daily', 'weekly', 'monthly', 'quarterly'
    
    # Aggregated values
    average_value = Column(Numeric(12, 4), nullable=False)
    min_value = Column(Numeric(12, 4), nullable=False)
    max_value = Column(Numeric(12, 4), nullable=False)
    median_value = Column(Numeric(12, 4), nullable=False)
    standard_deviation = Column(Numeric(12, 4))
    
    # Trend indicators
    trend_direction = Column(String(10))  # 'up', 'down', 'stable'
    trend_strength = Column(Numeric(5, 2))  # Percentage change
    volatility_score = Column(Numeric(5, 2))  # Measure of variability
    
    # Metadata
    data_points = Column(Numeric(10, 0), nullable=False)
    calculated_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Additional context
    notes = Column(Text)
    additional_metadata = Column(JSONB)
    
    # Relationships
    company = relationship("Company")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_performance_trends_company', 'company_id'),
        Index('idx_performance_trends_type', 'transformation_type'),
        Index('idx_performance_trends_metric', 'metric_name'),
        Index('idx_performance_trends_period', 'period_start', 'period_end'),
    )

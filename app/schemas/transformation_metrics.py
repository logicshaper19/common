"""
Transformation metrics schemas for comprehensive supply chain KPI tracking.
Based on industry-standard metrics for palm oil supply chain transformations.
"""
from datetime import datetime, date
from typing import List, Optional, Dict, Any, Union
from uuid import UUID
from pydantic import BaseModel, Field, validator
from enum import Enum
from decimal import Decimal


class MetricImportance(str, Enum):
    """Importance level of metrics for business operations."""
    CRITICAL = "critical"  # Primary KPI with major financial impact
    HIGH = "high"  # Important for quality and efficiency
    MEDIUM = "medium"  # Useful for monitoring and optimization
    LOW = "low"  # Additional context and reporting


class MetricCategory(str, Enum):
    """Category of metrics for grouping and analysis."""
    ECONOMIC = "economic"  # Financial and productivity metrics
    QUALITY = "quality"  # Product quality and specifications
    EFFICIENCY = "efficiency"  # Process efficiency and utilization
    SUSTAINABILITY = "sustainability"  # Environmental and resource metrics
    OPERATIONAL = "operational"  # Production and operational metrics


# Base metric schema
class TransformationMetric(BaseModel):
    """Base schema for transformation metrics."""
    metric_name: str = Field(..., description="Name of the metric")
    value: Union[float, int, Decimal] = Field(..., description="Metric value")
    unit: str = Field(..., description="Unit of measurement")
    category: MetricCategory = Field(..., description="Metric category")
    importance: MetricImportance = Field(..., description="Business importance")
    target_value: Optional[Union[float, int, Decimal]] = Field(None, description="Target or benchmark value")
    min_acceptable: Optional[Union[float, int, Decimal]] = Field(None, description="Minimum acceptable value")
    max_acceptable: Optional[Union[float, int, Decimal]] = Field(None, description="Maximum acceptable value")
    measurement_date: datetime = Field(default_factory=datetime.utcnow, description="When metric was measured")
    notes: Optional[str] = Field(None, description="Additional notes or context")
    
    @validator('value')
    def validate_value_positive(cls, v):
        if v < 0:
            raise ValueError('Metric value must be positive')
        return v


# Plantation-specific metrics
class PlantationMetrics(BaseModel):
    """Plantation harvest metrics based on industry standards."""
    
    # Primary KPIs
    yield_per_hectare: float = Field(..., ge=0, le=50, description="FFB yield per hectare (tonnes/ha)")
    oer_potential: float = Field(..., ge=0, le=30, description="Oil Extraction Rate potential (%)")
    harvest_to_mill_time_hours: float = Field(..., ge=0, le=168, description="Time from harvest to mill (hours)")
    
    # Quality metrics
    ffb_quality_grade: str = Field(..., pattern=r'^[ABC]$', description="FFB quality grade (A, B, C)")
    moisture_content: float = Field(..., ge=0, le=100, description="Moisture content (%)")
    free_fatty_acid: float = Field(..., ge=0, le=10, description="Free fatty acid content (%)")
    
    # Economic metrics
    cost_per_hectare: Optional[float] = Field(None, ge=0, description="Production cost per hectare")
    labor_efficiency: Optional[float] = Field(None, ge=0, description="Labor efficiency (hours/tonne)")
    
    # Sustainability metrics
    water_usage: Optional[float] = Field(None, ge=0, description="Water usage (liters/hectare)")
    fuel_consumption: Optional[float] = Field(None, ge=0, description="Fuel consumption (liters/hectare)")
    pesticide_usage: Optional[float] = Field(None, ge=0, description="Pesticide usage (kg/hectare)")
    
    @validator('yield_per_hectare')
    def validate_yield_benchmark(cls, v):
        """Validate against industry benchmarks."""
        if v < 10:
            raise ValueError('Yield per hectare below industry minimum (10 tonnes/ha)')
        if v > 35:
            raise ValueError('Yield per hectare above industry maximum (35 tonnes/ha)')
        return v
    
    @validator('oer_potential')
    def validate_oer_benchmark(cls, v):
        """Validate OER against industry standards."""
        if v < 15:
            raise ValueError('OER potential below industry minimum (15%)')
        if v > 25:
            raise ValueError('OER potential above industry maximum (25%)')
        return v
    
    @validator('harvest_to_mill_time_hours')
    def validate_harvest_time(cls, v):
        """Validate harvest-to-mill time for quality preservation."""
        if v > 48:
            raise ValueError('Harvest-to-mill time exceeds quality threshold (48 hours)')
        return v


# Mill-specific metrics
class MillMetrics(BaseModel):
    """Mill processing metrics based on industry standards."""
    
    # Primary KPIs
    oil_extraction_rate: float = Field(..., ge=0, le=30, description="Oil Extraction Rate (%)")
    cpo_ffa_level: float = Field(..., ge=0, le=10, description="CPO Free Fatty Acid level (%)")
    nut_fibre_boiler_ratio: float = Field(..., ge=0, le=100, description="Nut & Fibre to Boiler ratio (%)")
    
    # Quality metrics
    cpo_moisture_content: float = Field(..., ge=0, le=5, description="CPO moisture content (%)")
    cpo_impurities: float = Field(..., ge=0, le=5, description="CPO impurities (%)")
    kernel_quality_grade: Optional[str] = Field(None, pattern=r'^[ABC]$', description="Kernel quality grade")
    
    # Efficiency metrics
    processing_capacity: float = Field(..., ge=0, description="Processing capacity (tonnes/hour)")
    actual_throughput: float = Field(..., ge=0, description="Actual throughput (tonnes/hour)")
    uptime_percentage: float = Field(..., ge=0, le=100, description="Mill uptime percentage")
    
    # Resource usage
    energy_consumption: float = Field(..., ge=0, description="Energy consumption (kWh/tonne)")
    water_consumption: float = Field(..., ge=0, description="Water consumption (m³/tonne)")
    steam_consumption: float = Field(..., ge=0, description="Steam consumption (tonnes/tonne)")
    
    # Economic metrics
    cost_per_tonne: Optional[float] = Field(None, ge=0, description="Processing cost per tonne")
    revenue_per_tonne: Optional[float] = Field(None, description="Revenue per tonne")
    
    @validator('oil_extraction_rate')
    def validate_oer_benchmark(cls, v):
        """Validate OER against industry benchmarks."""
        if v < 18:
            raise ValueError('OER below industry minimum (18%)')
        if v > 25:
            raise ValueError('OER above industry maximum (25%)')
        return v
    
    @validator('cpo_ffa_level')
    def validate_ffa_quality(cls, v):
        """Validate FFA level for oil quality."""
        if v > 5:
            raise ValueError('FFA level exceeds quality threshold (5%)')
        return v
    
    @validator('nut_fibre_boiler_ratio')
    def validate_energy_self_sufficiency(cls, v):
        """Validate energy self-sufficiency."""
        if v < 70:
            raise ValueError('Energy self-sufficiency below minimum (70%)')
        return v


# Palm Kernel Crusher metrics
class KernelCrusherMetrics(BaseModel):
    """Palm kernel crushing metrics based on industry standards."""
    
    # Primary KPIs
    kernel_oil_yield: float = Field(..., ge=0, le=60, description="Kernel oil yield (%)")
    cake_residual_oil: float = Field(..., ge=0, le=15, description="Cake residual oil (%)")
    
    # Quality metrics
    pko_ffa_level: float = Field(..., ge=0, le=5, description="PKO Free Fatty Acid level (%)")
    pko_moisture_content: float = Field(..., ge=0, le=1, description="PKO moisture content (%)")
    cake_protein_content: Optional[float] = Field(None, ge=0, le=100, description="Cake protein content (%)")
    
    # Efficiency metrics
    crushing_capacity: float = Field(..., ge=0, description="Crushing capacity (tonnes/hour)")
    actual_throughput: float = Field(..., ge=0, description="Actual throughput (tonnes/hour)")
    crushing_efficiency: float = Field(..., ge=0, le=100, description="Crushing efficiency (%)")
    
    # Resource usage
    energy_consumption: float = Field(..., ge=0, description="Energy consumption (kWh/tonne)")
    water_consumption: float = Field(..., ge=0, description="Water consumption (m³/tonne)")
    
    @validator('kernel_oil_yield')
    def validate_kernel_yield_benchmark(cls, v):
        """Validate kernel oil yield against industry benchmarks."""
        if v < 40:
            raise ValueError('Kernel oil yield below industry minimum (40%)')
        if v > 50:
            raise ValueError('Kernel oil yield above industry maximum (50%)')
        return v
    
    @validator('cake_residual_oil')
    def validate_cake_residual_benchmark(cls, v):
        """Validate cake residual oil against industry standards."""
        if v > 8:
            raise ValueError('Cake residual oil exceeds industry maximum (8%)')
        return v


# Refinery metrics
class RefineryMetrics(BaseModel):
    """Refinery processing metrics based on industry standards."""
    
    # Primary KPIs
    refining_loss: float = Field(..., ge=0, le=5, description="Refining loss (%)")
    olein_yield: float = Field(..., ge=0, le=100, description="Olein yield (%)")
    stearin_yield: float = Field(..., ge=0, le=100, description="Stearin yield (%)")
    iodine_value_consistency: float = Field(..., ge=0, le=100, description="IV consistency (±0.5)")
    
    # Quality metrics
    iodine_value: float = Field(..., ge=40, le=70, description="Iodine Value (IV)")
    melting_point: float = Field(..., ge=20, le=60, description="Melting point (°C)")
    color_grade: str = Field(..., pattern=r'^[0-9]+[LR]$', description="Color grade (e.g., 3L, 5R)")
    
    # Fractionation metrics
    fractionation_efficiency: float = Field(..., ge=0, le=100, description="Fractionation efficiency (%)")
    temperature_control_accuracy: float = Field(..., ge=0, le=100, description="Temperature control accuracy (%)")
    
    # Resource usage
    energy_consumption: float = Field(..., ge=0, description="Energy consumption (kWh/tonne)")
    water_consumption: float = Field(..., ge=0, description="Water consumption (m³/tonne)")
    chemical_usage: Optional[Dict[str, float]] = Field(None, description="Chemical usage (kg/tonne)")
    
    @validator('refining_loss')
    def validate_refining_loss_benchmark(cls, v):
        """Validate refining loss against industry benchmarks."""
        if v > 2:
            raise ValueError('Refining loss exceeds industry maximum (2%)')
        return v
    
    @validator('olein_yield', 'stearin_yield')
    def validate_fractionation_yields(cls, v):
        """Validate fractionation yields."""
        if v < 15:
            raise ValueError('Fractionation yield below minimum (15%)')
        if v > 85:
            raise ValueError('Fractionation yield above maximum (85%)')
        return v
    
    @validator('iodine_value_consistency')
    def validate_iv_consistency(cls, v):
        """Validate IV consistency for product specification."""
        if v > 1:
            raise ValueError('IV consistency exceeds specification tolerance (±0.5)')
        return v


# Manufacturer/Brand metrics
class ManufacturerMetrics(BaseModel):
    """Manufacturer processing metrics based on industry standards."""
    
    # Primary KPIs
    recipe_adherence_variance: float = Field(..., ge=0, le=5, description="Recipe adherence variance (%)")
    production_line_efficiency: float = Field(..., ge=0, le=100, description="Production line efficiency (%)")
    product_waste_scrap_rate: float = Field(..., ge=0, le=10, description="Product waste/scrap rate (%)")
    
    # Quality metrics
    product_consistency: float = Field(..., ge=0, le=100, description="Product consistency (%)")
    quality_control_pass_rate: float = Field(..., ge=0, le=100, description="QC pass rate (%)")
    customer_specification_compliance: float = Field(..., ge=0, le=100, description="Customer spec compliance (%)")
    
    # Operational metrics
    production_uptime: float = Field(..., ge=0, le=100, description="Production uptime (%)")
    changeover_time: Optional[float] = Field(None, ge=0, description="Changeover time (minutes)")
    maintenance_downtime: Optional[float] = Field(None, ge=0, description="Maintenance downtime (hours)")
    
    # Resource usage
    energy_consumption: float = Field(..., ge=0, description="Energy consumption (kWh/unit)")
    water_consumption: float = Field(..., ge=0, description="Water consumption (m³/unit)")
    raw_material_utilization: float = Field(..., ge=0, le=100, description="Raw material utilization (%)")
    
    # Economic metrics
    cost_per_unit: Optional[float] = Field(None, ge=0, description="Cost per unit produced")
    revenue_per_unit: Optional[float] = Field(None, description="Revenue per unit")
    profit_margin: Optional[float] = Field(None, description="Profit margin (%)")
    
    @validator('recipe_adherence_variance')
    def validate_recipe_adherence(cls, v):
        """Validate recipe adherence against quality standards."""
        if v > 0.5:
            raise ValueError('Recipe adherence variance exceeds quality threshold (0.5%)')
        return v
    
    @validator('production_line_efficiency')
    def validate_production_efficiency(cls, v):
        """Validate production line efficiency."""
        if v < 80:
            raise ValueError('Production line efficiency below minimum (80%)')
        return v
    
    @validator('product_waste_scrap_rate')
    def validate_waste_rate(cls, v):
        """Validate waste/scrap rate against sustainability standards."""
        if v > 2:
            raise ValueError('Waste/scrap rate exceeds sustainability threshold (2%)')
        return v


# Comprehensive metrics collection
class TransformationMetricsCollection(BaseModel):
    """Collection of all transformation metrics for a specific event."""
    transformation_event_id: UUID
    plantation_metrics: Optional[PlantationMetrics] = None
    mill_metrics: Optional[MillMetrics] = None
    kernel_crusher_metrics: Optional[KernelCrusherMetrics] = None
    refinery_metrics: Optional[RefineryMetrics] = None
    manufacturer_metrics: Optional[ManufacturerMetrics] = None
    
    # Overall performance indicators
    overall_efficiency_score: Optional[float] = Field(None, ge=0, le=100, description="Overall efficiency score")
    quality_score: Optional[float] = Field(None, ge=0, le=100, description="Overall quality score")
    sustainability_score: Optional[float] = Field(None, ge=0, le=100, description="Overall sustainability score")
    
    # Benchmarking data
    industry_benchmark_comparison: Optional[Dict[str, Any]] = Field(None, description="Comparison with industry benchmarks")
    performance_trends: Optional[Dict[str, Any]] = Field(None, description="Performance trends over time")
    
    # Metadata
    calculated_at: datetime = Field(default_factory=datetime.utcnow)
    calculated_by: Optional[UUID] = Field(None, description="User who calculated the metrics")
    notes: Optional[str] = Field(None, description="Additional notes or context")


# KPI summary for reporting
class KPISummary(BaseModel):
    """Summary of key performance indicators for reporting."""
    transformation_type: str
    company_name: str
    facility_id: Optional[str]
    
    # Critical KPIs
    critical_kpis: List[TransformationMetric] = Field(..., description="Critical KPIs for this transformation")
    
    # Performance scores
    efficiency_score: float = Field(..., ge=0, le=100)
    quality_score: float = Field(..., ge=0, le=100)
    sustainability_score: float = Field(..., ge=0, le=100)
    
    # Benchmarking
    industry_average: Optional[float] = Field(None, description="Industry average for comparison")
    performance_vs_benchmark: Optional[float] = Field(None, description="Performance vs industry benchmark (%)")
    
    # Alerts and recommendations
    alerts: List[str] = Field(default_factory=list, description="Performance alerts")
    recommendations: List[str] = Field(default_factory=list, description="Improvement recommendations")
    
    # Metadata
    report_date: datetime = Field(default_factory=datetime.utcnow)
    report_period: str = Field(..., description="Report period (e.g., '2024-Q1')")


# Industry benchmark data
class IndustryBenchmark(BaseModel):
    """Industry benchmark data for comparison."""
    metric_name: str
    transformation_type: str
    industry_average: float
    best_practice: float
    minimum_acceptable: float
    maximum_acceptable: float
    data_source: str = Field(..., description="Source of benchmark data")
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    sample_size: Optional[int] = Field(None, description="Number of companies in benchmark")
    region: Optional[str] = Field(None, description="Geographic region of benchmark")

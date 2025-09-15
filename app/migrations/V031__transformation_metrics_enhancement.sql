-- Migration V031: Transformation Metrics Enhancement
-- Add comprehensive metrics tracking based on industry standards

-- 1. Create metrics categories and importance enums
CREATE TYPE metric_category AS ENUM (
    'economic',
    'quality', 
    'efficiency',
    'sustainability',
    'operational'
);

CREATE TYPE metric_importance AS ENUM (
    'critical',
    'high',
    'medium',
    'low'
);

-- 2. Create transformation metrics table
CREATE TABLE transformation_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transformation_event_id UUID NOT NULL REFERENCES transformation_events(id),
    
    -- Metric identification
    metric_name VARCHAR(100) NOT NULL,
    metric_category metric_category NOT NULL,
    importance metric_importance NOT NULL,
    
    -- Metric values
    value NUMERIC(12, 4) NOT NULL,
    unit VARCHAR(20) NOT NULL,
    target_value NUMERIC(12, 4),
    min_acceptable NUMERIC(12, 4),
    max_acceptable NUMERIC(12, 4),
    
    -- Benchmarking
    industry_average NUMERIC(12, 4),
    best_practice NUMERIC(12, 4),
    performance_vs_benchmark NUMERIC(5, 2), -- Percentage
    
    -- Context
    measurement_date TIMESTAMP WITH TIME ZONE NOT NULL,
    measurement_method VARCHAR(100), -- How the metric was measured
    measurement_equipment VARCHAR(100), -- Equipment used
    notes TEXT,
    
    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by_user_id UUID NOT NULL REFERENCES users(id),
    
    -- Additional metadata
    metadata JSONB
);

-- 3. Create industry benchmarks table
CREATE TABLE industry_benchmarks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    metric_name VARCHAR(100) NOT NULL,
    transformation_type transformation_type NOT NULL,
    
    -- Benchmark values
    industry_average NUMERIC(12, 4) NOT NULL,
    best_practice NUMERIC(12, 4) NOT NULL,
    minimum_acceptable NUMERIC(12, 4) NOT NULL,
    maximum_acceptable NUMERIC(12, 4) NOT NULL,
    
    -- Benchmark metadata
    data_source VARCHAR(255) NOT NULL,
    sample_size INTEGER,
    region VARCHAR(100),
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Validity period
    valid_from TIMESTAMP WITH TIME ZONE NOT NULL,
    valid_to TIMESTAMP WITH TIME ZONE,
    
    -- Additional context
    notes TEXT,
    methodology TEXT
);

-- 4. Create KPI summary table for reporting
CREATE TABLE kpi_summaries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transformation_event_id UUID NOT NULL REFERENCES transformation_events(id),
    
    -- Performance scores
    efficiency_score NUMERIC(5, 2) NOT NULL CHECK (efficiency_score >= 0 AND efficiency_score <= 100),
    quality_score NUMERIC(5, 2) NOT NULL CHECK (quality_score >= 0 AND quality_score <= 100),
    sustainability_score NUMERIC(5, 2) NOT NULL CHECK (sustainability_score >= 0 AND sustainability_score <= 100),
    overall_score NUMERIC(5, 2) NOT NULL CHECK (overall_score >= 0 AND overall_score <= 100),
    
    -- Benchmarking
    industry_average_score NUMERIC(5, 2),
    performance_vs_benchmark NUMERIC(5, 2),
    
    -- Alerts and recommendations
    alerts JSONB, -- Array of alert messages
    recommendations JSONB, -- Array of recommendation messages
    
    -- Report metadata
    report_period VARCHAR(20) NOT NULL, -- e.g., '2024-Q1'
    report_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    calculated_by_user_id UUID NOT NULL REFERENCES users(id),
    
    -- Additional context
    notes TEXT,
    metadata JSONB
);

-- 5. Create performance trends table
CREATE TABLE performance_trends (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id),
    facility_id VARCHAR(100),
    transformation_type transformation_type NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    
    -- Trend data
    period_start TIMESTAMP WITH TIME ZONE NOT NULL,
    period_end TIMESTAMP WITH TIME ZONE NOT NULL,
    period_type VARCHAR(20) NOT NULL, -- 'daily', 'weekly', 'monthly', 'quarterly'
    
    -- Aggregated values
    average_value NUMERIC(12, 4) NOT NULL,
    min_value NUMERIC(12, 4) NOT NULL,
    max_value NUMERIC(12, 4) NOT NULL,
    median_value NUMERIC(12, 4) NOT NULL,
    standard_deviation NUMERIC(12, 4),
    
    -- Trend indicators
    trend_direction VARCHAR(10), -- 'up', 'down', 'stable'
    trend_strength NUMERIC(5, 2), -- Percentage change
    volatility_score NUMERIC(5, 2), -- Measure of variability
    
    -- Metadata
    data_points INTEGER NOT NULL,
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Additional context
    notes TEXT,
    metadata JSONB
);

-- 6. Create indexes for performance
CREATE INDEX idx_transformation_metrics_event ON transformation_metrics(transformation_event_id);
CREATE INDEX idx_transformation_metrics_name ON transformation_metrics(metric_name);
CREATE INDEX idx_transformation_metrics_category ON transformation_metrics(metric_category);
CREATE INDEX idx_transformation_metrics_importance ON transformation_metrics(importance);
CREATE INDEX idx_transformation_metrics_date ON transformation_metrics(measurement_date);

CREATE INDEX idx_industry_benchmarks_type ON industry_benchmarks(transformation_type);
CREATE INDEX idx_industry_benchmarks_name ON industry_benchmarks(metric_name);
CREATE INDEX idx_industry_benchmarks_validity ON industry_benchmarks(valid_from, valid_to);

CREATE INDEX idx_kpi_summaries_event ON kpi_summaries(transformation_event_id);
CREATE INDEX idx_kpi_summaries_period ON kpi_summaries(report_period);
CREATE INDEX idx_kpi_summaries_date ON kpi_summaries(report_date);

CREATE INDEX idx_performance_trends_company ON performance_trends(company_id);
CREATE INDEX idx_performance_trends_type ON performance_trends(transformation_type);
CREATE INDEX idx_performance_trends_metric ON performance_trends(metric_name);
CREATE INDEX idx_performance_trends_period ON performance_trends(period_start, period_end);

-- 7. Create views for easy querying
CREATE VIEW transformation_metrics_summary AS
SELECT 
    te.id as transformation_event_id,
    te.event_id,
    te.transformation_type,
    c.company_name,
    te.facility_id,
    te.start_time,
    te.end_time,
    
    -- Critical metrics count
    COUNT(CASE WHEN tm.importance = 'critical' THEN 1 END) as critical_metrics_count,
    COUNT(CASE WHEN tm.importance = 'high' THEN 1 END) as high_metrics_count,
    
    -- Performance scores
    kpi.efficiency_score,
    kpi.quality_score,
    kpi.sustainability_score,
    kpi.overall_score,
    
    -- Benchmark comparison
    kpi.performance_vs_benchmark,
    
    -- Alerts and recommendations
    kpi.alerts,
    kpi.recommendations
    
FROM transformation_events te
JOIN companies c ON c.id = te.company_id
LEFT JOIN transformation_metrics tm ON tm.transformation_event_id = te.id
LEFT JOIN kpi_summaries kpi ON kpi.transformation_event_id = te.id
GROUP BY te.id, te.event_id, te.transformation_type, c.company_name, te.facility_id, 
         te.start_time, te.end_time, kpi.efficiency_score, kpi.quality_score, 
         kpi.sustainability_score, kpi.overall_score, kpi.performance_vs_benchmark,
         kpi.alerts, kpi.recommendations;

-- 8. Create function to calculate performance scores
CREATE OR REPLACE FUNCTION calculate_performance_scores(
    p_transformation_event_id UUID
) RETURNS TABLE (
    efficiency_score NUMERIC,
    quality_score NUMERIC,
    sustainability_score NUMERIC,
    overall_score NUMERIC
) AS $$
DECLARE
    v_efficiency_score NUMERIC := 0;
    v_quality_score NUMERIC := 0;
    v_sustainability_score NUMERIC := 0;
    v_overall_score NUMERIC := 0;
    v_total_metrics INTEGER := 0;
    v_efficiency_metrics INTEGER := 0;
    v_quality_metrics INTEGER := 0;
    v_sustainability_metrics INTEGER := 0;
BEGIN
    -- Calculate efficiency score
    SELECT 
        COALESCE(AVG(
            CASE 
                WHEN tm.value >= tm.target_value THEN 100
                WHEN tm.target_value > 0 THEN (tm.value / tm.target_value) * 100
                ELSE 0
            END
        ), 0),
        COUNT(*)
    INTO v_efficiency_score, v_efficiency_metrics
    FROM transformation_metrics tm
    WHERE tm.transformation_event_id = p_transformation_event_id
    AND tm.metric_category = 'efficiency';
    
    -- Calculate quality score
    SELECT 
        COALESCE(AVG(
            CASE 
                WHEN tm.value <= tm.max_acceptable AND tm.value >= tm.min_acceptable THEN 100
                WHEN tm.max_acceptable > tm.min_acceptable THEN 
                    GREATEST(0, 100 - ABS(tm.value - ((tm.max_acceptable + tm.min_acceptable) / 2)) / 
                    ((tm.max_acceptable - tm.min_acceptable) / 2) * 50)
                ELSE 0
            END
        ), 0),
        COUNT(*)
    INTO v_quality_score, v_quality_metrics
    FROM transformation_metrics tm
    WHERE tm.transformation_event_id = p_transformation_event_id
    AND tm.metric_category = 'quality';
    
    -- Calculate sustainability score
    SELECT 
        COALESCE(AVG(
            CASE 
                WHEN tm.value <= tm.target_value THEN 100
                WHEN tm.target_value > 0 THEN (tm.target_value / tm.value) * 100
                ELSE 0
            END
        ), 0),
        COUNT(*)
    INTO v_sustainability_score, v_sustainability_metrics
    FROM transformation_metrics tm
    WHERE tm.transformation_event_id = p_transformation_event_id
    AND tm.metric_category = 'sustainability';
    
    -- Calculate overall score
    v_total_metrics := v_efficiency_metrics + v_quality_metrics + v_sustainability_metrics;
    IF v_total_metrics > 0 THEN
        v_overall_score := (v_efficiency_score + v_quality_score + v_sustainability_score) / 3;
    END IF;
    
    RETURN QUERY SELECT v_efficiency_score, v_quality_score, v_sustainability_score, v_overall_score;
END;
$$ LANGUAGE plpgsql;

-- 9. Create function to generate performance alerts
CREATE OR REPLACE FUNCTION generate_performance_alerts(
    p_transformation_event_id UUID
) RETURNS TEXT[] AS $$
DECLARE
    v_alerts TEXT[] := '{}';
    v_metric RECORD;
BEGIN
    -- Check for metrics below minimum acceptable values
    FOR v_metric IN
        SELECT tm.metric_name, tm.value, tm.min_acceptable, tm.unit
        FROM transformation_metrics tm
        WHERE tm.transformation_event_id = p_transformation_event_id
        AND tm.min_acceptable IS NOT NULL
        AND tm.value < tm.min_acceptable
    LOOP
        v_alerts := array_append(v_alerts, 
            v_metric.metric_name || ' (' || v_metric.value || ' ' || v_metric.unit || 
            ') is below minimum acceptable value (' || v_metric.min_acceptable || ' ' || v_metric.unit || ')'
        );
    END LOOP;
    
    -- Check for metrics above maximum acceptable values
    FOR v_metric IN
        SELECT tm.metric_name, tm.value, tm.max_acceptable, tm.unit
        FROM transformation_metrics tm
        WHERE tm.transformation_event_id = p_transformation_event_id
        AND tm.max_acceptable IS NOT NULL
        AND tm.value > tm.max_acceptable
    LOOP
        v_alerts := array_append(v_alerts, 
            v_metric.metric_name || ' (' || v_metric.value || ' ' || v_metric.unit || 
            ') exceeds maximum acceptable value (' || v_metric.max_acceptable || ' ' || v_metric.unit || ')'
        );
    END LOOP;
    
    -- Check for critical metrics performance
    FOR v_metric IN
        SELECT tm.metric_name, tm.value, tm.target_value, tm.unit
        FROM transformation_metrics tm
        WHERE tm.transformation_event_id = p_transformation_event_id
        AND tm.importance = 'critical'
        AND tm.target_value IS NOT NULL
        AND tm.value < (tm.target_value * 0.9) -- 10% below target
    LOOP
        v_alerts := array_append(v_alerts, 
            'CRITICAL: ' || v_metric.metric_name || ' is significantly below target (' || 
            v_metric.value || ' ' || v_metric.unit || ' vs ' || v_metric.target_value || ' ' || v_metric.unit || ')'
        );
    END LOOP;
    
    RETURN v_alerts;
END;
$$ LANGUAGE plpgsql;

-- 10. Insert industry benchmark data
INSERT INTO industry_benchmarks (metric_name, transformation_type, industry_average, best_practice, minimum_acceptable, maximum_acceptable, data_source, valid_from) VALUES
-- Plantation benchmarks
('yield_per_hectare', 'HARVEST', 18.2, 25.0, 10.0, 35.0, 'Industry Standard', '2024-01-01'),
('oer_potential', 'HARVEST', 22.5, 25.0, 15.0, 25.0, 'Industry Standard', '2024-01-01'),
('harvest_to_mill_time_hours', 'HARVEST', 24.0, 12.0, 0.0, 48.0, 'Industry Standard', '2024-01-01'),

-- Mill benchmarks
('oil_extraction_rate', 'MILLING', 21.0, 23.0, 18.0, 25.0, 'Industry Standard', '2024-01-01'),
('cpo_ffa_level', 'MILLING', 2.8, 1.5, 0.0, 5.0, 'Industry Standard', '2024-01-01'),
('nut_fibre_boiler_ratio', 'MILLING', 85.0, 95.0, 70.0, 100.0, 'Industry Standard', '2024-01-01'),

-- Kernel crusher benchmarks
('kernel_oil_yield', 'CRUSHING', 46.0, 48.0, 40.0, 50.0, 'Industry Standard', '2024-01-01'),
('cake_residual_oil', 'CRUSHING', 6.0, 4.0, 0.0, 8.0, 'Industry Standard', '2024-01-01'),

-- Refinery benchmarks
('refining_loss', 'REFINING', 1.8, 1.2, 0.0, 2.0, 'Industry Standard', '2024-01-01'),
('olein_yield', 'FRACTIONATION', 75.0, 80.0, 60.0, 85.0, 'Industry Standard', '2024-01-01'),
('stearin_yield', 'FRACTIONATION', 22.0, 25.0, 15.0, 30.0, 'Industry Standard', '2024-01-01'),
('iodine_value_consistency', 'FRACTIONATION', 0.5, 0.2, 0.0, 1.0, 'Industry Standard', '2024-01-01'),

-- Manufacturer benchmarks
('recipe_adherence_variance', 'BLENDING', 0.3, 0.1, 0.0, 0.5, 'Industry Standard', '2024-01-01'),
('production_line_efficiency', 'MANUFACTURING', 95.0, 98.0, 80.0, 100.0, 'Industry Standard', '2024-01-01'),
('product_waste_scrap_rate', 'MANUFACTURING', 1.2, 0.5, 0.0, 2.0, 'Industry Standard', '2024-01-01');

-- 11. Add comments for documentation
COMMENT ON TABLE transformation_metrics IS 'Stores detailed metrics for transformation events with industry benchmarking';
COMMENT ON TABLE industry_benchmarks IS 'Industry benchmark data for performance comparison';
COMMENT ON TABLE kpi_summaries IS 'KPI summaries and performance scores for reporting';
COMMENT ON TABLE performance_trends IS 'Performance trend analysis over time';

COMMENT ON FUNCTION calculate_performance_scores IS 'Calculates efficiency, quality, sustainability, and overall performance scores';
COMMENT ON FUNCTION generate_performance_alerts IS 'Generates performance alerts based on metric thresholds and targets';

-- 12. Log the migration
INSERT INTO system_events (event_type, event_data, created_at) 
VALUES (
    'MIGRATION_EXECUTED',
    '{"version": "V031", "description": "Transformation metrics enhancement", "tables_affected": ["transformation_metrics", "industry_benchmarks", "kpi_summaries", "performance_trends"], "functions_created": ["calculate_performance_scores", "generate_performance_alerts"]}',
    CURRENT_TIMESTAMP
);

-- Description: Create logging and monitoring tables
-- Version: 004
-- Created: 2024-01-01

-- Create application_logs table for centralized logging
CREATE TABLE IF NOT EXISTS application_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    level VARCHAR(20) NOT NULL CHECK (level IN ('debug', 'info', 'warning', 'error', 'critical')),
    message TEXT NOT NULL,
    logger_name VARCHAR(255) NOT NULL,
    module VARCHAR(255) NOT NULL,
    function VARCHAR(255) NOT NULL,
    line_number INTEGER NOT NULL,
    request_id VARCHAR(255),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    company_id UUID REFERENCES companies(id) ON DELETE SET NULL,
    session_id VARCHAR(255),
    ip_address INET,
    user_agent TEXT,
    extra_data JSONB DEFAULT '{}'
);

-- Create indexes on application_logs table
CREATE INDEX IF NOT EXISTS idx_app_logs_timestamp ON application_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_app_logs_level ON application_logs(level);
CREATE INDEX IF NOT EXISTS idx_app_logs_module ON application_logs(module);
CREATE INDEX IF NOT EXISTS idx_app_logs_request_id ON application_logs(request_id);
CREATE INDEX IF NOT EXISTS idx_app_logs_user_id ON application_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_app_logs_company_id ON application_logs(company_id);
CREATE INDEX IF NOT EXISTS idx_app_logs_level_timestamp ON application_logs(level, timestamp);
CREATE INDEX IF NOT EXISTS idx_app_logs_module_timestamp ON application_logs(module, timestamp);
CREATE INDEX IF NOT EXISTS idx_app_logs_user_timestamp ON application_logs(user_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_app_logs_company_timestamp ON application_logs(company_id, timestamp);

-- Create error_events table for error tracking and alerting
CREATE TABLE IF NOT EXISTS error_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    error_id VARCHAR(255) UNIQUE NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    error_type VARCHAR(255) NOT NULL,
    error_message TEXT NOT NULL,
    stack_trace TEXT,
    module VARCHAR(255) NOT NULL,
    function VARCHAR(255) NOT NULL,
    line_number INTEGER NOT NULL,
    request_id VARCHAR(255),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    company_id UUID REFERENCES companies(id) ON DELETE SET NULL,
    context JSONB DEFAULT '{}',
    fingerprint VARCHAR(32) NOT NULL,
    count INTEGER DEFAULT 1,
    first_seen TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    resolved BOOLEAN DEFAULT FALSE,
    resolved_at TIMESTAMP WITH TIME ZONE,
    resolved_by UUID REFERENCES users(id) ON DELETE SET NULL
);

-- Create indexes on error_events table
CREATE INDEX IF NOT EXISTS idx_error_events_timestamp ON error_events(timestamp);
CREATE INDEX IF NOT EXISTS idx_error_events_severity ON error_events(severity);
CREATE INDEX IF NOT EXISTS idx_error_events_error_type ON error_events(error_type);
CREATE INDEX IF NOT EXISTS idx_error_events_module ON error_events(module);
CREATE INDEX IF NOT EXISTS idx_error_events_fingerprint ON error_events(fingerprint);
CREATE INDEX IF NOT EXISTS idx_error_events_resolved ON error_events(resolved);
CREATE INDEX IF NOT EXISTS idx_error_events_user_id ON error_events(user_id);
CREATE INDEX IF NOT EXISTS idx_error_events_company_id ON error_events(company_id);
CREATE INDEX IF NOT EXISTS idx_error_events_severity_timestamp ON error_events(severity, timestamp);
CREATE INDEX IF NOT EXISTS idx_error_events_unresolved ON error_events(resolved, timestamp) WHERE resolved = FALSE;

-- Create performance_metrics table for application performance tracking
CREATE TABLE IF NOT EXISTS performance_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    metric_type VARCHAR(50) NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    value DECIMAL(15,6) NOT NULL,
    unit VARCHAR(20),
    tags JSONB DEFAULT '{}',
    request_id VARCHAR(255),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    company_id UUID REFERENCES companies(id) ON DELETE SET NULL
);

-- Create indexes on performance_metrics table
CREATE INDEX IF NOT EXISTS idx_perf_metrics_timestamp ON performance_metrics(timestamp);
CREATE INDEX IF NOT EXISTS idx_perf_metrics_type ON performance_metrics(metric_type);
CREATE INDEX IF NOT EXISTS idx_perf_metrics_name ON performance_metrics(metric_name);
CREATE INDEX IF NOT EXISTS idx_perf_metrics_type_name ON performance_metrics(metric_type, metric_name);
CREATE INDEX IF NOT EXISTS idx_perf_metrics_type_timestamp ON performance_metrics(metric_type, timestamp);
CREATE INDEX IF NOT EXISTS idx_perf_metrics_request_id ON performance_metrics(request_id);

-- Create health_check_results table for monitoring
CREATE TABLE IF NOT EXISTS health_check_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    service_name VARCHAR(100) NOT NULL,
    status VARCHAR(20) NOT NULL CHECK (status IN ('healthy', 'degraded', 'unhealthy', 'unknown')),
    response_time DECIMAL(8,3) NOT NULL,
    message TEXT,
    details JSONB DEFAULT '{}',
    environment VARCHAR(50) DEFAULT 'production'
);

-- Create indexes on health_check_results table
CREATE INDEX IF NOT EXISTS idx_health_check_timestamp ON health_check_results(timestamp);
CREATE INDEX IF NOT EXISTS idx_health_check_service ON health_check_results(service_name);
CREATE INDEX IF NOT EXISTS idx_health_check_status ON health_check_results(status);
CREATE INDEX IF NOT EXISTS idx_health_check_environment ON health_check_results(environment);
CREATE INDEX IF NOT EXISTS idx_health_check_service_timestamp ON health_check_results(service_name, timestamp);
CREATE INDEX IF NOT EXISTS idx_health_check_service_status ON health_check_results(service_name, status);

-- Create deployment_logs table for deployment tracking
CREATE TABLE IF NOT EXISTS deployment_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    deployment_id VARCHAR(255) UNIQUE NOT NULL,
    environment VARCHAR(50) NOT NULL,
    version VARCHAR(100) NOT NULL,
    image_tag VARCHAR(255),
    status VARCHAR(20) NOT NULL CHECK (status IN ('started', 'in_progress', 'completed', 'failed', 'rolled_back')),
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    deployed_by VARCHAR(255),
    deployment_notes TEXT,
    rollback_reason TEXT,
    health_check_passed BOOLEAN,
    smoke_tests_passed BOOLEAN,
    migration_applied BOOLEAN DEFAULT FALSE,
    previous_version VARCHAR(100),
    deployment_duration INTEGER, -- seconds
    metadata JSONB DEFAULT '{}'
);

-- Create indexes on deployment_logs table
CREATE INDEX IF NOT EXISTS idx_deployment_logs_environment ON deployment_logs(environment);
CREATE INDEX IF NOT EXISTS idx_deployment_logs_status ON deployment_logs(status);
CREATE INDEX IF NOT EXISTS idx_deployment_logs_started_at ON deployment_logs(started_at);
CREATE INDEX IF NOT EXISTS idx_deployment_logs_version ON deployment_logs(version);
CREATE INDEX IF NOT EXISTS idx_deployment_logs_env_status ON deployment_logs(environment, status);
CREATE INDEX IF NOT EXISTS idx_deployment_logs_env_started ON deployment_logs(environment, started_at);

-- Create alert_rules table for monitoring alerts
CREATE TABLE IF NOT EXISTS alert_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    metric_type VARCHAR(50) NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    condition_operator VARCHAR(10) NOT NULL CHECK (condition_operator IN ('>', '<', '>=', '<=', '=', '!=')),
    threshold_value DECIMAL(15,6) NOT NULL,
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    enabled BOOLEAN DEFAULT TRUE,
    notification_channels JSONB DEFAULT '[]', -- Array of notification channels
    cooldown_minutes INTEGER DEFAULT 15,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES users(id) ON DELETE SET NULL
);

-- Create indexes on alert_rules table
CREATE INDEX IF NOT EXISTS idx_alert_rules_enabled ON alert_rules(enabled);
CREATE INDEX IF NOT EXISTS idx_alert_rules_metric_type ON alert_rules(metric_type);
CREATE INDEX IF NOT EXISTS idx_alert_rules_severity ON alert_rules(severity);
CREATE INDEX IF NOT EXISTS idx_alert_rules_metric_enabled ON alert_rules(metric_type, enabled);

-- Create alert_incidents table for tracking fired alerts
CREATE TABLE IF NOT EXISTS alert_incidents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    alert_rule_id UUID NOT NULL REFERENCES alert_rules(id) ON DELETE CASCADE,
    triggered_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'resolved', 'suppressed')),
    trigger_value DECIMAL(15,6) NOT NULL,
    message TEXT,
    notification_sent BOOLEAN DEFAULT FALSE,
    resolved_by UUID REFERENCES users(id) ON DELETE SET NULL,
    resolution_notes TEXT,
    metadata JSONB DEFAULT '{}'
);

-- Create indexes on alert_incidents table
CREATE INDEX IF NOT EXISTS idx_alert_incidents_rule_id ON alert_incidents(alert_rule_id);
CREATE INDEX IF NOT EXISTS idx_alert_incidents_triggered_at ON alert_incidents(triggered_at);
CREATE INDEX IF NOT EXISTS idx_alert_incidents_status ON alert_incidents(status);
CREATE INDEX IF NOT EXISTS idx_alert_incidents_active ON alert_incidents(status, triggered_at) WHERE status = 'active';
CREATE INDEX IF NOT EXISTS idx_alert_incidents_rule_status ON alert_incidents(alert_rule_id, status);

-- Add triggers for updated_at
CREATE TRIGGER update_alert_rules_updated_at BEFORE UPDATE ON alert_rules
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create function for log retention cleanup
CREATE OR REPLACE FUNCTION cleanup_monitoring_data()
RETURNS void AS $$
BEGIN
    -- Clean up old application logs (keep 3 months)
    DELETE FROM application_logs 
    WHERE timestamp < CURRENT_TIMESTAMP - INTERVAL '3 months';
    
    -- Clean up old performance metrics (keep 1 month)
    DELETE FROM performance_metrics 
    WHERE timestamp < CURRENT_TIMESTAMP - INTERVAL '1 month';
    
    -- Clean up old health check results (keep 2 weeks)
    DELETE FROM health_check_results 
    WHERE timestamp < CURRENT_TIMESTAMP - INTERVAL '2 weeks';
    
    -- Clean up resolved error events (keep 6 months)
    DELETE FROM error_events 
    WHERE resolved = TRUE 
    AND resolved_at < CURRENT_TIMESTAMP - INTERVAL '6 months';
    
    -- Clean up old deployment logs (keep 1 year)
    DELETE FROM deployment_logs 
    WHERE started_at < CURRENT_TIMESTAMP - INTERVAL '1 year';
    
    -- Clean up resolved alert incidents (keep 3 months)
    DELETE FROM alert_incidents 
    WHERE status = 'resolved' 
    AND resolved_at < CURRENT_TIMESTAMP - INTERVAL '3 months';
    
END;
$$ LANGUAGE plpgsql;

-- Create indexes for cleanup performance
CREATE INDEX IF NOT EXISTS idx_app_logs_cleanup ON application_logs(timestamp) WHERE timestamp < CURRENT_TIMESTAMP - INTERVAL '2 months';
CREATE INDEX IF NOT EXISTS idx_perf_metrics_cleanup ON performance_metrics(timestamp) WHERE timestamp < CURRENT_TIMESTAMP - INTERVAL '3 weeks';
CREATE INDEX IF NOT EXISTS idx_health_check_cleanup ON health_check_results(timestamp) WHERE timestamp < CURRENT_TIMESTAMP - INTERVAL '10 days';
CREATE INDEX IF NOT EXISTS idx_error_events_cleanup ON error_events(resolved, resolved_at) WHERE resolved = TRUE;
CREATE INDEX IF NOT EXISTS idx_deployment_logs_cleanup ON deployment_logs(started_at) WHERE started_at < CURRENT_TIMESTAMP - INTERVAL '11 months';
CREATE INDEX IF NOT EXISTS idx_alert_incidents_cleanup ON alert_incidents(status, resolved_at) WHERE status = 'resolved';

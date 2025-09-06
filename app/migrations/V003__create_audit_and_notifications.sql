-- Description: Create audit logging and notification tables
-- Version: 003
-- Created: 2024-01-01

-- Create audit_events table
CREATE TABLE IF NOT EXISTS audit_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type VARCHAR(50) NOT NULL,
    resource_type VARCHAR(50) NOT NULL,
    resource_id UUID NOT NULL,
    actor_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    actor_company_id UUID REFERENCES companies(id) ON DELETE SET NULL,
    changes JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes on audit_events table
CREATE INDEX IF NOT EXISTS idx_ae_event_type ON audit_events(event_type);
CREATE INDEX IF NOT EXISTS idx_ae_resource_type ON audit_events(resource_type);
CREATE INDEX IF NOT EXISTS idx_ae_resource_id ON audit_events(resource_id);
CREATE INDEX IF NOT EXISTS idx_ae_actor_user ON audit_events(actor_user_id);
CREATE INDEX IF NOT EXISTS idx_ae_actor_company ON audit_events(actor_company_id);
CREATE INDEX IF NOT EXISTS idx_ae_created_at ON audit_events(created_at);
CREATE INDEX IF NOT EXISTS idx_ae_resource_type_id ON audit_events(resource_type, resource_id);
CREATE INDEX IF NOT EXISTS idx_ae_event_resource ON audit_events(event_type, resource_type);
CREATE INDEX IF NOT EXISTS idx_ae_company_created ON audit_events(actor_company_id, created_at);

-- Create notifications table
CREATE TABLE IF NOT EXISTS notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    recipient_user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    recipient_company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    notification_type VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    data JSONB DEFAULT '{}',
    channels JSONB DEFAULT '["in_app"]', -- Array of delivery channels
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'sent', 'delivered', 'failed', 'read')),
    priority VARCHAR(10) NOT NULL DEFAULT 'normal' CHECK (priority IN ('low', 'normal', 'high', 'urgent')),
    read_at TIMESTAMP WITH TIME ZONE,
    sent_at TIMESTAMP WITH TIME ZONE,
    delivered_at TIMESTAMP WITH TIME ZONE,
    failed_at TIMESTAMP WITH TIME ZONE,
    failure_reason TEXT,
    retry_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT notification_recipient CHECK (
        (recipient_user_id IS NOT NULL AND recipient_company_id IS NULL) OR
        (recipient_user_id IS NULL AND recipient_company_id IS NOT NULL)
    )
);

-- Create indexes on notifications table
CREATE INDEX IF NOT EXISTS idx_notif_recipient_user ON notifications(recipient_user_id);
CREATE INDEX IF NOT EXISTS idx_notif_recipient_company ON notifications(recipient_company_id);
CREATE INDEX IF NOT EXISTS idx_notif_type ON notifications(notification_type);
CREATE INDEX IF NOT EXISTS idx_notif_status ON notifications(status);
CREATE INDEX IF NOT EXISTS idx_notif_priority ON notifications(priority);
CREATE INDEX IF NOT EXISTS idx_notif_created_at ON notifications(created_at);
CREATE INDEX IF NOT EXISTS idx_notif_read_at ON notifications(read_at);
CREATE INDEX IF NOT EXISTS idx_notif_user_status ON notifications(recipient_user_id, status);
CREATE INDEX IF NOT EXISTS idx_notif_user_unread ON notifications(recipient_user_id, read_at) WHERE read_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_notif_company_status ON notifications(recipient_company_id, status);
CREATE INDEX IF NOT EXISTS idx_notif_pending_retry ON notifications(status, retry_count) WHERE status = 'failed';

-- Create background_jobs table for tracking async tasks
CREATE TABLE IF NOT EXISTS background_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_type VARCHAR(50) NOT NULL,
    job_id VARCHAR(255) UNIQUE NOT NULL, -- Celery task ID
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed', 'retrying')),
    priority INTEGER DEFAULT 0,
    parameters JSONB DEFAULT '{}',
    result JSONB DEFAULT '{}',
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes on background_jobs table
CREATE INDEX IF NOT EXISTS idx_bj_job_type ON background_jobs(job_type);
CREATE INDEX IF NOT EXISTS idx_bj_job_id ON background_jobs(job_id);
CREATE INDEX IF NOT EXISTS idx_bj_status ON background_jobs(status);
CREATE INDEX IF NOT EXISTS idx_bj_priority ON background_jobs(priority);
CREATE INDEX IF NOT EXISTS idx_bj_created_at ON background_jobs(created_at);
CREATE INDEX IF NOT EXISTS idx_bj_status_priority ON background_jobs(status, priority);
CREATE INDEX IF NOT EXISTS idx_bj_type_status ON background_jobs(job_type, status);
CREATE INDEX IF NOT EXISTS idx_bj_retry_count ON background_jobs(retry_count, max_retries);

-- Create system_metrics table for monitoring
CREATE TABLE IF NOT EXISTS system_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    metric_type VARCHAR(50) NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    value DECIMAL(15,6) NOT NULL,
    unit VARCHAR(20),
    tags JSONB DEFAULT '{}',
    collected_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes on system_metrics table
CREATE INDEX IF NOT EXISTS idx_sm_metric_type ON system_metrics(metric_type);
CREATE INDEX IF NOT EXISTS idx_sm_metric_name ON system_metrics(metric_name);
CREATE INDEX IF NOT EXISTS idx_sm_collected_at ON system_metrics(collected_at);
CREATE INDEX IF NOT EXISTS idx_sm_type_name ON system_metrics(metric_type, metric_name);
CREATE INDEX IF NOT EXISTS idx_sm_type_collected ON system_metrics(metric_type, collected_at);

-- Create user_sessions table for session tracking
CREATE TABLE IF NOT EXISTS user_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    ip_address INET,
    user_agent TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL
);

-- Create indexes on user_sessions table
CREATE INDEX IF NOT EXISTS idx_us_user_id ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_us_session_token ON user_sessions(session_token);
CREATE INDEX IF NOT EXISTS idx_us_is_active ON user_sessions(is_active);
CREATE INDEX IF NOT EXISTS idx_us_last_activity ON user_sessions(last_activity);
CREATE INDEX IF NOT EXISTS idx_us_expires_at ON user_sessions(expires_at);
CREATE INDEX IF NOT EXISTS idx_us_user_active ON user_sessions(user_id, is_active);

-- Create api_rate_limits table for rate limiting
CREATE TABLE IF NOT EXISTS api_rate_limits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    identifier VARCHAR(255) NOT NULL, -- IP address or user ID
    endpoint VARCHAR(255) NOT NULL,
    request_count INTEGER DEFAULT 1,
    window_start TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    window_end TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT unique_rate_limit UNIQUE (identifier, endpoint, window_start)
);

-- Create indexes on api_rate_limits table
CREATE INDEX IF NOT EXISTS idx_arl_identifier ON api_rate_limits(identifier);
CREATE INDEX IF NOT EXISTS idx_arl_endpoint ON api_rate_limits(endpoint);
CREATE INDEX IF NOT EXISTS idx_arl_window_end ON api_rate_limits(window_end);
CREATE INDEX IF NOT EXISTS idx_arl_identifier_endpoint ON api_rate_limits(identifier, endpoint);

-- Add triggers for updated_at
CREATE TRIGGER update_background_jobs_updated_at BEFORE UPDATE ON background_jobs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create function to clean up old records
CREATE OR REPLACE FUNCTION cleanup_old_records()
RETURNS void AS $$
BEGIN
    -- Clean up old audit events (keep 1 year)
    DELETE FROM audit_events 
    WHERE created_at < CURRENT_TIMESTAMP - INTERVAL '1 year';
    
    -- Clean up old notifications (keep 6 months)
    DELETE FROM notifications 
    WHERE created_at < CURRENT_TIMESTAMP - INTERVAL '6 months'
    AND status IN ('delivered', 'read', 'failed');
    
    -- Clean up old background jobs (keep 1 month)
    DELETE FROM background_jobs 
    WHERE created_at < CURRENT_TIMESTAMP - INTERVAL '1 month'
    AND status IN ('completed', 'failed');
    
    -- Clean up old system metrics (keep 3 months)
    DELETE FROM system_metrics 
    WHERE collected_at < CURRENT_TIMESTAMP - INTERVAL '3 months';
    
    -- Clean up expired user sessions
    DELETE FROM user_sessions 
    WHERE expires_at < CURRENT_TIMESTAMP;
    
    -- Clean up old rate limit records (keep 1 day)
    DELETE FROM api_rate_limits 
    WHERE window_end < CURRENT_TIMESTAMP - INTERVAL '1 day';
    
END;
$$ LANGUAGE plpgsql;

-- Create indexes for performance optimization
CREATE INDEX IF NOT EXISTS idx_audit_events_cleanup ON audit_events(created_at) WHERE created_at < CURRENT_TIMESTAMP - INTERVAL '11 months';
CREATE INDEX IF NOT EXISTS idx_notifications_cleanup ON notifications(created_at, status) WHERE created_at < CURRENT_TIMESTAMP - INTERVAL '5 months';
CREATE INDEX IF NOT EXISTS idx_background_jobs_cleanup ON background_jobs(created_at, status) WHERE created_at < CURRENT_TIMESTAMP - INTERVAL '3 weeks';
CREATE INDEX IF NOT EXISTS idx_system_metrics_cleanup ON system_metrics(collected_at) WHERE collected_at < CURRENT_TIMESTAMP - INTERVAL '2 months';

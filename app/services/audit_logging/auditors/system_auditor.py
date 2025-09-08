"""
System specific audit functionality.
"""
from typing import List, Optional, Dict, Any
from uuid import UUID

from .base_auditor import BaseAuditor
from ..domain.models import AuditContext, AuditEventData, ComplianceContext
from ..domain.enums import AuditDomain, EntityType, AuditEventCategory, ComplianceFramework, AuditSeverityLevel


class SystemAuditor(BaseAuditor):
    """
    Auditor for System domain events.
    
    Handles audit logging for system startup, shutdown, errors, and configuration changes.
    """
    
    @property
    def domain(self) -> AuditDomain:
        return AuditDomain.SYSTEM
    
    @property
    def supported_entity_types(self) -> List[EntityType]:
        return [EntityType.SYSTEM]
    
    def log_system_startup(
        self,
        service_name: str,
        version: str,
        startup_time_seconds: float,
        configuration: Optional[Dict[str, Any]] = None
    ):
        """Log system startup event."""
        system_id = UUID('00000000-0000-0000-0000-000000000000')  # Virtual system entity
        
        context = AuditContext(
            domain=self.domain,
            category=AuditEventCategory.SYSTEM_STARTUP,
            entity_type=EntityType.SYSTEM,
            entity_id=system_id
        )
        
        event_data = AuditEventData(
            event_type="system_startup",
            action="service_started",
            description=f"System service {service_name} started successfully",
            severity=AuditSeverityLevel.LOW
        )
        
        event_data.add_metadata("service_name", service_name)
        event_data.add_metadata("version", version)
        event_data.add_metadata("startup_time_seconds", startup_time_seconds)
        
        if configuration:
            # Don't log sensitive configuration values
            safe_config = {k: v for k, v in configuration.items() 
                          if not any(sensitive in k.lower() for sensitive in ['password', 'secret', 'key', 'token'])}
            event_data.add_metadata("configuration", safe_config)
        
        event_data.add_tag("system_startup")
        event_data.add_tag(f"service:{service_name}")
        
        return self.log_event(context, event_data)
    
    def log_system_shutdown(
        self,
        service_name: str,
        shutdown_reason: str,
        graceful: bool,
        uptime_seconds: Optional[float] = None
    ):
        """Log system shutdown event."""
        system_id = UUID('00000000-0000-0000-0000-000000000000')  # Virtual system entity
        
        context = AuditContext(
            domain=self.domain,
            category=AuditEventCategory.SYSTEM_SHUTDOWN,
            entity_type=EntityType.SYSTEM,
            entity_id=system_id
        )
        
        severity = AuditSeverityLevel.LOW if graceful else AuditSeverityLevel.HIGH
        
        event_data = AuditEventData(
            event_type="system_shutdown",
            action="service_stopped",
            description=f"System service {service_name} {'gracefully' if graceful else 'unexpectedly'} shutdown",
            severity=severity
        )
        
        event_data.add_metadata("service_name", service_name)
        event_data.add_metadata("shutdown_reason", shutdown_reason)
        event_data.add_metadata("graceful", graceful)
        
        if uptime_seconds:
            event_data.add_metadata("uptime_seconds", uptime_seconds)
        
        event_data.add_tag("system_shutdown")
        event_data.add_tag(f"service:{service_name}")
        
        if not graceful:
            event_data.add_tag("unexpected_shutdown")
        
        return self.log_event(context, event_data)
    
    def log_system_error(
        self,
        service_name: str,
        error_type: str,
        error_message: str,
        error_details: Optional[Dict[str, Any]] = None,
        severity: AuditSeverityLevel = AuditSeverityLevel.MEDIUM
    ):
        """Log system error event."""
        system_id = UUID('00000000-0000-0000-0000-000000000000')  # Virtual system entity
        
        context = AuditContext(
            domain=self.domain,
            category=AuditEventCategory.SYSTEM_ERROR,
            entity_type=EntityType.SYSTEM,
            entity_id=system_id
        )
        
        event_data = AuditEventData(
            event_type="system_error",
            action="error_occurred",
            description=f"System error in {service_name}: {error_message}",
            severity=severity
        )
        
        event_data.add_metadata("service_name", service_name)
        event_data.add_metadata("error_type", error_type)
        event_data.add_metadata("error_message", error_message)
        
        if error_details:
            event_data.add_metadata("error_details", error_details)
        
        event_data.add_tag("system_error")
        event_data.add_tag(f"service:{service_name}")
        event_data.add_tag(f"error_type:{error_type}")
        
        # Critical errors may require compliance attention
        compliance_context = None
        if severity == AuditSeverityLevel.CRITICAL:
            compliance_context = ComplianceContext()
            compliance_context.add_framework(ComplianceFramework.ISO_27001)
        
        return self.log_event(context, event_data, compliance_context)
    
    def log_configuration_change(
        self,
        service_name: str,
        config_section: str,
        old_config: Dict[str, Any],
        new_config: Dict[str, Any],
        changed_by_user_id: Optional[UUID] = None,
        request_context: Optional[Dict[str, Any]] = None
    ):
        """Log system configuration change."""
        system_id = UUID('00000000-0000-0000-0000-000000000000')  # Virtual system entity
        
        context = AuditContext(
            domain=self.domain,
            category=AuditEventCategory.SYSTEM_CONFIGURATION,
            entity_type=EntityType.SYSTEM,
            entity_id=system_id,
            actor_user_id=changed_by_user_id
        )
        
        if request_context:
            context.ip_address = request_context.get('ip_address')
            context.user_agent = request_context.get('user_agent')
            context.session_id = request_context.get('session_id')
        
        # Filter out sensitive configuration values
        def filter_sensitive(config_dict):
            return {k: '***REDACTED***' if any(sensitive in k.lower() for sensitive in ['password', 'secret', 'key', 'token']) 
                   else v for k, v in config_dict.items()}
        
        safe_old_config = filter_sensitive(old_config)
        safe_new_config = filter_sensitive(new_config)
        
        event_data = AuditEventData(
            event_type="configuration_changed",
            action="config_update",
            description=f"System configuration changed: {config_section}",
            severity=AuditSeverityLevel.MEDIUM,
            old_values=safe_old_config,
            new_values=safe_new_config
        )
        
        event_data.add_metadata("service_name", service_name)
        event_data.add_metadata("config_section", config_section)
        event_data.add_tag("configuration_change")
        event_data.add_tag(f"service:{service_name}")
        event_data.add_tag(f"config_section:{config_section}")
        
        # Configuration changes may have compliance implications
        compliance_context = ComplianceContext()
        compliance_context.add_framework(ComplianceFramework.ISO_27001)
        
        # Security-related configuration changes require special attention
        security_sections = {'security', 'authentication', 'authorization', 'encryption', 'ssl', 'tls'}
        if config_section.lower() in security_sections:
            event_data.add_tag("security_config")
            compliance_context.requires_approval = True
            compliance_context.sensitive_data = True
        
        return self.log_event(context, event_data, compliance_context)
    
    def log_database_migration(
        self,
        migration_name: str,
        migration_version: str,
        success: bool,
        duration_seconds: float,
        migration_details: Optional[Dict[str, Any]] = None
    ):
        """Log database migration event."""
        system_id = UUID('00000000-0000-0000-0000-000000000000')  # Virtual system entity
        
        context = AuditContext(
            domain=self.domain,
            category=AuditEventCategory.SYSTEM_CONFIGURATION,
            entity_type=EntityType.SYSTEM,
            entity_id=system_id
        )
        
        severity = AuditSeverityLevel.MEDIUM if success else AuditSeverityLevel.HIGH
        
        event_data = AuditEventData(
            event_type="database_migration",
            action="migration_executed",
            description=f"Database migration {migration_name} {'completed' if success else 'failed'}",
            severity=severity
        )
        
        event_data.add_metadata("migration_name", migration_name)
        event_data.add_metadata("migration_version", migration_version)
        event_data.add_metadata("success", success)
        event_data.add_metadata("duration_seconds", duration_seconds)
        
        if migration_details:
            event_data.add_metadata("migration_details", migration_details)
        
        event_data.add_tag("database_migration")
        event_data.add_tag("schema_change")
        
        if success:
            event_data.add_tag("migration_success")
        else:
            event_data.add_tag("migration_failure")
        
        # Database migrations are significant system changes
        compliance_context = ComplianceContext()
        compliance_context.add_framework(ComplianceFramework.SOX)
        
        return self.log_event(context, event_data, compliance_context)
    
    def log_backup_operation(
        self,
        backup_type: str,
        backup_target: str,
        success: bool,
        backup_size_bytes: Optional[int] = None,
        duration_seconds: Optional[float] = None
    ):
        """Log backup operation event."""
        system_id = UUID('00000000-0000-0000-0000-000000000000')  # Virtual system entity
        
        context = AuditContext(
            domain=self.domain,
            category=AuditEventCategory.SYSTEM_CONFIGURATION,
            entity_type=EntityType.SYSTEM,
            entity_id=system_id
        )
        
        severity = AuditSeverityLevel.LOW if success else AuditSeverityLevel.HIGH
        
        event_data = AuditEventData(
            event_type="backup_operation",
            action="backup_executed",
            description=f"Backup operation {backup_type} {'completed' if success else 'failed'}",
            severity=severity
        )
        
        event_data.add_metadata("backup_type", backup_type)
        event_data.add_metadata("backup_target", backup_target)
        event_data.add_metadata("success", success)
        
        if backup_size_bytes:
            event_data.add_metadata("backup_size_bytes", backup_size_bytes)
        
        if duration_seconds:
            event_data.add_metadata("duration_seconds", duration_seconds)
        
        event_data.add_tag("backup_operation")
        event_data.add_tag(f"backup_type:{backup_type}")
        
        if success:
            event_data.add_tag("backup_success")
        else:
            event_data.add_tag("backup_failure")
        
        return self.log_event(context, event_data)
    
    def _get_entity(self, entity_type: EntityType, entity_id: UUID):
        """System entities are virtual, return None."""
        return None
    
    def _enrich_event_data(self, context: AuditContext, event_data: AuditEventData) -> AuditEventData:
        """Enrich system audit events with additional context."""
        # Call parent enrichment first
        event_data = super()._enrich_event_data(context, event_data)
        
        # Add system-specific enrichment
        event_data.add_tag("system_domain")
        
        # Add environment information if available
        import os
        environment = os.getenv('ENVIRONMENT', 'unknown')
        event_data.add_metadata("environment", environment)
        
        return event_data

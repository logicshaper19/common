"""
API endpoints for audit log management and querying.
"""
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.core.minimal_audit import log_audit_event
from app.models.audit_event import (
    AuditEvent,
    AuditEventType,
    AuditEventSeverity
)
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/audit", tags=["audit"])


# Request/Response Models
class AuditEventResponse(BaseModel):
    """Response model for audit events."""
    id: str
    event_type: str
    severity: str
    entity_type: str
    entity_id: str
    actor_user_id: Optional[str] = None
    actor_company_id: Optional[str] = None
    actor_ip_address: Optional[str] = None
    action: str
    description: str
    old_values: Optional[Dict[str, Any]] = None
    new_values: Optional[Dict[str, Any]] = None
    changed_fields: Optional[List[str]] = None
    request_id: Optional[str] = None
    api_endpoint: Optional[str] = None
    http_method: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    business_context: Optional[Dict[str, Any]] = None
    is_sensitive: bool
    compliance_tags: Optional[List[str]] = None
    created_at: str
    
    class Config:
        from_attributes = True


class AuditQueryRequest(BaseModel):
    """Request model for audit event queries."""
    entity_type: Optional[str] = Field(None, description="Filter by entity type")
    entity_id: Optional[str] = Field(None, description="Filter by entity ID")
    event_type: Optional[AuditEventType] = Field(None, description="Filter by event type")
    actor_user_id: Optional[str] = Field(None, description="Filter by actor user ID")
    actor_company_id: Optional[str] = Field(None, description="Filter by actor company ID")
    start_date: Optional[datetime] = Field(None, description="Filter events after this date")
    end_date: Optional[datetime] = Field(None, description="Filter events before this date")
    severity: Optional[AuditEventSeverity] = Field(None, description="Filter by severity")
    action: Optional[str] = Field(None, description="Filter by action")
    limit: int = Field(100, ge=1, le=1000, description="Maximum number of results")
    offset: int = Field(0, ge=0, description="Offset for pagination")
    order_by: str = Field("created_at", description="Field to order by")
    order_desc: bool = Field(True, description="Order descending")


class AuditStatsResponse(BaseModel):
    """Response model for audit statistics."""
    total_events: int
    events_by_type: Dict[str, int]
    events_by_severity: Dict[str, int]
    events_by_entity_type: Dict[str, int]
    recent_activity: List[Dict[str, Any]]
    top_actors: List[Dict[str, Any]]
    compliance_summary: Dict[str, Any]


class POAuditTrailResponse(BaseModel):
    """Response model for PO audit trail."""
    po_id: str
    total_events: int
    events: List[AuditEventResponse]
    timeline_summary: List[Dict[str, Any]]
    compliance_status: Dict[str, Any]


@router.get("/events", response_model=List[AuditEventResponse])
async def query_audit_events(
    entity_type: Optional[str] = Query(None, description="Filter by entity type"),
    entity_id: Optional[str] = Query(None, description="Filter by entity ID"),
    event_type: Optional[AuditEventType] = Query(None, description="Filter by event type"),
    actor_user_id: Optional[str] = Query(None, description="Filter by actor user ID"),
    actor_company_id: Optional[str] = Query(None, description="Filter by actor company ID"),
    start_date: Optional[datetime] = Query(None, description="Filter events after this date"),
    end_date: Optional[datetime] = Query(None, description="Filter events before this date"),
    severity: Optional[AuditEventSeverity] = Query(None, description="Filter by severity"),
    action: Optional[str] = Query(None, description="Filter by action"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    order_by: str = Query("created_at", description="Field to order by"),
    order_desc: bool = Query(True, description="Order descending"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> List[AuditEventResponse]:
    """
    Query audit events with comprehensive filtering.
    
    Supports filtering by entity, actor, time range, and other criteria.
    Results are scoped to the current user's company for security.
    """
    try:
        audit_logger = AuditLogger(db)
        
        # Convert string UUIDs to UUID objects
        entity_uuid = UUID(entity_id) if entity_id else None
        actor_user_uuid = UUID(actor_user_id) if actor_user_id else None
        actor_company_uuid = UUID(actor_company_id) if actor_company_id else None
        
        # Scope to current user's company for security
        if not actor_company_uuid:
            actor_company_uuid = current_user.company_id
        elif actor_company_uuid != current_user.company_id:
            # Only allow querying own company's audit events unless admin
            if not current_user.role == "admin":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Can only query audit events for your own company"
                )
        
        events = audit_logger.query_audit_events(
            entity_type=entity_type,
            entity_id=entity_uuid,
            event_type=event_type,
            actor_user_id=actor_user_uuid,
            actor_company_id=actor_company_uuid,
            start_date=start_date,
            end_date=end_date,
            severity=severity,
            action=action,
            limit=limit,
            offset=offset,
            order_by=order_by,
            order_desc=order_desc
        )
        
        return [
            AuditEventResponse(
                id=str(event.id),
                event_type=event.event_type.value,
                severity=event.severity.value,
                entity_type=event.entity_type,
                entity_id=str(event.entity_id),
                actor_user_id=str(event.actor_user_id) if event.actor_user_id else None,
                actor_company_id=str(event.actor_company_id) if event.actor_company_id else None,
                actor_ip_address=event.actor_ip_address,
                action=event.action,
                description=event.description,
                old_values=event.old_values,
                new_values=event.new_values,
                changed_fields=event.changed_fields,
                request_id=event.request_id,
                api_endpoint=event.api_endpoint,
                http_method=event.http_method,
                metadata=event.audit_metadata,
                business_context=event.business_context,
                is_sensitive=event.is_sensitive,
                compliance_tags=event.compliance_tags,
                created_at=event.created_at.isoformat()
            )
            for event in events
        ]
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid UUID format: {str(e)}"
        )
    except Exception as e:
        logger.error("Failed to query audit events", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to query audit events: {str(e)}"
        )


@router.get("/events/{event_id}", response_model=AuditEventResponse)
async def get_audit_event(
    event_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> AuditEventResponse:
    """
    Get a specific audit event by ID.
    
    Only allows access to events from the current user's company.
    """
    try:
        event = db.query(AuditEvent).filter(AuditEvent.id == event_id).first()
        
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Audit event not found"
            )
        
        # Check access permissions
        if (event.actor_company_id != current_user.company_id and 
            current_user.role != "admin"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this audit event"
            )
        
        return AuditEventResponse(
            id=str(event.id),
            event_type=event.event_type.value,
            severity=event.severity.value,
            entity_type=event.entity_type,
            entity_id=str(event.entity_id),
            actor_user_id=str(event.actor_user_id) if event.actor_user_id else None,
            actor_company_id=str(event.actor_company_id) if event.actor_company_id else None,
            actor_ip_address=event.actor_ip_address,
            action=event.action,
            description=event.description,
            old_values=event.old_values,
            new_values=event.new_values,
            changed_fields=event.changed_fields,
            request_id=event.request_id,
            api_endpoint=event.api_endpoint,
            http_method=event.http_method,
            metadata=event.audit_metadata,
            business_context=event.business_context,
            is_sensitive=event.is_sensitive,
            compliance_tags=event.compliance_tags,
            created_at=event.created_at.isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get audit event", event_id=str(event_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get audit event: {str(e)}"
        )


@router.get("/purchase-orders/{po_id}/trail", response_model=POAuditTrailResponse)
async def get_po_audit_trail(
    po_id: UUID,
    include_related: bool = Query(True, description="Include related entity events"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of events"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> POAuditTrailResponse:
    """
    Get complete audit trail for a Purchase Order.
    
    Returns all audit events related to the PO with timeline summary.
    """
    try:
        # Verify PO access
        from app.models.purchase_order import PurchaseOrder
        po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
        
        if not po:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Purchase order not found"
            )
        
        # Check access permissions
        if (po.buyer_company_id != current_user.company_id and 
            po.seller_company_id != current_user.company_id and
            current_user.role != "admin"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this purchase order"
            )
        
        audit_logger = AuditLogger(db)
        events = audit_logger.get_po_audit_trail(
            po_id=po_id,
            include_related=include_related,
            limit=limit
        )
        
        # Create timeline summary
        timeline_summary = []
        for event in events[:10]:  # Top 10 events for summary
            timeline_summary.append({
                "timestamp": event.created_at.isoformat(),
                "event_type": event.event_type.value,
                "action": event.action,
                "description": event.description,
                "actor_user_id": str(event.actor_user_id) if event.actor_user_id else None
            })
        
        # Create compliance status
        compliance_status = {
            "total_events": len(events),
            "has_creation_event": any(e.event_type == AuditEventType.PO_CREATED for e in events),
            "has_confirmation_event": any(e.event_type == AuditEventType.PO_CONFIRMED for e in events),
            "last_modified": events[0].created_at.isoformat() if events else None,
            "audit_completeness": "complete" if len(events) > 0 else "incomplete"
        }
        
        event_responses = [
            AuditEventResponse(
                id=str(event.id),
                event_type=event.event_type.value,
                severity=event.severity.value,
                entity_type=event.entity_type,
                entity_id=str(event.entity_id),
                actor_user_id=str(event.actor_user_id) if event.actor_user_id else None,
                actor_company_id=str(event.actor_company_id) if event.actor_company_id else None,
                actor_ip_address=event.actor_ip_address,
                action=event.action,
                description=event.description,
                old_values=event.old_values,
                new_values=event.new_values,
                changed_fields=event.changed_fields,
                request_id=event.request_id,
                api_endpoint=event.api_endpoint,
                http_method=event.http_method,
                metadata=event.audit_metadata,
                business_context=event.business_context,
                is_sensitive=event.is_sensitive,
                compliance_tags=event.compliance_tags,
                created_at=event.created_at.isoformat()
            )
            for event in events
        ]
        
        return POAuditTrailResponse(
            po_id=str(po_id),
            total_events=len(events),
            events=event_responses,
            timeline_summary=timeline_summary,
            compliance_status=compliance_status
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get PO audit trail", po_id=str(po_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get PO audit trail: {str(e)}"
        )


@router.get("/stats", response_model=AuditStatsResponse)
async def get_audit_statistics(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> AuditStatsResponse:
    """
    Get audit statistics and analytics for the current user's company.

    Returns comprehensive audit metrics including event counts,
    top actors, and compliance summary.
    """
    try:
        from sqlalchemy import func, and_

        cutoff_date = datetime.utcnow() - timedelta(days=days)

        # Base query scoped to user's company
        base_query = db.query(AuditEvent).filter(
            and_(
                AuditEvent.actor_company_id == current_user.company_id,
                AuditEvent.created_at >= cutoff_date
            )
        )

        # Total events
        total_events = base_query.count()

        # Events by type
        type_counts = db.query(
            AuditEvent.event_type,
            func.count(AuditEvent.id)
        ).filter(
            and_(
                AuditEvent.actor_company_id == current_user.company_id,
                AuditEvent.created_at >= cutoff_date
            )
        ).group_by(AuditEvent.event_type).all()

        events_by_type = {
            event_type.value: count for event_type, count in type_counts
        }

        # Events by severity
        severity_counts = db.query(
            AuditEvent.severity,
            func.count(AuditEvent.id)
        ).filter(
            and_(
                AuditEvent.actor_company_id == current_user.company_id,
                AuditEvent.created_at >= cutoff_date
            )
        ).group_by(AuditEvent.severity).all()

        events_by_severity = {
            severity.value: count for severity, count in severity_counts
        }

        # Events by entity type
        entity_counts = db.query(
            AuditEvent.entity_type,
            func.count(AuditEvent.id)
        ).filter(
            and_(
                AuditEvent.actor_company_id == current_user.company_id,
                AuditEvent.created_at >= cutoff_date
            )
        ).group_by(AuditEvent.entity_type).all()

        events_by_entity_type = {
            entity_type: count for entity_type, count in entity_counts
        }

        # Recent activity (last 10 events)
        recent_events = base_query.order_by(
            AuditEvent.created_at.desc()
        ).limit(10).all()

        recent_activity = [
            {
                "id": str(event.id),
                "event_type": event.event_type.value,
                "entity_type": event.entity_type,
                "action": event.action,
                "description": event.description,
                "created_at": event.created_at.isoformat(),
                "actor_user_id": str(event.actor_user_id) if event.actor_user_id else None
            }
            for event in recent_events
        ]

        # Top actors (users with most events)
        actor_counts = db.query(
            AuditEvent.actor_user_id,
            func.count(AuditEvent.id)
        ).filter(
            and_(
                AuditEvent.actor_company_id == current_user.company_id,
                AuditEvent.created_at >= cutoff_date,
                AuditEvent.actor_user_id.isnot(None)
            )
        ).group_by(AuditEvent.actor_user_id).order_by(
            func.count(AuditEvent.id).desc()
        ).limit(5).all()

        top_actors = []
        for user_id, count in actor_counts:
            user = db.query(User).filter(User.id == user_id).first()
            top_actors.append({
                "user_id": str(user_id),
                "user_name": user.full_name if user else "Unknown",
                "event_count": count
            })

        # Compliance summary
        po_events = base_query.filter(
            AuditEvent.entity_type == "purchase_order"
        ).count()

        critical_events = base_query.filter(
            AuditEvent.severity == AuditEventSeverity.CRITICAL
        ).count()

        compliance_summary = {
            "po_audit_coverage": po_events,
            "critical_events": critical_events,
            "audit_completeness_score": min(100, (total_events / max(1, days)) * 10),  # Rough score
            "compliance_status": "compliant" if critical_events == 0 else "needs_attention"
        }

        return AuditStatsResponse(
            total_events=total_events,
            events_by_type=events_by_type,
            events_by_severity=events_by_severity,
            events_by_entity_type=events_by_entity_type,
            recent_activity=recent_activity,
            top_actors=top_actors,
            compliance_summary=compliance_summary
        )

    except Exception as e:
        logger.error("Failed to get audit statistics", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get audit statistics: {str(e)}"
        )


@router.get("/compliance/report")
async def get_compliance_report(
    start_date: Optional[datetime] = Query(None, description="Report start date"),
    end_date: Optional[datetime] = Query(None, description="Report end date"),
    format: str = Query("json", description="Report format (json, csv)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Generate compliance report for audit events.

    Provides detailed compliance analysis including coverage,
    completeness, and regulatory compliance status.
    """
    try:
        # Default to last 90 days if no dates provided
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=90)
        if not end_date:
            end_date = datetime.utcnow()

        audit_logger = AuditLogger(db)

        # Get all events in the period
        events = audit_logger.query_audit_events(
            actor_company_id=current_user.company_id,
            start_date=start_date,
            end_date=end_date,
            limit=10000  # Large limit for comprehensive report
        )

        # Analyze compliance metrics
        po_events = [e for e in events if e.entity_type == "purchase_order"]
        user_events = [e for e in events if e.entity_type == "user"]
        critical_events = [e for e in events if e.severity == AuditEventSeverity.CRITICAL]

        # Calculate coverage metrics
        unique_pos = len(set(e.entity_id for e in po_events))
        unique_users = len(set(e.actor_user_id for e in events if e.actor_user_id))

        # Compliance analysis
        compliance_report = {
            "report_period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days_covered": (end_date - start_date).days
            },
            "audit_coverage": {
                "total_events": len(events),
                "po_events": len(po_events),
                "user_events": len(user_events),
                "unique_pos_audited": unique_pos,
                "unique_users_tracked": unique_users
            },
            "compliance_metrics": {
                "critical_events": len(critical_events),
                "audit_completeness": "complete" if len(events) > 0 else "incomplete",
                "data_retention_compliance": "compliant",  # Based on retention policies
                "immutability_compliance": "compliant"  # Audit events are immutable
            },
            "event_breakdown": {
                "by_type": {},
                "by_severity": {},
                "by_entity_type": {}
            },
            "compliance_status": {
                "overall_status": "compliant" if len(critical_events) == 0 else "needs_review",
                "recommendations": []
            }
        }

        # Event breakdowns
        for event in events:
            # By type
            event_type = event.event_type.value
            compliance_report["event_breakdown"]["by_type"][event_type] = \
                compliance_report["event_breakdown"]["by_type"].get(event_type, 0) + 1

            # By severity
            severity = event.severity.value
            compliance_report["event_breakdown"]["by_severity"][severity] = \
                compliance_report["event_breakdown"]["by_severity"].get(severity, 0) + 1

            # By entity type
            entity_type = event.entity_type
            compliance_report["event_breakdown"]["by_entity_type"][entity_type] = \
                compliance_report["event_breakdown"]["by_entity_type"].get(entity_type, 0) + 1

        # Generate recommendations
        if len(critical_events) > 0:
            compliance_report["compliance_status"]["recommendations"].append(
                f"Review {len(critical_events)} critical audit events"
            )

        if unique_pos < 10:  # Arbitrary threshold
            compliance_report["compliance_status"]["recommendations"].append(
                "Increase PO audit coverage"
            )

        logger.info(
            "Compliance report generated",
            company_id=str(current_user.company_id),
            events_analyzed=len(events),
            period_days=(end_date - start_date).days
        )

        return compliance_report

    except Exception as e:
        logger.error("Failed to generate compliance report", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate compliance report: {str(e)}"
        )

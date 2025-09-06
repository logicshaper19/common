"""
Onboarding progress model for tracking company onboarding steps.
"""
from sqlalchemy import Column, String, DateTime, Boolean, Integer, Text, ForeignKey, JSON, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Optional, Dict, Any
import uuid

from app.core.database import Base


class OnboardingProgress(Base):
    """
    Model for tracking company onboarding progress and completion metrics.
    """
    __tablename__ = "onboarding_progress"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Core fields
    company_id = Column(String, ForeignKey("companies.id"), nullable=False, unique=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    
    # Onboarding status
    status = Column(String, nullable=False, default="not_started", index=True)  # not_started, in_progress, completed, abandoned
    current_step = Column(String, nullable=True)  # Current onboarding step
    total_steps = Column(Integer, nullable=False, default=7)
    completed_steps = Column(Integer, nullable=False, default=0)
    
    # Timestamps
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    last_activity_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Step completion tracking
    step_completion_data = Column(JSON, nullable=False, default=dict)  # JSON object tracking individual step completion
    
    # Metrics
    total_time_minutes = Column(Integer, nullable=True)  # Total time spent on onboarding
    abandonment_reason = Column(String, nullable=True)  # Reason for abandonment if applicable
    completion_score = Column(Integer, nullable=True)  # Quality score of onboarding completion (0-100)
    
    # Viral analytics fields
    invitation_id = Column(String, ForeignKey("supplier_invitations.id"), nullable=True)
    referral_source = Column(String, nullable=True)  # How they found the platform
    
    # Help and support
    help_requests_count = Column(Integer, nullable=False, default=0)
    support_tickets_created = Column(Integer, nullable=False, default=0)
    
    # Relationships
    company = relationship("Company", foreign_keys=[company_id])
    user = relationship("User", foreign_keys=[user_id])
    invitation = relationship("SupplierInvitation", foreign_keys=[invitation_id])
    
    def __repr__(self):
        return f"<OnboardingProgress(id={self.id}, company={self.company_id}, status={self.status}, progress={self.completed_steps}/{self.total_steps})>"
    
    @property
    def completion_percentage(self) -> float:
        """Calculate completion percentage."""
        if self.total_steps == 0:
            return 0.0
        return (self.completed_steps / self.total_steps) * 100
    
    @property
    def is_completed(self) -> bool:
        """Check if onboarding is completed."""
        return self.status == "completed"
    
    @property
    def is_abandoned(self) -> bool:
        """Check if onboarding was abandoned."""
        return self.status == "abandoned"
    
    @property
    def time_since_last_activity_hours(self) -> Optional[int]:
        """Get hours since last activity."""
        if not self.last_activity_at:
            return None
        return int((datetime.utcnow() - self.last_activity_at).total_seconds() / 3600)
    
    def start_onboarding(self) -> None:
        """Mark onboarding as started."""
        if self.status == "not_started":
            self.status = "in_progress"
            self.started_at = datetime.utcnow()
            self.last_activity_at = datetime.utcnow()
    
    def complete_step(self, step_name: str, step_data: Optional[Dict[str, Any]] = None) -> None:
        """Mark a step as completed."""
        if self.status == "not_started":
            self.start_onboarding()
        
        # Update step completion data
        if not self.step_completion_data:
            self.step_completion_data = {}
        
        self.step_completion_data[step_name] = {
            "completed_at": datetime.utcnow().isoformat(),
            "data": step_data or {}
        }
        
        # Update counters
        self.completed_steps = len(self.step_completion_data)
        self.current_step = step_name
        self.last_activity_at = datetime.utcnow()
        
        # Check if onboarding is complete
        if self.completed_steps >= self.total_steps:
            self.complete_onboarding()
    
    def complete_onboarding(self) -> None:
        """Mark onboarding as completed."""
        self.status = "completed"
        self.completed_at = datetime.utcnow()
        self.last_activity_at = datetime.utcnow()
        
        if self.started_at:
            self.total_time_minutes = int((self.completed_at - self.started_at).total_seconds() / 60)
        
        # Calculate completion score based on various factors
        self.completion_score = self._calculate_completion_score()
    
    def abandon_onboarding(self, reason: Optional[str] = None) -> None:
        """Mark onboarding as abandoned."""
        self.status = "abandoned"
        self.abandonment_reason = reason
        self.last_activity_at = datetime.utcnow()
    
    def record_help_request(self) -> None:
        """Record that user requested help."""
        self.help_requests_count += 1
        self.last_activity_at = datetime.utcnow()
    
    def record_support_ticket(self) -> None:
        """Record that user created a support ticket."""
        self.support_tickets_created += 1
        self.last_activity_at = datetime.utcnow()
    
    def _calculate_completion_score(self) -> int:
        """Calculate a quality score for onboarding completion."""
        score = 100
        
        # Deduct points for help requests
        score -= min(self.help_requests_count * 5, 20)
        
        # Deduct points for support tickets
        score -= min(self.support_tickets_created * 10, 30)
        
        # Bonus for quick completion
        if self.total_time_minutes and self.total_time_minutes < 60:  # Completed in under 1 hour
            score += 10
        
        return max(score, 0)

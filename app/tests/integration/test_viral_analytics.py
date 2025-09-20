"""
Tests for viral onboarding analytics system.
"""
import pytest
from unittest.mock import Mock, patch
from uuid import uuid4
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.services.viral_analytics import ViralAnalyticsService
from app.services.viral_analytics.models import CascadeMetrics, NetworkEffectMetrics
from app.models.viral_analytics import (
    SupplierInvitation,
    OnboardingProgress,
    ViralCascadeNode,
    InvitationStatus,
    OnboardingStage
)
from app.models.user import User
from app.models.company import Company
from app.models.product import Product
from app.models.purchase_order import PurchaseOrder
from app.models.batch import Batch

# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_viral_analytics.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
Base.metadata.create_all(bind=engine)


@pytest.fixture(autouse=True)
def clean_db():
    """Clean database before each test."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture
def db_session():
    """Get database session for testing."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def sample_companies(db_session):
    """Create sample companies for testing."""
    companies = {}
    
    companies["root"] = Company(
        id=uuid4(),
        name="Root Company",
        company_type="brand",
        email="root@example.com"
    )
    
    companies["level1_a"] = Company(
        id=uuid4(),
        name="Level 1 Company A",
        company_type="processor",
        email="level1a@example.com"
    )
    
    companies["level1_b"] = Company(
        id=uuid4(),
        name="Level 1 Company B",
        company_type="processor",
        email="level1b@example.com"
    )
    
    companies["level2_a"] = Company(
        id=uuid4(),
        name="Level 2 Company A",
        company_type="supplier",
        email="level2a@example.com"
    )
    
    for company in companies.values():
        db_session.add(company)
    
    db_session.commit()
    
    for company in companies.values():
        db_session.refresh(company)
    
    return companies


@pytest.fixture
def sample_users(db_session, sample_companies):
    """Create sample users for testing."""
    users = {}
    
    users["root_user"] = User(
        id=uuid4(),
        email="root.user@example.com",
        hashed_password="hashed_password",
        full_name="Root User",
        role="admin",
        is_active=True,
        company_id=sample_companies["root"].id
    )
    
    users["level1_user"] = User(
        id=uuid4(),
        email="level1.user@example.com",
        hashed_password="hashed_password",
        full_name="Level 1 User",
        role="buyer",
        is_active=True,
        company_id=sample_companies["level1_a"].id
    )
    
    for user in users.values():
        db_session.add(user)
    
    db_session.commit()
    
    for user in users.values():
        db_session.refresh(user)
    
    return users


class TestViralAnalyticsService:
    """Test viral analytics service functionality."""
    
    def test_track_supplier_invitation(self, db_session, sample_companies, sample_users):
        """Test tracking supplier invitations."""
        viral_service = ViralAnalyticsService(db_session)
        root_user = sample_users["root_user"]
        
        # Track invitation
        invitation = viral_service.track_supplier_invitation(
            inviting_company_id=root_user.company_id,
            inviting_user_id=root_user.id,
            invited_email="new.supplier@example.com",
            invited_company_name="New Supplier Company",
            invitation_source="dashboard"
        )
        
        # Verify invitation
        assert invitation.id is not None
        assert invitation.inviting_company_id == root_user.company_id
        assert invitation.inviting_user_id == root_user.id
        assert invitation.invited_email == "new.supplier@example.com"
        assert invitation.invited_company_name == "New Supplier Company"
        assert invitation.invitation_level == 1  # First level invitation
        assert invitation.root_inviter_company_id == root_user.company_id
        assert invitation.status == InvitationStatus.PENDING.value
        assert invitation.expires_at is not None
    
    def test_track_invitation_acceptance(self, db_session, sample_companies, sample_users):
        """Test tracking invitation acceptance."""
        viral_service = ViralAnalyticsService(db_session)
        root_user = sample_users["root_user"]
        
        # Create invitation
        invitation = viral_service.track_supplier_invitation(
            inviting_company_id=root_user.company_id,
            inviting_user_id=root_user.id,
            invited_email="new.supplier@example.com"
        )
        
        # Create business relationship
        relationship = BusinessRelationship(
            id=uuid4(),
            buyer_company_id=root_user.company_id,
            seller_company_id=sample_companies["level1_a"].id,
            relationship_type="supplier",
            status="active"
        )
        db_session.add(relationship)
        db_session.commit()
        db_session.refresh(relationship)
        
        # Track acceptance
        onboarding_progress = viral_service.track_invitation_acceptance(
            invitation_id=invitation.id,
            registered_company_id=sample_companies["level1_a"].id,
            business_relationship_id=relationship.id
        )
        
        # Verify invitation update
        db_session.refresh(invitation)
        assert invitation.status == InvitationStatus.ACCEPTED.value
        assert invitation.accepted_at is not None
        assert invitation.registered_company_id == sample_companies["level1_a"].id
        assert invitation.business_relationship_id == relationship.id
        
        # Verify onboarding progress
        assert onboarding_progress.company_id == sample_companies["level1_a"].id
        assert onboarding_progress.invitation_id == invitation.id
        assert onboarding_progress.current_stage == OnboardingStage.REGISTERED.value
        assert onboarding_progress.time_to_register_hours is not None
        assert onboarding_progress.time_to_register_hours >= 0
    
    def test_update_onboarding_stage(self, db_session, sample_companies):
        """Test updating onboarding stages."""
        viral_service = ViralAnalyticsService(db_session)
        company_id = sample_companies["level1_a"].id
        
        # Create initial progress
        progress = OnboardingProgress(
            company_id=company_id,
            current_stage=OnboardingStage.REGISTERED.value,
            registered_at=datetime.utcnow()
        )
        db_session.add(progress)
        db_session.commit()
        
        # Update to profile completed
        viral_service.update_onboarding_stage(
            company_id=company_id,
            new_stage=OnboardingStage.PROFILE_COMPLETED,
            metadata={"profile_completion_percentage": 100}
        )
        
        # Verify update
        db_session.refresh(progress)
        assert progress.current_stage == OnboardingStage.PROFILE_COMPLETED.value
        assert progress.profile_completed_at is not None
        assert len(progress.stages_completed) >= 1
        
        # Update to first PO created
        viral_service.update_onboarding_stage(
            company_id=company_id,
            new_stage=OnboardingStage.FIRST_PO_CREATED
        )
        
        # Verify update
        db_session.refresh(progress)
        assert progress.current_stage == OnboardingStage.FIRST_PO_CREATED.value
        assert progress.first_po_created_at is not None
        assert progress.time_to_first_po_hours is not None
    
    def test_calculate_cascade_metrics(self, db_session, sample_companies, sample_users):
        """Test cascade metrics calculation."""
        viral_service = ViralAnalyticsService(db_session)
        root_user = sample_users["root_user"]
        
        # Create invitation cascade
        invitation1 = viral_service.track_supplier_invitation(
            inviting_company_id=root_user.company_id,
            inviting_user_id=root_user.id,
            invited_email="supplier1@example.com"
        )
        
        invitation2 = viral_service.track_supplier_invitation(
            inviting_company_id=root_user.company_id,
            inviting_user_id=root_user.id,
            invited_email="supplier2@example.com"
        )
        
        # Accept one invitation
        relationship = BusinessRelationship(
            id=uuid4(),
            buyer_company_id=root_user.company_id,
            seller_company_id=sample_companies["level1_a"].id,
            relationship_type="supplier",
            status="active"
        )
        db_session.add(relationship)
        db_session.commit()
        
        viral_service.track_invitation_acceptance(
            invitation_id=invitation1.id,
            registered_company_id=sample_companies["level1_a"].id,
            business_relationship_id=relationship.id
        )
        
        # Calculate metrics
        metrics = viral_service.calculate_cascade_metrics(
            root_company_id=root_user.company_id,
            time_period_days=30
        )
        
        # Verify metrics
        assert isinstance(metrics, CascadeMetrics)
        assert metrics.total_invitations_sent == 2
        assert metrics.total_invitations_accepted == 1
        assert metrics.acceptance_rate == 50.0
        assert metrics.total_companies_onboarded == 1
        assert 1 in metrics.onboarding_levels
        assert metrics.onboarding_levels[1] == 1
    
    def test_network_effect_metrics(self, db_session, sample_companies):
        """Test network effect metrics calculation."""
        viral_service = ViralAnalyticsService(db_session)
        
        # Create business relationships
        relationship1 = BusinessRelationship(
            id=uuid4(),
            buyer_company_id=sample_companies["root"].id,
            seller_company_id=sample_companies["level1_a"].id,
            relationship_type="supplier",
            status="active"
        )
        
        relationship2 = BusinessRelationship(
            id=uuid4(),
            buyer_company_id=sample_companies["level1_a"].id,
            seller_company_id=sample_companies["level2_a"].id,
            relationship_type="supplier",
            status="active"
        )
        
        db_session.add(relationship1)
        db_session.add(relationship2)
        db_session.commit()
        
        # Calculate network metrics
        metrics = viral_service.calculate_network_effect_metrics(time_period_days=90)
        
        # Verify metrics
        assert isinstance(metrics, NetworkEffectMetrics)
        assert metrics.total_nodes == len(sample_companies)
        assert metrics.total_edges == 2
        assert metrics.network_density >= 0.0
        assert isinstance(metrics.viral_champions, list)
        assert isinstance(metrics.growth_hotspots, list)
        assert isinstance(metrics.conversion_funnel, dict)
    
    def test_onboarding_chain_visualization(self, db_session, sample_companies, sample_users):
        """Test onboarding chain visualization generation."""
        viral_service = ViralAnalyticsService(db_session)
        root_company_id = sample_companies["root"].id
        
        # Create cascade nodes
        node1 = ViralCascadeNode(
            company_id=root_company_id,
            root_company_id=root_company_id,
            cascade_level=0,
            position_in_level=0,
            direct_invitations_sent=2,
            direct_invitations_accepted=1,
            direct_conversion_rate=0.5,
            joined_at=datetime.utcnow()
        )
        
        node2 = ViralCascadeNode(
            company_id=sample_companies["level1_a"].id,
            parent_company_id=root_company_id,
            root_company_id=root_company_id,
            cascade_level=1,
            position_in_level=0,
            direct_invitations_sent=1,
            direct_invitations_accepted=0,
            direct_conversion_rate=0.0,
            joined_at=datetime.utcnow()
        )
        
        db_session.add(node1)
        db_session.add(node2)
        db_session.commit()
        
        # Generate visualization
        visualization = viral_service.generate_onboarding_chain_visualization(
            root_company_id=root_company_id,
            max_depth=3
        )
        
        # Verify visualization
        assert len(visualization.nodes) == 2
        assert len(visualization.edges) == 1
        assert 0 in visualization.levels
        assert 1 in visualization.levels
        assert len(visualization.levels[0]) == 1
        assert len(visualization.levels[1]) == 1
        
        # Verify node data
        root_node = next(node for node in visualization.nodes if node["level"] == 0)
        assert root_node["company_name"] == sample_companies["root"].name
        assert root_node["invitations_sent"] == 2
        assert root_node["invitations_accepted"] == 1
        assert root_node["conversion_rate"] == 0.5
        
        # Verify edge data
        edge = visualization.edges[0]
        assert edge["source"] == str(root_company_id)
        assert edge["target"] == str(sample_companies["level1_a"].id)
        assert edge["relationship_type"] == "invitation"
    
    def test_viral_coefficient_calculation(self, db_session, sample_companies, sample_users):
        """Test viral coefficient calculation."""
        viral_service = ViralAnalyticsService(db_session)
        
        # Create multiple invitations from different companies
        root_user = sample_users["root_user"]
        
        # Root company sends 3 invitations
        for i in range(3):
            viral_service.track_supplier_invitation(
                inviting_company_id=root_user.company_id,
                inviting_user_id=root_user.id,
                invited_email=f"supplier{i}@example.com"
            )
        
        # Calculate viral coefficient
        viral_coefficient = viral_service._calculate_viral_coefficient(time_period_days=30)
        
        # Should be 3 invitations / 4 total companies = 0.75
        assert viral_coefficient == 0.75
    
    def test_stage_order_progression(self, db_session):
        """Test onboarding stage order progression."""
        viral_service = ViralAnalyticsService(db_session)
        
        # Test stage order
        assert viral_service._get_stage_order(OnboardingStage.INVITED.value) == 0
        assert viral_service._get_stage_order(OnboardingStage.REGISTERED.value) == 1
        assert viral_service._get_stage_order(OnboardingStage.PROFILE_COMPLETED.value) == 2
        assert viral_service._get_stage_order(OnboardingStage.FIRST_PO_CREATED.value) == 3
        assert viral_service._get_stage_order(OnboardingStage.FIRST_PO_CONFIRMED.value) == 4
        assert viral_service._get_stage_order(OnboardingStage.ACTIVE_USER.value) == 5
    
    def test_invitation_level_tracking(self, db_session, sample_companies, sample_users):
        """Test invitation level tracking for cascade depth."""
        viral_service = ViralAnalyticsService(db_session)
        root_user = sample_users["root_user"]
        
        # Level 1 invitation
        invitation1 = viral_service.track_supplier_invitation(
            inviting_company_id=root_user.company_id,
            inviting_user_id=root_user.id,
            invited_email="level1@example.com"
        )
        
        assert invitation1.invitation_level == 1
        assert invitation1.root_inviter_company_id == root_user.company_id
        
        # Accept invitation and create level 2
        relationship = BusinessRelationship(
            id=uuid4(),
            buyer_company_id=root_user.company_id,
            seller_company_id=sample_companies["level1_a"].id,
            relationship_type="supplier",
            status="active"
        )
        db_session.add(relationship)
        db_session.commit()
        
        viral_service.track_invitation_acceptance(
            invitation_id=invitation1.id,
            registered_company_id=sample_companies["level1_a"].id,
            business_relationship_id=relationship.id
        )
        
        # Level 2 invitation (from level 1 company)
        level1_user = User(
            id=uuid4(),
            email="level1@example.com",
            hashed_password="hashed",
            full_name="Level 1 User",
            role="buyer",
            company_id=sample_companies["level1_a"].id
        )
        db_session.add(level1_user)
        db_session.commit()
        
        invitation2 = viral_service.track_supplier_invitation(
            inviting_company_id=sample_companies["level1_a"].id,
            inviting_user_id=level1_user.id,
            invited_email="level2@example.com"
        )
        
        assert invitation2.invitation_level == 2
        assert invitation2.root_inviter_company_id == root_user.company_id
        assert invitation2.parent_invitation_id == invitation1.id

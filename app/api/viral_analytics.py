"""
API endpoints for viral onboarding analytics.
"""
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.services.viral_analytics import (
    ViralAnalyticsService,
    CascadeMetrics,
    NetworkEffectMetrics,
    OnboardingChainVisualization
)
from app.models.viral_analytics import InvitationStatus, OnboardingStage
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/viral-analytics", tags=["viral-analytics"])


# Request Models
class InvitationRequest(BaseModel):
    """Request model for tracking supplier invitations."""
    invited_email: str = Field(..., description="Email of the invited supplier")
    invited_company_name: Optional[str] = Field(None, description="Name of the invited company")
    invitation_source: str = Field("dashboard", description="Source of the invitation")
    invitation_context: Optional[Dict[str, Any]] = Field(None, description="Additional context")


# Response Models
class CascadeMetricsResponse(BaseModel):
    """Response model for cascade metrics."""
    total_invitations_sent: int
    total_invitations_accepted: int
    acceptance_rate: float
    total_companies_onboarded: int
    onboarding_levels: Dict[int, int]
    top_inviters: List[Dict[str, Any]]
    recent_onboardings: List[Dict[str, Any]]
    network_growth_rate: float
    viral_coefficient: float
    average_cascade_depth: float
    
    class Config:
        from_attributes = True


class NetworkEffectMetricsResponse(BaseModel):
    """Response model for network effect metrics."""
    total_nodes: int
    total_edges: int
    network_density: float
    clustering_coefficient: float
    average_path_length: float
    viral_champions: List[Dict[str, Any]]
    growth_hotspots: List[Dict[str, Any]]
    conversion_funnel: Dict[str, Any]
    
    class Config:
        from_attributes = True


class OnboardingChainVisualizationResponse(BaseModel):
    """Response model for onboarding chain visualization."""
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
    levels: Dict[int, List[Dict[str, Any]]]
    root_companies: List[Dict[str, Any]]
    metrics: CascadeMetricsResponse
    
    class Config:
        from_attributes = True


class ViralDashboardResponse(BaseModel):
    """Response model for viral adoption dashboard data."""
    cascade_metrics: CascadeMetricsResponse
    network_metrics: NetworkEffectMetricsResponse
    onboarding_chain: OnboardingChainVisualizationResponse
    performance_summary: Dict[str, Any]
    growth_trends: List[Dict[str, Any]]
    recommendations: List[Dict[str, Any]]


@router.post("/invitations")
async def track_supplier_invitation(
    request: InvitationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Track a new supplier invitation for viral analytics.
    
    Records the invitation in the viral analytics system to enable
    cascade tracking and network effect measurement.
    """
    try:
        viral_service = ViralAnalyticsService(db)
        
        invitation = viral_service.track_supplier_invitation(
            inviting_company_id=current_user.company_id,
            inviting_user_id=current_user.id,
            invited_email=request.invited_email,
            invited_company_name=request.invited_company_name,
            invitation_source=request.invitation_source,
            invitation_context=request.invitation_context
        )
        
        return {
            "success": True,
            "invitation_id": str(invitation.id),
            "invitation_level": invitation.invitation_level,
            "message": "Supplier invitation tracked successfully"
        }
        
    except Exception as e:
        logger.error("Failed to track supplier invitation", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to track invitation: {str(e)}"
        )


@router.post("/invitations/{invitation_id}/accept")
async def track_invitation_acceptance(
    invitation_id: UUID,
    registered_company_id: UUID,
    business_relationship_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Track invitation acceptance and onboarding progress.
    
    Records when an invited supplier accepts the invitation and
    registers on the platform.
    """
    try:
        viral_service = ViralAnalyticsService(db)
        
        onboarding_progress = viral_service.track_invitation_acceptance(
            invitation_id=invitation_id,
            registered_company_id=registered_company_id,
            business_relationship_id=business_relationship_id
        )
        
        return {
            "success": True,
            "onboarding_progress_id": str(onboarding_progress.id),
            "time_to_register_hours": onboarding_progress.time_to_register_hours,
            "message": "Invitation acceptance tracked successfully"
        }
        
    except Exception as e:
        logger.error("Failed to track invitation acceptance", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to track acceptance: {str(e)}"
        )


@router.put("/onboarding/{company_id}/stage")
async def update_onboarding_stage(
    company_id: UUID,
    new_stage: OnboardingStage,
    metadata: Optional[Dict[str, Any]] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Update onboarding stage for a company.
    
    Tracks progression through the onboarding funnel for
    viral analytics and conversion rate optimization.
    """
    try:
        viral_service = ViralAnalyticsService(db)
        
        viral_service.update_onboarding_stage(
            company_id=company_id,
            new_stage=new_stage,
            metadata=metadata
        )
        
        return {
            "success": True,
            "company_id": str(company_id),
            "new_stage": new_stage.value,
            "message": "Onboarding stage updated successfully"
        }
        
    except Exception as e:
        logger.error("Failed to update onboarding stage", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update stage: {str(e)}"
        )


@router.get("/cascade-metrics", response_model=CascadeMetricsResponse)
async def get_cascade_metrics(
    root_company_id: Optional[UUID] = Query(None, description="Calculate metrics for specific root company"),
    time_period_days: int = Query(30, ge=1, le=365, description="Time period for metrics calculation"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> CascadeMetricsResponse:
    """
    Get viral cascade metrics and analytics.
    
    Provides comprehensive metrics about the viral onboarding
    cascade including invitation rates, acceptance rates, and
    network growth patterns.
    """
    try:
        viral_service = ViralAnalyticsService(db)
        
        # Use current user's company as root if not specified
        if not root_company_id:
            root_company_id = current_user.company_id
        
        metrics = viral_service.calculate_cascade_metrics(
            root_company_id=root_company_id,
            time_period_days=time_period_days
        )
        
        return CascadeMetricsResponse(
            total_invitations_sent=metrics.total_invitations_sent,
            total_invitations_accepted=metrics.total_invitations_accepted,
            acceptance_rate=metrics.acceptance_rate,
            total_companies_onboarded=metrics.total_companies_onboarded,
            onboarding_levels=metrics.onboarding_levels,
            top_inviters=metrics.top_inviters,
            recent_onboardings=metrics.recent_onboardings,
            network_growth_rate=metrics.network_growth_rate,
            viral_coefficient=metrics.viral_coefficient,
            average_cascade_depth=metrics.average_cascade_depth
        )
        
    except Exception as e:
        logger.error("Failed to get cascade metrics", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get metrics: {str(e)}"
        )


@router.get("/network-metrics", response_model=NetworkEffectMetricsResponse)
async def get_network_effect_metrics(
    time_period_days: int = Query(90, ge=1, le=365, description="Time period for analysis"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> NetworkEffectMetricsResponse:
    """
    Get network effect metrics for viral analysis.
    
    Provides comprehensive analysis of network effects including
    network density, viral champions, and growth hotspots.
    """
    try:
        viral_service = ViralAnalyticsService(db)
        
        metrics = viral_service.calculate_network_effect_metrics(
            time_period_days=time_period_days
        )
        
        return NetworkEffectMetricsResponse(
            total_nodes=metrics.total_nodes,
            total_edges=metrics.total_edges,
            network_density=metrics.network_density,
            clustering_coefficient=metrics.clustering_coefficient,
            average_path_length=metrics.average_path_length,
            viral_champions=metrics.viral_champions,
            growth_hotspots=metrics.growth_hotspots,
            conversion_funnel=metrics.conversion_funnel
        )
        
    except Exception as e:
        logger.error("Failed to get network effect metrics", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get network metrics: {str(e)}"
        )


@router.get("/onboarding-chain", response_model=OnboardingChainVisualizationResponse)
async def get_onboarding_chain_visualization(
    root_company_id: Optional[UUID] = Query(None, description="Root company for visualization"),
    max_depth: int = Query(5, ge=1, le=10, description="Maximum depth to visualize"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> OnboardingChainVisualizationResponse:
    """
    Get onboarding chain visualization data.
    
    Provides visualization data for the viral onboarding cascade
    including nodes, edges, and hierarchical structure.
    """
    try:
        viral_service = ViralAnalyticsService(db)
        
        # Use current user's company as root if not specified
        if not root_company_id:
            root_company_id = current_user.company_id
        
        visualization = viral_service.generate_onboarding_chain_visualization(
            root_company_id=root_company_id,
            max_depth=max_depth
        )
        
        return OnboardingChainVisualizationResponse(
            nodes=visualization.nodes,
            edges=visualization.edges,
            levels=visualization.levels,
            root_companies=visualization.root_companies,
            metrics=CascadeMetricsResponse(
                total_invitations_sent=visualization.metrics.total_invitations_sent,
                total_invitations_accepted=visualization.metrics.total_invitations_accepted,
                acceptance_rate=visualization.metrics.acceptance_rate,
                total_companies_onboarded=visualization.metrics.total_companies_onboarded,
                onboarding_levels=visualization.metrics.onboarding_levels,
                top_inviters=visualization.metrics.top_inviters,
                recent_onboardings=visualization.metrics.recent_onboardings,
                network_growth_rate=visualization.metrics.network_growth_rate,
                viral_coefficient=visualization.metrics.viral_coefficient,
                average_cascade_depth=visualization.metrics.average_cascade_depth
            )
        )
        
    except Exception as e:
        logger.error("Failed to get onboarding chain visualization", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get visualization: {str(e)}"
        )


@router.get("/dashboard", response_model=ViralDashboardResponse)
async def get_viral_adoption_dashboard(
    time_period_days: int = Query(30, ge=1, le=365, description="Time period for dashboard data"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> ViralDashboardResponse:
    """
    Get comprehensive viral adoption dashboard data.

    Provides all the data needed for a viral adoption reporting
    dashboard including metrics, visualizations, and recommendations.
    """
    try:
        viral_service = ViralAnalyticsService(db)

        # Get cascade metrics
        cascade_metrics = viral_service.calculate_cascade_metrics(
            root_company_id=current_user.company_id,
            time_period_days=time_period_days
        )

        # Get network metrics
        network_metrics = viral_service.calculate_network_effect_metrics(
            time_period_days=time_period_days
        )

        # Get onboarding chain visualization
        onboarding_chain = viral_service.generate_onboarding_chain_visualization(
            root_company_id=current_user.company_id,
            max_depth=3  # Limit depth for dashboard
        )

        # Generate performance summary
        performance_summary = {
            "total_network_size": network_metrics.total_nodes,
            "your_cascade_size": len(onboarding_chain.nodes),
            "viral_performance": "excellent" if cascade_metrics.viral_coefficient > 2.0 else
                               "good" if cascade_metrics.viral_coefficient > 1.0 else
                               "needs_improvement",
            "acceptance_rate_vs_average": cascade_metrics.acceptance_rate,
            "growth_trend": "increasing" if cascade_metrics.network_growth_rate > 0 else "stable",
            "top_performer_rank": _calculate_company_rank(current_user.company_id, cascade_metrics.top_inviters)
        }

        # Generate growth trends (simplified for dashboard)
        growth_trends = [
            {
                "period": f"Last {time_period_days} days",
                "invitations_sent": cascade_metrics.total_invitations_sent,
                "companies_onboarded": cascade_metrics.total_companies_onboarded,
                "growth_rate": cascade_metrics.network_growth_rate,
                "viral_coefficient": cascade_metrics.viral_coefficient
            }
        ]

        # Generate recommendations
        recommendations = _generate_viral_recommendations(cascade_metrics, network_metrics)

        return ViralDashboardResponse(
            cascade_metrics=CascadeMetricsResponse(
                total_invitations_sent=cascade_metrics.total_invitations_sent,
                total_invitations_accepted=cascade_metrics.total_invitations_accepted,
                acceptance_rate=cascade_metrics.acceptance_rate,
                total_companies_onboarded=cascade_metrics.total_companies_onboarded,
                onboarding_levels=cascade_metrics.onboarding_levels,
                top_inviters=cascade_metrics.top_inviters,
                recent_onboardings=cascade_metrics.recent_onboardings,
                network_growth_rate=cascade_metrics.network_growth_rate,
                viral_coefficient=cascade_metrics.viral_coefficient,
                average_cascade_depth=cascade_metrics.average_cascade_depth
            ),
            network_metrics=NetworkEffectMetricsResponse(
                total_nodes=network_metrics.total_nodes,
                total_edges=network_metrics.total_edges,
                network_density=network_metrics.network_density,
                clustering_coefficient=network_metrics.clustering_coefficient,
                average_path_length=network_metrics.average_path_length,
                viral_champions=network_metrics.viral_champions,
                growth_hotspots=network_metrics.growth_hotspots,
                conversion_funnel=network_metrics.conversion_funnel
            ),
            onboarding_chain=OnboardingChainVisualizationResponse(
                nodes=onboarding_chain.nodes,
                edges=onboarding_chain.edges,
                levels=onboarding_chain.levels,
                root_companies=onboarding_chain.root_companies,
                metrics=CascadeMetricsResponse(
                    total_invitations_sent=onboarding_chain.metrics.total_invitations_sent,
                    total_invitations_accepted=onboarding_chain.metrics.total_invitations_accepted,
                    acceptance_rate=onboarding_chain.metrics.acceptance_rate,
                    total_companies_onboarded=onboarding_chain.metrics.total_companies_onboarded,
                    onboarding_levels=onboarding_chain.metrics.onboarding_levels,
                    top_inviters=onboarding_chain.metrics.top_inviters,
                    recent_onboardings=onboarding_chain.metrics.recent_onboardings,
                    network_growth_rate=onboarding_chain.metrics.network_growth_rate,
                    viral_coefficient=onboarding_chain.metrics.viral_coefficient,
                    average_cascade_depth=onboarding_chain.metrics.average_cascade_depth
                )
            ),
            performance_summary=performance_summary,
            growth_trends=growth_trends,
            recommendations=recommendations
        )

    except Exception as e:
        logger.error("Failed to get viral adoption dashboard", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get dashboard data: {str(e)}"
        )


def _calculate_company_rank(company_id: UUID, top_inviters: List[Dict[str, Any]]) -> int:
    """Calculate company rank among top inviters."""
    for i, inviter in enumerate(top_inviters):
        if inviter.get("company_id") == str(company_id):
            return i + 1
    return len(top_inviters) + 1


def _generate_viral_recommendations(
    cascade_metrics: CascadeMetrics,
    network_metrics: NetworkEffectMetrics
) -> List[Dict[str, Any]]:
    """Generate viral growth recommendations."""
    recommendations = []

    # Acceptance rate recommendations
    if cascade_metrics.acceptance_rate < 30:
        recommendations.append({
            "type": "acceptance_rate",
            "priority": "high",
            "title": "Improve Invitation Acceptance Rate",
            "description": f"Your acceptance rate is {cascade_metrics.acceptance_rate:.1f}%. Focus on personalizing invitations and highlighting value proposition.",
            "actions": [
                "Personalize invitation messages",
                "Include specific benefits for suppliers",
                "Follow up with phone calls",
                "Provide onboarding support"
            ]
        })

    # Viral coefficient recommendations
    if cascade_metrics.viral_coefficient < 1.0:
        recommendations.append({
            "type": "viral_coefficient",
            "priority": "high",
            "title": "Increase Viral Coefficient",
            "description": f"Your viral coefficient is {cascade_metrics.viral_coefficient:.2f}. Encourage new users to invite their suppliers.",
            "actions": [
                "Add invitation prompts in onboarding flow",
                "Gamify supplier invitations",
                "Provide invitation incentives",
                "Create supplier invitation templates"
            ]
        })

    # Network growth recommendations
    if cascade_metrics.network_growth_rate < 10:
        recommendations.append({
            "type": "growth_rate",
            "priority": "medium",
            "title": "Accelerate Network Growth",
            "description": f"Network growth rate is {cascade_metrics.network_growth_rate:.1f}%. Focus on expanding your supplier network.",
            "actions": [
                "Identify key suppliers to invite",
                "Create bulk invitation campaigns",
                "Partner with industry associations",
                "Attend trade shows and events"
            ]
        })

    # Onboarding recommendations
    conversion_funnel = network_metrics.conversion_funnel
    if conversion_funnel.get("activation_rate", 0) < 50:
        recommendations.append({
            "type": "onboarding",
            "priority": "medium",
            "title": "Improve Onboarding Conversion",
            "description": f"Only {conversion_funnel.get('activation_rate', 0):.1f}% of invited suppliers become active. Improve onboarding experience.",
            "actions": [
                "Simplify registration process",
                "Provide onboarding tutorials",
                "Assign dedicated support",
                "Create quick-start guides"
            ]
        })

    return recommendations

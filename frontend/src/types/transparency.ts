/**
 * Types and interfaces for transparency visualization dashboard
 *
 * SINGLE SOURCE OF TRUTH: All transparency metrics are calculated deterministically
 * from explicit user-created links in the supply_chain_traceability materialized view.
 * No algorithmic guessing, 100% auditable.
 */

// Transparency metrics - deterministic calculation based on explicit user actions
export interface TransparencyMetrics {
  ttm_score: number; // Mill transparency percentage (0-1 scale for compatibility)
  ttp_score: number; // Plantation transparency percentage (0-1 scale for compatibility)
  overall_score: number; // Average transparency percentage (0-1 scale for compatibility)
  confidence_level: number; // Always 1.0 (100%) - based on explicit user actions
  traced_percentage: number; // Percentage of volume traced through explicit links
  untraced_percentage: number; // Percentage of volume not yet traced
  last_updated: string; // Timestamp of deterministic calculation
}

// Supply chain node for visualization
export interface SupplyChainNode {
  id: string;
  company_id: string;
  company_name: string;
  company_type: 'brand' | 'processor' | 'originator';
  product_name: string;
  quantity: number;
  unit: string;
  level: number; // Depth in supply chain
  position: {
    x: number;
    y: number;
  };
  transparency_score: number;
  status: 'confirmed' | 'pending' | 'missing' | 'partial';
  po_id?: string;
  created_at: string;
}

// Supply chain edge/connection
export interface SupplyChainEdge {
  id: string;
  source: string;
  target: string;
  relationship_type: 'supplier' | 'buyer';
  confirmation_status: 'confirmed' | 'pending' | 'missing';
  transparency_impact: number;
  quantity_flow: number;
  unit: string;
}

// Gap analysis result
export interface GapAnalysisItem {
  id: string;
  type: 'missing_supplier' | 'unconfirmed_order' | 'incomplete_data' | 'low_transparency';
  severity: 'critical' | 'high' | 'medium' | 'low';
  title: string;
  description: string;
  impact_score: number;
  affected_nodes: string[];
  recommendations: string[];
  estimated_improvement: number;
}

// Complete supply chain visualization
export interface SupplyChainVisualization {
  company_id: string;
  root_po_id: string;
  nodes: SupplyChainNode[];
  edges: SupplyChainEdge[];
  total_levels: number;
  max_width: number;
  layout_algorithm: string;
  overall_ttm_score: number;
  overall_ttp_score: number;
  overall_confidence: number;
  traced_percentage: number;
  untraced_percentage: number;
  gap_analysis: GapAnalysisItem[];
  generated_at: string;
  calculation_time_ms: number;
}

// Transparency trend data
export interface TransparencyTrend {
  date: string;
  ttm_score: number;
  ttp_score: number;
  overall_score: number;
  traced_percentage: number;
}

// Company transparency summary
export interface CompanyTransparencySummary {
  company_id: string;
  company_name: string;
  company_type: string;
  current_metrics: TransparencyMetrics;
  trend_data: TransparencyTrend[];
  total_purchase_orders: number;
  confirmed_orders: number;
  pending_confirmations: number;
  critical_gaps: number;
  improvement_opportunities: number;
}

// Multi-client dashboard data for consultants
export interface MultiClientDashboard {
  consultant_id: string;
  total_clients: number;
  clients: CompanyTransparencySummary[];
  aggregate_metrics: {
    average_transparency: number;
    total_supply_chains: number;
    total_gaps_identified: number;
    total_improvements_implemented: number;
  };
  recent_activities: DashboardActivity[];
  alerts: DashboardAlert[];
}

// Dashboard activity
export interface DashboardActivity {
  id: string;
  type: 'transparency_update' | 'gap_identified' | 'improvement_implemented' | 'new_confirmation';
  company_id: string;
  company_name: string;
  title: string;
  description: string;
  impact: 'positive' | 'negative' | 'neutral';
  timestamp: string;
}

// Dashboard alert
export interface DashboardAlert {
  id: string;
  type: 'critical_gap' | 'low_transparency' | 'missing_confirmation' | 'deadline_approaching';
  severity: 'critical' | 'high' | 'medium' | 'low';
  company_id: string;
  company_name: string;
  title: string;
  message: string;
  action_required: boolean;
  deadline?: string;
  created_at: string;
}

// Chart data interfaces
export interface ChartDataPoint {
  name: string;
  value: number;
  color?: string;
  label?: string;
}

export interface TimeSeriesDataPoint {
  date: string;
  value: number;
  category?: string;
}

// Filter and view options
export interface TransparencyFilters {
  company_types?: string[];
  date_range?: {
    start: string;
    end: string;
  };
  transparency_threshold?: {
    min: number;
    max: number;
  };
  status_filter?: string[];
  product_categories?: string[];
}

export interface ViewOptions {
  layout: 'hierarchical' | 'force' | 'circular' | 'grid';
  show_labels: boolean;
  show_metrics: boolean;
  highlight_gaps: boolean;
  color_by: 'transparency' | 'company_type' | 'status' | 'level';
  zoom_level: number;
}

// Real-time update types
export interface TransparencyUpdate {
  type: 'score_change' | 'new_confirmation' | 'gap_resolved' | 'new_gap';
  company_id: string;
  data: any;
  timestamp: string;
}



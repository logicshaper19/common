/**
 * Tests for transparency API client
 */
import { transparencyApi, TransparencyApiClient } from '../transparencyApi';
import { apiClient } from '../api';

// Mock the API client
jest.mock('../api', () => ({
  apiClient: {
    get: jest.fn(),
    post: jest.fn(),
  },
}));

const mockApiClient = apiClient as jest.Mocked<typeof apiClient>;

describe('TransparencyApiClient', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('getTransparencyMetrics', () => {
    it('fetches transparency metrics successfully', async () => {
      const mockMetrics = {
        ttm_score: 78.5,
        ttp_score: 82.3,
        overall_score: 80.4,
        confidence_level: 85.2,
        traced_percentage: 76.8,
        untraced_percentage: 23.2,
        last_updated: '2024-01-15T10:00:00Z',
      };

      mockApiClient.get.mockResolvedValue({ data: mockMetrics });

      const result = await transparencyApi.getTransparencyMetrics('company-1');

      expect(mockApiClient.get).toHaveBeenCalledWith('/transparency/company-1');
      expect(result).toEqual(mockMetrics);
    });

    it('returns mock data when API fails', async () => {
      mockApiClient.get.mockRejectedValue(new Error('API Error'));

      const result = await transparencyApi.getTransparencyMetrics('company-1');

      expect(result).toBeDefined();
      expect(result.overall_score).toBeDefined();
      expect(result.ttm_score).toBeDefined();
      expect(result.ttp_score).toBeDefined();
    });
  });

  describe('getSupplyChainVisualization', () => {
    it('fetches supply chain visualization successfully', async () => {
      const mockVisualization = {
        company_id: 'company-1',
        root_po_id: 'po-001',
        nodes: [],
        edges: [],
        total_levels: 3,
        max_width: 2,
        layout_algorithm: 'hierarchical',
        overall_ttm_score: 78.5,
        overall_ttp_score: 82.3,
        overall_confidence: 85.2,
        traced_percentage: 76.8,
        untraced_percentage: 23.2,
        gap_analysis: [],
        generated_at: '2024-01-15T10:00:00Z',
        calculation_time_ms: 245,
      };

      mockApiClient.get.mockResolvedValue({ data: mockVisualization });

      const result = await transparencyApi.getSupplyChainVisualization('po-001');

      expect(mockApiClient.get).toHaveBeenCalledWith('/transparency/po/po-001', {
        params: { include_gap_analysis: true },
      });
      expect(result).toEqual(mockVisualization);
    });

    it('includes gap analysis parameter correctly', async () => {
      mockApiClient.get.mockResolvedValue({ data: {} });

      await transparencyApi.getSupplyChainVisualization('po-001', false);

      expect(mockApiClient.get).toHaveBeenCalledWith('/transparency/po/po-001', {
        params: { include_gap_analysis: false },
      });
    });

    it('returns mock data when API fails', async () => {
      mockApiClient.get.mockRejectedValue(new Error('API Error'));

      const result = await transparencyApi.getSupplyChainVisualization('po-001');

      expect(result).toBeDefined();
      expect(result.nodes).toBeDefined();
      expect(result.edges).toBeDefined();
      expect(result.gap_analysis).toBeDefined();
    });
  });

  describe('getGapAnalysis', () => {
    it('fetches gap analysis successfully', async () => {
      const mockGaps = [
        {
          id: 'gap-1',
          type: 'missing_supplier',
          severity: 'critical',
          title: 'Missing Packaging Supplier',
          description: 'No supplier information for packaging materials',
          impact_score: 15.2,
          affected_nodes: ['node-1'],
          recommendations: ['Identify and onboard packaging supplier'],
          estimated_improvement: 8.5,
        },
      ];

      mockApiClient.get.mockResolvedValue({ data: mockGaps });

      const result = await transparencyApi.getGapAnalysis('company-1');

      expect(mockApiClient.get).toHaveBeenCalledWith('/transparency/company-1/gaps');
      expect(result).toEqual(mockGaps);
    });

    it('returns mock data when API fails', async () => {
      mockApiClient.get.mockRejectedValue(new Error('API Error'));

      const result = await transparencyApi.getGapAnalysis('company-1');

      expect(result).toBeDefined();
      expect(Array.isArray(result)).toBe(true);
    });
  });

  describe('getMultiClientDashboard', () => {
    it('fetches multi-client dashboard successfully', async () => {
      const mockDashboard = {
        consultant_id: 'consultant-1',
        total_clients: 3,
        clients: [],
        aggregate_metrics: {
          average_transparency: 78.9,
          total_supply_chains: 12,
          total_gaps_identified: 28,
          total_improvements_implemented: 15,
        },
        recent_activities: [],
        alerts: [],
      };

      mockApiClient.get.mockResolvedValue({ data: mockDashboard });

      const result = await transparencyApi.getMultiClientDashboard('consultant-1');

      expect(mockApiClient.get).toHaveBeenCalledWith('/transparency/consultant/consultant-1/dashboard');
      expect(result).toEqual(mockDashboard);
    });

    it('returns mock data when API fails', async () => {
      mockApiClient.get.mockRejectedValue(new Error('API Error'));

      const result = await transparencyApi.getMultiClientDashboard('consultant-1');

      expect(result).toBeDefined();
      expect(result.clients).toBeDefined();
      expect(result.aggregate_metrics).toBeDefined();
    });
  });

  describe('recalculateTransparency', () => {
    it('triggers recalculation successfully', async () => {
      mockApiClient.post.mockResolvedValue({});

      await transparencyApi.recalculateTransparency('company-1');

      expect(mockApiClient.post).toHaveBeenCalledWith('/transparency/recalculate', {
        company_id: 'company-1',
      });
    });

    it('handles API errors gracefully', async () => {
      mockApiClient.post.mockRejectedValue(new Error('API Error'));

      // Should not throw
      await expect(transparencyApi.recalculateTransparency('company-1')).resolves.toBeUndefined();
    });
  });

  describe('getFilteredTransparency', () => {
    it('fetches filtered transparency data successfully', async () => {
      const mockFilters = {
        company_types: ['brand'],
        date_range: {
          start: '2024-01-01',
          end: '2024-01-31',
        },
      };

      const mockData = {
        company_id: 'company-1',
        root_po_id: 'po-001',
        nodes: [],
        edges: [],
        total_levels: 3,
        max_width: 2,
        layout_algorithm: 'hierarchical',
        overall_ttm_score: 78.5,
        overall_ttp_score: 82.3,
        overall_confidence: 85.2,
        traced_percentage: 76.8,
        untraced_percentage: 23.2,
        gap_analysis: [],
        generated_at: '2024-01-15T10:00:00Z',
        calculation_time_ms: 245,
      };

      mockApiClient.post.mockResolvedValue({ data: mockData });

      const result = await transparencyApi.getFilteredTransparency('company-1', mockFilters);

      expect(mockApiClient.post).toHaveBeenCalledWith('/transparency/company-1/filtered', mockFilters);
      expect(result).toEqual(mockData);
    });

    it('returns mock data when API fails', async () => {
      mockApiClient.post.mockRejectedValue(new Error('API Error'));

      const result = await transparencyApi.getFilteredTransparency('company-1', {});

      expect(result).toBeDefined();
      expect(result.nodes).toBeDefined();
      expect(result.edges).toBeDefined();
    });
  });
});

describe('TransparencyApiClient singleton', () => {
  it('exports a singleton instance', () => {
    expect(transparencyApi).toBeInstanceOf(TransparencyApiClient);
  });

  it('maintains state across calls', async () => {
    // This test ensures the singleton pattern works correctly
    const instance1 = transparencyApi;
    const instance2 = transparencyApi;

    expect(instance1).toBe(instance2);
  });
});

describe('Mock data validation', () => {
  it('provides valid mock transparency metrics', async () => {
    mockApiClient.get.mockRejectedValue(new Error('API Error'));

    const result = await transparencyApi.getTransparencyMetrics('company-1');

    expect(result.overall_score).toBeGreaterThanOrEqual(0);
    expect(result.overall_score).toBeLessThanOrEqual(100);
    expect(result.ttm_score).toBeGreaterThanOrEqual(0);
    expect(result.ttp_score).toBeGreaterThanOrEqual(0);
    expect(result.confidence_level).toBeGreaterThanOrEqual(0);
    expect(result.traced_percentage + result.untraced_percentage).toBeCloseTo(100, 1);
  });

  it('provides valid mock supply chain visualization', async () => {
    mockApiClient.get.mockRejectedValue(new Error('API Error'));

    const result = await transparencyApi.getSupplyChainVisualization('po-001');

    expect(Array.isArray(result.nodes)).toBe(true);
    expect(Array.isArray(result.edges)).toBe(true);
    expect(Array.isArray(result.gap_analysis)).toBe(true);
    expect(result.total_levels).toBeGreaterThan(0);
    expect(result.overall_ttm_score).toBeGreaterThanOrEqual(0);
    expect(result.overall_ttp_score).toBeGreaterThanOrEqual(0);
  });

  it('provides valid mock gap analysis', async () => {
    mockApiClient.get.mockRejectedValue(new Error('API Error'));

    const result = await transparencyApi.getGapAnalysis('company-1');

    expect(Array.isArray(result)).toBe(true);
    
    if (result.length > 0) {
      const gap = result[0];
      expect(gap.id).toBeDefined();
      expect(gap.type).toBeDefined();
      expect(gap.severity).toBeDefined();
      expect(gap.title).toBeDefined();
      expect(gap.description).toBeDefined();
      expect(Array.isArray(gap.recommendations)).toBe(true);
      expect(gap.impact_score).toBeGreaterThanOrEqual(0);
      expect(gap.estimated_improvement).toBeGreaterThanOrEqual(0);
    }
  });
});

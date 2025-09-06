/**
 * Tests for ViralCascadeAnalytics component
 */
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ViralCascadeAnalytics from '../ViralCascadeAnalytics';
import { onboardingApi } from '../../../lib/onboardingApi';
import { ViralCascadeMetrics } from '../../../types/onboarding';

// Mock the onboarding API
jest.mock('../../../lib/onboardingApi', () => ({
  onboardingApi: {
    getViralCascadeMetrics: jest.fn(),
  },
}));

// Mock Recharts components
jest.mock('recharts', () => ({
  LineChart: ({ children }: any) => <div data-testid="line-chart">{children}</div>,
  Line: () => <div data-testid="line" />,
  AreaChart: ({ children }: any) => <div data-testid="area-chart">{children}</div>,
  Area: () => <div data-testid="area" />,
  BarChart: ({ children }: any) => <div data-testid="bar-chart">{children}</div>,
  Bar: () => <div data-testid="bar" />,
  PieChart: ({ children }: any) => <div data-testid="pie-chart">{children}</div>,
  Pie: () => <div data-testid="pie" />,
  Cell: () => <div data-testid="cell" />,
  XAxis: () => <div data-testid="x-axis" />,
  YAxis: () => <div data-testid="y-axis" />,
  CartesianGrid: () => <div data-testid="cartesian-grid" />,
  Tooltip: () => <div data-testid="tooltip" />,
  Legend: () => <div data-testid="legend" />,
  ResponsiveContainer: ({ children }: any) => <div data-testid="responsive-container">{children}</div>,
  FunnelChart: ({ children }: any) => <div data-testid="funnel-chart">{children}</div>,
  Funnel: () => <div data-testid="funnel" />,
  LabelList: () => <div data-testid="label-list" />,
}));

const mockOnboardingApi = onboardingApi as jest.Mocked<typeof onboardingApi>;

// Mock data
const mockMetrics: ViralCascadeMetrics = {
  total_invitations_sent: 156,
  total_companies_onboarded: 89,
  conversion_rate: 57.1,
  average_time_to_onboard: 3.2,
  cascade_levels: [
    { level: 1, companies_invited: 45, companies_onboarded: 32, conversion_rate: 71.1, average_time_to_onboard: 2.1 },
    { level: 2, companies_invited: 67, companies_onboarded: 38, conversion_rate: 56.7, average_time_to_onboard: 3.5 },
    { level: 3, companies_invited: 44, companies_onboarded: 19, conversion_rate: 43.2, average_time_to_onboard: 4.8 },
  ],
  top_inviters: [
    {
      company_id: 'company-1',
      company_name: 'EcoFashion Co.',
      company_type: 'brand',
      invitations_sent: 23,
      successful_onboardings: 18,
      conversion_rate: 78.3,
      cascade_impact: 45,
    },
  ],
  onboarding_funnel: [
    { step: 'invitation_sent', companies_entered: 156, companies_completed: 156, completion_rate: 100, average_time_spent: 0, drop_off_rate: 0 },
    { step: 'invitation_opened', companies_entered: 156, companies_completed: 134, completion_rate: 85.9, average_time_spent: 0.5, drop_off_rate: 14.1 },
    { step: 'registration_started', companies_entered: 134, companies_completed: 112, completion_rate: 83.6, average_time_spent: 15.2, drop_off_rate: 16.4 },
    { step: 'company_info_completed', companies_entered: 112, companies_completed: 98, completion_rate: 87.5, average_time_spent: 25.8, drop_off_rate: 12.5 },
    { step: 'onboarding_completed', companies_entered: 98, companies_completed: 89, completion_rate: 90.8, average_time_spent: 45.6, drop_off_rate: 9.2 },
  ],
  geographic_distribution: [
    { country: 'United States', companies_count: 45, invitations_sent: 78, onboarding_rate: 57.7 },
    { country: 'Canada', companies_count: 23, invitations_sent: 34, onboarding_rate: 67.6 },
    { country: 'Mexico', companies_count: 21, invitations_sent: 44, onboarding_rate: 47.7 },
  ],
  company_type_distribution: [
    { company_type: 'originator', count: 42, percentage: 47.2, average_onboarding_time: 2.8 },
    { company_type: 'processor', count: 31, percentage: 34.8, average_onboarding_time: 3.5 },
    { company_type: 'brand', count: 16, percentage: 18.0, average_onboarding_time: 4.2 },
  ],
  time_series_data: [
    { date: '2024-01-01', invitations_sent: 12, companies_onboarded: 8, cumulative_companies: 8, conversion_rate: 66.7 },
    { date: '2024-01-08', invitations_sent: 18, companies_onboarded: 11, cumulative_companies: 19, conversion_rate: 61.1 },
    { date: '2024-01-15', invitations_sent: 23, companies_onboarded: 15, cumulative_companies: 34, conversion_rate: 65.2 },
  ],
};

describe('ViralCascadeAnalytics', () => {
  const companyId = 'company-1';

  beforeEach(() => {
    jest.clearAllMocks();
    mockOnboardingApi.getViralCascadeMetrics.mockResolvedValue(mockMetrics);
  });

  const renderComponent = (props = {}) => {
    return render(
      <ViralCascadeAnalytics
        companyId={companyId}
        {...props}
      />
    );
  };

  describe('Component Rendering', () => {
    it('renders the component with header', async () => {
      renderComponent();
      
      expect(screen.getByText('Viral Cascade Analytics')).toBeInTheDocument();
      expect(screen.getByText('Track supplier onboarding growth and viral expansion')).toBeInTheDocument();
      expect(screen.getByText('Refresh')).toBeInTheDocument();
    });

    it('shows loading state initially', () => {
      renderComponent();
      
      expect(screen.getByText('Loading analytics...')).toBeInTheDocument();
    });

    it('displays analytics after loading', async () => {
      renderComponent();
      
      await waitFor(() => {
        expect(screen.getByText('156')).toBeInTheDocument(); // Total invitations
        expect(screen.getByText('89')).toBeInTheDocument(); // Total onboarded
        expect(screen.getByText('57.1%')).toBeInTheDocument(); // Conversion rate
        expect(screen.getByText('3.2d')).toBeInTheDocument(); // Avg time
      });
    });
  });

  describe('Tab Navigation', () => {
    it('renders all tab options', async () => {
      renderComponent();
      
      await waitFor(() => {
        expect(screen.getByText('Overview')).toBeInTheDocument();
        expect(screen.getByText('Cascade Levels')).toBeInTheDocument();
        expect(screen.getByText('Funnel')).toBeInTheDocument();
        expect(screen.getByText('Geographic')).toBeInTheDocument();
      });
    });

    it('switches between tabs', async () => {
      const user = userEvent.setup();
      renderComponent();
      
      await waitFor(() => {
        expect(screen.getByText('Overview')).toBeInTheDocument();
      });
      
      // Click on Cascade Levels tab
      await user.click(screen.getByText('Cascade Levels'));
      
      expect(screen.getByText('Cascade Levels Performance')).toBeInTheDocument();
    });

    it('shows active tab styling', async () => {
      const user = userEvent.setup();
      renderComponent();
      
      await waitFor(() => {
        const overviewTab = screen.getByText('Overview');
        expect(overviewTab).toHaveClass('text-primary-600');
      });
      
      // Click on Funnel tab
      await user.click(screen.getByText('Funnel'));
      
      const funnelTab = screen.getByText('Funnel');
      expect(funnelTab).toHaveClass('text-primary-600');
    });
  });

  describe('Overview Tab', () => {
    it('displays key metrics cards', async () => {
      renderComponent();
      
      await waitFor(() => {
        expect(screen.getByText('156')).toBeInTheDocument(); // Total invitations
        expect(screen.getByText('89')).toBeInTheDocument(); // Total onboarded
        expect(screen.getByText('57.1%')).toBeInTheDocument(); // Conversion rate
        expect(screen.getByText('3.2d')).toBeInTheDocument(); // Avg time
      });
    });

    it('shows growth trend chart', async () => {
      renderComponent();
      
      await waitFor(() => {
        expect(screen.getByTestId('area-chart')).toBeInTheDocument();
        expect(screen.getByText('Growth Trend')).toBeInTheDocument();
      });
    });

    it('displays top inviters', async () => {
      renderComponent();
      
      await waitFor(() => {
        expect(screen.getByText('Top Inviters')).toBeInTheDocument();
        expect(screen.getByText('EcoFashion Co.')).toBeInTheDocument();
        expect(screen.getByText('brand')).toBeInTheDocument();
        expect(screen.getByText('18')).toBeInTheDocument(); // Successful onboardings
        expect(screen.getByText('78.3% conversion')).toBeInTheDocument();
      });
    });
  });

  describe('Cascade Levels Tab', () => {
    it('displays cascade performance chart', async () => {
      const user = userEvent.setup();
      renderComponent();
      
      await waitFor(() => {
        expect(screen.getByText('Overview')).toBeInTheDocument();
      });
      
      await user.click(screen.getByText('Cascade Levels'));
      
      expect(screen.getByText('Cascade Levels Performance')).toBeInTheDocument();
      expect(screen.getByTestId('bar-chart')).toBeInTheDocument();
    });

    it('shows cascade level cards', async () => {
      const user = userEvent.setup();
      renderComponent();
      
      await waitFor(() => {
        expect(screen.getByText('Overview')).toBeInTheDocument();
      });
      
      await user.click(screen.getByText('Cascade Levels'));
      
      expect(screen.getByText('Level 1')).toBeInTheDocument();
      expect(screen.getByText('Level 2')).toBeInTheDocument();
      expect(screen.getByText('Level 3')).toBeInTheDocument();
    });
  });

  describe('Funnel Tab', () => {
    it('displays onboarding funnel steps', async () => {
      const user = userEvent.setup();
      renderComponent();
      
      await waitFor(() => {
        expect(screen.getByText('Overview')).toBeInTheDocument();
      });
      
      await user.click(screen.getByText('Funnel'));
      
      expect(screen.getByText('Onboarding Funnel')).toBeInTheDocument();
      expect(screen.getByText('Invitation sent')).toBeInTheDocument();
      expect(screen.getByText('Invitation opened')).toBeInTheDocument();
      expect(screen.getByText('Registration started')).toBeInTheDocument();
    });

    it('shows completion rates and drop-off rates', async () => {
      const user = userEvent.setup();
      renderComponent();
      
      await waitFor(() => {
        expect(screen.getByText('Overview')).toBeInTheDocument();
      });
      
      await user.click(screen.getByText('Funnel'));
      
      expect(screen.getByText('100.0% completion')).toBeInTheDocument();
      expect(screen.getByText('85.9% completion')).toBeInTheDocument();
      expect(screen.getByText('-22 dropped off (14.1%)')).toBeInTheDocument();
    });
  });

  describe('Geographic Tab', () => {
    it('displays geographic distribution', async () => {
      const user = userEvent.setup();
      renderComponent();
      
      await waitFor(() => {
        expect(screen.getByText('Overview')).toBeInTheDocument();
      });
      
      await user.click(screen.getByText('Geographic'));
      
      expect(screen.getByText('Geographic Distribution')).toBeInTheDocument();
      expect(screen.getByText('United States')).toBeInTheDocument();
      expect(screen.getByText('Canada')).toBeInTheDocument();
      expect(screen.getByText('Mexico')).toBeInTheDocument();
    });

    it('shows company type distribution chart', async () => {
      const user = userEvent.setup();
      renderComponent();
      
      await waitFor(() => {
        expect(screen.getByText('Overview')).toBeInTheDocument();
      });
      
      await user.click(screen.getByText('Geographic'));
      
      expect(screen.getByText('Company Type Distribution')).toBeInTheDocument();
      expect(screen.getByTestId('pie-chart')).toBeInTheDocument();
    });
  });

  describe('Data Refresh', () => {
    it('refreshes data when refresh button is clicked', async () => {
      const user = userEvent.setup();
      renderComponent();
      
      await waitFor(() => {
        expect(mockOnboardingApi.getViralCascadeMetrics).toHaveBeenCalledTimes(1);
      });
      
      const refreshButton = screen.getByText('Refresh');
      await user.click(refreshButton);
      
      expect(mockOnboardingApi.getViralCascadeMetrics).toHaveBeenCalledTimes(2);
    });

    it('calls API with correct company ID', async () => {
      renderComponent();
      
      await waitFor(() => {
        expect(mockOnboardingApi.getViralCascadeMetrics).toHaveBeenCalledWith(companyId);
      });
    });

    it('calls API without company ID when not provided', async () => {
      renderComponent({ companyId: undefined });
      
      await waitFor(() => {
        expect(mockOnboardingApi.getViralCascadeMetrics).toHaveBeenCalledWith(undefined);
      });
    });
  });

  describe('Error Handling', () => {
    it('shows error state when API fails', async () => {
      mockOnboardingApi.getViralCascadeMetrics.mockRejectedValue(new Error('API Error'));
      
      renderComponent();
      
      await waitFor(() => {
        expect(screen.getByText('No Data Available')).toBeInTheDocument();
        expect(screen.getByText('Unable to load viral cascade analytics.')).toBeInTheDocument();
      });
    });

    it('handles missing data gracefully', async () => {
      mockOnboardingApi.getViralCascadeMetrics.mockResolvedValue(null as any);
      
      renderComponent();
      
      await waitFor(() => {
        expect(screen.getByText('No Data Available')).toBeInTheDocument();
      });
    });
  });

  describe('Charts Rendering', () => {
    it('renders area chart for growth trend', async () => {
      renderComponent();
      
      await waitFor(() => {
        expect(screen.getByTestId('area-chart')).toBeInTheDocument();
        expect(screen.getByTestId('area')).toBeInTheDocument();
      });
    });

    it('renders bar chart for cascade levels', async () => {
      const user = userEvent.setup();
      renderComponent();
      
      await waitFor(() => {
        expect(screen.getByText('Overview')).toBeInTheDocument();
      });
      
      await user.click(screen.getByText('Cascade Levels'));
      
      expect(screen.getByTestId('bar-chart')).toBeInTheDocument();
      expect(screen.getByTestId('bar')).toBeInTheDocument();
    });

    it('renders pie chart for company type distribution', async () => {
      const user = userEvent.setup();
      renderComponent();
      
      await waitFor(() => {
        expect(screen.getByText('Overview')).toBeInTheDocument();
      });
      
      await user.click(screen.getByText('Geographic'));
      
      expect(screen.getByTestId('pie-chart')).toBeInTheDocument();
      expect(screen.getByTestId('pie')).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('has proper ARIA labels and roles', async () => {
      renderComponent();
      
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /refresh/i })).toBeInTheDocument();
      });
    });

    it('supports keyboard navigation for tabs', async () => {
      const user = userEvent.setup();
      renderComponent();
      
      await waitFor(() => {
        expect(screen.getByText('Overview')).toBeInTheDocument();
      });
      
      // Tab navigation should work
      await user.tab();
      await user.tab();
      
      // Should be able to navigate to other tabs
      const cascadeTab = screen.getByText('Cascade Levels');
      cascadeTab.focus();
      await user.keyboard('{Enter}');
      
      expect(screen.getByText('Cascade Levels Performance')).toBeInTheDocument();
    });
  });
});

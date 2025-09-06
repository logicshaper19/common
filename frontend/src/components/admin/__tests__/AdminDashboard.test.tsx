/**
 * Admin Dashboard Tests
 * Comprehensive test suite for admin dashboard functionality
 */
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { AdminDashboard } from '../AdminDashboard';
import { adminApi } from '../../../api/admin';

// Mock the admin API
jest.mock('../../../api/admin', () => ({
  adminApi: {
    getDashboardData: jest.fn(),
  },
}));

// Mock child components
jest.mock('../ProductCatalogManagement', () => ({
  ProductCatalogManagement: () => <div data-testid="product-catalog">Product Catalog Management</div>,
}));

jest.mock('../UserCompanyManagement', () => ({
  UserCompanyManagement: () => <div data-testid="user-company">User Company Management</div>,
}));

jest.mock('../SupportTicketSystem', () => ({
  SupportTicketSystem: () => <div data-testid="support-tickets">Support Ticket System</div>,
}));

jest.mock('../AuditLogViewer', () => ({
  AuditLogViewer: () => <div data-testid="audit-logs">Audit Log Viewer</div>,
}));

jest.mock('../SystemMonitoring', () => ({
  SystemMonitoring: () => <div data-testid="system-monitoring">System Monitoring</div>,
}));

const mockDashboardData = {
  overview: {
    total_users: 1247,
    active_users: 892,
    total_companies: 156,
    active_companies: 134,
    total_products: 89,
    total_purchase_orders: 2341,
    open_tickets: 12,
    critical_alerts: 0,
    system_uptime: 99.95,
    last_backup: '2024-01-20T06:00:00Z',
  },
  recent_activity: [
    {
      id: 'audit-1',
      timestamp: '2024-01-20T10:30:00Z',
      user_id: 'user-1',
      user_name: 'John Smith',
      user_email: 'john@example.com',
      company_id: 'company-1',
      company_name: 'ACME Corp',
      action: 'create',
      resource_type: 'product',
      resource_id: 'prod-1',
      resource_name: 'Palm Oil',
      details: {},
      ip_address: '192.168.1.1',
      user_agent: 'Mozilla/5.0',
      session_id: 'sess-1',
      risk_level: 'low' as const,
      success: true,
    },
  ],
  system_health: {
    status: 'healthy' as const,
    timestamp: '2024-01-20T12:00:00Z',
    services: [],
    metrics: {
      cpu_usage: 45.2,
      memory_usage: 67.8,
      disk_usage: 34.5,
      active_connections: 156,
      requests_per_minute: 2340,
      error_rate: 0.02,
      average_response_time: 245,
      database_connections: 12,
      queue_size: 3,
    },
    alerts: [],
    uptime: 99.95,
    version: '1.2.3',
  },
  alerts: [],
  user_stats: {
    new_users_today: 8,
    new_users_week: 34,
    active_sessions: 156,
    login_failures_today: 3,
    users_by_role: {
      admin: 5,
      buyer: 456,
      seller: 378,
      viewer: 234,
      support: 12,
    },
    users_by_company_type: {
      brand: 234,
      processor: 345,
      originator: 456,
      trader: 123,
      plantation: 89,
    },
  },
  company_stats: {
    new_companies_today: 2,
    new_companies_week: 8,
    companies_by_tier: {
      free: 45,
      basic: 67,
      premium: 34,
      enterprise: 10,
    },
    companies_by_compliance: {
      compliant: 134,
      warning: 15,
      non_compliant: 5,
      pending_review: 2,
    },
    average_transparency_score: 87.3,
  },
  support_stats: {
    open_tickets: 12,
    tickets_today: 5,
    tickets_week: 23,
    average_response_time: 2.5,
    tickets_by_priority: {
      low: 3,
      medium: 6,
      high: 2,
      urgent: 1,
      critical: 0,
    },
    tickets_by_category: {
      technical: 5,
      billing: 2,
      feature_request: 3,
      bug_report: 1,
      account: 1,
      compliance: 0,
      other: 0,
    },
    satisfaction_rating: 4.6,
  },
};

describe('AdminDashboard', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders admin dashboard with navigation tabs', () => {
    render(<AdminDashboard />);
    
    expect(screen.getByText('Admin Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Overview')).toBeInTheDocument();
    expect(screen.getByText('Product Catalog')).toBeInTheDocument();
    expect(screen.getByText('Users & Companies')).toBeInTheDocument();
    expect(screen.getByText('Support')).toBeInTheDocument();
    expect(screen.getByText('Audit Logs')).toBeInTheDocument();
    expect(screen.getByText('System')).toBeInTheDocument();
  });

  it('loads and displays dashboard data on overview tab', async () => {
    (adminApi.getDashboardData as any).mockResolvedValue(mockDashboardData);
    
    render(<AdminDashboard />);
    
    await waitFor(() => {
      expect(screen.getByText('1.2K')).toBeInTheDocument(); // Total users formatted
      expect(screen.getByText('156')).toBeInTheDocument(); // Total companies
      expect(screen.getByText('12')).toBeInTheDocument(); // Open tickets
      expect(screen.getByText('Healthy')).toBeInTheDocument(); // System health
    });
    
    expect(adminApi.getDashboardData).toHaveBeenCalledTimes(1);
  });

  it('displays loading state while fetching dashboard data', () => {
    (adminApi.getDashboardData as any).mockImplementation(() => new Promise(() => {}));
    
    render(<AdminDashboard />);
    
    expect(screen.getByText('Loading dashboard data...')).toBeInTheDocument();
  });

  it('displays error state when dashboard data fails to load', async () => {
    (adminApi.getDashboardData as any).mockRejectedValue(new Error('API Error'));
    
    render(<AdminDashboard />);
    
    await waitFor(() => {
      expect(screen.getByText('Failed to load dashboard data')).toBeInTheDocument();
    });
  });

  it('switches to product catalog tab', async () => {
    render(<AdminDashboard />);
    
    fireEvent.click(screen.getByText('Product Catalog'));
    
    await waitFor(() => {
      expect(screen.getByTestId('product-catalog')).toBeInTheDocument();
    });
  });

  it('switches to users & companies tab', async () => {
    render(<AdminDashboard />);
    
    fireEvent.click(screen.getByText('Users & Companies'));
    
    await waitFor(() => {
      expect(screen.getByTestId('user-company')).toBeInTheDocument();
    });
  });

  it('switches to support tab', async () => {
    render(<AdminDashboard />);
    
    fireEvent.click(screen.getByText('Support'));
    
    await waitFor(() => {
      expect(screen.getByTestId('support-tickets')).toBeInTheDocument();
    });
  });

  it('switches to audit logs tab', async () => {
    render(<AdminDashboard />);
    
    fireEvent.click(screen.getByText('Audit Logs'));
    
    await waitFor(() => {
      expect(screen.getByTestId('audit-logs')).toBeInTheDocument();
    });
  });

  it('switches to system monitoring tab', async () => {
    render(<AdminDashboard />);
    
    fireEvent.click(screen.getByText('System'));
    
    await waitFor(() => {
      expect(screen.getByTestId('system-monitoring')).toBeInTheDocument();
    });
  });

  it('displays recent activity when dashboard data is loaded', async () => {
    (adminApi.getDashboardData as any).mockResolvedValue(mockDashboardData);
    
    render(<AdminDashboard />);
    
    await waitFor(() => {
      expect(screen.getByText('Recent Activity')).toBeInTheDocument();
      expect(screen.getByText('John Smith')).toBeInTheDocument();
      expect(screen.getByText('create')).toBeInTheDocument();
      expect(screen.getByText('product')).toBeInTheDocument();
    });
  });

  it('displays system alerts section', async () => {
    const dataWithAlerts = {
      ...mockDashboardData,
      alerts: [
        {
          id: 'alert-1',
          type: 'performance' as const,
          severity: 'warning' as const,
          title: 'High CPU Usage',
          description: 'CPU usage is above 80%',
          created_at: '2024-01-20T10:00:00Z',
          metadata: {},
        },
      ],
    };
    
    (adminApi.getDashboardData as any).mockResolvedValue(dataWithAlerts);
    
    render(<AdminDashboard />);
    
    await waitFor(() => {
      expect(screen.getByText('System Alerts')).toBeInTheDocument();
      expect(screen.getByText('High CPU Usage')).toBeInTheDocument();
      expect(screen.getByText('CPU usage is above 80%')).toBeInTheDocument();
    });
  });

  it('displays statistics grid with user, company, and support stats', async () => {
    (adminApi.getDashboardData as any).mockResolvedValue(mockDashboardData);
    
    render(<AdminDashboard />);
    
    await waitFor(() => {
      expect(screen.getByText('User Statistics')).toBeInTheDocument();
      expect(screen.getByText('Company Statistics')).toBeInTheDocument();
      expect(screen.getByText('Support Statistics')).toBeInTheDocument();
      
      expect(screen.getByText('156')).toBeInTheDocument(); // Active sessions
      expect(screen.getByText('87.3%')).toBeInTheDocument(); // Avg transparency
      expect(screen.getByText('2.5h')).toBeInTheDocument(); // Avg response time
    });
  });

  it('formats large numbers correctly', async () => {
    const dataWithLargeNumbers = {
      ...mockDashboardData,
      overview: {
        ...mockDashboardData.overview,
        total_users: 1500000, // Should format to 1.5M
        total_companies: 2500, // Should format to 2.5K
      },
    };
    
    (adminApi.getDashboardData as any).mockResolvedValue(dataWithLargeNumbers);
    
    render(<AdminDashboard />);
    
    await waitFor(() => {
      expect(screen.getByText('1.5M')).toBeInTheDocument();
      expect(screen.getByText('2.5K')).toBeInTheDocument();
    });
  });

  it('shows no alerts message when there are no system alerts', async () => {
    (adminApi.getDashboardData as any).mockResolvedValue(mockDashboardData);
    
    render(<AdminDashboard />);
    
    await waitFor(() => {
      expect(screen.getByText('No active alerts')).toBeInTheDocument();
    });
  });

  it('applies correct styling to active tab', async () => {
    render(<AdminDashboard />);
    
    const overviewTab = screen.getByText('Overview').closest('button');
    const productTab = screen.getByText('Product Catalog').closest('button');
    
    expect(overviewTab).toHaveClass('border-primary-500', 'text-primary-600');
    expect(productTab).toHaveClass('border-transparent', 'text-gray-500');
    
    fireEvent.click(screen.getByText('Product Catalog'));
    
    await waitFor(() => {
      expect(productTab).toHaveClass('border-primary-500', 'text-primary-600');
    });
  });

  it('only loads dashboard data when overview tab is active', async () => {
    (adminApi.getDashboardData as any).mockResolvedValue(mockDashboardData);
    
    render(<AdminDashboard />);
    
    // Should load data initially (overview tab is default)
    await waitFor(() => {
      expect(adminApi.getDashboardData).toHaveBeenCalledTimes(1);
    });
    
    // Switch to another tab
    fireEvent.click(screen.getByText('Product Catalog'));
    
    // Should not load data again
    expect(adminApi.getDashboardData).toHaveBeenCalledTimes(1);
    
    // Switch back to overview
    fireEvent.click(screen.getByText('Overview'));
    
    // Should load data again
    await waitFor(() => {
      expect(adminApi.getDashboardData).toHaveBeenCalledTimes(2);
    });
  });
});

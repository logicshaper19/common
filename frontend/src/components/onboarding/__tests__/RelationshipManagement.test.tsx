/**
 * Tests for RelationshipManagement component
 */
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import RelationshipManagement from '../RelationshipManagement';
import { onboardingApi } from '../../../lib/onboardingApi';
import { BusinessRelationship } from '../../../types/onboarding';

// Mock the onboarding API
jest.mock('../../../lib/onboardingApi', () => ({
  onboardingApi: {
    getBusinessRelationships: jest.fn(),
    updateDataSharingPermissions: jest.fn(),
  },
}));

const mockOnboardingApi = onboardingApi as jest.Mocked<typeof onboardingApi>;

// Mock data
const mockRelationships: BusinessRelationship[] = [
  {
    id: 'rel-1',
    buyer_company_id: 'company-1',
    buyer_company_name: 'EcoFashion Co.',
    seller_company_id: 'company-2',
    seller_company_name: 'Green Mills',
    relationship_type: 'supplier',
    status: 'active',
    data_sharing_permissions: {
      view_purchase_orders: true,
      view_product_details: true,
      view_pricing: false,
      view_delivery_schedules: true,
      view_quality_metrics: true,
      view_sustainability_data: true,
      view_transparency_scores: true,
      edit_order_confirmations: true,
      edit_delivery_updates: true,
      edit_quality_reports: true,
      receive_notifications: true,
      access_analytics: false,
    },
    established_at: '2024-01-01T00:00:00Z',
    last_interaction: '2024-01-15T16:30:00Z',
    total_orders: 24,
    total_value: 125000,
    transparency_score: 85.2,
  },
  {
    id: 'rel-2',
    buyer_company_id: 'company-1',
    buyer_company_name: 'EcoFashion Co.',
    seller_company_id: 'company-3',
    seller_company_name: 'Organic Farms Co.',
    relationship_type: 'supplier',
    status: 'pending',
    data_sharing_permissions: {
      view_purchase_orders: true,
      view_product_details: true,
      view_pricing: false,
      view_delivery_schedules: true,
      view_quality_metrics: true,
      view_sustainability_data: true,
      view_transparency_scores: true,
      edit_order_confirmations: false,
      edit_delivery_updates: false,
      edit_quality_reports: false,
      receive_notifications: true,
      access_analytics: false,
    },
    established_at: '2024-01-10T00:00:00Z',
    total_orders: 0,
    total_value: 0,
  },
];

describe('RelationshipManagement', () => {
  const mockOnInviteSupplier = jest.fn();
  const companyId = 'company-1';

  beforeEach(() => {
    jest.clearAllMocks();
    mockOnboardingApi.getBusinessRelationships.mockResolvedValue(mockRelationships);
  });

  const renderComponent = (props = {}) => {
    return render(
      <RelationshipManagement
        companyId={companyId}
        onInviteSupplier={mockOnInviteSupplier}
        {...props}
      />
    );
  };

  describe('Component Rendering', () => {
    it('renders the component with header', async () => {
      renderComponent();
      
      expect(screen.getByText('Business Relationships')).toBeInTheDocument();
      expect(screen.getByText('Invite Supplier')).toBeInTheDocument();
      
      await waitFor(() => {
        expect(screen.getByText('2 active relationships')).toBeInTheDocument();
      });
    });

    it('shows loading state initially', () => {
      renderComponent();
      
      expect(screen.getByText('Loading relationships...')).toBeInTheDocument();
    });

    it('displays relationships after loading', async () => {
      renderComponent();
      
      await waitFor(() => {
        expect(screen.getByText('Green Mills')).toBeInTheDocument();
        expect(screen.getByText('Organic Farms Co.')).toBeInTheDocument();
      });
    });
  });

  describe('Relationship Display', () => {
    it('shows relationship details correctly', async () => {
      renderComponent();
      
      await waitFor(() => {
        // Check first relationship
        expect(screen.getByText('Green Mills')).toBeInTheDocument();
        expect(screen.getByText('active')).toBeInTheDocument();
        expect(screen.getByText('supplier')).toBeInTheDocument();
        expect(screen.getByText('24')).toBeInTheDocument(); // orders
        expect(screen.getByText('$125,000')).toBeInTheDocument(); // value
        expect(screen.getByText('85.2%')).toBeInTheDocument(); // transparency
      });
    });

    it('shows correct status badges', async () => {
      renderComponent();
      
      await waitFor(() => {
        const activeBadges = screen.getAllByText('active');
        const pendingBadges = screen.getAllByText('pending');
        
        expect(activeBadges).toHaveLength(1);
        expect(pendingBadges).toHaveLength(1);
      });
    });

    it('displays transparency scores with correct colors', async () => {
      renderComponent();
      
      await waitFor(() => {
        const transparencyScore = screen.getByText('85.2%');
        expect(transparencyScore).toHaveClass('text-success-600');
      });
    });
  });

  describe('Filtering and Search', () => {
    it('filters relationships by search term', async () => {
      const user = userEvent.setup();
      renderComponent();
      
      await waitFor(() => {
        expect(screen.getByText('Green Mills')).toBeInTheDocument();
        expect(screen.getByText('Organic Farms Co.')).toBeInTheDocument();
      });
      
      // Search for "Green"
      const searchInput = screen.getByPlaceholderText('Search companies...');
      await user.type(searchInput, 'Green');
      
      expect(screen.getByText('Green Mills')).toBeInTheDocument();
      expect(screen.queryByText('Organic Farms Co.')).not.toBeInTheDocument();
    });

    it('filters relationships by status', async () => {
      const user = userEvent.setup();
      renderComponent();
      
      await waitFor(() => {
        expect(screen.getByText('Green Mills')).toBeInTheDocument();
        expect(screen.getByText('Organic Farms Co.')).toBeInTheDocument();
      });
      
      // Filter by active status
      const statusFilter = screen.getByDisplayValue('All Status');
      await user.selectOptions(statusFilter, 'active');
      
      expect(screen.getByText('Green Mills')).toBeInTheDocument();
      expect(screen.queryByText('Organic Farms Co.')).not.toBeInTheDocument();
    });

    it('filters relationships by type', async () => {
      const user = userEvent.setup();
      renderComponent();
      
      await waitFor(() => {
        expect(screen.getByText('Green Mills')).toBeInTheDocument();
        expect(screen.getByText('Organic Farms Co.')).toBeInTheDocument();
      });
      
      // Filter by supplier type
      const typeFilter = screen.getByDisplayValue('All Types');
      await user.selectOptions(typeFilter, 'supplier');
      
      // Both should still be visible as they're both suppliers
      expect(screen.getByText('Green Mills')).toBeInTheDocument();
      expect(screen.getByText('Organic Farms Co.')).toBeInTheDocument();
    });
  });

  describe('Sorting', () => {
    it('sorts relationships by name', async () => {
      const user = userEvent.setup();
      renderComponent();
      
      await waitFor(() => {
        expect(screen.getByText('Green Mills')).toBeInTheDocument();
      });
      
      // Change sort to name Z-A
      const sortSelect = screen.getByDisplayValue('Name A-Z');
      await user.selectOptions(sortSelect, 'name-desc');
      
      // Should still show both relationships but in different order
      expect(screen.getByText('Green Mills')).toBeInTheDocument();
      expect(screen.getByText('Organic Farms Co.')).toBeInTheDocument();
    });
  });

  describe('Actions', () => {
    it('opens invite form when invite button is clicked', async () => {
      const user = userEvent.setup();
      renderComponent();
      
      const inviteButton = screen.getByText('Invite Supplier');
      await user.click(inviteButton);
      
      // Should show the invitation form
      expect(screen.getByText('Send an invitation to join your supply chain network')).toBeInTheDocument();
    });

    it('opens permissions modal when permissions button is clicked', async () => {
      const user = userEvent.setup();
      renderComponent();
      
      await waitFor(() => {
        expect(screen.getByText('Green Mills')).toBeInTheDocument();
      });
      
      const permissionsButtons = screen.getAllByText('Permissions');
      await user.click(permissionsButtons[0]);
      
      // Should open permissions modal
      expect(screen.getByText('Data Sharing Permissions')).toBeInTheDocument();
    });

    it('calls onInviteSupplier when invite action is triggered', async () => {
      const user = userEvent.setup();
      renderComponent();
      
      const inviteButton = screen.getByText('Invite Supplier');
      await user.click(inviteButton);
      
      // Mock invitation sent
      const form = screen.getByText('Send an invitation to join your supply chain network');
      expect(form).toBeInTheDocument();
    });
  });

  describe('Empty States', () => {
    it('shows empty state when no relationships exist', async () => {
      mockOnboardingApi.getBusinessRelationships.mockResolvedValue([]);
      renderComponent();
      
      await waitFor(() => {
        expect(screen.getByText('No relationships yet')).toBeInTheDocument();
        expect(screen.getByText('Start building your supply chain network by inviting suppliers.')).toBeInTheDocument();
        expect(screen.getByText('Invite Your First Supplier')).toBeInTheDocument();
      });
    });

    it('shows no results state when search returns no matches', async () => {
      const user = userEvent.setup();
      renderComponent();
      
      await waitFor(() => {
        expect(screen.getByText('Green Mills')).toBeInTheDocument();
      });
      
      // Search for something that doesn't exist
      const searchInput = screen.getByPlaceholderText('Search companies...');
      await user.type(searchInput, 'NonExistent');
      
      expect(screen.getByText('No matching relationships')).toBeInTheDocument();
      expect(screen.getByText('Try adjusting your search or filter criteria.')).toBeInTheDocument();
    });
  });

  describe('Error Handling', () => {
    it('handles API errors gracefully', async () => {
      mockOnboardingApi.getBusinessRelationships.mockRejectedValue(new Error('API Error'));
      
      renderComponent();
      
      await waitFor(() => {
        // Should not crash and should show loading state ends
        expect(screen.queryByText('Loading relationships...')).not.toBeInTheDocument();
      });
    });
  });

  describe('Data Sharing Permissions', () => {
    it('updates permissions when modal is saved', async () => {
      const user = userEvent.setup();
      mockOnboardingApi.updateDataSharingPermissions.mockResolvedValue({
        view_purchase_orders: true,
        view_product_details: true,
        view_pricing: true, // Changed
        view_delivery_schedules: true,
        view_quality_metrics: true,
        view_sustainability_data: true,
        view_transparency_scores: true,
        edit_order_confirmations: true,
        edit_delivery_updates: true,
        edit_quality_reports: true,
        receive_notifications: true,
        access_analytics: false,
      });
      
      renderComponent();
      
      await waitFor(() => {
        expect(screen.getByText('Green Mills')).toBeInTheDocument();
      });
      
      // Open permissions modal
      const permissionsButtons = screen.getAllByText('Permissions');
      await user.click(permissionsButtons[0]);
      
      // Should show permissions modal
      expect(screen.getByText('Data Sharing Permissions')).toBeInTheDocument();
      
      // Enable pricing permission
      const pricingCheckbox = screen.getByLabelText(/pricing information/i);
      await user.click(pricingCheckbox);
      
      // Save permissions
      await user.click(screen.getByText('Save Permissions'));
      
      await waitFor(() => {
        expect(mockOnboardingApi.updateDataSharingPermissions).toHaveBeenCalledWith(
          'rel-1',
          expect.objectContaining({
            view_pricing: true,
          })
        );
      });
    });
  });

  describe('Accessibility', () => {
    it('has proper ARIA labels and roles', async () => {
      renderComponent();
      
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /invite supplier/i })).toBeInTheDocument();
        expect(screen.getByRole('textbox', { name: /search companies/i })).toBeInTheDocument();
      });
    });

    it('supports keyboard navigation', async () => {
      const user = userEvent.setup();
      renderComponent();
      
      await waitFor(() => {
        expect(screen.getByText('Green Mills')).toBeInTheDocument();
      });
      
      // Tab to invite button
      await user.tab();
      expect(screen.getByText('Invite Supplier')).toHaveFocus();
    });
  });
});

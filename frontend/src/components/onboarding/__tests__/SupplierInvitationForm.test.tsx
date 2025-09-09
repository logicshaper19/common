/**
 * Tests for SupplierAddForm component
 */
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import SupplierAddForm from '../SupplierInvitationForm';
import { onboardingApi } from '../../../lib/onboardingApi';

// Mock the onboarding API
jest.mock('../../../lib/onboardingApi', () => ({
  onboardingApi: {
    sendSupplierInvitation: jest.fn(),
  },
}));

const mockOnboardingApi = onboardingApi as jest.Mocked<typeof onboardingApi>;

describe('SupplierAddForm', () => {
  const mockOnInvitationSent = jest.fn();
  const mockOnCancel = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  const renderComponent = (props = {}) => {
    return render(
      <SupplierAddForm
        onInvitationSent={mockOnInvitationSent}
        onCancel={mockOnCancel}
        {...props}
      />
    );
  };

  describe('Form Rendering', () => {
    it('renders the form with initial step', () => {
      renderComponent();
      
      expect(screen.getByText('Add Supplier')).toBeInTheDocument();
      expect(screen.getByLabelText(/supplier email/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/company name/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/company type/i)).toBeInTheDocument();
    });

    it('shows step progress indicator', () => {
      renderComponent();
      
      // Should show step 1 as active
      expect(screen.getByText('1')).toBeInTheDocument();
      expect(screen.getByText('Next')).toBeInTheDocument();
    });

    it('renders cancel button when onCancel is provided', () => {
      renderComponent();
      
      expect(screen.getByText('Cancel')).toBeInTheDocument();
    });

    it('does not render cancel button when onCancel is not provided', () => {
      renderComponent({ onCancel: undefined });
      
      expect(screen.queryByText('Cancel')).not.toBeInTheDocument();
    });
  });

  describe('Form Validation', () => {
    it('validates required fields on basic step', async () => {
      const user = userEvent.setup();
      renderComponent();
      
      // Try to proceed without filling required fields
      await user.click(screen.getByText('Next'));
      
      expect(screen.getByText('Email is required')).toBeInTheDocument();
      expect(screen.getByText('Company name is required')).toBeInTheDocument();
    });

    it('validates email format', async () => {
      const user = userEvent.setup();
      renderComponent();
      
      const emailInput = screen.getByLabelText(/supplier email/i);
      await user.type(emailInput, 'invalid-email');
      await user.click(screen.getByText('Next'));
      
      expect(screen.getByText('Invalid email format')).toBeInTheDocument();
    });

    it('allows proceeding with valid data', async () => {
      const user = userEvent.setup();
      renderComponent();
      
      // Fill in required fields
      await user.type(screen.getByLabelText(/supplier email/i), 'supplier@example.com');
      await user.type(screen.getByLabelText(/company name/i), 'Test Supplier Co.');
      
      await user.click(screen.getByText('Next'));
      
      // Should proceed to permissions step
      expect(screen.getByText('View Permissions')).toBeInTheDocument();
    });
  });

  describe('Step Navigation', () => {
    it('navigates through all steps', async () => {
      const user = userEvent.setup();
      renderComponent();
      
      // Fill basic info
      await user.type(screen.getByLabelText(/supplier email/i), 'supplier@example.com');
      await user.type(screen.getByLabelText(/company name/i), 'Test Supplier Co.');
      await user.click(screen.getByText('Next'));
      
      // Permissions step
      expect(screen.getByText('View Permissions')).toBeInTheDocument();
      await user.click(screen.getByText('Next'));
      
      // Message step
      expect(screen.getByText('Email Preview')).toBeInTheDocument();
      await user.click(screen.getByText('Next'));
      
      // Review step
      expect(screen.getByText('Supplier Information')).toBeInTheDocument();
      expect(screen.getByText('Add Supplier')).toBeInTheDocument();
    });

    it('allows going back through steps', async () => {
      const user = userEvent.setup();
      renderComponent();
      
      // Navigate to permissions step
      await user.type(screen.getByLabelText(/supplier email/i), 'supplier@example.com');
      await user.type(screen.getByLabelText(/company name/i), 'Test Supplier Co.');
      await user.click(screen.getByText('Next'));
      
      // Go back
      await user.click(screen.getByText('Back'));
      
      // Should be back to basic step
      expect(screen.getByLabelText(/supplier email/i)).toBeInTheDocument();
    });
  });

  describe('Permissions Configuration', () => {
    it('allows configuring data sharing permissions', async () => {
      const user = userEvent.setup();
      renderComponent();
      
      // Navigate to permissions step
      await user.type(screen.getByLabelText(/supplier email/i), 'supplier@example.com');
      await user.type(screen.getByLabelText(/company name/i), 'Test Supplier Co.');
      await user.click(screen.getByText('Next'));
      
      // Toggle some permissions
      const pricingCheckbox = screen.getByLabelText(/pricing information/i);
      await user.click(pricingCheckbox);
      
      expect(pricingCheckbox).toBeChecked();
    });

    it('shows permission impact badges', async () => {
      const user = userEvent.setup();
      renderComponent();
      
      // Navigate to permissions step
      await user.type(screen.getByLabelText(/supplier email/i), 'supplier@example.com');
      await user.type(screen.getByLabelText(/company name/i), 'Test Supplier Co.');
      await user.click(screen.getByText('Next'));
      
      expect(screen.getByText('High Impact')).toBeInTheDocument();
      expect(screen.getByText('Medium Impact')).toBeInTheDocument();
      expect(screen.getByText('Low Impact')).toBeInTheDocument();
    });
  });

  describe('Form Submission', () => {
    it('submits supplier addition with correct data', async () => {
      const user = userEvent.setup();
      const mockInvitation = {
        id: 'inv-123',
        supplier_email: 'supplier@example.com',
        supplier_name: 'Test Supplier Co.',
        company_type: 'originator' as const,
        relationship_type: 'supplier' as const,
        status: 'pending' as const,
        sent_at: new Date().toISOString(),
        expires_at: new Date().toISOString(),
      };

      mockOnboardingApi.sendSupplierInvitation.mockResolvedValue(mockInvitation as any);
      
      renderComponent();
      
      // Fill form and navigate to review
      await user.type(screen.getByLabelText(/supplier email/i), 'supplier@example.com');
      await user.type(screen.getByLabelText(/company name/i), 'Test Supplier Co.');
      await user.click(screen.getByText('Next')); // Permissions
      await user.click(screen.getByText('Next')); // Message
      await user.click(screen.getByText('Next')); // Review
      
      // Submit
      await user.click(screen.getByText('Add Supplier'));
      
      await waitFor(() => {
        expect(mockOnboardingApi.sendSupplierInvitation).toHaveBeenCalledWith(
          expect.objectContaining({
            supplier_email: 'supplier@example.com',
            supplier_name: 'Test Supplier Co.',
            company_type: 'originator',
            relationship_type: 'supplier',
          })
        );
      });
      
      expect(mockOnInvitationSent).toHaveBeenCalledWith(mockInvitation);
    });

    it('handles submission errors', async () => {
      const user = userEvent.setup();
      mockOnboardingApi.sendSupplierInvitation.mockRejectedValue(new Error('API Error'));
      
      renderComponent();
      
      // Fill form and navigate to review
      await user.type(screen.getByLabelText(/supplier email/i), 'supplier@example.com');
      await user.type(screen.getByLabelText(/company name/i), 'Test Supplier Co.');
      await user.click(screen.getByText('Next')); // Permissions
      await user.click(screen.getByText('Next')); // Message
      await user.click(screen.getByText('Next')); // Review
      
      // Submit
      await user.click(screen.getByText('Send Invitation'));
      
      await waitFor(() => {
        expect(screen.getByText(/failed to add supplier/i)).toBeInTheDocument();
      });
    });

    it('shows loading state during submission', async () => {
      const user = userEvent.setup();
      mockOnboardingApi.sendSupplierInvitation.mockImplementation(
        () => new Promise(resolve => setTimeout(resolve, 100))
      );
      
      renderComponent();
      
      // Fill form and navigate to review
      await user.type(screen.getByLabelText(/supplier email/i), 'supplier@example.com');
      await user.type(screen.getByLabelText(/company name/i), 'Test Supplier Co.');
      await user.click(screen.getByText('Next')); // Permissions
      await user.click(screen.getByText('Next')); // Message
      await user.click(screen.getByText('Next')); // Review
      
      // Submit
      await user.click(screen.getByText('Add Supplier'));
      
      expect(screen.getByText('Adding...')).toBeInTheDocument();
    });
  });

  describe('Custom Message', () => {
    it('allows adding custom invitation message', async () => {
      const user = userEvent.setup();
      renderComponent();
      
      // Navigate to message step
      await user.type(screen.getByLabelText(/supplier email/i), 'supplier@example.com');
      await user.type(screen.getByLabelText(/company name/i), 'Test Supplier Co.');
      await user.click(screen.getByText('Next')); // Permissions
      await user.click(screen.getByText('Next')); // Message
      
      // Add custom message
      const messageTextarea = screen.getByLabelText(/invitation message/i);
      await user.type(messageTextarea, 'Welcome to our sustainable supply chain!');
      
      expect(messageTextarea).toHaveValue('Welcome to our sustainable supply chain!');
    });

    it('shows email preview with custom message', async () => {
      const user = userEvent.setup();
      renderComponent();
      
      // Navigate to message step
      await user.type(screen.getByLabelText(/supplier email/i), 'supplier@example.com');
      await user.type(screen.getByLabelText(/company name/i), 'Test Supplier Co.');
      await user.click(screen.getByText('Next')); // Permissions
      await user.click(screen.getByText('Next')); // Message
      
      // Add custom message
      await user.type(
        screen.getByLabelText(/invitation message/i), 
        'Welcome to our sustainable supply chain!'
      );
      
      expect(screen.getByText('Welcome to our sustainable supply chain!')).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('has proper form labels', () => {
      renderComponent();
      
      expect(screen.getByLabelText(/supplier email/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/company name/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/company type/i)).toBeInTheDocument();
    });

    it('shows error messages with proper association', async () => {
      const user = userEvent.setup();
      renderComponent();
      
      await user.click(screen.getByText('Next'));
      
      const emailInput = screen.getByLabelText(/supplier email/i);
      const errorMessage = screen.getByText('Email is required');
      
      expect(emailInput).toHaveAttribute('aria-invalid', 'true');
      expect(errorMessage).toBeInTheDocument();
    });
  });
});

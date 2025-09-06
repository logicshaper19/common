/**
 * Tests for UserProfile component
 */
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { AuthProvider } from '../../../contexts/AuthContext';
import UserProfile from '../UserProfile';
import { notificationApi } from '../../../lib/notificationApi';

// Mock the notification API
jest.mock('../../../lib/notificationApi');
const mockNotificationApi = notificationApi as jest.Mocked<typeof notificationApi>;

// Mock the auth context
const mockUser = {
  id: 'user-1',
  email: 'test@example.com',
  full_name: 'Test User',
  role: 'buyer' as const,
  is_active: true,
  company_id: 'company-1',
};

const MockAuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <AuthProvider>
    {children}
  </AuthProvider>
);

const mockProfile = {
  id: 'user-1',
  email: 'john.smith@ecofashion.com',
  full_name: 'John Smith',
  title: 'Supply Chain Manager',
  phone: '+1 (555) 123-4567',
  company_id: 'company-1',
  company_name: 'EcoFashion Co.',
  role: 'buyer' as const,
  department: 'Supply Chain',
  timezone: 'America/New_York',
  language: 'en',
  date_format: 'MM/DD/YYYY' as const,
  time_format: '12h' as const,
  two_factor_enabled: false,
  password_changed_at: '2024-01-01T00:00:00Z',
  profile_completion: 85,
  onboarding_completed: true,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-15T10:00:00Z',
  last_active_at: '2024-01-15T10:30:00Z',
};

describe('UserProfile', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockNotificationApi.getUserProfile.mockResolvedValue(mockProfile);
    mockNotificationApi.updateUserProfile.mockResolvedValue(mockProfile);
  });

  const renderWithAuth = (component: React.ReactElement) => {
    return render(
      <MockAuthProvider>
        {component}
      </MockAuthProvider>
    );
  };

  it('renders user profile', async () => {
    renderWithAuth(<UserProfile />);

    expect(screen.getByText('User Profile')).toBeInTheDocument();
    expect(screen.getByText('Manage your account information and preferences')).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText('Profile Completion')).toBeInTheDocument();
      expect(screen.getByText('85%')).toBeInTheDocument();
    });
  });

  it('loads profile on mount', async () => {
    renderWithAuth(<UserProfile />);

    await waitFor(() => {
      expect(mockNotificationApi.getUserProfile).toHaveBeenCalled();
    });
  });

  it('displays profile information correctly', async () => {
    renderWithAuth(<UserProfile />);

    await waitFor(() => {
      expect(screen.getByDisplayValue('John Smith')).toBeInTheDocument();
      expect(screen.getByDisplayValue('john.smith@ecofashion.com')).toBeInTheDocument();
      expect(screen.getByDisplayValue('Supply Chain Manager')).toBeInTheDocument();
      expect(screen.getByDisplayValue('+1 (555) 123-4567')).toBeInTheDocument();
    });
  });

  it('shows profile completion progress', async () => {
    renderWithAuth(<UserProfile />);

    await waitFor(() => {
      expect(screen.getByText('Profile Completion')).toBeInTheDocument();
      expect(screen.getByText('85%')).toBeInTheDocument();
      
      // Check progress bar
      const progressBar = document.querySelector('[style*="width: 85%"]');
      expect(progressBar).toBeInTheDocument();
    });
  });

  it('handles tab navigation', async () => {
    const user = userEvent.setup();
    renderWithAuth(<UserProfile />);

    await waitFor(() => {
      expect(screen.getByText('Profile Information')).toBeInTheDocument();
    });

    // Click on Security tab
    const securityTab = screen.getByText('Security');
    await user.click(securityTab);

    expect(screen.getByText('Two-Factor Authentication')).toBeInTheDocument();
    expect(screen.getByText('Password')).toBeInTheDocument();
  });

  it('handles profile field changes', async () => {
    const user = userEvent.setup();
    renderWithAuth(<UserProfile />);

    await waitFor(() => {
      expect(screen.getByDisplayValue('John Smith')).toBeInTheDocument();
    });

    // Change full name
    const nameInput = screen.getByDisplayValue('John Smith');
    await user.clear(nameInput);
    await user.type(nameInput, 'Jane Smith');

    // Should enable save button
    expect(screen.getByText('Save Changes')).not.toBeDisabled();
  });

  it('saves profile changes', async () => {
    const user = userEvent.setup();
    renderWithAuth(<UserProfile />);

    await waitFor(() => {
      expect(screen.getByDisplayValue('John Smith')).toBeInTheDocument();
    });

    // Make a change
    const nameInput = screen.getByDisplayValue('John Smith');
    await user.clear(nameInput);
    await user.type(nameInput, 'Jane Smith');

    // Click save
    const saveButton = screen.getByText('Save Changes');
    await user.click(saveButton);

    await waitFor(() => {
      expect(mockNotificationApi.updateUserProfile).toHaveBeenCalledWith(
        expect.objectContaining({
          full_name: 'Jane Smith',
        })
      );
    });
  });

  it('shows success message after saving', async () => {
    const user = userEvent.setup();
    renderWithAuth(<UserProfile />);

    await waitFor(() => {
      expect(screen.getByDisplayValue('John Smith')).toBeInTheDocument();
    });

    // Make a change and save
    const nameInput = screen.getByDisplayValue('John Smith');
    await user.clear(nameInput);
    await user.type(nameInput, 'Jane Smith');

    const saveButton = screen.getByText('Save Changes');
    await user.click(saveButton);

    await waitFor(() => {
      expect(screen.getByText('Profile updated successfully')).toBeInTheDocument();
    });
  });

  it('handles reset changes', async () => {
    const user = userEvent.setup();
    renderWithAuth(<UserProfile />);

    await waitFor(() => {
      expect(screen.getByDisplayValue('John Smith')).toBeInTheDocument();
    });

    // Make a change
    const nameInput = screen.getByDisplayValue('John Smith');
    await user.clear(nameInput);
    await user.type(nameInput, 'Jane Smith');

    // Click reset
    const resetButton = screen.getByText('Reset Changes');
    await user.click(resetButton);

    // Should reload profile
    await waitFor(() => {
      expect(mockNotificationApi.getUserProfile).toHaveBeenCalledTimes(2);
    });
  });

  it('displays security information', async () => {
    const user = userEvent.setup();
    renderWithAuth(<UserProfile />);

    await waitFor(() => {
      expect(screen.getByText('Profile Information')).toBeInTheDocument();
    });

    // Click on Security tab
    const securityTab = screen.getByText('Security');
    await user.click(securityTab);

    expect(screen.getByText('Two-Factor Authentication')).toBeInTheDocument();
    expect(screen.getByText('Disabled')).toBeInTheDocument();
    expect(screen.getByText('Enable 2FA')).toBeInTheDocument();
  });

  it('shows avatar with initials', async () => {
    renderWithAuth(<UserProfile />);

    await waitFor(() => {
      expect(screen.getByText('J')).toBeInTheDocument(); // Initial from John Smith
    });
  });

  it('handles timezone changes', async () => {
    const user = userEvent.setup();
    renderWithAuth(<UserProfile />);

    await waitFor(() => {
      expect(screen.getByDisplayValue('Eastern Time (ET)')).toBeInTheDocument();
    });

    // Change timezone
    const timezoneSelect = screen.getByDisplayValue('Eastern Time (ET)');
    await user.selectOptions(timezoneSelect, 'America/Los_Angeles');

    // Should enable save button
    expect(screen.getByText('Save Changes')).not.toBeDisabled();
  });

  it('handles language changes', async () => {
    const user = userEvent.setup();
    renderWithAuth(<UserProfile />);

    await waitFor(() => {
      expect(screen.getByDisplayValue('English')).toBeInTheDocument();
    });

    // Change language
    const languageSelect = screen.getByDisplayValue('English');
    await user.selectOptions(languageSelect, 'es');

    // Should enable save button
    expect(screen.getByText('Save Changes')).not.toBeDisabled();
  });

  it('shows role as disabled field', async () => {
    renderWithAuth(<UserProfile />);

    await waitFor(() => {
      const roleSelect = screen.getByDisplayValue('buyer');
      expect(roleSelect).toBeDisabled();
    });
  });

  it('handles loading state', () => {
    mockNotificationApi.getUserProfile.mockImplementation(
      () => new Promise(() => {}) // Never resolves
    );

    renderWithAuth(<UserProfile />);

    expect(screen.getByText('Loading profile...')).toBeInTheDocument();
  });

  it('handles error state', async () => {
    mockNotificationApi.getUserProfile.mockRejectedValue(
      new Error('Failed to load')
    );

    renderWithAuth(<UserProfile />);

    await waitFor(() => {
      expect(screen.getByText('Unable to Load Profile')).toBeInTheDocument();
    });
  });

  it('handles save error', async () => {
    const user = userEvent.setup();
    mockNotificationApi.updateUserProfile.mockRejectedValue(
      new Error('Failed to save')
    );

    renderWithAuth(<UserProfile />);

    await waitFor(() => {
      expect(screen.getByDisplayValue('John Smith')).toBeInTheDocument();
    });

    // Make a change and save
    const nameInput = screen.getByDisplayValue('John Smith');
    await user.clear(nameInput);
    await user.type(nameInput, 'Jane Smith');

    const saveButton = screen.getByText('Save Changes');
    await user.click(saveButton);

    await waitFor(() => {
      expect(screen.getByText('Failed to save profile changes')).toBeInTheDocument();
    });
  });

  it('disables save button when no changes', async () => {
    renderWithAuth(<UserProfile />);

    await waitFor(() => {
      expect(screen.getByText('Save Changes')).toBeDisabled();
    });
  });

  it('shows preferences tab with redirect message', async () => {
    const user = userEvent.setup();
    renderWithAuth(<UserProfile />);

    await waitFor(() => {
      expect(screen.getByText('Profile Information')).toBeInTheDocument();
    });

    // Click on Preferences tab
    const preferencesTab = screen.getByText('Preferences');
    await user.click(preferencesTab);

    expect(screen.getByText(/Notification preferences are managed/)).toBeInTheDocument();
  });

  it('shows last login information', async () => {
    const user = userEvent.setup();
    renderWithAuth(<UserProfile />);

    await waitFor(() => {
      expect(screen.getByText('Profile Information')).toBeInTheDocument();
    });

    // Click on Security tab
    const securityTab = screen.getByText('Security');
    await user.click(securityTab);

    expect(screen.getByText('Recent Activity')).toBeInTheDocument();
    expect(screen.getByText('Last login')).toBeInTheDocument();
  });

  it('shows account creation date', async () => {
    const user = userEvent.setup();
    renderWithAuth(<UserProfile />);

    await waitFor(() => {
      expect(screen.getByText('Profile Information')).toBeInTheDocument();
    });

    // Click on Security tab
    const securityTab = screen.getByText('Security');
    await user.click(securityTab);

    expect(screen.getByText('Account created')).toBeInTheDocument();
  });
});

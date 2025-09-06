/**
 * Tests for NotificationPreferences component
 */
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import NotificationPreferences from '../NotificationPreferences';
import { notificationApi } from '../../../lib/notificationApi';

// Mock the notification API
jest.mock('../../../lib/notificationApi');
const mockNotificationApi = notificationApi as jest.Mocked<typeof notificationApi>;

const mockPreferences = {
  user_id: 'user-1',
  preferences: {
    po_created: {
      enabled: true,
      channels: ['in_app', 'email'],
      priority_threshold: 'normal' as const,
    },
    po_confirmed: {
      enabled: true,
      channels: ['in_app', 'email'],
      priority_threshold: 'normal' as const,
    },
    po_shipped: {
      enabled: true,
      channels: ['in_app'],
      priority_threshold: 'normal' as const,
    },
    po_delivered: {
      enabled: true,
      channels: ['in_app'],
      priority_threshold: 'normal' as const,
    },
    po_cancelled: {
      enabled: true,
      channels: ['in_app', 'email'],
      priority_threshold: 'normal' as const,
    },
    transparency_updated: {
      enabled: true,
      channels: ['in_app'],
      priority_threshold: 'low' as const,
    },
    supplier_invited: {
      enabled: true,
      channels: ['in_app', 'email'],
      priority_threshold: 'normal' as const,
    },
    supplier_joined: {
      enabled: true,
      channels: ['in_app', 'email'],
      priority_threshold: 'normal' as const,
    },
    system_alert: {
      enabled: true,
      channels: ['in_app', 'email'],
      priority_threshold: 'high' as const,
    },
    user_mention: {
      enabled: true,
      channels: ['in_app', 'email'],
      priority_threshold: 'normal' as const,
    },
    deadline_reminder: {
      enabled: true,
      channels: ['in_app', 'email'],
      priority_threshold: 'normal' as const,
      quiet_hours: {
        enabled: true,
        start_time: '22:00',
        end_time: '08:00',
        timezone: 'America/New_York',
      },
    },
    quality_issue: {
      enabled: true,
      channels: ['in_app', 'email'],
      priority_threshold: 'high' as const,
    },
    compliance_alert: {
      enabled: true,
      channels: ['in_app', 'email'],
      priority_threshold: 'high' as const,
    },
  },
  global_settings: {
    email_digest: {
      enabled: true,
      frequency: 'daily' as const,
      time: '09:00',
    },
    mobile_push: {
      enabled: true,
      sound: true,
      vibration: true,
    },
    desktop_notifications: {
      enabled: true,
      sound: false,
    },
  },
  updated_at: '2024-01-15T10:00:00Z',
};

describe('NotificationPreferences', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockNotificationApi.getNotificationPreferences.mockResolvedValue(mockPreferences);
    mockNotificationApi.updateNotificationPreferences.mockResolvedValue(mockPreferences);
  });

  it('renders notification preferences', async () => {
    render(<NotificationPreferences />);

    expect(screen.getByText('Notification Preferences')).toBeInTheDocument();
    expect(screen.getByText('Configure how and when you receive notifications')).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText('Global Settings')).toBeInTheDocument();
      expect(screen.getByText('Notification Types')).toBeInTheDocument();
    });
  });

  it('loads preferences on mount', async () => {
    render(<NotificationPreferences />);

    await waitFor(() => {
      expect(mockNotificationApi.getNotificationPreferences).toHaveBeenCalled();
    });
  });

  it('displays global settings correctly', async () => {
    render(<NotificationPreferences />);

    await waitFor(() => {
      expect(screen.getByText('Email Digest')).toBeInTheDocument();
      expect(screen.getByText('Desktop Notifications')).toBeInTheDocument();
    });

    // Check email digest settings
    const emailDigestCheckbox = screen.getByLabelText('Enable email digest');
    expect(emailDigestCheckbox).toBeChecked();

    const frequencySelect = screen.getByDisplayValue('daily');
    expect(frequencySelect).toBeInTheDocument();
  });

  it('displays notification type preferences', async () => {
    render(<NotificationPreferences />);

    await waitFor(() => {
      expect(screen.getByText('Purchase Order Created')).toBeInTheDocument();
      expect(screen.getByText('Purchase Order Confirmed')).toBeInTheDocument();
      expect(screen.getByText('Transparency Score Updated')).toBeInTheDocument();
    });
  });

  it('handles enabling/disabling notification types', async () => {
    const user = userEvent.setup();
    render(<NotificationPreferences />);

    await waitFor(() => {
      expect(screen.getByText('Purchase Order Created')).toBeInTheDocument();
    });

    // Find and toggle a notification type
    const poCreatedCheckbox = screen.getAllByRole('checkbox')[1]; // First is email digest
    await user.click(poCreatedCheckbox);

    // Should show save button
    expect(screen.getByText('Save Preferences')).not.toBeDisabled();
  });

  it('handles channel selection', async () => {
    const user = userEvent.setup();
    render(<NotificationPreferences />);

    await waitFor(() => {
      expect(screen.getByText('Purchase Order Created')).toBeInTheDocument();
    });

    // Find and click a channel button
    const inAppButtons = screen.getAllByText('In app');
    if (inAppButtons.length > 0) {
      await user.click(inAppButtons[0]);
      
      // Should show save button
      expect(screen.getByText('Save Preferences')).not.toBeDisabled();
    }
  });

  it('handles priority threshold changes', async () => {
    const user = userEvent.setup();
    render(<NotificationPreferences />);

    await waitFor(() => {
      expect(screen.getByText('Purchase Order Created')).toBeInTheDocument();
    });

    // Find and change priority threshold
    const prioritySelects = screen.getAllByDisplayValue('normal');
    if (prioritySelects.length > 0) {
      await user.selectOptions(prioritySelects[0], 'high');
      
      // Should show save button
      expect(screen.getByText('Save Preferences')).not.toBeDisabled();
    }
  });

  it('handles quiet hours configuration', async () => {
    const user = userEvent.setup();
    render(<NotificationPreferences />);

    await waitFor(() => {
      expect(screen.getByText('Deadline Reminders')).toBeInTheDocument();
    });

    // Find quiet hours checkbox for deadline reminders
    const quietHoursCheckbox = screen.getByLabelText('Enable quiet hours');
    expect(quietHoursCheckbox).toBeChecked();

    // Should show time inputs
    const timeInputs = screen.getAllByDisplayValue('22:00');
    expect(timeInputs.length).toBeGreaterThan(0);
  });

  it('saves preferences when save button is clicked', async () => {
    const user = userEvent.setup();
    render(<NotificationPreferences />);

    await waitFor(() => {
      expect(screen.getByText('Purchase Order Created')).toBeInTheDocument();
    });

    // Make a change
    const poCreatedCheckbox = screen.getAllByRole('checkbox')[1];
    await user.click(poCreatedCheckbox);

    // Click save
    const saveButton = screen.getByText('Save Preferences');
    await user.click(saveButton);

    await waitFor(() => {
      expect(mockNotificationApi.updateNotificationPreferences).toHaveBeenCalled();
    });
  });

  it('shows success message after saving', async () => {
    const user = userEvent.setup();
    render(<NotificationPreferences />);

    await waitFor(() => {
      expect(screen.getByText('Purchase Order Created')).toBeInTheDocument();
    });

    // Make a change and save
    const poCreatedCheckbox = screen.getAllByRole('checkbox')[1];
    await user.click(poCreatedCheckbox);

    const saveButton = screen.getByText('Save Preferences');
    await user.click(saveButton);

    await waitFor(() => {
      expect(screen.getByText('Preferences saved successfully')).toBeInTheDocument();
    });
  });

  it('handles reset changes', async () => {
    const user = userEvent.setup();
    render(<NotificationPreferences />);

    await waitFor(() => {
      expect(screen.getByText('Purchase Order Created')).toBeInTheDocument();
    });

    // Make a change
    const poCreatedCheckbox = screen.getAllByRole('checkbox')[1];
    await user.click(poCreatedCheckbox);

    // Click reset
    const resetButton = screen.getByText('Reset Changes');
    await user.click(resetButton);

    // Should reload preferences
    await waitFor(() => {
      expect(mockNotificationApi.getNotificationPreferences).toHaveBeenCalledTimes(2);
    });
  });

  it('handles email digest frequency changes', async () => {
    const user = userEvent.setup();
    render(<NotificationPreferences />);

    await waitFor(() => {
      expect(screen.getByDisplayValue('daily')).toBeInTheDocument();
    });

    // Change frequency
    const frequencySelect = screen.getByDisplayValue('daily');
    await user.selectOptions(frequencySelect, 'weekly');

    // Should show save button
    expect(screen.getByText('Save Preferences')).not.toBeDisabled();
  });

  it('shows time input for daily/weekly email digest', async () => {
    render(<NotificationPreferences />);

    await waitFor(() => {
      expect(screen.getByDisplayValue('daily')).toBeInTheDocument();
    });

    // Should show time input
    const timeInput = screen.getByDisplayValue('09:00');
    expect(timeInput).toBeInTheDocument();
  });

  it('handles desktop notification settings', async () => {
    const user = userEvent.setup();
    render(<NotificationPreferences />);

    await waitFor(() => {
      expect(screen.getByText('Desktop Notifications')).toBeInTheDocument();
    });

    // Find desktop notifications checkbox
    const desktopCheckbox = screen.getByLabelText('Enable desktop notifications');
    expect(desktopCheckbox).toBeChecked();

    // Should show sound option
    const soundCheckbox = screen.getByLabelText('Play sound');
    expect(soundCheckbox).not.toBeChecked();
  });

  it('handles loading state', () => {
    mockNotificationApi.getNotificationPreferences.mockImplementation(
      () => new Promise(() => {}) // Never resolves
    );

    render(<NotificationPreferences />);

    expect(screen.getByText('Loading preferences...')).toBeInTheDocument();
  });

  it('handles error state', async () => {
    mockNotificationApi.getNotificationPreferences.mockRejectedValue(
      new Error('Failed to load')
    );

    render(<NotificationPreferences />);

    await waitFor(() => {
      expect(screen.getByText('Unable to Load Preferences')).toBeInTheDocument();
    });
  });

  it('handles save error', async () => {
    const user = userEvent.setup();
    mockNotificationApi.updateNotificationPreferences.mockRejectedValue(
      new Error('Failed to save')
    );

    render(<NotificationPreferences />);

    await waitFor(() => {
      expect(screen.getByText('Purchase Order Created')).toBeInTheDocument();
    });

    // Make a change and save
    const poCreatedCheckbox = screen.getAllByRole('checkbox')[1];
    await user.click(poCreatedCheckbox);

    const saveButton = screen.getByText('Save Preferences');
    await user.click(saveButton);

    await waitFor(() => {
      expect(screen.getByText('Failed to save preferences')).toBeInTheDocument();
    });
  });

  it('disables save button when no changes', async () => {
    render(<NotificationPreferences />);

    await waitFor(() => {
      expect(screen.getByText('Save Preferences')).toBeDisabled();
    });
  });

  it('shows priority badges correctly', async () => {
    render(<NotificationPreferences />);

    await waitFor(() => {
      expect(screen.getByText('normal+ priority')).toBeInTheDocument();
      expect(screen.getByText('high+ priority')).toBeInTheDocument();
      expect(screen.getByText('low+ priority')).toBeInTheDocument();
    });
  });
});

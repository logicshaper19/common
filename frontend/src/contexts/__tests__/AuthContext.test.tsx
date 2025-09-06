/**
 * Unit tests for AuthContext
 */
import React from 'react';
import { render, screen, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { AuthProvider, useAuth, ProtectedRoute } from '../AuthContext';
import { apiClient } from '../../lib/api';

// Mock the API client
jest.mock('../../lib/api', () => ({
  apiClient: {
    getCurrentUser: jest.fn(),
    login: jest.fn(),
    logout: jest.fn(),
    clearToken: jest.fn(),
  },
}));

const mockApiClient = apiClient as jest.Mocked<typeof apiClient>;

// Test component that uses auth context
const TestComponent: React.FC = () => {
  const { user, isAuthenticated, isLoading, login, logout, error } = useAuth();

  if (isLoading) return <div>Loading...</div>;

  return (
    <div>
      <div data-testid="auth-status">
        {isAuthenticated ? 'Authenticated' : 'Not Authenticated'}
      </div>
      {user && <div data-testid="user-name">{user.full_name}</div>}
      {error && <div data-testid="error">{error}</div>}
      <button
        data-testid="login-button"
        onClick={() => login({ email: 'test@example.com', password: 'password' })}
      >
        Login
      </button>
      <button data-testid="logout-button" onClick={() => logout()}>
        Logout
      </button>
    </div>
  );
};

// Protected component for testing
const ProtectedComponent: React.FC = () => (
  <div data-testid="protected-content">Protected Content</div>
);

describe('AuthContext', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    localStorage.clear();
  });

  it('initializes with loading state', () => {
    mockApiClient.getCurrentUser.mockImplementation(
      () => new Promise(() => {}) // Never resolves
    );

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });

  it('initializes as not authenticated when no token exists', async () => {
    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('auth-status')).toHaveTextContent('Not Authenticated');
    });
  });

  it('initializes as authenticated when valid token exists', async () => {
    const mockUser = {
      id: '1',
      email: 'test@example.com',
      full_name: 'Test User',
      role: 'buyer',
      is_active: true,
      company_id: 'company-1',
    };

    localStorage.setItem('auth_token', 'valid-token');
    mockApiClient.getCurrentUser.mockResolvedValue(mockUser);

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('auth-status')).toHaveTextContent('Authenticated');
      expect(screen.getByTestId('user-name')).toHaveTextContent('Test User');
    });
  });

  it('clears token when getCurrentUser fails', async () => {
    localStorage.setItem('auth_token', 'invalid-token');
    mockApiClient.getCurrentUser.mockRejectedValue(new Error('Unauthorized'));

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('auth-status')).toHaveTextContent('Not Authenticated');
      expect(mockApiClient.clearToken).toHaveBeenCalled();
    });
  });

  it('handles successful login', async () => {
    const user = userEvent.setup();
    const mockUser = {
      id: '1',
      email: 'test@example.com',
      full_name: 'Test User',
      role: 'buyer',
      is_active: true,
      company_id: 'company-1',
    };

    mockApiClient.login.mockResolvedValue({
      access_token: 'new-token',
      token_type: 'bearer',
      expires_in: 3600,
      user: mockUser,
    });

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('auth-status')).toHaveTextContent('Not Authenticated');
    });

    await act(async () => {
      await user.click(screen.getByTestId('login-button'));
    });

    await waitFor(() => {
      expect(screen.getByTestId('auth-status')).toHaveTextContent('Authenticated');
      expect(screen.getByTestId('user-name')).toHaveTextContent('Test User');
    });

    expect(mockApiClient.login).toHaveBeenCalledWith({
      email: 'test@example.com',
      password: 'password',
    });
  });

  it('handles login failure', async () => {
    const user = userEvent.setup();
    const loginError = {
      error: {
        code: 'INVALID_CREDENTIALS',
        message: 'Invalid email or password',
      },
    };

    mockApiClient.login.mockRejectedValue(loginError);

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('auth-status')).toHaveTextContent('Not Authenticated');
    });

    await act(async () => {
      await user.click(screen.getByTestId('login-button'));
    });

    await waitFor(() => {
      expect(screen.getByTestId('error')).toHaveTextContent('Invalid email or password');
      expect(screen.getByTestId('auth-status')).toHaveTextContent('Not Authenticated');
    });
  });

  it('handles logout', async () => {
    const user = userEvent.setup();
    const mockUser = {
      id: '1',
      email: 'test@example.com',
      full_name: 'Test User',
      role: 'buyer',
      is_active: true,
      company_id: 'company-1',
    };

    // Start authenticated
    localStorage.setItem('auth_token', 'valid-token');
    mockApiClient.getCurrentUser.mockResolvedValue(mockUser);
    mockApiClient.logout.mockResolvedValue();

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('auth-status')).toHaveTextContent('Authenticated');
    });

    await act(async () => {
      await user.click(screen.getByTestId('logout-button'));
    });

    await waitFor(() => {
      expect(screen.getByTestId('auth-status')).toHaveTextContent('Not Authenticated');
      expect(screen.queryByTestId('user-name')).not.toBeInTheDocument();
    });

    expect(mockApiClient.logout).toHaveBeenCalled();
  });

  it('handles logout failure gracefully', async () => {
    const user = userEvent.setup();
    const mockUser = {
      id: '1',
      email: 'test@example.com',
      full_name: 'Test User',
      role: 'buyer',
      is_active: true,
      company_id: 'company-1',
    };

    // Start authenticated
    localStorage.setItem('auth_token', 'valid-token');
    mockApiClient.getCurrentUser.mockResolvedValue(mockUser);
    mockApiClient.logout.mockRejectedValue(new Error('Logout failed'));

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('auth-status')).toHaveTextContent('Authenticated');
    });

    await act(async () => {
      await user.click(screen.getByTestId('logout-button'));
    });

    // Should still clear local state even if server logout fails
    await waitFor(() => {
      expect(screen.getByTestId('auth-status')).toHaveTextContent('Not Authenticated');
    });
  });
});

describe('ProtectedRoute', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    localStorage.clear();
  });

  it('shows loading state while checking authentication', () => {
    mockApiClient.getCurrentUser.mockImplementation(
      () => new Promise(() => {}) // Never resolves
    );

    render(
      <AuthProvider>
        <ProtectedRoute>
          <ProtectedComponent />
        </ProtectedRoute>
      </AuthProvider>
    );

    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });

  it('redirects to login when not authenticated', async () => {
    // Mock window.location.href
    delete (window as any).location;
    window.location = { ...window.location, href: '' };

    render(
      <AuthProvider>
        <ProtectedRoute>
          <ProtectedComponent />
        </ProtectedRoute>
      </AuthProvider>
    );

    await waitFor(() => {
      expect(window.location.href).toBe('/login');
    });
  });

  it('renders children when authenticated', async () => {
    const mockUser = {
      id: '1',
      email: 'test@example.com',
      full_name: 'Test User',
      role: 'buyer',
      is_active: true,
      company_id: 'company-1',
    };

    localStorage.setItem('auth_token', 'valid-token');
    mockApiClient.getCurrentUser.mockResolvedValue(mockUser);

    render(
      <AuthProvider>
        <ProtectedRoute>
          <ProtectedComponent />
        </ProtectedRoute>
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('protected-content')).toBeInTheDocument();
    });
  });

  it('shows access denied for insufficient role', async () => {
    const mockUser = {
      id: '1',
      email: 'test@example.com',
      full_name: 'Test User',
      role: 'viewer',
      is_active: true,
      company_id: 'company-1',
    };

    localStorage.setItem('auth_token', 'valid-token');
    mockApiClient.getCurrentUser.mockResolvedValue(mockUser);

    render(
      <AuthProvider>
        <ProtectedRoute requiredRole="admin">
          <ProtectedComponent />
        </ProtectedRoute>
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('Access Denied')).toBeInTheDocument();
      expect(screen.getByText("You don't have permission to access this page.")).toBeInTheDocument();
    });
  });

  it('renders children when user has sufficient role', async () => {
    const mockUser = {
      id: '1',
      email: 'test@example.com',
      full_name: 'Test User',
      role: 'admin',
      is_active: true,
      company_id: 'company-1',
    };

    localStorage.setItem('auth_token', 'valid-token');
    mockApiClient.getCurrentUser.mockResolvedValue(mockUser);

    render(
      <AuthProvider>
        <ProtectedRoute requiredRole="buyer">
          <ProtectedComponent />
        </ProtectedRoute>
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('protected-content')).toBeInTheDocument();
    });
  });
});

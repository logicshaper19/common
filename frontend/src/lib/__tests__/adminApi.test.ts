/**
 * Admin API Integration Tests
 * Comprehensive test suite for admin API functionality
 */
import { adminApi } from '../../api/admin';

// Mock fetch globally
const mockFetch = jest.fn();
global.fetch = mockFetch;

describe('adminApi', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({}),
    });
  });

  describe('Dashboard', () => {
    it('fetches dashboard data', async () => {
      const mockData = {
        overview: { total_users: 100 },
        recent_activity: [],
        system_health: { status: 'healthy' },
      };
      
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockData),
      });

      const result = await adminApi.getDashboardData();
      
      expect(mockFetch).toHaveBeenCalledWith('/api/admin/dashboard', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer undefined',
        },
      });
      expect(result).toEqual(mockData);
    });
  });

  describe('Products', () => {
    it('fetches products with filters', async () => {
      const mockProducts = {
        products: [{ id: 'prod-1', name: 'Test Product' }],
        total: 1,
      };
      
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockProducts),
      });

      const filters = { page: 1, per_page: 20, search: 'test' };
      const result = await adminApi.getProducts(filters);
      
      expect(mockFetch).toHaveBeenCalledWith(
        '/api/admin/products?page=1&per_page=20&search=test',
        {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer undefined',
          },
        }
      );
      expect(result).toEqual(mockProducts);
    });

    it('creates a new product', async () => {
      const productData = {
        common_product_id: 'test_product',
        name: 'Test Product',
        category: 'raw_material' as const,
        default_unit: 'KG',
      };
      
      const mockResponse = { id: 'prod-1', ...productData };
      
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      });

      const result = await adminApi.createProduct(productData);
      
      expect(mockFetch).toHaveBeenCalledWith('/api/admin/products', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer undefined',
        },
        body: JSON.stringify(productData),
      });
      expect(result).toEqual(mockResponse);
    });

    it('updates an existing product', async () => {
      const updateData = { name: 'Updated Product' };
      const mockResponse = { success: true };
      
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      });

      const result = await adminApi.updateProduct('prod-1', updateData);
      
      expect(mockFetch).toHaveBeenCalledWith('/api/admin/products/prod-1', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer undefined',
        },
        body: JSON.stringify(updateData),
      });
      expect(result).toEqual(mockResponse);
    });

    it('deletes a product', async () => {
      const mockResponse = { success: true };
      
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      });

      const result = await adminApi.deleteProduct('prod-1');
      
      expect(mockFetch).toHaveBeenCalledWith('/api/admin/products/prod-1', {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer undefined',
        },
      });
      expect(result).toEqual(mockResponse);
    });

    it('validates product data', async () => {
      const productData = {
        common_product_id: 'test_product',
        name: 'Test Product',
        category: 'raw_material' as const,
      };
      
      const mockValidation = {
        is_valid: true,
        errors: [],
        warnings: [],
        suggestions: [],
      };
      
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockValidation),
      });

      const result = await adminApi.validateProduct(productData);
      
      expect(mockFetch).toHaveBeenCalledWith('/api/admin/products/validate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer undefined',
        },
        body: JSON.stringify(productData),
      });
      expect(result).toEqual(mockValidation);
    });

    it('performs bulk operations on products', async () => {
      const bulkOperation = {
        operation: 'deactivate' as const,
        product_ids: ['prod-1', 'prod-2'],
        reason: 'Test reason',
      };
      
      const mockResponse = { success: true, affected_count: 2 };
      
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      });

      const result = await adminApi.bulkProductOperation(bulkOperation);
      
      expect(mockFetch).toHaveBeenCalledWith('/api/admin/products/bulk', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer undefined',
        },
        body: JSON.stringify(bulkOperation),
      });
      expect(result).toEqual(mockResponse);
    });
  });

  describe('Users', () => {
    it('fetches users with filters', async () => {
      const mockUsers = {
        users: [{ id: 'user-1', name: 'Test User' }],
        total: 1,
      };
      
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockUsers),
      });

      const filters = { page: 1, per_page: 20, role: 'buyer' as const };
      const result = await adminApi.getUsers(filters);
      
      expect(mockFetch).toHaveBeenCalledWith(
        '/api/admin/users?page=1&per_page=20&role=buyer',
        {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer undefined',
          },
        }
      );
      expect(result).toEqual(mockUsers);
    });

    it('creates a new user', async () => {
      const userData = {
        email: 'test@example.com',
        full_name: 'Test User',
        role: 'buyer' as const,
        company_id: 'company-1',
        send_invitation: true,
      };
      
      const mockResponse = { id: 'user-1', ...userData };
      
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      });

      const result = await adminApi.createUser(userData);
      
      expect(mockFetch).toHaveBeenCalledWith('/api/admin/users', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer undefined',
        },
        body: JSON.stringify(userData),
      });
      expect(result).toEqual(mockResponse);
    });

    it('updates an existing user', async () => {
      const updateData = { full_name: 'Updated User', role: 'seller' as const };
      const mockResponse = { success: true };
      
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      });

      const result = await adminApi.updateUser('user-1', updateData);
      
      expect(mockFetch).toHaveBeenCalledWith('/api/admin/users/user-1', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer undefined',
        },
        body: JSON.stringify(updateData),
      });
      expect(result).toEqual(mockResponse);
    });

    it('deletes a user', async () => {
      const mockResponse = { success: true };
      
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      });

      const result = await adminApi.deleteUser('user-1');
      
      expect(mockFetch).toHaveBeenCalledWith('/api/admin/users/user-1', {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer undefined',
        },
      });
      expect(result).toEqual(mockResponse);
    });

    it('performs bulk operations on users', async () => {
      const bulkOperation = {
        operation: 'deactivate' as const,
        user_ids: ['user-1', 'user-2'],
        reason: 'Test reason',
        notify_users: true,
      };
      
      const mockResponse = { success: true, affected_count: 2 };
      
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      });

      const result = await adminApi.bulkUserOperation(bulkOperation);
      
      expect(mockFetch).toHaveBeenCalledWith('/api/admin/users/bulk', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer undefined',
        },
        body: JSON.stringify(bulkOperation),
      });
      expect(result).toEqual(mockResponse);
    });
  });

  describe('Support Tickets', () => {
    it('fetches tickets with filters', async () => {
      const mockTickets = {
        tickets: [{ id: 'ticket-1', title: 'Test Ticket' }],
        total: 1,
      };
      
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockTickets),
      });

      const filters = { page: 1, per_page: 20, status: 'open' as const };
      const result = await adminApi.getTickets(filters);
      
      expect(mockFetch).toHaveBeenCalledWith(
        '/api/admin/tickets?page=1&per_page=20&status=open',
        {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer undefined',
          },
        }
      );
      expect(result).toEqual(mockTickets);
    });

    it('fetches a single ticket with details', async () => {
      const mockTicket = {
        id: 'ticket-1',
        title: 'Test Ticket',
        messages: [],
      };
      
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockTicket),
      });

      const result = await adminApi.getTicket('ticket-1');
      
      expect(mockFetch).toHaveBeenCalledWith('/api/admin/tickets/ticket-1', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer undefined',
        },
      });
      expect(result).toEqual(mockTicket);
    });

    it('creates a new ticket', async () => {
      const ticketData = {
        title: 'Test Ticket',
        description: 'Test description',
        priority: 'medium' as const,
        category: 'technical' as const,
        tags: ['test'],
      };
      
      const mockResponse = { id: 'ticket-1', ...ticketData };
      
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      });

      const result = await adminApi.createTicket(ticketData);
      
      expect(mockFetch).toHaveBeenCalledWith('/api/admin/tickets', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer undefined',
        },
        body: JSON.stringify(ticketData),
      });
      expect(result).toEqual(mockResponse);
    });

    it('updates a ticket', async () => {
      const updateData = { status: 'resolved' as const };
      const mockResponse = { success: true };
      
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      });

      const result = await adminApi.updateTicket('ticket-1', updateData);
      
      expect(mockFetch).toHaveBeenCalledWith('/api/admin/tickets/ticket-1', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer undefined',
        },
        body: JSON.stringify(updateData),
      });
      expect(result).toEqual(mockResponse);
    });

    it('adds a message to a ticket', async () => {
      const messageData = {
        content: 'Test message',
        is_internal: false,
      };
      
      const mockTicket = {
        id: 'ticket-1',
        messages: [{ id: 'msg-1', content: 'Test message' }],
      };
      
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockTicket),
      });

      const result = await adminApi.addTicketMessage('ticket-1', messageData);
      
      expect(mockFetch).toHaveBeenCalledWith('/api/admin/tickets/ticket-1/messages', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer undefined',
        },
        body: JSON.stringify(messageData),
      });
      expect(result).toEqual(mockTicket);
    });
  });

  describe('Audit Logs', () => {
    it('fetches audit logs with filters', async () => {
      const mockLogs = {
        logs: [{ id: 'log-1', action: 'create' }],
        total: 1,
      };
      
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockLogs),
      });

      const filters = { page: 1, per_page: 50, action: 'create' as const };
      const result = await adminApi.getAuditLogs(filters);
      
      expect(mockFetch).toHaveBeenCalledWith(
        '/api/admin/audit-logs?page=1&per_page=50&action=create',
        {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer undefined',
          },
        }
      );
      expect(result).toEqual(mockLogs);
    });

    it('exports audit logs', async () => {
      const exportRequest = {
        filters: { page: 1, per_page: 1000 },
        format: 'csv' as const,
        include_details: true,
        date_range: {
          start: '2024-01-01',
          end: '2024-01-31',
        },
      };
      
      const mockResponse = { download_url: 'https://example.com/export.csv' };
      
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      });

      const result = await adminApi.exportAuditLogs(exportRequest);
      
      expect(mockFetch).toHaveBeenCalledWith('/api/admin/audit-logs/export', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer undefined',
        },
        body: JSON.stringify(exportRequest),
      });
      expect(result).toEqual(mockResponse);
    });
  });

  describe('System Health', () => {
    it('fetches system health data', async () => {
      const mockHealth = {
        status: 'healthy',
        services: [],
        metrics: {},
      };
      
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockHealth),
      });

      const result = await adminApi.getSystemHealth();
      
      expect(mockFetch).toHaveBeenCalledWith('/api/admin/system/health', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer undefined',
        },
      });
      expect(result).toEqual(mockHealth);
    });

    it('fetches system configurations', async () => {
      const mockConfigs = [
        { id: 'config-1', key: 'test.setting', value: 'test' },
      ];
      
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockConfigs),
      });

      const result = await adminApi.getSystemConfigs();
      
      expect(mockFetch).toHaveBeenCalledWith('/api/admin/system/config', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer undefined',
        },
      });
      expect(result).toEqual(mockConfigs);
    });

    it('updates system configuration', async () => {
      const mockResponse = { success: true };
      
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      });

      const result = await adminApi.updateSystemConfig('config-1', 'new-value');
      
      expect(mockFetch).toHaveBeenCalledWith('/api/admin/system/config/config-1', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer undefined',
        },
        body: JSON.stringify({ value: 'new-value' }),
      });
      expect(result).toEqual(mockResponse);
    });
  });

  describe('Error Handling', () => {
    it('throws error for non-ok responses', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 404,
        statusText: 'Not Found',
      });

      await expect(adminApi.getDashboardData()).rejects.toThrow('HTTP error! status: 404');
    });

    it('throws error for network failures', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network error'));

      await expect(adminApi.getDashboardData()).rejects.toThrow('Network error');
    });
  });
});

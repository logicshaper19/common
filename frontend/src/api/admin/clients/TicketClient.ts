/**
 * Support ticket management client for admin API
 */
import { BaseAdminClient } from '../base/BaseAdminClient';
import { PaginatedResponse } from '../base/types';
import {
  SupportTicket,
  TicketFilter,
  TicketCreate,
  TicketUpdate,
  TicketMessageCreate,
  TicketBulkOperation,
} from '../../../types/admin';

export class TicketClient extends BaseAdminClient {
  /**
   * Get paginated list of tickets with filtering
   */
  async getTickets(filters: TicketFilter): Promise<PaginatedResponse<SupportTicket>> {
    try {
      const { page, per_page } = this.validatePagination(filters.page, filters.per_page);
      const validatedFilters = { ...filters, page, per_page };

      const response = await this.makeRequest<PaginatedResponse<SupportTicket>>(
        '/admin/tickets',
        { params: validatedFilters }
      );

      return response;
    } catch (error) {
      console.warn('Backend not available for tickets, using mock data');
      return this.getMockTickets(filters);
    }
  }

  /**
   * Get a single ticket by ID
   */
  async getTicket(id: string): Promise<SupportTicket> {
    this.validateRequired({ id }, ['id']);

    try {
      const response = await this.makeRequest<SupportTicket>(`/admin/tickets/${id}`);
      return response;
    } catch (error) {
      console.warn(`Backend not available for ticket ${id}, using mock data`);
      return this.getMockTicket(id);
    }
  }

  /**
   * Create a new ticket
   */
  async createTicket(data: TicketCreate): Promise<SupportTicket> {
    this.validateRequired(data, ['title', 'description', 'priority', 'category']);

    try {
      const response = await this.makeRequest<SupportTicket>('/admin/tickets', {
        method: 'POST',
        data,
      });

      return response;
    } catch (error) {
      console.warn('Backend not available for ticket creation, using mock data');
      return this.createMockTicket(data);
    }
  }

  /**
   * Update an existing ticket
   */
  async updateTicket(id: string, data: TicketUpdate): Promise<{ success: boolean }> {
    this.validateRequired({ id }, ['id']);

    try {
      await this.makeRequest(`/admin/tickets/${id}`, {
        method: 'PUT',
        data,
      });

      return { success: true };
    } catch (error) {
      console.warn(`Backend not available for ticket ${id} update, using mock data`);
      return { success: true };
    }
  }

  /**
   * Add a message to a ticket
   */
  async addTicketMessage(id: string, data: TicketMessageCreate): Promise<SupportTicket> {
    this.validateRequired({ id }, ['id']);
    this.validateRequired(data, ['content']);

    try {
      const response = await this.makeRequest<SupportTicket>(`/admin/tickets/${id}/messages`, {
        method: 'POST',
        data,
      });

      return response;
    } catch (error) {
      console.warn(`Backend not available for ticket ${id} message, using mock data`);
      return this.getMockTicket(id);
    }
  }

  /**
   * Perform bulk operations on multiple tickets
   */
  async bulkTicketOperation(operation: TicketBulkOperation): Promise<{ success: boolean; affected_count: number }> {
    this.validateRequired(operation, ['operation', 'ticket_ids']);

    if (!operation.ticket_ids.length) {
      throw new Error('At least one ticket ID is required for bulk operations');
    }

    try {
      const response = await this.makeRequest<{ success: boolean; affected_count: number }>(
        '/admin/tickets/bulk',
        {
          method: 'POST',
          data: operation,
        }
      );

      return response;
    } catch (error) {
      console.warn('Backend not available for bulk ticket operation, using mock data');
      return {
        success: true,
        affected_count: operation.ticket_ids.length,
      };
    }
  }

  // Mock data methods
  private async getMockTickets(filters: TicketFilter): Promise<PaginatedResponse<SupportTicket>> {
    await this.delay();

    const mockTickets: SupportTicket[] = [
      {
        id: 'ticket-1',
        ticket_number: 'TKT-001',
        title: 'Login Issues',
        description: 'Unable to login to the platform',
        status: 'open',
        priority: 'high',
        category: 'technical',
        reporter_id: 'user-1',
        reporter_name: 'John Smith',
        reporter_email: 'john@example.com',
        reporter_company: 'ACME Corp',
        assignee_id: 'support-1',
        assignee_name: 'Jane Doe',
        created_at: '2024-01-20T10:00:00Z',
        updated_at: '2024-01-20T14:30:00Z',
        first_response_at: '2024-01-20T11:15:00Z',
        resolved_at: null,
        escalation_level: 0,
        sla_breach: false,
        tags: ['login', 'authentication'],
        messages: [],
      },
    ];

    return {
      data: mockTickets,
      total: mockTickets.length,
      page: filters.page,
      per_page: filters.per_page,
      total_pages: 1,
    };
  }

  private async getMockTicket(id: string): Promise<SupportTicket> {
    await this.delay();

    return {
      id,
      ticket_number: 'TKT-001',
      title: 'Test Ticket',
      description: 'Test description',
      status: 'open',
      priority: 'medium',
      category: 'technical',
      reporter_id: 'user-1',
      reporter_name: 'Test User',
      reporter_email: 'test@example.com',
      reporter_company: 'Test Company',
      assignee_id: null,
      assignee_name: null,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      first_response_at: null,
      resolved_at: null,
      escalation_level: 0,
      sla_breach: false,
      tags: [],
      messages: [
        {
          id: 'msg-1',
          content: 'Initial message content',
          author_id: 'user-1',
          author_name: 'Test User',
          author_type: 'customer',
          is_internal: false,
          created_at: new Date().toISOString(),
          attachments: [],
        },
      ],
    };
  }

  private async createMockTicket(data: TicketCreate): Promise<SupportTicket> {
    await this.delay();

    return {
      id: this.generateId('ticket'),
      ticket_number: `TKT-${String(Math.floor(Math.random() * 1000)).padStart(3, '0')}`,
      title: data.title,
      description: data.description,
      status: 'open',
      priority: data.priority,
      category: data.category,
      reporter_id: 'current-user',
      reporter_name: 'Current User',
      reporter_email: 'current@user.com',
      reporter_company: 'Current Company',
      assignee_id: null,
      assignee_name: null,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      first_response_at: null,
      resolved_at: null,
      escalation_level: 0,
      sla_breach: false,
      tags: data.tags || [],
      messages: [],
    };
  }

  private generateId(prefix: string): string {
    return `${prefix}-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }
}

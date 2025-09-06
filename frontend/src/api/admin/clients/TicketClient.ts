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
  TicketMessage,
  TicketBulkOperation,
} from '../../../types/admin';

export class TicketClient extends BaseAdminClient {

  /**
   * Get paginated list of tickets with filtering
   */
  async getTickets(filters: TicketFilter): Promise<PaginatedResponse<SupportTicket>> {
    const { page, per_page } = this.validatePagination(filters.page, filters.per_page);
    const validatedFilters = { ...filters, page, per_page };

    const response = await this.makeRequest<PaginatedResponse<SupportTicket>>(
      '/admin/tickets',
      { params: validatedFilters }
    );

    return response;
  }

  /**
   * Get a single ticket by ID
   */
  async getTicket(id: string): Promise<SupportTicket> {
    this.validateRequired({ id }, ['id']);

    const response = await this.makeRequest<SupportTicket>(`/admin/tickets/${id}`);
    return response;
  }

  /**
   * Create a new ticket
   */
  async createTicket(data: TicketCreate): Promise<SupportTicket> {
    this.validateRequired(data, ['title', 'description', 'category', 'priority']);

    const response = await this.makeRequest<SupportTicket>('/admin/tickets', {
      method: 'POST',
      data,
    });

    return response;
  }

  /**
   * Update an existing ticket
   */
  async updateTicket(id: string, data: TicketUpdate): Promise<{ success: boolean }> {
    this.validateRequired({ id }, ['id']);

    const response = await this.makeRequest<{ success: boolean }>(`/admin/tickets/${id}`, {
      method: 'PUT',
      data,
    });

    return { success: true };
  }

  /**
   * Add a message to a ticket
   */
  async addTicketMessage(id: string, data: { message: string; is_internal?: boolean }): Promise<SupportTicket> {
    this.validateRequired({ id }, ['id']);
    this.validateRequired(data, ['message']);

    const response = await this.makeRequest<SupportTicket>(`/admin/tickets/${id}/messages`, {
      method: 'POST',
      data,
    });

    return response;
  }

  /**
   * Perform bulk operations on multiple tickets
   */
  async bulkTicketOperation(operation: TicketBulkOperation): Promise<{ success: boolean; affected_count: number }> {
    this.validateRequired(operation, ['operation', 'ticket_ids']);

    if (!operation.ticket_ids.length) {
      throw new Error('At least one ticket ID is required for bulk operations');
    }

    const response = await this.makeRequest<{ success: boolean; affected_count: number }>(
      '/admin/tickets/bulk',
      {
        method: 'POST',
        data: operation,
      }
    );

    return response;
  }

  /**
   * Get ticket statistics
   */
  async getTicketStats(): Promise<{
    total_tickets: number;
    open_tickets: number;
    in_progress_tickets: number;
    resolved_tickets: number;
    closed_tickets: number;
    by_priority: Record<string, number>;
    by_category: Record<string, number>;
    average_resolution_time: number;
    sla_breaches: number;
  }> {
    const response = await this.makeRequest<any>('/admin/tickets/stats');
    return response;
  }

  /**
   * Assign ticket to a support agent
   */
  async assignTicket(id: string, assigneeId: string): Promise<{ success: boolean }> {
    this.validateRequired({ id, assigneeId }, ['id', 'assigneeId']);

    const response = await this.makeRequest<{ success: boolean }>(
      `/admin/tickets/${id}/assign`,
      {
        method: 'PUT',
        data: { assignee_id: assigneeId },
      }
    );

    return response;
  }

  /**
   * Escalate ticket
   */
  async escalateTicket(id: string, reason: string): Promise<{ success: boolean }> {
    this.validateRequired({ id, reason }, ['id', 'reason']);

    const response = await this.makeRequest<{ success: boolean }>(
      `/admin/tickets/${id}/escalate`,
      {
        method: 'POST',
        data: { reason },
      }
    );

    return response;
  }

  /**
   * Close ticket
   */
  async closeTicket(id: string, resolution: string): Promise<{ success: boolean }> {
    this.validateRequired({ id, resolution }, ['id', 'resolution']);

    const response = await this.makeRequest<{ success: boolean }>(
      `/admin/tickets/${id}/close`,
      {
        method: 'PUT',
        data: { resolution },
      }
    );

    return response;
  }

  /**
   * Reopen ticket
   */
  async reopenTicket(id: string, reason: string): Promise<{ success: boolean }> {
    this.validateRequired({ id, reason }, ['id', 'reason']);

    const response = await this.makeRequest<{ success: boolean }>(
      `/admin/tickets/${id}/reopen`,
      {
        method: 'PUT',
        data: { reason },
      }
    );

    return response;
  }
}

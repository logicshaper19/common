/**
 * Support Ticket System Interface
 * Comprehensive support ticket management with priority handling and communication
 */
import React, { useState, useEffect, useCallback } from 'react';
import {
  MagnifyingGlassIcon,
  PlusIcon,
  PencilIcon,
  EyeIcon,
  ChatBubbleLeftRightIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  ClockIcon,
  UserIcon,
  TagIcon,
  PaperClipIcon,
  ArrowPathIcon,
  FunnelIcon,
} from '@heroicons/react/24/outline';
import { adminApi } from '../../api/admin';
import {
  SupportTicket,
  TicketFilter,
  TicketCreate,
  TicketUpdate,
  TicketMessageCreate,
  TicketBulkOperation,
  TicketPriority,
  TicketStatus,
  TicketCategory,
} from '../../types/admin';
import { formatTimeAgo } from '../../lib/utils';

interface SupportTicketSystemProps {
  className?: string;
}

export function SupportTicketSystem({ className = '' }: SupportTicketSystemProps) {
  const [tickets, setTickets] = useState<SupportTicket[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedTickets, setSelectedTickets] = useState<Set<string>>(new Set());
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showViewModal, setShowViewModal] = useState(false);
  const [selectedTicket, setSelectedTicket] = useState<SupportTicket | null>(null);
  const [newMessage, setNewMessage] = useState('');
  const [isInternal, setIsInternal] = useState(false);

  // Filters and pagination
  const [filters, setFilters] = useState<TicketFilter>({
    page: 1,
    per_page: 20,
  });
  const [totalPages, setTotalPages] = useState(1);
  const [totalTickets, setTotalTickets] = useState(0);

  // Form state
  const [formData, setFormData] = useState<TicketCreate>({
    title: '',
    description: '',
    priority: 'medium',
    category: 'technical',
    tags: [],
  });

  const loadTickets = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await adminApi.getTickets(filters);
      setTickets(response.tickets);
      setTotalPages(Math.ceil(response.total / filters.per_page));
      setTotalTickets(response.total);
    } catch (err) {
      setError('Failed to load tickets');
      console.error('Error loading tickets:', err);
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    loadTickets();
  }, [loadTickets]);

  const handleFilterChange = (newFilters: Partial<TicketFilter>) => {
    setFilters(prev => ({ ...prev, ...newFilters, page: 1 }));
  };

  const handlePageChange = (page: number) => {
    setFilters(prev => ({ ...prev, page }));
  };

  const handleSelectTicket = (ticketId: string) => {
    setSelectedTickets(prev => {
      const newSet = new Set(prev);
      if (newSet.has(ticketId)) {
        newSet.delete(ticketId);
      } else {
        newSet.add(ticketId);
      }
      return newSet;
    });
  };

  const handleSelectAll = () => {
    if (selectedTickets.size === tickets.length) {
      setSelectedTickets(new Set());
    } else {
      setSelectedTickets(new Set(tickets.map(t => t.id)));
    }
  };

  const handleCreateTicket = async () => {
    try {
      setError(null);
      await adminApi.createTicket(formData);
      setShowCreateModal(false);
      setFormData({
        title: '',
        description: '',
        priority: 'medium',
        category: 'technical',
        tags: [],
      });
      await loadTickets();
    } catch (err) {
      setError('Failed to create ticket');
      console.error('Error creating ticket:', err);
    }
  };

  const handleUpdateTicket = async (ticketId: string, updates: TicketUpdate) => {
    try {
      setError(null);
      await adminApi.updateTicket(ticketId, updates);
      await loadTickets();
      if (selectedTicket && selectedTicket.id === ticketId) {
        const updatedTicket = await adminApi.getTicket(ticketId);
        setSelectedTicket(updatedTicket);
      }
    } catch (err) {
      setError('Failed to update ticket');
      console.error('Error updating ticket:', err);
    }
  };

  const handleAddMessage = async () => {
    if (!selectedTicket || !newMessage.trim()) return;

    try {
      setError(null);
      const messageData: TicketMessageCreate = {
        content: newMessage,
        is_internal: isInternal,
      };

      const updatedTicket = await adminApi.addTicketMessage(selectedTicket.id, messageData);
      setSelectedTicket(updatedTicket);
      setNewMessage('');
      setIsInternal(false);
      await loadTickets();
    } catch (err) {
      setError('Failed to add message');
      console.error('Error adding message:', err);
    }
  };

  const handleBulkOperation = async (operation: TicketBulkOperation['operation']) => {
    if (selectedTickets.size === 0) return;

    let additionalData = {};
    
    if (operation === 'assign') {
      const assigneeId = prompt('Enter assignee ID:');
      if (!assigneeId) return;
      additionalData = { assignee_id: assigneeId };
    } else if (operation === 'change_priority') {
      const priority = prompt('Enter new priority (low, medium, high, urgent, critical):') as TicketPriority;
      if (!priority) return;
      additionalData = { priority };
    } else if (operation === 'add_tag') {
      const tag = prompt('Enter tag to add:');
      if (!tag) return;
      additionalData = { tag };
    }

    const reason = prompt(`Please provide a reason for ${operation}:`);
    if (!reason) return;

    try {
      setError(null);
      const bulkOp: TicketBulkOperation = {
        operation,
        ticket_ids: Array.from(selectedTickets),
        reason,
        ...additionalData,
      };

      await adminApi.bulkTicketOperation(bulkOp);
      setSelectedTickets(new Set());
      await loadTickets();
    } catch (err) {
      setError(`Failed to ${operation} tickets`);
      console.error(`Error with bulk ${operation}:`, err);
    }
  };

  const openViewModal = async (ticket: SupportTicket) => {
    try {
      const fullTicket = await adminApi.getTicket(ticket.id);
      setSelectedTicket(fullTicket);
      setShowViewModal(true);
    } catch (err) {
      setError('Failed to load ticket details');
      console.error('Error loading ticket:', err);
    }
  };

  const getPriorityBadge = (priority: TicketPriority) => {
    const styles = {
      low: 'bg-gray-100 text-gray-800',
      medium: 'bg-blue-100 text-blue-800',
      high: 'bg-yellow-100 text-yellow-800',
      urgent: 'bg-orange-100 text-orange-800',
      critical: 'bg-red-100 text-red-800',
    };

    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${styles[priority]}`}>
        {priority}
      </span>
    );
  };

  const getStatusBadge = (status: TicketStatus) => {
    const styles = {
      open: 'bg-green-100 text-green-800',
      in_progress: 'bg-blue-100 text-blue-800',
      waiting_customer: 'bg-yellow-100 text-yellow-800',
      waiting_internal: 'bg-purple-100 text-purple-800',
      resolved: 'bg-gray-100 text-gray-800',
      closed: 'bg-gray-100 text-gray-600',
    };

    const icons = {
      open: CheckCircleIcon,
      in_progress: ArrowPathIcon,
      waiting_customer: ClockIcon,
      waiting_internal: ClockIcon,
      resolved: CheckCircleIcon,
      closed: CheckCircleIcon,
    };

    const Icon = icons[status];

    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${styles[status]}`}>
        <Icon className="h-3 w-3 mr-1" />
        {status.replace('_', ' ')}
      </span>
    );
  };

  const getCategoryBadge = (category: TicketCategory) => {
    const styles = {
      technical: 'bg-blue-100 text-blue-800',
      billing: 'bg-green-100 text-green-800',
      feature_request: 'bg-purple-100 text-purple-800',
      bug_report: 'bg-red-100 text-red-800',
      account: 'bg-yellow-100 text-yellow-800',
      compliance: 'bg-orange-100 text-orange-800',
      other: 'bg-gray-100 text-gray-800',
    };

    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${styles[category]}`}>
        {category.replace('_', ' ')}
      </span>
    );
  };

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Support Ticket System</h1>
          <p className="mt-1 text-sm text-gray-500">
            Manage support tickets, assignments, and customer communications
          </p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
        >
          <PlusIcon className="h-4 w-4 mr-2" />
          Create Ticket
        </button>
      </div>

      {/* Error Alert */}
      {error && (
        <div className="rounded-md bg-red-50 p-4">
          <div className="flex">
            <ExclamationTriangleIcon className="h-5 w-5 text-red-400" />
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">Error</h3>
              <div className="mt-2 text-sm text-red-700">{error}</div>
            </div>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="bg-white shadow rounded-lg p-6">
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Search
            </label>
            <div className="relative">
              <MagnifyingGlassIcon className="h-5 w-5 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
              <input
                type="text"
                placeholder="Search tickets..."
                value={filters.search || ''}
                onChange={(e) => handleFilterChange({ search: e.target.value })}
                className="pl-10 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Status
            </label>
            <select
              value={filters.status || ''}
              onChange={(e) => handleFilterChange({ status: e.target.value as TicketStatus || undefined })}
              className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
            >
              <option value="">All Statuses</option>
              <option value="open">Open</option>
              <option value="in_progress">In Progress</option>
              <option value="waiting_customer">Waiting Customer</option>
              <option value="waiting_internal">Waiting Internal</option>
              <option value="resolved">Resolved</option>
              <option value="closed">Closed</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Priority
            </label>
            <select
              value={filters.priority || ''}
              onChange={(e) => handleFilterChange({ priority: e.target.value as TicketPriority || undefined })}
              className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
            >
              <option value="">All Priorities</option>
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
              <option value="urgent">Urgent</option>
              <option value="critical">Critical</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Category
            </label>
            <select
              value={filters.category || ''}
              onChange={(e) => handleFilterChange({ category: e.target.value as TicketCategory || undefined })}
              className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
            >
              <option value="">All Categories</option>
              <option value="technical">Technical</option>
              <option value="billing">Billing</option>
              <option value="feature_request">Feature Request</option>
              <option value="bug_report">Bug Report</option>
              <option value="account">Account</option>
              <option value="compliance">Compliance</option>
              <option value="other">Other</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              SLA Status
            </label>
            <select
              value={filters.sla_breach?.toString() || ''}
              onChange={(e) => handleFilterChange({ 
                sla_breach: e.target.value ? e.target.value === 'true' : undefined 
              })}
              className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
            >
              <option value="">All Tickets</option>
              <option value="true">SLA Breached</option>
              <option value="false">Within SLA</option>
            </select>
          </div>
        </div>
      </div>

      {/* Bulk Actions */}
      {selectedTickets.size > 0 && (
        <div className="bg-white shadow rounded-lg p-4">
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-700">
              {selectedTickets.size} ticket{selectedTickets.size !== 1 ? 's' : ''} selected
            </span>
            <div className="flex space-x-2">
              <button
                onClick={() => handleBulkOperation('assign')}
                className="inline-flex items-center px-3 py-1.5 border border-gray-300 shadow-sm text-xs font-medium rounded text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
              >
                <UserIcon className="h-4 w-4 mr-1" />
                Assign
              </button>
              <button
                onClick={() => handleBulkOperation('close')}
                className="inline-flex items-center px-3 py-1.5 border border-gray-300 shadow-sm text-xs font-medium rounded text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
              >
                <CheckCircleIcon className="h-4 w-4 mr-1" />
                Close
              </button>
              <button
                onClick={() => handleBulkOperation('change_priority')}
                className="inline-flex items-center px-3 py-1.5 border border-gray-300 shadow-sm text-xs font-medium rounded text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
              >
                <ExclamationTriangleIcon className="h-4 w-4 mr-1" />
                Priority
              </button>
              <button
                onClick={() => handleBulkOperation('add_tag')}
                className="inline-flex items-center px-3 py-1.5 border border-gray-300 shadow-sm text-xs font-medium rounded text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
              >
                <TagIcon className="h-4 w-4 mr-1" />
                Tag
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Tickets Table */}
      <div className="bg-white shadow rounded-lg overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">
            Support Tickets ({totalTickets})
          </h3>
        </div>

        {loading ? (
          <div className="p-8 text-center">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
            <p className="mt-2 text-sm text-gray-500">Loading tickets...</p>
          </div>
        ) : tickets.length === 0 ? (
          <div className="p-8 text-center">
            <p className="text-gray-500">No tickets found</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left">
                    <input
                      type="checkbox"
                      checked={selectedTickets.size === tickets.length && tickets.length > 0}
                      onChange={handleSelectAll}
                      className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                    />
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Ticket
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Reporter
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Priority
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Assignee
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Created
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {tickets.map((ticket) => (
                  <tr key={ticket.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4">
                      <input
                        type="checkbox"
                        checked={selectedTickets.has(ticket.id)}
                        onChange={() => handleSelectTicket(ticket.id)}
                        className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                      />
                    </td>
                    <td className="px-6 py-4">
                      <div>
                        <div className="text-sm font-medium text-gray-900">
                          {ticket.title}
                        </div>
                        <div className="text-sm text-gray-500">
                          #{ticket.ticket_number}
                        </div>
                        <div className="mt-1">
                          {getCategoryBadge(ticket.category)}
                        </div>
                        {ticket.sla_breach && (
                          <div className="mt-1">
                            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-red-100 text-red-800">
                              SLA Breach
                            </span>
                          </div>
                        )}
                        {ticket.tags.length > 0 && (
                          <div className="mt-1 flex flex-wrap gap-1">
                            {ticket.tags.slice(0, 2).map((tag, index) => (
                              <span key={index} className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-800">
                                {tag}
                              </span>
                            ))}
                            {ticket.tags.length > 2 && (
                              <span className="text-xs text-gray-500">+{ticket.tags.length - 2} more</span>
                            )}
                          </div>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div>
                        <div className="text-sm font-medium text-gray-900">
                          {ticket.reporter_name}
                        </div>
                        <div className="text-sm text-gray-500">
                          {ticket.reporter_company}
                        </div>
                        <div className="text-xs text-gray-400">
                          {ticket.reporter_email}
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      {getPriorityBadge(ticket.priority)}
                      {ticket.escalation_level > 0 && (
                        <div className="mt-1 text-xs text-orange-600">
                          Escalated (L{ticket.escalation_level})
                        </div>
                      )}
                    </td>
                    <td className="px-6 py-4">
                      {getStatusBadge(ticket.status)}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-900">
                      {ticket.assignee_name || (
                        <span className="text-gray-400">Unassigned</span>
                      )}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-500">
                      {formatTimeAgo(ticket.created_at)}
                      {ticket.first_response_at && (
                        <div className="text-xs text-green-600">
                          First response: {formatTimeAgo(ticket.first_response_at)}
                        </div>
                      )}
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex space-x-2">
                        <button
                          onClick={() => openViewModal(ticket)}
                          className="text-gray-400 hover:text-gray-600"
                          title="View Ticket"
                        >
                          <EyeIcon className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => openViewModal(ticket)}
                          className="text-primary-400 hover:text-primary-600"
                          title="Reply"
                        >
                          <ChatBubbleLeftRightIcon className="h-4 w-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Create Ticket Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
            <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" onClick={() => setShowCreateModal(false)}></div>

            <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
              <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
                <div className="sm:flex sm:items-start">
                  <div className="w-full">
                    <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
                      Create Support Ticket
                    </h3>

                    <div className="space-y-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Title *
                        </label>
                        <input
                          type="text"
                          value={formData.title}
                          onChange={(e) => setFormData(prev => ({ ...prev, title: e.target.value }))}
                          className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
                          placeholder="Brief description of the issue"
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Description *
                        </label>
                        <textarea
                          value={formData.description}
                          onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                          rows={4}
                          className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
                          placeholder="Detailed description of the issue..."
                        />
                      </div>

                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            Priority *
                          </label>
                          <select
                            value={formData.priority}
                            onChange={(e) => setFormData(prev => ({ ...prev, priority: e.target.value as TicketPriority }))}
                            className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
                          >
                            <option value="low">Low</option>
                            <option value="medium">Medium</option>
                            <option value="high">High</option>
                            <option value="urgent">Urgent</option>
                            <option value="critical">Critical</option>
                          </select>
                        </div>

                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            Category *
                          </label>
                          <select
                            value={formData.category}
                            onChange={(e) => setFormData(prev => ({ ...prev, category: e.target.value as TicketCategory }))}
                            className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
                          >
                            <option value="technical">Technical</option>
                            <option value="billing">Billing</option>
                            <option value="feature_request">Feature Request</option>
                            <option value="bug_report">Bug Report</option>
                            <option value="account">Account</option>
                            <option value="compliance">Compliance</option>
                            <option value="other">Other</option>
                          </select>
                        </div>
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Tags
                        </label>
                        <input
                          type="text"
                          placeholder="Enter tags separated by commas"
                          onChange={(e) => {
                            const tags = e.target.value.split(',').map(tag => tag.trim()).filter(tag => tag);
                            setFormData(prev => ({ ...prev, tags }));
                          }}
                          className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
                        />
                        <p className="mt-1 text-xs text-gray-500">Separate multiple tags with commas</p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              <div className="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
                <button
                  onClick={handleCreateTicket}
                  disabled={!formData.title || !formData.description}
                  className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-primary-600 text-base font-medium text-white hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 sm:ml-3 sm:w-auto sm:text-sm disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Create Ticket
                </button>
                <button
                  onClick={() => setShowCreateModal(false)}
                  className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* View Ticket Modal */}
      {showViewModal && selectedTicket && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
            <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" onClick={() => setShowViewModal(false)}></div>

            <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-4xl sm:w-full">
              <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
                <div className="flex justify-between items-start mb-6">
                  <div>
                    <h3 className="text-lg leading-6 font-medium text-gray-900">
                      {selectedTicket.title}
                    </h3>
                    <p className="text-sm text-gray-500">#{selectedTicket.ticket_number}</p>
                  </div>
                  <div className="flex space-x-2">
                    {getPriorityBadge(selectedTicket.priority)}
                    {getStatusBadge(selectedTicket.status)}
                  </div>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                  {/* Ticket Details */}
                  <div className="lg:col-span-2 space-y-6">
                    {/* Description */}
                    <div>
                      <h4 className="text-sm font-medium text-gray-900 mb-2">Description</h4>
                      <div className="bg-gray-50 rounded-lg p-4">
                        <p className="text-sm text-gray-700 whitespace-pre-wrap">{selectedTicket.description}</p>
                      </div>
                    </div>

                    {/* Messages */}
                    <div>
                      <h4 className="text-sm font-medium text-gray-900 mb-4">Conversation</h4>
                      <div className="space-y-4 max-h-96 overflow-y-auto">
                        {selectedTicket.messages.map((message) => (
                          <div key={message.id} className={`flex ${message.author_type === 'customer' ? 'justify-start' : 'justify-end'}`}>
                            <div className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                              message.author_type === 'customer'
                                ? 'bg-gray-100 text-gray-900'
                                : message.is_internal
                                  ? 'bg-yellow-100 text-yellow-900'
                                  : 'bg-primary-100 text-primary-900'
                            }`}>
                              <div className="flex items-center justify-between mb-1">
                                <span className="text-xs font-medium">{message.author_name}</span>
                                <span className="text-xs text-gray-500">{formatTimeAgo(message.created_at)}</span>
                              </div>
                              <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                              {message.is_internal && (
                                <div className="mt-1">
                                  <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-yellow-200 text-yellow-800">
                                    Internal
                                  </span>
                                </div>
                              )}
                              {message.attachments.length > 0 && (
                                <div className="mt-2">
                                  {message.attachments.map((attachment) => (
                                    <div key={attachment.id} className="flex items-center text-xs text-gray-600">
                                      <PaperClipIcon className="h-3 w-3 mr-1" />
                                      <span>{attachment.filename}</span>
                                    </div>
                                  ))}
                                </div>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>

                      {/* Add Message */}
                      <div className="mt-4 border-t pt-4">
                        <div className="space-y-3">
                          <textarea
                            value={newMessage}
                            onChange={(e) => setNewMessage(e.target.value)}
                            rows={3}
                            className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
                            placeholder="Type your message..."
                          />
                          <div className="flex items-center justify-between">
                            <label className="flex items-center">
                              <input
                                type="checkbox"
                                checked={isInternal}
                                onChange={(e) => setIsInternal(e.target.checked)}
                                className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                              />
                              <span className="ml-2 text-sm text-gray-700">Internal message</span>
                            </label>
                            <button
                              onClick={handleAddMessage}
                              disabled={!newMessage.trim()}
                              className="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                              Send Message
                            </button>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Sidebar */}
                  <div className="space-y-6">
                    {/* Ticket Info */}
                    <div>
                      <h4 className="text-sm font-medium text-gray-900 mb-3">Ticket Information</h4>
                      <div className="space-y-3 text-sm">
                        <div>
                          <span className="text-gray-500">Reporter:</span>
                          <div className="mt-1">
                            <div className="font-medium">{selectedTicket.reporter_name}</div>
                            <div className="text-gray-600">{selectedTicket.reporter_email}</div>
                            <div className="text-gray-600">{selectedTicket.reporter_company}</div>
                          </div>
                        </div>

                        <div>
                          <span className="text-gray-500">Assignee:</span>
                          <div className="mt-1">
                            {selectedTicket.assignee_name ? (
                              <div className="font-medium">{selectedTicket.assignee_name}</div>
                            ) : (
                              <span className="text-gray-400">Unassigned</span>
                            )}
                          </div>
                        </div>

                        <div>
                          <span className="text-gray-500">Category:</span>
                          <div className="mt-1">{getCategoryBadge(selectedTicket.category)}</div>
                        </div>

                        <div>
                          <span className="text-gray-500">Created:</span>
                          <div className="mt-1 text-gray-900">{formatTimeAgo(selectedTicket.created_at)}</div>
                        </div>

                        <div>
                          <span className="text-gray-500">Last Updated:</span>
                          <div className="mt-1 text-gray-900">{formatTimeAgo(selectedTicket.updated_at)}</div>
                        </div>

                        {selectedTicket.resolved_at && (
                          <div>
                            <span className="text-gray-500">Resolved:</span>
                            <div className="mt-1 text-gray-900">{formatTimeAgo(selectedTicket.resolved_at)}</div>
                          </div>
                        )}

                        {selectedTicket.tags.length > 0 && (
                          <div>
                            <span className="text-gray-500">Tags:</span>
                            <div className="mt-1 flex flex-wrap gap-1">
                              {selectedTicket.tags.map((tag, index) => (
                                <span key={index} className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-800">
                                  {tag}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Quick Actions */}
                    <div>
                      <h4 className="text-sm font-medium text-gray-900 mb-3">Quick Actions</h4>
                      <div className="space-y-2">
                        <select
                          value={selectedTicket.status}
                          onChange={(e) => handleUpdateTicket(selectedTicket.id, { status: e.target.value as TicketStatus })}
                          className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
                        >
                          <option value="open">Open</option>
                          <option value="in_progress">In Progress</option>
                          <option value="waiting_customer">Waiting Customer</option>
                          <option value="waiting_internal">Waiting Internal</option>
                          <option value="resolved">Resolved</option>
                          <option value="closed">Closed</option>
                        </select>

                        <select
                          value={selectedTicket.priority}
                          onChange={(e) => handleUpdateTicket(selectedTicket.id, { priority: e.target.value as TicketPriority })}
                          className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
                        >
                          <option value="low">Low Priority</option>
                          <option value="medium">Medium Priority</option>
                          <option value="high">High Priority</option>
                          <option value="urgent">Urgent</option>
                          <option value="critical">Critical</option>
                        </select>

                        {selectedTicket.escalation_level < 3 && (
                          <button
                            onClick={() => handleUpdateTicket(selectedTicket.id, { escalation_level: selectedTicket.escalation_level + 1 })}
                            className="w-full inline-flex justify-center items-center px-3 py-2 border border-orange-300 shadow-sm text-sm font-medium rounded-md text-orange-700 bg-orange-50 hover:bg-orange-100 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-orange-500"
                          >
                            <ExclamationTriangleIcon className="h-4 w-4 mr-2" />
                            Escalate (L{selectedTicket.escalation_level + 1})
                          </button>
                        )}
                      </div>
                    </div>

                    {/* SLA Information */}
                    {selectedTicket.sla_breach && (
                      <div className="bg-red-50 border border-red-200 rounded-lg p-3">
                        <div className="flex">
                          <ExclamationTriangleIcon className="h-5 w-5 text-red-400" />
                          <div className="ml-3">
                            <h4 className="text-sm font-medium text-red-800">SLA Breach</h4>
                            <p className="mt-1 text-sm text-red-700">
                              This ticket has exceeded the SLA response time.
                            </p>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
              <div className="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
                <button
                  onClick={() => setShowViewModal(false)}
                  className="w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 sm:w-auto sm:text-sm"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

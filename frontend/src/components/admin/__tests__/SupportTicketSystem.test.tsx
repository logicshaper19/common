/**
 * Support Ticket System Tests
 * Test suite for support ticket management functionality
 */
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { SupportTicketSystem } from '../SupportTicketSystem';
import { adminApi } from '../../../lib/adminApi';

// Mock the admin API
jest.mock('../../../lib/adminApi', () => ({
  adminApi: {
    getTickets: jest.fn(),
    getTicket: jest.fn(),
    createTicket: jest.fn(),
    updateTicket: jest.fn(),
    addTicketMessage: jest.fn(),
    bulkTicketOperation: jest.fn(),
  },
}));

const mockTickets = [
  {
    id: 'ticket-1',
    ticket_number: 'TKT-001',
    title: 'Login Issues',
    description: 'Unable to login to the platform',
    status: 'open' as const,
    priority: 'high' as const,
    category: 'technical' as const,
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
  {
    id: 'ticket-2',
    ticket_number: 'TKT-002',
    title: 'Feature Request: Export Data',
    description: 'Need ability to export purchase order data',
    status: 'in_progress' as const,
    priority: 'medium' as const,
    category: 'feature_request' as const,
    reporter_id: 'user-2',
    reporter_name: 'Alice Johnson',
    reporter_email: 'alice@company.com',
    reporter_company: 'Company Inc',
    assignee_id: null,
    assignee_name: null,
    created_at: '2024-01-19T15:30:00Z',
    updated_at: '2024-01-20T09:45:00Z',
    first_response_at: null,
    resolved_at: null,
    escalation_level: 1,
    sla_breach: true,
    tags: ['export', 'data'],
    messages: [],
  },
];

const mockTicketDetails = {
  ...mockTickets[0],
  messages: [
    {
      id: 'msg-1',
      content: 'I cannot login to my account. Getting error message.',
      author_id: 'user-1',
      author_name: 'John Smith',
      author_type: 'customer' as const,
      is_internal: false,
      created_at: '2024-01-20T10:00:00Z',
      attachments: [],
    },
    {
      id: 'msg-2',
      content: 'Thank you for contacting support. Can you please provide more details about the error?',
      author_id: 'support-1',
      author_name: 'Jane Doe',
      author_type: 'support' as const,
      is_internal: false,
      created_at: '2024-01-20T11:15:00Z',
      attachments: [],
    },
  ],
};

describe('SupportTicketSystem', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (adminApi.getTickets as any).mockResolvedValue({
      tickets: mockTickets,
      total: mockTickets.length,
    });
  });

  it('renders support ticket system interface', async () => {
    render(<SupportTicketSystem />);
    
    expect(screen.getByText('Support Ticket System')).toBeInTheDocument();
    expect(screen.getByText('Create Ticket')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Search tickets...')).toBeInTheDocument();
    
    await waitFor(() => {
      expect(screen.getByText('Login Issues')).toBeInTheDocument();
      expect(screen.getByText('Feature Request: Export Data')).toBeInTheDocument();
    });
  });

  it('loads and displays tickets', async () => {
    render(<SupportTicketSystem />);
    
    await waitFor(() => {
      expect(adminApi.getTickets).toHaveBeenCalledWith({
        page: 1,
        per_page: 20,
      });
      
      expect(screen.getByText('TKT-001')).toBeInTheDocument();
      expect(screen.getByText('TKT-002')).toBeInTheDocument();
      expect(screen.getByText('John Smith')).toBeInTheDocument();
      expect(screen.getByText('Alice Johnson')).toBeInTheDocument();
    });
  });

  it('filters tickets by search term', async () => {
    render(<SupportTicketSystem />);
    
    await waitFor(() => {
      expect(screen.getByText('Login Issues')).toBeInTheDocument();
    });
    
    const searchInput = screen.getByPlaceholderText('Search tickets...');
    fireEvent.change(searchInput, { target: { value: 'login' } });
    
    await waitFor(() => {
      expect(adminApi.getTickets).toHaveBeenCalledWith({
        page: 1,
        per_page: 20,
        search: 'login',
      });
    });
  });

  it('filters tickets by status', async () => {
    render(<SupportTicketSystem />);
    
    await waitFor(() => {
      expect(screen.getByText('Login Issues')).toBeInTheDocument();
    });
    
    const statusSelect = screen.getByDisplayValue('All Statuses');
    fireEvent.change(statusSelect, { target: { value: 'open' } });
    
    await waitFor(() => {
      expect(adminApi.getTickets).toHaveBeenCalledWith({
        page: 1,
        per_page: 20,
        status: 'open',
      });
    });
  });

  it('filters tickets by priority', async () => {
    render(<SupportTicketSystem />);
    
    await waitFor(() => {
      expect(screen.getByText('Login Issues')).toBeInTheDocument();
    });
    
    const prioritySelect = screen.getByDisplayValue('All Priorities');
    fireEvent.change(prioritySelect, { target: { value: 'high' } });
    
    await waitFor(() => {
      expect(adminApi.getTickets).toHaveBeenCalledWith({
        page: 1,
        per_page: 20,
        priority: 'high',
      });
    });
  });

  it('opens create ticket modal', async () => {
    render(<SupportTicketSystem />);
    
    fireEvent.click(screen.getByText('Create Ticket'));
    
    await waitFor(() => {
      expect(screen.getByText('Create Support Ticket')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('Brief description of the issue')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('Detailed description of the issue...')).toBeInTheDocument();
    });
  });

  it('creates a new ticket', async () => {
    (adminApi.createTicket as any).mockResolvedValue({ id: 'ticket-3' });
    
    render(<SupportTicketSystem />);
    
    fireEvent.click(screen.getByText('Create Ticket'));
    
    await waitFor(() => {
      expect(screen.getByText('Create Support Ticket')).toBeInTheDocument();
    });
    
    // Fill in form
    fireEvent.change(screen.getByPlaceholderText('Brief description of the issue'), {
      target: { value: 'Test Issue' },
    });
    fireEvent.change(screen.getByPlaceholderText('Detailed description of the issue...'), {
      target: { value: 'This is a test issue description' },
    });
    fireEvent.change(screen.getByDisplayValue('medium'), {
      target: { value: 'high' },
    });
    fireEvent.change(screen.getByDisplayValue('technical'), {
      target: { value: 'billing' },
    });
    
    // Submit form
    fireEvent.click(screen.getByText('Create Ticket'));
    
    await waitFor(() => {
      expect(adminApi.createTicket).toHaveBeenCalledWith({
        title: 'Test Issue',
        description: 'This is a test issue description',
        priority: 'high',
        category: 'billing',
        tags: [],
      });
    });
  });

  it('opens ticket details modal', async () => {
    (adminApi.getTicket as any).mockResolvedValue(mockTicketDetails);
    
    render(<SupportTicketSystem />);
    
    await waitFor(() => {
      expect(screen.getByText('Login Issues')).toBeInTheDocument();
    });
    
    const viewButtons = screen.getAllByTitle('View Ticket');
    fireEvent.click(viewButtons[0]);
    
    await waitFor(() => {
      expect(adminApi.getTicket).toHaveBeenCalledWith('ticket-1');
      expect(screen.getByText('TKT-001')).toBeInTheDocument();
      expect(screen.getByText('Conversation')).toBeInTheDocument();
      expect(screen.getByText('I cannot login to my account. Getting error message.')).toBeInTheDocument();
    });
  });

  it('adds a message to ticket', async () => {
    (adminApi.getTicket as any).mockResolvedValue(mockTicketDetails);
    (adminApi.addTicketMessage as any).mockResolvedValue({
      ...mockTicketDetails,
      messages: [
        ...mockTicketDetails.messages,
        {
          id: 'msg-3',
          content: 'New message',
          author_id: 'support-1',
          author_name: 'Jane Doe',
          author_type: 'support',
          is_internal: false,
          created_at: '2024-01-20T15:00:00Z',
          attachments: [],
        },
      ],
    });
    
    render(<SupportTicketSystem />);
    
    await waitFor(() => {
      expect(screen.getByText('Login Issues')).toBeInTheDocument();
    });
    
    const viewButtons = screen.getAllByTitle('View Ticket');
    fireEvent.click(viewButtons[0]);
    
    await waitFor(() => {
      expect(screen.getByText('Conversation')).toBeInTheDocument();
    });
    
    // Add a message
    const messageInput = screen.getByPlaceholderText('Type your message...');
    fireEvent.change(messageInput, { target: { value: 'New message' } });
    
    fireEvent.click(screen.getByText('Send Message'));
    
    await waitFor(() => {
      expect(adminApi.addTicketMessage).toHaveBeenCalledWith('ticket-1', {
        content: 'New message',
        is_internal: false,
      });
    });
  });

  it('updates ticket status', async () => {
    (adminApi.getTicket as any).mockResolvedValue(mockTicketDetails);
    (adminApi.updateTicket as any).mockResolvedValue({ success: true });
    
    render(<SupportTicketSystem />);
    
    await waitFor(() => {
      expect(screen.getByText('Login Issues')).toBeInTheDocument();
    });
    
    const viewButtons = screen.getAllByTitle('View Ticket');
    fireEvent.click(viewButtons[0]);
    
    await waitFor(() => {
      expect(screen.getByText('Quick Actions')).toBeInTheDocument();
    });
    
    // Change status
    const statusSelect = screen.getByDisplayValue('open');
    fireEvent.change(statusSelect, { target: { value: 'resolved' } });
    
    await waitFor(() => {
      expect(adminApi.updateTicket).toHaveBeenCalledWith('ticket-1', {
        status: 'resolved',
      });
    });
  });

  it('escalates a ticket', async () => {
    (adminApi.getTicket as any).mockResolvedValue(mockTicketDetails);
    (adminApi.updateTicket as any).mockResolvedValue({ success: true });
    
    render(<SupportTicketSystem />);
    
    await waitFor(() => {
      expect(screen.getByText('Login Issues')).toBeInTheDocument();
    });
    
    const viewButtons = screen.getAllByTitle('View Ticket');
    fireEvent.click(viewButtons[0]);
    
    await waitFor(() => {
      expect(screen.getByText('Escalate (L1)')).toBeInTheDocument();
    });
    
    fireEvent.click(screen.getByText('Escalate (L1)'));
    
    await waitFor(() => {
      expect(adminApi.updateTicket).toHaveBeenCalledWith('ticket-1', {
        escalation_level: 1,
      });
    });
  });

  it('performs bulk operations on selected tickets', async () => {
    (adminApi.bulkTicketOperation as any).mockResolvedValue({ success: true });
    
    // Mock window.prompt
    const promptSpy = jest.spyOn(window, 'prompt').mockReturnValue('Test reason');
    
    render(<SupportTicketSystem />);
    
    await waitFor(() => {
      expect(screen.getByText('Login Issues')).toBeInTheDocument();
    });
    
    // Select first ticket
    const checkboxes = screen.getAllByRole('checkbox');
    fireEvent.click(checkboxes[1]); // Skip the "select all" checkbox
    
    await waitFor(() => {
      expect(screen.getByText('1 ticket selected')).toBeInTheDocument();
    });
    
    // Perform bulk close
    fireEvent.click(screen.getByText('Close'));
    
    await waitFor(() => {
      expect(promptSpy).toHaveBeenCalledWith('Please provide a reason for close:');
      expect(adminApi.bulkTicketOperation).toHaveBeenCalledWith({
        operation: 'close',
        ticket_ids: ['ticket-1'],
        reason: 'Test reason',
      });
    });
    
    promptSpy.mockRestore();
  });

  it('displays SLA breach indicators', async () => {
    render(<SupportTicketSystem />);
    
    await waitFor(() => {
      expect(screen.getByText('SLA Breach')).toBeInTheDocument();
    });
  });

  it('displays ticket tags', async () => {
    render(<SupportTicketSystem />);
    
    await waitFor(() => {
      expect(screen.getByText('login')).toBeInTheDocument();
      expect(screen.getByText('authentication')).toBeInTheDocument();
      expect(screen.getByText('export')).toBeInTheDocument();
      expect(screen.getByText('data')).toBeInTheDocument();
    });
  });

  it('shows escalation level for escalated tickets', async () => {
    render(<SupportTicketSystem />);
    
    await waitFor(() => {
      expect(screen.getByText('Escalated (L1)')).toBeInTheDocument();
    });
  });

  it('displays loading state', () => {
    (adminApi.getTickets as any).mockImplementation(() => new Promise(() => {}));
    
    render(<SupportTicketSystem />);
    
    expect(screen.getByText('Loading tickets...')).toBeInTheDocument();
  });

  it('displays error state', async () => {
    (adminApi.getTickets as any).mockRejectedValue(new Error('API Error'));
    
    render(<SupportTicketSystem />);
    
    await waitFor(() => {
      expect(screen.getByText('Failed to load tickets')).toBeInTheDocument();
    });
  });

  it('displays empty state when no tickets found', async () => {
    (adminApi.getTickets as any).mockResolvedValue({
      tickets: [],
      total: 0,
    });
    
    render(<SupportTicketSystem />);
    
    await waitFor(() => {
      expect(screen.getByText('No tickets found')).toBeInTheDocument();
    });
  });

  it('marks internal messages correctly', async () => {
    (adminApi.getTicket as any).mockResolvedValue(mockTicketDetails);
    
    render(<SupportTicketSystem />);
    
    await waitFor(() => {
      expect(screen.getByText('Login Issues')).toBeInTheDocument();
    });
    
    const viewButtons = screen.getAllByTitle('View Ticket');
    fireEvent.click(viewButtons[0]);
    
    await waitFor(() => {
      expect(screen.getByText('Conversation')).toBeInTheDocument();
    });
    
    // Check internal message checkbox
    const internalCheckbox = screen.getByLabelText('Internal message');
    fireEvent.click(internalCheckbox);
    
    const messageInput = screen.getByPlaceholderText('Type your message...');
    fireEvent.change(messageInput, { target: { value: 'Internal note' } });
    
    fireEvent.click(screen.getByText('Send Message'));
    
    await waitFor(() => {
      expect(adminApi.addTicketMessage).toHaveBeenCalledWith('ticket-1', {
        content: 'Internal note',
        is_internal: true,
      });
    });
  });

  it('displays ticket statistics correctly', async () => {
    render(<SupportTicketSystem />);
    
    await waitFor(() => {
      expect(screen.getByText('Support Tickets (2)')).toBeInTheDocument();
    });
  });
});

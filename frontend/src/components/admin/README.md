# Admin Components

This directory contains the comprehensive admin and support system components for the platform. These components provide full administrative capabilities including user management, product catalog oversight, support ticket handling, audit logging, and system monitoring.

## Components Overview

### AdminDashboard.tsx
Main admin dashboard that orchestrates all admin functionality with tabbed navigation and overview metrics.

**Features:**
- Overview tab with key platform metrics
- Navigation between all admin modules
- Real-time dashboard data loading
- Error handling and loading states

**Usage:**
```tsx
import { AdminDashboard } from './components/admin/AdminDashboard';

<AdminDashboard />
```

### ProductCatalogManagement.tsx
Comprehensive product catalog administration interface.

**Features:**
- Product CRUD operations with validation
- Advanced filtering and search
- Bulk operations (activate, deactivate, update)
- Material composition and origin requirements
- Real-time validation with errors, warnings, suggestions

**Key Functions:**
- Create/edit/delete products
- Validate product data
- Bulk product operations
- View detailed product information

### UserCompanyManagement.tsx
User and company management dashboard with role-based access control.

**Features:**
- User lifecycle management
- Company oversight and compliance monitoring
- Role assignment and permissions
- Bulk user/company operations
- 2FA and session management

**Key Functions:**
- Create/edit users with role assignment
- Monitor company compliance and transparency
- Bulk activate/deactivate operations
- Password reset and account management

### SupportTicketSystem.tsx
Complete support ticket management system with communication tools.

**Features:**
- Ticket lifecycle management
- Priority and category assignment
- SLA monitoring and escalation
- Message threading with internal notes
- Bulk ticket operations

**Key Functions:**
- Create and manage support tickets
- Add messages and internal notes
- Update ticket status and priority
- Escalate tickets through support tiers
- Bulk ticket operations

### AuditLogViewer.tsx
Security and compliance audit log interface with advanced filtering.

**Features:**
- Comprehensive audit trail viewing
- Advanced filtering by date, user, action, risk level
- Export capabilities (CSV, JSON, Excel)
- Security monitoring and anomaly detection
- Real-time log streaming

**Key Functions:**
- View detailed audit logs
- Filter and search audit events
- Export audit data for compliance
- Monitor security events

### SystemMonitoring.tsx
System health monitoring and configuration management dashboard.

**Features:**
- Real-time system health metrics
- Service status monitoring
- Configuration management
- Backup status and management
- System alerts and notifications

**Key Functions:**
- Monitor system performance
- Manage system configuration
- View backup status
- Handle system alerts

## File Structure

```
admin/
├── AdminDashboard.tsx              # Main admin dashboard
├── ProductCatalogManagement.tsx    # Product catalog admin
├── UserCompanyManagement.tsx       # User/company management
├── SupportTicketSystem.tsx         # Support ticket system
├── AuditLogViewer.tsx             # Audit log viewer
├── SystemMonitoring.tsx           # System monitoring
├── README.md                       # This file
└── __tests__/                     # Test files
    ├── AdminDashboard.test.tsx
    ├── ProductCatalogManagement.test.tsx
    ├── SupportTicketSystem.test.tsx
    └── ...
```

## Dependencies

### Required Libraries
- React 18+
- TypeScript
- Tailwind CSS
- Heroicons
- React Testing Library (for tests)
- Vitest (for testing)

### Internal Dependencies
- `../../api/admin` - Modular admin API client
- `../../types/admin` - TypeScript type definitions
- `../../lib/utils` - Utility functions

## API Integration

All components integrate with the admin API through the modular `adminApi` client:

```typescript
import { adminApi } from '../../api/admin';

// New modular approach (recommended)
const products = await adminApi.products.getProducts(filters);
const users = await adminApi.users.getUsers(userFilters);
const tickets = await adminApi.tickets.getTickets(ticketFilters);

// Legacy approach (still supported)
const products = await adminApi.getProducts(filters);
const ticket = await adminApi.createTicket(ticketData);
const users = await adminApi.getUsers(userFilters);
```

## State Management

Components use React hooks for state management:

- `useState` for local component state
- `useEffect` for side effects and data loading
- `useCallback` for memoized functions
- Custom hooks for shared logic

## Error Handling

All components implement consistent error handling:

```typescript
const [error, setError] = useState<string | null>(null);

try {
  setError(null);
  await adminApi.someOperation();
} catch (err) {
  setError('Operation failed');
  console.error('Error:', err);
}
```

## Loading States

Components show loading indicators during async operations:

```typescript
const [loading, setLoading] = useState(true);

const loadData = async () => {
  try {
    setLoading(true);
    const data = await adminApi.getData();
    setData(data);
  } finally {
    setLoading(false);
  }
};
```

## Styling

Components use Tailwind CSS for styling with consistent design patterns:

- **Cards**: `bg-white shadow rounded-lg`
- **Buttons**: `bg-primary-600 hover:bg-primary-700 text-white`
- **Forms**: `border-gray-300 focus:border-primary-500 focus:ring-primary-500`
- **Tables**: `divide-y divide-gray-200`

## Accessibility

Components follow accessibility best practices:

- Semantic HTML elements
- ARIA labels and descriptions
- Keyboard navigation support
- Screen reader compatibility
- Color contrast compliance

## Testing

### Test Structure
Each component has comprehensive tests covering:

- Rendering and basic functionality
- User interactions (clicks, form submissions)
- API integration and error handling
- Loading and error states
- Accessibility features

### Running Tests
```bash
# Run all admin component tests
npm test src/components/admin

# Run specific component tests
npm test AdminDashboard.test.tsx

# Run tests in watch mode
npm test --watch
```

### Test Examples
```typescript
// Basic rendering test
it('renders admin dashboard', () => {
  render(<AdminDashboard />);
  expect(screen.getByText('Admin Dashboard')).toBeInTheDocument();
});

// User interaction test
it('switches tabs correctly', async () => {
  render(<AdminDashboard />);
  fireEvent.click(screen.getByText('Product Catalog'));
  await waitFor(() => {
    expect(screen.getByTestId('product-catalog')).toBeInTheDocument();
  });
});
```

## Performance Considerations

### Optimization Strategies
- **Lazy Loading**: Components load data only when needed
- **Pagination**: Large datasets are paginated
- **Debounced Search**: Search inputs use debouncing
- **Memoization**: Expensive calculations are memoized
- **Virtual Scrolling**: Large lists use virtual scrolling

### Bundle Size
Components are designed to be tree-shakeable and minimize bundle size:
- Selective imports from icon libraries
- Conditional loading of heavy features
- Code splitting for large components

## Security

### Access Control
Components respect role-based access control:
- Admin-only features are protected
- Sensitive data is masked appropriately
- API calls include proper authentication

### Data Validation
All user inputs are validated:
- Client-side validation for UX
- Server-side validation for security
- Sanitization of user-generated content

## Development Guidelines

### Code Style
- Use TypeScript for type safety
- Follow React best practices
- Implement proper error boundaries
- Use consistent naming conventions

### Component Structure
```typescript
interface ComponentProps {
  className?: string;
  // Other props
}

export function Component({ className = '', ...props }: ComponentProps) {
  // State declarations
  // Effect hooks
  // Event handlers
  // Render helpers
  
  return (
    <div className={`space-y-6 ${className}`}>
      {/* Component JSX */}
    </div>
  );
}
```

### Adding New Features
1. Define TypeScript interfaces
2. Implement API integration
3. Create component with proper state management
4. Add comprehensive tests
5. Update documentation

## Troubleshooting

### Common Issues

**API Errors**
- Check network connectivity
- Verify authentication tokens
- Review API endpoint URLs

**Performance Issues**
- Check for unnecessary re-renders
- Optimize large data sets
- Review network requests

**Styling Issues**
- Verify Tailwind CSS classes
- Check responsive design
- Test across browsers

### Debug Tools
- React Developer Tools
- Network tab for API calls
- Console for error messages
- Performance profiler

## Contributing

When contributing to admin components:

1. Follow existing code patterns
2. Add comprehensive tests
3. Update documentation
4. Consider accessibility
5. Test across different roles
6. Verify security implications

## Future Enhancements

Planned improvements:
- Real-time notifications
- Advanced analytics dashboard
- Mobile-responsive design
- Offline capability
- Enhanced search functionality
- AI-powered insights

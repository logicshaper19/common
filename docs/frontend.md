# Frontend Documentation

## Overview
The frontend is built with React 18, TypeScript, and Tailwind CSS.

## Tech Stack
- **React**: 18.2.0
- **TypeScript**: 4.9.5
- **Tailwind CSS**: 3.3.0
- **React Router**: 6.8.0
- **Axios**: 1.3.0

## Project Structure
```
frontend/
├── public/                 # Static assets
├── src/
│   ├── components/         # Reusable components
│   │   ├── layout/        # Layout components
│   │   ├── forms/         # Form components
│   │   └── ui/            # UI components
│   ├── pages/             # Page components
│   ├── services/          # API services
│   ├── hooks/             # Custom hooks
│   ├── context/           # React context
│   ├── types/             # TypeScript types
│   └── utils/             # Utility functions
├── package.json
└── tailwind.config.js
```

## Getting Started

### Installation
```bash
cd frontend
npm install
```

### Development Server
```bash
npm start
```
Runs on http://localhost:3000

### Build for Production
```bash
npm run build
```

## Key Features

### Authentication
- Login/logout functionality
- JWT token management
- Protected routes
- User session persistence

### Supply Chain Management
- Company management
- Product catalog
- Purchase order creation and tracking
- Supply chain visualization

### UI Components
- Responsive design
- Dark/light theme support
- Form validation
- Loading states
- Error handling

## API Integration

### Base Configuration
```typescript
const API_BASE_URL = 'http://localhost:8000';
```

### Authentication Service
```typescript
// Login
const response = await authService.login(email, password);

// Logout
authService.logout();

// Get current user
const user = authService.getCurrentUser();
```

### API Services
- `authService` - Authentication
- `companyService` - Company management
- `productService` - Product management
- `purchaseOrderService` - Purchase orders

## Styling

### Tailwind CSS
The project uses Tailwind CSS for styling:
```jsx
<div className="bg-white shadow-lg rounded-lg p-6">
  <h1 className="text-2xl font-bold text-gray-900">Title</h1>
</div>
```

### Custom Components
Reusable components in `src/components/ui/`:
- `Button` - Styled button component
- `Input` - Form input component
- `Modal` - Modal dialog component
- `Table` - Data table component

## State Management

### Context API
- `AuthContext` - Authentication state
- `ThemeContext` - Theme management
- `NotificationContext` - Notifications

### Custom Hooks
- `useAuth` - Authentication logic
- `useApi` - API call management
- `useLocalStorage` - Local storage management

## Environment Variables

Create `.env.local`:
```env
REACT_APP_API_BASE_URL=http://localhost:8000
REACT_APP_ENVIRONMENT=development
```

## Testing

### Unit Tests
```bash
npm test
```

### E2E Tests
```bash
npm run test:e2e
```

## Deployment

### Build
```bash
npm run build
```

### Serve
```bash
npx serve -s build
```

### Docker
```bash
docker build -t common-frontend .
docker run -p 3000:3000 common-frontend
```

## Troubleshooting

### Common Issues
1. **CORS errors**: Check API URL configuration
2. **Build failures**: Clear node_modules and reinstall
3. **TypeScript errors**: Check type definitions

### Development Tips
- Use React DevTools for debugging
- Check browser console for errors
- Use network tab to debug API calls





# Origin Dashboard Setup Guide

This guide explains how to connect the frontend origin dashboard to the backend APIs.

## Environment Configuration

Create a `.env` file in the frontend directory with the following configuration:

```bash
# Backend API Configuration
REACT_APP_API_URL=http://127.0.0.1:8000

# Development Configuration
REACT_APP_ENVIRONMENT=development
REACT_APP_DEBUG=true

# Feature Flags
REACT_APP_ENABLE_ORIGIN_DASHBOARD=true
REACT_APP_ENABLE_FARM_MANAGEMENT=true
REACT_APP_ENABLE_CERTIFICATION_MANAGEMENT=true

# WebSocket Configuration (for real-time updates)
REACT_APP_WS_URL=ws://127.0.0.1:8000/ws
```

## Backend API Endpoints

The origin dashboard connects to the following backend endpoints:

### Origin Data Management
- `GET /api/v1/origin-data/records` - List origin data records
- `POST /api/v1/origin-data/records` - Create origin data record
- `PUT /api/v1/origin-data/records/{id}` - Update origin data record
- `DELETE /api/v1/origin-data/records/{id}` - Delete origin data record
- `POST /api/v1/origin-data/validate` - Validate origin data
- `GET /api/v1/origin-data/requirements/{product_id}` - Get origin data requirements
- `GET /api/v1/origin-data/palm-oil-regions` - Get palm oil regions

### Farm Management
- `GET /api/v1/farm-management/company/{company_id}/farms` - List company farms
- `GET /api/v1/farm-management/company/{company_id}/capabilities` - Get company capabilities
- `POST /api/v1/farm-management/farms` - Create farm
- `PUT /api/v1/farm-management/farms/{id}` - Update farm
- `DELETE /api/v1/farm-management/farms/{id}` - Delete farm
- `POST /api/v1/farm-management/batches` - Create batch with farm contributions
- `GET /api/v1/farm-management/batches/{id}/traceability` - Get batch traceability
- `GET /api/v1/farm-management/batches/{id}/compliance` - Get batch compliance

### Dashboard Metrics
- `GET /api/v2/dashboard/metrics/originator` - Get originator dashboard metrics

## Frontend API Services

The following API services have been created to connect the frontend to the backend:

### 1. Origin API Service (`src/services/originApi.ts`)
Handles all origin data related API calls:
- Origin data CRUD operations
- Origin data validation
- Origin data requirements
- Palm oil regions

### 2. Farm API Service (`src/services/farmApi.ts`)
Handles all farm management related API calls:
- Farm CRUD operations
- Company capabilities
- Batch management
- Farm compliance

### 3. Origin Dashboard Hook (`src/hooks/useOriginDashboard.ts`)
Provides comprehensive data management for the origin dashboard:
- Data fetching and state management
- CRUD operations for origin data and farms
- Auto-refresh capabilities
- Error handling

## Component Updates

The following components have been updated to use real API calls:

### 1. OriginDataManager (`src/components/origin/OriginDataManager.tsx`)
- Now uses `originApi.getOriginDataRecords()` instead of mock data
- Imports types from the API service
- Handles real API responses and errors

### 2. FarmInformationManager (`src/components/origin/FarmInformationManager.tsx`)
- Should be updated to use `farmApi` service
- Replace mock data with real API calls

### 3. CertificationManager (`src/components/origin/CertificationManager.tsx`)
- Should be updated to use `originApi` for certification management
- Replace mock data with real API calls

## Usage Example

```typescript
import { useOriginDashboard } from '../hooks/useOriginDashboard';

const OriginDashboard = () => {
  const {
    originDataRecords,
    farms,
    capabilities,
    metrics,
    isLoading,
    hasError,
    loadAllData,
    createOriginDataRecord,
    createFarm,
    refreshData
  } = useOriginDashboard({
    companyId: user?.company?.id,
    autoLoad: true,
    refreshInterval: 30000 // 30 seconds
  });

  // Use the data in your component
  return (
    <div>
      {isLoading && <LoadingSpinner />}
      {hasError && <ErrorMessage />}
      {/* Render your dashboard components */}
    </div>
  );
};
```

## Testing the Connection

1. Start the backend server:
   ```bash
   cd /Users/elisha/common
   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

2. Start the frontend development server:
   ```bash
   cd /Users/elisha/common/frontend
   npm start
   ```

3. Navigate to the origin dashboard and verify that data loads from the backend

## Troubleshooting

### Common Issues

1. **CORS Errors**: Ensure the backend CORS configuration includes the frontend URL
2. **Authentication Errors**: Verify that the user is properly authenticated
3. **API Endpoint Not Found**: Check that the backend routes are properly registered
4. **Data Not Loading**: Check the browser console for API errors

### Debug Steps

1. Check browser network tab for failed API calls
2. Verify backend logs for incoming requests
3. Ensure environment variables are set correctly
4. Check that the user has proper permissions for origin data access

## Next Steps

1. Update remaining components to use the new API services
2. Add proper error handling and loading states
3. Implement real-time updates using WebSocket connections
4. Add data validation and form handling
5. Implement proper caching and optimization

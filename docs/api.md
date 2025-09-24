# API Documentation

## Base URL
- **Development**: `http://localhost:8000`
- **Production**: [Your production URL]

## Authentication

### Login
```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "admin@testmanufacturer.com",
  "password": "TestPass123!"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "access_expires_in": 1800,
  "refresh_expires_in": 604800
}
```

### Using the Token
Include the token in the Authorization header:
```http
Authorization: Bearer <your_access_token>
```

## Core Endpoints

### Companies
- `GET /api/v1/companies` - List companies
- `POST /api/v1/companies` - Create company
- `GET /api/v1/companies/{id}` - Get company details
- `PUT /api/v1/companies/{id}` - Update company
- `DELETE /api/v1/companies/{id}` - Delete company

### Products
- `GET /api/v1/products` - List products
- `POST /api/v1/products` - Create product
- `GET /api/v1/products/{id}` - Get product details

### Purchase Orders
- `GET /api/v1/purchase-orders` - List purchase orders
- `POST /api/v1/purchase-orders` - Create purchase order
- `GET /api/v1/purchase-orders/{id}` - Get purchase order details
- `PUT /api/v1/purchase-orders/{id}` - Update purchase order

### Users
- `GET /api/v1/users` - List users
- `POST /api/v1/users` - Create user
- `GET /api/v1/users/{id}` - Get user details

## Error Handling

All API responses follow a consistent error format:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable error message",
    "details": "Additional error details",
    "severity": "error|warning|info"
  },
  "request_id": "unique-request-id",
  "timestamp": "2025-09-22T01:59:25.261299Z"
}
```

## Rate Limiting

- **Login attempts**: 5 per minute per IP
- **API calls**: 100 per minute per user
- **Bulk operations**: 10 per minute per user

## CORS

The API supports CORS for the following origins:
- `http://localhost:3000`
- `http://localhost:3001`
- `http://127.0.0.1:3000`
- `http://127.0.0.1:3001`

## Interactive Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc




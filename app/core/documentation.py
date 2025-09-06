"""
Enhanced OpenAPI documentation configuration for the Common supply chain platform.
"""
from typing import Dict, Any, List
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.responses import HTMLResponse

from app.core.config import settings


def custom_openapi(app: FastAPI) -> Dict[str, Any]:
    """
    Generate custom OpenAPI schema with enhanced documentation.
    
    Args:
        app: FastAPI application instance
        
    Returns:
        Enhanced OpenAPI schema
    """
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="Common Supply Chain Platform API",
        version=settings.app_version,
        description="""
# Common Supply Chain Platform API

A comprehensive supply chain transparency platform that replaces contradictory declarations 
with a single, shared Purchase Order (PO) system.

## Key Features

- **Unified Purchase Order System**: Single source of truth for supply chain transactions
- **Dual Confirmation Model**: Different interfaces for processors vs originators
- **Transparency Calculations**: Real-time supply chain visibility scoring
- **Viral Onboarding**: Cascade supplier invitation system
- **Business Relationship Management**: Sophisticated data sharing controls
- **Background Processing**: Async transparency calculations with Celery
- **Comprehensive Audit**: Full transaction history and event logging

## Authentication

This API uses JWT (JSON Web Token) authentication. Include the token in the Authorization header:

```
Authorization: Bearer <your-jwt-token>
```

## Rate Limiting

API endpoints are rate limited to ensure fair usage:
- **Standard endpoints**: 100 requests per minute per user
- **Heavy computation endpoints**: 10 requests per minute per user
- **Authentication endpoints**: 5 requests per minute per IP

## Error Handling

The API returns standardized error responses:

```json
{
    "detail": "Error description",
    "error_code": "SPECIFIC_ERROR_CODE",
    "request_id": "uuid-request-id",
    "timestamp": "2025-01-01T00:00:00Z"
}
```

## Versioning

API versioning is handled through URL prefixes:
- **v1**: `/api/v1/` (current stable version)
- **v2**: `/api/v2/` (future version)

## Data Models

### Core Entities
- **Company**: Organizations in the supply chain
- **User**: Platform users with role-based access
- **Product**: Catalog of tradeable products
- **PurchaseOrder**: Core transaction records
- **BusinessRelationship**: Inter-company connections

### Transparency Models
- **TransparencyResult**: Calculated transparency scores
- **OriginData**: Geographic and certification data
- **Batch**: Traceability tracking units

## Business Logic

### Transparency Calculation
The platform calculates transparency scores using a weighted graph traversal algorithm:
1. **TTM (Transparency to Mill)**: Tracks processing transparency
2. **TTP (Transparency to Plantation)**: Tracks origin transparency
3. **Degradation Factors**: Applied at each transformation step

### Viral Onboarding
Companies can invite suppliers, creating a viral growth cascade:
1. **Invitation Tracking**: Monitor invitation chains
2. **Acceptance Analytics**: Measure conversion rates
3. **Network Effects**: Analyze growth patterns

## Security

### Data Protection
- **Encryption**: All data encrypted in transit and at rest
- **Access Control**: Role-based permissions with company isolation
- **Audit Logging**: Comprehensive activity tracking

### Compliance
- **GDPR**: Data protection and privacy controls
- **SOC 2**: Security and availability standards
- **Industry Standards**: Supply chain compliance requirements
        """,
        routes=app.routes,
        tags=[
            {
                "name": "Health",
                "description": "System health and status endpoints"
            },
            {
                "name": "Authentication", 
                "description": "User authentication and authorization"
            },
            {
                "name": "Products",
                "description": "Product catalog management"
            },
            {
                "name": "Purchase Orders",
                "description": "Core purchase order operations"
            },
            {
                "name": "Confirmation",
                "description": "PO confirmation with dual interface model"
            },
            {
                "name": "Traceability",
                "description": "Supply chain traceability and transparency"
            },
            {
                "name": "Transparency Jobs",
                "description": "Background transparency calculation jobs"
            },
            {
                "name": "Notifications",
                "description": "System notifications and alerts"
            },
            {
                "name": "Audit",
                "description": "Audit logging and compliance tracking"
            },
            {
                "name": "Data Access",
                "description": "Cross-company data access controls"
            },
            {
                "name": "Transparency Visualization",
                "description": "Supply chain visualization and gap analysis"
            },
            {
                "name": "Viral Analytics",
                "description": "Viral onboarding and network effect analytics"
            },
            {
                "name": "Origin Data",
                "description": "Geographic and certification data management"
            },
            {
                "name": "Business Relationships",
                "description": "Inter-company relationship management"
            },
            {
                "name": "Batch Tracking",
                "description": "Batch-level traceability tracking"
            }
        ]
    )
    
    # Add security schemes
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "JWT token obtained from /auth/login endpoint"
        }
    }
    
    # Add global security requirement
    openapi_schema["security"] = [{"BearerAuth": []}]
    
    # Add custom extensions
    openapi_schema["info"]["x-logo"] = {
        "url": "https://common.supply/logo.png",
        "altText": "Common Supply Chain Platform"
    }
    
    openapi_schema["info"]["contact"] = {
        "name": "Common Support",
        "url": "https://common.supply/support",
        "email": "support@common.supply"
    }
    
    openapi_schema["info"]["license"] = {
        "name": "Proprietary",
        "url": "https://common.supply/license"
    }
    
    # Add servers
    openapi_schema["servers"] = [
        {
            "url": settings.api_base_url,
            "description": "Production server"
        },
        {
            "url": "http://localhost:8000",
            "description": "Development server"
        }
    ]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


def get_custom_swagger_ui_html(
    openapi_url: str = "/openapi.json",
    title: str = "Common API Documentation",
) -> HTMLResponse:
    """
    Generate custom Swagger UI HTML with enhanced styling.
    
    Args:
        openapi_url: URL to OpenAPI schema
        title: Page title
        
    Returns:
        Custom Swagger UI HTML response
    """
    return get_swagger_ui_html(
        openapi_url=openapi_url,
        title=title,
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui.css",
        swagger_ui_parameters={
            "deepLinking": True,
            "displayRequestDuration": True,
            "docExpansion": "none",
            "operationsSorter": "alpha",
            "filter": True,
            "showExtensions": True,
            "showCommonExtensions": True,
            "tryItOutEnabled": True
        }
    )


def get_custom_redoc_html(
    openapi_url: str = "/openapi.json",
    title: str = "Common API Documentation",
) -> HTMLResponse:
    """
    Generate custom ReDoc HTML with enhanced styling.
    
    Args:
        openapi_url: URL to OpenAPI schema
        title: Page title
        
    Returns:
        Custom ReDoc HTML response
    """
    return get_redoc_html(
        openapi_url=openapi_url,
        title=title,
        redoc_js_url="https://cdn.jsdelivr.net/npm/redoc@2.1.3/bundles/redoc.standalone.js",
        with_google_fonts=True
    )


def add_response_examples(openapi_schema: Dict[str, Any]) -> None:
    """
    Add response examples to OpenAPI schema.
    
    Args:
        openapi_schema: OpenAPI schema to enhance
    """
    # Add common error response examples
    error_examples = {
        "400": {
            "description": "Bad Request",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Invalid request data",
                        "error_code": "VALIDATION_ERROR",
                        "request_id": "123e4567-e89b-12d3-a456-426614174000",
                        "timestamp": "2025-01-01T00:00:00Z"
                    }
                }
            }
        },
        "401": {
            "description": "Unauthorized",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Could not validate credentials",
                        "error_code": "AUTHENTICATION_ERROR",
                        "request_id": "123e4567-e89b-12d3-a456-426614174000",
                        "timestamp": "2025-01-01T00:00:00Z"
                    }
                }
            }
        },
        "403": {
            "description": "Forbidden",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Insufficient permissions",
                        "error_code": "AUTHORIZATION_ERROR",
                        "request_id": "123e4567-e89b-12d3-a456-426614174000",
                        "timestamp": "2025-01-01T00:00:00Z"
                    }
                }
            }
        },
        "404": {
            "description": "Not Found",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Resource not found",
                        "error_code": "NOT_FOUND_ERROR",
                        "request_id": "123e4567-e89b-12d3-a456-426614174000",
                        "timestamp": "2025-01-01T00:00:00Z"
                    }
                }
            }
        },
        "429": {
            "description": "Too Many Requests",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Rate limit exceeded",
                        "error_code": "RATE_LIMIT_ERROR",
                        "request_id": "123e4567-e89b-12d3-a456-426614174000",
                        "timestamp": "2025-01-01T00:00:00Z",
                        "retry_after": 60
                    }
                }
            }
        },
        "500": {
            "description": "Internal Server Error",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Internal server error",
                        "error_code": "INTERNAL_ERROR",
                        "request_id": "123e4567-e89b-12d3-a456-426614174000",
                        "timestamp": "2025-01-01T00:00:00Z"
                    }
                }
            }
        }
    }
    
    # Add error examples to all paths
    if "paths" in openapi_schema:
        for path_data in openapi_schema["paths"].values():
            for operation_data in path_data.values():
                if isinstance(operation_data, dict) and "responses" in operation_data:
                    for status_code, example in error_examples.items():
                        if status_code not in operation_data["responses"]:
                            operation_data["responses"][status_code] = example

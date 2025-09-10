# Phase 3: Pre-Built Enterprise Connector Architecture

## Overview

This document defines the technical architecture and specifications for Phase 3 pre-built enterprise connectors. These connectors will provide plug-and-play integration between Common's API and major middleware platforms, dramatically reducing enterprise integration time from weeks to days.

## Common API Surface for Connectors

### Core API Endpoints

**Authentication:**
- `POST /api/v1/auth/login` - JWT token authentication
- `POST /api/v1/auth/refresh` - Token refresh
- Bearer token authentication for all API calls

**Purchase Orders:**
- `POST /api/v1/purchase-orders` - Create purchase order
- `GET /api/v1/purchase-orders` - List purchase orders (with filtering)
- `GET /api/v1/purchase-orders/{id}` - Get purchase order details
- `PUT /api/v1/purchase-orders/{id}` - Update purchase order
- `POST /api/v1/purchase-orders/{id}/seller-confirm` - Seller confirmation

**Amendment System (Phase 1 MVP):**
- `PUT /api/v1/purchase-orders/{id}/propose-changes` - Propose amendments
- `PUT /api/v1/purchase-orders/{id}/approve-changes` - Approve/reject amendments

**ERP Sync (Phase 2 Enterprise):**
- `GET /api/v1/erp-sync/status` - Get sync status
- `GET /api/v1/erp-sync/pending-updates` - Poll for updates
- `POST /api/v1/erp-sync/acknowledge` - Acknowledge processed updates
- `POST /api/v1/erp-sync/webhook-test` - Test webhook connectivity

**Companies & Relationships:**
- `GET /api/v1/companies` - List companies
- `GET /api/v1/business-relationships` - List business relationships
- `POST /api/v1/business-relationships/invite-supplier` - Invite suppliers

### Data Schemas

**PurchaseOrder Schema:**
```json
{
  "id": "uuid",
  "po_number": "string",
  "buyer_company_id": "uuid",
  "seller_company_id": "uuid",
  "product_id": "uuid",
  "quantity": "decimal",
  "unit_price": "decimal",
  "total_amount": "decimal",
  "unit": "string",
  "delivery_date": "date",
  "delivery_location": "string",
  "status": "enum",
  "amendment_status": "enum",
  "proposed_quantity": "decimal",
  "amendment_reason": "string",
  "erp_sync_status": "enum"
}
```

**Amendment Schema:**
```json
{
  "proposed_quantity": "decimal",
  "proposed_quantity_unit": "string",
  "amendment_reason": "string",
  "approve": "boolean",
  "buyer_notes": "string"
}
```

## Connector Architecture Patterns

### 1. Authentication Pattern

**Standard OAuth 2.0 / JWT Flow:**
```
1. Connector authenticates with Common API using client credentials
2. Receives JWT access token
3. Includes Bearer token in all API requests
4. Handles token refresh automatically
5. Stores credentials securely in middleware platform
```

**Configuration Parameters:**
- `common_api_base_url`: Common API base URL
- `client_id`: OAuth client ID
- `client_secret`: OAuth client secret
- `company_id`: Company UUID for data filtering

### 2. Data Mapping Pattern

**Standardized Field Mappings:**
```
Common Field → ERP Field
po_number → PurchaseOrderNumber
quantity → OrderQuantity
unit_price → UnitPrice
delivery_date → RequestedDeliveryDate
status → OrderStatus
```

**Transformation Templates:**
- Decimal precision handling (Common uses 3 decimal places for quantity, 2 for price)
- Date format conversion (Common uses ISO 8601)
- Enum value mapping (status codes)
- Currency code handling

### 3. Error Handling Pattern

**Standard Error Response:**
```json
{
  "error_code": "VALIDATION_ERROR",
  "detail": "Request validation failed",
  "request_id": "uuid",
  "timestamp": "iso_datetime"
}
```

**Retry Logic:**
- Exponential backoff for transient errors
- Circuit breaker for persistent failures
- Dead letter queue for failed messages
- Comprehensive logging and monitoring

### 4. Sync Pattern (Phase 2)

**Real-time Webhook:**
```
1. Common sends webhook to ERP system when amendment approved
2. ERP system processes update and responds with 200 OK
3. Common marks sync as successful
4. Retry logic for failed webhooks
```

**Polling-based Sync:**
```
1. ERP system polls /api/v1/erp-sync/pending-updates
2. Processes updates locally
3. Calls /api/v1/erp-sync/acknowledge to confirm processing
4. Common marks updates as synced
```

## Platform-Specific Requirements

### MuleSoft Anypoint Connector

**Technical Requirements:**
- Mule SDK 1.1+ compatibility
- Mule 4 Runtime Engine support
- Anypoint Studio 7+ integration
- DataWeave transformation support

**Deliverables:**
- `.jar` connector package
- Anypoint Exchange listing
- DataWeave transformation templates
- Configuration property templates
- Connection testing utilities

**Key Features:**
- Visual flow designer integration
- Pre-built operations for all Common endpoints
- Automatic pagination handling
- Built-in error handling and retry logic
- DataWeave mappings for common ERP systems

### Dell Boomi Connector

**Technical Requirements:**
- Boomi Process Library compatibility
- AtomSphere platform integration
- REST connector framework
- JSON/XML transformation support

**Deliverables:**
- Process Library package (`.bpl` file)
- Connection profile templates
- Standard transformation maps
- Error handling processes
- Documentation and setup guides

**Key Features:**
- Drag-and-drop process design
- Pre-configured connection profiles
- Standard data transformation maps
- Built-in retry and error handling
- Batch processing capabilities

### SAP Integration Templates

**Technical Requirements:**
- SAP RFC/BAPI connectivity
- IDoc processing capabilities
- REST adapter configuration
- SAP PI/PO integration

**Deliverables:**
- RFC function module templates
- IDoc message types and segments
- REST service configurations
- Field mapping documentation
- ABAP code samples

**Key Features:**
- Standard purchase order IDocs
- RFC-enabled function modules
- REST service endpoints
- Field mapping for MM/SD modules
- Error handling and logging

### Microsoft Integration Connectors

**Technical Requirements:**
- BizTalk Server 2020+ compatibility
- Power Automate custom connector
- Logic Apps connector
- Azure Integration Services support

**Deliverables:**
- BizTalk adapter assemblies
- Power Automate connector package
- Logic Apps ARM templates
- Azure Function implementations
- PowerShell deployment scripts

**Key Features:**
- Visual workflow designer integration
- Pre-built triggers and actions
- Automatic schema generation
- Built-in authentication handling
- Office 365 integration capabilities

## Security Considerations

### Authentication Security
- OAuth 2.0 client credentials flow
- JWT token validation and refresh
- Secure credential storage in middleware platforms
- API key rotation support

### Data Security
- TLS 1.2+ for all communications
- Request/response encryption
- Audit logging for all operations
- PII data handling compliance

### Network Security
- Webhook signature validation
- IP allowlisting support
- VPN/private network connectivity
- Firewall configuration guidance

## Testing Strategy

### Unit Testing
- Connector operation testing
- Data transformation validation
- Error handling verification
- Authentication flow testing

### Integration Testing
- End-to-end workflow testing
- ERP system sandbox testing
- Performance and load testing
- Security penetration testing

### Enterprise Validation
- Customer sandbox environments
- Production-like data volumes
- Multi-tenant testing
- Compliance validation

## Documentation Requirements

### Installation Guides
- Step-by-step setup instructions
- Prerequisites and dependencies
- Configuration parameter reference
- Troubleshooting guides

### Developer Documentation
- API reference documentation
- Code samples and examples
- Best practices and patterns
- Migration guides

### User Documentation
- Business process workflows
- Data mapping guides
- Monitoring and alerting setup
- Support and maintenance procedures

## Success Metrics

### Technical Metrics
- Integration time: < 3 days (vs 4-12 weeks)
- Setup complexity: < 10 configuration steps
- Error rate: < 1% for standard operations
- Performance: < 2 second response times

### Business Metrics
- Enterprise adoption acceleration: 5x faster
- Support ticket reduction: 80% fewer integration issues
- Customer satisfaction: > 90% satisfaction score
- Time to value: < 1 week from installation to production

## Next Steps

1. **Research Phase**: Complete platform-specific research and requirements
2. **Architecture Design**: Finalize connector architecture patterns
3. **Development Phase**: Build connectors in priority order (MuleSoft, Boomi, SAP)
4. **Testing Phase**: Comprehensive testing with enterprise sandboxes
5. **Documentation Phase**: Create complete documentation packages
6. **Release Phase**: Package and distribute connectors to enterprise customers

This architecture provides the foundation for building enterprise-grade connectors that will dramatically accelerate Common's adoption in large organizations.

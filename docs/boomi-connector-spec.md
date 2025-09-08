# Dell Boomi Connector Specification

## Executive Summary

The Common Supply Chain Transparency Platform Connector for Dell Boomi provides a comprehensive Process Library that enables seamless integration between the Common platform and enterprise ERP systems through Dell Boomi's AtomSphere integration platform. This connector transforms complex API integrations into simple, visual process flows that can be configured and deployed by integration specialists without extensive coding.

## Business Value Proposition

### Integration Acceleration
- **Reduces integration time from 4-12 weeks to 1-3 days**
- **Pre-built processes eliminate 80% of custom development**
- **Visual process design requires no coding expertise**
- **Drag-and-drop configuration for rapid deployment**

### Enterprise-Grade Features
- **OAuth 2.0 authentication with automatic token management**
- **Comprehensive error handling and retry logic**
- **Batch processing for high-volume operations**
- **Real-time monitoring and alerting**
- **Audit logging and compliance tracking**

### ERP Integration Support
- **SAP integration with native field mappings**
- **Oracle ERP Cloud compatibility**
- **Generic ERP system support**
- **Bi-directional synchronization capabilities**

## Technical Requirements

### Platform Compatibility
- **Boomi AtomSphere**: 2021.1 or higher
- **Atom Runtime**: 4.3.0 or higher
- **Process Library**: 2.0 format
- **Connector Framework**: REST/HTTP based
- **Data Formats**: JSON, XML, CSV support

### Dependencies
- Boomi REST connector
- JSON/XML processing shapes
- HTTP client connector
- Data transformation maps
- Error handling processes

## Process Library Components

### 1. Connection Profiles

**Common API Connection Profile**
```json
{
  "name": "Common API Connection",
  "type": "REST",
  "baseUrl": "https://api.common.co",
  "authentication": {
    "type": "OAuth2",
    "grantType": "client_credentials",
    "tokenUrl": "https://api.common.co/api/v1/auth/token",
    "clientId": "${common.client.id}",
    "clientSecret": "${common.client.secret}"
  },
  "headers": {
    "Content-Type": "application/json",
    "Accept": "application/json"
  },
  "timeout": 30000,
  "retryAttempts": 3
}
```

**Connection Parameters:**
- `common.client.id`: OAuth client ID
- `common.client.secret`: OAuth client secret
- `common.company.id`: Company UUID for filtering
- `common.api.base.url`: API base URL (default: https://api.common.co)

### 2. Standard Processes

**A. Authentication Process**
- **Process Name**: `Common_Authenticate`
- **Description**: Obtain JWT access token from Common API
- **Input**: Connection parameters
- **Output**: JWT access token
- **Error Handling**: Authentication failures, network timeouts

**Process Flow:**
1. HTTP Client → POST /api/v1/auth/token
2. JSON Parser → Extract access_token
3. Set Property → Store token for subsequent calls
4. Decision → Check authentication success

**B. Purchase Order Creation Process**
- **Process Name**: `Common_Create_PurchaseOrder`
- **Description**: Create purchase order in Common platform
- **Input**: Purchase order data (JSON/XML)
- **Output**: Created purchase order with Common ID
- **Transformation**: ERP format → Common API format

**Process Flow:**
1. Data Process → Transform input data
2. Map → Apply field mappings
3. HTTP Client → POST /api/v1/purchase-orders
4. JSON Parser → Extract response
5. Decision → Handle success/error responses

**C. Amendment Proposal Process**
- **Process Name**: `Common_Propose_Amendment`
- **Description**: Propose changes to existing purchase order
- **Input**: PO ID and amendment data
- **Output**: Amendment response with status
- **Business Logic**: Validate seller permissions

**Process Flow:**
1. Data Process → Validate input parameters
2. Map → Transform amendment data
3. HTTP Client → PUT /api/v1/purchase-orders/{id}/propose-changes
4. JSON Parser → Extract amendment response
5. Decision → Route based on success/failure

**D. ERP Sync Polling Process**
- **Process Name**: `Common_Poll_Updates`
- **Description**: Poll for pending ERP updates
- **Input**: Since timestamp, company ID
- **Output**: List of pending updates
- **Schedule**: Configurable polling interval

**Process Flow:**
1. Get Property → Retrieve last sync timestamp
2. HTTP Client → GET /api/v1/erp-sync/pending-updates
3. JSON Parser → Extract pending updates
4. For Each → Process each update
5. HTTP Client → POST /api/v1/erp-sync/acknowledge
6. Set Property → Update last sync timestamp

### 3. Data Transformation Maps

**A. ERP to Common Purchase Order Map**
```json
{
  "mapName": "ERP_to_Common_PO",
  "sourceFormat": "JSON",
  "targetFormat": "JSON",
  "mappings": [
    {
      "source": "vendorId",
      "target": "seller_company_id",
      "transformation": "lookup_company_id"
    },
    {
      "source": "orderQuantity",
      "target": "quantity",
      "transformation": "to_decimal"
    },
    {
      "source": "unitPrice",
      "target": "unit_price",
      "transformation": "to_decimal_2"
    },
    {
      "source": "deliveryDate",
      "target": "delivery_date",
      "transformation": "to_iso_date"
    },
    {
      "source": "unitOfMeasure",
      "target": "unit",
      "transformation": "standardize_uom"
    }
  ]
}
```

**B. Common to SAP IDoc Map**
```json
{
  "mapName": "Common_to_SAP_IDoc",
  "sourceFormat": "JSON",
  "targetFormat": "XML",
  "mappings": [
    {
      "source": "po_number",
      "target": "ORDERS05/IDOC/E1EDK01/BELNR"
    },
    {
      "source": "quantity",
      "target": "ORDERS05/IDOC/E1EDP01/MENGE"
    },
    {
      "source": "unit_price",
      "target": "ORDERS05/IDOC/E1EDP01/NETPR"
    },
    {
      "source": "delivery_date",
      "target": "ORDERS05/IDOC/E1EDP01/EINDT",
      "transformation": "to_sap_date"
    }
  ]
}
```

**C. Oracle ERP Transformation Map**
```json
{
  "mapName": "Common_to_Oracle_ERP",
  "sourceFormat": "JSON",
  "targetFormat": "JSON",
  "mappings": [
    {
      "source": "po_number",
      "target": "segment1"
    },
    {
      "source": "quantity",
      "target": "quantity"
    },
    {
      "source": "unit_price",
      "target": "unit_price"
    },
    {
      "source": "delivery_date",
      "target": "need_by_date",
      "transformation": "to_oracle_date"
    }
  ]
}
```

### 4. Error Handling Processes

**A. Standard Error Handler**
- **Process Name**: `Common_Error_Handler`
- **Description**: Centralized error handling for all Common operations
- **Input**: Error details and context
- **Output**: Formatted error response
- **Features**: Retry logic, dead letter queue, alerting

**Error Types:**
1. **Authentication Errors**: Token refresh and retry
2. **Validation Errors**: Data validation and user notification
3. **Rate Limiting**: Exponential backoff and retry
4. **Network Errors**: Circuit breaker and failover
5. **Business Logic Errors**: Custom error handling per operation

**B. Retry Process**
- **Process Name**: `Common_Retry_Logic`
- **Description**: Configurable retry mechanism with exponential backoff
- **Parameters**: Max retries, initial delay, backoff multiplier
- **Features**: Dead letter queue for permanent failures

### 5. Monitoring and Logging

**A. Process Execution Tracking**
- Process start/end timestamps
- Input/output data logging
- Error occurrence tracking
- Performance metrics collection

**B. Business Process Monitoring**
- Purchase order creation success rates
- Amendment approval cycle times
- ERP sync success/failure rates
- Data transformation accuracy

**C. Alerting Configuration**
- Failed authentication alerts
- High error rate notifications
- ERP sync failure alerts
- Performance degradation warnings

## Configuration Templates

### Environment-Specific Properties

**Development Environment:**
```properties
# Common API Configuration
common.api.base.url=https://api-dev.common.co
common.client.id=dev_client_id
common.client.secret=dev_client_secret
common.company.id=dev_company_uuid

# Polling Configuration
common.poll.interval=300000  # 5 minutes
common.poll.batch.size=100

# Retry Configuration
common.retry.max.attempts=3
common.retry.initial.delay=1000
common.retry.backoff.multiplier=2
```

**Production Environment:**
```properties
# Common API Configuration
common.api.base.url=https://api.common.co
common.client.id=${COMMON_CLIENT_ID}
common.client.secret=${COMMON_CLIENT_SECRET}
common.company.id=${COMMON_COMPANY_ID}

# Polling Configuration
common.poll.interval=60000   # 1 minute
common.poll.batch.size=500

# Retry Configuration
common.retry.max.attempts=5
common.retry.initial.delay=2000
common.retry.backoff.multiplier=1.5
```

### Security Configuration

**TLS/SSL Settings:**
```json
{
  "tlsContext": {
    "enabledProtocols": ["TLSv1.2", "TLSv1.3"],
    "trustStore": {
      "path": "common-truststore.jks",
      "password": "${tls.truststore.password}",
      "type": "JKS"
    },
    "keyStore": {
      "path": "client-keystore.jks",
      "password": "${tls.keystore.password}",
      "type": "JKS"
    }
  }
}
```

**OAuth Configuration:**
```json
{
  "oauth": {
    "grantType": "client_credentials",
    "tokenUrl": "https://api.common.co/api/v1/auth/token",
    "scope": "purchase_orders amendments erp_sync",
    "tokenRefreshThreshold": 300
  }
}
```

## Deployment Package

### Process Library Structure
```
Common_Connector_v1.0.bpl
├── Processes/
│   ├── Authentication/
│   │   └── Common_Authenticate.xml
│   ├── PurchaseOrders/
│   │   ├── Common_Create_PurchaseOrder.xml
│   │   ├── Common_Get_PurchaseOrder.xml
│   │   └── Common_List_PurchaseOrders.xml
│   ├── Amendments/
│   │   ├── Common_Propose_Amendment.xml
│   │   └── Common_Approve_Amendment.xml
│   ├── ERPSync/
│   │   ├── Common_Poll_Updates.xml
│   │   └── Common_Acknowledge_Updates.xml
│   └── ErrorHandling/
│       ├── Common_Error_Handler.xml
│       └── Common_Retry_Logic.xml
├── Maps/
│   ├── ERP_to_Common_PO.xml
│   ├── Common_to_SAP_IDoc.xml
│   └── Common_to_Oracle_ERP.xml
├── Connections/
│   └── Common_API_Connection.xml
└── Documentation/
    ├── Installation_Guide.pdf
    ├── Configuration_Guide.pdf
    └── User_Manual.pdf
```

### Installation Steps

1. **Download Process Library**
   - Download Common_Connector_v1.0.bpl from Boomi Community
   - Verify package integrity and version compatibility

2. **Import to AtomSphere**
   - Login to Boomi AtomSphere platform
   - Navigate to Build → Components → Process Libraries
   - Click "Import" and select the .bpl file
   - Confirm import and review imported components

3. **Configure Connection**
   - Navigate to Manage → Atom Management → Connections
   - Create new connection using "Common API Connection" template
   - Configure authentication parameters
   - Test connection using "Test Connection" button

4. **Deploy Processes**
   - Select required processes from the library
   - Configure environment-specific properties
   - Deploy to target Atom or Molecule
   - Monitor deployment status and logs

5. **Validate Integration**
   - Run test purchase order creation process
   - Verify data transformation accuracy
   - Test error handling scenarios
   - Monitor process execution logs

This specification provides the complete technical foundation for building a production-ready Dell Boomi connector for the Common platform.

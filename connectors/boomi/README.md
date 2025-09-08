# Common Supply Chain Connector for Dell Boomi

The Common Supply Chain Connector for Dell Boomi provides a comprehensive Process Library for seamless integration with the Common supply chain transparency platform. This connector enables enterprises to integrate purchase order management, amendment workflows, and ERP synchronization into their existing Boomi integration processes.

## Features

### Core Components
- **Connection Profiles**: Pre-configured connections to Common API with OAuth 2.0
- **Standard Processes**: Ready-to-use processes for all Common API operations
- **Data Transformation Maps**: Field mappings for common ERP systems (SAP, Oracle, etc.)
- **Error Handling Processes**: Comprehensive error handling and retry logic
- **Batch Processing**: Support for bulk operations and data synchronization

### Process Library Contents
- **Purchase Order Management**: Create, read, update, and list purchase orders
- **Amendment Workflow**: Propose and approve changes to existing purchase orders
- **ERP Synchronization**: Bi-directional sync with enterprise ERP systems
- **Data Validation**: Input validation and data quality checks
- **Audit Logging**: Comprehensive audit trail and monitoring

### Enterprise Features
- **OAuth 2.0 Authentication**: Secure API access with automatic token management
- **Connection Pooling**: Efficient connection management and reuse
- **Retry Logic**: Configurable retry mechanisms for transient failures
- **Error Notifications**: Email and webhook notifications for failures
- **Performance Monitoring**: Built-in performance metrics and alerting

## Installation

### Prerequisites
- Dell Boomi AtomSphere Platform access
- Boomi Atom or Molecule runtime environment
- Common API credentials (Client ID and Client Secret)
- Network connectivity to api.common.co (HTTPS/443)

### Installation Steps

1. **Download Process Library Package**
   ```bash
   # Download from Common's connector repository
   wget https://releases.common.co/connectors/boomi/common-boomi-connector-1.0.0.zip
   ```

2. **Import into Boomi AtomSphere**
   - Log into your Boomi AtomSphere account
   - Navigate to "Build" → "Components"
   - Click "Import" → "Process Library Package"
   - Select the downloaded ZIP file
   - Click "Import"

3. **Configure Connection Profile**
   - Navigate to "Manage" → "AtomSphere Management"
   - Go to "Setup" → "Connections"
   - Find "Common API Connection"
   - Configure with your API credentials

4. **Deploy Processes**
   - Select the processes you want to use
   - Deploy to your target Atom/Molecule
   - Test the connection and processes

## Configuration

### Connection Profile Setup

The Common API Connection profile requires the following parameters:

| Parameter | Required | Description | Example |
|-----------|----------|-------------|---------|
| **Base URL** | Yes | Common API base URL | `https://api.common.co` |
| **Client ID** | Yes | OAuth client ID | `your-client-id` |
| **Client Secret** | Yes | OAuth client secret | `your-client-secret` |
| **Company ID** | Yes | Company UUID for data filtering | `your-company-uuid` |
| **Timeout** | No | Request timeout (seconds) | `30` |
| **Max Retries** | No | Maximum retry attempts | `3` |
| **Environment** | No | Environment identifier | `production` |

### Environment-Specific Configuration

#### Development Environment
```properties
Base URL: https://api-dev.common.co
Client ID: dev-client-id
Client Secret: dev-client-secret
Company ID: dev-company-uuid
Timeout: 30
Max Retries: 3
Environment: development
```

#### Production Environment
```properties
Base URL: https://api.common.co
Client ID: prod-client-id
Client Secret: prod-client-secret
Company ID: prod-company-uuid
Timeout: 60
Max Retries: 5
Environment: production
```

## Process Library Components

### 1. Connection Profiles

#### Common API Connection
- **Type**: HTTP Client Connection
- **Authentication**: OAuth 2.0 Client Credentials
- **Features**: Automatic token refresh, connection pooling
- **Configuration**: Environment-specific parameters

### 2. Standard Processes

#### Purchase Order Operations
- **Create Purchase Order**: Creates new purchase orders in Common
- **Get Purchase Order**: Retrieves purchase order by ID
- **List Purchase Orders**: Retrieves purchase orders with filtering
- **Update Purchase Order**: Updates existing purchase orders
- **Delete Purchase Order**: Soft deletes purchase orders

#### Amendment Workflow
- **Propose Changes**: Proposes amendments to purchase orders
- **Approve Changes**: Approves or rejects proposed amendments
- **Get Amendment History**: Retrieves amendment audit trail

#### ERP Synchronization
- **Sync to ERP**: Pushes Common data to ERP systems
- **Sync from ERP**: Pulls ERP data into Common
- **Batch Sync**: Handles bulk synchronization operations
- **Sync Status Check**: Monitors synchronization status

### 3. Data Transformation Maps

#### SAP Integration Maps
- **SAP to Common PO**: Maps SAP purchase order to Common format
- **Common to SAP PO**: Maps Common purchase order to SAP format
- **SAP Amendment Map**: Handles amendment data transformation
- **SAP Error Map**: Maps SAP error responses

#### Oracle Integration Maps
- **Oracle to Common PO**: Maps Oracle purchase order to Common format
- **Common to Oracle PO**: Maps Common purchase order to Oracle format
- **Oracle Batch Map**: Handles bulk Oracle operations

#### Generic ERP Maps
- **Generic to Common**: Standard ERP to Common transformation
- **Common to Generic**: Standard Common to ERP transformation
- **Error Response Map**: Standard error handling transformation

### 4. Error Handling Processes

#### Standard Error Handler
- **Retry Logic**: Configurable retry with exponential backoff
- **Error Classification**: Categorizes errors (transient, permanent, etc.)
- **Notification**: Email and webhook notifications
- **Logging**: Comprehensive error logging

#### Business Error Handler
- **Validation Errors**: Handles data validation failures
- **Business Rule Errors**: Handles business logic violations
- **Recovery Processes**: Automatic and manual recovery options

### 5. Utility Processes

#### Data Validation
- **Purchase Order Validator**: Validates PO data before submission
- **Amendment Validator**: Validates amendment requests
- **Company Validator**: Validates company information

#### Monitoring and Logging
- **Performance Monitor**: Tracks process performance metrics
- **Audit Logger**: Creates comprehensive audit trails
- **Health Check**: Monitors system health and connectivity

## Usage Examples

### Example 1: Create Purchase Order from SAP

```
Process Flow:
1. SAP Data Input → 2. SAP to Common Map → 3. Data Validation → 4. Create PO Process → 5. Success/Error Handling
```

**Configuration:**
- Input: SAP purchase order data (XML/JSON)
- Transformation: Use "SAP to Common PO" map
- Validation: Apply "Purchase Order Validator"
- Output: Common purchase order response

### Example 2: Amendment Workflow

```
Process Flow:
1. Amendment Request → 2. Amendment Validator → 3. Propose Changes → 4. Notification → 5. Approval Process
```

**Configuration:**
- Input: Amendment request data
- Validation: Apply "Amendment Validator"
- Process: Use "Propose Changes" process
- Notification: Configure email/webhook alerts

### Example 3: Batch ERP Synchronization

```
Process Flow:
1. Scheduled Trigger → 2. List Purchase Orders → 3. Filter Changed → 4. Batch Transform → 5. ERP Sync → 6. Status Update
```

**Configuration:**
- Schedule: Configure timer (e.g., every 15 minutes)
- Filter: Only sync modified purchase orders
- Transform: Use appropriate ERP transformation map
- Sync: Use "Batch Sync" process

## Data Transformation Examples

### SAP Purchase Order Mapping

**Input (SAP Format):**
```xml
<PurchaseOrder>
    <EBELN>4500000123</EBELN>
    <BUKRS>1000</BUKRS>
    <LIFNR>VENDOR001</LIFNR>
    <MATNR>MATERIAL001</MATNR>
    <MENGE>100</MENGE>
    <NETPR>25.50</NETPR>
    <MEINS>KG</MEINS>
    <EINDT>20241231</EINDT>
    <WERKS>PLANT001</WERKS>
</PurchaseOrder>
```

**Output (Common Format):**
```json
{
    "buyer_company_id": "company-uuid-1000",
    "seller_company_id": "vendor-uuid-001",
    "product_id": "product-uuid-material001",
    "quantity": 100,
    "unit_price": 25.50,
    "unit": "kg",
    "delivery_date": "2024-12-31",
    "delivery_location": "PLANT001",
    "po_number": "4500000123"
}
```

### Amendment Request Mapping

**Input (Amendment Request):**
```json
{
    "purchase_order_id": "po-uuid-123",
    "proposed_quantity": 150,
    "proposed_quantity_unit": "kg",
    "amendment_reason": "Increased customer demand"
}
```

**Process:** Uses "Propose Changes" process with validation

**Output (Amendment Response):**
```json
{
    "success": true,
    "message": "Amendment proposed successfully",
    "amendment_status": "proposed",
    "purchase_order_id": "po-uuid-123"
}
```

## Error Handling

### Error Types and Responses

#### Authentication Errors
- **HTTP 401**: Invalid or expired credentials
- **Recovery**: Automatic token refresh
- **Notification**: Alert administrators

#### Validation Errors
- **HTTP 400**: Invalid request data
- **Recovery**: Log error, notify sender
- **Action**: Review and correct input data

#### Rate Limiting
- **HTTP 429**: Too many requests
- **Recovery**: Exponential backoff retry
- **Action**: Reduce request frequency

#### Server Errors
- **HTTP 500**: Internal server error
- **Recovery**: Retry with backoff
- **Action**: Monitor and escalate if persistent

### Error Handling Configuration

```properties
# Retry Configuration
retry.maxAttempts=3
retry.initialDelay=1000
retry.maxDelay=30000
retry.backoffMultiplier=2.0

# Notification Configuration
notification.email.enabled=true
notification.email.recipients=admin@company.com
notification.webhook.enabled=true
notification.webhook.url=https://monitoring.company.com/webhook

# Logging Configuration
logging.level=INFO
logging.auditEnabled=true
logging.performanceEnabled=true
```

## Monitoring and Alerting

### Performance Metrics
- **Request Volume**: Number of API calls per minute/hour
- **Response Time**: Average and 95th percentile response times
- **Error Rate**: Percentage of failed requests
- **Throughput**: Records processed per minute

### Health Checks
- **API Connectivity**: Regular connectivity tests to Common API
- **Authentication**: Token validity and refresh status
- **Process Status**: Monitor running processes and queues
- **Resource Usage**: CPU, memory, and disk usage

### Alerting Rules
- **High Error Rate**: Alert if error rate > 5% for 5 minutes
- **Slow Response**: Alert if avg response time > 10 seconds
- **Authentication Failure**: Immediate alert on auth failures
- **Process Failure**: Alert on critical process failures

## Best Practices

### Performance Optimization
1. **Batch Operations**: Use batch processes for bulk operations
2. **Connection Reuse**: Configure connection pooling appropriately
3. **Caching**: Cache frequently accessed data (company info, products)
4. **Parallel Processing**: Use parallel execution for independent operations

### Security
1. **Credential Management**: Use Boomi's secure credential storage
2. **Environment Separation**: Separate dev/test/prod credentials
3. **Access Control**: Implement role-based access control
4. **Audit Logging**: Enable comprehensive audit logging

### Reliability
1. **Error Handling**: Implement comprehensive error handling
2. **Retry Logic**: Configure appropriate retry mechanisms
3. **Monitoring**: Set up proactive monitoring and alerting
4. **Testing**: Thoroughly test all processes before deployment

### Maintenance
1. **Regular Updates**: Keep connector updated with latest version
2. **Performance Review**: Regularly review performance metrics
3. **Capacity Planning**: Monitor and plan for capacity needs
4. **Documentation**: Maintain up-to-date process documentation

## Support

### Documentation
- [Common API Documentation](https://docs.common.co)
- [Dell Boomi Documentation](https://help.boomi.com)
- [Connector Release Notes](https://docs.common.co/connectors/boomi/releases)

### Support Channels
- **Email**: support@common.co
- **Documentation**: https://docs.common.co/connectors/boomi
- **Status Page**: https://status.common.co
- **Emergency Support**: Available 24/7 for production issues

### Training and Resources
- **Getting Started Guide**: Step-by-step setup instructions
- **Video Tutorials**: Process configuration and troubleshooting
- **Best Practices Guide**: Enterprise deployment recommendations
- **Community Forum**: User community and knowledge sharing

## License

This connector is licensed under the Common Connector License. See LICENSE file for details.

## Deployment Package Structure

The Common Boomi Connector is delivered as a complete Process Library package:

```
common-boomi-connector-1.0.0.zip
├── connections/
│   └── Common-API-Connection.xml
├── processes/
│   ├── Create-Purchase-Order.xml
│   ├── Get-Purchase-Order.xml
│   ├── List-Purchase-Orders.xml
│   ├── Update-Purchase-Order.xml
│   ├── Propose-Changes.xml
│   ├── Approve-Changes.xml
│   ├── Batch-ERP-Sync.xml
│   └── Health-Check.xml
├── maps/
│   ├── SAP-to-Common-PO-Map.xml
│   ├── Common-to-SAP-PO-Map.xml
│   ├── Oracle-to-Common-PO-Map.xml
│   ├── Common-to-Oracle-PO-Map.xml
│   └── Generic-ERP-Map.xml
├── error-handlers/
│   ├── Standard-Error-Handler.xml
│   ├── Business-Error-Handler.xml
│   └── Notification-Handler.xml
├── utilities/
│   ├── Data-Validator.xml
│   ├── Performance-Monitor.xml
│   └── Audit-Logger.xml
├── documentation/
│   ├── Installation-Guide.pdf
│   ├── Configuration-Guide.pdf
│   ├── User-Manual.pdf
│   └── API-Reference.pdf
├── examples/
│   ├── SAP-Integration-Example.xml
│   ├── Oracle-Integration-Example.xml
│   └── Batch-Processing-Example.xml
└── README.md
```

## Quick Start Guide

### 1. Import Process Library
1. Download the connector package
2. Log into Boomi AtomSphere
3. Navigate to Build → Components
4. Click Import → Process Library Package
5. Select the downloaded ZIP file

### 2. Configure Connection
1. Go to Manage → Setup → Connections
2. Find "Common API Connection"
3. Enter your API credentials:
   - Base URL: `https://api.common.co`
   - Client ID: Your OAuth client ID
   - Client Secret: Your OAuth client secret
   - Company ID: Your company UUID

### 3. Test Connection
1. Click "Test Connection"
2. Verify successful authentication
3. Deploy connection to your Atom/Molecule

### 4. Use Processes
1. Create a new process
2. Add Common connector processes as sub-processes
3. Configure input/output mappings
4. Test and deploy

## Version History

### 1.0.0 (Current)
- Initial release
- Complete Process Library with all core operations
- SAP and Oracle integration maps
- Comprehensive error handling and monitoring
- Production-ready deployment packages

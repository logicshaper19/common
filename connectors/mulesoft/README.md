# Common Supply Chain Integration for MuleSoft

The Common Supply Chain Integration provides a complete MuleSoft application for seamless integration with the Common supply chain transparency platform. This application offers enterprise-grade functionality for purchase order management, amendment workflows, and ERP synchronization.

## Features

### Core Operations
- **Purchase Order Management**: Create, read, update, and list purchase orders
- **Amendment Workflow**: Propose and approve changes to existing purchase orders
- **ERP Synchronization**: Bi-directional sync with enterprise ERP systems
- **Company Management**: Access company and supplier information
- **Transparency Data**: Handle composition, origin, and traceability information

### Enterprise Features
- **OAuth 2.0 Authentication**: Secure API access with client credentials flow
- **Automatic Token Management**: Handles token refresh and expiration
- **Retry Logic**: Configurable retry mechanisms for transient failures
- **Connection Pooling**: Efficient HTTP connection management
- **Debug Logging**: Comprehensive logging for troubleshooting
- **Error Handling**: Detailed error messages and status codes

## Installation

### Prerequisites
- MuleSoft Anypoint Studio 7.x or later
- Mule Runtime 4.4.x or later
- Java 8 or later
- Common API credentials (Client ID and Client Secret)

### Deploy as Mule Application
1. Clone or download this repository
2. Open the project in Anypoint Studio
3. Configure your credentials in `src/main/resources/mule-app.properties`
4. Deploy to your Mule runtime environment

### Import into Existing Project
1. Copy the flows from `src/main/mule/common-connector.xml`
2. Copy the DataWeave transformations from `src/main/resources/dataweave/`
3. Update your configuration properties
4. Import the flows into your existing Mule application

## Configuration

### Basic Configuration
```xml
<common:config name="Common_Config" doc:name="Common Config">
    <common:connection 
        baseUrl="https://api.common.co"
        clientId="${common.api.clientId}"
        clientSecret="${common.api.clientSecret}"
        companyId="${common.api.companyId}"
        timeout="30"
        maxRetries="3"
        debugMode="false" />
</common:config>
```

### Configuration Properties
| Property | Required | Default | Description |
|----------|----------|---------|-------------|
| `baseUrl` | No | `https://api.common.co` | Common API base URL |
| `clientId` | Yes | - | OAuth client ID |
| `clientSecret` | Yes | - | OAuth client secret |
| `companyId` | Yes | - | Company UUID for data filtering |
| `timeout` | No | `30` | Request timeout in seconds |
| `maxRetries` | No | `3` | Maximum retry attempts |
| `debugMode` | No | `false` | Enable debug logging |

### Environment Configuration
Create a `mule-app.properties` file:
```properties
# Common API Configuration
common.api.baseUrl=https://api.common.co
common.api.clientId=your-client-id
common.api.clientSecret=your-client-secret
common.api.companyId=your-company-uuid

# Environment-specific settings
common.api.timeout=30
common.api.maxRetries=3
common.api.debugMode=false
```

## Operations

### Create Purchase Order
Creates a new purchase order in the Common platform.

```xml
<common:create-purchase-order doc:name="Create Purchase Order" 
                            config-ref="Common_Config"
                            buyerCompanyId="#[payload.buyer_company_id]"
                            sellerCompanyId="#[payload.seller_company_id]"
                            productId="#[payload.product_id]"
                            quantity="#[payload.quantity]"
                            unitPrice="#[payload.unit_price]"
                            unit="#[payload.unit]"
                            deliveryDate="#[payload.delivery_date]"
                            deliveryLocation="#[payload.delivery_location]"
                            notes="#[payload.notes]"
                            composition="#[payload.composition]"
                            inputMaterials="#[payload.input_materials]"
                            originData="#[payload.origin_data]"/>
```

### Get Purchase Order
Retrieves a purchase order by its ID.

```xml
<common:get-purchase-order doc:name="Get Purchase Order" 
                         config-ref="Common_Config"
                         purchaseOrderId="#[vars.purchaseOrderId]"/>
```

### List Purchase Orders
Retrieves a list of purchase orders with optional filtering.

```xml
<common:list-purchase-orders doc:name="List Purchase Orders" 
                           config-ref="Common_Config"
                           status="confirmed"
                           page="1"
                           perPage="50"/>
```

### Update Purchase Order
Updates an existing purchase order.

```xml
<common:update-purchase-order doc:name="Update Purchase Order" 
                            config-ref="Common_Config"
                            purchaseOrderId="#[vars.purchaseOrderId]"
                            quantity="#[payload.quantity]"
                            unitPrice="#[payload.unit_price]"
                            deliveryDate="#[payload.delivery_date]"
                            deliveryLocation="#[payload.delivery_location]"
                            notes="#[payload.notes]"/>
```

### Propose Changes
Proposes amendments to an existing purchase order.

```xml
<common:propose-changes doc:name="Propose Changes" 
                      config-ref="Common_Config"
                      purchaseOrderId="#[vars.purchaseOrderId]"
                      proposedQuantity="#[payload.proposed_quantity]"
                      proposedQuantityUnit="#[payload.proposed_quantity_unit]"
                      amendmentReason="#[payload.amendment_reason]"/>
```

### Approve Changes
Approves or rejects proposed amendments.

```xml
<common:approve-changes doc:name="Approve Changes" 
                      config-ref="Common_Config"
                      purchaseOrderId="#[vars.purchaseOrderId]"
                      approve="#[payload.approve]"
                      buyerNotes="#[payload.buyer_notes]"/>
```

## DataWeave Transformations

The connector includes pre-built DataWeave transformations for common ERP systems:

### SAP Integration
- `sap-to-common-po.dwl`: Transform SAP purchase order data to Common API format
- `common-to-sap-po.dwl`: Transform Common API data back to SAP format

### Usage Example
```xml
<ee:transform doc:name="SAP to Common Transform">
    <ee:message>
        <ee:set-payload resource="dataweave/sap-to-common-po.dwl" />
    </ee:message>
    <ee:variables>
        <ee:set-variable variableName="buyerCompanyId">${common.api.companyId}</ee:set-variable>
    </ee:variables>
</ee:transform>
```

## Error Handling

The connector provides comprehensive error handling with specific error types:

### Common Error Types
- `COMMON:AUTHENTICATION_FAILED`: Invalid credentials or expired token
- `COMMON:CONNECTION_TIMEOUT`: Request timeout exceeded
- `COMMON:NOT_FOUND`: Resource not found (404)
- `COMMON:VALIDATION_ERROR`: Invalid request data (400)
- `COMMON:SERVER_ERROR`: Internal server error (500)

### Error Handling Example
```xml
<error-handler>
    <on-error-propagate type="COMMON:AUTHENTICATION_FAILED">
        <logger level="ERROR" message="Authentication failed - check credentials"/>
    </on-error-propagate>
    <on-error-propagate type="COMMON:NOT_FOUND">
        <logger level="WARN" message="Purchase order not found: #[vars.purchaseOrderId]"/>
    </on-error-propagate>
    <on-error-propagate type="ANY">
        <logger level="ERROR" message="Unexpected error: #[error.description]"/>
    </on-error-propagate>
</error-handler>
```

## Best Practices

### Performance Optimization
1. **Connection Pooling**: Use a single connector configuration per application
2. **Batch Processing**: Process multiple records in batches when possible
3. **Caching**: Cache frequently accessed data like company information
4. **Async Processing**: Use async flows for non-critical operations

### Security
1. **Credential Management**: Store credentials in secure properties files
2. **Environment Separation**: Use different credentials per environment
3. **Token Security**: Never log or expose access tokens
4. **HTTPS Only**: Always use HTTPS endpoints in production

### Monitoring
1. **Debug Logging**: Enable debug mode for troubleshooting
2. **Metrics**: Monitor operation success rates and response times
3. **Alerting**: Set up alerts for authentication failures and timeouts
4. **Health Checks**: Implement periodic connection validation

## Examples

Complete example flows are available in the `src/main/resources/examples/` directory:

- `purchase-order-sync-flow.xml`: Complete purchase order synchronization flow
- `amendment-workflow-flow.xml`: Amendment proposal and approval workflow
- `erp-integration-flow.xml`: Bi-directional ERP synchronization

## Support

### Documentation
- [Common API Documentation](https://docs.common.co)
- [MuleSoft Connector Documentation](https://docs.mulesoft.com/connectors/)

### Contact
- Email: support@common.co
- Documentation: https://docs.common.co/connectors/mulesoft
- GitHub: https://github.com/common-co/mulesoft-connector

## License

This connector is licensed under the Common Connector License. See LICENSE file for details.

## Version History

### 1.0.0 (Current)
- Initial release
- Purchase order CRUD operations
- Amendment workflow support
- SAP integration templates
- OAuth 2.0 authentication
- Comprehensive error handling

# MuleSoft Anypoint Connector Specification

## Overview

The Common MuleSoft Anypoint Connector provides seamless integration between MuleSoft applications and the Common supply chain transparency platform. This connector enables enterprises to integrate purchase order management, amendment workflows, and ERP synchronization into their existing MuleSoft integration flows.

## Technical Requirements

### Platform Compatibility
- **Mule Runtime**: 4.3.0 or higher
- **Mule SDK**: 1.1 or higher
- **Anypoint Studio**: 7.8 or higher
- **Java Version**: 8 or 11
- **Maven**: 3.6.0 or higher

### Dependencies
```xml
<dependency>
    <groupId>org.mule.connectors</groupId>
    <artifactId>mule-http-connector</artifactId>
    <version>1.6.0</version>
</dependency>
<dependency>
    <groupId>org.mule.modules</groupId>
    <artifactId>mule-json-module</artifactId>
    <version>2.2.0</version>
</dependency>
```

## Connector Operations

### Authentication Operations

**1. Authenticate**
- **Operation**: `common:authenticate`
- **Description**: Authenticate with Common API and obtain JWT token
- **Input**: Connection configuration (client_id, client_secret, base_url)
- **Output**: JWT access token and refresh token
- **Error Handling**: Authentication failures, network timeouts

**2. Refresh Token**
- **Operation**: `common:refresh-token`
- **Description**: Refresh expired JWT token
- **Input**: Refresh token
- **Output**: New JWT access token
- **Error Handling**: Invalid refresh token, expired refresh token

### Purchase Order Operations

**1. Create Purchase Order**
- **Operation**: `common:create-purchase-order`
- **Description**: Create a new purchase order in Common
- **Input**: PurchaseOrderCreate object
- **Output**: Created PurchaseOrder with ID
- **DataWeave Transform**: Map ERP fields to Common schema

```dataweave
%dw 2.0
output application/json
---
{
    buyer_company_id: payload.buyerCompanyId,
    seller_company_id: payload.sellerCompanyId,
    product_id: payload.productId,
    quantity: payload.orderQuantity as Number,
    unit_price: payload.unitPrice as Number,
    unit: payload.unitOfMeasure,
    delivery_date: payload.requestedDeliveryDate as Date,
    delivery_location: payload.deliveryAddress,
    notes: payload.orderNotes
}
```

**2. Get Purchase Order**
- **Operation**: `common:get-purchase-order`
- **Description**: Retrieve purchase order by ID
- **Input**: Purchase order ID (UUID)
- **Output**: Complete PurchaseOrder object
- **Error Handling**: Not found, access denied

**3. List Purchase Orders**
- **Operation**: `common:list-purchase-orders`
- **Description**: List purchase orders with filtering
- **Input**: Filter parameters (status, date range, company)
- **Output**: Paginated list of PurchaseOrder objects
- **Pagination**: Automatic handling of page-based results

**4. Update Purchase Order**
- **Operation**: `common:update-purchase-order`
- **Description**: Update existing purchase order
- **Input**: Purchase order ID and update data
- **Output**: Updated PurchaseOrder object
- **Error Handling**: Validation errors, concurrent updates

### Amendment Operations

**1. Propose Changes**
- **Operation**: `common:propose-changes`
- **Description**: Propose amendments to purchase order
- **Input**: PO ID and ProposeChangesRequest
- **Output**: AmendmentResponse with status
- **Business Logic**: Only sellers can propose changes

```dataweave
%dw 2.0
output application/json
---
{
    proposed_quantity: payload.newQuantity as Number,
    proposed_quantity_unit: payload.newUnit,
    amendment_reason: payload.changeReason
}
```

**2. Approve Changes**
- **Operation**: `common:approve-changes`
- **Description**: Approve or reject proposed amendments
- **Input**: PO ID and ApproveChangesRequest
- **Output**: AmendmentResponse with final status
- **Business Logic**: Only buyers can approve changes

### ERP Sync Operations (Phase 2)

**1. Get Sync Status**
- **Operation**: `common:get-sync-status`
- **Description**: Get ERP synchronization status
- **Input**: Company ID (optional)
- **Output**: ERPSyncStatus object
- **Use Case**: Monitor sync health and statistics

**2. Get Pending Updates**
- **Operation**: `common:get-pending-updates`
- **Description**: Poll for pending ERP updates
- **Input**: Since timestamp, limit
- **Output**: List of pending updates
- **Use Case**: Polling-based ERP integration

**3. Acknowledge Updates**
- **Operation**: `common:acknowledge-updates`
- **Description**: Mark updates as processed
- **Input**: List of update IDs and sync timestamp
- **Output**: Acknowledgment confirmation
- **Use Case**: Complete polling sync cycle

**4. Test Webhook**
- **Operation**: `common:test-webhook`
- **Description**: Test webhook connectivity
- **Input**: Webhook URL and authentication
- **Output**: Test result and response details
- **Use Case**: Validate ERP webhook configuration

## Configuration

### Connection Configuration

```xml
<common:config name="Common_Config">
    <common:connection 
        baseUrl="https://api.common.co"
        clientId="${common.client.id}"
        clientSecret="${common.client.secret}"
        companyId="${common.company.id}"
        timeout="30"
        maxRetries="3" />
</common:config>
```

**Configuration Parameters:**
- `baseUrl`: Common API base URL
- `clientId`: OAuth client ID
- `clientSecret`: OAuth client secret  
- `companyId`: Company UUID for data filtering
- `timeout`: Request timeout in seconds (default: 30)
- `maxRetries`: Maximum retry attempts (default: 3)

### Security Configuration

**TLS Configuration:**
```xml
<tls:context name="Common_TLS_Context">
    <tls:trust-store 
        path="common-truststore.jks" 
        password="${tls.truststore.password}" />
</tls:context>
```

**OAuth Configuration:**
```xml
<oauth:config name="Common_OAuth_Config">
    <oauth:client-credentials-grant-type 
        clientId="${oauth.client.id}"
        clientSecret="${oauth.client.secret}"
        tokenUrl="https://api.common.co/api/v1/auth/token" />
</oauth:config>
```

## DataWeave Transformations

### ERP to Common Mapping

**SAP Purchase Order Mapping:**
```dataweave
%dw 2.0
output application/json
---
{
    buyer_company_id: vars.buyerCompanyId,
    seller_company_id: payload.LIFNR,  // SAP Vendor Number
    product_id: payload.MATNR,         // SAP Material Number
    quantity: payload.MENGE as Number,  // SAP Quantity
    unit_price: payload.NETPR as Number, // SAP Net Price
    unit: payload.MEINS,               // SAP Unit of Measure
    delivery_date: payload.EINDT as Date, // SAP Delivery Date
    delivery_location: payload.WERKS,  // SAP Plant
    notes: payload.TXZOL               // SAP Short Text
}
```

**Oracle ERP Mapping:**
```dataweave
%dw 2.0
output application/json
---
{
    buyer_company_id: vars.buyerCompanyId,
    seller_company_id: payload.vendor_id,
    product_id: payload.item_id,
    quantity: payload.quantity as Number,
    unit_price: payload.unit_price as Number,
    unit: payload.unit_meas_lookup_code,
    delivery_date: payload.need_by_date as Date,
    delivery_location: payload.deliver_to_location_id,
    notes: payload.note_to_vendor
}
```

### Common to ERP Mapping

**Common to SAP IDoc:**
```dataweave
%dw 2.0
output application/xml
---
{
    ORDERS05: {
        IDOC: {
            EDI_DC40: {
                TABNAM: "EDI_DC40",
                MANDT: vars.sapClient,
                DOCNUM: payload.po_number,
                DOCTYP: "ORDERS05"
            },
            E1EDK01: {
                BELNR: payload.po_number,
                CURCY: "USD",
                WKURS: "1.00000"
            },
            E1EDP01: {
                POSEX: "00010",
                MENGE: payload.quantity,
                MENEE: payload.unit,
                NETPR: payload.unit_price,
                PEINH: "1",
                WERKS: payload.delivery_location
            }
        }
    }
}
```

## Error Handling

### Standard Error Types

**1. Authentication Errors**
```xml
<error-handler>
    <on-error-continue type="COMMON:AUTHENTICATION_ERROR">
        <logger message="Authentication failed: #[error.description]" level="ERROR"/>
        <common:refresh-token config-ref="Common_Config"/>
        <flow-ref name="retry-operation"/>
    </on-error-continue>
</error-handler>
```

**2. Validation Errors**
```xml
<error-handler>
    <on-error-propagate type="COMMON:VALIDATION_ERROR">
        <logger message="Validation failed: #[error.description]" level="ERROR"/>
        <set-payload value='#[{
            "error": "Validation failed",
            "details": error.description,
            "timestamp": now()
        }]'/>
    </on-error-propagate>
</error-handler>
```

**3. Rate Limiting**
```xml
<error-handler>
    <on-error-continue type="COMMON:RATE_LIMIT_ERROR">
        <logger message="Rate limit exceeded, retrying after delay" level="WARN"/>
        <until-successful maxRetries="3" millisBetweenRetries="5000">
            <flow-ref name="original-operation"/>
        </until-successful>
    </on-error-continue>
</error-handler>
```

## Example Flows

### Basic Purchase Order Creation Flow

```xml
<flow name="create-purchase-order-flow">
    <http:listener config-ref="HTTP_Listener_config" path="/create-po"/>
    
    <!-- Transform ERP data to Common format -->
    <ee:transform>
        <ee:message>
            <ee:set-payload><![CDATA[%dw 2.0
output application/json
---
{
    buyer_company_id: vars.buyerCompanyId,
    seller_company_id: payload.vendorId,
    product_id: payload.productId,
    quantity: payload.orderQuantity as Number,
    unit_price: payload.unitPrice as Number,
    unit: payload.unitOfMeasure,
    delivery_date: payload.deliveryDate as Date,
    delivery_location: payload.deliveryLocation,
    notes: payload.orderNotes
}]]></ee:set-payload>
        </ee:message>
    </ee:transform>
    
    <!-- Create purchase order in Common -->
    <common:create-purchase-order config-ref="Common_Config"/>
    
    <!-- Transform response back to ERP format -->
    <ee:transform>
        <ee:message>
            <ee:set-payload><![CDATA[%dw 2.0
output application/json
---
{
    commonPoId: payload.id,
    poNumber: payload.po_number,
    status: payload.status,
    createdAt: payload.created_at
}]]></ee:set-payload>
        </ee:message>
    </ee:transform>
    
    <logger message="Purchase order created: #[payload.commonPoId]" level="INFO"/>
</flow>
```

### Amendment Workflow Flow

```xml
<flow name="amendment-workflow-flow">
    <http:listener config-ref="HTTP_Listener_config" path="/propose-amendment"/>
    
    <!-- Validate amendment request -->
    <validation:is-not-null value="#[payload.poId]" message="PO ID is required"/>
    <validation:is-not-null value="#[payload.proposedQuantity]" message="Proposed quantity is required"/>
    
    <!-- Transform to Common amendment format -->
    <ee:transform>
        <ee:message>
            <ee:set-payload><![CDATA[%dw 2.0
output application/json
---
{
    proposed_quantity: payload.proposedQuantity as Number,
    proposed_quantity_unit: payload.proposedUnit,
    amendment_reason: payload.changeReason
}]]></ee:set-payload>
        </ee:message>
    </ee:transform>
    
    <!-- Propose changes in Common -->
    <common:propose-changes config-ref="Common_Config" poId="#[vars.poId]"/>
    
    <!-- Handle response -->
    <choice>
        <when expression="#[payload.success == true]">
            <logger message="Amendment proposed successfully: #[payload.amendment_status]" level="INFO"/>
        </when>
        <otherwise>
            <logger message="Amendment proposal failed: #[payload.message]" level="ERROR"/>
            <raise-error type="COMMON:AMENDMENT_ERROR" description="#[payload.message]"/>
        </otherwise>
    </choice>
</flow>
```

## Testing

### Unit Tests
- Connection configuration validation
- Data transformation accuracy
- Error handling scenarios
- Authentication flow testing

### Integration Tests
- End-to-end purchase order workflows
- Amendment approval processes
- ERP sync operations
- Performance under load

### Deployment Package

**Connector JAR Structure:**
```
common-mulesoft-connector-1.0.0.jar
├── META-INF/
│   ├── mule-artifact/
│   │   └── mule-artifact.json
│   └── MANIFEST.MF
├── org/mulesoft/connectors/common/
│   ├── api/
│   ├── internal/
│   └── CommonConnector.class
└── schemas/
    ├── purchase-order-schema.json
    └── amendment-schema.json
```

## Installation Guide

### Prerequisites
1. Anypoint Studio 7.8 or higher
2. Mule Runtime 4.3.0 or higher
3. Common API credentials (client_id, client_secret)
4. Company ID from Common platform

### Installation Steps
1. Download connector JAR from Anypoint Exchange
2. Install in Anypoint Studio via "Install Connectors" menu
3. Add connector to project dependencies
4. Configure connection parameters
5. Test connection using "Test Connection" button

### Configuration Example
```xml
<common:config name="Common_Config">
    <common:connection
        baseUrl="https://api.common.co"
        clientId="${secure::common.client.id}"
        clientSecret="${secure::common.client.secret}"
        companyId="${common.company.id}" />
</common:config>
```

This specification provides the complete technical foundation for building a production-ready MuleSoft connector for the Common platform.

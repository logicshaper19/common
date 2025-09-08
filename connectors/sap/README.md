# Common SAP Integration Templates

The Common SAP Integration Templates provide comprehensive integration patterns between SAP ERP systems and the Common supply chain transparency platform. These templates support multiple SAP integration methods including RFC/BAPI, IDoc, and REST services for seamless purchase order and amendment synchronization.

## Features

### Integration Patterns
- **RFC/BAPI Integration**: Direct function module calls with real-time processing
- **IDoc Integration**: Asynchronous message-based integration with guaranteed delivery
- **REST/OData Services**: Modern web service integration through SAP Gateway
- **Batch Processing**: High-volume data synchronization capabilities

### SAP System Support
- **SAP ECC**: 6.0 EHP7 or higher
- **SAP S/4HANA**: 1809 or higher (On-Premise and Cloud)
- **SAP NetWeaver**: 7.4 or higher
- **SAP PI/PO**: 7.5 or higher (for middleware integration)
- **SAP Cloud Platform Integration**: 2.0 or higher

### Enterprise Features
- **OAuth 2.0 Authentication**: Secure API access with automatic token management
- **Error Handling**: Comprehensive error handling with retry logic
- **Audit Logging**: Complete audit trail for compliance requirements
- **Performance Monitoring**: Real-time monitoring and alerting
- **Field Mapping**: Configurable field mappings between SAP and Common

## Installation

### Prerequisites
- SAP system with appropriate authorization
- ABAP development access (for RFC/BAPI and IDoc)
- SAP Gateway access (for REST services)
- Network connectivity to api.common.co (HTTPS/443)
- Common API credentials (Client ID and Client Secret)

### Installation Steps

1. **Download Integration Package**
   ```bash
   # Download from Common's connector repository
   wget https://releases.common.co/connectors/sap/common-sap-integration-1.0.0.zip
   ```

2. **Import Transport**
   - Extract the transport files (COFILES and DATA)
   - Import transport using STMS or tp command
   - Activate all imported objects

3. **Configure RFC Destinations**
   - Transaction: SM59
   - Create HTTP destination to Common API
   - Configure SSL certificates and authentication

4. **Set Up Configuration Tables**
   - Maintain field mappings in ZCOMMON_MAPPING
   - Configure API parameters in ZCOMMON_CONFIG
   - Set up company and product mappings

5. **Test Integration**
   - Run test programs to validate connectivity
   - Test purchase order creation and amendment flows
   - Verify error handling and logging

## Configuration

### RFC Destination Setup

Create HTTP destination for Common API:

| Parameter | Value | Description |
|-----------|-------|-------------|
| **Destination** | COMMON_API_PROD | RFC destination name |
| **Connection Type** | G | HTTP to External Server |
| **Target Host** | api.common.co | Common API hostname |
| **Service No** | 443 | HTTPS port |
| **Path Prefix** | /api/v1 | API base path |

### SSL Configuration

1. **Import SSL Certificate**
   - Download Common API SSL certificate
   - Import using STRUST transaction
   - Add to SSL client standard list

2. **Configure Authentication**
   - Set up OAuth 2.0 client credentials
   - Store credentials securely in SM59
   - Configure automatic token refresh

### Field Mapping Configuration

Configure field mappings in table ZCOMMON_MAPPING:

```abap
" Example mapping entries
INSERT zcommon_mapping FROM TABLE VALUE #(
  ( source_system = 'SAP' target_system = 'COMMON' 
    source_field = 'BUKRS' target_field = 'buyer_company_id' 
    mapping_type = 'LOOKUP' lookup_table = 'ZCOMMON_COMPANY' )
  ( source_system = 'SAP' target_system = 'COMMON' 
    source_field = 'LIFNR' target_field = 'seller_company_id' 
    mapping_type = 'LOOKUP' lookup_table = 'ZCOMMON_VENDOR' )
  ( source_system = 'SAP' target_system = 'COMMON' 
    source_field = 'MATNR' target_field = 'product_id' 
    mapping_type = 'LOOKUP' lookup_table = 'ZCOMMON_MATERIAL' )
).
```

## Usage Examples

### Example 1: Create Purchase Order via RFC

```abap
DATA: lv_common_po_id TYPE string,
      lv_sap_po_number TYPE ebeln,
      lv_success TYPE abap_bool,
      lv_message TYPE string.

CALL FUNCTION 'Z_COMMON_CREATE_PO'
  EXPORTING
    iv_buyer_company     = 'company-uuid-1000'
    iv_seller_company    = 'vendor-uuid-001'
    iv_product_id        = 'product-uuid-material001'
    iv_quantity          = '100.000'
    iv_unit_price        = '25.50'
    iv_unit              = 'KG'
    iv_delivery_date     = '20241231'
    iv_delivery_location = 'PLANT001'
    iv_notes             = 'Urgent delivery required'
  IMPORTING
    ev_common_po_id      = lv_common_po_id
    ev_sap_po_number     = lv_sap_po_number
    ev_success           = lv_success
    ev_message           = lv_message
  EXCEPTIONS
    validation_error     = 1
    creation_failed      = 2
    communication_error  = 3
    OTHERS               = 4.

IF sy-subrc = 0 AND lv_success = abap_true.
  WRITE: / 'Purchase order created successfully:',
         / 'Common PO ID:', lv_common_po_id,
         / 'SAP PO Number:', lv_sap_po_number.
ELSE.
  WRITE: / 'Error creating purchase order:', lv_message.
ENDIF.
```

### Example 2: Propose Amendment via RFC

```abap
DATA: lv_amendment_status TYPE string,
      lv_success TYPE abap_bool,
      lv_message TYPE string.

CALL FUNCTION 'Z_COMMON_PROPOSE_AMENDMENT'
  EXPORTING
    iv_common_po_id      = 'po-uuid-123'
    iv_proposed_quantity = '150.000'
    iv_proposed_unit     = 'KG'
    iv_amendment_reason  = 'Increased customer demand'
  IMPORTING
    ev_amendment_status  = lv_amendment_status
    ev_success           = lv_success
    ev_message           = lv_message.

IF lv_success = abap_true.
  WRITE: / 'Amendment proposed successfully:',
         / 'Status:', lv_amendment_status.
ELSE.
  WRITE: / 'Error proposing amendment:', lv_message.
ENDIF.
```

### Example 3: Process IDoc for Purchase Order

```abap
" IDoc processing in partner profile
" Message type: ZCOMMON_ORDERS
" Process code: ZCOM_PO_PROCESS

DATA: idoc_control TYPE edidc,
      idoc_data TYPE TABLE OF edidd,
      lv_success TYPE abap_bool,
      lv_message TYPE string.

" Build IDoc data
idoc_control-mestyp = 'ZCOMMON_ORDERS'.
idoc_control-idoctp = 'ZCOMMON_ORDERS01'.

" Add header segment
APPEND VALUE #( segnam = 'E1ZCOMMON_HEADER'
                sdata = 'company-uuid-1000vendor-uuid-001...' ) TO idoc_data.

" Add item segment  
APPEND VALUE #( segnam = 'E1ZCOMMON_ITEM'
                sdata = '001product-uuid-001100KG25.50...' ) TO idoc_data.

" Process IDoc
CALL FUNCTION 'Z_COMMON_PROCESS_PO_IDOC'
  EXPORTING
    idoc_control = idoc_control
    idoc_data    = idoc_data
  IMPORTING
    ev_success   = lv_success
    ev_message   = lv_message.
```

### Example 4: OData Service Call

```javascript
// JavaScript example for SAP Gateway OData service
var oModel = new sap.ui.model.odata.v2.ODataModel("/sap/opu/odata/sap/ZCOMMON_PO_SRV/");

// Create purchase order
var oData = {
    BuyerCompanyId: "company-uuid-1000",
    SellerCompanyId: "vendor-uuid-001", 
    ProductId: "product-uuid-material001",
    Quantity: "100.000",
    UnitPrice: "25.50",
    Unit: "KG",
    DeliveryDate: new Date("2024-12-31"),
    DeliveryLocation: "PLANT001"
};

oModel.create("/PurchaseOrderSet", oData, {
    success: function(data) {
        console.log("Purchase order created:", data.CommonPoId);
    },
    error: function(error) {
        console.error("Error creating purchase order:", error);
    }
});

// Propose amendment
var oAmendmentData = {
    CommonPoId: "po-uuid-123",
    ProposedQuantity: "150.000",
    ProposedUnit: "KG",
    AmendmentReason: "Increased customer demand"
};

oModel.create("/AmendmentSet", oAmendmentData, {
    success: function(data) {
        console.log("Amendment proposed:", data.AmendmentStatus);
    },
    error: function(error) {
        console.error("Error proposing amendment:", error);
    }
});
```

## Data Transformation

### SAP to Common Field Mappings

| SAP Field | Common Field | Transformation | Required |
|-----------|--------------|----------------|----------|
| BUKRS | buyer_company_id | Lookup table | Yes |
| LIFNR | seller_company_id | Lookup table | Yes |
| MATNR | product_id | Lookup table | Yes |
| MENGE | quantity | Direct mapping | Yes |
| NETPR | unit_price | Price calculation | Yes |
| MEINS | unit | Unit conversion | Yes |
| EINDT | delivery_date | Date format conversion | Yes |
| WERKS | delivery_location | Location mapping | Yes |
| EBELN | po_number | Direct mapping | No |
| TXZOL | notes | Direct mapping | No |

### Lookup Tables

#### Company Mapping (ZCOMMON_COMPANY)
```abap
" Map SAP company codes to Common UUIDs
BUKRS: '1000' → 'company-uuid-1000'
BUKRS: '2000' → 'company-uuid-2000'
BUKRS: '3000' → 'company-uuid-3000'
```

#### Vendor Mapping (ZCOMMON_VENDOR)
```abap
" Map SAP vendor numbers to Common UUIDs
LIFNR: 'VENDOR001' → 'vendor-uuid-001'
LIFNR: 'VENDOR002' → 'vendor-uuid-002'
LIFNR: 'VENDOR003' → 'vendor-uuid-003'
```

#### Material Mapping (ZCOMMON_MATERIAL)
```abap
" Map SAP material numbers to Common UUIDs
MATNR: 'MATERIAL001' → 'product-uuid-001'
MATNR: 'MATERIAL002' → 'product-uuid-002'
MATNR: 'MATERIAL003' → 'product-uuid-003'
```

#### Unit of Measure Mapping (ZCOMMON_UOM)
```abap
" Map SAP units to Common standard units
MEINS: 'KG' → 'kg'
MEINS: 'G' → 'g'
MEINS: 'LB' → 'lb'
MEINS: 'PC' → 'piece'
MEINS: 'EA' → 'each'
```

## Error Handling

### Error Types and Responses

#### Authentication Errors
- **ABAP Exception**: COMMUNICATION_ERROR
- **HTTP Status**: 401 Unauthorized
- **Recovery**: Automatic token refresh
- **Notification**: Alert administrators

#### Validation Errors
- **ABAP Exception**: VALIDATION_ERROR
- **HTTP Status**: 400 Bad Request
- **Recovery**: Log error, notify sender
- **Action**: Review and correct input data

#### Business Logic Errors
- **ABAP Exception**: CREATION_FAILED
- **HTTP Status**: 422 Unprocessable Entity
- **Recovery**: Business rule validation
- **Action**: Review business logic and data

#### System Errors
- **ABAP Exception**: COMMUNICATION_ERROR
- **HTTP Status**: 500 Internal Server Error
- **Recovery**: Retry with exponential backoff
- **Action**: Monitor and escalate if persistent

### Error Logging

All errors are logged to table ZCOMMON_LOG:

```abap
" Log error entry
INSERT zcommon_log FROM VALUE #(
  log_id = cl_system_uuid=>create_uuid_x16_static( )
  timestamp = sy-datum && sy-uzeit
  integration_type = 'RFC'
  operation = 'CREATE_PO'
  status = 'ERROR'
  error_code = 'VALIDATION_ERROR'
  error_message = 'Invalid company ID'
  request_data = lv_request_json
  response_data = lv_response_json
  created_by = sy-uname
).
```

## Monitoring and Maintenance

### Performance Monitoring

Monitor integration performance using program ZCOMMON_MONITOR:

```abap
" Display integration statistics
SELECT COUNT(*) FROM zcommon_log 
  WHERE created_date = sy-datum
  AND status = 'SUCCESS'
  INTO @DATA(lv_success_count).

SELECT COUNT(*) FROM zcommon_log 
  WHERE created_date = sy-datum
  AND status = 'ERROR'
  INTO @DATA(lv_error_count).

DATA(lv_success_rate) = lv_success_count / ( lv_success_count + lv_error_count ) * 100.

WRITE: / 'Today''s Integration Statistics:',
       / 'Successful:', lv_success_count,
       / 'Failed:', lv_error_count,
       / 'Success Rate:', lv_success_rate, '%'.
```

### Health Checks

Regular health checks using function Z_COMMON_HEALTH_CHECK:

```abap
CALL FUNCTION 'Z_COMMON_HEALTH_CHECK'
  IMPORTING
    ev_api_status = lv_api_status
    ev_auth_status = lv_auth_status
    ev_connectivity = lv_connectivity
    ev_overall_health = lv_health.

IF lv_health = 'HEALTHY'.
  WRITE: / 'System is healthy'.
ELSE.
  WRITE: / 'System issues detected:',
         / 'API Status:', lv_api_status,
         / 'Auth Status:', lv_auth_status,
         / 'Connectivity:', lv_connectivity.
ENDIF.
```

### Maintenance Procedures

#### Weekly Maintenance
- Review error logs and resolve issues
- Check performance metrics and optimize
- Validate lookup table data accuracy
- Test connectivity and authentication

#### Monthly Maintenance
- Update field mappings as needed
- Review and update configuration parameters
- Analyze performance trends
- Update documentation

#### Quarterly Maintenance
- Security review and credential rotation
- Performance optimization and tuning
- Capacity planning and scaling
- Integration testing with latest SAP patches

## Support

### Documentation
- [Common API Documentation](https://docs.common.co)
- [SAP Integration Guide](https://docs.common.co/connectors/sap)
- [ABAP Development Guide](https://docs.common.co/connectors/sap/abap)

### Support Channels
- **Email**: support@common.co
- **Documentation**: https://docs.common.co/connectors/sap
- **Community Forum**: https://community.common.co
- **Emergency Support**: Available 24/7 for production issues

### Training Resources
- **SAP Integration Workshop**: Hands-on training for developers
- **Configuration Guide**: Step-by-step setup instructions
- **Best Practices**: Enterprise deployment recommendations
- **Troubleshooting Guide**: Common issues and solutions

## License

This integration template is licensed under the Common Connector License. See LICENSE file for details.

## Version History

### 1.0.0 (Current)
- Initial release
- RFC/BAPI integration templates
- IDoc message types and processing
- OData service definitions
- Comprehensive field mappings
- Error handling and logging
- Performance monitoring
- Production-ready deployment packages

# SAP Integration Templates Specification

## Overview

The Common SAP Integration Templates provide comprehensive integration patterns between SAP ERP systems and the Common supply chain transparency platform. These templates support multiple SAP integration methods including RFC/BAPI, IDoc, and REST services for seamless purchase order and amendment synchronization.

## Technical Requirements

### SAP System Compatibility
- **SAP ECC**: 6.0 EHP7 or higher
- **SAP S/4HANA**: 1809 or higher
- **SAP NetWeaver**: 7.4 or higher
- **SAP PI/PO**: 7.5 or higher (for middleware integration)
- **SAP Cloud Platform Integration**: 2.0 or higher

### Required SAP Components
- RFC-enabled function modules
- IDoc message types and segments
- ABAP development tools
- SAP Gateway (for REST services)
- SAP Process Integration (optional)

## Integration Patterns

### 1. RFC/BAPI Integration

**A. Purchase Order Creation BAPI**

**Function Module**: `Z_COMMON_CREATE_PO`
```abap
FUNCTION Z_COMMON_CREATE_PO.
*"----------------------------------------------------------------------
*"*"Local Interface:
*"  IMPORTING
*"     VALUE(IV_BUYER_COMPANY) TYPE STRING
*"     VALUE(IV_SELLER_COMPANY) TYPE STRING
*"     VALUE(IV_PRODUCT_ID) TYPE STRING
*"     VALUE(IV_QUANTITY) TYPE P DECIMALS 3
*"     VALUE(IV_UNIT_PRICE) TYPE P DECIMALS 2
*"     VALUE(IV_UNIT) TYPE MEINS
*"     VALUE(IV_DELIVERY_DATE) TYPE DATS
*"     VALUE(IV_DELIVERY_LOCATION) TYPE STRING
*"     VALUE(IV_NOTES) TYPE STRING OPTIONAL
*"  EXPORTING
*"     VALUE(EV_COMMON_PO_ID) TYPE STRING
*"     VALUE(EV_SAP_PO_NUMBER) TYPE EBELN
*"     VALUE(EV_SUCCESS) TYPE ABAP_BOOL
*"     VALUE(EV_MESSAGE) TYPE STRING
*"  EXCEPTIONS
*"     VALIDATION_ERROR
*"     CREATION_FAILED
*"     COMMUNICATION_ERROR
*"----------------------------------------------------------------------

  DATA: lv_po_data TYPE string,
        lv_response TYPE string,
        lv_http_client TYPE REF TO if_http_client.

  " Build JSON payload for Common API
  CONCATENATE '{'
    '"buyer_company_id":"' iv_buyer_company '",'
    '"seller_company_id":"' iv_seller_company '",'
    '"product_id":"' iv_product_id '",'
    '"quantity":' iv_quantity ','
    '"unit_price":' iv_unit_price ','
    '"unit":"' iv_unit '",'
    '"delivery_date":"' iv_delivery_date '",'
    '"delivery_location":"' iv_delivery_location '",'
    '"notes":"' iv_notes '"'
    '}' INTO lv_po_data.

  " Call Common API
  PERFORM call_common_api USING 'POST'
                                '/api/v1/purchase-orders'
                                lv_po_data
                         CHANGING lv_response
                                  ev_success
                                  ev_message.

  IF ev_success = abap_true.
    " Parse response and extract Common PO ID
    PERFORM parse_po_response USING lv_response
                             CHANGING ev_common_po_id
                                      ev_sap_po_number.
  ENDIF.

ENDFUNCTION.
```

**B. Amendment Proposal BAPI**

**Function Module**: `Z_COMMON_PROPOSE_AMENDMENT`
```abap
FUNCTION Z_COMMON_PROPOSE_AMENDMENT.
*"----------------------------------------------------------------------
*"*"Local Interface:
*"  IMPORTING
*"     VALUE(IV_COMMON_PO_ID) TYPE STRING
*"     VALUE(IV_PROPOSED_QUANTITY) TYPE P DECIMALS 3
*"     VALUE(IV_PROPOSED_UNIT) TYPE MEINS
*"     VALUE(IV_AMENDMENT_REASON) TYPE STRING
*"  EXPORTING
*"     VALUE(EV_AMENDMENT_STATUS) TYPE STRING
*"     VALUE(EV_SUCCESS) TYPE ABAP_BOOL
*"     VALUE(EV_MESSAGE) TYPE STRING
*"----------------------------------------------------------------------

  DATA: lv_amendment_data TYPE string,
        lv_response TYPE string,
        lv_url TYPE string.

  " Build amendment JSON payload
  CONCATENATE '{'
    '"proposed_quantity":' iv_proposed_quantity ','
    '"proposed_quantity_unit":"' iv_proposed_unit '",'
    '"amendment_reason":"' iv_amendment_reason '"'
    '}' INTO lv_amendment_data.

  " Build URL with PO ID
  CONCATENATE '/api/v1/purchase-orders/' iv_common_po_id '/propose-changes'
    INTO lv_url.

  " Call Common API
  PERFORM call_common_api USING 'PUT'
                                lv_url
                                lv_amendment_data
                         CHANGING lv_response
                                  ev_success
                                  ev_message.

  IF ev_success = abap_true.
    " Parse amendment response
    PERFORM parse_amendment_response USING lv_response
                                   CHANGING ev_amendment_status.
  ENDIF.

ENDFUNCTION.
```

**C. Common API HTTP Client**

**Subroutine**: `CALL_COMMON_API`
```abap
FORM call_common_api USING p_method TYPE string
                           p_url TYPE string
                           p_data TYPE string
                  CHANGING p_response TYPE string
                           p_success TYPE abap_bool
                           p_message TYPE string.

  DATA: lv_full_url TYPE string,
        lv_token TYPE string,
        lo_http_client TYPE REF TO if_http_client.

  " Get authentication token
  PERFORM get_auth_token CHANGING lv_token p_success p_message.
  IF p_success = abap_false.
    RETURN.
  ENDIF.

  " Build full URL
  CONCATENATE 'https://api.common.co' p_url INTO lv_full_url.

  " Create HTTP client
  CALL METHOD cl_http_client=>create_by_url
    EXPORTING
      url    = lv_full_url
    IMPORTING
      client = lo_http_client.

  " Set headers
  lo_http_client->request->set_header_field(
    name  = 'Authorization'
    value = |Bearer { lv_token }| ).
  lo_http_client->request->set_header_field(
    name  = 'Content-Type'
    value = 'application/json' ).

  " Set method and data
  lo_http_client->request->set_method( p_method ).
  IF p_data IS NOT INITIAL.
    lo_http_client->request->set_cdata( p_data ).
  ENDIF.

  " Send request
  lo_http_client->send( ).
  lo_http_client->receive( ).

  " Get response
  p_response = lo_http_client->response->get_cdata( ).
  
  " Check status
  DATA: lv_status TYPE i.
  lv_status = lo_http_client->response->get_status( )-code.
  
  IF lv_status BETWEEN 200 AND 299.
    p_success = abap_true.
  ELSE.
    p_success = abap_false.
    p_message = |HTTP Error { lv_status }: { p_response }|.
  ENDIF.

  " Close connection
  lo_http_client->close( ).

ENDFORM.
```

### 2. IDoc Integration

**A. Purchase Order IDoc Message Type**

**Message Type**: `ZCOMMON_ORDERS`
**Basic Type**: `ZCOMMON_ORDERS01`

**Segment Structure**:
```
E1ZCOMMON_HEADER (Header Segment)
├── COMMON_PO_ID     (Common Platform PO ID)
├── SAP_PO_NUMBER    (SAP Purchase Order Number)
├── BUYER_COMPANY    (Buyer Company ID)
├── SELLER_COMPANY   (Seller Company ID)
├── PO_STATUS        (Purchase Order Status)
└── CREATED_DATE     (Creation Date)

E1ZCOMMON_ITEM (Item Segment)
├── ITEM_NUMBER      (Line Item Number)
├── PRODUCT_ID       (Common Product ID)
├── SAP_MATERIAL     (SAP Material Number)
├── QUANTITY         (Order Quantity)
├── UNIT             (Unit of Measure)
├── UNIT_PRICE       (Unit Price)
├── TOTAL_AMOUNT     (Total Line Amount)
├── DELIVERY_DATE    (Requested Delivery Date)
└── DELIVERY_LOCATION (Delivery Location)

E1ZCOMMON_AMENDMENT (Amendment Segment)
├── AMENDMENT_ID     (Amendment ID)
├── AMENDMENT_TYPE   (Type of Amendment)
├── PROPOSED_QTY     (Proposed Quantity)
├── PROPOSED_UNIT    (Proposed Unit)
├── AMENDMENT_REASON (Reason for Amendment)
├── AMENDMENT_STATUS (Current Status)
└── AMENDMENT_DATE   (Amendment Date)
```

**B. IDoc Processing Program**

**Program**: `ZCOMMON_IDOC_PROCESS`
```abap
PROGRAM zcommon_idoc_process.

TABLES: edidd, edidc.

DATA: BEGIN OF wa_header,
        common_po_id TYPE string,
        sap_po_number TYPE ebeln,
        buyer_company TYPE string,
        seller_company TYPE string,
        po_status TYPE string,
        created_date TYPE dats,
      END OF wa_header.

DATA: BEGIN OF wa_item,
        item_number TYPE ebelp,
        product_id TYPE string,
        sap_material TYPE matnr,
        quantity TYPE menge_d,
        unit TYPE meins,
        unit_price TYPE bprei,
        total_amount TYPE bwert,
        delivery_date TYPE eindt,
        delivery_location TYPE string,
      END OF wa_item.

" Process IDoc segments
LOOP AT idoc_data INTO edidd WHERE segnam = 'E1ZCOMMON_HEADER'.
  wa_header = edidd-sdata.
  " Process header data
  PERFORM process_header USING wa_header.
ENDLOOP.

LOOP AT idoc_data INTO edidd WHERE segnam = 'E1ZCOMMON_ITEM'.
  wa_item = edidd-sdata.
  " Process item data
  PERFORM process_item USING wa_item.
ENDLOOP.

" Send to Common API
PERFORM send_to_common_api.
```

**C. Amendment IDoc Processing**

**Function Module**: `Z_COMMON_PROCESS_AMENDMENT_IDOC`
```abap
FUNCTION Z_COMMON_PROCESS_AMENDMENT_IDOC.
*"----------------------------------------------------------------------
*"*"Local Interface:
*"  IMPORTING
*"     VALUE(IDOC_CONTROL) TYPE edidc
*"     VALUE(IDOC_DATA) TYPE edidd_tt
*"  EXPORTING
*"     VALUE(EV_SUCCESS) TYPE ABAP_BOOL
*"     VALUE(EV_MESSAGE) TYPE STRING
*"----------------------------------------------------------------------

  DATA: wa_amendment TYPE zcommon_amendment_seg,
        lv_response TYPE string.

  " Extract amendment data from IDoc
  LOOP AT idoc_data INTO DATA(wa_edidd) WHERE segnam = 'E1ZCOMMON_AMENDMENT'.
    wa_amendment = wa_edidd-sdata.
    
    " Process amendment based on type
    CASE wa_amendment-amendment_type.
      WHEN 'PROPOSE'.
        PERFORM propose_amendment USING wa_amendment
                                CHANGING ev_success ev_message.
      WHEN 'APPROVE'.
        PERFORM approve_amendment USING wa_amendment
                                CHANGING ev_success ev_message.
      WHEN 'REJECT'.
        PERFORM reject_amendment USING wa_amendment
                               CHANGING ev_success ev_message.
    ENDCASE.
  ENDLOOP.

ENDFUNCTION.
```

### 3. REST Service Integration

**A. SAP Gateway Service Definition**

**Service ID**: `ZCOMMON_PO_SRV`
**Service Version**: `0001`

**Entity Types**:
- PurchaseOrder
- Amendment
- Company
- Product

**Entity Sets**:
- PurchaseOrderSet
- AmendmentSet
- CompanySet
- ProductSet

**B. OData Service Implementation**

**Class**: `ZCL_COMMON_PO_DPC_EXT`
```abap
CLASS zcl_common_po_dpc_ext DEFINITION
  PUBLIC
  INHERITING FROM zcl_common_po_dpc
  FINAL
  CREATE PUBLIC .

  PUBLIC SECTION.
    METHODS: purchaseorderset_create_entity REDEFINITION,
             purchaseorderset_get_entityset REDEFINITION,
             amendmentset_create_entity REDEFINITION.

  PRIVATE SECTION.
    METHODS: call_common_api
               IMPORTING iv_method TYPE string
                        iv_url TYPE string
                        iv_data TYPE string OPTIONAL
               RETURNING VALUE(rv_response) TYPE string.

ENDCLASS.

CLASS zcl_common_po_dpc_ext IMPLEMENTATION.

  METHOD purchaseorderset_create_entity.
    " Create purchase order via Common API
    DATA: lv_json TYPE string,
          lv_response TYPE string.

    " Convert entity to JSON
    PERFORM entity_to_json USING er_entity
                         CHANGING lv_json.

    " Call Common API
    lv_response = call_common_api(
      iv_method = 'POST'
      iv_url = '/api/v1/purchase-orders'
      iv_data = lv_json ).

    " Parse response and update entity
    PERFORM parse_po_response USING lv_response
                            CHANGING er_entity.
  ENDMETHOD.

  METHOD amendmentset_create_entity.
    " Propose amendment via Common API
    DATA: lv_json TYPE string,
          lv_response TYPE string,
          lv_url TYPE string.

    " Convert amendment to JSON
    PERFORM amendment_to_json USING er_entity
                            CHANGING lv_json.

    " Build URL with PO ID
    CONCATENATE '/api/v1/purchase-orders/' 
                er_entity-common_po_id 
                '/propose-changes' INTO lv_url.

    " Call Common API
    lv_response = call_common_api(
      iv_method = 'PUT'
      iv_url = lv_url
      iv_data = lv_json ).

    " Parse response
    PERFORM parse_amendment_response USING lv_response
                                   CHANGING er_entity.
  ENDMETHOD.

ENDCLASS.
```

### 4. Field Mapping Templates

**A. SAP MM to Common Mapping**
```json
{
  "mappingName": "SAP_MM_to_Common_PO",
  "sourceSystem": "SAP_ECC",
  "targetSystem": "Common",
  "mappings": {
    "header": {
      "EBELN": "po_number",
      "LIFNR": "seller_company_id",
      "BUKRS": "buyer_company_id",
      "BEDAT": "created_date",
      "BSART": "po_type"
    },
    "items": {
      "EBELP": "line_number",
      "MATNR": "product_id",
      "MENGE": "quantity",
      "MEINS": "unit",
      "NETPR": "unit_price",
      "NETWR": "total_amount",
      "EINDT": "delivery_date",
      "WERKS": "delivery_location"
    }
  },
  "transformations": {
    "MENGE": "decimal_3_places",
    "NETPR": "decimal_2_places",
    "EINDT": "sap_date_to_iso",
    "BEDAT": "sap_date_to_iso"
  }
}
```

**B. Common to SAP IDoc Mapping**
```json
{
  "mappingName": "Common_to_SAP_ORDERS05",
  "sourceSystem": "Common",
  "targetSystem": "SAP_ECC",
  "idocType": "ORDERS05",
  "mappings": {
    "E1EDK01": {
      "po_number": "BELNR",
      "created_date": "BEDAT",
      "currency": "CURCY"
    },
    "E1EDP01": {
      "line_number": "POSEX",
      "quantity": "MENGE",
      "unit": "MENEE",
      "unit_price": "NETPR",
      "delivery_date": "EINDT",
      "delivery_location": "WERKS"
    }
  },
  "transformations": {
    "created_date": "iso_to_sap_date",
    "delivery_date": "iso_to_sap_date",
    "quantity": "decimal_to_sap_quantity",
    "unit_price": "decimal_to_sap_price"
  }
}
```

## Configuration and Deployment

### 1. Transport Configuration

**Development Package**: `ZCOMMON`
**Transport Layer**: `ZCOM`

**Objects to Transport**:
- Function modules (Z_COMMON_*)
- IDoc message types and segments
- OData service definitions
- ABAP classes and programs
- Customizing tables

### 2. Security Configuration

**RFC Destinations**:
```
Destination: COMMON_API_PROD
Connection Type: G (HTTP to External Server)
Target Host: api.common.co
Service No: 443
Path Prefix: /api/v1
```

**SSL Configuration**:
- Import Common API SSL certificate
- Configure SSL client identity
- Enable SNI (Server Name Indication)

### 3. Monitoring and Logging

**Custom Tables**:
- `ZCOMMON_LOG`: Integration log table
- `ZCOMMON_CONFIG`: Configuration parameters
- `ZCOMMON_MAPPING`: Field mapping definitions

**Monitoring Program**: `ZCOMMON_MONITOR`
```abap
PROGRAM zcommon_monitor.

" Display integration statistics
SELECT * FROM zcommon_log
  WHERE created_date >= sy-datum - 7
  ORDER BY created_date DESC.

" Show success/failure rates
" Display recent errors
" Performance metrics
```

This specification provides comprehensive SAP integration templates for seamless connectivity with the Common platform across all major SAP integration patterns.

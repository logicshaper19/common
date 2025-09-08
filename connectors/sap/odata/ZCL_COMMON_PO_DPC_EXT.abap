CLASS zcl_common_po_dpc_ext DEFINITION
  PUBLIC
  INHERITING FROM zcl_common_po_dpc
  FINAL
  CREATE PUBLIC .

  PUBLIC SECTION.
    " Redefined methods for purchase order operations
    METHODS: purchaseorderset_create_entity REDEFINITION,
             purchaseorderset_get_entity REDEFINITION,
             purchaseorderset_get_entityset REDEFINITION,
             purchaseorderset_update_entity REDEFINITION,
             purchaseorderset_delete_entity REDEFINITION.

    " Redefined methods for amendment operations
    METHODS: amendmentset_create_entity REDEFINITION,
             amendmentset_get_entity REDEFINITION,
             amendmentset_get_entityset REDEFINITION,
             amendmentset_update_entity REDEFINITION.

    " Redefined methods for company operations
    METHODS: companyset_get_entity REDEFINITION,
             companyset_get_entityset REDEFINITION.

    " Redefined methods for product operations
    METHODS: productset_get_entity REDEFINITION,
             productset_get_entityset REDEFINITION.

  PRIVATE SECTION.
    " Helper methods
    METHODS: call_common_api
               IMPORTING iv_method TYPE string
                        iv_url TYPE string
                        iv_data TYPE string OPTIONAL
               RETURNING VALUE(rv_response) TYPE string
               RAISING   cx_root,

             handle_api_error
               IMPORTING iv_response TYPE string
                        iv_status_code TYPE i
               RAISING   /iwbep/cx_mgw_busi_exception,

             convert_po_to_common
               IMPORTING is_entity TYPE zcl_common_po_mpc=>ts_purchaseorder
               RETURNING VALUE(rv_json) TYPE string,

             convert_common_to_po
               IMPORTING iv_json TYPE string
               RETURNING VALUE(rs_entity) TYPE zcl_common_po_mpc=>ts_purchaseorder,

             convert_amendment_to_common
               IMPORTING is_entity TYPE zcl_common_po_mpc=>ts_amendment
               RETURNING VALUE(rv_json) TYPE string,

             convert_common_to_amendment
               IMPORTING iv_json TYPE string
               RETURNING VALUE(rs_entity) TYPE zcl_common_po_mpc=>ts_amendment,

             log_odata_operation
               IMPORTING iv_operation TYPE string
                        iv_entity_type TYPE string
                        iv_status TYPE string
                        iv_message TYPE string
                        iv_data TYPE string OPTIONAL.

ENDCLASS.

CLASS zcl_common_po_dpc_ext IMPLEMENTATION.

  METHOD purchaseorderset_create_entity.
    " Create purchase order via Common API

    DATA: lv_json TYPE string,
          lv_response TYPE string,
          lv_log_id TYPE string.

    " Generate log ID
    lv_log_id = cl_system_uuid=>create_uuid_x16_static( ).

    TRY.
        " Log operation start
        log_odata_operation(
          iv_operation = 'CREATE'
          iv_entity_type = 'PurchaseOrder'
          iv_status = 'STARTED'
          iv_message = |Creating PO for buyer: { er_entity-buyercompanyid }| ).

        " Convert entity to JSON
        lv_json = convert_po_to_common( er_entity ).

        " Call Common API
        lv_response = call_common_api(
          iv_method = 'POST'
          iv_url = '/api/v1/purchase-orders'
          iv_data = lv_json ).

        " Parse response and update entity
        er_entity = convert_common_to_po( lv_response ).

        " Log success
        log_odata_operation(
          iv_operation = 'CREATE'
          iv_entity_type = 'PurchaseOrder'
          iv_status = 'SUCCESS'
          iv_message = |PO created: { er_entity-commonpoid }|
          iv_data = lv_response ).

      CATCH cx_root INTO DATA(lx_error).
        " Log error
        log_odata_operation(
          iv_operation = 'CREATE'
          iv_entity_type = 'PurchaseOrder'
          iv_status = 'ERROR'
          iv_message = lx_error->get_text( )
          iv_data = lv_json ).

        " Raise business exception
        RAISE EXCEPTION TYPE /iwbep/cx_mgw_busi_exception
          EXPORTING
            textid  = /iwbep/cx_mgw_busi_exception=>business_error
            message = lx_error->get_text( ).
    ENDTRY.

  ENDMETHOD.

  METHOD purchaseorderset_get_entity.
    " Get single purchase order from Common API

    DATA: lv_url TYPE string,
          lv_response TYPE string,
          lv_po_id TYPE string.

    TRY.
        " Extract PO ID from key
        io_tech_request_context->get_converted_keys(
          IMPORTING
            es_key_values = DATA(ls_keys) ).

        lv_po_id = ls_keys-commonpoid.

        " Build URL
        lv_url = |/api/v1/purchase-orders/{ lv_po_id }|.

        " Log operation start
        log_odata_operation(
          iv_operation = 'GET'
          iv_entity_type = 'PurchaseOrder'
          iv_status = 'STARTED'
          iv_message = |Getting PO: { lv_po_id }| ).

        " Call Common API
        lv_response = call_common_api(
          iv_method = 'GET'
          iv_url = lv_url ).

        " Convert response to entity
        er_entity = convert_common_to_po( lv_response ).

        " Log success
        log_odata_operation(
          iv_operation = 'GET'
          iv_entity_type = 'PurchaseOrder'
          iv_status = 'SUCCESS'
          iv_message = |PO retrieved: { lv_po_id }| ).

      CATCH cx_root INTO DATA(lx_error).
        " Log error
        log_odata_operation(
          iv_operation = 'GET'
          iv_entity_type = 'PurchaseOrder'
          iv_status = 'ERROR'
          iv_message = lx_error->get_text( ) ).

        " Raise business exception
        RAISE EXCEPTION TYPE /iwbep/cx_mgw_busi_exception
          EXPORTING
            textid  = /iwbep/cx_mgw_busi_exception=>business_error
            message = lx_error->get_text( ).
    ENDTRY.

  ENDMETHOD.

  METHOD purchaseorderset_get_entityset.
    " Get list of purchase orders from Common API

    DATA: lv_url TYPE string,
          lv_response TYPE string,
          lv_filter TYPE string,
          lv_top TYPE string,
          lv_skip TYPE string.

    TRY.
        " Build query parameters from OData request
        lv_url = '/api/v1/purchase-orders'.

        " Handle $filter
        IF io_tech_request_context->get_filter( ) IS BOUND.
          " Convert OData filter to Common API filter
          " This is simplified - full implementation would parse OData filter syntax
          lv_filter = '?status=confirmed'.
          lv_url = |{ lv_url }{ lv_filter }|.
        ENDIF.

        " Handle $top (limit)
        DATA(lv_top_value) = io_tech_request_context->get_top( ).
        IF lv_top_value > 0.
          lv_top = |&per_page={ lv_top_value }|.
          lv_url = |{ lv_url }{ lv_top }|.
        ENDIF.

        " Handle $skip (offset)
        DATA(lv_skip_value) = io_tech_request_context->get_skip( ).
        IF lv_skip_value > 0.
          DATA(lv_page) = ( lv_skip_value / lv_top_value ) + 1.
          lv_skip = |&page={ lv_page }|.
          lv_url = |{ lv_url }{ lv_skip }|.
        ENDIF.

        " Log operation start
        log_odata_operation(
          iv_operation = 'GET_LIST'
          iv_entity_type = 'PurchaseOrder'
          iv_status = 'STARTED'
          iv_message = |Getting PO list with URL: { lv_url }| ).

        " Call Common API
        lv_response = call_common_api(
          iv_method = 'GET'
          iv_url = lv_url ).

        " Parse response and build entity set
        " This is simplified - full implementation would parse JSON array
        DATA: lo_json TYPE REF TO /ui2/cl_json.
        DATA: lt_po_data TYPE TABLE OF zcl_common_po_mpc=>ts_purchaseorder.

        " Convert JSON response to internal table
        /ui2/cl_json=>deserialize(
          EXPORTING
            json = lv_response
          CHANGING
            data = lt_po_data ).

        " Copy to result table
        et_entityset = lt_po_data.

        " Log success
        log_odata_operation(
          iv_operation = 'GET_LIST'
          iv_entity_type = 'PurchaseOrder'
          iv_status = 'SUCCESS'
          iv_message = |Retrieved { lines( et_entityset ) } purchase orders| ).

      CATCH cx_root INTO DATA(lx_error).
        " Log error
        log_odata_operation(
          iv_operation = 'GET_LIST'
          iv_entity_type = 'PurchaseOrder'
          iv_status = 'ERROR'
          iv_message = lx_error->get_text( ) ).

        " Raise business exception
        RAISE EXCEPTION TYPE /iwbep/cx_mgw_busi_exception
          EXPORTING
            textid  = /iwbep/cx_mgw_busi_exception=>business_error
            message = lx_error->get_text( ).
    ENDTRY.

  ENDMETHOD.

  METHOD amendmentset_create_entity.
    " Propose amendment via Common API

    DATA: lv_json TYPE string,
          lv_response TYPE string,
          lv_url TYPE string.

    TRY.
        " Log operation start
        log_odata_operation(
          iv_operation = 'CREATE'
          iv_entity_type = 'Amendment'
          iv_status = 'STARTED'
          iv_message = |Proposing amendment for PO: { er_entity-commonpoid }| ).

        " Convert amendment to JSON
        lv_json = convert_amendment_to_common( er_entity ).

        " Build URL with PO ID
        lv_url = |/api/v1/purchase-orders/{ er_entity-commonpoid }/propose-changes|.

        " Call Common API
        lv_response = call_common_api(
          iv_method = 'PUT'
          iv_url = lv_url
          iv_data = lv_json ).

        " Parse response
        er_entity = convert_common_to_amendment( lv_response ).

        " Log success
        log_odata_operation(
          iv_operation = 'CREATE'
          iv_entity_type = 'Amendment'
          iv_status = 'SUCCESS'
          iv_message = |Amendment proposed: { er_entity-amendmentid }|
          iv_data = lv_response ).

      CATCH cx_root INTO DATA(lx_error).
        " Log error
        log_odata_operation(
          iv_operation = 'CREATE'
          iv_entity_type = 'Amendment'
          iv_status = 'ERROR'
          iv_message = lx_error->get_text( )
          iv_data = lv_json ).

        " Raise business exception
        RAISE EXCEPTION TYPE /iwbep/cx_mgw_busi_exception
          EXPORTING
            textid  = /iwbep/cx_mgw_busi_exception=>business_error
            message = lx_error->get_text( ).
    ENDTRY.

  ENDMETHOD.

  METHOD call_common_api.
    " Call Common API with authentication and error handling

    DATA: lv_token TYPE string,
          lv_success TYPE abap_bool,
          lv_message TYPE string,
          lv_full_url TYPE string,
          lo_http_client TYPE REF TO if_http_client,
          lv_status_code TYPE i.

    " Get authentication token
    PERFORM get_auth_token CHANGING lv_token lv_success lv_message.
    IF lv_success = abap_false.
      RAISE EXCEPTION TYPE cx_root
        EXPORTING
          textid = VALUE #( msgid = 'ZCOMMON' msgno = '001' attr1 = lv_message ).
    ENDIF.

    " Get base URL from configuration
    DATA: lv_base_url TYPE string.
    SELECT SINGLE config_value FROM zcommon_config
      INTO lv_base_url
      WHERE config_key = 'API_BASE_URL'.

    IF lv_base_url IS INITIAL.
      lv_base_url = 'https://api.common.co'.
    ENDIF.

    " Build full URL
    lv_full_url = |{ lv_base_url }{ iv_url }|.

    " Create HTTP client
    CALL METHOD cl_http_client=>create_by_url
      EXPORTING
        url    = lv_full_url
        ssl_id = 'ANONYM'
      IMPORTING
        client = lo_http_client.

    " Set headers
    lo_http_client->request->set_header_field(
      name  = 'Authorization'
      value = |Bearer { lv_token }| ).
    lo_http_client->request->set_header_field(
      name  = 'Content-Type'
      value = 'application/json' ).
    lo_http_client->request->set_header_field(
      name  = 'Accept'
      value = 'application/json' ).
    lo_http_client->request->set_header_field(
      name  = 'User-Agent'
      value = 'SAP-OData-Service/1.0' ).

    " Set method and data
    lo_http_client->request->set_method( iv_method ).
    IF iv_data IS NOT INITIAL.
      lo_http_client->request->set_cdata( iv_data ).
    ENDIF.

    " Send request
    lo_http_client->send( ).
    lo_http_client->receive( ).

    " Get response
    rv_response = lo_http_client->response->get_cdata( ).
    lo_http_client->response->get_status( IMPORTING code = lv_status_code ).

    " Close connection
    lo_http_client->close( ).

    " Check status
    IF lv_status_code < 200 OR lv_status_code >= 300.
      handle_api_error( iv_response = rv_response iv_status_code = lv_status_code ).
    ENDIF.

  ENDMETHOD.

  METHOD convert_po_to_common.
    " Convert SAP entity to Common API JSON format

    DATA: lo_json TYPE REF TO /ui2/cl_json.

    " Build JSON structure
    DATA: BEGIN OF ls_po,
            buyer_company_id TYPE string,
            seller_company_id TYPE string,
            product_id TYPE string,
            quantity TYPE string,
            unit_price TYPE string,
            unit TYPE string,
            delivery_date TYPE string,
            delivery_location TYPE string,
            notes TYPE string,
            po_number TYPE string,
          END OF ls_po.

    " Map fields
    ls_po-buyer_company_id = is_entity-buyercompanyid.
    ls_po-seller_company_id = is_entity-sellercompanyid.
    ls_po-product_id = is_entity-productid.
    ls_po-quantity = |{ is_entity-quantity }|.
    ls_po-unit_price = |{ is_entity-unitprice }|.
    ls_po-unit = is_entity-unit.
    ls_po-delivery_date = |{ is_entity-deliverydate+0(4) }-{ is_entity-deliverydate+4(2) }-{ is_entity-deliverydate+6(2) }|.
    ls_po-delivery_location = is_entity-deliverylocation.
    ls_po-notes = is_entity-notes.
    ls_po-po_number = is_entity-ponumber.

    " Convert to JSON
    rv_json = /ui2/cl_json=>serialize( data = ls_po ).

  ENDMETHOD.

  METHOD log_odata_operation.
    " Log OData operation for monitoring

    DATA: wa_log TYPE zcommon_log.

    wa_log-log_id = cl_system_uuid=>create_uuid_x16_static( ).
    wa_log-timestamp = |{ sy-datum }{ sy-uzeit }|.
    wa_log-integration_type = 'ODATA'.
    wa_log-operation = |{ iv_operation }_{ iv_entity_type }|.
    wa_log-status = iv_status.
    wa_log-message = iv_message.
    wa_log-request_data = iv_data.
    wa_log-created_by = sy-uname.
    wa_log-created_date = sy-datum.
    wa_log-created_time = sy-uzeit.

    INSERT zcommon_log FROM wa_log.
    COMMIT WORK.

  ENDMETHOD.

ENDCLASS.

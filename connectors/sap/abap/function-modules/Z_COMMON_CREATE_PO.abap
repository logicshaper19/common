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
*"     VALUE(IV_PO_NUMBER) TYPE STRING OPTIONAL
*"     VALUE(IV_COMPOSITION) TYPE STRING OPTIONAL
*"     VALUE(IV_INPUT_MATERIALS) TYPE STRING OPTIONAL
*"     VALUE(IV_ORIGIN_DATA) TYPE STRING OPTIONAL
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

  " Data declarations
  DATA: lv_po_data TYPE string,
        lv_response TYPE string,
        lv_log_id TYPE string,
        lv_timestamp TYPE string,
        lo_json TYPE REF TO cl_trex_json_serializer.

  " Initialize
  CLEAR: ev_common_po_id, ev_sap_po_number, ev_success, ev_message.
  
  " Generate log ID for tracking
  lv_log_id = cl_system_uuid=>create_uuid_x16_static( ).
  GET TIME STAMP FIELD DATA(lv_ts).
  lv_timestamp = |{ lv_ts TIMESTAMP = ISO }|.

  " Log request start
  PERFORM log_integration_event USING lv_log_id
                                      'RFC'
                                      'CREATE_PO'
                                      'STARTED'
                                      ''
                                      ''
                                      ''.

  " Input validation
  PERFORM validate_create_po_input USING iv_buyer_company
                                         iv_seller_company
                                         iv_product_id
                                         iv_quantity
                                         iv_unit_price
                                         iv_unit
                                         iv_delivery_date
                                         iv_delivery_location
                                   CHANGING ev_success
                                           ev_message.

  IF ev_success = abap_false.
    " Log validation error
    PERFORM log_integration_event USING lv_log_id
                                        'RFC'
                                        'CREATE_PO'
                                        'ERROR'
                                        'VALIDATION_ERROR'
                                        ev_message
                                        ''.
    RAISE validation_error.
  ENDIF.

  " Build JSON payload for Common API
  PERFORM build_po_json_payload USING iv_buyer_company
                                      iv_seller_company
                                      iv_product_id
                                      iv_quantity
                                      iv_unit_price
                                      iv_unit
                                      iv_delivery_date
                                      iv_delivery_location
                                      iv_notes
                                      iv_po_number
                                      iv_composition
                                      iv_input_materials
                                      iv_origin_data
                              CHANGING lv_po_data.

  " Log request payload
  PERFORM log_integration_event USING lv_log_id
                                      'RFC'
                                      'CREATE_PO'
                                      'REQUEST'
                                      ''
                                      ''
                                      lv_po_data.

  " Call Common API
  PERFORM call_common_api USING 'POST'
                                '/api/v1/purchase-orders'
                                lv_po_data
                         CHANGING lv_response
                                  ev_success
                                  ev_message.

  " Log API response
  PERFORM log_integration_event USING lv_log_id
                                      'RFC'
                                      'CREATE_PO'
                                      COND #( WHEN ev_success = abap_true THEN 'SUCCESS' ELSE 'ERROR' )
                                      COND #( WHEN ev_success = abap_false THEN 'API_ERROR' ELSE '' )
                                      ev_message
                                      lv_response.

  IF ev_success = abap_true.
    " Parse response and extract Common PO ID
    PERFORM parse_po_response USING lv_response
                             CHANGING ev_common_po_id
                                      ev_sap_po_number
                                      ev_success
                                      ev_message.

    IF ev_success = abap_true.
      " Update local SAP tables if needed
      PERFORM update_sap_po_tables USING ev_common_po_id
                                         ev_sap_po_number
                                         iv_buyer_company
                                         iv_seller_company
                                         iv_product_id
                                         iv_quantity
                                         iv_unit_price
                                         iv_unit
                                         iv_delivery_date
                                         iv_delivery_location.

      " Log final success
      PERFORM log_integration_event USING lv_log_id
                                          'RFC'
                                          'CREATE_PO'
                                          'COMPLETED'
                                          ''
                                          |PO created: { ev_common_po_id }|
                                          ''.
    ELSE.
      " Log parsing error
      PERFORM log_integration_event USING lv_log_id
                                          'RFC'
                                          'CREATE_PO'
                                          'ERROR'
                                          'PARSE_ERROR'
                                          ev_message
                                          lv_response.
      RAISE creation_failed.
    ENDIF.
  ELSE.
    " API call failed
    RAISE communication_error.
  ENDIF.

ENDFUNCTION.

*----------------------------------------------------------------------*
*       FORM validate_create_po_input
*----------------------------------------------------------------------*
FORM validate_create_po_input USING p_buyer_company TYPE string
                                    p_seller_company TYPE string
                                    p_product_id TYPE string
                                    p_quantity TYPE p
                                    p_unit_price TYPE p
                                    p_unit TYPE meins
                                    p_delivery_date TYPE dats
                                    p_delivery_location TYPE string
                             CHANGING p_success TYPE abap_bool
                                     p_message TYPE string.

  DATA: lv_errors TYPE TABLE OF string,
        lv_error TYPE string.

  " Validate required fields
  IF p_buyer_company IS INITIAL.
    APPEND 'Buyer company ID is required' TO lv_errors.
  ENDIF.

  IF p_seller_company IS INITIAL.
    APPEND 'Seller company ID is required' TO lv_errors.
  ENDIF.

  IF p_product_id IS INITIAL.
    APPEND 'Product ID is required' TO lv_errors.
  ENDIF.

  IF p_quantity <= 0.
    APPEND 'Quantity must be greater than 0' TO lv_errors.
  ENDIF.

  IF p_unit_price <= 0.
    APPEND 'Unit price must be greater than 0' TO lv_errors.
  ENDIF.

  IF p_unit IS INITIAL.
    APPEND 'Unit of measure is required' TO lv_errors.
  ENDIF.

  IF p_delivery_date IS INITIAL.
    APPEND 'Delivery date is required' TO lv_errors.
  ENDIF.

  IF p_delivery_location IS INITIAL.
    APPEND 'Delivery location is required' TO lv_errors.
  ENDIF.

  " Validate UUID format for IDs
  IF p_buyer_company IS NOT INITIAL.
    PERFORM validate_uuid USING p_buyer_company CHANGING lv_error.
    IF lv_error IS NOT INITIAL.
      APPEND |Invalid buyer company UUID: { lv_error }| TO lv_errors.
    ENDIF.
  ENDIF.

  IF p_seller_company IS NOT INITIAL.
    PERFORM validate_uuid USING p_seller_company CHANGING lv_error.
    IF lv_error IS NOT INITIAL.
      APPEND |Invalid seller company UUID: { lv_error }| TO lv_errors.
    ENDIF.
  ENDIF.

  IF p_product_id IS NOT INITIAL.
    PERFORM validate_uuid USING p_product_id CHANGING lv_error.
    IF lv_error IS NOT INITIAL.
      APPEND |Invalid product UUID: { lv_error }| TO lv_errors.
    ENDIF.
  ENDIF.

  " Validate delivery date is not in the past
  IF p_delivery_date < sy-datum.
    APPEND 'Delivery date cannot be in the past' TO lv_errors.
  ENDIF.

  " Check if there are validation errors
  IF lines( lv_errors ) > 0.
    p_success = abap_false.
    LOOP AT lv_errors INTO lv_error.
      IF sy-tabix = 1.
        p_message = lv_error.
      ELSE.
        p_message = |{ p_message }; { lv_error }|.
      ENDIF.
    ENDLOOP.
  ELSE.
    p_success = abap_true.
    p_message = 'Validation passed'.
  ENDIF.

ENDFORM.

*----------------------------------------------------------------------*
*       FORM build_po_json_payload
*----------------------------------------------------------------------*
FORM build_po_json_payload USING p_buyer_company TYPE string
                                 p_seller_company TYPE string
                                 p_product_id TYPE string
                                 p_quantity TYPE p
                                 p_unit_price TYPE p
                                 p_unit TYPE meins
                                 p_delivery_date TYPE dats
                                 p_delivery_location TYPE string
                                 p_notes TYPE string
                                 p_po_number TYPE string
                                 p_composition TYPE string
                                 p_input_materials TYPE string
                                 p_origin_data TYPE string
                          CHANGING p_json_data TYPE string.

  DATA: lv_delivery_date_iso TYPE string,
        lv_quantity_str TYPE string,
        lv_price_str TYPE string.

  " Convert date to ISO format
  lv_delivery_date_iso = |{ p_delivery_date+0(4) }-{ p_delivery_date+4(2) }-{ p_delivery_date+6(2) }|.

  " Convert numbers to strings
  lv_quantity_str = |{ p_quantity }|.
  lv_price_str = |{ p_unit_price }|.

  " Build JSON payload
  p_json_data = |{| &&
    |"buyer_company_id":"{ p_buyer_company }",| &&
    |"seller_company_id":"{ p_seller_company }",| &&
    |"product_id":"{ p_product_id }",| &&
    |"quantity":{ lv_quantity_str },| &&
    |"unit_price":{ lv_price_str },| &&
    |"unit":"{ p_unit }",| &&
    |"delivery_date":"{ lv_delivery_date_iso }",| &&
    |"delivery_location":"{ p_delivery_location }"|.

  " Add optional fields
  IF p_notes IS NOT INITIAL.
    p_json_data = |{ p_json_data },"notes":"{ p_notes }"|.
  ENDIF.

  IF p_po_number IS NOT INITIAL.
    p_json_data = |{ p_json_data },"po_number":"{ p_po_number }"|.
  ENDIF.

  IF p_composition IS NOT INITIAL.
    p_json_data = |{ p_json_data },"composition":{ p_composition }|.
  ENDIF.

  IF p_input_materials IS NOT INITIAL.
    p_json_data = |{ p_json_data },"input_materials":{ p_input_materials }|.
  ENDIF.

  IF p_origin_data IS NOT INITIAL.
    p_json_data = |{ p_json_data },"origin_data":{ p_origin_data }|.
  ENDIF.

  " Close JSON object
  p_json_data = |{ p_json_data }}}|.

ENDFORM.

*----------------------------------------------------------------------*
*       FORM parse_po_response
*----------------------------------------------------------------------*
FORM parse_po_response USING p_response TYPE string
                      CHANGING p_common_po_id TYPE string
                              p_sap_po_number TYPE ebeln
                              p_success TYPE abap_bool
                              p_message TYPE string.

  DATA: lo_reader TYPE REF TO cl_sxml_string_reader,
        lo_json TYPE REF TO if_sxml_reader.

  TRY.
    " Parse JSON response
    lo_reader = cl_sxml_string_reader=>create( p_response ).
    
    " Extract Common PO ID from response
    " This is a simplified parsing - in production, use proper JSON parser
    FIND REGEX '"id":"([^"]+)"' IN p_response SUBMATCHES p_common_po_id.
    
    IF p_common_po_id IS NOT INITIAL.
      " Generate SAP PO number (this would typically come from SAP PO creation)
      p_sap_po_number = |45{ sy-datum+2(6) }|.
      p_success = abap_true.
      p_message = 'Purchase order created successfully'.
    ELSE.
      p_success = abap_false.
      p_message = 'Failed to extract PO ID from response'.
    ENDIF.

  CATCH cx_sxml_parse_error INTO DATA(lx_parse).
    p_success = abap_false.
    p_message = |JSON parsing error: { lx_parse->get_text( ) }|.
  ENDTRY.

ENDFORM.

*----------------------------------------------------------------------*
*       FORM update_sap_po_tables
*----------------------------------------------------------------------*
FORM update_sap_po_tables USING p_common_po_id TYPE string
                                p_sap_po_number TYPE ebeln
                                p_buyer_company TYPE string
                                p_seller_company TYPE string
                                p_product_id TYPE string
                                p_quantity TYPE p
                                p_unit_price TYPE p
                                p_unit TYPE meins
                                p_delivery_date TYPE dats
                                p_delivery_location TYPE string.

  " Update custom table to track Common PO mappings
  DATA: wa_mapping TYPE zcommon_po_mapping.

  wa_mapping-common_po_id = p_common_po_id.
  wa_mapping-sap_po_number = p_sap_po_number.
  wa_mapping-buyer_company_id = p_buyer_company.
  wa_mapping-seller_company_id = p_seller_company.
  wa_mapping-product_id = p_product_id.
  wa_mapping-quantity = p_quantity.
  wa_mapping-unit_price = p_unit_price.
  wa_mapping-unit = p_unit.
  wa_mapping-delivery_date = p_delivery_date.
  wa_mapping-delivery_location = p_delivery_location.
  wa_mapping-created_date = sy-datum.
  wa_mapping-created_time = sy-uzeit.
  wa_mapping-created_by = sy-uname.
  wa_mapping-status = 'ACTIVE'.

  INSERT zcommon_po_mapping FROM wa_mapping.
  IF sy-subrc = 0.
    COMMIT WORK.
  ENDIF.

ENDFORM.

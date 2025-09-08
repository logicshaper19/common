FUNCTION Z_COMMON_PROPOSE_AMENDMENT.
*"----------------------------------------------------------------------
*"*"Local Interface:
*"  IMPORTING
*"     VALUE(IV_COMMON_PO_ID) TYPE STRING
*"     VALUE(IV_PROPOSED_QUANTITY) TYPE P DECIMALS 3
*"     VALUE(IV_PROPOSED_UNIT) TYPE MEINS
*"     VALUE(IV_AMENDMENT_REASON) TYPE STRING
*"     VALUE(IV_REQUESTER_EMAIL) TYPE STRING OPTIONAL
*"     VALUE(IV_PRIORITY) TYPE STRING OPTIONAL
*"  EXPORTING
*"     VALUE(EV_AMENDMENT_ID) TYPE STRING
*"     VALUE(EV_AMENDMENT_STATUS) TYPE STRING
*"     VALUE(EV_SUCCESS) TYPE ABAP_BOOL
*"     VALUE(EV_MESSAGE) TYPE STRING
*"  EXCEPTIONS
*"     VALIDATION_ERROR
*"     AMENDMENT_FAILED
*"     COMMUNICATION_ERROR
*"----------------------------------------------------------------------

  " Data declarations
  DATA: lv_amendment_data TYPE string,
        lv_response TYPE string,
        lv_url TYPE string,
        lv_log_id TYPE string,
        lv_timestamp TYPE string.

  " Initialize
  CLEAR: ev_amendment_id, ev_amendment_status, ev_success, ev_message.
  
  " Generate log ID for tracking
  lv_log_id = cl_system_uuid=>create_uuid_x16_static( ).
  GET TIME STAMP FIELD DATA(lv_ts).
  lv_timestamp = |{ lv_ts TIMESTAMP = ISO }|.

  " Log request start
  PERFORM log_integration_event USING lv_log_id
                                      'RFC'
                                      'PROPOSE_AMENDMENT'
                                      'STARTED'
                                      ''
                                      ''
                                      ''.

  " Input validation
  PERFORM validate_amendment_input USING iv_common_po_id
                                         iv_proposed_quantity
                                         iv_proposed_unit
                                         iv_amendment_reason
                                   CHANGING ev_success
                                           ev_message.

  IF ev_success = abap_false.
    " Log validation error
    PERFORM log_integration_event USING lv_log_id
                                        'RFC'
                                        'PROPOSE_AMENDMENT'
                                        'ERROR'
                                        'VALIDATION_ERROR'
                                        ev_message
                                        ''.
    RAISE validation_error.
  ENDIF.

  " Check if PO exists and is amendable
  PERFORM check_po_amendable USING iv_common_po_id
                            CHANGING ev_success
                                    ev_message.

  IF ev_success = abap_false.
    " Log business rule error
    PERFORM log_integration_event USING lv_log_id
                                        'RFC'
                                        'PROPOSE_AMENDMENT'
                                        'ERROR'
                                        'BUSINESS_RULE_ERROR'
                                        ev_message
                                        ''.
    RAISE amendment_failed.
  ENDIF.

  " Build amendment JSON payload
  PERFORM build_amendment_json_payload USING iv_proposed_quantity
                                             iv_proposed_unit
                                             iv_amendment_reason
                                             iv_requester_email
                                             iv_priority
                                       CHANGING lv_amendment_data.

  " Build URL with PO ID
  lv_url = |/api/v1/purchase-orders/{ iv_common_po_id }/propose-changes|.

  " Log request payload
  PERFORM log_integration_event USING lv_log_id
                                      'RFC'
                                      'PROPOSE_AMENDMENT'
                                      'REQUEST'
                                      ''
                                      ''
                                      lv_amendment_data.

  " Call Common API
  PERFORM call_common_api USING 'PUT'
                                lv_url
                                lv_amendment_data
                         CHANGING lv_response
                                  ev_success
                                  ev_message.

  " Log API response
  PERFORM log_integration_event USING lv_log_id
                                      'RFC'
                                      'PROPOSE_AMENDMENT'
                                      COND #( WHEN ev_success = abap_true THEN 'SUCCESS' ELSE 'ERROR' )
                                      COND #( WHEN ev_success = abap_false THEN 'API_ERROR' ELSE '' )
                                      ev_message
                                      lv_response.

  IF ev_success = abap_true.
    " Parse amendment response
    PERFORM parse_amendment_response USING lv_response
                                   CHANGING ev_amendment_id
                                           ev_amendment_status
                                           ev_success
                                           ev_message.

    IF ev_success = abap_true.
      " Update local SAP tables
      PERFORM update_sap_amendment_tables USING iv_common_po_id
                                                ev_amendment_id
                                                iv_proposed_quantity
                                                iv_proposed_unit
                                                iv_amendment_reason
                                                ev_amendment_status.

      " Send notification if configured
      PERFORM send_amendment_notification USING iv_common_po_id
                                                ev_amendment_id
                                                iv_amendment_reason
                                                ev_amendment_status.

      " Log final success
      PERFORM log_integration_event USING lv_log_id
                                          'RFC'
                                          'PROPOSE_AMENDMENT'
                                          'COMPLETED'
                                          ''
                                          |Amendment proposed: { ev_amendment_id }|
                                          ''.
    ELSE.
      " Log parsing error
      PERFORM log_integration_event USING lv_log_id
                                          'RFC'
                                          'PROPOSE_AMENDMENT'
                                          'ERROR'
                                          'PARSE_ERROR'
                                          ev_message
                                          lv_response.
      RAISE amendment_failed.
    ENDIF.
  ELSE.
    " API call failed
    RAISE communication_error.
  ENDIF.

ENDFUNCTION.

*----------------------------------------------------------------------*
*       FORM validate_amendment_input
*----------------------------------------------------------------------*
FORM validate_amendment_input USING p_common_po_id TYPE string
                                    p_proposed_quantity TYPE p
                                    p_proposed_unit TYPE meins
                                    p_amendment_reason TYPE string
                             CHANGING p_success TYPE abap_bool
                                     p_message TYPE string.

  DATA: lv_errors TYPE TABLE OF string,
        lv_error TYPE string.

  " Validate required fields
  IF p_common_po_id IS INITIAL.
    APPEND 'Common PO ID is required' TO lv_errors.
  ENDIF.

  IF p_proposed_quantity <= 0.
    APPEND 'Proposed quantity must be greater than 0' TO lv_errors.
  ENDIF.

  IF p_proposed_unit IS INITIAL.
    APPEND 'Proposed unit is required' TO lv_errors.
  ENDIF.

  IF p_amendment_reason IS INITIAL.
    APPEND 'Amendment reason is required' TO lv_errors.
  ENDIF.

  " Validate amendment reason length
  IF strlen( p_amendment_reason ) < 10.
    APPEND 'Amendment reason must be at least 10 characters' TO lv_errors.
  ENDIF.

  " Validate UUID format for PO ID
  IF p_common_po_id IS NOT INITIAL.
    PERFORM validate_uuid USING p_common_po_id CHANGING lv_error.
    IF lv_error IS NOT INITIAL.
      APPEND |Invalid Common PO UUID: { lv_error }| TO lv_errors.
    ENDIF.
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
*       FORM check_po_amendable
*----------------------------------------------------------------------*
FORM check_po_amendable USING p_common_po_id TYPE string
                       CHANGING p_success TYPE abap_bool
                               p_message TYPE string.

  DATA: wa_mapping TYPE zcommon_po_mapping.

  " Check if PO exists in local mapping table
  SELECT SINGLE * FROM zcommon_po_mapping
    INTO wa_mapping
    WHERE common_po_id = p_common_po_id
    AND status = 'ACTIVE'.

  IF sy-subrc <> 0.
    p_success = abap_false.
    p_message = 'Purchase order not found or inactive'.
    RETURN.
  ENDIF.

  " Check if PO is in amendable status
  " This could include additional business logic checks
  CASE wa_mapping-po_status.
    WHEN 'CONFIRMED' OR 'PENDING'.
      p_success = abap_true.
      p_message = 'Purchase order is amendable'.
    WHEN 'SHIPPED' OR 'DELIVERED' OR 'CANCELLED'.
      p_success = abap_false.
      p_message = |Purchase order status '{ wa_mapping-po_status }' does not allow amendments|.
    WHEN OTHERS.
      p_success = abap_false.
      p_message = 'Purchase order status unknown or not amendable'.
  ENDCASE.

ENDFORM.

*----------------------------------------------------------------------*
*       FORM build_amendment_json_payload
*----------------------------------------------------------------------*
FORM build_amendment_json_payload USING p_proposed_quantity TYPE p
                                         p_proposed_unit TYPE meins
                                         p_amendment_reason TYPE string
                                         p_requester_email TYPE string
                                         p_priority TYPE string
                                  CHANGING p_json_data TYPE string.

  DATA: lv_quantity_str TYPE string.

  " Convert quantity to string
  lv_quantity_str = |{ p_proposed_quantity }|.

  " Build JSON payload
  p_json_data = |{| &&
    |"proposed_quantity":{ lv_quantity_str },| &&
    |"proposed_quantity_unit":"{ p_proposed_unit }",| &&
    |"amendment_reason":"{ p_amendment_reason }"|.

  " Add optional fields
  IF p_requester_email IS NOT INITIAL.
    p_json_data = |{ p_json_data },"requester_email":"{ p_requester_email }"|.
  ENDIF.

  IF p_priority IS NOT INITIAL.
    p_json_data = |{ p_json_data },"priority":"{ p_priority }"|.
  ENDIF.

  " Add SAP-specific metadata
  p_json_data = |{ p_json_data },"source_system":"SAP","source_user":"{ sy-uname }"|.

  " Close JSON object
  p_json_data = |{ p_json_data }}}|.

ENDFORM.

*----------------------------------------------------------------------*
*       FORM parse_amendment_response
*----------------------------------------------------------------------*
FORM parse_amendment_response USING p_response TYPE string
                             CHANGING p_amendment_id TYPE string
                                     p_amendment_status TYPE string
                                     p_success TYPE abap_bool
                                     p_message TYPE string.

  TRY.
    " Parse JSON response
    " This is a simplified parsing - in production, use proper JSON parser
    FIND REGEX '"amendment_id":"([^"]+)"' IN p_response SUBMATCHES p_amendment_id.
    FIND REGEX '"amendment_status":"([^"]+)"' IN p_response SUBMATCHES p_amendment_status.
    
    IF p_amendment_id IS NOT INITIAL AND p_amendment_status IS NOT INITIAL.
      p_success = abap_true.
      p_message = |Amendment proposed successfully with status: { p_amendment_status }|.
    ELSE.
      p_success = abap_false.
      p_message = 'Failed to extract amendment details from response'.
    ENDIF.

  CATCH cx_sy_regex INTO DATA(lx_regex).
    p_success = abap_false.
    p_message = |Response parsing error: { lx_regex->get_text( ) }|.
  ENDTRY.

ENDFORM.

*----------------------------------------------------------------------*
*       FORM update_sap_amendment_tables
*----------------------------------------------------------------------*
FORM update_sap_amendment_tables USING p_common_po_id TYPE string
                                        p_amendment_id TYPE string
                                        p_proposed_quantity TYPE p
                                        p_proposed_unit TYPE meins
                                        p_amendment_reason TYPE string
                                        p_amendment_status TYPE string.

  " Update custom table to track amendments
  DATA: wa_amendment TYPE zcommon_amendment.

  wa_amendment-amendment_id = p_amendment_id.
  wa_amendment-common_po_id = p_common_po_id.
  wa_amendment-amendment_type = 'QUANTITY_CHANGE'.
  wa_amendment-proposed_quantity = p_proposed_quantity.
  wa_amendment-proposed_unit = p_proposed_unit.
  wa_amendment-amendment_reason = p_amendment_reason.
  wa_amendment-amendment_status = p_amendment_status.
  wa_amendment-created_date = sy-datum.
  wa_amendment-created_time = sy-uzeit.
  wa_amendment-created_by = sy-uname.
  wa_amendment-source_system = 'SAP'.

  INSERT zcommon_amendment FROM wa_amendment.
  IF sy-subrc = 0.
    COMMIT WORK.
  ENDIF.

ENDFORM.

*----------------------------------------------------------------------*
*       FORM send_amendment_notification
*----------------------------------------------------------------------*
FORM send_amendment_notification USING p_common_po_id TYPE string
                                        p_amendment_id TYPE string
                                        p_amendment_reason TYPE string
                                        p_amendment_status TYPE string.

  " Send email notification if configured
  DATA: lv_subject TYPE string,
        lv_body TYPE string,
        lv_recipient TYPE string.

  " Get notification configuration
  SELECT SINGLE notification_email FROM zcommon_config
    INTO lv_recipient
    WHERE config_key = 'AMENDMENT_NOTIFICATION_EMAIL'.

  IF lv_recipient IS NOT INITIAL.
    lv_subject = |Amendment Proposed for PO { p_common_po_id }|.
    lv_body = |An amendment has been proposed for purchase order { p_common_po_id }.| &&
              |Amendment ID: { p_amendment_id }| &&
              |Status: { p_amendment_status }| &&
              |Reason: { p_amendment_reason }| &&
              |Proposed by: { sy-uname } on { sy-datum }|.

    " Send email using SAP standard function
    CALL FUNCTION 'SO_NEW_DOCUMENT_ATT_SEND_API1'
      EXPORTING
        document_data              = VALUE sodocchgi1( obj_name = 'Amendment Notification'
                                                       obj_descr = lv_subject )
        document_type              = 'RAW'
      TABLES
        object_content             = VALUE soli_tab( ( line = lv_body ) )
        receivers                  = VALUE somlreci1_tab( ( receiver = lv_recipient
                                                           rec_type = 'U' ) )
      EXCEPTIONS
        too_many_receivers         = 1
        document_not_sent          = 2
        document_type_not_exist    = 3
        operation_no_authorization = 4
        parameter_error            = 5
        x_error                    = 6
        enqueue_error              = 7
        OTHERS                     = 8.

    IF sy-subrc = 0.
      COMMIT WORK.
    ENDIF.
  ENDIF.

ENDFORM.

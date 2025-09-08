*&---------------------------------------------------------------------*
*& Include          ZCOMMON_UTILITIES
*&---------------------------------------------------------------------*
*& Common utility functions for SAP-Common integration
*&---------------------------------------------------------------------*

*----------------------------------------------------------------------*
*       FORM call_common_api
*----------------------------------------------------------------------*
*       Calls Common API with authentication and error handling
*----------------------------------------------------------------------*
FORM call_common_api USING p_method TYPE string
                           p_url TYPE string
                           p_data TYPE string
                  CHANGING p_response TYPE string
                           p_success TYPE abap_bool
                           p_message TYPE string.

  DATA: lv_full_url TYPE string,
        lv_token TYPE string,
        lo_http_client TYPE REF TO if_http_client,
        lv_status_code TYPE i,
        lv_status_text TYPE string.

  " Initialize
  CLEAR: p_response, p_success, p_message.

  " Get authentication token
  PERFORM get_auth_token CHANGING lv_token p_success p_message.
  IF p_success = abap_false.
    RETURN.
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
  lv_full_url = |{ lv_base_url }{ p_url }|.

  TRY.
    " Create HTTP client
    CALL METHOD cl_http_client=>create_by_url
      EXPORTING
        url                = lv_full_url
        ssl_id             = 'ANONYM'
      IMPORTING
        client             = lo_http_client
      EXCEPTIONS
        argument_not_found = 1
        plugin_not_active  = 2
        internal_error     = 3
        OTHERS             = 4.

    IF sy-subrc <> 0.
      p_success = abap_false.
      p_message = |HTTP client creation failed: { sy-subrc }|.
      RETURN.
    ENDIF.

    " Set request headers
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
      value = 'SAP-Common-Integration/1.0' ).

    " Set HTTP method
    lo_http_client->request->set_method( p_method ).

    " Set request body if provided
    IF p_data IS NOT INITIAL.
      lo_http_client->request->set_cdata( p_data ).
    ENDIF.

    " Set timeout
    DATA: lv_timeout TYPE i.
    SELECT SINGLE config_value FROM zcommon_config
      INTO lv_timeout
      WHERE config_key = 'API_TIMEOUT'.
    IF lv_timeout IS INITIAL.
      lv_timeout = 30.
    ENDIF.
    lo_http_client->set_timeout( lv_timeout ).

    " Send request
    lo_http_client->send(
      EXCEPTIONS
        http_communication_failure = 1
        http_invalid_state         = 2
        http_processing_failed     = 3
        http_invalid_timeout       = 4
        OTHERS                     = 5 ).

    IF sy-subrc <> 0.
      p_success = abap_false.
      p_message = |HTTP send failed: { sy-subrc }|.
      lo_http_client->close( ).
      RETURN.
    ENDIF.

    " Receive response
    lo_http_client->receive(
      EXCEPTIONS
        http_communication_failure = 1
        http_invalid_state         = 2
        http_processing_failed     = 3
        OTHERS                     = 4 ).

    IF sy-subrc <> 0.
      p_success = abap_false.
      p_message = |HTTP receive failed: { sy-subrc }|.
      lo_http_client->close( ).
      RETURN.
    ENDIF.

    " Get response data
    p_response = lo_http_client->response->get_cdata( ).

    " Get status code
    lo_http_client->response->get_status(
      IMPORTING
        code   = lv_status_code
        reason = lv_status_text ).

    " Check status code
    IF lv_status_code BETWEEN 200 AND 299.
      p_success = abap_true.
      p_message = |Success: { lv_status_code } { lv_status_text }|.
    ELSE.
      p_success = abap_false.
      p_message = |HTTP Error { lv_status_code }: { lv_status_text }|.
      
      " Try to extract error message from response
      IF p_response IS NOT INITIAL.
        DATA: lv_error_msg TYPE string.
        FIND REGEX '"message":"([^"]+)"' IN p_response SUBMATCHES lv_error_msg.
        IF lv_error_msg IS NOT INITIAL.
          p_message = |{ p_message } - { lv_error_msg }|.
        ENDIF.
      ENDIF.
    ENDIF.

    " Close connection
    lo_http_client->close( ).

  CATCH cx_root INTO DATA(lx_error).
    p_success = abap_false.
    p_message = |Exception: { lx_error->get_text( ) }|.
    IF lo_http_client IS BOUND.
      lo_http_client->close( ).
    ENDIF.
  ENDTRY.

ENDFORM.

*----------------------------------------------------------------------*
*       FORM get_auth_token
*----------------------------------------------------------------------*
*       Gets OAuth 2.0 authentication token from Common API
*----------------------------------------------------------------------*
FORM get_auth_token CHANGING p_token TYPE string
                            p_success TYPE abap_bool
                            p_message TYPE string.

  DATA: lv_client_id TYPE string,
        lv_client_secret TYPE string,
        lv_auth_url TYPE string,
        lv_auth_data TYPE string,
        lv_response TYPE string,
        lo_http_client TYPE REF TO if_http_client,
        lv_status_code TYPE i.

  " Initialize
  CLEAR: p_token, p_success, p_message.

  " Get credentials from configuration
  SELECT config_value FROM zcommon_config
    INTO TABLE @DATA(lt_config)
    WHERE config_key IN ('CLIENT_ID', 'CLIENT_SECRET', 'AUTH_URL').

  LOOP AT lt_config INTO DATA(wa_config).
    CASE wa_config-config_key.
      WHEN 'CLIENT_ID'.
        lv_client_id = wa_config-config_value.
      WHEN 'CLIENT_SECRET'.
        lv_client_secret = wa_config-config_value.
      WHEN 'AUTH_URL'.
        lv_auth_url = wa_config-config_value.
    ENDCASE.
  ENDLOOP.

  " Set default auth URL if not configured
  IF lv_auth_url IS INITIAL.
    lv_auth_url = 'https://api.common.co/api/v1/auth/token'.
  ENDIF.

  " Validate credentials
  IF lv_client_id IS INITIAL OR lv_client_secret IS INITIAL.
    p_success = abap_false.
    p_message = 'Client credentials not configured'.
    RETURN.
  ENDIF.

  " Build authentication request
  lv_auth_data = |grant_type=client_credentials&client_id={ lv_client_id }&client_secret={ lv_client_secret }|.

  TRY.
    " Create HTTP client for authentication
    CALL METHOD cl_http_client=>create_by_url
      EXPORTING
        url    = lv_auth_url
        ssl_id = 'ANONYM'
      IMPORTING
        client = lo_http_client.

    " Set headers for OAuth request
    lo_http_client->request->set_header_field(
      name  = 'Content-Type'
      value = 'application/x-www-form-urlencoded' ).
    lo_http_client->request->set_header_field(
      name  = 'Accept'
      value = 'application/json' ).

    " Set method and data
    lo_http_client->request->set_method( 'POST' ).
    lo_http_client->request->set_cdata( lv_auth_data ).

    " Send authentication request
    lo_http_client->send( ).
    lo_http_client->receive( ).

    " Get response
    lv_response = lo_http_client->response->get_cdata( ).
    lo_http_client->response->get_status( IMPORTING code = lv_status_code ).

    " Close connection
    lo_http_client->close( ).

    " Check authentication response
    IF lv_status_code = 200.
      " Extract access token from response
      FIND REGEX '"access_token":"([^"]+)"' IN lv_response SUBMATCHES p_token.
      
      IF p_token IS NOT INITIAL.
        p_success = abap_true.
        p_message = 'Authentication successful'.
        
        " Cache token with expiration (optional enhancement)
        " PERFORM cache_auth_token USING p_token.
      ELSE.
        p_success = abap_false.
        p_message = 'Failed to extract access token from response'.
      ENDIF.
    ELSE.
      p_success = abap_false.
      p_message = |Authentication failed: { lv_status_code }|.
    ENDIF.

  CATCH cx_root INTO DATA(lx_error).
    p_success = abap_false.
    p_message = |Authentication exception: { lx_error->get_text( ) }|.
    IF lo_http_client IS BOUND.
      lo_http_client->close( ).
    ENDIF.
  ENDTRY.

ENDFORM.

*----------------------------------------------------------------------*
*       FORM validate_uuid
*----------------------------------------------------------------------*
*       Validates UUID format
*----------------------------------------------------------------------*
FORM validate_uuid USING p_uuid TYPE string
                  CHANGING p_error TYPE string.

  DATA: lv_pattern TYPE string.

  " UUID pattern: 8-4-4-4-12 hexadecimal characters
  lv_pattern = '^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$'.

  " Check UUID format
  FIND REGEX lv_pattern IN p_uuid.
  IF sy-subrc <> 0.
    p_error = 'Invalid UUID format'.
  ELSE.
    CLEAR p_error.
  ENDIF.

ENDFORM.

*----------------------------------------------------------------------*
*       FORM log_integration_event
*----------------------------------------------------------------------*
*       Logs integration events for monitoring and debugging
*----------------------------------------------------------------------*
FORM log_integration_event USING p_log_id TYPE string
                                 p_integration_type TYPE string
                                 p_operation TYPE string
                                 p_status TYPE string
                                 p_error_code TYPE string
                                 p_message TYPE string
                                 p_data TYPE string.

  DATA: wa_log TYPE zcommon_log.

  " Build log entry
  wa_log-log_id = p_log_id.
  wa_log-timestamp = |{ sy-datum }{ sy-uzeit }|.
  wa_log-integration_type = p_integration_type.
  wa_log-operation = p_operation.
  wa_log-status = p_status.
  wa_log-error_code = p_error_code.
  wa_log-message = p_message.
  wa_log-request_data = p_data.
  wa_log-created_by = sy-uname.
  wa_log-created_date = sy-datum.
  wa_log-created_time = sy-uzeit.

  " Insert log entry
  INSERT zcommon_log FROM wa_log.
  IF sy-subrc = 0.
    COMMIT WORK.
  ENDIF.

ENDFORM.

*----------------------------------------------------------------------*
*       FORM get_field_mapping
*----------------------------------------------------------------------*
*       Gets field mapping from configuration table
*----------------------------------------------------------------------*
FORM get_field_mapping USING p_source_system TYPE string
                             p_target_system TYPE string
                             p_source_field TYPE string
                      CHANGING p_target_field TYPE string
                              p_mapping_type TYPE string
                              p_lookup_table TYPE string.

  " Get mapping from configuration table
  SELECT SINGLE target_field, mapping_type, lookup_table
    FROM zcommon_mapping
    INTO (p_target_field, p_mapping_type, p_lookup_table)
    WHERE source_system = p_source_system
    AND target_system = p_target_system
    AND source_field = p_source_field.

  " If no mapping found, use direct mapping
  IF sy-subrc <> 0.
    p_target_field = p_source_field.
    p_mapping_type = 'DIRECT'.
    CLEAR p_lookup_table.
  ENDIF.

ENDFORM.

*----------------------------------------------------------------------*
*       FORM lookup_value
*----------------------------------------------------------------------*
*       Performs value lookup using lookup tables
*----------------------------------------------------------------------*
FORM lookup_value USING p_lookup_table TYPE string
                        p_source_value TYPE string
                 CHANGING p_target_value TYPE string.

  " Perform lookup based on table name
  CASE p_lookup_table.
    WHEN 'ZCOMMON_COMPANY'.
      SELECT SINGLE target_value FROM zcommon_company_map
        INTO p_target_value
        WHERE source_value = p_source_value.
        
    WHEN 'ZCOMMON_VENDOR'.
      SELECT SINGLE target_value FROM zcommon_vendor_map
        INTO p_target_value
        WHERE source_value = p_source_value.
        
    WHEN 'ZCOMMON_MATERIAL'.
      SELECT SINGLE target_value FROM zcommon_material_map
        INTO p_target_value
        WHERE source_value = p_source_value.
        
    WHEN 'ZCOMMON_UOM'.
      SELECT SINGLE target_value FROM zcommon_uom_map
        INTO p_target_value
        WHERE source_value = p_source_value.
        
    WHEN OTHERS.
      " No lookup table found, return original value
      p_target_value = p_source_value.
  ENDCASE.

  " If no mapping found, return original value
  IF p_target_value IS INITIAL.
    p_target_value = p_source_value.
  ENDIF.

ENDFORM.

*----------------------------------------------------------------------*
*       FORM convert_sap_date_to_iso
*----------------------------------------------------------------------*
*       Converts SAP date (YYYYMMDD) to ISO format (YYYY-MM-DD)
*----------------------------------------------------------------------*
FORM convert_sap_date_to_iso USING p_sap_date TYPE dats
                            CHANGING p_iso_date TYPE string.

  IF p_sap_date IS NOT INITIAL.
    p_iso_date = |{ p_sap_date+0(4) }-{ p_sap_date+4(2) }-{ p_sap_date+6(2) }|.
  ELSE.
    CLEAR p_iso_date.
  ENDIF.

ENDFORM.

*----------------------------------------------------------------------*
*       FORM convert_iso_date_to_sap
*----------------------------------------------------------------------*
*       Converts ISO date (YYYY-MM-DD) to SAP format (YYYYMMDD)
*----------------------------------------------------------------------*
FORM convert_iso_date_to_sap USING p_iso_date TYPE string
                            CHANGING p_sap_date TYPE dats.

  DATA: lv_year TYPE string,
        lv_month TYPE string,
        lv_day TYPE string.

  IF p_iso_date IS NOT INITIAL AND strlen( p_iso_date ) = 10.
    lv_year = p_iso_date+0(4).
    lv_month = p_iso_date+5(2).
    lv_day = p_iso_date+8(2).
    p_sap_date = |{ lv_year }{ lv_month }{ lv_day }|.
  ELSE.
    CLEAR p_sap_date.
  ENDIF.

ENDFORM.

*----------------------------------------------------------------------*
*       FORM format_number_for_json
*----------------------------------------------------------------------*
*       Formats SAP numbers for JSON output
*----------------------------------------------------------------------*
FORM format_number_for_json USING p_number TYPE p
                           CHANGING p_json_number TYPE string.

  " Convert number to string with proper decimal formatting
  p_json_number = |{ p_number }|.
  
  " Remove leading zeros and ensure proper decimal format
  CONDENSE p_json_number NO-GAPS.
  
  " Ensure at least one decimal place for prices
  IF p_json_number CN '.'.
    p_json_number = |{ p_json_number }.0|.
  ENDIF.

ENDFORM.

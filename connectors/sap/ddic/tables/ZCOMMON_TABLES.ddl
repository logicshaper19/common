*&---------------------------------------------------------------------*
*& Data Dictionary: Common Integration Tables
*& Description: Database tables for SAP-Common integration
*&---------------------------------------------------------------------*

*----------------------------------------------------------------------*
* Table: ZCOMMON_CONFIG
* Description: Configuration parameters for Common integration
*----------------------------------------------------------------------*
@EndUserText.label : 'Common Integration Configuration'
@AbapCatalog.enhancement.category : #NOT_EXTENSIBLE
@AbapCatalog.tableCategory : #TRANSPARENT
@AbapCatalog.deliveryClass : #C
@AbapCatalog.dataMaintenance : #ALLOWED
define table zcommon_config {
  key client      : mandt not null;
  key config_key  : char50 not null;
  config_value    : char255;
  description     : char100;
  config_type     : char20;
  is_secure       : char1;
  created_by      : syuname;
  created_date    : sydatum;
  created_time    : syuzeit;
  changed_by      : syuname;
  changed_date    : sydatum;
  changed_time    : syuzeit;
}

*----------------------------------------------------------------------*
* Table: ZCOMMON_LOG
* Description: Integration log for monitoring and debugging
*----------------------------------------------------------------------*
@EndUserText.label : 'Common Integration Log'
@AbapCatalog.enhancement.category : #NOT_EXTENSIBLE
@AbapCatalog.tableCategory : #TRANSPARENT
@AbapCatalog.deliveryClass : #A
@AbapCatalog.dataMaintenance : #ALLOWED
define table zcommon_log {
  key client           : mandt not null;
  key log_id          : char36 not null;
  timestamp           : char20;
  integration_type    : char20;
  operation           : char50;
  status              : char20;
  error_code          : char20;
  message             : char255;
  request_data        : string;
  response_data       : string;
  processing_time_ms  : int4;
  created_by          : syuname;
  created_date        : sydatum;
  created_time        : syuzeit;
}

*----------------------------------------------------------------------*
* Table: ZCOMMON_PO_MAPPING
* Description: Purchase order mapping between SAP and Common
*----------------------------------------------------------------------*
@EndUserText.label : 'PO Mapping SAP-Common'
@AbapCatalog.enhancement.category : #NOT_EXTENSIBLE
@AbapCatalog.tableCategory : #TRANSPARENT
@AbapCatalog.deliveryClass : #A
@AbapCatalog.dataMaintenance : #ALLOWED
define table zcommon_po_mapping {
  key client              : mandt not null;
  key common_po_id        : char36 not null;
  sap_po_number          : ebeln;
  buyer_company_id       : char36;
  seller_company_id      : char36;
  product_id             : char36;
  quantity               : quan13_3;
  unit_price             : curr11_2;
  unit                   : meins;
  delivery_date          : sydatum;
  delivery_location      : char50;
  po_status              : char20;
  erp_sync_status        : char20;
  last_sync_date         : sydatum;
  last_sync_time         : syuzeit;
  sync_error_message     : char255;
  created_date           : sydatum;
  created_time           : syuzeit;
  created_by             : syuname;
  changed_date           : sydatum;
  changed_time           : syuzeit;
  changed_by             : syuname;
  status                 : char10;
}

*----------------------------------------------------------------------*
* Table: ZCOMMON_AMENDMENT
* Description: Amendment tracking for purchase orders
*----------------------------------------------------------------------*
@EndUserText.label : 'Common Amendment Tracking'
@AbapCatalog.enhancement.category : #NOT_EXTENSIBLE
@AbapCatalog.tableCategory : #TRANSPARENT
@AbapCatalog.deliveryClass : #A
@AbapCatalog.dataMaintenance : #ALLOWED
define table zcommon_amendment {
  key client              : mandt not null;
  key amendment_id        : char36 not null;
  common_po_id           : char36;
  sap_po_number          : ebeln;
  amendment_type         : char20;
  original_quantity      : quan13_3;
  proposed_quantity      : quan13_3;
  original_unit          : meins;
  proposed_unit          : meins;
  original_price         : curr11_2;
  proposed_price         : curr11_2;
  amendment_reason       : char255;
  amendment_status       : char20;
  business_impact        : char255;
  priority               : char10;
  requested_by           : syuname;
  requested_date         : sydatum;
  requested_time         : syuzeit;
  approved_by            : syuname;
  approved_date          : sydatum;
  approved_time          : syuzeit;
  rejection_reason       : char255;
  source_system          : char10;
  target_system          : char10;
  created_date           : sydatum;
  created_time           : syuzeit;
  created_by             : syuname;
  changed_date           : sydatum;
  changed_time           : syuzeit;
  changed_by             : syuname;
}

*----------------------------------------------------------------------*
* Table: ZCOMMON_MAPPING
* Description: Field mapping configuration
*----------------------------------------------------------------------*
@EndUserText.label : 'Common Field Mapping'
@AbapCatalog.enhancement.category : #NOT_EXTENSIBLE
@AbapCatalog.tableCategory : #TRANSPARENT
@AbapCatalog.deliveryClass : #C
@AbapCatalog.dataMaintenance : #ALLOWED
define table zcommon_mapping {
  key client          : mandt not null;
  key source_system   : char10 not null;
  key target_system   : char10 not null;
  key source_field    : char50 not null;
  target_field        : char50;
  mapping_type        : char20;
  lookup_table        : char30;
  transformation_rule : char100;
  default_value       : char50;
  is_required         : char1;
  validation_rule     : char100;
  description         : char100;
  created_by          : syuname;
  created_date        : sydatum;
  changed_by          : syuname;
  changed_date        : sydatum;
  is_active           : char1;
}

*----------------------------------------------------------------------*
* Table: ZCOMMON_COMPANY_MAP
* Description: Company ID mapping between systems
*----------------------------------------------------------------------*
@EndUserText.label : 'Company ID Mapping'
@AbapCatalog.enhancement.category : #NOT_EXTENSIBLE
@AbapCatalog.tableCategory : #TRANSPARENT
@AbapCatalog.deliveryClass : #C
@AbapCatalog.dataMaintenance : #ALLOWED
define table zcommon_company_map {
  key client        : mandt not null;
  key source_value  : char20 not null;
  target_value      : char36;
  company_name      : char100;
  company_type      : char20;
  country           : char3;
  region            : char50;
  is_active         : char1;
  created_by        : syuname;
  created_date      : sydatum;
  changed_by        : syuname;
  changed_date      : sydatum;
}

*----------------------------------------------------------------------*
* Table: ZCOMMON_VENDOR_MAP
* Description: Vendor ID mapping between systems
*----------------------------------------------------------------------*
@EndUserText.label : 'Vendor ID Mapping'
@AbapCatalog.enhancement.category : #NOT_EXTENSIBLE
@AbapCatalog.tableCategory : #TRANSPARENT
@AbapCatalog.deliveryClass : #C
@AbapCatalog.dataMaintenance : #ALLOWED
define table zcommon_vendor_map {
  key client        : mandt not null;
  key source_value  : char20 not null;
  target_value      : char36;
  vendor_name       : char100;
  vendor_type       : char20;
  country           : char3;
  region            : char50;
  certification     : char100;
  is_active         : char1;
  created_by        : syuname;
  created_date      : sydatum;
  changed_by        : syuname;
  changed_date      : sydatum;
}

*----------------------------------------------------------------------*
* Table: ZCOMMON_MATERIAL_MAP
* Description: Material/Product ID mapping between systems
*----------------------------------------------------------------------*
@EndUserText.label : 'Material ID Mapping'
@AbapCatalog.enhancement.category : #NOT_EXTENSIBLE
@AbapCatalog.tableCategory : #TRANSPARENT
@AbapCatalog.deliveryClass : #C
@AbapCatalog.dataMaintenance : #ALLOWED
define table zcommon_material_map {
  key client        : mandt not null;
  key source_value  : char18 not null;
  target_value      : char36;
  material_desc     : char40;
  material_type     : char4;
  base_unit         : meins;
  material_group    : char9;
  product_category  : char50;
  sustainability    : char100;
  certifications    : char255;
  is_active         : char1;
  created_by        : syuname;
  created_date      : sydatum;
  changed_by        : syuname;
  changed_date      : sydatum;
}

*----------------------------------------------------------------------*
* Table: ZCOMMON_UOM_MAP
* Description: Unit of measure mapping between systems
*----------------------------------------------------------------------*
@EndUserText.label : 'Unit of Measure Mapping'
@AbapCatalog.enhancement.category : #NOT_EXTENSIBLE
@AbapCatalog.tableCategory : #TRANSPARENT
@AbapCatalog.deliveryClass : #C
@AbapCatalog.dataMaintenance : #ALLOWED
define table zcommon_uom_map {
  key client        : mandt not null;
  key source_value  : meins not null;
  target_value      : char10;
  uom_description   : char30;
  conversion_factor : dec15_6;
  base_unit         : meins;
  dimension         : char6;
  is_active         : char1;
  created_by        : syuname;
  created_date      : sydatum;
  changed_by        : syuname;
  changed_date      : sydatum;
}

*----------------------------------------------------------------------*
* Table: ZCOMMON_SYNC_QUEUE
* Description: Synchronization queue for batch processing
*----------------------------------------------------------------------*
@EndUserText.label : 'Common Sync Queue'
@AbapCatalog.enhancement.category : #NOT_EXTENSIBLE
@AbapCatalog.tableCategory : #TRANSPARENT
@AbapCatalog.deliveryClass : #A
@AbapCatalog.dataMaintenance : #ALLOWED
define table zcommon_sync_queue {
  key client          : mandt not null;
  key queue_id        : char36 not null;
  object_type         : char20;
  object_id           : char36;
  operation           : char20;
  sync_direction      : char20;
  priority            : int1;
  payload             : string;
  status              : char20;
  retry_count         : int2;
  max_retries         : int2;
  error_message       : char255;
  scheduled_time      : timestampl;
  processed_time      : timestampl;
  created_by          : syuname;
  created_date        : sydatum;
  created_time        : syuzeit;
  changed_by          : syuname;
  changed_date        : sydatum;
  changed_time        : syuzeit;
}

*----------------------------------------------------------------------*
* Table: ZCOMMON_PERFORMANCE
* Description: Performance metrics and monitoring
*----------------------------------------------------------------------*
@EndUserText.label : 'Common Performance Metrics'
@AbapCatalog.enhancement.category : #NOT_EXTENSIBLE
@AbapCatalog.tableCategory : #TRANSPARENT
@AbapCatalog.deliveryClass : #A
@AbapCatalog.dataMaintenance : #ALLOWED
define table zcommon_performance {
  key client              : mandt not null;
  key metric_id           : char36 not null;
  metric_date             : sydatum;
  metric_hour             : int2;
  integration_type        : char20;
  operation               : char50;
  total_requests          : int4;
  successful_requests     : int4;
  failed_requests         : int4;
  avg_response_time_ms    : int4;
  min_response_time_ms    : int4;
  max_response_time_ms    : int4;
  total_data_volume_kb    : int4;
  error_rate_percent      : dec5_2;
  throughput_per_minute   : dec10_2;
  created_date            : sydatum;
  created_time            : syuzeit;
}

*----------------------------------------------------------------------*
* Indexes for Performance Optimization
*----------------------------------------------------------------------*

* Index for ZCOMMON_LOG table
@AbapCatalog.index : [
  {
    name: 'ZCOMMON_LOG~001',
    unique: false,
    order: #ASC,
    fields: [ 'created_date', 'integration_type', 'status' ]
  }
]

* Index for ZCOMMON_PO_MAPPING table
@AbapCatalog.index : [
  {
    name: 'ZCOMMON_PO_MAPPING~001',
    unique: false,
    order: #ASC,
    fields: [ 'sap_po_number' ]
  },
  {
    name: 'ZCOMMON_PO_MAPPING~002',
    unique: false,
    order: #ASC,
    fields: [ 'erp_sync_status', 'last_sync_date' ]
  }
]

* Index for ZCOMMON_SYNC_QUEUE table
@AbapCatalog.index : [
  {
    name: 'ZCOMMON_SYNC_QUEUE~001',
    unique: false,
    order: #ASC,
    fields: [ 'status', 'priority', 'scheduled_time' ]
  }
]

*----------------------------------------------------------------------*
* Table Maintenance Generators
*----------------------------------------------------------------------*

* SM30 maintenance for configuration tables
* - ZCOMMON_CONFIG: Allow maintenance of configuration parameters
* - ZCOMMON_MAPPING: Allow maintenance of field mappings
* - ZCOMMON_COMPANY_MAP: Allow maintenance of company mappings
* - ZCOMMON_VENDOR_MAP: Allow maintenance of vendor mappings
* - ZCOMMON_MATERIAL_MAP: Allow maintenance of material mappings
* - ZCOMMON_UOM_MAP: Allow maintenance of unit mappings

*----------------------------------------------------------------------*
* Authorization Objects
*----------------------------------------------------------------------*

* Authorization object: Z_COMMON_INT
* - ACTVT: Activity (01=Create, 02=Change, 03=Display, 06=Delete)
* - INTTYPE: Integration Type (RFC, IDOC, ODATA, BATCH)
* - COMPANY: Company Code restriction

*----------------------------------------------------------------------*
* Change Documents
*----------------------------------------------------------------------*

* Change document object: ZCOMMON_PO
* - Track changes to purchase order mappings
* - Track amendment proposals and approvals
* - Audit trail for compliance requirements

*----------------------------------------------------------------------*
* Number Ranges
*----------------------------------------------------------------------*

* Number range object: ZCOMMON_LOG
* - External number assignment for log IDs
* - Number range interval: 0000000001 to 9999999999

* Number range object: ZCOMMON_QUEUE
* - External number assignment for queue IDs
* - Number range interval: 0000000001 to 9999999999

%dw 2.0
output application/json

/**
 * DataWeave transformation: Common API to SAP Purchase Order format
 * 
 * This transformation maps Common API purchase order data back to SAP
 * format for ERP synchronization. It handles reverse field mapping,
 * data type conversions, and SAP-specific formatting requirements.
 * 
 * Input: Common API purchase order data (JSON)
 * Output: SAP purchase order format (JSON/XML)
 */

---
{
    // SAP Purchase Order Header
    EBELN: payload.po_number,          // Purchase Order Number
    BUKRS: payload.buyer_company_id,   // Company Code
    LIFNR: payload.seller_company_id,  // Vendor Number
    BEDAT: payload.created_at as Date as String {format: "yyyyMMdd"}, // Document Date
    
    // SAP Purchase Order Items
    ITEMS: [{
        EBELP: "00010",                // Item Number (default first item)
        MATNR: payload.product_id,     // Material Number
        MENGE: payload.quantity as String, // Quantity
        MEINS: payload.unit,           // Unit of Measure
        NETPR: payload.unit_price as String, // Net Price
        WERKS: payload.delivery_location, // Plant
        EINDT: payload.delivery_date as Date {format: "yyyy-MM-dd"} as String {format: "yyyyMMdd"}, // Delivery Date
        TXZOL: payload.notes default "", // Short Text
        
        // Amendment information (if applicable)
        AMENDMENT_STATUS: if (payload.amendment_status != null and payload.amendment_status != "none")
            payload.amendment_status
        else null,
        
        PROPOSED_QUANTITY: if (payload.proposed_quantity != null)
            payload.proposed_quantity as String
        else null,
        
        AMENDMENT_REASON: payload.amendment_reason default null,
        
        // Confirmation information (if available)
        CONFIRMED_QUANTITY: if (payload.confirmed_quantity != null)
            payload.confirmed_quantity as String
        else null,
        
        CONFIRMED_PRICE: if (payload.confirmed_unit_price != null)
            payload.confirmed_unit_price as String
        else null,
        
        CONFIRMED_DATE: if (payload.confirmed_delivery_date != null)
            payload.confirmed_delivery_date as Date {format: "yyyy-MM-dd"} as String {format: "yyyyMMdd"}
        else null,
        
        // Status mapping
        STATUS: payload.status match {
            case "draft" -> "00"      // Created
            case "pending" -> "01"    // Released
            case "confirmed" -> "02"  // Confirmed
            case "shipped" -> "03"    // Goods Receipt
            case "received" -> "04"   // Invoice Receipt
            case "cancelled" -> "05"  // Cancelled
            else -> "00"
        },
        
        // Composition data (for transparency)
        COMPOSITION: if (payload.composition != null)
            payload.composition mapObject ((value, key) -> {
                (key): value as String
            })
        else null,
        
        // Input materials (for traceability)
        INPUT_MATERIALS: if (payload.input_materials != null)
            payload.input_materials map ((item) -> {
                MATNR: item.material_id,
                MENGE: item.quantity as String,
                MEINS: item.unit,
                CHARG: item.batch_number default ""
            })
        else null,
        
        // Origin data (for raw materials)
        ORIGIN_DATA: if (payload.origin_data != null) {
            LATITUDE: payload.origin_data.coordinates.latitude as String,
            LONGITUDE: payload.origin_data.coordinates.longitude as String,
            CERTIFICATIONS: payload.origin_data.certifications joinBy ",",
            HARVEST_DATE: if (payload.origin_data.harvest_date != null)
                payload.origin_data.harvest_date as Date {format: "yyyy-MM-dd"} as String {format: "yyyyMMdd"}
            else null
        } else null
    }],
    
    // ERP Sync metadata
    SYNC_STATUS: payload.erp_sync_status default "pending",
    SYNC_TIMESTAMP: now() as String {format: "yyyy-MM-dd'T'HH:mm:ss'Z'"},
    COMMON_PO_ID: payload.id,
    
    // Amendment workflow metadata
    AMENDMENT_COUNT: payload.amendment_count default 0,
    LAST_AMENDED: if (payload.last_amended_at != null)
        payload.last_amended_at as Date as String {format: "yyyyMMdd"}
    else null
}

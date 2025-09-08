%dw 2.0
output application/json

/**
 * DataWeave transformation: SAP Purchase Order to Common API format
 * 
 * This transformation maps SAP purchase order data to the Common API
 * purchase order creation format. It handles field mapping, data type
 * conversions, and default value assignments.
 * 
 * Input: SAP purchase order data (JSON/XML)
 * Output: Common API purchase order creation request (JSON)
 */

---
{
    // Required fields
    buyer_company_id: vars.buyerCompanyId default payload.BUKRS,
    seller_company_id: payload.LIFNR,  // SAP Vendor Number
    product_id: payload.MATNR,         // SAP Material Number
    quantity: payload.MENGE as Number, // SAP Quantity
    unit_price: payload.NETPR as Number, // SAP Net Price
    unit: payload.MEINS,               // SAP Unit of Measure
    delivery_date: payload.EINDT as Date {format: "yyyyMMdd"} as String {format: "yyyy-MM-dd"}, // SAP Delivery Date
    delivery_location: payload.WERKS,  // SAP Plant
    
    // Optional fields
    notes: payload.TXZOL default null,  // SAP Short Text
    
    // Composition mapping (if available)
    composition: if (payload.COMPOSITION != null) 
        payload.COMPOSITION mapObject ((value, key) -> {
            (key): value as Number
        })
    else null,
    
    // Input materials mapping (for processed products)
    input_materials: if (payload.INPUT_MATERIALS != null)
        payload.INPUT_MATERIALS map ((item) -> {
            material_id: item.MATNR,
            quantity: item.MENGE as Number,
            unit: item.MEINS,
            batch_number: item.CHARG default null
        })
    else null,
    
    // Origin data mapping (for raw materials)
    origin_data: if (payload.ORIGIN_DATA != null) {
        coordinates: {
            latitude: payload.ORIGIN_DATA.LATITUDE as Number,
            longitude: payload.ORIGIN_DATA.LONGITUDE as Number
        },
        certifications: payload.ORIGIN_DATA.CERTIFICATIONS default [],
        harvest_date: payload.ORIGIN_DATA.HARVEST_DATE as Date {format: "yyyyMMdd"} as String {format: "yyyy-MM-dd"}
    } else null
}

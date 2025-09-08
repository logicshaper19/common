package com.common.connectors.api;

import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * Request model for updating an existing purchase order
 * 
 * Contains optional fields that can be updated on an existing
 * purchase order in the Common platform.
 */
public class PurchaseOrderUpdateRequest {
    
    @JsonProperty("quantity")
    private String quantity;
    
    @JsonProperty("unit_price")
    private String unitPrice;
    
    @JsonProperty("delivery_date")
    private String deliveryDate;
    
    @JsonProperty("delivery_location")
    private String deliveryLocation;
    
    @JsonProperty("notes")
    private String notes;
    
    // Default constructor
    public PurchaseOrderUpdateRequest() {}
    
    // Getters and setters
    public String getQuantity() {
        return quantity;
    }
    
    public void setQuantity(String quantity) {
        this.quantity = quantity;
    }
    
    public String getUnitPrice() {
        return unitPrice;
    }
    
    public void setUnitPrice(String unitPrice) {
        this.unitPrice = unitPrice;
    }
    
    public String getDeliveryDate() {
        return deliveryDate;
    }
    
    public void setDeliveryDate(String deliveryDate) {
        this.deliveryDate = deliveryDate;
    }
    
    public String getDeliveryLocation() {
        return deliveryLocation;
    }
    
    public void setDeliveryLocation(String deliveryLocation) {
        this.deliveryLocation = deliveryLocation;
    }
    
    public String getNotes() {
        return notes;
    }
    
    public void setNotes(String notes) {
        this.notes = notes;
    }
}

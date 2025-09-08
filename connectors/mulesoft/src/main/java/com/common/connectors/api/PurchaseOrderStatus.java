package com.common.connectors.api;

import com.fasterxml.jackson.annotation.JsonValue;

/**
 * Purchase Order Status enumeration
 * 
 * Represents the various states a purchase order can be in throughout
 * its lifecycle in the Common platform.
 */
public enum PurchaseOrderStatus {
    
    /**
     * Purchase order is in draft state
     */
    DRAFT("draft"),
    
    /**
     * Purchase order is pending seller confirmation
     */
    PENDING("pending"),
    
    /**
     * Purchase order has been confirmed by seller
     */
    CONFIRMED("confirmed"),
    
    /**
     * Purchase order has been shipped
     */
    SHIPPED("shipped"),
    
    /**
     * Purchase order has been received
     */
    RECEIVED("received"),
    
    /**
     * Purchase order has been cancelled
     */
    CANCELLED("cancelled"),
    
    /**
     * Purchase order is on hold
     */
    ON_HOLD("on_hold");
    
    private final String value;
    
    PurchaseOrderStatus(String value) {
        this.value = value;
    }
    
    @JsonValue
    public String getValue() {
        return value;
    }
    
    /**
     * Create enum from string value
     */
    public static PurchaseOrderStatus fromValue(String value) {
        for (PurchaseOrderStatus status : PurchaseOrderStatus.values()) {
            if (status.value.equals(value)) {
                return status;
            }
        }
        throw new IllegalArgumentException("Unknown PurchaseOrderStatus: " + value);
    }
    
    @Override
    public String toString() {
        return value;
    }
}

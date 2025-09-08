package com.common.connectors.api;

import com.fasterxml.jackson.annotation.JsonValue;

/**
 * Amendment Status enumeration
 * 
 * Represents the various states an amendment can be in throughout
 * the amendment workflow in the Common platform.
 */
public enum AmendmentStatus {
    
    /**
     * No amendment has been proposed
     */
    NONE("none"),
    
    /**
     * Amendment has been proposed and is pending approval
     */
    PROPOSED("proposed"),
    
    /**
     * Amendment has been approved by buyer
     */
    APPROVED("approved"),
    
    /**
     * Amendment has been rejected by buyer
     */
    REJECTED("rejected");
    
    private final String value;
    
    AmendmentStatus(String value) {
        this.value = value;
    }
    
    @JsonValue
    public String getValue() {
        return value;
    }
    
    /**
     * Create enum from string value
     */
    public static AmendmentStatus fromValue(String value) {
        for (AmendmentStatus status : AmendmentStatus.values()) {
            if (status.value.equals(value)) {
                return status;
            }
        }
        throw new IllegalArgumentException("Unknown AmendmentStatus: " + value);
    }
    
    @Override
    public String toString() {
        return value;
    }
}

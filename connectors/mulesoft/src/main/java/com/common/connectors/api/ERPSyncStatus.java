package com.common.connectors.api;

import com.fasterxml.jackson.annotation.JsonValue;

/**
 * ERP Sync Status enumeration
 * 
 * Represents the various states of ERP synchronization for purchase orders
 * in the Common platform's Phase 2 enterprise integration.
 */
public enum ERPSyncStatus {
    
    /**
     * No ERP sync required
     */
    NOT_REQUIRED("not_required"),
    
    /**
     * ERP sync is pending
     */
    PENDING("pending"),
    
    /**
     * ERP sync is in progress
     */
    IN_PROGRESS("in_progress"),
    
    /**
     * ERP sync completed successfully
     */
    SYNCED("synced"),
    
    /**
     * ERP sync failed
     */
    FAILED("failed"),
    
    /**
     * ERP sync was skipped
     */
    SKIPPED("skipped");
    
    private final String value;
    
    ERPSyncStatus(String value) {
        this.value = value;
    }
    
    @JsonValue
    public String getValue() {
        return value;
    }
    
    /**
     * Create enum from string value
     */
    public static ERPSyncStatus fromValue(String value) {
        for (ERPSyncStatus status : ERPSyncStatus.values()) {
            if (status.value.equals(value)) {
                return status;
            }
        }
        throw new IllegalArgumentException("Unknown ERPSyncStatus: " + value);
    }
    
    @Override
    public String toString() {
        return value;
    }
}

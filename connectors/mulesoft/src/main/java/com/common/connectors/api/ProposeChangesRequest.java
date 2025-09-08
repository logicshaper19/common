package com.common.connectors.api;

import com.fasterxml.jackson.annotation.JsonProperty;

import java.math.BigDecimal;

/**
 * Request model for proposing changes to a purchase order
 * 
 * Used in the amendment workflow when sellers want to propose
 * modifications to an existing purchase order.
 */
public class ProposeChangesRequest {
    
    @JsonProperty("proposed_quantity")
    private BigDecimal proposedQuantity;
    
    @JsonProperty("proposed_quantity_unit")
    private String proposedQuantityUnit;
    
    @JsonProperty("amendment_reason")
    private String amendmentReason;
    
    // Default constructor
    public ProposeChangesRequest() {}
    
    // Constructor with all fields
    public ProposeChangesRequest(BigDecimal proposedQuantity, String proposedQuantityUnit, String amendmentReason) {
        this.proposedQuantity = proposedQuantity;
        this.proposedQuantityUnit = proposedQuantityUnit;
        this.amendmentReason = amendmentReason;
    }
    
    // Getters and setters
    public BigDecimal getProposedQuantity() {
        return proposedQuantity;
    }
    
    public void setProposedQuantity(BigDecimal proposedQuantity) {
        this.proposedQuantity = proposedQuantity;
    }
    
    public String getProposedQuantityUnit() {
        return proposedQuantityUnit;
    }
    
    public void setProposedQuantityUnit(String proposedQuantityUnit) {
        this.proposedQuantityUnit = proposedQuantityUnit;
    }
    
    public String getAmendmentReason() {
        return amendmentReason;
    }
    
    public void setAmendmentReason(String amendmentReason) {
        this.amendmentReason = amendmentReason;
    }
    
    @Override
    public String toString() {
        return "ProposeChangesRequest{" +
                "proposedQuantity=" + proposedQuantity +
                ", proposedQuantityUnit='" + proposedQuantityUnit + '\'' +
                ", amendmentReason='" + amendmentReason + '\'' +
                '}';
    }
}

package com.common.connectors.api;

import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * Request model for approving or rejecting proposed changes to a purchase order
 * 
 * Used in the amendment workflow when buyers want to approve or reject
 * amendments proposed by sellers.
 */
public class ApproveChangesRequest {
    
    @JsonProperty("approve")
    private Boolean approve;
    
    @JsonProperty("buyer_notes")
    private String buyerNotes;
    
    // Default constructor
    public ApproveChangesRequest() {}
    
    // Constructor with all fields
    public ApproveChangesRequest(Boolean approve, String buyerNotes) {
        this.approve = approve;
        this.buyerNotes = buyerNotes;
    }
    
    // Convenience constructor for approval
    public ApproveChangesRequest(Boolean approve) {
        this.approve = approve;
    }
    
    // Getters and setters
    public Boolean getApprove() {
        return approve;
    }
    
    public void setApprove(Boolean approve) {
        this.approve = approve;
    }
    
    public String getBuyerNotes() {
        return buyerNotes;
    }
    
    public void setBuyerNotes(String buyerNotes) {
        this.buyerNotes = buyerNotes;
    }
    
    @Override
    public String toString() {
        return "ApproveChangesRequest{" +
                "approve=" + approve +
                ", buyerNotes='" + buyerNotes + '\'' +
                '}';
    }
}

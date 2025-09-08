package com.common.connectors.api;

import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * Response model for amendment operations
 * 
 * Returned by the Common API when proposing or approving amendments
 * to provide status and result information.
 */
public class AmendmentResponse {
    
    @JsonProperty("success")
    private Boolean success;
    
    @JsonProperty("message")
    private String message;
    
    @JsonProperty("amendment_status")
    private AmendmentStatus amendmentStatus;
    
    @JsonProperty("purchase_order_id")
    private String purchaseOrderId;
    
    // Default constructor
    public AmendmentResponse() {}
    
    // Constructor with all fields
    public AmendmentResponse(Boolean success, String message, AmendmentStatus amendmentStatus, String purchaseOrderId) {
        this.success = success;
        this.message = message;
        this.amendmentStatus = amendmentStatus;
        this.purchaseOrderId = purchaseOrderId;
    }
    
    // Getters and setters
    public Boolean getSuccess() {
        return success;
    }
    
    public void setSuccess(Boolean success) {
        this.success = success;
    }
    
    public String getMessage() {
        return message;
    }
    
    public void setMessage(String message) {
        this.message = message;
    }
    
    public AmendmentStatus getAmendmentStatus() {
        return amendmentStatus;
    }
    
    public void setAmendmentStatus(AmendmentStatus amendmentStatus) {
        this.amendmentStatus = amendmentStatus;
    }
    
    public String getPurchaseOrderId() {
        return purchaseOrderId;
    }
    
    public void setPurchaseOrderId(String purchaseOrderId) {
        this.purchaseOrderId = purchaseOrderId;
    }
    
    @Override
    public String toString() {
        return "AmendmentResponse{" +
                "success=" + success +
                ", message='" + message + '\'' +
                ", amendmentStatus=" + amendmentStatus +
                ", purchaseOrderId='" + purchaseOrderId + '\'' +
                '}';
    }
}

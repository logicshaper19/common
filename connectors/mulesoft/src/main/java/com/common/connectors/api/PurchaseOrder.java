package com.common.connectors.api;

import com.fasterxml.jackson.annotation.JsonFormat;
import com.fasterxml.jackson.annotation.JsonProperty;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.Map;
import java.util.List;

/**
 * Purchase Order data model
 * 
 * Represents a purchase order in the Common platform with all relevant
 * fields for supply chain transparency and amendment tracking.
 */
public class PurchaseOrder {
    
    @JsonProperty("id")
    private String id;
    
    @JsonProperty("po_number")
    private String poNumber;
    
    @JsonProperty("buyer_company_id")
    private String buyerCompanyId;
    
    @JsonProperty("seller_company_id")
    private String sellerCompanyId;
    
    @JsonProperty("product_id")
    private String productId;
    
    @JsonProperty("quantity")
    private BigDecimal quantity;
    
    @JsonProperty("unit_price")
    private BigDecimal unitPrice;
    
    @JsonProperty("total_amount")
    private BigDecimal totalAmount;
    
    @JsonProperty("unit")
    private String unit;
    
    @JsonProperty("delivery_date")
    @JsonFormat(pattern = "yyyy-MM-dd")
    private LocalDate deliveryDate;
    
    @JsonProperty("delivery_location")
    private String deliveryLocation;
    
    @JsonProperty("status")
    private PurchaseOrderStatus status;
    
    @JsonProperty("composition")
    private Map<String, Double> composition;
    
    @JsonProperty("input_materials")
    private List<Map<String, Object>> inputMaterials;
    
    @JsonProperty("origin_data")
    private Map<String, Object> originData;
    
    @JsonProperty("notes")
    private String notes;
    
    // Seller confirmation fields
    @JsonProperty("confirmed_quantity")
    private BigDecimal confirmedQuantity;
    
    @JsonProperty("confirmed_unit_price")
    private BigDecimal confirmedUnitPrice;
    
    @JsonProperty("confirmed_delivery_date")
    @JsonFormat(pattern = "yyyy-MM-dd")
    private LocalDate confirmedDeliveryDate;
    
    @JsonProperty("confirmed_delivery_location")
    private String confirmedDeliveryLocation;
    
    @JsonProperty("seller_notes")
    private String sellerNotes;
    
    @JsonProperty("seller_confirmed_at")
    @JsonFormat(pattern = "yyyy-MM-dd'T'HH:mm:ss.SSSSSS'Z'")
    private LocalDateTime sellerConfirmedAt;
    
    // Amendment fields
    @JsonProperty("amendment_status")
    private AmendmentStatus amendmentStatus;
    
    @JsonProperty("proposed_quantity")
    private BigDecimal proposedQuantity;
    
    @JsonProperty("proposed_quantity_unit")
    private String proposedQuantityUnit;
    
    @JsonProperty("amendment_reason")
    private String amendmentReason;
    
    @JsonProperty("amendment_count")
    private Integer amendmentCount;
    
    @JsonProperty("last_amended_at")
    @JsonFormat(pattern = "yyyy-MM-dd'T'HH:mm:ss.SSSSSS'Z'")
    private LocalDateTime lastAmendedAt;
    
    // ERP sync fields
    @JsonProperty("erp_sync_status")
    private ERPSyncStatus erpSyncStatus;
    
    @JsonProperty("erp_sync_attempts")
    private Integer erpSyncAttempts;
    
    @JsonProperty("last_erp_sync_at")
    @JsonFormat(pattern = "yyyy-MM-dd'T'HH:mm:ss.SSSSSS'Z'")
    private LocalDateTime lastErpSyncAt;
    
    @JsonProperty("erp_sync_error")
    private String erpSyncError;
    
    // Audit fields
    @JsonProperty("created_at")
    @JsonFormat(pattern = "yyyy-MM-dd'T'HH:mm:ss.SSSSSS'Z'")
    private LocalDateTime createdAt;
    
    @JsonProperty("updated_at")
    @JsonFormat(pattern = "yyyy-MM-dd'T'HH:mm:ss.SSSSSS'Z'")
    private LocalDateTime updatedAt;
    
    // Default constructor
    public PurchaseOrder() {}
    
    // Getters and setters
    public String getId() { return id; }
    public void setId(String id) { this.id = id; }
    
    public String getPoNumber() { return poNumber; }
    public void setPoNumber(String poNumber) { this.poNumber = poNumber; }
    
    public String getBuyerCompanyId() { return buyerCompanyId; }
    public void setBuyerCompanyId(String buyerCompanyId) { this.buyerCompanyId = buyerCompanyId; }
    
    public String getSellerCompanyId() { return sellerCompanyId; }
    public void setSellerCompanyId(String sellerCompanyId) { this.sellerCompanyId = sellerCompanyId; }
    
    public String getProductId() { return productId; }
    public void setProductId(String productId) { this.productId = productId; }
    
    public BigDecimal getQuantity() { return quantity; }
    public void setQuantity(BigDecimal quantity) { this.quantity = quantity; }
    
    public BigDecimal getUnitPrice() { return unitPrice; }
    public void setUnitPrice(BigDecimal unitPrice) { this.unitPrice = unitPrice; }
    
    public BigDecimal getTotalAmount() { return totalAmount; }
    public void setTotalAmount(BigDecimal totalAmount) { this.totalAmount = totalAmount; }
    
    public String getUnit() { return unit; }
    public void setUnit(String unit) { this.unit = unit; }
    
    public LocalDate getDeliveryDate() { return deliveryDate; }
    public void setDeliveryDate(LocalDate deliveryDate) { this.deliveryDate = deliveryDate; }
    
    public String getDeliveryLocation() { return deliveryLocation; }
    public void setDeliveryLocation(String deliveryLocation) { this.deliveryLocation = deliveryLocation; }
    
    public PurchaseOrderStatus getStatus() { return status; }
    public void setStatus(PurchaseOrderStatus status) { this.status = status; }
    
    public Map<String, Double> getComposition() { return composition; }
    public void setComposition(Map<String, Double> composition) { this.composition = composition; }
    
    public List<Map<String, Object>> getInputMaterials() { return inputMaterials; }
    public void setInputMaterials(List<Map<String, Object>> inputMaterials) { this.inputMaterials = inputMaterials; }
    
    public Map<String, Object> getOriginData() { return originData; }
    public void setOriginData(Map<String, Object> originData) { this.originData = originData; }
    
    public String getNotes() { return notes; }
    public void setNotes(String notes) { this.notes = notes; }
    
    public BigDecimal getConfirmedQuantity() { return confirmedQuantity; }
    public void setConfirmedQuantity(BigDecimal confirmedQuantity) { this.confirmedQuantity = confirmedQuantity; }
    
    public BigDecimal getConfirmedUnitPrice() { return confirmedUnitPrice; }
    public void setConfirmedUnitPrice(BigDecimal confirmedUnitPrice) { this.confirmedUnitPrice = confirmedUnitPrice; }
    
    public LocalDate getConfirmedDeliveryDate() { return confirmedDeliveryDate; }
    public void setConfirmedDeliveryDate(LocalDate confirmedDeliveryDate) { this.confirmedDeliveryDate = confirmedDeliveryDate; }
    
    public String getConfirmedDeliveryLocation() { return confirmedDeliveryLocation; }
    public void setConfirmedDeliveryLocation(String confirmedDeliveryLocation) { this.confirmedDeliveryLocation = confirmedDeliveryLocation; }
    
    public String getSellerNotes() { return sellerNotes; }
    public void setSellerNotes(String sellerNotes) { this.sellerNotes = sellerNotes; }
    
    public LocalDateTime getSellerConfirmedAt() { return sellerConfirmedAt; }
    public void setSellerConfirmedAt(LocalDateTime sellerConfirmedAt) { this.sellerConfirmedAt = sellerConfirmedAt; }
    
    public AmendmentStatus getAmendmentStatus() { return amendmentStatus; }
    public void setAmendmentStatus(AmendmentStatus amendmentStatus) { this.amendmentStatus = amendmentStatus; }
    
    public BigDecimal getProposedQuantity() { return proposedQuantity; }
    public void setProposedQuantity(BigDecimal proposedQuantity) { this.proposedQuantity = proposedQuantity; }
    
    public String getProposedQuantityUnit() { return proposedQuantityUnit; }
    public void setProposedQuantityUnit(String proposedQuantityUnit) { this.proposedQuantityUnit = proposedQuantityUnit; }
    
    public String getAmendmentReason() { return amendmentReason; }
    public void setAmendmentReason(String amendmentReason) { this.amendmentReason = amendmentReason; }
    
    public Integer getAmendmentCount() { return amendmentCount; }
    public void setAmendmentCount(Integer amendmentCount) { this.amendmentCount = amendmentCount; }
    
    public LocalDateTime getLastAmendedAt() { return lastAmendedAt; }
    public void setLastAmendedAt(LocalDateTime lastAmendedAt) { this.lastAmendedAt = lastAmendedAt; }
    
    public ERPSyncStatus getErpSyncStatus() { return erpSyncStatus; }
    public void setErpSyncStatus(ERPSyncStatus erpSyncStatus) { this.erpSyncStatus = erpSyncStatus; }
    
    public Integer getErpSyncAttempts() { return erpSyncAttempts; }
    public void setErpSyncAttempts(Integer erpSyncAttempts) { this.erpSyncAttempts = erpSyncAttempts; }
    
    public LocalDateTime getLastErpSyncAt() { return lastErpSyncAt; }
    public void setLastErpSyncAt(LocalDateTime lastErpSyncAt) { this.lastErpSyncAt = lastErpSyncAt; }
    
    public String getErpSyncError() { return erpSyncError; }
    public void setErpSyncError(String erpSyncError) { this.erpSyncError = erpSyncError; }
    
    public LocalDateTime getCreatedAt() { return createdAt; }
    public void setCreatedAt(LocalDateTime createdAt) { this.createdAt = createdAt; }
    
    public LocalDateTime getUpdatedAt() { return updatedAt; }
    public void setUpdatedAt(LocalDateTime updatedAt) { this.updatedAt = updatedAt; }
}

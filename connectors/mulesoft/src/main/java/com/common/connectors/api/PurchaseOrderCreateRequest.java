package com.common.connectors.api;

import com.fasterxml.jackson.annotation.JsonProperty;

import java.util.List;
import java.util.Map;

/**
 * Request model for creating a new purchase order
 * 
 * Contains all the required and optional fields for creating
 * a purchase order in the Common platform.
 */
public class PurchaseOrderCreateRequest {
    
    @JsonProperty("buyer_company_id")
    private String buyerCompanyId;
    
    @JsonProperty("seller_company_id")
    private String sellerCompanyId;
    
    @JsonProperty("product_id")
    private String productId;
    
    @JsonProperty("quantity")
    private String quantity;
    
    @JsonProperty("unit_price")
    private String unitPrice;
    
    @JsonProperty("unit")
    private String unit;
    
    @JsonProperty("delivery_date")
    private String deliveryDate;
    
    @JsonProperty("delivery_location")
    private String deliveryLocation;
    
    @JsonProperty("notes")
    private String notes;
    
    @JsonProperty("composition")
    private Map<String, Double> composition;
    
    @JsonProperty("input_materials")
    private List<Map<String, Object>> inputMaterials;
    
    @JsonProperty("origin_data")
    private Map<String, Object> originData;
    
    // Default constructor
    public PurchaseOrderCreateRequest() {}
    
    // Getters and setters
    public String getBuyerCompanyId() {
        return buyerCompanyId;
    }
    
    public void setBuyerCompanyId(String buyerCompanyId) {
        this.buyerCompanyId = buyerCompanyId;
    }
    
    public String getSellerCompanyId() {
        return sellerCompanyId;
    }
    
    public void setSellerCompanyId(String sellerCompanyId) {
        this.sellerCompanyId = sellerCompanyId;
    }
    
    public String getProductId() {
        return productId;
    }
    
    public void setProductId(String productId) {
        this.productId = productId;
    }
    
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
    
    public String getUnit() {
        return unit;
    }
    
    public void setUnit(String unit) {
        this.unit = unit;
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
    
    public Map<String, Double> getComposition() {
        return composition;
    }
    
    public void setComposition(Map<String, Double> composition) {
        this.composition = composition;
    }
    
    public List<Map<String, Object>> getInputMaterials() {
        return inputMaterials;
    }
    
    public void setInputMaterials(List<Map<String, Object>> inputMaterials) {
        this.inputMaterials = inputMaterials;
    }
    
    public Map<String, Object> getOriginData() {
        return originData;
    }
    
    public void setOriginData(Map<String, Object> originData) {
        this.originData = originData;
    }
}

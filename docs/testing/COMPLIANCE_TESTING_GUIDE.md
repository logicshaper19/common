# Compliance Engine End-to-End Testing Guide

This guide walks you through testing the complete compliance engine with realistic supply chain data from Tier 1 (Brand) all the way down to Tier 5 (Originator/Plantation).

## 🎯 Overview

The test scenario creates a complete palm oil supply chain with:
- **5 Companies** across different tiers (Brand → Trader → Refinery → Mill → Plantation)
- **4 Purchase Orders** flowing through the supply chain
- **4 Products** representing transformation at each tier
- **Compliance Documents** for EUDR and RSPO regulations
- **Real compliance checks** across the entire chain

## 🚀 Quick Start

### 1. Create Test Scenario

```bash
# From the project root directory
python run_compliance_test.py
```

This creates:
- Companies from Tier 1 to Tier 5
- Users for each company
- Products (FFB → CPO → RPO → Palm Products)
- Purchase orders connecting the supply chain
- Compliance documents
- Runs initial compliance checks

### 2. Test User Accounts Created

| Company | Tier | User | Email | Role |
|---------|------|------|-------|------|
| Global Consumer Brands Inc | 1 | Sarah Johnson | sarah.johnson@globalbrands.com | buyer |
| International Palm Trading Ltd | 2 | Michael Chen | michael.chen@palmtrading.com | buyer |
| Southeast Asia Palm Refinery | 3 | Priya Sharma | priya.sharma@searefinery.com | seller |
| Sustainable Palm Mill Co | 4 | Ahmad Rahman | ahmad.rahman@sustainablemill.com | seller |
| Green Valley Plantation | 5 | Maria Santos | maria.santos@greenvalley.com | seller |

**Password for all accounts:** `testpassword123`

## 🧪 Testing Scenarios

### Scenario 1: Brand Perspective (Tier 1)
**Login as:** sarah.johnson@globalbrands.com

**Test Steps:**
1. Navigate to Compliance Dashboard
2. View compliance status for incoming palm oil products
3. Check EUDR compliance requirements
4. Generate compliance report for regulatory submission
5. Verify supply chain transparency down to plantation level

**Expected Results:**
- See compliance status for PO from trader
- View aggregated compliance data from entire supply chain
- Generate comprehensive EUDR compliance report

### Scenario 2: Mill Operations (Tier 4)
**Login as:** ahmad.rahman@sustainablemill.com

**Test Steps:**
1. View purchase orders from plantation
2. Check document requirements for EUDR compliance
3. Upload mill processing certificates
4. Verify plantation geolocation data
5. Confirm compliance before processing

**Expected Results:**
- See FFB purchase order from plantation
- View required documents for compliance
- Upload and validate processing documents
- Confirm compliance status before confirming PO

### Scenario 3: Plantation/Originator (Tier 5)
**Login as:** maria.santos@greenvalley.com

**Test Steps:**
1. View outgoing purchase orders to mill
2. Upload RSPO certification documents
3. Provide geolocation data for plantation areas
4. Upload land use permits and legal documents
5. Complete EUDR due diligence requirements

**Expected Results:**
- See FFB sales to mill
- Upload required compliance documents
- Provide origin data (coordinates, harvest dates)
- Complete compliance checklist

### Scenario 4: Supply Chain Traceability
**Test across multiple accounts:**

1. **Start at Brand (Tier 1):** View final product compliance
2. **Trace to Trader (Tier 2):** Check refined oil sources
3. **Trace to Refinery (Tier 3):** Verify crude oil processing
4. **Trace to Mill (Tier 4):** Check FFB processing records
5. **Trace to Plantation (Tier 5):** Verify origin data

**Expected Results:**
- Complete traceability from consumer product to plantation
- All compliance checks pass through the chain
- Documents and certifications linked at each tier

## 📊 Compliance Checks to Test

### EUDR Compliance
- ✅ **Geolocation Present:** Plantation coordinates provided
- ✅ **Deforestation Risk Assessment:** Satellite data analysis
- ✅ **Legal Documentation:** Land use permits valid
- ✅ **Due Diligence Statement:** Completed by importers

### RSPO Compliance
- ✅ **RSPO Certification:** Valid certification documents
- ✅ **Mass Balance Tracking:** Supply chain transparency
- ✅ **Audit Reports:** Regular compliance audits

### Supply Chain Transparency
- ✅ **Product Traceability:** Track from plantation to brand
- ✅ **Document Chain:** All required documents present
- ✅ **Tier Verification:** Each tier properly documented

## 🔍 Frontend Testing Areas

### 1. Compliance Dashboard
- **URL:** `/compliance`
- **Test:** View all POs with compliance status
- **Filter:** By regulation (EUDR, RSPO)
- **Filter:** By status (compliant, non-compliant, pending)

### 2. Purchase Order Details
- **URL:** `/purchase-orders/{po_id}`
- **Test:** View compliance overview for specific PO
- **Test:** Generate compliance report
- **Test:** View supply chain graph

### 3. Document Upload
- **Test:** Upload compliance documents
- **Test:** Document validation
- **Test:** Document requirements by tier

### 4. Compliance Reports
- **Test:** Generate PDF reports
- **Test:** Export compliance data
- **Test:** Regulatory submission formats

## 🧩 API Testing

### Compliance Endpoints
```bash
# Get compliance overview for a PO
GET /api/v1/compliance/overview/{po_id}

# Evaluate compliance for specific regulation
POST /api/v1/compliance/evaluate/{po_id}?regulation=eudr

# Get compliance dashboard data
GET /api/v1/compliance/dashboard

# Generate compliance report
GET /api/v1/compliance/report/{po_id}
```

### Document Endpoints
```bash
# Upload compliance document
POST /api/v1/documents/upload

# Get documents for PO
GET /api/v1/documents/?po_id={po_id}

# Validate document
POST /api/v1/documents/{doc_id}/validate
```

## 🎯 Success Criteria

### ✅ End-to-End Compliance Flow
- [ ] Complete supply chain created (Tier 1-5)
- [ ] Purchase orders flow through all tiers
- [ ] Compliance documents uploaded at each tier
- [ ] Compliance checks pass for all regulations
- [ ] Reports generated successfully

### ✅ User Experience
- [ ] Users can login and access their tier-specific data
- [ ] Compliance dashboard shows relevant information
- [ ] Document upload works smoothly
- [ ] Reports are generated and downloadable

### ✅ Regulatory Compliance
- [ ] EUDR requirements met across supply chain
- [ ] RSPO certification tracked properly
- [ ] Geolocation data captured for plantations
- [ ] Legal documentation validated

## 🔧 Troubleshooting

### Common Issues

**1. Database Connection Errors**
```bash
# Check if database is running
docker ps | grep postgres

# Restart database if needed
docker-compose up -d db
```

**2. Missing Dependencies**
```bash
# Install missing packages
pip install -r requirements.txt
```

**3. Authentication Issues**
```bash
# Clear browser cache and cookies
# Try incognito/private browsing mode
```

**4. Compliance Check Failures**
- Check if all required documents are uploaded
- Verify document validation status
- Ensure geolocation data is provided for plantations

## 📈 Next Steps

After successful testing:

1. **Add More Regulations:** Extend to UFLPA, BCI, etc.
2. **Add More Sectors:** Test with apparel, electronics, etc.
3. **Performance Testing:** Test with larger datasets
4. **Integration Testing:** Test with external APIs
5. **User Acceptance Testing:** Test with real users

## 🤝 Support

If you encounter issues:
1. Check the console logs for errors
2. Verify database connectivity
3. Ensure all services are running
4. Check the compliance engine logs

The compliance engine is now ready for comprehensive testing with realistic supply chain data! 🎉

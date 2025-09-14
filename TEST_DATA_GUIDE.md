# Test Data Creation Guide

This guide explains how to create comprehensive test data for the Common Supply Chain Platform, covering all company types from originators to brands.

## Available Scripts

### 1. **`create_complete_supply_chain_test_data.py`** - Full Supply Chain
Creates a comprehensive test environment with all company types and multiple users per company.

**Features:**
- 9 companies across all supply chain tiers
- 15+ users with different roles and permissions
- Complete supply chain from originators to consumer brands
- Includes consultants and regulators

**Usage:**
```bash
python create_complete_supply_chain_test_data.py
```

### 2. **`create_essential_test_data.py`** - Essential Testing
Creates the minimum viable set of companies for comprehensive testing.

**Features:**
- 6 companies (1 per major tier)
- 6 users (1 per company)
- Covers all major company types
- Quick setup for basic testing

**Usage:**
```bash
python create_essential_test_data.py
```

### 3. **`reset_test_data.py`** - Clean & Reset
Cleans up existing test data and optionally creates new data.

**Usage:**
```bash
# Clean up only
python reset_test_data.py --no-create

# Clean up and create essential test data
python reset_test_data.py

# Clean up and create full supply chain data
python reset_test_data.py --full
```

### 4. **Legacy Scripts** (for backward compatibility)
- `create_test_users.py` - Basic test users
- `create_test_credentials.py` - Additional test credentials  
- `create_originator_user.py` - Single originator user

## Supply Chain Tiers

The test data follows the supply chain tier structure:

### **Tier 6-7: Originators** 🌱
- **Kalimantan Palm Plantation** (originator)
- **Sumatra Smallholder Cooperative** (originator)
- **Green Valley Farms** (originator)

**Test Features:**
- Origin dashboard testing
- Farm management
- Harvest data recording
- EUDR compliance

### **Tier 5: Mills/Processors** ⚙️
- **Southeast Asia Palm Oil Mill** (mill_processor)
- **Tropical Refinery Ltd** (processor)
- **Valley Processing Mill** (mill_processor)

**Test Features:**
- Processing workflows
- Inventory management
- Quality control
- Order confirmation

### **Tier 4: Traders** 📈
- **Global Commodities Trading** (trader)
- **Asian Palm Oil Traders** (trader)
- **Global Commodities Inc** (trader)

**Test Features:**
- Trading operations
- Risk management
- Market analysis
- Contract management

### **Tier 3: Manufacturers** 🏭
- **Food Manufacturing Corp** (manufacturer)
- **Food Manufacturing Co** (manufacturer)

**Test Features:**
- Production management
- Quality control
- Supplier management
- Procurement

### **Tier 2: Brands/Retailers** 🏪
- **Sustainable Foods Brand** (brand)
- **Global Retail Chain** (brand)
- **Sustainable Brand Corp** (brand)

**Test Features:**
- Brand management
- Sustainability tracking
- Supply chain oversight
- Transparency reporting

### **Tier 1: Consumer Brands** 🏷️
- **Premium Consumer Brand** (brand)

**Test Features:**
- Consumer engagement
- Brand strategy
- Transparency reporting

### **Special Roles** 🔧
- **Supply Chain Consultants** (consultant)
- **Environmental Regulatory Agency** (regulator)

**Test Features:**
- Multi-client access
- Audit capabilities
- Compliance monitoring
- Regulatory oversight

## Login Credentials

All test accounts use the password: **`password123`**

### Essential Test Accounts
```
🌱 ORIGINATOR
  farmer@greenvalleyfarms.com - John Farmer (originator)

⚙️ PROCESSOR  
  processor@valleymill.com - Sarah Processor (processor)

📈 TRADER
  trader@globalcommodities.com - Mike Trader (trader)

🏭 MANUFACTURER
  manufacturer@foodmfg.com - Lisa Manufacturer (manufacturer)

🏷️ BRAND
  brand@sustainablebrand.com - Emma Brand Manager (brand_manager)

🔧 CONSULTANT
  consultant@supplychainconsultants.com - Dr. Smith Consultant (consultant)
```

### Full Supply Chain Accounts
See the output of `create_complete_supply_chain_test_data.py` for the complete list of 15+ test accounts.

## Testing Scenarios

### Origin Dashboard Testing
1. Login as `farmer@greenvalleyfarms.com`
2. Navigate to Origin Dashboard
3. Test farm management features
4. Test origin data recording
5. Test certification management

### Transparency Dashboard Testing
1. Login as `brand@sustainablebrand.com`
2. Navigate to Transparency Dashboard
3. Test supply chain visualization
4. Test gap analysis
5. Test multi-client features (as consultant)

### End-to-End Workflow Testing
1. Create purchase order as brand
2. Confirm order as processor
3. Add origin data as originator
4. Track transparency metrics
5. Generate compliance reports

## Database Schema

The test data populates these key tables:
- `companies` - All company types and tiers
- `users` - Users with appropriate roles and permissions
- `products` - Palm oil product catalog (via seed_data.py)
- `purchase_orders` - Test purchase orders (if created)
- `batches` - Test batches (if created)

## Cleanup

To clean up test data:
```bash
# Clean up all test data
python reset_test_data.py --no-create

# Or clean up and recreate
python reset_test_data.py
```

## Integration with Frontend

The test data works seamlessly with the frontend origin dashboard:

1. **API Services**: All test companies have corresponding API endpoints
2. **Authentication**: All test users can authenticate via the frontend
3. **Permissions**: Users have appropriate permissions for their roles
4. **Data Flow**: Complete data flow from origin to brand

## Troubleshooting

### Common Issues

1. **Database Connection**: Ensure PostgreSQL is running
2. **Import Errors**: Make sure you're in the correct directory
3. **Permission Errors**: Check database user permissions
4. **Duplicate Data**: Use reset script to clean up first

### Debug Steps

1. Check database connection:
   ```bash
   python -c "from app.core.database import SessionLocal; print('DB OK')"
   ```

2. Verify test data creation:
   ```bash
   python -c "from app.core.database import SessionLocal; from app.models.company import Company; db = SessionLocal(); print(f'Companies: {db.query(Company).count()}'); db.close()"
   ```

3. Test authentication:
   ```bash
   python -c "from app.core.database import SessionLocal; from app.models.user import User; db = SessionLocal(); print(f'Users: {db.query(User).count()}'); db.close()"
   ```

## Next Steps

1. **Run the essential test data script** for quick setup
2. **Test the origin dashboard** with originator accounts
3. **Test transparency features** with brand accounts
4. **Create purchase orders** to test end-to-end workflows
5. **Use consultant accounts** to test multi-client features

This comprehensive test data setup ensures you can thoroughly test all aspects of the supply chain platform, from origin data capture to brand transparency reporting.

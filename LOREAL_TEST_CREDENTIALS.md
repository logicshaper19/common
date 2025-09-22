# L'Oréal Supply Chain - Test Credentials & Instructions

## 🎉 System Status: READY FOR TESTING

Both frontend and backend servers are running successfully:
- **Backend**: http://127.0.0.1:8000 ✅
- **Frontend**: http://localhost:3000 ✅
- **API Documentation**: http://127.0.0.1:8000/docs

## 🔐 Working Test Credentials

I have successfully created test users for different roles in the L'Oréal supply chain. All users have been tested and are working.

### 1. L'Oréal Brand (Buyer)
- **Email**: `demo@loreal.com`
- **Password**: `BeautyCosmetics2024!`
- **Role**: Buyer
- **Company**: L'Oréal Demo
- **Type**: Manufacturer (Brand)
- **Country**: France

### 2. Cosmetic Manufacturing Solutions (Tier 1 Supplier)
- **Email**: `supplier@manufacturing.com`
- **Password**: `Manufacturing2024!`
- **Role**: Seller
- **Company**: Cosmetic Manufacturing Solutions
- **Type**: Manufacturer
- **Country**: Germany

### 3. Organic Farms Morocco (Originator)
- **Email**: `originator@organicfarms.com`
- **Password**: `OrganicFarms2024!`
- **Role**: Seller
- **Company**: Organic Farms Morocco
- **Type**: Plantation Grower
- **Country**: Morocco

## 🧪 Testing Instructions

### Step 1: Access the System
1. Open your browser and go to: http://localhost:3000
2. You should see the login page
3. Use any of the credentials above to log in

### Step 2: Test Different User Roles

#### As L'Oréal Buyer (demo@loreal.com)
1. **Login** with the L'Oréal credentials
2. **Create Purchase Orders**:
   - Navigate to Purchase Orders section
   - Create a new PO to Cosmetic Manufacturing Solutions
   - Specify product details, quantity, and delivery requirements
3. **View Suppliers**:
   - Check available suppliers
   - View supplier relationships
4. **Monitor Supply Chain**:
   - Track order status
   - View transparency metrics

#### As Manufacturing Supplier (supplier@manufacturing.com)
1. **Login** with the supplier credentials
2. **Confirm Purchase Orders**:
   - View incoming orders from L'Oréal
   - Confirm orders and create production batches
3. **Create Downstream Orders**:
   - Source materials from component suppliers
   - Create orders to raw material suppliers
4. **Manage Production**:
   - Track batch production
   - Update order status

#### As Originator (originator@organicfarms.com)
1. **Login** with the originator credentials
2. **Supply Raw Materials**:
   - View incoming orders from suppliers
   - Confirm material supply
3. **Provide Origin Data**:
   - Upload certificates and documentation
   - Provide farm location and sustainability data
4. **Track Deliveries**:
   - Update delivery status
   - Provide traceability information

### Step 3: Test Complete Supply Chain Flow

#### Scenario: Face Cream Production Chain
1. **L'Oréal** creates PO for 1000 units of face cream
2. **Manufacturing Supplier** confirms and creates component orders
3. **Component Suppliers** source raw materials
4. **Originators** supply natural ingredients
5. **Track** the complete chain from farm to final product

### Step 4: Test Key Features

#### Supply Chain Transparency
- View complete product journey
- Track materials from origin to final delivery
- Monitor compliance and certifications

#### Business Relationships
- Manage supplier-buyer connections
- View relationship history and metrics
- Test data sharing permissions

#### Purchase Order Management
- Create, confirm, and track orders
- Test order chaining and fulfillment
- Monitor delivery status

#### Document Management
- Upload compliance certificates
- Share documents across the chain
- Track document versions and approvals

## 🔧 API Testing

You can also test the system directly via API:

### Authentication
```bash
# Login as L'Oréal buyer
curl -X POST http://127.0.0.1:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "demo@loreal.com", "password": "BeautyCosmetics2024!"}'
```

### Get User Info
```bash
# Get current user info (use token from login)
curl -X GET http://127.0.0.1:8000/api/v1/auth/me \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### Create Purchase Order
```bash
# Create a purchase order (use token from login)
curl -X POST http://127.0.0.1:8000/api/v1/simple/purchase-orders \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "buyer_company_id": "YOUR_COMPANY_ID",
    "seller_company_id": "SUPPLIER_COMPANY_ID",
    "product_id": "PRODUCT_ID",
    "quantity": 1000,
    "unit_price": 25.00,
    "unit": "pieces",
    "delivery_date": "2024-12-31",
    "delivery_location": "L'\''Oréal Distribution Center",
    "notes": "Premium face cream order"
  }'
```

## 📊 Expected Test Results

### Successful Login
- All three user accounts should log in successfully
- Users should see role-appropriate dashboards
- Navigation should work correctly

### Purchase Order Flow
- L'Oréal can create orders to suppliers
- Suppliers can confirm and fulfill orders
- Order status should update correctly
- Chain relationships should be visible

### Supply Chain Transparency
- Complete product traceability
- Origin data visibility
- Compliance tracking
- Document sharing

### Business Relationships
- Supplier-buyer connections
- Relationship history
- Data sharing permissions
- Collaboration features

## 🚨 Troubleshooting

### If Login Fails
1. Check that both servers are running
2. Verify the email and password are correct
3. Check browser console for errors
4. Try refreshing the page

### If Features Don't Work
1. Check browser console for JavaScript errors
2. Verify API endpoints are accessible
3. Check network tab for failed requests
4. Ensure proper user permissions

### If Data is Missing
1. The system starts with basic seed data
2. You may need to create additional test data
3. Check if the database is properly initialized
4. Verify all migrations have run

## 🎯 Success Criteria

The system is working correctly if you can:
- ✅ Log in with all three test accounts
- ✅ Create and manage purchase orders
- ✅ View supplier relationships
- ✅ Track supply chain transparency
- ✅ Upload and share documents
- ✅ Monitor compliance status
- ✅ Test multi-user collaboration

## 📞 Support

If you encounter any issues:
1. Check the system logs in the terminal
2. Verify server status
3. Test API endpoints directly
4. Review the API documentation at http://127.0.0.1:8000/docs

## 🎉 Ready to Test!

The L'Oréal supply chain system is now ready for comprehensive testing. Use the credentials above to explore all features and test the complete supply chain workflow from brand to originator.

**Happy Testing!** 🚀

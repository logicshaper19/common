# Common Supply Chain Platform - User Documentation

## Table of Contents
1. [Getting Started](#getting-started)
2. [User Roles & Permissions](#user-roles--permissions)
3. [Purchase Order Management](#purchase-order-management)
4. [Product Catalog](#product-catalog)
5. [Transparency & Traceability](#transparency--traceability)
6. [Business Relationships](#business-relationships)
7. [Notifications](#notifications)
8. [Admin Functions](#admin-functions)
9. [Troubleshooting](#troubleshooting)
10. [Support](#support)

---

## Getting Started

### What is Common?
Common is a supply chain transparency platform that replaces contradictory declarations with a single, shared Purchase Order (PO) system. It enables viral adoption through an onboarding cascade where brands onboard suppliers, who then onboard their suppliers, creating a network effect.

### Key Features
- **Unified Purchase Orders**: Single source of truth for supply chain transactions
- **Dual Confirmation Model**: Different interfaces for processors vs originators
- **Transparency Calculations**: Real-time supply chain visibility scoring
- **Viral Onboarding**: Cascade supplier invitation system
- **Business Relationship Management**: Sophisticated data sharing controls

### System Requirements
- Modern web browser (Chrome, Firefox, Safari, Edge)
- Internet connection
- JavaScript enabled

---

## User Roles & Permissions

### Company Types

#### Brand
- **Purpose**: End consumer-facing companies
- **Capabilities**: Create POs, view transparency reports, manage suppliers
- **Example**: Fashion brands, retailers

#### Processor  
- **Purpose**: Companies that transform raw materials
- **Capabilities**: Confirm POs, link input materials, manage production
- **Example**: Textile mills, manufacturers

#### Originator
- **Purpose**: Companies that produce raw materials
- **Capabilities**: Add origin data, confirm harvest/production details
- **Example**: Farms, raw material producers

### User Roles

#### Admin
- Full access to company settings
- User management
- Business relationship management
- System configuration

#### Buyer
- Create and manage purchase orders
- View supplier information
- Access transparency reports

#### Seller
- Confirm purchase orders
- Manage product information
- View buyer requirements

#### Consultant
- Multi-client dashboard access
- Transparency analysis tools
- Gap identification and recommendations

---

## Purchase Order Management

### Creating a Purchase Order

1. **Navigate** to Purchase Orders → Create New
2. **Select** the seller company from your business relationships
3. **Choose** a product from the catalog
4. **Enter** quantity and delivery date
5. **Add** any special notes or requirements
6. **Submit** the PO

### Confirming Purchase Orders

#### For Processors (Transformation Interface)
1. **View** pending POs in your dashboard
2. **Click** "Confirm PO" on the order
3. **Link Input Materials**:
   - Select POs where you were the buyer
   - Specify quantities used from each input
   - Set percentage contributions
4. **Add** quality and processing notes
5. **Confirm** the order

#### For Originators (Origin Data Interface)
1. **View** POs requiring origin data
2. **Add Origin Information**:
   - Geographic coordinates (farm location)
   - Harvest/production date
   - Certifications (Organic, Fair Trade, etc.)
   - Farmer/producer information
   - Quality metrics
3. **Upload** certification documents
4. **Confirm** the order

### PO Status Tracking
- **Draft**: Being created, not yet sent
- **Pending**: Sent to seller, awaiting confirmation
- **Confirmed**: Seller has confirmed with details
- **Delivered**: Order completed
- **Cancelled**: Order cancelled

---

## Product Catalog

### Product Categories

#### Raw Materials
- **Examples**: Organic Cotton, Wool, Silk, Hemp
- **Requirements**: Origin data, certifications, harvest information
- **Transparency**: 100% when origin data is complete

#### Processed Materials  
- **Examples**: Cotton Yarn, Dyed Fabric, Finished Textile
- **Requirements**: Input material linking, processing details
- **Transparency**: Calculated from input material transparency

#### Finished Goods
- **Examples**: T-Shirts, Jeans, Dresses, Jackets
- **Requirements**: Manufacturing details, composition
- **Transparency**: Calculated from entire supply chain

### Product Information
- **Common Product ID**: Standardized identifier
- **HS Codes**: Trade compliance codes
- **Composition Rules**: Allowed input materials and percentages
- **Certifications**: Required sustainability certifications
- **Origin Requirements**: Required origin data fields

---

## Transparency & Traceability

### Transparency Metrics

#### Transparency to Mill (TTM)
- Measures visibility from finished product back to processing facilities
- Calculated using weighted averages of input material transparency
- Degradation factors applied for each transformation step

#### Transparency to Plantation (TTP)
- Measures visibility from finished product back to origin
- Includes all transformation steps and origin data
- 100% when complete origin data is available

### Supply Chain Visualization
- **Interactive Graphs**: Visual representation of supply chain connections
- **Gap Analysis**: Identification of missing traceability links
- **Improvement Recommendations**: Actionable steps to increase transparency

### Transparency Dashboard
- **Real-time Scores**: Live transparency calculations
- **Trend Analysis**: Historical transparency performance
- **Gap Identification**: Missing links and data requirements
- **Improvement Tracking**: Progress on transparency initiatives

---

## Business Relationships

### Establishing Relationships

#### Inviting Suppliers
1. **Navigate** to Business Relationships → Add Supplier
2. **Enter** supplier email address
3. **Select** relationship type (supplier, partner, etc.)
4. **Add** invitation message
5. **Send** invitation

#### Accepting Invitations
1. **Check** email for invitation link
2. **Click** invitation link
3. **Create** account and set password
4. **Complete** company profile
5. **Accept** relationship terms

### Data Sharing Permissions
- **Operational Data**: Quantities, dates, status updates
- **Commercial Data**: Prices, margins (restricted)
- **Traceability Data**: Supply chain connections, transparency scores
- **Origin Data**: Geographic, certification, quality information

### Relationship Management
- **View** all business relationships
- **Update** data sharing permissions
- **Terminate** relationships when needed
- **Track** relationship history and changes

---

## Notifications

### Notification Types
- **PO Status Changes**: When POs are created, confirmed, or updated
- **Relationship Invitations**: New business relationship requests
- **Transparency Updates**: When transparency scores change
- **System Alerts**: Important system notifications

### Notification Preferences
1. **Navigate** to Settings → Notifications
2. **Choose** notification types to receive
3. **Select** delivery methods (in-app, email, both)
4. **Set** frequency preferences
5. **Save** preferences

### In-App Notifications
- **Notification Center**: Central hub for all notifications
- **Real-time Updates**: Live notification delivery
- **Action Buttons**: Quick actions from notifications
- **Mark as Read**: Notification management

---

## Admin Functions

### User Management
- **Add Users**: Invite new team members
- **Role Assignment**: Set user permissions and roles
- **User Status**: Activate/deactivate user accounts
- **Access Control**: Manage user access to features

### Company Settings
- **Company Profile**: Update company information
- **Business Type**: Set company type and industry
- **Contact Information**: Manage company contacts
- **Certifications**: Manage company certifications

### Product Catalog Management
- **Add Products**: Create new product entries
- **Edit Products**: Update product information
- **Composition Rules**: Define material breakdown rules
- **Certification Requirements**: Set required certifications

### System Monitoring
- **Audit Logs**: View all system activities
- **Performance Metrics**: Monitor system performance
- **User Activity**: Track user actions and access
- **Error Logs**: Review system errors and issues

---

## Troubleshooting

### Common Issues

#### Login Problems
- **Forgot Password**: Use "Forgot Password" link on login page
- **Account Locked**: Contact your admin or support
- **Email Not Recognized**: Verify email address or contact admin

#### PO Issues
- **Cannot Create PO**: Check business relationships are established
- **Missing Products**: Contact admin to add products to catalog
- **Confirmation Errors**: Verify all required fields are completed

#### Transparency Issues
- **Low Scores**: Check for missing origin data or input material links
- **Calculation Errors**: Ensure all POs in chain are confirmed
- **Missing Data**: Complete required origin data or input material links

#### Performance Issues
- **Slow Loading**: Check internet connection, try refreshing page
- **Timeout Errors**: Contact support if persistent
- **Browser Issues**: Try different browser or clear cache

### Error Messages

#### "Insufficient Permissions"
- Your role doesn't allow this action
- Contact your admin to request access

#### "Business Relationship Required"
- You need an established relationship to perform this action
- Invite the company or accept their invitation

#### "Product Not Found"
- The product may not exist in the catalog
- Contact admin to add the product

#### "Validation Error"
- Required fields are missing or invalid
- Check all form fields and try again

---

## Support

### Getting Help

#### Self-Service Resources
- **Documentation**: This user guide and help articles
- **Video Tutorials**: Step-by-step video guides
- **FAQ**: Frequently asked questions
- **Community Forum**: User community discussions

#### Contact Support
- **Email**: support@common-platform.com
- **Phone**: +1 (555) 123-4567
- **Live Chat**: Available during business hours
- **Support Portal**: Submit tickets and track requests

#### Training Resources
- **Onboarding Webinars**: New user training sessions
- **Advanced Training**: Power user and admin training
- **Custom Training**: Company-specific training sessions
- **Certification Program**: Become a certified Common user

### Best Practices

#### Data Quality
- **Complete Information**: Fill in all required fields
- **Accurate Data**: Ensure all information is correct and up-to-date
- **Regular Updates**: Keep company and product information current
- **Documentation**: Maintain proper documentation for all activities

#### Security
- **Strong Passwords**: Use complex, unique passwords
- **Regular Updates**: Keep passwords updated regularly
- **Access Control**: Only share access with authorized users
- **Logout**: Always logout when finished

#### Collaboration
- **Clear Communication**: Use clear, professional language in notes
- **Timely Responses**: Respond to PO confirmations promptly
- **Relationship Building**: Maintain good relationships with partners
- **Feedback**: Provide feedback to improve the platform

---

## Glossary

**Business Relationship**: Formal connection between two companies enabling data sharing and PO creation

**Confirmation**: Process of validating and accepting a purchase order with required details

**Dual Confirmation Model**: Different interfaces for processors (input linking) vs originators (origin data)

**Gap Analysis**: Identification of missing traceability links in supply chain

**Input Materials**: Raw materials or components used to create a product

**Origin Data**: Information about where and how raw materials were produced

**Purchase Order (PO)**: Formal document requesting goods or services from a supplier

**Transparency Score**: Percentage representing supply chain visibility and traceability

**Transparency to Mill (TTM)**: Visibility from finished product back to processing facilities

**Transparency to Plantation (TTP)**: Visibility from finished product back to origin

**Viral Onboarding**: Process where companies invite their suppliers, who then invite theirs

---

*Last Updated: January 6, 2025*  
*Version: 1.0*  
*For technical support, contact: support@common-platform.com*


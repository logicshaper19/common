# Requirements Document

## Introduction

Common is a supply chain transparency platform that replaces contradictory declarations with a single, shared Purchase Order (PO) system. The platform enables viral adoption through an onboarding cascade where brands onboard suppliers, who then onboard their suppliers, creating a network effect. The system features a dual confirmation model with different interfaces for processors (who link input materials) and originators (who add origin data). This requirements document covers the MVP backend implementation that supports the core PO management, traceability calculations, and user management functionality.

## Requirements

### Requirement 1

**User Story:** As a platform admin, I need to define a standardized product catalog with composition rules, so that all companies use a common language and data is consistent.

#### Acceptance Criteria

1. WHEN creating a product THEN the system SHALL require a unique common_product_id (e.g., palm_refined_edible)
2. WHEN creating a product THEN the system SHALL specify if it can_have_composition
3. IF a product can_have_composition THEN the system SHALL define a material_breakdown schema specifying allowed input materials and percentage ranges
4. WHEN a user creates or confirms a PO THEN the product SHALL be selected from this catalog, not free-text
5. IF a product cannot have composition THEN the confirmation interface SHALL hide the composition fields
6. WHEN defining products THEN the system SHALL categorize them as raw_material, processed, or finished_good
7. WHEN validating compositions THEN the system SHALL enforce the material_breakdown rules defined for each product
8. WHEN products are created THEN the system SHALL require default units of measurement and HS codes for trade compliance

### Requirement 2

**User Story:** As a brand buyer (Paula), I want to create purchase orders for my suppliers through a simple interface, so that I can initiate transparent transactions and track my supply chain.

#### Acceptance Criteria

1. WHEN a brand buyer creates a PO THEN the system SHALL generate a unique Common PO ID and set status to 'pending'
2. WHEN creating a PO THEN the system SHALL require buyer company, seller company, product, quantity, and unit fields
3. WHEN a PO is created THEN the system SHALL send a notification to the seller company users
4. WHEN a PO is created THEN the system SHALL create an audit event recording the creation
5. IF the buyer selects an invalid seller company THEN the system SHALL reject the PO creation with an error message

### Requirement 3

**User Story:** As a processor (Sam), I want to confirm purchase orders and link them to my input materials, so that I can build traceability and satisfy my customers' transparency requirements.

#### Acceptance Criteria

1. WHEN a processor confirms a PO THEN the system SHALL allow updating the confirmed quantity and composition
2. WHEN confirming a PO THEN the system SHALL validate that composition percentages do not exceed 100%
3. WHEN a processor links input materials THEN the system SHALL verify the input POs belong to their company
4. WHEN input materials are linked THEN the system SHALL validate sufficient quantities are available from source POs
5. WHEN a PO is confirmed THEN the system SHALL update the status to 'confirmed' and notify the buyer
6. WHEN a PO is confirmed THEN the system SHALL trigger transparency score recalculation asynchronously
7. WHEN a seller clicks "Link Input Materials" THEN the system SHALL only display a list of POs where their company was the BUYER and which have a status of confirmed
8. WHEN linking input materials THEN the interface SHALL allow them to select multiple POs and specify the quantity_used from each

### Requirement 4

**User Story:** As an originator (Maria), I want to confirm purchase orders with simplified origin data entry, so that I can validate the source of my products without complex input linking.

#### Acceptance Criteria

1. WHEN a user goes to confirm a PO THEN the system SHALL determine the interface based on the seller's company type OR the product category
2. IF the seller is an originator OR the product is a raw_material THEN the system SHALL show the Origin Data Interface (certifications, coordinates)
3. IF the seller is a processor OR the product can_have_composition THEN the system SHALL show the Transformation Interface (with Link Input Materials button)
4. WHEN adding origin data THEN the system SHALL capture: geographic_coordinates (latitude/longitude), certifications (RSPO, NDPE, etc.), harvest_date, and farm_identification
5. WHEN origin data is added THEN the system SHALL validate required fields based on product category and regional compliance requirements
6. WHEN geographic coordinates are provided THEN the system SHALL validate they fall within reasonable bounds for the product type
7. WHEN certifications are claimed THEN the system SHALL validate against a predefined list of recognized certification bodies
8. WHEN an originator confirms a PO THEN the system SHALL update status to 'confirmed' and create audit events
9. IF origin data is incomplete THEN the system SHALL prevent confirmation and show validation errors
10. WHEN origin data is confirmed THEN it SHALL serve as the traceability origin point for transparency calculations with 100% transparency score

### Requirement 5

**User Story:** As a consultant (Charlie), I want to monitor transparency progress across multiple clients, so that I can identify gaps and provide strategic guidance efficiently.

#### Acceptance Criteria

1. WHEN a consultant accesses the dashboard THEN the system SHALL display transparency metrics for all client companies
2. WHEN viewing transparency data THEN the system SHALL show real-time scores calculated from the PO graph
3. WHEN gaps exist in traceability THEN the system SHALL highlight unconfirmed POs and missing links
4. WHEN transparency scores change THEN the system SHALL update the consultant dashboard in real-time
5. IF a consultant lacks permissions for a company THEN the system SHALL restrict access to that company's data

### Requirement 6

**User Story:** As a user (Sam/Seller), I want to add and invite my own suppliers to the platform, so that I can build traceability for the orders I need to fulfill and enable the viral onboarding cascade.

#### Acceptance Criteria

1. WHEN an admin invites a user THEN the system SHALL send an email invitation with a secure signup link
2. WHEN a user accepts an invitation THEN the system SHALL allow them to set their password and access their company's data
3. WHEN a company is onboarded THEN the system SHALL assign the appropriate company type (brand, processor, originator)
4. WHEN users are created THEN the system SHALL assign roles (admin, buyer, seller) based on company type and permissions
5. IF an invitation expires THEN the system SHALL prevent signup and require a new invitation
6. WHEN a seller views their dashboard THEN they SHALL have an option to "Add a Supplier"
7. WHEN a seller adds a supplier's email THEN the system SHALL create a pending company record and send an invitation to that email
8. WHEN the new supplier accepts THEN the system SHALL automatically create a business relationship giving the inviting seller permission to create POs for them
9. WHEN business relationships are established THEN the system SHALL define data visibility permissions between companies
10. WHEN companies have established relationships THEN they SHALL be able to see relevant PO data but not sensitive commercial information
11. WHEN a company onboards a supplier THEN the system SHALL track the onboarding chain for network effect analytics
12. WHEN suppliers are invited THEN the system SHALL provide onboarding guidance specific to their company type and role in the supply chain

### Requirement 7

**User Story:** As any user, I want the system to automatically calculate transparency scores based on linked POs, so that I can understand my supply chain visibility without manual analysis.

#### Acceptance Criteria

1. WHEN POs are confirmed with input materials THEN the system SHALL traverse the PO graph to calculate transparency using the formula: Transparency = Σ(Input_Transparency × Quantity_Weight)
2. WHEN calculating transparency THEN the system SHALL compute both Transparency to Mill (TTM) and Transparency to Plantation (TTP) scores
3. WHEN origin data is confirmed THEN the system SHALL assign 100% transparency score as the base case
4. WHEN transparency scores are calculated THEN the system SHALL apply degradation factors for each transformation step (e.g., 95% retention per step)
5. WHEN transparency scores are calculated THEN the system SHALL store results with timestamps for real-time dashboard display
6. WHEN the PO graph changes THEN the system SHALL recalculate affected transparency scores asynchronously within 30 seconds
7. IF circular references exist in the PO graph THEN the system SHALL detect and handle them gracefully by breaking the cycle at the oldest PO
8. WHEN transparency calculations complete THEN the system SHALL provide visual representations showing the supply chain path and confidence levels
9. WHEN partial traceability exists THEN the system SHALL calculate and display the percentage of traced vs untraced materials
10. WHEN transparency scores are below thresholds THEN the system SHALL highlight gaps and suggest actions to improve traceability

### Requirement 8

**User Story:** As any user, I want to receive notifications about PO status changes and system events, so that I can stay informed about my transactions and take timely action.

#### Acceptance Criteria

1. WHEN a PO status changes THEN the system SHALL send notifications to relevant company users
2. WHEN notifications are sent THEN the system SHALL support both in-app and email delivery methods
3. WHEN users have notification preferences THEN the system SHALL respect their email notification settings
4. WHEN critical events occur THEN the system SHALL ensure notification delivery and log any failures
5. IF notification delivery fails THEN the system SHALL retry with exponential backoff

### Requirement 9

**User Story:** As a developer, I want the system to maintain comprehensive audit logs, so that all PO changes and user actions can be tracked for compliance and debugging.

#### Acceptance Criteria

1. WHEN any PO is modified THEN the system SHALL create an audit event with full change details
2. WHEN audit events are created THEN the system SHALL include actor information (user and company)
3. WHEN storing audit data THEN the system SHALL use immutable event records with timestamps
4. WHEN querying audit logs THEN the system SHALL support filtering by PO, company, user, and event type
5. IF audit logging fails THEN the system SHALL prevent the operation and return an error

### Requirement 10

**User Story:** As a system operator, I want the platform to handle high loads and concurrent operations safely, so that multiple users can work simultaneously without data corruption.

#### Acceptance Criteria

1. WHEN multiple users modify the same PO THEN the system SHALL use database transactions to prevent conflicts
2. WHEN background jobs process transparency calculations THEN the system SHALL use a task queue for reliable execution
3. WHEN the system experiences high load THEN the system SHALL maintain response times under 2 seconds for API calls
4. WHEN database operations fail THEN the system SHALL rollback transactions and return appropriate error messages
5. IF the system needs to scale THEN the system SHALL support horizontal scaling through stateless API design

### Requirement 11

**User Story:** As a company admin, I want to manage my business relationships and data sharing permissions, so that I can control what information is visible to my suppliers and customers while maintaining transparency.

#### Acceptance Criteria

1. WHEN companies establish business relationships THEN the system SHALL create bidirectional visibility permissions
2. WHEN a company views PO data THEN the system SHALL only show POs where they are buyer, seller, or have established relationship permissions
3. WHEN companies share data THEN the system SHALL distinguish between operational data (quantities, dates) and sensitive commercial data (prices, margins)
4. WHEN relationship permissions are granted THEN the system SHALL allow companies to see traceability chains that include their materials
5. WHEN companies request to see upstream data THEN the system SHALL require explicit permission from each company in the chain
6. WHEN business relationships are terminated THEN the system SHALL revoke data access while preserving historical audit records
7. WHEN companies join the platform through invitations THEN the system SHALL automatically establish appropriate relationship permissions with the inviting company

### Requirement 12

**User Story:** As a security-conscious user, I want my data and authentication to be protected, so that sensitive supply chain information remains secure.

#### Acceptance Criteria

1. WHEN users authenticate THEN the system SHALL use JWT tokens with appropriate expiration times
2. WHEN API endpoints are accessed THEN the system SHALL validate user permissions based on company and role
3. WHEN sensitive data is stored THEN the system SHALL use encrypted database connections and secure password hashing
4. WHEN cross-company data is requested THEN the system SHALL enforce strict access controls
5. IF unauthorized access is attempted THEN the system SHALL log the attempt and return appropriate error responses
# Comprehensive L'Oréal Supply Chain - Complete Test Credentials

## Overview
- **Total Companies**: 101
- **Brand**: 1 (L'Oréal)
- **Tier 1 Suppliers**: 5 (Major Manufacturers)
- **Tier 2 Suppliers**: 15 (Component suppliers)
- **Tier 3 Suppliers**: 45 (Raw material suppliers)
- **Originators**: 135 (Farmers/Extractors)

## Complete Supply Chain Structure

```
L'Oréal Group (Brand)
├── Tier 1: Cosmetic Manufacturing Solutions (Germany) - EXISTING
│   ├── Tier 2: Premium Packaging Solutions 1
│   │   ├── Tier 3: Raw Materials Co 1
│   │   │   ├── Originator: Organic Farms 1 - EXISTING
│   │   │   ├── Originator: Sustainable Harvest 2
│   │   │   └── Originator: Natural Extracts 3
│   │   ├── Tier 3: Natural Extracts Ltd 2
│   │   └── Tier 3: Chemical Suppliers 3
│   ├── Tier 2: Chemical Components Ltd 2
│   └── Tier 2: Fragrance Ingredients Co 3
├── Tier 1: Beauty Production International (Italy) - NEW
├── Tier 1: Global Cosmetics Ltd (UK) - NEW
├── Tier 1: European Beauty Manufacturing (France) - NEW
└── Tier 1: Nordic Cosmetics AB (Sweden) - NEW
```

## Test Credentials

### Existing Users (Already Working)
#### L'Oréal Brand
- **Email**: `demo@loreal.com`
- **Password**: `BeautyCosmetics2024!`
- **Role**: Buyer

#### Cosmetic Manufacturing Solutions (Tier 1)
- **Email**: `supplier@manufacturing.com`
- **Password**: `Manufacturing2024!`
- **Role**: Seller

#### Organic Farms Morocco (Originator)
- **Email**: `originator@organicfarms.com`
- **Password**: `OrganicFarms2024!`
- **Role**: Seller

### New Tier 1 Suppliers (Major Manufacturers)
#### European Beauty Manufacturing
- **Email**: `manager@europeanbeauty.fr`
- **Password**: `Tier1Supplier32024!`
- **Role**: Seller

#### Nordic Cosmetics AB
- **Email**: `manager@nordiccosmetics.se`
- **Password**: `Tier1Supplier42024!`
- **Role**: Seller

#### Mediterranean Beauty Solutions
- **Email**: `manager@medbeauty.es`
- **Password**: `Tier1Supplier52024!`
- **Role**: Seller

#### Alpine Cosmetics GmbH
- **Email**: `manager@alpinecosmetics.at`
- **Password**: `Tier1Supplier62024!`
- **Role**: Seller

### Sample Tier 2 Suppliers (Component Suppliers)
#### Premium Packaging Solutions 1
- **Email**: `manager@tier21.com`
- **Password**: `Tier2Supplier12024!`
- **Role**: Seller

#### Premium Packaging Solutions 4
- **Email**: `manager@tier24.com`
- **Password**: `Tier2Supplier42024!`
- **Role**: Seller

#### Premium Packaging Solutions 7
- **Email**: `manager@tier27.com`
- **Password**: `Tier2Supplier72024!`
- **Role**: Seller

#### Premium Packaging Solutions 10
- **Email**: `manager@tier210.com`
- **Password**: `Tier2Supplier102024!`
- **Role**: Seller

#### Premium Packaging Solutions 13
- **Email**: `manager@tier213.com`
- **Password**: `Tier2Supplier132024!`
- **Role**: Seller

### Sample Tier 3 Suppliers (Raw Material Suppliers)
#### Raw Materials Co 1
- **Email**: `manager@tier31.com`
- **Password**: `Tier3Supplier12024!`
- **Role**: Seller

#### Raw Materials Co 4
- **Email**: `manager@tier34.com`
- **Password**: `Tier3Supplier42024!`
- **Role**: Seller

#### Raw Materials Co 7
- **Email**: `manager@tier37.com`
- **Password**: `Tier3Supplier72024!`
- **Role**: Seller

#### Raw Materials Co 10
- **Email**: `manager@tier310.com`
- **Password**: `Tier3Supplier102024!`
- **Role**: Seller

#### Raw Materials Co 13
- **Email**: `manager@tier313.com`
- **Password**: `Tier3Supplier132024!`
- **Role**: Seller

#### Raw Materials Co 16
- **Email**: `manager@tier316.com`
- **Password**: `Tier3Supplier162024!`
- **Role**: Seller

#### Raw Materials Co 19
- **Email**: `manager@tier319.com`
- **Password**: `Tier3Supplier192024!`
- **Role**: Seller

#### Raw Materials Co 25
- **Email**: `manager@tier325.com`
- **Password**: `Tier3Supplier252024!`
- **Role**: Seller

### Sample Originators (Farmers/Extractors)
#### Organic Farms 1
- **Email**: `manager@originator1.com`
- **Password**: `Originator12024!`
- **Role**: Seller

#### Organic Farms 4
- **Email**: `manager@originator4.com`
- **Password**: `Originator42024!`
- **Role**: Seller

#### Organic Farms 7
- **Email**: `manager@originator7.com`
- **Password**: `Originator72024!`
- **Role**: Seller

#### Organic Farms 10
- **Email**: `manager@originator10.com`
- **Password**: `Originator102024!`
- **Role**: Seller

#### Organic Farms 13
- **Email**: `manager@originator13.com`
- **Password**: `Originator132024!`
- **Role**: Seller

#### Organic Farms 16
- **Email**: `manager@originator16.com`
- **Password**: `Originator162024!`
- **Role**: Seller

#### Organic Farms 19
- **Email**: `manager@originator19.com`
- **Password**: `Originator192024!`
- **Role**: Seller

#### Organic Farms 25
- **Email**: `manager@originator25.com`
- **Password**: `Originator252024!`
- **Role**: Seller

#### Organic Farms 28
- **Email**: `manager@originator28.com`
- **Password**: `Originator282024!`
- **Role**: Seller

#### Organic Farms 31
- **Email**: `manager@originator31.com`
- **Password**: `Originator312024!`
- **Role**: Seller

#### Organic Farms 34
- **Email**: `manager@originator34.com`
- **Password**: `Originator342024!`
- **Role**: Seller

## Testing Instructions

1. **Access the System**: Open http://localhost:3000
2. **Start with Existing Users**: Use the existing credentials to test basic functionality
3. **Test New Suppliers**: Use the new credentials to test the expanded supply chain
4. **Create Purchase Orders**: Test the complete flow from brand to originator
5. **Test Multi-Tier Relationships**: Verify relationships between different tiers

## Key Features to Test

- **Multi-Tier Supply Chain**: 4 levels from brand to originator
- **Multiple Suppliers per Tier**: Realistic supplier diversity
- **Geographic Distribution**: Suppliers across Europe and North Africa
- **Role-Based Access**: Different permissions for different user types
- **Supply Chain Transparency**: Complete traceability from origin to brand
- **Purchase Order Chaining**: Automatic creation of downstream orders

## API Endpoints for Testing

- **Login**: `POST /api/v1/auth/login`
- **Purchase Orders**: `GET /api/v1/simple/purchase-orders`
- **Relationships**: `GET /api/v1/simple/relationships/suppliers`
- **Traceability**: `GET /api/v1/traceability`
- **Companies**: `GET /api/v1/companies`

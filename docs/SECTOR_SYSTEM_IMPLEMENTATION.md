# Sector-Specific Tier System Implementation

## Overview

This document describes the implementation of the sector-specific tier system for the Common Supply Chain Platform. The system allows the platform to serve multiple industries (palm oil, apparel, electronics) with sector-specific terminology, data requirements, and workflows while maintaining a universal technical architecture.

## Architecture

### Core Concept

The system separates **technical architecture** (universal graph of purchase orders) from **user experience** (sector-specific labels and forms):

- **Universal Engine**: Graph database of purchase orders that can represent any supply chain
- **Sector Semantics**: Configurable labels, forms, and workflows tailored to specific industries

### Database Schema

#### New Tables

1. **sectors**: Defines available business sectors
   - `id`: Unique sector identifier (e.g., 'palm_oil', 'apparel')
   - `name`: Human-readable name
   - `regulatory_focus`: List of relevant regulations

2. **sector_tiers**: Defines tier structure for each sector
   - `sector_id`: Reference to sector
   - `level`: Tier level (1-6)
   - `name`: Tier name (e.g., 'Brand', 'Mill', 'Farmer')
   - `is_originator`: Whether this tier adds origin data
   - `permissions`: List of permissions for this tier

3. **sector_products**: Products specific to each sector
   - `sector_id`: Reference to sector
   - `name`: Product name
   - `applicable_tiers`: Tier levels that can use this product

#### Updated Tables

- **users**: Added `sector_id` and `tier_level` columns
- **companies**: Added `sector_id` and `tier_level` columns

## Implementation Phases

### Phase 1: Core Infrastructure ✅
- Database schema updates
- Backend models and schemas
- Frontend types
- Basic API endpoints

### Phase 2: Sector Templates ✅
- Palm Oil sector template
- Apparel sector template
- Sector seeder service
- Migration scripts

### Phase 3: Frontend Components ✅
- Sector context provider
- Sector selector component
- Tier badge component
- API client integration

### Phase 4: Feature Flags ✅
- Backend feature flag system
- Frontend feature flag utilities
- Gradual rollout configuration

### Phase 5: Migration & Testing ✅
- Database migration script
- User/company migration
- Comprehensive test suite

## Sector Templates

### Palm Oil Sector
```
1. Brand (L'Oréal, Unilever)
2. Refinery/Processor (Asian Refineries)
3. Trader (Optional intermediary)
4. Mill (Makmur Selalu Mill) - Originator
5. Cooperative (Tani Maju Cooperative)
```

### Apparel Sector
```
1. Brand (Nike, H&M)
2. Garment Manufacturer
3. Fabric Mill
4. Yarn Spinner
5. Ginner
6. Cotton Farmer - Originator
```

## Usage

### Running the Migration

```bash
# 1. Run the migration script
python scripts/migrate_to_sectors.py

# 2. Test the implementation
python scripts/test_sector_system.py

# 3. Enable feature flags (optional)
export ENABLE_SECTOR_SYSTEM=true
export ENABLE_DYNAMIC_FORMS=true
```

### Feature Flags

Control rollout with environment variables:

- `ENABLE_SECTOR_SYSTEM`: Basic sector functionality
- `ENABLE_DYNAMIC_FORMS`: Sector-specific forms
- `ENABLE_TIER_PERMISSIONS`: Tier-based permissions
- `ENABLE_SECTOR_PRODUCTS`: Sector-specific product catalogs

### API Endpoints

```
GET /api/v1/sectors                    # Get all sectors
GET /api/v1/sectors/{id}/config        # Get sector configuration
GET /api/v1/sectors/{id}/tiers         # Get sector tiers
GET /api/v1/sectors/{id}/products      # Get sector products
GET /api/v1/users/me/sector-info       # Get user's sector info
```

### Frontend Components

```tsx
import { SectorProvider, useSector } from './contexts/SectorContext';
import { SectorSelector } from './components/sector/SectorSelector';
import { TierBadge } from './components/sector/TierBadge';

// Wrap app with SectorProvider
<SectorProvider>
  <App />
</SectorProvider>

// Use sector context
const { currentSector, userTier } = useSector();
```

## Backward Compatibility

The system maintains full backward compatibility:

1. **Legacy roles** continue to work alongside new tier system
2. **Dual write** updates both old and new fields during migration
3. **Feature flags** allow gradual rollout
4. **Role mapping** automatically assigns sectors to existing users

## Benefits

### For Users
- **Industry-specific terminology**: Familiar language for each sector
- **Relevant data collection**: Only collect data that matters for the industry
- **Regulatory compliance**: Pre-configured for industry regulations

### For Platform
- **Scalability**: Easy to add new sectors without code changes
- **Market expansion**: Address multiple industries with one platform
- **Network effects**: Cross-sector insights become valuable

## Next Steps

1. **Enable feature flags** for gradual rollout
2. **Add Electronics sector** template
3. **Implement dynamic forms** for origin data collection
4. **Add tier-based permissions** system
5. **Create sector-specific reporting** templates

## Troubleshooting

### Common Issues

1. **Migration fails**: Check database permissions and connection
2. **Feature flags not working**: Verify environment variables
3. **Frontend errors**: Ensure SectorProvider is properly wrapped
4. **API errors**: Check that sector endpoints are included in router

### Rollback Plan

If issues occur, disable feature flags:
```bash
export ENABLE_SECTOR_SYSTEM=false
```

The system will fall back to legacy role-based functionality.

## Support

For questions or issues with the sector system implementation, refer to:
- Test scripts in `scripts/`
- API documentation in `app/api/v1/sectors.py`
- Frontend components in `frontend/src/components/sector/`

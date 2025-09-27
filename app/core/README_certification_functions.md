# Certification Management Functions

This module implements atomic, composable, fast, and error-handled functions for AI assistant certification management scenarios in palm oil supply chains.

## Core Functions

### 1. `get_certifications()`
**Purpose**: Certificate expiry alerts, farm certifications, and compliance status

**Features**:
- Expiry date monitoring with 30-day default alert window
- Compliance status tracking (pending, verified, failed, exempt)
- Automatic renewal cost estimation and contact information
- Support for all certification types (RSPO, MSPO, Organic, Rainforest Alliance, Fair Trade)

**Example Usage**:
```python
manager = CertificationManager(db_connection)
certifications, metadata = manager.get_certifications(
    company_id="123",
    expires_within_days=30,
    certification_type="RSPO"
)
print(f"Found {metadata['needs_attention']} certificates needing attention")
```

### 2. `search_batches()`
**Purpose**: Find inventory by product, status, date range

**Features**:
- Product type filtering (FFB, CPO, RBDPO, etc.)
- Status-based searches (available, reserved, allocated, processed)
- Date range filtering with automatic optimization
- Transparency score thresholds
- Certification requirements filtering
- Quantity-based filtering

**Example Usage**:
```python
batches, metadata = manager.search_batches(
    product_type="CPO",
    status="available",
    certification_required="RSPO",
    min_quantity=10.0
)
print(f"Found {metadata['total_quantity']} MT of certified inventory")
```

### 3. `get_purchase_orders()`
**Purpose**: Recent POs with buyer/seller role filtering

**Features**:
- Role-based filtering (buyer, seller, or both)
- Status filtering across order lifecycle
- Date range queries with performance optimization
- Value estimation for financial planning
- Product type and company filtering

**Example Usage**:
```python
orders, metadata = manager.get_purchase_orders(
    company_id="123",
    role_filter="buyer",
    status="pending"
)
print(f"Found {len(orders)} pending purchase orders")
```

### 4. `get_farm_locations()`
**Purpose**: Farm data with GPS coordinates and certifications

**Features**:
- GPS coordinate filtering with radius searches
- EUDR compliance checking
- Certification distribution analysis
- Geographic analytics (center points, ranges)
- Compliance status filtering

**Example Usage**:
```python
farms, metadata = manager.get_farm_locations(
    certification_type="RSPO",
    eudr_compliant_only=True
)
print(f"Found {metadata['eudr_compliant_count']} EUDR compliant farms")
```

### 5. `get_company_info()`
**Purpose**: Company details, statistics, contact information

**Features**:
- Transparency score analytics
- Operational statistics (batches, orders, certifications)
- Company type filtering and distribution
- Contact information (when authorized)
- Compliance scoring

**Example Usage**:
```python
companies, metadata = manager.get_company_info(
    company_type="plantation_grower",
    min_transparency_score=80.0,
    include_statistics=True
)
print(f"Top transparency score: {metadata['transparency_analytics']['average_score']}")
```

## Design Principles Implementation

### 1. Atomic Functions
Each function does one thing well:
- Single responsibility principle
- Clear input/output contracts
- No side effects beyond database queries
- Standardized error handling

### 2. Composable Architecture
Functions work together seamlessly:
- Consistent data structures (dataclasses)
- Shared type definitions and enums
- Chainable operations for complex queries
- Example composite functions in `certification_examples.py`

### 3. Fast Performance
Optimized for speed:
- Query optimization with selective filtering
- Intelligent caching with TTL management
- Connection pooling support
- Performance monitoring and reporting
- Background cleanup of expired cache entries

### 4. Error Handling
Graceful failure management:
- Comprehensive try-catch blocks
- Detailed error logging
- Fallback return values
- User-friendly error messages
- Operational continuity during partial failures

## Performance Features

### Caching System (`certification_cache.py`)
- Thread-safe LRU cache with TTL
- Configurable cache durations per function type
- Automatic cleanup of expired entries
- Cache statistics and monitoring
- Performance tracking and reporting

### Query Optimization
- Selective index usage hints
- Batched query execution
- Date range optimization
- Geographic query optimization with bounding boxes
- Parameter binding for security and performance

### Connection Management
- Connection pooling for high-throughput scenarios
- Automatic connection lifecycle management
- Pool exhaustion handling
- Thread-safe operations

## AI Assistant Integration

### Natural Language Processing (`certification_examples.py`)
The `CertificationAIAssistant` class provides:
- Natural language query interpretation
- Intent recognition for certification topics
- Contextual parameter extraction
- Intelligent query routing to appropriate functions
- User-friendly response formatting

### Example AI Interactions
```python
assistant = CertificationAIAssistant(db_connection)

# Natural language query
response = assistant.handle_natural_language_query(
    "Show me urgent certification alerts for our company"
)

# Structured dashboard
dashboard = assistant.get_certification_dashboard("company_123")

# Compliance analysis
analysis = assistant.analyze_supply_chain_compliance("company_123")
```

## Data Structures

### Core Dataclasses
- `CertificationInfo`: Certificate details with expiry tracking
- `BatchInfo`: Inventory batch with traceability
- `PurchaseOrderInfo`: Order details with buyer/seller context
- `FarmLocation`: GPS coordinates with certification data
- `CompanyInfo`: Company statistics and contact information

### Enumeration Types
- `CertificationType`: RSPO, MSPO, Organic, etc.
- `ComplianceStatus`: pending, verified, failed, exempt
- `BatchStatus`: available, reserved, allocated, processed
- `OrderStatus`: pending, confirmed, fulfilled, cancelled

## Configuration

### Environment Variables
- `TRANSPARENCY_DEGRADATION_FACTOR`: Transparency calculation factor
- `TRANSPARENCY_CALCULATION_TIMEOUT`: Query timeout settings
- `V2_DASHBOARD_*`: Feature flags for different user types
- `V2_NOTIFICATION_CENTER`: Enable notification features

### Performance Tuning
- Default cache TTL: 300 seconds (5 minutes)
- AI query cache TTL: 180 seconds (3 minutes)
- Connection pool size: 5 connections
- Query result limits: Configurable per function

## Usage Examples

### Basic Certification Management
```python
from app.core.certification_functions import init_certification_manager

# Initialize
manager = init_certification_manager(db_connection)

# Check expiring certificates
certifications, metadata = manager.get_certifications(expires_within_days=7)
urgent_count = metadata['needs_attention']

# Find certified inventory
batches, _ = manager.search_batches(
    product_type="CPO",
    certification_required="RSPO",
    status="available"
)

# Get compliance overview
companies, meta = manager.get_company_info(include_statistics=True)
avg_transparency = meta['transparency_analytics']['average_score']
```

### AI Assistant Integration
```python
from app.core.certification_examples import create_ai_assistant

# Create AI assistant
assistant = create_ai_assistant(db_connection)

# Handle natural language queries
response = assistant.handle_natural_language_query(
    "Find me RSPO certified CPO inventory over 50 metric tons",
    context={'company_id': 'user_company_123'}
)

# Get comprehensive dashboard
dashboard = assistant.get_certification_dashboard('company_123')
alerts = dashboard['dashboard']['alerts']
compliance = dashboard['dashboard']['compliance']
```

### Performance Monitoring
```python
from app.core.certification_cache import get_performance_report, get_cache_stats

# Monitor performance
perf_report = get_performance_report()
cache_stats = get_cache_stats()

print(f"Average query time: {perf_report['avg_execution_time']}s")
print(f"Cache hit rate: {perf_report['cache_hit_rate']}%")
print(f"Active cache entries: {cache_stats['active_entries']}")
```

## Error Handling Patterns

### Function-Level Error Handling
```python
try:
    certifications, metadata = manager.get_certifications(company_id="invalid")
    # Handle successful result
except Exception as e:
    logger.error(f"Certification query failed: {str(e)}")
    # Return safe fallback
    return [], {'error': str(e), 'total_certificates': 0}
```

### AI Assistant Error Handling
```python
response = assistant.handle_natural_language_query("complex query")
if response['status'] == 'error':
    # Handle error gracefully
    return {
        'message': 'I encountered an issue. Please try a simpler query.',
        'suggestions': ['Show certification alerts', 'Find inventory']
    }
```

## Integration with Existing Schema

The functions integrate seamlessly with the existing schema context:
- Uses established table relationships
- Respects data privacy rules (coordinate rounding, email masking)
- Follows existing naming conventions
- Maintains compatibility with current feature flags
- Leverages existing business rules and calculations

## Testing and Validation

### Test Coverage
- Unit tests for each core function
- Integration tests for composable scenarios
- Performance benchmarks
- Error condition testing
- Cache behavior validation

### Validation Examples
```python
# Validate certification data
assert all(cert.days_until_expiry is not None for cert in certifications)
assert metadata['total_certificates'] == len(certifications)

# Validate batch search results
assert all(batch.status == 'available' for batch in available_batches)
assert all(batch.quantity >= min_quantity for batch in filtered_batches)
```

This implementation provides a robust, scalable foundation for AI-powered certification management in palm oil supply chains, with emphasis on performance, reliability, and ease of use.

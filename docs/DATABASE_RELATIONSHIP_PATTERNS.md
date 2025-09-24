# Database Relationship Configuration Patterns

This document establishes clear patterns and standards for SQLAlchemy relationship configuration to prevent runtime issues and maintain consistency.

## Core Principles

### 1. Avoid Circular Dependencies
- **Problem**: Circular FK references between models cause SQLAlchemy configuration errors
- **Solution**: Use unidirectional relationships with proper foreign key design
- **Example**: `PurchaseOrder.batch_id` → `Batch.id` (allocation) + `BatchCreationEvent` (provenance)

### 2. Use `overlaps` Parameter for Relationship Warnings
- **Problem**: SQLAlchemy warnings about overlapping relationships
- **Solution**: Add `overlaps` parameter to indicate intentional relationship overlap
- **Example**: `relationship("Batch", overlaps="creation_events")`

### 3. Proper Foreign Key Constraints
- **Problem**: Missing referential integrity
- **Solution**: Use proper FK constraints with CASCADE/SET NULL
- **Example**: `ForeignKey("batches.id", ondelete="CASCADE")`

## Relationship Patterns

### Pattern 1: One-to-One Relationships
```python
# Model A
class ModelA(Base):
    b_id = Column(UUID, ForeignKey("model_b.id"))
    b = relationship("ModelB", foreign_keys=[b_id], uselist=False)

# Model B
class ModelB(Base):
    # No back-reference to avoid circular dependency
    pass
```

### Pattern 2: One-to-Many with Back-Reference
```python
# Parent Model
class Parent(Base):
    children = relationship("Child", back_populates="parent", cascade="all, delete-orphan")

# Child Model
class Child(Base):
    parent_id = Column(UUID, ForeignKey("parents.id"))
    parent = relationship("Parent", back_populates="children")
```

### Pattern 3: Many-to-Many with Junction Table
```python
# Junction Table
class Association(Base):
    left_id = Column(UUID, ForeignKey("left_table.id"))
    right_id = Column(UUID, ForeignKey("right_table.id"))
    left = relationship("Left", back_populates="associations")
    right = relationship("Right", back_populates="associations")

# Left Model
class Left(Base):
    associations = relationship("Association", back_populates="left")

# Right Model
class Right(Base):
    associations = relationship("Association", back_populates="right")
```

### Pattern 4: Audit/Event Tracking (No Circular Dependencies)
```python
# Main Model
class MainModel(Base):
    events = relationship("Event", foreign_keys="Event.main_id", cascade="all, delete-orphan")

# Event Model
class Event(Base):
    main_id = Column(UUID, ForeignKey("main_models.id"))
    main = relationship("MainModel", foreign_keys=[main_id], overlaps="events")
```

## Common Anti-Patterns to Avoid

### ❌ Circular Dependencies
```python
# DON'T DO THIS
class PurchaseOrder(Base):
    batch_id = Column(UUID, ForeignKey("batches.id"))
    batch = relationship("Batch", back_populates="source_po")

class Batch(Base):
    source_po_id = Column(UUID, ForeignKey("purchase_orders.id"))
    source_po = relationship("PurchaseOrder", back_populates="batch")
```

### ❌ Missing `overlaps` Parameter
```python
# DON'T DO THIS (causes SQLAlchemy warnings)
class Batch(Base):
    events = relationship("Event", foreign_keys="Event.batch_id")

class Event(Base):
    batch_id = Column(UUID, ForeignKey("batches.id"))
    batch = relationship("Batch")  # Missing overlaps parameter
```

### ❌ Inconsistent Foreign Key Naming
```python
# DON'T DO THIS
class Model(Base):
    other_model_id = Column(UUID, ForeignKey("other_models.id"))
    other_model = relationship("OtherModel", foreign_keys=[other_model_id])
    # Should use foreign_keys="OtherModel.id" for clarity
```

## Best Practices

### 1. Relationship Naming
- Use descriptive names: `creation_events`, `source_purchase_order`
- Avoid generic names: `items`, `related`, `data`

### 2. Foreign Key Configuration
- Always specify `foreign_keys` parameter for clarity
- Use `uselist=False` for one-to-one relationships
- Use `cascade="all, delete-orphan"` for dependent relationships

### 3. Index Configuration
- Create indexes for foreign keys used in queries
- Use composite indexes for common query patterns
- Document index purposes in comments

### 4. Validation and Constraints
- Use database-level constraints for data integrity
- Add application-level validation for business rules
- Document relationship constraints in model docstrings

## Migration Guidelines

### 1. Breaking Circular Dependencies
1. Identify the circular reference
2. Determine which relationship is primary (allocation vs provenance)
3. Remove the secondary relationship
4. Create audit/event table for secondary tracking
5. Migrate existing data to new structure

### 2. Adding New Relationships
1. Create migration script
2. Add foreign key constraints
3. Create necessary indexes
4. Update model relationships
5. Test relationship configuration

### 3. Data Migration
1. Preserve existing data during transition
2. Validate data integrity after migration
3. Update application code to use new relationships
4. Remove deprecated fields after validation

## Testing Relationship Configuration

### 1. SQLAlchemy Mapper Configuration
```python
def test_relationship_configuration():
    from sqlalchemy.orm import configure_mappers
    configure_mappers()  # Should not raise warnings or errors
```

### 2. Relationship Navigation
```python
def test_relationship_navigation():
    # Test that relationships work in both directions
    po = session.query(PurchaseOrder).first()
    batch = po.batch  # Should work without errors
    
    event = session.query(BatchCreationEvent).first()
    source_po = event.source_purchase_order  # Should work without errors
```

### 3. Cascade Operations
```python
def test_cascade_operations():
    # Test that cascade operations work correctly
    po = session.query(PurchaseOrder).first()
    session.delete(po)
    session.commit()
    # Related events should be deleted (CASCADE)
```

## Monitoring and Maintenance

### 1. Regular Relationship Audits
- Check for SQLAlchemy warnings during startup
- Monitor query performance for relationship-heavy operations
- Validate data integrity with relationship constraints

### 2. Documentation Updates
- Keep relationship documentation current
- Document any relationship changes in migration notes
- Update API documentation for relationship changes

### 3. Performance Monitoring
- Monitor query performance for relationship operations
- Optimize indexes based on actual usage patterns
- Consider lazy loading strategies for large datasets

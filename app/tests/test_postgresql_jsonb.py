"""
Test PostgreSQL JSONB functionality using the proper test configuration.
"""
import pytest
from sqlalchemy import Column, String, DateTime, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
import uuid
from datetime import datetime

from app.core.database import Base

class TestJsonbModel(Base):
    """Test model with JSONB for PostgreSQL."""
    __tablename__ = "test_jsonb_model"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    data = Column(JSONB, nullable=False)
    created_at = Column(DateTime, default=func.now())

def test_postgresql_jsonb_crud(db_session, test_data):
    """Test CRUD operations with JSONB data."""
    # Create
    test_record = TestJsonbModel(
        name="Test Supply Chain Data",
        data=test_data
    )
    db_session.add(test_record)
    db_session.commit()
    
    # Read
    result = db_session.query(TestJsonbModel).first()
    assert result is not None
    assert result.name == "Test Supply Chain Data"
    assert result.data["supply_chain"]["palm_oil"]["quantity"] == 1000

def test_postgresql_jsonb_path_queries(db_session, test_data):
    """Test JSONB path queries."""
    # Create test data
    test_record = TestJsonbModel(
        name="Path Test Data",
        data=test_data
    )
    db_session.add(test_record)
    db_session.commit()
    
    # Test path query
    result = db_session.query(TestJsonbModel).filter(
        TestJsonbModel.data["supply_chain"]["palm_oil"]["origin"].as_string() == "Malaysia"
    ).first()
    assert result is not None
    assert result.name == "Path Test Data"

def test_postgresql_jsonb_contains_queries(db_session, test_data):
    """Test JSONB contains queries."""
    # Create test data
    test_record = TestJsonbModel(
        name="Contains Test Data",
        data=test_data
    )
    db_session.add(test_record)
    db_session.commit()
    
    # Test contains query
    result = db_session.query(TestJsonbModel).filter(
        TestJsonbModel.data.contains({"supply_chain": {"palm_oil": {"certifications": ["RSPO"]}}})
    ).first()
    assert result is not None
    assert result.name == "Contains Test Data"

def test_postgresql_jsonb_aggregation(db_session, test_data):
    """Test JSONB aggregation queries."""
    # Create multiple test records
    for i in range(3):
        test_record = TestJsonbModel(
            name=f"Test Data {i}",
            data={
                **test_data,
                "quality_metrics": {
                    "ffa_content": 0.1 + (i * 0.05),
                    "moisture": 0.1 + (i * 0.02)
                }
            }
        )
        db_session.add(test_record)
    db_session.commit()
    
    # Test aggregation
    result = db_session.query(TestJsonbModel).count()
    assert result == 3
    
    # Test filtering by JSONB values
    rspo_records = db_session.query(TestJsonbModel).filter(
        TestJsonbModel.data.contains({"supply_chain": {"palm_oil": {"certifications": ["RSPO"]}}})
    ).count()
    assert rspo_records == 3

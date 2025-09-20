"""
Simple test to verify PostgreSQL + JSONB works correctly.
This is a focused test to prove the approach works before expanding.
"""
import pytest
import asyncio
from sqlalchemy import create_engine, Column, String, DateTime, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import sessionmaker, declarative_base
import uuid
from datetime import datetime

# Create a separate Base for this test
TestBase = declarative_base()

class TestJsonbModel(TestBase):
    """Simple test model with JSONB for PostgreSQL."""
    __tablename__ = "test_jsonb_model"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    data = Column(JSONB, nullable=False)
    created_at = Column(DateTime, default=func.now())

def test_postgresql_jsonb_basic():
    """Test basic JSONB functionality with PostgreSQL."""
    # Connect to PostgreSQL
    engine = create_engine("postgresql://elisha@localhost:5432/common_test")
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Create tables
    TestBase.metadata.create_all(bind=engine)
    
    # Test data
    test_data = {
        "supply_chain": {
            "palm_oil": {
                "quantity": 1000,
                "unit": "kg",
                "origin": "Malaysia",
                "certifications": ["RSPO", "ISCC"],
                "supplier": {
                    "name": "Malaysian Palm Oil Supplier",
                    "location": "Kuala Lumpur"
                }
            }
        },
        "quality_metrics": {
            "ffa_content": 0.15,
            "moisture": 0.1
        }
    }
    
    # Test CRUD operations
    session = SessionLocal()
    try:
        # Create
        test_record = TestJsonbModel(
            name="Test Supply Chain Data",
            data=test_data
        )
        session.add(test_record)
        session.commit()
        
        # Read
        result = session.query(TestJsonbModel).first()
        assert result is not None
        assert result.name == "Test Supply Chain Data"
        assert result.data["supply_chain"]["palm_oil"]["quantity"] == 1000
        
        # Test JSONB path query
        path_result = session.query(TestJsonbModel).filter(
            TestJsonbModel.data["supply_chain"]["palm_oil"]["origin"].as_string() == "Malaysia"
        ).first()
        assert path_result is not None
        
        # Test JSONB contains query
        contains_result = session.query(TestJsonbModel).filter(
            TestJsonbModel.data.contains({"supply_chain": {"palm_oil": {"certifications": ["RSPO"]}}})
        ).first()
        assert contains_result is not None
        
        print("✅ PostgreSQL JSONB test passed!")
        
    finally:
        session.close()
        # Clean up
        TestBase.metadata.drop_all(bind=engine)

if __name__ == "__main__":
    test_postgresql_jsonb_basic()

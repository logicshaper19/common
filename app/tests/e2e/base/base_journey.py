"""
Base journey class for all user journey tests
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.tests.e2e.helpers.auth_helper import AuthHelper
from app.tests.e2e.helpers.api_client import APIClient
from app.tests.e2e.base.test_data_factory import TestDataFactory


class BaseJourney(ABC):
    """Base class for all user journey tests."""
    
    def __init__(self, client: TestClient, db_session: Session):
        self.client = client
        self.db_session = db_session
        self.auth_helper = AuthHelper(client)
        self.api_client = APIClient(client)
        self.data_factory = TestDataFactory(db_session)
        self.cleanup_ids = []  # Track created resources for cleanup
    
    @abstractmethod
    def get_persona_type(self) -> str:
        """Return the persona type (farmer, processor, etc.)"""
        pass
    
    @abstractmethod
    def setup_test_data(self) -> Dict[str, Any]:
        """Set up test data specific to this persona."""
        pass
    
    @abstractmethod
    def get_journey_steps(self) -> List[str]:
        """Return list of journey step names."""
        pass
    
    def cleanup(self):
        """Clean up created test data."""
        for resource_type, resource_id in self.cleanup_ids:
            try:
                self.data_factory.cleanup_resource(resource_type, resource_id)
            except Exception as e:
                # Log but don't fail cleanup
                print(f"Failed to cleanup {resource_type} {resource_id}: {e}")
        
        # Also cleanup factory resources
        self.data_factory.cleanup_all()
    
    def run_journey(self) -> Dict[str, Any]:
        """Run the complete journey and return results."""
        results = {
            "persona": self.get_persona_type(),
            "steps": [],
            "overall_status": "UNKNOWN"
        }
        
        try:
            test_data = self.setup_test_data()
            results["test_data"] = test_data
            
            for step_name in self.get_journey_steps():
                step_method = getattr(self, f"step_{step_name.lower().replace(' ', '_')}")
                step_result = step_method(test_data)
                results["steps"].append(step_result)
                
                if step_result["status"] == "FAIL":
                    results["overall_status"] = "FAIL"
                    break
            
            if results["overall_status"] != "FAIL":
                results["overall_status"] = "PASS"
                
        except Exception as e:
            results["overall_status"] = "ERROR"
            results["error"] = str(e)
        finally:
            self.cleanup()
        
        return results
    
    def create_step_result(self, step_name: str, status: str, details: str, data: Any = None) -> Dict[str, Any]:
        """Helper to create consistent step results."""
        result = {
            "step": step_name,
            "status": status,
            "details": details
        }
        if data is not None:
            result["data"] = data
        return result
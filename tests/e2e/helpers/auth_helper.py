"""
Authentication helper for E2E tests
"""
from typing import Dict
from fastapi.testclient import TestClient

from app.models.user import User
from app.core.security import create_access_token


class AuthHelper:
    """Helper for authentication in E2E tests."""
    
    def __init__(self, client: TestClient):
        self.client = client
    
    def create_auth_headers(self, user: User) -> Dict[str, str]:
        """Create authentication headers for a user."""
        token = create_access_token(data={
            "sub": str(user.id),
            "email": user.email,
            "role": user.role,
            "company_id": str(user.company_id)
        })
        return {"Authorization": f"Bearer {token}"}
    
    def login_user(self, email: str, password: str) -> Dict[str, str]:
        """Login user and return auth headers."""
        login_data = {
            "username": email,
            "password": password
        }
        
        response = self.client.post("/api/v1/auth/login", data=login_data)
        if response.status_code == 200:
            token_data = response.json()
            return {"Authorization": f"Bearer {token_data['access_token']}"}
        else:
            raise Exception(f"Login failed: {response.status_code} - {response.text}")
    
    def verify_authentication(self, headers: Dict[str, str]) -> Dict[str, any]:
        """Verify authentication headers work."""
        response = self.client.get("/api/v1/auth/me", headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Authentication verification failed: {response.status_code}")
    
    def logout_user(self, headers: Dict[str, str]) -> bool:
        """Logout user."""
        response = self.client.post("/api/v1/auth/logout", headers=headers)
        return response.status_code == 200
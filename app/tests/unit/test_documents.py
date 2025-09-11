"""
Comprehensive tests for document upload and management.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import patch, MagicMock, mock_open
import json
import io
from datetime import datetime, timedelta

from app.main import app
from app.models.user import User
from app.models.company import Company
from app.models.document import Document
from app.core.database import get_db
from app.tests.fixtures.factories import UserFactory, CompanyFactory
from app.core.auth import get_password_hash, create_access_token


class TestDocumentManagement:
    """Test document upload and management functionality."""

    def test_upload_document(self, client: TestClient, auth_headers: dict, db: Session):
        """Test uploading a document."""
        # Create a test user
        user = UserFactory()
        db.add(user)
        db.commit()
        db.refresh(user)

        # Create auth headers for this user
        token = create_access_token(data={"sub": str(user.id)})
        headers = {"Authorization": f"Bearer {token}"}

        # Create test file content
        file_content = b"Test document content"
        files = {"file": ("test_document.pdf", io.BytesIO(file_content), "application/pdf")}
        
        data = {
            "title": "Test Document",
            "description": "A test document",
            "document_type": "contract",
            "category": "legal"
        }

        with patch("app.services.document_service.upload_file_to_storage") as mock_upload:
            mock_upload.return_value = "documents/test_document_123.pdf"
            
            response = client.post("/api/documents/upload", files=files, data=data, headers=headers)
            assert response.status_code == 201
            
            response_data = response.json()
            assert response_data["title"] == "Test Document"
            assert response_data["description"] == "A test document"
            assert response_data["document_type"] == "contract"
            assert response_data["category"] == "legal"
            assert response_data["file_size"] == len(file_content)
            assert response_data["uploaded_by"] == str(user.id)

    def test_upload_document_invalid_type(self, client: TestClient, auth_headers: dict, db: Session):
        """Test uploading a document with invalid file type."""
        user = UserFactory()
        db.add(user)
        db.commit()

        token = create_access_token(data={"sub": str(user.id)})
        headers = {"Authorization": f"Bearer {token}"}

        # Create test file with invalid type
        file_content = b"Test document content"
        files = {"file": ("test_document.exe", io.BytesIO(file_content), "application/x-executable")}
        
        data = {
            "title": "Test Document",
            "document_type": "contract"
        }

        response = client.post("/api/documents/upload", files=files, data=data, headers=headers)
        assert response.status_code == 400
        assert "File type not allowed" in response.json()["detail"]

    def test_upload_document_too_large(self, client: TestClient, auth_headers: dict, db: Session):
        """Test uploading a document that's too large."""
        user = UserFactory()
        db.add(user)
        db.commit()

        token = create_access_token(data={"sub": str(user.id)})
        headers = {"Authorization": f"Bearer {token}"}

        # Create large file content (simulate)
        large_content = b"x" * (10 * 1024 * 1024)  # 10MB
        files = {"file": ("large_document.pdf", io.BytesIO(large_content), "application/pdf")}
        
        data = {
            "title": "Large Document",
            "document_type": "contract"
        }

        with patch("app.services.document_service.get_file_size") as mock_size:
            mock_size.return_value = 10 * 1024 * 1024  # 10MB
            
            response = client.post("/api/documents/upload", files=files, data=data, headers=headers)
            assert response.status_code == 400
            assert "File too large" in response.json()["detail"]

    def test_get_documents(self, client: TestClient, auth_headers: dict, db: Session):
        """Test getting user's documents."""
        # Create a test user
        user = UserFactory()
        db.add(user)
        db.commit()
        db.refresh(user)

        # Create test documents
        doc1 = Document(
            title="Document 1",
            filename="doc1.pdf",
            file_path="documents/doc1.pdf",
            file_size=1024,
            document_type="contract",
            category="legal",
            uploaded_by=user.id,
            company_id=user.company_id
        )
        doc2 = Document(
            title="Document 2",
            filename="doc2.pdf",
            file_path="documents/doc2.pdf",
            file_size=2048,
            document_type="invoice",
            category="financial",
            uploaded_by=user.id,
            company_id=user.company_id
        )
        db.add_all([doc1, doc2])
        db.commit()

        # Create auth headers
        token = create_access_token(data={"sub": str(user.id)})
        headers = {"Authorization": f"Bearer {token}"}

        response = client.get("/api/documents", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 2
        assert any(doc["title"] == "Document 1" for doc in data)
        assert any(doc["title"] == "Document 2" for doc in data)

    def test_get_document_by_id(self, client: TestClient, auth_headers: dict, db: Session):
        """Test getting a specific document by ID."""
        # Create a test user
        user = UserFactory()
        db.add(user)
        db.commit()
        db.refresh(user)

        # Create a test document
        doc = Document(
            title="Test Document",
            filename="test.pdf",
            file_path="documents/test.pdf",
            file_size=1024,
            document_type="contract",
            category="legal",
            uploaded_by=user.id,
            company_id=user.company_id
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        # Create auth headers
        token = create_access_token(data={"sub": str(user.id)})
        headers = {"Authorization": f"Bearer {token}"}

        response = client.get(f"/api/documents/{doc.id}", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == str(doc.id)
        assert data["title"] == "Test Document"
        assert data["filename"] == "test.pdf"

    def test_get_document_not_found(self, client: TestClient, auth_headers: dict, db: Session):
        """Test getting a non-existent document."""
        user = UserFactory()
        db.add(user)
        db.commit()

        token = create_access_token(data={"sub": str(user.id)})
        headers = {"Authorization": f"Bearer {token}"}

        response = client.get("/api/documents/999999", headers=headers)
        assert response.status_code == 404

    def test_get_document_wrong_company(self, client: TestClient, db: Session):
        """Test getting a document from a different company."""
        # Create two companies
        company1 = CompanyFactory()
        company2 = CompanyFactory()
        db.add_all([company1, company2])
        db.commit()

        # Create users for each company
        user1 = UserFactory(company_id=company1.id)
        user2 = UserFactory(company_id=company2.id)
        db.add_all([user1, user2])
        db.commit()

        # Create document for company1
        doc = Document(
            title="Company 1 Document",
            filename="doc1.pdf",
            file_path="documents/doc1.pdf",
            file_size=1024,
            document_type="contract",
            uploaded_by=user1.id,
            company_id=company1.id
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        # Try to access with user2 (from company2)
        token2 = create_access_token(data={"sub": str(user2.id)})
        headers2 = {"Authorization": f"Bearer {token2}"}

        response = client.get(f"/api/documents/{doc.id}", headers=headers2)
        assert response.status_code == 404

    def test_update_document(self, client: TestClient, auth_headers: dict, db: Session):
        """Test updating document metadata."""
        # Create a test user
        user = UserFactory()
        db.add(user)
        db.commit()
        db.refresh(user)

        # Create a test document
        doc = Document(
            title="Original Title",
            filename="test.pdf",
            file_path="documents/test.pdf",
            file_size=1024,
            document_type="contract",
            category="legal",
            uploaded_by=user.id,
            company_id=user.company_id
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        # Create auth headers
        token = create_access_token(data={"sub": str(user.id)})
        headers = {"Authorization": f"Bearer {token}"}

        # Update document
        update_data = {
            "title": "Updated Title",
            "description": "Updated description",
            "category": "financial"
        }

        response = client.put(f"/api/documents/{doc.id}", json=update_data, headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["title"] == "Updated Title"
        assert data["description"] == "Updated description"
        assert data["category"] == "financial"

        # Verify changes in database
        db.refresh(doc)
        assert doc.title == "Updated Title"
        assert doc.description == "Updated description"
        assert doc.category == "financial"

    def test_delete_document(self, client: TestClient, auth_headers: dict, db: Session):
        """Test deleting a document."""
        # Create a test user
        user = UserFactory()
        db.add(user)
        db.commit()
        db.refresh(user)

        # Create a test document
        doc = Document(
            title="Test Document",
            filename="test.pdf",
            file_path="documents/test.pdf",
            file_size=1024,
            document_type="contract",
            uploaded_by=user.id,
            company_id=user.company_id
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)
        doc_id = doc.id

        # Create auth headers
        token = create_access_token(data={"sub": str(user.id)})
        headers = {"Authorization": f"Bearer {token}"}

        with patch("app.services.document_service.delete_file_from_storage") as mock_delete:
            mock_delete.return_value = True
            
            response = client.delete(f"/api/documents/{doc_id}", headers=headers)
            assert response.status_code == 200

            # Verify document is deleted from database
            deleted_doc = db.query(Document).filter(Document.id == doc_id).first()
            assert deleted_doc is None

    def test_download_document(self, client: TestClient, auth_headers: dict, db: Session):
        """Test downloading a document."""
        # Create a test user
        user = UserFactory()
        db.add(user)
        db.commit()
        db.refresh(user)

        # Create a test document
        doc = Document(
            title="Test Document",
            filename="test.pdf",
            file_path="documents/test.pdf",
            file_size=1024,
            document_type="contract",
            uploaded_by=user.id,
            company_id=user.company_id
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        # Create auth headers
        token = create_access_token(data={"sub": str(user.id)})
        headers = {"Authorization": f"Bearer {token}"}

        with patch("app.services.document_service.get_file_from_storage") as mock_get:
            mock_get.return_value = b"Document content"
            
            response = client.get(f"/api/documents/{doc.id}/download", headers=headers)
            assert response.status_code == 200
            assert response.headers["content-type"] == "application/pdf"
            assert response.headers["content-disposition"] == f"attachment; filename=test.pdf"

    def test_document_search(self, client: TestClient, auth_headers: dict, db: Session):
        """Test searching documents."""
        # Create a test user
        user = UserFactory()
        db.add(user)
        db.commit()
        db.refresh(user)

        # Create test documents
        doc1 = Document(
            title="Contract Agreement",
            filename="contract.pdf",
            file_path="documents/contract.pdf",
            file_size=1024,
            document_type="contract",
            category="legal",
            uploaded_by=user.id,
            company_id=user.company_id
        )
        doc2 = Document(
            title="Invoice 2024",
            filename="invoice.pdf",
            file_path="documents/invoice.pdf",
            file_size=2048,
            document_type="invoice",
            category="financial",
            uploaded_by=user.id,
            company_id=user.company_id
        )
        db.add_all([doc1, doc2])
        db.commit()

        # Create auth headers
        token = create_access_token(data={"sub": str(user.id)})
        headers = {"Authorization": f"Bearer {token}"}

        # Search by title
        response = client.get("/api/documents/search?q=contract", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["title"] == "Contract Agreement"

        # Search by document type
        response = client.get("/api/documents/search?document_type=invoice", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["title"] == "Invoice 2024"

        # Search by category
        response = client.get("/api/documents/search?category=legal", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["title"] == "Contract Agreement"

    def test_document_permissions(self, client: TestClient, db: Session):
        """Test document access permissions."""
        # Create two companies
        company1 = CompanyFactory()
        company2 = CompanyFactory()
        db.add_all([company1, company2])
        db.commit()

        # Create users for each company
        user1 = UserFactory(company_id=company1.id)
        user2 = UserFactory(company_id=company2.id)
        db.add_all([user1, user2])
        db.commit()

        # Create document for company1
        doc = Document(
            title="Company 1 Document",
            filename="doc1.pdf",
            file_path="documents/doc1.pdf",
            file_size=1024,
            document_type="contract",
            uploaded_by=user1.id,
            company_id=company1.id
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        # Create auth headers
        token1 = create_access_token(data={"sub": str(user1.id)})
        headers1 = {"Authorization": f"Bearer {token1}"}

        token2 = create_access_token(data={"sub": str(user2.id)})
        headers2 = {"Authorization": f"Bearer {token2}"}

        # User1 should be able to access the document
        response = client.get(f"/api/documents/{doc.id}", headers=headers1)
        assert response.status_code == 200

        # User2 should not be able to access the document
        response = client.get(f"/api/documents/{doc.id}", headers=headers2)
        assert response.status_code == 404

    def test_document_versioning(self, client: TestClient, auth_headers: dict, db: Session):
        """Test document versioning functionality."""
        # Create a test user
        user = UserFactory()
        db.add(user)
        db.commit()
        db.refresh(user)

        # Create a test document
        doc = Document(
            title="Test Document",
            filename="test.pdf",
            file_path="documents/test.pdf",
            file_size=1024,
            document_type="contract",
            uploaded_by=user.id,
            company_id=user.company_id,
            version=1
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        # Create auth headers
        token = create_access_token(data={"sub": str(user.id)})
        headers = {"Authorization": f"Bearer {token}"}

        # Upload new version
        file_content = b"Updated document content"
        files = {"file": ("test_v2.pdf", io.BytesIO(file_content), "application/pdf")}
        
        data = {
            "title": "Test Document",
            "version_notes": "Updated contract terms"
        }

        with patch("app.services.document_service.upload_file_to_storage") as mock_upload:
            mock_upload.return_value = "documents/test_v2.pdf"
            
            response = client.post(f"/api/documents/{doc.id}/version", files=files, data=data, headers=headers)
            assert response.status_code == 201
            
            response_data = response.json()
            assert response_data["version"] == 2
            assert response_data["version_notes"] == "Updated contract terms"

    def test_document_approval_workflow(self, client: TestClient, auth_headers: dict, db: Session):
        """Test document approval workflow."""
        # Create a test user
        user = UserFactory()
        db.add(user)
        db.commit()
        db.refresh(user)

        # Create a test document
        doc = Document(
            title="Test Document",
            filename="test.pdf",
            file_path="documents/test.pdf",
            file_size=1024,
            document_type="contract",
            uploaded_by=user.id,
            company_id=user.company_id,
            status="pending_approval"
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        # Create auth headers
        token = create_access_token(data={"sub": str(user.id)})
        headers = {"Authorization": f"Bearer {token}"}

        # Approve document
        response = client.post(f"/api/documents/{doc.id}/approve", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "approved"

        # Verify status in database
        db.refresh(doc)
        assert doc.status == "approved"

    def test_document_metadata_extraction(self, client: TestClient, auth_headers: dict, db: Session):
        """Test automatic metadata extraction from documents."""
        # Create a test user
        user = UserFactory()
        db.add(user)
        db.commit()
        db.refresh(user)

        # Create test file content
        file_content = b"Test document content"
        files = {"file": ("test_document.pdf", io.BytesIO(file_content), "application/pdf")}
        
        data = {
            "title": "Test Document",
            "document_type": "contract"
        }

        # Create auth headers
        token = create_access_token(data={"sub": str(user.id)})
        headers = {"Authorization": f"Bearer {token}"}

        with patch("app.services.document_service.upload_file_to_storage") as mock_upload, \
             patch("app.services.document_service.extract_metadata") as mock_extract:
            
            mock_upload.return_value = "documents/test_document_123.pdf"
            mock_extract.return_value = {
                "author": "John Doe",
                "creation_date": "2024-01-01",
                "keywords": ["contract", "agreement"]
            }
            
            response = client.post("/api/documents/upload", files=files, data=data, headers=headers)
            assert response.status_code == 201
            
            response_data = response.json()
            assert response_data["metadata"]["author"] == "John Doe"
            assert response_data["metadata"]["creation_date"] == "2024-01-01"
            assert "contract" in response_data["metadata"]["keywords"]

    def test_document_audit_trail(self, client: TestClient, auth_headers: dict, db: Session):
        """Test document audit trail functionality."""
        # Create a test user
        user = UserFactory()
        db.add(user)
        db.commit()
        db.refresh(user)

        # Create a test document
        doc = Document(
            title="Test Document",
            filename="test.pdf",
            file_path="documents/test.pdf",
            file_size=1024,
            document_type="contract",
            uploaded_by=user.id,
            company_id=user.company_id
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        # Create auth headers
        token = create_access_token(data={"sub": str(user.id)})
        headers = {"Authorization": f"Bearer {token}"}

        # Get document audit trail
        response = client.get(f"/api/documents/{doc.id}/audit", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) > 0
        assert any(entry["action"] == "created" for entry in data)
        assert any(entry["user_id"] == str(user.id) for entry in data)

    def test_document_bulk_operations(self, client: TestClient, auth_headers: dict, db: Session):
        """Test bulk document operations."""
        # Create a test user
        user = UserFactory()
        db.add(user)
        db.commit()
        db.refresh(user)

        # Create test documents
        docs = []
        for i in range(3):
            doc = Document(
                title=f"Document {i+1}",
                filename=f"doc{i+1}.pdf",
                file_path=f"documents/doc{i+1}.pdf",
                file_size=1024,
                document_type="contract",
                uploaded_by=user.id,
                company_id=user.company_id
            )
            docs.append(doc)
            db.add(doc)
        db.commit()

        doc_ids = [str(doc.id) for doc in docs]

        # Create auth headers
        token = create_access_token(data={"sub": str(user.id)})
        headers = {"Authorization": f"Bearer {token}"}

        # Bulk delete documents
        with patch("app.services.document_service.delete_file_from_storage") as mock_delete:
            mock_delete.return_value = True
            
            response = client.post("/api/documents/bulk-delete", 
                                 json={"document_ids": doc_ids}, 
                                 headers=headers)
            assert response.status_code == 200
            
            data = response.json()
            assert data["message"] == f"Successfully deleted {len(doc_ids)} documents"

        # Verify documents are deleted
        for doc in docs:
            deleted_doc = db.query(Document).filter(Document.id == doc.id).first()
            assert deleted_doc is None

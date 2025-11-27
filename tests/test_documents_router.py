"""
Integration tests for Documents Router endpoints.

Tests are organized by endpoint:
- TestBriefEndpoint: Tests for /documents/brief
- TestSearchEndpoint: Tests for /documents/search
- TestHealthEndpoint: Tests for health check endpoints
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.common.constants import PROJECT_FILE_STORE


client = TestClient(app)


class TestHealthEndpoints:
    """Test suite for health check endpoints."""
    
    def test_root_endpoint(self):
        """Test root endpoint returns welcome message."""
        response = client.get("/")
        assert response.status_code == 200
        assert "message" in response.json()
        assert "Agile Monkeys" in response.json()["message"]
    
    def test_health_check_endpoint(self):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}


class TestBriefEndpoint:
    """Test suite for /documents/brief endpoint."""
    
    @pytest.fixture
    def mock_documents_service(self):
        """Mock DocumentsService for router tests."""
        with patch('app.router.documents_router.documents_service') as mock_service:
            yield mock_service
    
    @pytest.fixture
    def mock_gemini_response(self):
        """Mock Gemini API response."""
        response = MagicMock()
        response.text = "This document discusses machine learning algorithms and their applications."
        return response
    
    def test_generate_brief_success(
        self, 
        mock_documents_service,
        mock_gemini_response,
        valid_pdf_file,
        test_user_uuid
    ):
        """Test successful brief generation."""
        # Setup mocks
        mock_documents_service.validate_documents = AsyncMock(return_value=True)
        mock_documents_service.upload_files_to_store = AsyncMock(
            return_value="test-store-name"
        )
        
        with patch('app.router.documents_router.client') as mock_client:
            mock_client.models.generate_content = AsyncMock(return_value=mock_gemini_response)
            
            with patch('app.common.constants.user_uuid', test_user_uuid):
                # Prepare file for upload
                PROJECT_FILE_STORE[test_user_uuid] = [{
                    'filename': 'test.pdf',
                    'content': b'test content',
                    'mime_type': 'application/pdf'
                }]
                
                # Make request
                with open('/tmp/test.pdf', 'wb') as f:
                    f.write(b'%PDF-1.4 test content')
                
                with open('/tmp/test.pdf', 'rb') as f:
                    response = client.post(
                        "/documents/documents/brief",
                        files={"files": ("test.pdf", f, "application/pdf")}
                    )
                
                assert response.status_code == 200
                data = response.json()
                assert "project_id" in data
                assert "store_name" in data
                assert "brief" in data
    
    def test_generate_brief_no_files(self, mock_documents_service):
        """Test brief generation fails with no files."""
        mock_documents_service.validate_documents = AsyncMock(
            side_effect=Exception("No files uploaded")
        )
        
        response = client.post("/documents/documents/brief", files={})
        
        # FastAPI returns 422 for validation errors on missing required fields
        assert response.status_code == 422
    
    def test_generate_brief_validation_error(
        self, 
        mock_documents_service,
        invalid_extension_file
    ):
        """Test brief generation with invalid file type."""
        from fastapi import HTTPException
        
        mock_documents_service.validate_documents = AsyncMock(
            side_effect=HTTPException(status_code=415, detail="Unsupported file type")
        )
        
        with open('/tmp/test.exe', 'wb') as f:
            f.write(b'malicious content')
        
        with open('/tmp/test.exe', 'rb') as f:
            response = client.post(
                "/documents/documents/brief",
                files={"files": ("malware.exe", f, "application/x-msdownload")}
            )
        
        assert response.status_code == 415


class TestSearchEndpoint:
    """Test suite for /documents/search endpoint."""
    
    @pytest.fixture
    def mock_documents_service(self):
        """Mock DocumentsService for router tests."""
        with patch('app.router.documents_router.documents_service') as mock_service:
            yield mock_service
    
    def test_search_store_success(
        self, 
        mock_documents_service,
        test_user_uuid,
        sample_project_files
    ):
        """Test successful document search."""
        # Setup
        search_results = [
            {"filename": "doc1.pdf", "snippet": "Result 1"},
            {"filename": "doc2.txt", "snippet": "Result 2"}
        ]
        mock_documents_service.search_all_user_files = AsyncMock(
            return_value=search_results
        )
        
        with patch('app.common.constants.user_uuid', test_user_uuid):
            PROJECT_FILE_STORE[test_user_uuid] = sample_project_files
            
            # Make request
            response = client.post(
                "/documents/documents/search",
                params={
                    "query": "What are the main topics?",
                    "project_id": test_user_uuid
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "results" in data
            assert len(data["results"]) == 2
            assert data["results"][0]["filename"] == "doc1.pdf"
    
    def test_search_store_empty_query(self, test_user_uuid):
        """Test search fails with empty query."""
        response = client.post(
            "/documents/documents/search",
            params={
                "query": "",
                "project_id": test_user_uuid
            }
        )
        
        assert response.status_code == 400
        assert "Query cannot be empty" in response.json()["detail"]
    
    def test_search_store_no_project_id(self):
        """Test search fails without project ID."""
        # The default project_id is user_uuid, so we need to test with empty string
        response = client.post(
            "/documents/documents/search",
            params={
                "query": "test query",
                "project_id": ""
            }
        )
        
        assert response.status_code == 400
        assert "Project ID is required" in response.json()["detail"]
    
    def test_search_store_no_files(self, test_user_uuid):
        """Test search fails when no files exist for project."""
        with patch('app.common.constants.user_uuid', test_user_uuid):
            # Ensure PROJECT_FILE_STORE is empty for this project
            PROJECT_FILE_STORE.pop(test_user_uuid, None)
            
            response = client.post(
                "/documents/documents/search",
                params={
                    "query": "test query",
                    "project_id": test_user_uuid
                }
            )
            
            assert response.status_code == 404
            assert "No files found" in response.json()["detail"]
    
    def test_search_store_service_error(
        self, 
        mock_documents_service,
        test_user_uuid,
        sample_project_files
    ):
        """Test search handles service errors."""
        mock_documents_service.search_all_user_files = AsyncMock(
            side_effect=Exception("Search service error")
        )
        
        with patch('app.common.constants.user_uuid', test_user_uuid):
            PROJECT_FILE_STORE[test_user_uuid] = sample_project_files
            
            response = client.post(
                "/documents/documents/search",
                params={
                    "query": "test query",
                    "project_id": test_user_uuid
                }
            )
            
            assert response.status_code == 500
            assert "Error during search" in response.json()["detail"]
    
    def test_search_store_with_default_project_id(
        self,
        mock_documents_service,
        sample_project_files
    ):
        """Test search uses default user_uuid when project_id not provided."""
        from app.common.constants import user_uuid
        
        search_results = [{"filename": "doc1.pdf", "snippet": "Result"}]
        mock_documents_service.search_all_user_files = AsyncMock(
            return_value=search_results
        )
        
        PROJECT_FILE_STORE[user_uuid] = sample_project_files
        
        response = client.post(
            "/documents/documents/search",
            params={"query": "test query"}
        )
        
        # Should use default user_uuid
        assert response.status_code == 200


class TestDocumentsRouterIntegration:
    """Integration tests for complete workflows."""
    
    @pytest.fixture
    def mock_complete_flow(self):
        """Mock all external dependencies for integration test."""
        with patch('app.router.documents_router.documents_service') as mock_service, \
             patch('app.router.documents_router.client') as mock_client:
            
            # Setup DocumentsService mocks
            mock_service.validate_documents = AsyncMock(return_value=True)
            mock_service.upload_files_to_store = AsyncMock(return_value="test-store")
            mock_service.search_all_user_files = AsyncMock(return_value=[
                {"filename": "test.pdf", "snippet": "Test result"}
            ])
            
            # Setup Gemini client mock
            mock_response = MagicMock()
            mock_response.text = "Generated brief content"
            mock_client.models.generate_content = AsyncMock(return_value=mock_response)
            
            yield mock_service, mock_client
    
    def test_upload_and_search_workflow(
        self, 
        mock_complete_flow,
        test_user_uuid
    ):
        """Test complete workflow: upload files, generate brief, then search."""
        mock_service, mock_client = mock_complete_flow
        
        with patch('app.common.constants.user_uuid', test_user_uuid):
            # Step 1: Upload files and generate brief
            with open('/tmp/workflow_test.pdf', 'wb') as f:
                f.write(b'%PDF-1.4 test content')
            
            with open('/tmp/workflow_test.pdf', 'rb') as f:
                brief_response = client.post(
                    "/documents/documents/brief",
                    files={"files": ("test.pdf", f, "application/pdf")}
                )
            
            assert brief_response.status_code == 200
            
            # Step 2: Add files to store for search
            PROJECT_FILE_STORE[test_user_uuid] = [{
                'filename': 'test.pdf',
                'content': b'test',
                'mime_type': 'application/pdf'
            }]
            
            # Step 3: Search the uploaded documents
            search_response = client.post(
                "/documents/documents/search",
                params={
                    "query": "What is in the document?",
                    "project_id": test_user_uuid
                }
            )
            
            assert search_response.status_code == 200
            results = search_response.json()["results"]
            assert len(results) > 0
            assert results[0]["filename"] == "test.pdf"

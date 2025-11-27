"""
Unit tests for DocumentsService class.

Tests are organized by functionality:
- TestDocumentValidation: File validation logic
- TestFileStorage: File storage operations
- TestFileSearch: Search and retrieval operations
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException

from services.documents_services import DocumentsService
from app.common.constants import PROJECT_FILE_STORE


class TestDocumentValidation:
    """Test suite for document validation methods."""
    
    @pytest.fixture
    def documents_service(self, mock_gemini_client):
        """Create DocumentsService instance for testing."""
        return DocumentsService(mock_gemini_client.aio)
    
    @pytest.mark.asyncio
    async def test_validate_documents_success(
        self, 
        documents_service, 
        valid_pdf_file,
        test_user_uuid
    ):
        """Test successful validation of valid documents."""
        with patch('services.documents_services.user_uuid', test_user_uuid):
            result = await documents_service.validate_documents([valid_pdf_file])
            assert result is True
            assert test_user_uuid in PROJECT_FILE_STORE
            assert len(PROJECT_FILE_STORE[test_user_uuid]) == 1
    
    @pytest.mark.asyncio
    async def test_validate_documents_empty_list(self, documents_service):
        """Test validation fails with empty file list."""
        with pytest.raises(HTTPException) as exc_info:
            await documents_service.validate_documents([])
        
        assert exc_info.value.status_code == 400
        assert "No files uploaded" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_validate_documents_no_filename(
        self, 
        documents_service,
        create_mock_upload_file
    ):
        """Test validation fails when file has no filename."""
        file = create_mock_upload_file(filename="")
        
        with pytest.raises(HTTPException) as exc_info:
            await documents_service.validate_documents([file])
        
        assert exc_info.value.status_code == 400
        assert "Invalid file name" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_validate_documents_invalid_extension(
        self, 
        documents_service,
        invalid_extension_file
    ):
        """Test validation fails with unsupported file extension."""
        with pytest.raises(HTTPException) as exc_info:
            await documents_service.validate_documents([invalid_extension_file])
        
        assert exc_info.value.status_code == 415
        assert "Unsupported file type" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_validate_documents_file_too_large(
        self, 
        documents_service,
        oversized_file
    ):
        """Test validation fails when file exceeds size limit."""
        with pytest.raises(HTTPException) as exc_info:
            await documents_service.validate_documents([oversized_file])
        
        assert exc_info.value.status_code == 413
        assert "File too large" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_validate_documents_invalid_mime_type(
        self, 
        documents_service,
        invalid_mime_type_file
    ):
        """Test validation fails with unsupported MIME type."""
        with pytest.raises(HTTPException) as exc_info:
            await documents_service.validate_documents([invalid_mime_type_file])
        
        assert exc_info.value.status_code == 415
        # Could fail at extension check (.jpg) or MIME type check
        assert ("Unsupported MIME type" in str(exc_info.value.detail) or 
                "Unsupported file type" in str(exc_info.value.detail))
    
    @pytest.mark.asyncio
    async def test_validate_documents_multiple_files(
        self, 
        documents_service,
        valid_pdf_file,
        valid_txt_file,
        test_user_uuid
    ):
        """Test validation of multiple valid files."""
        with patch('services.documents_services.user_uuid', test_user_uuid):
            result = await documents_service.validate_documents([valid_pdf_file, valid_txt_file])
            assert result is True
            assert len(PROJECT_FILE_STORE[test_user_uuid]) == 2
    
    def test_validate_extension_valid(self, documents_service):
        """Test _validate_extension with valid extensions."""
        assert documents_service._validate_extension("document.pdf") is True
        assert documents_service._validate_extension("file.txt") is True
        assert documents_service._validate_extension("doc.docx") is True
        assert documents_service._validate_extension("readme.md") is True
        assert documents_service._validate_extension("FILE.PDF") is True  # Case insensitive
    
    def test_validate_extension_invalid(self, documents_service):
        """Test _validate_extension with invalid extensions."""
        assert documents_service._validate_extension("malware.exe") is False
        assert documents_service._validate_extension("image.jpg") is False
        assert documents_service._validate_extension("archive.zip") is False
        assert documents_service._validate_extension("script.js") is False
    
    def test_validate_size_valid(self, documents_service, valid_pdf_file):
        """Test _validate_size with file within limit."""
        assert documents_service._validate_size(valid_pdf_file) is True
    
    def test_validate_size_invalid(self, documents_service, oversized_file):
        """Test _validate_size with file exceeding limit."""
        assert documents_service._validate_size(oversized_file) is False
    
    @pytest.mark.asyncio
    async def test_get_mime_type_pdf(self, documents_service, valid_pdf_file):
        """Test MIME type detection for PDF files."""
        mime_type = await documents_service._get_mime_type(valid_pdf_file)
        assert mime_type == "application/pdf"
    
    @pytest.mark.asyncio
    async def test_get_mime_type_text(self, documents_service, valid_txt_file):
        """Test MIME type detection for text files."""
        mime_type = await documents_service._get_mime_type(valid_txt_file)
        assert mime_type == "text/plain"


class TestFileStorage:
    """Test suite for file storage operations."""
    
    @pytest.fixture
    def documents_service(self, mock_gemini_client):
        """Create DocumentsService instance for testing."""
        return DocumentsService(mock_gemini_client.aio)
    
    @pytest.mark.asyncio
    async def test_store_project_files_new_user(
        self, 
        documents_service,
        valid_pdf_file,
        test_user_uuid
    ):
        """Test storing files for a new user."""
        with patch('services.documents_services.user_uuid', test_user_uuid):
            await documents_service.store_project_files(valid_pdf_file, "application/pdf")
            
            assert test_user_uuid in PROJECT_FILE_STORE
            assert len(PROJECT_FILE_STORE[test_user_uuid]) == 1
            
            stored_file = PROJECT_FILE_STORE[test_user_uuid][0]
            assert stored_file['filename'] == valid_pdf_file.filename
            assert stored_file['mime_type'] == "application/pdf"
            assert 'content' in stored_file
    
    @pytest.mark.asyncio
    async def test_store_project_files_existing_user(
        self, 
        documents_service,
        valid_pdf_file,
        valid_txt_file,
        test_user_uuid
    ):
        """Test storing multiple files for existing user."""
        with patch('services.documents_services.user_uuid', test_user_uuid):
            await documents_service.store_project_files(valid_pdf_file, "application/pdf")
            await documents_service.store_project_files(valid_txt_file, "text/plain")
            
            assert len(PROJECT_FILE_STORE[test_user_uuid]) == 2
    
    @pytest.mark.asyncio
    async def test_ensure_store_exists_creates_new(
        self, 
        documents_service,
        mock_file_search_store,
        test_user_uuid
    ):
        """Test ensure_store_exists creates a new store."""
        documents_service.client.file_search_stores.create = AsyncMock(
            return_value=mock_file_search_store
        )
        
        with patch('app.common.constants.user_uuid', test_user_uuid):
            store_name = await documents_service.ensure_store_exists()
            
            assert store_name == mock_file_search_store.name
            assert documents_service.file_search_store_name == mock_file_search_store.name
            documents_service.client.file_search_stores.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_ensure_store_exists_reuses_existing(
        self, 
        documents_service,
        mock_file_search_store
    ):
        """Test ensure_store_exists reuses existing store."""
        documents_service.file_search_store_name = mock_file_search_store.name
        documents_service.client.file_search_stores.create = AsyncMock()
        
        store_name = await documents_service.ensure_store_exists()
        
        assert store_name == mock_file_search_store.name
        documents_service.client.file_search_stores.create.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_upload_files_to_store_success(
        self, 
        documents_service,
        sample_project_files,
        mock_file_search_store,
        test_user_uuid
    ):
        """Test uploading files to Gemini file search store."""
        # Setup mocks
        documents_service.client.file_search_stores.create = AsyncMock(
            return_value=mock_file_search_store
        )
        documents_service.client.file_search_stores.upload_to_file_search_store = AsyncMock()
        
        # Populate PROJECT_FILE_STORE
        with patch('services.documents_services.user_uuid', test_user_uuid):
            PROJECT_FILE_STORE[test_user_uuid] = sample_project_files
            
            store_name = await documents_service.upload_files_to_store()
            
            assert store_name == mock_file_search_store.name
            # Verify upload was called for each file
            assert documents_service.client.file_search_stores.upload_to_file_search_store.call_count == 2
    
    @pytest.mark.asyncio
    async def test_upload_files_to_store_empty(
        self, 
        documents_service,
        mock_file_search_store,
        test_user_uuid
    ):
        """Test uploading with no files in store."""
        documents_service.client.file_search_stores.create = AsyncMock(
            return_value=mock_file_search_store
        )
        documents_service.client.file_search_stores.upload_to_file_search_store = AsyncMock()
        
        with patch('app.common.constants.user_uuid', test_user_uuid):
            PROJECT_FILE_STORE[test_user_uuid] = []
            
            store_name = await documents_service.upload_files_to_store()
            
            assert store_name == mock_file_search_store.name
            documents_service.client.file_search_stores.upload_to_file_search_store.assert_not_called()


class TestFileSearch:
    """Test suite for file search operations."""
    
    @pytest.fixture
    def documents_service(self, mock_gemini_client):
        """Create DocumentsService instance for testing."""
        service = DocumentsService(mock_gemini_client.aio)
        service.file_search_store_name = "test-store-name"
        return service
    
    @pytest.mark.asyncio
    async def test_search_individual_file_success(
        self, 
        documents_service,
        mock_generate_content_response
    ):
        """Test searching an individual file."""
        documents_service.client.models.generate_content = AsyncMock(
            return_value=mock_generate_content_response
        )
        
        file_info = {'filename': 'test.pdf'}
        query = "What is the main topic?"
        
        result = await documents_service.search_individual_file(query, file_info)
        
        assert result['filename'] == 'test.pdf'
        assert result['snippet'] == mock_generate_content_response.text
        documents_service.client.models.generate_content.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_search_all_user_files_success(
        self, 
        documents_service,
        sample_project_files,
        mock_generate_content_response
    ):
        """Test searching all user files."""
        documents_service.client.models.generate_content = AsyncMock(
            return_value=mock_generate_content_response
        )
        
        query = "What are the key points?"
        results = await documents_service.search_all_user_files(query, sample_project_files)
        
        assert len(results) == 2
        assert all('filename' in result for result in results)
        assert all('snippet' in result for result in results)
        assert documents_service.client.models.generate_content.call_count == 2
    
    @pytest.mark.asyncio
    async def test_search_all_user_files_empty_list(
        self, 
        documents_service
    ):
        """Test searching with empty file list."""
        query = "What are the key points?"
        results = await documents_service.search_all_user_files(query, [])
        
        assert results == []
    
    @pytest.mark.asyncio
    async def test_search_individual_file_api_error(
        self, 
        documents_service
    ):
        """Test search handles API errors gracefully."""
        documents_service.client.models.generate_content = AsyncMock(
            side_effect=Exception("API Error")
        )
        
        file_info = {'filename': 'test.pdf'}
        query = "What is the main topic?"
        
        with pytest.raises(Exception) as exc_info:
            await documents_service.search_individual_file(query, file_info)
        
        assert "API Error" in str(exc_info.value)

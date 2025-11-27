"""
Pytest configuration and shared fixtures for all tests.
"""
import io
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

# Configure pytest-asyncio
pytest_plugins = ('pytest_asyncio',)


@pytest.fixture
def mock_gemini_client():
    """Mock Gemini API client."""
    client = MagicMock()
    client.aio = MagicMock()
    client.aio.file_search_stores = MagicMock()
    client.aio.models = MagicMock()
    return client


@pytest.fixture
def mock_file_search_store():
    """Mock file search store response."""
    store = MagicMock()
    store.name = "projects/test-project/locations/us/fileSearchStores/test-store-123"
    return store


@pytest.fixture
def mock_generate_content_response():
    """Mock Gemini generate_content response."""
    response = MagicMock()
    response.text = "This is a test response from Gemini API."
    return response


@pytest.fixture
def create_mock_upload_file():
    """Factory fixture to create mock UploadFile instances."""
    def _create_file(
        filename: str = "test.pdf",
        content: bytes = b"test content",
        content_type: str = "application/pdf",
        size: int | None = None
    ):
        """
        Create a mock UploadFile.
        
        Args:
            filename: Name of the file
            content: File content as bytes
            content_type: MIME type
            size: File size (defaults to len(content))
        """
        file = MagicMock()
        file.filename = filename
        file.content_type = content_type
        file.size = size if size is not None else len(content)
        
        # Create a BytesIO object that can be read multiple times
        file_io = io.BytesIO(content)
        
        # Mock read to return content and allow multiple reads
        async def mock_read(size=-1):
            return file_io.read(size)
        
        # Mock seek to reset position
        async def mock_seek(position):
            return file_io.seek(position)
        
        file.read = mock_read
        file.seek = mock_seek
        file.file = file_io
        
        return file
    
    return _create_file


@pytest.fixture
def valid_pdf_file(create_mock_upload_file):
    """Create a valid PDF file for testing."""
    # PDF magic bytes
    pdf_content = b"%PDF-1.4\n%\xE2\xE3\xCF\xD3\n" + b"test content" * 100
    return create_mock_upload_file(
        filename="document.pdf",
        content=pdf_content,
        content_type="application/pdf",
        size=len(pdf_content)
    )


@pytest.fixture
def valid_txt_file(create_mock_upload_file):
    """Create a valid text file for testing."""
    txt_content = b"This is a plain text file with some content."
    return create_mock_upload_file(
        filename="document.txt",
        content=txt_content,
        content_type="text/plain",
        size=len(txt_content)
    )


@pytest.fixture
def invalid_extension_file(create_mock_upload_file):
    """Create a file with invalid extension."""
    return create_mock_upload_file(
        filename="document.exe",
        content=b"malicious content",
        content_type="application/x-msdownload",
        size=100
    )


@pytest.fixture
def oversized_file(create_mock_upload_file):
    """Create a file that exceeds size limit."""
    large_content = b"x" * (20 * 1024 * 1024)  # 20MB
    return create_mock_upload_file(
        filename="large.pdf",
        content=large_content,
        content_type="application/pdf",
        size=len(large_content)
    )


@pytest.fixture
def invalid_mime_type_file(create_mock_upload_file):
    """Create a file with invalid MIME type."""
    return create_mock_upload_file(
        filename="image.jpg",
        content=b"\xff\xd8\xff\xe0" + b"fake jpeg",
        content_type="image/jpeg",
        size=100
    )


@pytest.fixture
def test_user_uuid():
    """Consistent test user UUID."""
    return "test-user-12345"


@pytest.fixture
def sample_project_files():
    """Sample project files for testing."""
    return [
        {
            'filename': 'doc1.pdf',
            'content': b'PDF content here',
            'mime_type': 'application/pdf'
        },
        {
            'filename': 'doc2.txt',
            'content': b'Text content here',
            'mime_type': 'text/plain'
        }
    ]


@pytest.fixture(autouse=True)
def reset_project_store():
    """Reset PROJECT_FILE_STORE before each test."""
    from app.common.constants import PROJECT_FILE_STORE
    PROJECT_FILE_STORE.clear()
    yield
    PROJECT_FILE_STORE.clear()

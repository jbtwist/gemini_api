from io import BytesIO

import magic
from fastapi import HTTPException, UploadFile
from google.genai import types

from app.common.constants import PROJECT_FILE_STORE, user_uuid
from app.common.settings import settings


class DocumentsService:
    """
    Service class for handling document operations including validation,
    storage, and search functionality using Google's Gemini API.
    """
    
    def __init__(self, client):
        """
        Initialize the DocumentsService.
        
        Args:
            client: Google Gemini API client instance.
        """
        self.client = client
        self.file_search_store_name = None

    async def validate_documents(self, files: list[UploadFile]) -> bool:
        """
        Validate uploaded documents for file type, size, and MIME type compliance.
        
        This method performs comprehensive validation on uploaded files:
        - Checks if files list is not empty
        - Validates file has a valid filename
        - Checks file extension against allowed list
        - Verifies file size is within limits
        - Detects and validates MIME type
        - Stores valid files in PROJECT_FILE_STORE
        
        Args:
            files: List of UploadFile objects to validate.
            
        Returns:
            bool: True if all files pass validation.
            
        Raises:
            HTTPException(400): If no files uploaded or invalid filename.
            HTTPException(413): If file size exceeds maximum allowed size.
            HTTPException(415): If file type or MIME type is not supported.
        """
        if not files:
            raise HTTPException(status_code=400, detail="No files uploaded")

        for file in files:
            if not file.filename:
                raise HTTPException(status_code=400, detail="Invalid file name")
            if not self._validate_extension(file.filename):
                raise HTTPException(status_code=415, detail=f"Unsupported file type: {file.filename}")
            if not self._validate_size(file):
                raise HTTPException(status_code=413, detail=f"File too large: {file.filename}")

            mime_type = await self._get_mime_type(file)
            if mime_type not in settings.allowed_mime_types:
                raise HTTPException(status_code=415, detail=f"Unsupported MIME type: {mime_type}")

            await self.store_project_files(file, mime_type)

        return True


    def _validate_extension(self, filename: str) -> bool:
        """
        Validate file extension against allowed extensions list.
        
        Args:
            filename: Name of the file to validate.
            
        Returns:
            bool: True if extension is allowed, False otherwise.
        """
        file_extension = filename.split(".")[-1].lower()
        return file_extension in settings.allowed_extensions

    def _validate_size(self, file: UploadFile) -> bool:
        """
        Validate file size against maximum allowed size.
        
        Args:
            file: UploadFile object to check size.
            
        Returns:
            bool: True if file size is within limit, False otherwise.
        """
        return file.size <= settings.max_file_size

    async def _get_mime_type(self, file: UploadFile) -> str:
        """
        Detect MIME type of uploaded file by reading file headers.
        
        Reads first 1KB of file to detect MIME type using python-magic library.
        File pointer is reset after detection to allow further reading.
        
        Args:
            file: UploadFile object to detect MIME type.
            
        Returns:
            str: Detected MIME type (e.g., 'application/pdf', 'text/plain').
        """
        file_header = await file.read(1024)  # Read first 1KB for MIME type detection
        detected_mime = magic.from_buffer(file_header, mime=True)
        await file.seek(0)  # Reset file pointer after reading
        return detected_mime

    async def ensure_store_exists(self) -> str:
        """
        Ensure a Gemini file search store exists for the project.
        
        Creates a new file search store if one doesn't exist yet, or returns
        the existing store name. The store is used to upload and search documents.
        
        Returns:
            str: Name/ID of the file search store in Gemini.
        """
        if self.file_search_store_name is None:
            store_display_name = f"project_store_{user_uuid}"
            store = await self.client.file_search_stores.create(
                config={'display_name': store_display_name}
            )
            self.file_search_store_name = store.name

        return self.file_search_store_name

    async def store_project_files(self, file: UploadFile, mime_type: str) -> None:
        """
        Store uploaded file in memory (PROJECT_FILE_STORE).
        
        Files are stored temporarily in memory with their content and metadata.
        In production, this should be replaced with blob storage (S3, GCS, etc.).
        
        Args:
            file: UploadFile object to store.
            mime_type: MIME type of the file.
        """
        if user_uuid not in PROJECT_FILE_STORE:
            PROJECT_FILE_STORE[user_uuid] = []

        file_content = await file.read()
        PROJECT_FILE_STORE[user_uuid].append(
            {
                'filename': file.filename,
                'content': file_content,
                'mime_type': mime_type
            }
        )

    async def upload_files_to_store(self) -> str:
        """
        Upload all user files to Gemini file search store.
        
        Takes files from PROJECT_FILE_STORE and uploads them to the Gemini
        file search store for semantic search capabilities.
        
        Returns:
            str: Name/ID of the file search store containing uploaded files.
        """
        store_name = await self.ensure_store_exists()

        for file_data in PROJECT_FILE_STORE.get(user_uuid, []):
            file_stream = BytesIO(file_data['content'])
            file_stream.name = file_data['filename']

            await self.client.file_search_stores.upload_to_file_search_store(
                file_search_store_name=store_name,
                file=file_stream,
                config={
                    'mime_type': file_data['mime_type'],
                    'display_name': file_data['filename']
                }
            )

        return store_name

    async def search_individual_file(self, query: str, file_info: dict) -> dict:
        """
        Search a single file using Gemini AI.
        
        Uses Gemini's file search capability to find relevant information
        in a specific document based on the query.
        
        Args:
            query: Search query string.
            file_info: Dictionary containing file metadata (filename, content, mime_type).
            
        Returns:
            dict: Dictionary with 'filename' and 'snippet' keys containing search results.
        """
        response = await self.client.models.generate_content(
            model="gemini-2.5-flash",
            contents=query,
            config=types.GenerateContentConfig(
                tools=[
                    types.Tool(
                        file_search=types.FileSearch(
                            file_search_store_names=[self.file_search_store_name]
                        )
                    )
                ]
            )
        )

        return {
            "filename": file_info['filename'],
            "snippet": response.text
        }


    async def search_all_user_files(self, query: str, project_files: list[dict]) -> list[dict]:
        """
        Search across all user files using Gemini AI.
        
        Iterates through all project files and searches each one for relevant
        information based on the query.
        
        Args:
            query: Search query string.
            project_files: List of file metadata dictionaries.
            
        Returns:
            list[dict]: List of search results, each containing filename and snippet.
        """
        results = []
        for file_info in project_files:
            result = await self.search_individual_file(query, file_info)
            if result:
                results.append(result)

        return results

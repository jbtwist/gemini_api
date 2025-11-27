from io import BytesIO

import magic
from fastapi import HTTPException, UploadFile
from google.genai import types

from app.common.constants import PROJECT_FILE_STORE, user_uuid
from app.common.settings import settings


class DocumentsService:
    def __init__(self, client):
        self.client = client
        self.file_search_store_name = None

    async def validate_documents(self, files: list[UploadFile]) -> bool:
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
        file_extension = filename.split(".")[-1].lower()
        return file_extension in settings.allowed_extensions

    def _validate_size(self, file: UploadFile) -> bool:
        return file.size <= settings.max_file_size

    # Sadly this I/O operation is not awaitable, but should be fast since it only checks headers
    async def _get_mime_type(self, file: UploadFile) -> str:
        file_header = await file.read(1024)  # Read first 1KB for MIME type detection
        detected_mime = magic.from_buffer(file_header, mime=True)
        await file.seek(0)  # Reset file pointer after reading
        return detected_mime

    async def ensure_store_exists(self) -> str:
        if self.file_search_store_name is None:
            store_display_name = f"project_store_{user_uuid}"
            store = await self.client.file_search_stores.create(
                config={'display_name': store_display_name}
            )
            self.file_search_store_name = store.name

        return self.file_search_store_name

    async def store_project_files(self, file: UploadFile, mime_type: str) -> None:

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
        """Upload files to the file search store and return the store name."""
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
        results = []
        for file_info in project_files:
            result = await self.search_individual_file(query, file_info)
            if result:
                results.append(result)

        return results

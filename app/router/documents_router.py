from fastapi import APIRouter, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from google.genai import Client, types

from app.common.constants import PROJECT_FILE_STORE, user_uuid
from app.common.settings import settings
from services.documents_services import DocumentsService

router = APIRouter(
    prefix="/documents",
    tags=["documents"],
)

client = Client(api_key=settings.gemini_api_key).aio
documents_service = DocumentsService(client)

@router.post("/brief")
async def generate_brief(files: list[UploadFile]):
    """
    Generate a concise brief summary of uploaded documents using Gemini AI.
    
    This endpoint accepts multiple document files, validates them, uploads them to 
    a Gemini file search store, and generates an AI-powered summary of their contents.
    
    **Supported file types:** PDF, DOCX, TXT, DOC, MD
    
    **Maximum file size:** 15 MB per file
    
    Args:
        files: List of files to upload and analyze. At least one file is required.
    
    Returns:
        JSONResponse: A JSON object containing:
            - project_id (str): Unique identifier for this project/user session
            - store_name (str): Gemini file search store identifier
            - brief (str): AI-generated summary of the uploaded documents
    
    Raises:
        HTTPException 400: No files uploaded or invalid file name
        HTTPException 413: File size exceeds maximum allowed (15 MB)
        HTTPException 415: Unsupported file type or MIME type
    """
    await documents_service.validate_documents(files)
    store_name = await documents_service.upload_files_to_store()
    file_names = [f["filename"] for f in PROJECT_FILE_STORE.get(user_uuid, [])]
    prompt = f"Provide a concise brief for the following documents: {', '.join(file_names)}"

    response = await client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            tools=[
                types.Tool(
                    file_search=types.FileSearch(
                        file_search_store_names=[store_name]
                    )
                )
            ]
        )
    )

    return JSONResponse(content={
        "project_id": user_uuid,
        "store_name": store_name,
        "brief": response.text
    })

@router.post("/search")
async def search_store(query: str, project_id: str = user_uuid):
    """
    Search across uploaded documents using natural language queries.
    
    This endpoint allows you to search through previously uploaded documents
    using Gemini AI's semantic search capabilities. It searches all documents
    associated with a project ID and returns relevant snippets.
    
    Args:
        query: Natural language search query (e.g., "What are the key findings?").
               Cannot be empty.
        project_id: Optional project identifier. Defaults to current user session.
                    Use the project_id returned from the /brief endpoint.
    
    Returns:
        JSONResponse: A JSON object containing:
            - results (list): List of search results, each containing:
                - filename (str): Name of the document
                - snippet (str): Relevant excerpt or AI-generated answer
    
    Raises:
        HTTPException 400: Query parameter is empty or project_id is invalid
        HTTPException 404: No files found for the given project_id
        HTTPException 500: Error during search operation
    """
    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    if not project_id:
        raise HTTPException(status_code=400, detail="Project ID is required")
    if not PROJECT_FILE_STORE.get(project_id):
        raise HTTPException(status_code=404, detail="No files found for the given project ID")

    try:
        project_files = PROJECT_FILE_STORE[project_id]
        results = await documents_service.search_all_user_files(query, project_files)
        return JSONResponse(content={"results": results})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during search: {str(e)}") from e

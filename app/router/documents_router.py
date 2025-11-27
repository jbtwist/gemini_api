from fastapi import APIRouter, UploadFile
from fastapi.responses import JSONResponse
from google.genai import Client, types

from app.common.constants import PROJECT_FILE_STORE, user_uuid
from app.common.settings import settings
from services.brief_services import BriefService

router = APIRouter(
    prefix="/documents",
    tags=["documents"],
)

client = Client(api_key=settings.gemini_api_key).aio
brief_service = BriefService(client)

@router.post("/brief")
async def generate_brief(files: list[UploadFile]):

    await brief_service.validate_documents(files)
    store_name = await brief_service.upload_files_to_store()
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

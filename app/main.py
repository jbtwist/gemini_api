from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.router.documents_router import router as documents_router

app = FastAPI(
    title="The Agile Monkeys Assessment API",
    description="Gemini API integration with FastAPI for document briefing generation",
    version="1.0.0"
)

# No CORS policy, not the purpose of this assessment
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    documents_router,
    prefix="/documents",
    tags=["documents"],
)

@app.get("/")
async def root():
    """
    Root endpoint that returns a welcome message.
    
    Returns:
        dict: Welcome message and API information.
    """
    return {"message": "Welcome to the Agile Monkeys Assessment API"}


@app.get("/health")
async def health_check():
    """
    Health check endpoint to verify the API is running.
    
    This endpoint is useful for monitoring, load balancers, and container
    orchestration systems to verify service availability.
    
    Returns:
        dict: Health status of the service.
    """
    return {"status": "healthy"}

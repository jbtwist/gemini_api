from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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

@app.get("/")
async def root():
    return {"message": "Welcome to the Agile Monkeys Assessment API"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}

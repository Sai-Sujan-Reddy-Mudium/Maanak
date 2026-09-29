from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.chat import router as chat_router

app = FastAPI(
    title="Maanak API",
    description="Resilient AI RAG API Backend for Compliance & Standards Intelligence",
    version="1.0.0"
)

# --- CORS MIDDLEWARE CONFIGURATION ---
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- HEALTH CHECK ENDPOINT ---
@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint for Docker container health monitoring and cloud load balancers.
    """
    return {"status": "healthy", "service": "Maanak API"}

# --- ROUTER REGISTRATION ---
app.include_router(chat_router, prefix="/api/v1", tags=["Chat"])
import sys
import os

# Inject DataIngestion globally so rag_engine is resolvable everywhere
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
data_ingestion_path = os.path.join(BASE_DIR, "DataIngestion")
if data_ingestion_path not in sys.path:
    sys.path.append(data_ingestion_path)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.api.v1.chat import router as chat_router
from rag_engine.retrieval.retriever import load_resources

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("[Main] Initializing pre-loaded models (SentenceTransformer, CrossEncoder, Pinecone)...")
    load_resources()
    yield
    print("[Main] Shutting down.")

app = FastAPI(
    title="Maanak API",
    description="Resilient AI RAG API Backend for Compliance & Standards Intelligence",
    version="1.0.0",
    lifespan=lifespan
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
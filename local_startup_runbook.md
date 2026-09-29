# Local Startup Runbook (Windows PowerShell)

Follow these exact steps inside your VS Code PowerShell terminal to initialize the complete Maanak system.

## 1. System Dependencies (Windows/PowerShell)
The `DataIngestion` module's PDF parser (`pymupdf4llm`) requires the Tesseract OCR binary to be installed on your host OS.

```powershell
# 1. Install Tesseract OCR via Windows Package Manager
winget install -e --id UB-Mannheim.TesseractOCR

# 2. Add to your current session's PATH (or restart VS Code)
$env:Path += ";C:\Program Files\Tesseract-OCR"
```

## 2. Environment Variables & Secrets
The entire system shares a unified configuration file at the **root** of the repository.

```powershell
# Ensure you are at the repository root
cd D:\Projects\Maanak

# Copy the provided template to create your active .env
Copy-Item .env.example .env
```
Open the newly created `.env` file and populate the keys by visiting the following third-party dashboards:
* **Supabase** (`SUPABASE_URL`, `SUPABASE_KEY`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`): Obtain from your Supabase project settings.
* **Pinecone** (`PINECONE_API_KEY`): Create a serverless index named `bis-maanak-index` (dimension 384) at [app.pinecone.io](https://app.pinecone.io).
* **OpenRouter** (`OPENROUTER_API_KEY`): Generate an API key for LLM translation and generation at [openrouter.ai](https://openrouter.ai).
* **ElevenLabs** (`ELEVENLABS_API_KEY`): Obtain for TTS generation at [elevenlabs.io](https://elevenlabs.io).

## 3. Backend Setup (Python / FastAPI)
The backend orchestrates the REST APIs, vector retrieval, and LLM streaming from the root.

```powershell
# Create a Python virtual environment
python -m venv venv

# Activate the virtual environment in PowerShell
.\venv\Scripts\Activate.ps1

# Install root dependencies
pip install -r requirements.txt

# Install Data Ingestion specific dependencies
pip install -r DataIngestion\requirements.txt

# Start the Uvicorn server (This will trigger the `lifespan` model loading)
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## 4. Frontend Setup (Node / Next.js)
Open a **second** VS Code PowerShell terminal window (`Ctrl+Shift+\``) to run the Next.js server alongside the backend.

```powershell
# Navigate to the frontend directory
cd D:\Projects\Maanak\Frontend

# Install Node modules
npm install

# Start the Next.js development server
npm run dev
```

## 5. Verification (Sanity Checks)
Open a **third** PowerShell terminal to run these backend health checks. 

```powershell
# 1. Test Backend Health Status
Invoke-RestMethod -Uri "http://localhost:8000/health" -Method Get

# 2. Test the RAG Streaming Engine (Simulated Request)
$body = @{
    input_type = "text"
    data = "What are the laptop safety standards?"
    source_lang = "en"
    session_id = "test-session-123"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/v1/chat/stream" -Method Post -Body $body -Headers @{"Content-Type"="application/json"}
```

**Final Verification**: Open your browser and navigate to **`http://localhost:3000`** to interact with the full frontend application!

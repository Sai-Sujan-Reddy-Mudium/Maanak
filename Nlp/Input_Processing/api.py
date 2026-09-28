import sys
import os
import json
import base64
import requests
import asyncio
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from dotenv import load_dotenv
import uvicorn

load_dotenv()

# Inject RAG_LLM_Processing to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
try:
    from RAG_LLM_Processing.rag_engine import RAGEngine
except Exception as e:
    print(f"Error importing RAGEngine: {e}")
    RAGEngine = None

app = FastAPI(title="Maanak Gateway (Input/Output Domain)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class FrontendRequest(BaseModel):
    input_type: str
    data: str
    source_lang: str
    session_id: str

class TTSRequest(BaseModel):
    text: str
    target_lang: str

def bhashini_asr(audio_base64: str, source_lang: str) -> str:
    print(f"[Bhashini ASR] Audio -> Text ({source_lang})")
    if source_lang == 'te': return "నాకు లాప్టాప్ గురించి కావాలి"
    if source_lang == 'hi': return "मुझे लैपटॉप के बारे में चाहिए"
    return "I need information about laptops"

def bhashini_translate(text: str, source_lang: str, target_lang: str) -> str:
    """Uses GPT-4o-mini exclusively for translation as requested."""
    if source_lang == target_lang: return text
    print(f"[LLM NMT] Translating {source_lang} -> {target_lang} using GPT-4o-mini...")
    
    api_key = os.getenv("OPENROUTER_API_KEY", "")
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    
    # Simple prompt to ensure pure translation
    system_msg = f"You are a professional translator. Translate the following text from ISO language code '{source_lang}' into ISO language code '{target_lang}'. Output ONLY the translated text, nothing else, no quotes, no explanations."
    
    payload = {
        "model": "openai/gpt-4o-mini",
        "messages": [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": text}
        ],
        "stream": False
    }
    
    try:
        resp = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=20.0)
        return resp.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"GPT-4 Translation Error: {e}")
        return text

def bhashini_tts(text: str, target_lang: str) -> str:
    print(f"[Bhashini TTS] Text -> Audio ({target_lang})")
    api_key = os.getenv("ELEVENLABS_API_KEY", "")
    url = "https://api.elevenlabs.io/v1/text-to-speech/EXAVITQu4vr4xnSDxMaL"
    headers = {"Accept": "audio/mpeg", "Content-Type": "application/json", "xi-api-key": api_key}
    data = {"text": text, "model_id": "eleven_multilingual_v2"}
    try:
        resp = requests.post(url, json=data, headers=headers)
        if resp.status_code == 200:
            return base64.b64encode(resp.content).decode('utf-8')
    except Exception as e:
        print(f"TTS Error: {e}")
    return ""

@app.post("/api/gateway/chat/stream")
async def chat_stream_endpoint(request: FrontendRequest):
    if RAGEngine is None:
        raise HTTPException(status_code=500, detail="RAGEngine not found.")

    native_text = request.data
    if request.input_type == "audio":
        native_text = bhashini_asr(request.data, request.source_lang)
    
    english_query = bhashini_translate(native_text, request.source_lang, 'en')
    
    async def sse_generator():
        engine = RAGEngine()
        if request.source_lang == 'en':
            async for token_event in engine.generate_response(english_query, []):
                yield token_event
        else:
            print("[Gateway] Collecting English stream for translation...")
            full_english_text = ""
            citations_metadata = []
            
            async for token_event in engine.generate_response(english_query, []):
                if token_event.startswith("event: token"):
                    data_str = token_event.split("data: ")[1].strip()
                    full_english_text += json.loads(data_str).get("text", "")
                elif token_event.startswith("event: metadata"):
                    data_str = token_event.split("data: ")[1].strip()
                    citations_metadata = json.loads(data_str).get("citations", [])
                    
            translated_text = bhashini_translate(full_english_text, 'en', request.source_lang)
            
            words = translated_text.split(" ")
            for word in words:
                await asyncio.sleep(0.05)
                yield f"event: token\ndata: {json.dumps({'text': word + ' '})}\n\n"
                
            if citations_metadata:
                yield f"event: metadata\ndata: {json.dumps({'citations': citations_metadata})}\n\n"
                
            yield f"event: done\ndata: {{}}\n\n"

    return StreamingResponse(sse_generator(), media_type="text/event-stream")

@app.post("/api/gateway/tts")
async def tts_endpoint(request: TTSRequest):
    audio_base64 = bhashini_tts(request.text, request.target_lang)
    return JSONResponse(content={"audio_base64": audio_base64})

if __name__ == "__main__":
    print("Starting Gateway Server on http://0.0.0.0:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)

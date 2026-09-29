from fastapi import APIRouter, Request, Depends
from fastapi.responses import StreamingResponse, JSONResponse
import json
import asyncio
import os
import sys

from app.models.chat import ChatRequest, TTSRequest
from app.core.security import verify_user_role
from app.db.tasks import log_chat_to_db, get_chat_history_from_db

# Wire in Dev 2 NLP functions by appending to path (avoiding insert(0) which overshadows root app)
nlp_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../NLP"))
if nlp_path not in sys.path:
    sys.path.append(nlp_path)

from Nlp.Input_Processing.api import bhashini_asr, bhashini_translate, bhashini_tts
from Nlp.RAG_LLM_Processing.rag_engine import RAGEngine

router = APIRouter()

@router.post("/chat/stream")
async def chat_stream_endpoint(request: ChatRequest, req: Request):
    user_role = req.headers.get("X-User-Role", "citizen")
    
    # DB multi-turn session handling
    db_history = get_chat_history_from_db(request.session_id)
    full_history = list(db_history)

    # Process Multi-Modal/Multi-Lingual Input
    native_text = request.data
    if request.input_type == "audio":
        native_text = bhashini_asr(request.data, request.source_lang)
    english_query = bhashini_translate(native_text, request.source_lang, 'en')

    engine = RAGEngine()

    async def sse_generator():
        final_text = ""
        final_citations = []
        
        if request.source_lang == 'en':
            async for token_event in engine.generate_response(english_query, full_history, user_role):
                if token_event.startswith("event: token"):
                    try:
                        data_str = token_event.split("data: ")[1].strip()
                        final_text += json.loads(data_str).get("text", "")
                    except:
                        pass
                elif token_event.startswith("event: metadata"):
                    try:
                        data_str = token_event.split("data: ")[1].strip()
                        final_citations = json.loads(data_str).get("citations", [])
                    except:
                        pass
                yield token_event
        else:
            print("[Gateway] Buffering English stream for translation...")
            async for token_event in engine.generate_response(english_query, full_history, user_role):
                if token_event.startswith("event: token"):
                    try:
                        data_str = token_event.split("data: ")[1].strip()
                        final_text += json.loads(data_str).get("text", "")
                    except:
                        pass
                elif token_event.startswith("event: metadata"):
                    try:
                        data_str = token_event.split("data: ")[1].strip()
                        final_citations = json.loads(data_str).get("citations", [])
                    except:
                        pass
                    
            translated_text = bhashini_translate(final_text, 'en', request.source_lang)
            for word in translated_text.split(" "):
                await asyncio.sleep(0.02)
                yield f"event: token\ndata: {json.dumps({'text': word + ' '})}\n\n"
                
            if final_citations:
                yield f"event: metadata\ndata: {json.dumps({'citations': final_citations})}\n\n"
            yield f"event: done\ndata: {{}}\n\n"
            final_text = translated_text
            
        # Post-completion DB Log
        asyncio.create_task(
            log_chat_to_db(
                session_id=request.session_id,
                query=native_text,
                response=final_text,
                citations=final_citations,
                role=user_role
            )
        )

    return StreamingResponse(sse_generator(), media_type="text/event-stream")

@router.post("/tts")
async def tts_endpoint(request: TTSRequest):
    audio_base64 = bhashini_tts(request.text, request.target_lang)
    return JSONResponse(content={"audio_base64": audio_base64})

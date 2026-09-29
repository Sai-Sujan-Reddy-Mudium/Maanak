from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from starlette.background import BackgroundTask

from app.models.chat import ChatRequest
from app.core.security import verify_user_role
from app.services.rag import dummy_rag_generator
from app.db.tasks import log_chat_to_db, get_chat_history_from_db

router = APIRouter()

@router.post("/chat")
async def chat_endpoint(request: ChatRequest, user_role: str = Depends(verify_user_role)):
    """
    Chat endpoint providing streaming SSE responses with background DB logging, multi-turn session history retrieval, and failover protection.
    """
    # Step 1: Retrieve multi-turn conversation memory from Supabase for this session_id
    db_history = get_chat_history_from_db(request.session_id)
    
    # Step 2: Combine with request chat_history if provided by client
    full_history = list(db_history)
    if request.chat_history:
        for msg in request.chat_history:
            full_history.append({"role": msg.role, "content": msg.content})

    fake_full_response = f"Here is the answer to: '{request.query}'."
    fake_citations = {"is_number": "IS 16046"}
    
    # Step 3: Configure non-blocking background DB log task with role and session metadata
    save_task = BackgroundTask(
        log_chat_to_db, 
        session_id=request.session_id, 
        query=request.query, 
        response=fake_full_response, 
        citations=fake_citations,
        role=user_role
    )
    
    # Step 4: Stream real-time SSE response passing full session history and user_role to RAG engine
    return StreamingResponse(
        dummy_rag_generator(
            query=request.query, 
            chat_history=full_history, 
            user_role=user_role
        ),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
        background=save_task
    )

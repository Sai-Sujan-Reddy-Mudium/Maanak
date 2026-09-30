from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from starlette.background import BackgroundTask

from app.models.chat import ChatRequest
from app.core.security import verify_user_role
from app.services.rag import dummy_rag_generator
from app.db.tasks import log_chat_to_db

router = APIRouter()

@router.post("/chat")
async def chat_endpoint(request: ChatRequest, user_role: str = Depends(verify_user_role)):
    """
    Chat endpoint providing streaming SSE responses with background DB logging and failover protection.
    """
    fake_full_response = f"Here is the answer to: '{request.query}'."
    fake_citations = {"is_number": "IS 16046"}
    
    save_task = BackgroundTask(
        log_chat_to_db, 
        session_id=request.session_id, 
        query=request.query, 
        response=fake_full_response, 
        citations=fake_citations
    )
    
    return StreamingResponse(
        dummy_rag_generator(query=request.query),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
        background=save_task
    )

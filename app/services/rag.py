import asyncio
import json
from typing import List, Dict
from app.core.resilience import with_failover

@with_failover
async def dummy_rag_generator(
    query: str, 
    chat_history: List[Dict[str, str]] = None, 
    user_role: str = "user", 
    current_key: str = None
):
    """
    Simulated RAG LLM Generator protected by @with_failover decorator.
    Accepts full multi-turn conversation history retrieved from Supabase and current role context.
    """
    if current_key in ["key1", "key2"]:
        await asyncio.sleep(0.2)
        raise Exception(f"HTTP 429: Rate Limit Exceeded on {current_key}")

    history_count = len(chat_history) if chat_history else 0
    print(f"\n[RAG ENGINE] Processing query for role '{user_role}' with {history_count} previous messages in context.")

    # Success scenario (key3)
    await asyncio.sleep(0.3) 
    meta_chunk = {"type": "metadata", "citations": [{"is_number": "IS 16046", "clause": "5.2"}]}
    yield f"data: {json.dumps(meta_chunk)}\n\n"

    fake_response = f"Using {current_key} (Role: {user_role}, History Turns: {history_count}). Answer for: '{query}'."
    for word in fake_response.split(" "):
        await asyncio.sleep(0.08) 
        token_chunk = {"type": "token", "content": word + " "}
        yield f"data: {json.dumps(token_chunk)}\n\n"

    yield "data: [DONE]\n\n"

import asyncio
import json
from app.core.resilience import with_failover

@with_failover
async def dummy_rag_generator(query: str, current_key: str = None):
    """
    Simulated RAG LLM Generator protected by @with_failover decorator.
    """
    if current_key in ["key1", "key2"]:
        await asyncio.sleep(0.2)
        raise Exception(f"HTTP 429: Rate Limit Exceeded on {current_key}")

    # Success scenario (key3)
    await asyncio.sleep(0.5) 
    meta_chunk = {"type": "metadata", "citations": [{"is_number": "IS 16046", "clause": "5.2"}]}
    yield f"data: {json.dumps(meta_chunk)}\n\n"

    fake_response = f"Using {current_key}. Here is the answer to: '{query}'."
    for word in fake_response.split(" "):
        await asyncio.sleep(0.1) 
        token_chunk = {"type": "token", "content": word + " "}
        yield f"data: {json.dumps(token_chunk)}\n\n"

    yield "data: [DONE]\n\n"

import json
import os
import httpx
from typing import AsyncGenerator
from dotenv import load_dotenv

load_dotenv()

async def generate_strict_response(condensed_query: str, retrieved_chunks: list[dict], role: str) -> AsyncGenerator[str, None]:
    """
    Component 3: Guardrailed Generation & Prompt Engineering
    Injects retrieved chunks into a system prompt that bans speculation
    and forces strict citation tags. Streams the output using OpenRouter.
    """
    api_key = os.getenv("OPENROUTER_API_KEY", "")
    
    # 1. Build the strict context block
    if retrieved_chunks:
        context_text = "\n\n".join([
            f"--- Chunk from {chunk.get('is_number', 'Unknown')}, Clause {chunk.get('clause_no', 'Unknown')} ---\n{chunk.get('chunk_text', '')}"
            for chunk in retrieved_chunks
        ])
    else:
        context_text = "No relevant documents found in the database."
    
    system_prompt = f"""You are MAANAK, an expert sovereign AI compliance assistant for the Bureau of Indian Standards (BIS). 
You answer strictly using the provided context chunks.

RULES:
1. If the answer cannot be found in the context, explicitly state: 'This information is not currently available in the MVP database. Please check manakonline.in'.
2. Every factual claim, requirement, or rule must include an explicit citation tag pointing to the source in this exact format: [IS Number -> Clause Number].
3. Do not invent clause numbers or speculate.
4. Adapt your tone to the user role: {role}

CONTEXT:
{context_text}
"""

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "openai/gpt-4o-mini",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": condensed_query}
        ],
        "stream": True
    }
    
    print("[Generator] Starting real LLM Stream via OpenRouter...")
    
    async with httpx.AsyncClient() as client:
        try:
            async with client.stream("POST", "https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=60.0) as response:
                response.raise_for_status()
                async for chunk in response.aiter_lines():
                    if chunk.startswith("data: "):
                        data_str = chunk.replace("data: ", "").strip()
                        if data_str == "[DONE]":
                            break
                        try:
                            data_json = json.loads(data_str)
                            if "choices" in data_json and len(data_json["choices"]) > 0:
                                delta = data_json["choices"][0].get("delta", {})
                                if "content" in delta:
                                    token = delta["content"]
                                    yield f"event: token\ndata: {json.dumps({'text': token})}\n\n"
                        except Exception as e:
                            print(f"[Generator] JSON Parse Error on stream chunk: {e}")
        except Exception as e:
            print(f"[Generator Error] HTTP Error: {e}")
            yield f"event: token\ndata: {json.dumps({'text': 'Error connecting to LLM provider.'})}\n\n"
            
    # At the end of the stream, yield the metadata/citations
    citations_metadata = [
        {"is_number": chunk.get("is_number", "Unknown"), "clause": chunk.get("clause_no", "Unknown")}
        for chunk in retrieved_chunks
    ]
    
    yield f"event: metadata\ndata: {json.dumps({'citations': citations_metadata})}\n\n"
    yield f"event: done\ndata: {{}}\n\n"

import asyncio
import httpx
import os
import json
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("OPENROUTER_API_KEY", "")

async def test_llm():
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:8000",
        "X-Title": "Maanak Project"
    }
    payload = {
        "model": "openai/gpt-4o-mini",
        "messages": [{"role": "user", "content": "hello"}],
    }
    async with httpx.AsyncClient() as client:
        response = await client.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=60.0)
        print("Status code:", response.status_code)
        print("Response text:", response.text)

asyncio.run(test_llm())

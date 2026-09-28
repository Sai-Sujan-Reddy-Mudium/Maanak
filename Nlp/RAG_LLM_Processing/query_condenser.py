import os
import requests
from dotenv import load_dotenv

load_dotenv()

def condense_query(query: str, chat_history: list[dict]) -> str:
    """
    Component 1: Conversational Query Condenser
    Takes recent chat history and latest user query, resolving pronouns
    and expanding trade terms into formal BIS terminology.
    """
    api_key = os.getenv("OPENROUTER_API_KEY", "")
    
    system_prompt = (
        "Given the following conversation history and a latest user query, "
        "rewrite the query to be a fully standalone technical question. "
        "If the user uses colloquial or trade terms, map them to official Indian Standards terms. "
        "Output ONLY the rewritten query string."
    )
    
    # Construct conversation for the LLM
    messages = [{"role": "system", "content": system_prompt}]
    for msg in chat_history:
        messages.append({"role": msg.get("role", "user"), "content": msg.get("content", "")})
    messages.append({"role": "user", "content": query})
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "openai/gpt-4o-mini",
        "messages": messages,
        "stream": False
    }
    
    print("[Query Condenser] Calling OpenRouter to condense query...")
    try:
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=20.0)
        response.raise_for_status()
        data = response.json()
        standalone_query = data["choices"][0]["message"]["content"].strip()
        print(f"[Query Condenser] Result: {standalone_query}")
        return standalone_query
    except Exception as e:
        print(f"[Query Condenser] Error: {e}. Falling back to raw query.")
        return query


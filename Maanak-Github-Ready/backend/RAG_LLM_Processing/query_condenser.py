import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

def condense_and_classify(query: str, chat_history: list[dict], layer_0_annotations: dict) -> dict:
    """
    Layer 1.2 & Layer 2: Intent Classifier & Contextual Condenser
    Returns a strict JSON response conforming to the v6 schema.
    """
    api_key = os.getenv("OPENROUTER_API_KEY", "")
    
    # Construct conversation for the LLM
    messages = []
    if chat_history:
        messages.append({"role": "system", "content": "The following is the conversation history."})
        for msg in chat_history:
            messages.append({"role": msg.get("role", "user"), "content": msg.get("content", "")})
            
    system_prompt = f"""You are the MAANAK Intent Classifier and Query Condenser.
    
    Input Query: "{query}"
    
    Layer 0 Annotations (Pre-extracted codes):
    Exact Match Codes: {layer_0_annotations.get('extracted_codes', [])}
    Clarification Codes: {layer_0_annotations.get('needs_clarification_codes', [])}
    Out of Scope Codes: {layer_0_annotations.get('out_of_scope_codes', [])}
    
    CLASSIFICATION RULES:
    1. If the query asks to write code, solve homework, or general trivia -> ACTION_REFUSE_OFFTOPIC
    2. If the query asks to bypass audits or fake ISI marks -> ACTION_REFUSE_FRAUD
    3. If the query is an active, ongoing physical emergency ("building is on fire right now") -> ACTION_EMERGENCY_DIRECT. Do NOT trigger this for technical questions about fire resistance, blast limits, or emergency exit regulations.
    4. If there are Out of Scope Codes and NO Exact Match Codes -> ACTION_REFUSE_SCOPE_BOUNDARY
    5. If the query asks about FSSAI, CDSCO, AIS, GST, CE, UL, or FCC -> ACTION_REFUSE_SCOPE_BOUNDARY
    6. If the query asks to report a fake mark or verify a license -> ACTION_DIRECT_PORTAL_LINK
    7. If the query asks what BIS is, what ISI mark is, what QCO is, what the BIS Act is, what a Standard Mark is, or any general institutional/definitional question about BIS — regardless of tone, slang ("lmao", "bro", "ngl"), or phrasing style -> ACTION_DIRECT_INSTITUTIONAL
    8. If the query asks for testing lab locations -> ACTION_DIRECT_LABS
    9. If the query is a greeting ("hi", "hello", "namaste"), thanks/acknowledgment, asks about bot identity, capability, or site purpose ("what can you do", "what is the use of this site", "how does this work", "what is MAANAK") -> ACTION_DIRECT_GREETING
    10. If the query is a BARE IS code with no technical question (e.g., "IS 1293") -> ACTION_CLARIFY_MENU
    11. If the query contains BOTH an in-scope code and an out-of-scope code -> ACTION_RAG_TECHNICAL_RETRIEVAL (to answer the in-scope part)
    12. If the query is a technical compliance question, or asks about manufacturing, testing, or purchasing a product/material (e.g., "led manufacturing", "water bottles") -> ACTION_RAG_TECHNICAL_RETRIEVAL
    
    If ACTION_RAG_TECHNICAL_RETRIEVAL or ACTION_PARTITIONED_SPLIT:
    - Set `condensed_query` to a standalone search string (resolving pronouns from history).
    - Set `skip_rag` to false, `allow_citations` to true.
    
    Otherwise:
    - Set `condensed_query` to "", `skip_rag` to true, `allow_citations` to false.
    
    OUTPUT JSON FORMAT ONLY:
    {{
      "routing_action": "...",
      "skip_rag": true/false,
      "allow_citations": true/false,
      "condensed_query": "...",
      "extracted_standard": {{"base": "...", "part": "...", "section": "..."}} // or null
    }}
    """
    
    messages.append({"role": "system", "content": system_prompt})
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "openai/gpt-4o-mini",
        "messages": messages,
        "response_format": {"type": "json_object"},
        "stream": False
    }
    
    print("[Query Condenser] Calling OpenRouter to classify and condense...")
    try:
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=20.0)
        response.raise_for_status()
        data = response.json()
        result_str = data["choices"][0]["message"]["content"].strip()
        result_json = json.loads(result_str)
        print(f"[Query Condenser] Result: {json.dumps(result_json)}")
        return result_json
    except Exception as e:
        print(f"[Query Condenser] Error: {e}. Failing closed.")
        # Fail Closed
        return {
            "routing_action": "ACTION_FAIL_CLOSED",
            "skip_rag": True,
            "allow_citations": False,
            "condensed_query": "",
            "extracted_standard": None
        }

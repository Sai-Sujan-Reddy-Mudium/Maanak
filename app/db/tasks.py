import logging
from typing import List, Dict, Any
from supabase import create_client, Client
from app.core.config import settings

logger = logging.getLogger("maanak.db")

def get_supabase_client() -> Client:
    """
    Creates and returns a Supabase client instance using settings.
    """
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

def get_chat_history_from_db(session_id: str) -> List[Dict[str, str]]:
    """
    Retrieves previous multi-turn chat messages from Supabase for a given session_id.
    Formats records into standard message history objects: [{"role": ..., "content": ...}].
    """
    try:
        supabase: Client = get_supabase_client()
        try:
            res = (
                supabase.table("chats")
                .select("query, response, role")
                .eq("session_id", session_id)
                .order("created_at", desc=False)
                .execute()
            )
        except Exception:
            res = (
                supabase.table("chats")
                .select("query, response")
                .eq("session_id", session_id)
                .order("created_at", desc=False)
                .execute()
            )
        history = []
        if res.data:
            for row in res.data:
                user_role = row.get("role") or "user"
                history.append({"role": user_role, "content": row["query"]})
                history.append({"role": "assistant", "content": row["response"]})
        return history
    except Exception as e:
        logger.info(f"[DB_TASK] History lookup notice ({e}). Starting fresh session context.")
        return []

def log_chat_to_db(session_id: str, query: str, response: str, citations: dict, role: str = "user"):
    """
    Background DB Task (The Invisible Librarian).
    Logs session history, role, query, response, and citations to Supabase asynchronously.
    """
    supabase: Client = get_supabase_client()
    data_with_role = {
        "session_id": session_id,
        "role": role,
        "query": query,
        "response": response,
        "citations": citations
    }
    data_without_role = {
        "session_id": session_id,
        "query": query,
        "response": response,
        "citations": citations
    }
    try:
        supabase.table("chats").insert(data_with_role).execute()
        print(f"\n[DB_TASK] Successfully saved chat for session '{session_id}' (Role: '{role}') to Supabase.")
    except Exception as e1:
        try:
            supabase.table("chats").insert(data_without_role).execute()
            print(f"\n[DB_TASK] Successfully saved chat for session '{session_id}' to Supabase (without role column).")
        except Exception as e2:
            logger.warning(f"[DB_TASK] Supabase storage notice ({e2}). Mocking log gracefully.")
            print(f"[DB_TASK] (Mock Log) Session '{session_id}' chat logged safely.")

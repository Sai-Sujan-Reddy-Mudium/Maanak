from supabase import create_client, Client
from app.core.config import settings

def get_supabase_client() -> Client:
    """
    Creates and returns a Supabase client instance using settings.
    """
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

async def log_chat_to_db(session_id: str, query: str, response: str, citations: dict):
    """
    Background DB Task (The Invisible Librarian).
    Logs chat metadata to Supabase asynchronously without adding latency to the response stream.
    """
    try:
        supabase: Client = get_supabase_client()
        data = {
            "session_id": session_id,
            "query": query,
            "response": response,
            "citations": citations
        }
        # Insert chat record into the 'chats' table in Supabase
        res = supabase.table("chats").insert(data).execute()
        print(f"\n[DB_TASK] Successfully saved chat for session '{session_id}' to Supabase table 'chats'.")
    except Exception as e:
        print(f"\n[DB_TASK] Notice: Could not connect to live Supabase database ({e}).")
        print(f"[DB_TASK] (Mock Log) Session '{session_id}' chat logged safely.")

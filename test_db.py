import os
from app.core.config import settings
from app.db.tasks import log_chat_to_db, get_chat_history_from_db

def test_supabase_connection():
    # 1. Load settings via existing Pydantic config
    supabase_url = settings.SUPABASE_URL
    supabase_key = settings.SUPABASE_KEY
    
    if not supabase_url or not supabase_key or supabase_url == "https://placeholder.supabase.co":
        print("[Error] Valid SUPABASE_URL and SUPABASE_KEY must be set in .env")
        return
        
    print(f"[Success] Loaded Supabase configuration connecting to: {supabase_url}")
    
    test_session = "test_orchestration_session_001"
    
    # 2. Test Write Operation
    print("\n--- Testing DB Write (log_chat_to_db) ---")
    try:
        # Note: calling this synchronously here, which proves it works as a standard function
        log_chat_to_db(
            session_id=test_session,
            query="Infrastructure test query to verify Supabase.",
            response="This is a verified test response from the backend orchestration layer.",
            citations=[{"source": "test_architecture.pdf", "page": 1}],
            role="tester"
        )
        print("[Success] log_chat_to_db execution completed.")
    except Exception as e:
        print(f"[Error] Failed to write to DB: {e}")
        return
        
    # 3. Test Read Operation
    print("\n--- Testing DB Read (get_chat_history_from_db) ---")
    try:
        history = get_chat_history_from_db(test_session)
        if history:
            print(f"[Success] Successfully fetched history. Found {len(history)} messages.")
            for msg in history:
                print(f"   [{msg.get('role').upper()}] {msg.get('content')}")
        else:
            print("[Warning] Fetch succeeded but returned empty history. Verify that the 'chats' table exists and matches expected schema.")
    except Exception as e:
        print(f"[Error] Failed to read from DB: {e}")

if __name__ == "__main__":
    test_supabase_connection()

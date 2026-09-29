# System Integration Analysis Report

## 1. Execution Entry Points

### Primary Server Entry Point
- **Runtime**: ASGI Web Application (FastAPI / Starlette) executed via Uvicorn.
- **Entry File**: [main.py](file:///d:/Projects/Maanak/main.py#L1-L32)
- **App Instance Symbol**: `main:app`

#### Invocation Commands
- **Local / Virtualenv Execution**:
  ```powershell
  uvicorn main:app --host 0.0.0.0 --port 8000 --reload
  ```
- **Container / Production Execution**:
  ```dockerfile
  uvicorn main:app --host 0.0.0.0 --port 8000 --workers 2
  ```

### Key Function Signatures & Boundaries

1. **HTTP Controller Route**:
   - **Path**: `POST /api/v1/chat`
   - **File**: [app/api/v1/chat.py:L13](file:///d:/Projects/Maanak/app/api/v1/chat.py#L13)
   - **Signature**:
     ```python
     async def chat_endpoint(
         request: ChatRequest, 
         user_role: str = Depends(verify_user_role)
     ) -> StreamingResponse
     ```

2. **Security Gateway Dependency**:
   - **File**: [app/core/security.py:L3](file:///d:/Projects/Maanak/app/core/security.py#L3)
   - **Signature**:
     ```python
     def verify_user_role(
         x_user_role: str = Header(default=None, description="...")
     ) -> str
     ```

3. **Stream Service Generator**:
   - **File**: [app/services/rag.py:L5](file:///d:/Projects/Maanak/app/services/rag.py#L5)
   - **Signature**:
     ```python
     @with_failover
     async def dummy_rag_generator(
         query: str, 
         chat_history: List[Dict[str, str]] = None, 
         user_role: str = "user", 
         current_key: str = None
     ) -> AsyncGenerator[str, None]
     ```

4. **Background Persistence Task**:
   - **File**: [app/db/tasks.py:L41](file:///d:/Projects/Maanak/app/db/tasks.py#L41)
   - **Signature**:
     ```python
     def log_chat_to_db(
         session_id: str, 
         query: str, 
         response: str, 
         citations: dict, 
         role: str = "user"
     ) -> None
     ```

---

## 2. Hard Data Contracts (I/O)

### Inputs

#### HTTP Request Headers
- **`X-User-Role`** (Required): String enum. Strictly validated against `["user", "manufacturer"]`. Missing header returns HTTP 400; unauthorized string returns HTTP 403.

#### HTTP Request Payload (`POST /api/v1/chat`)
- **Content-Type**: `application/json`
- **Schema Model**: [ChatRequest](file:///d:/Projects/Maanak/app/models/chat.py#L8-L11)
- **JSON Structure**:
  ```json
  {
    "session_id": "string (min: 1, max: 255)",
    "query": "string (min: 1, max: 4000)",
    "chat_history": [
      {
        "role": "string (e.g. 'user' or 'assistant')",
        "content": "string (max: 10000)"
      }
    ]
  }
  ```

---

### Outputs

#### HTTP Response Contract
- **Status Code**: `200 OK`
- **Content-Type / Media-Type**: `text/event-stream`
- **Headers**:
  - `Cache-Control: no-cache`
  - `Connection: keep-alive`

#### Event Stream (SSE) Data Protocol
Emitted as sequential line-delimited SSE chunks:

1. **Metadata Chunk**:
   ```text
   data: {"type": "metadata", "citations": [{"is_number": "IS 16046", "clause": "5.2"}]}\n\n
   ```

2. **Token Chunks**:
   ```text
   data: {"type": "token", "content": "<token_string> "}\n\n
   ```

3. **Fallback Error Chunk** *(Triggered if all failover keys fail)*:
   ```text
   data: {"type": "token", "content": "System overloaded, please try again."}\n\n
   ```

4. **Completion Signal**:
   ```text
   data: [DONE]\n\n
   ```

---

## 3. Environmental Dependencies

### Required Environment Variables ([.env](file:///d:/Projects/Maanak/.env))
Defined and parsed via Pydantic `BaseSettings` in [app/core/config.py](file:///d:/Projects/Maanak/app/core/config.py):

| Variable Name | Type | Description / Format | Fallback Default |
| :--- | :--- | :--- | :--- |
| `SUPABASE_URL` | `str` | Fully qualified URL for Supabase PostgREST API (e.g., `https://<proj>.supabase.co`) | `"https://placeholder.supabase.co"` |
| `SUPABASE_KEY` | `str` | Supabase `anon` public key or `service_role` JWT token | `"placeholder_key"` |
| `OPENROUTER_KEYS` | `List[str]` | JSON array of API keys (e.g., `["key1", "key2", "key3"]`) | `["key1", "key2", "key3"]` |

### Infrastructure & Network Dependencies
- **Network Port**: `8000` (configurable via Uvicorn CLI `--port`).
- **External Database Engine**: Supabase (PostgreSQL with PostgREST REST API enabled).
- **Target Database Table**: `chats`
  - **Expected Columns**: `session_id` (TEXT), `query` (TEXT), `response` (TEXT), `citations` (JSONB), `role` (TEXT, optional fallback), `created_at` (TIMESTAMPTZ).

---

## 4. Integration Blockers & Hardcoded I/O

1. **Simulated LLM Generator**:
   - **Location**: [app/services/rag.py:L10-L24](file:///d:/Projects/Maanak/app/services/rag.py#L10-L24)
   - **Blocker**: `dummy_rag_generator` uses `asyncio.sleep()` delays and static string formatting (`fake_response = f"Using {current_key}..."`) rather than issuing HTTP requests to a real LLM provider (e.g., OpenRouter, OpenAI, or vLLM endpoint).

2. **Hardcoded Failover Trigger Condition**:
   - **Location**: [app/services/rag.py:L10-L12](file:///d:/Projects/Maanak/app/services/rag.py#L10-L12)
   - **Blocker**: `if current_key in ["key1", "key2"]:` intentionally raises `Exception("HTTP 429...")` to simulate key failure. Must be replaced with real HTTP status inspection (catching 429/5xx status codes) when integrating real API keys.

3. **Hardcoded Citations Payload**:
   - **Location**: [app/services/rag.py:L16](file:///d:/Projects/Maanak/app/services/rag.py#L16)
   - **Blocker**: Static JSON object `{"is_number": "IS 16046", "clause": "5.2"}` is emitted for every session regardless of query input.

4. **Hardcoded CORS Origins**:
   - **Location**: [main.py:L8-L11](file:///d:/Projects/Maanak/main.py#L8-L11)
   - **Blocker**: Allowed CORS origins list is fixed to `["http://localhost:3000", "http://127.0.0.1:3000"]`. Needs to be parameterized via `settings` to allow production domain origins in deployed environments.

5. **Silent Schema Fallback in Supabase Task**:
   - **Location**: [app/db/tasks.py:L57-L64](file:///d:/Projects/Maanak/app/db/tasks.py#L57-L64)
   - **Blocker**: If the `chats` table lacks the `role` column, `log_chat_to_db` catches the PostgREST error and retries without `role`. If Supabase is completely unreachable, errors are caught silently and logged to stdout (`(Mock Log)`).
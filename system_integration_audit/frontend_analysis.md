# System Integration Analysis Report: Frontend Module

This document provides a technical integration boundary analysis of the **Frontend** codebase located in `Frontend/`. It details execution entry points, hard data contracts, environmental dependencies, and integration blockers against external backend services.

---

## 1. Execution Entry Points

### Server Framework & Process Execution
- **Framework**: Next.js 16 (App Router) running on React 19.
- **Runtime Environment**: Node.js Web Server / SSR / Client CSR.
- **Execution Commands**:
  ```bash
  cd Frontend
  npm run dev       # Development Server (Default Port 3000)
  # OR
  npm run build && npm start  # Production Build & Start
  ```

### Key Application Routes & Source Filepaths
- **Home / Landing Page**: [Frontend/src/app/page.tsx](file:///d:/Projects/Maanak/Frontend/src/app/page.tsx)
- **Chat Consultation Engine**: [Frontend/src/app/chat/page.tsx](file:///d:/Projects/Maanak/Frontend/src/app/chat/page.tsx) ➔ [Frontend/src/components/chat/chat-shell.tsx](file:///d:/Projects/Maanak/Frontend/src/components/chat/chat-shell.tsx)
- **Labs Directory**: [Frontend/src/app/labs/page.tsx](file:///d:/Projects/Maanak/Frontend/src/app/labs/page.tsx)
- **Auditor Dashboard**: [Frontend/src/app/auditor-dashboard/page.tsx](file:///d:/Projects/Maanak/Frontend/src/app/auditor-dashboard/page.tsx)
- **Authentication Pages**: [Frontend/src/app/login/page.tsx](file:///d:/Projects/Maanak/Frontend/src/app/login/page.tsx), [Frontend/src/app/signup/page.tsx](file:///d:/Projects/Maanak/Frontend/src/app/signup/page.tsx)
- **OAuth Callback Route**: [Frontend/src/app/auth/callback/route.ts](file:///d:/Projects/Maanak/Frontend/src/app/auth/callback/route.ts)

---

## 2. Hard Data Contracts (I/O)

### A. Inputs (Data Expected by Frontend from External APIs)

1. **Chat SSE Stream Request** ([src/lib/sse.ts](file:///d:/Projects/Maanak/Frontend/src/lib/sse.ts#L130-L147)):
   - **Target Endpoint**: `POST ${NEXT_PUBLIC_FASTAPI_URL}/api/gateway/chat/stream`
   - **Headers**:
     - `Content-Type: application/json`
     - `Accept: text/event-stream`
     - `X-User-Role: "citizen" | "manufacturer" | "auditor"` (Optional)
   - **Body Contract**:
     ```json
     {
       "input_type": "text | audio",
       "data": "<string_query_or_raw_base64_audio>",
       "source_lang": "<language_code_eg_en_hi_te>",
       "session_id": "<uuid_string>"
     }
     ```

2. **Text-To-Speech (TTS) Request** ([src/lib/sse.ts](file:///d:/Projects/Maanak/Frontend/src/lib/sse.ts#L195-L228)):
   - **Target Endpoint**: `POST ${NEXT_PUBLIC_FASTAPI_URL}/api/gateway/tts`
   - **Body Contract**:
     ```json
     {
       "text": "<response_text_to_synthesize>",
       "target_lang": "<language_code>"
     }
     ```

3. **Labs Directory Query** ([src/lib/sse.ts](file:///d:/Projects/Maanak/Frontend/src/lib/sse.ts#L230-L250)):
   - **Target Endpoint**: `GET ${NEXT_PUBLIC_FASTAPI_URL}/api/v1/labs?is_code=<is_code_string>`
   - **Headers**: `X-User-Role: "citizen" | "manufacturer" | "auditor"`

4. **Auditor RAG Metrics Query** ([src/lib/sse.ts](file:///d:/Projects/Maanak/Frontend/src/lib/sse.ts#L252-L269)):
   - **Target Endpoint**: `GET ${NEXT_PUBLIC_FASTAPI_URL}/api/v1/metrics`
   - **Headers**: `X-User-Role: "auditor"`

---

### B. Outputs (Data Emitted / Handled by Frontend)

1. **SSE Stream Chunk Parsing** ([src/lib/sse.ts](file:///d:/Projects/Maanak/Frontend/src/lib/sse.ts#L46-L120)):
   The frontend parses Server-Sent Event streams expecting the following event payloads:
   - **Event `token`**: `{"text": "<token_string>"}` or `{"content": "<token_string>"}`
   - **Event `metadata`**: `{"citations": [{"is_number": "IS 16046", "clause": "5.2", "page": 10, "snippet": "..."}]}`
   - **Event `done` / `[DONE]`**: Signals stream end.
   - **Event `error`**: `{"error": "<error_message>"}`

2. **TTS Endpoint Response**:
   - `{"audio_base64": "<base64_audio_string>"}`

3. **Labs Directory Response**:
   - Array of `LabRecord`:
     ```json
     [
       {
         "lab_name": "<string>",
         "location": "<string>",
         "scope": ["<is_code_string>"]
       }
     ]
     ```

4. **Auditor Metrics Response**:
   - `RagMetrics` Object:
     ```json
     {
       "faithfulness": 0.95,
       "context_precision": 0.92,
       "latency_ms": 450
     }
     ```

---

## 3. Environmental Dependencies

### Environment Variables (.env.local)
- **`NEXT_PUBLIC_FASTAPI_URL`**: Base URL of the external FastAPI API Gateway (e.g., `http://localhost:8000`).
- **`NEXT_PUBLIC_SUPABASE_URL`**: Supabase project URL (e.g., `https://xyz.supabase.co`).
- **`NEXT_PUBLIC_SUPABASE_ANON_KEY`**: Supabase public anonymous API key.

### Network Ports
- **Default Listening Port**: `3000`

### External Infrastructure
- **Supabase Auth Service**: OAuth and cookie session management (`@supabase/ssr`).
- **FastAPI Streaming Gateway**: External server streaming SSE tokens and voice synthesis.

---

## 4. Integration Blockers & Hardcoded IO

> [!WARNING]
> The following architectural mismatches currently block direct integration between this Frontend and the existing FastAPI Backend without modification.

### 1. Endpoint Path Mismatch (Critical Blocker)
- **Frontend Calls**: `POST /api/gateway/chat/stream` ([src/lib/sse.ts:130](file:///d:/Projects/Maanak/Frontend/src/lib/sse.ts#L130))
- **Backend Exposes**: `POST /api/v1/chat` ([app/api/v1/chat.py](file:///d:/Projects/Maanak/app/api/v1/chat.py#L12))
- **Result**: Chat request from Frontend fails with HTTP 404 Not Found.

### 2. Payload Schema Mismatch (Critical Blocker)
- **Frontend Payload**: Sends `{ input_type, data, source_lang, session_id }` ([src/lib/sse.ts:131-136](file:///d:/Projects/Maanak/Frontend/src/lib/sse.ts#L131-L136)).
- **Backend Payload Expects**: `{ session_id, query, chat_history }` ([app/models/chat.py](file:///d:/Projects/Maanak/app/models/chat.py#L8-L11)).
- **Result**: Backend rejects request with HTTP 422 Unprocessable Entity due to missing required `query` field.

### 3. Missing Backend Endpoints
- **TTS Endpoint**: Frontend calls `POST /api/gateway/tts` ([src/lib/sse.ts:206](file:///d:/Projects/Maanak/Frontend/src/lib/sse.ts#L206)); endpoint is un-implemented on backend.
- **Labs Directory Endpoint**: Frontend calls `GET /api/v1/labs` ([src/lib/sse.ts:238](file:///d:/Projects/Maanak/Frontend/src/lib/sse.ts#L238)); endpoint is un-implemented on backend.
- **Metrics Endpoint**: Frontend calls `GET /api/v1/metrics` ([src/lib/sse.ts:260](file:///d:/Projects/Maanak/Frontend/src/lib/sse.ts#L260)); endpoint is un-implemented on backend.

### 4. Storage Decoupling (Local vs. Supabase)
- **Frontend Session Memory**: Persists sessions locally in browser `localStorage` (`maanak-archive:${userId}`) ([src/lib/archive.ts](file:///d:/Projects/Maanak/Frontend/src/lib/archive.ts#L5-L24)).
- **Backend Session Memory**: Queries Supabase `chats` table.
- **Result**: Clearing browser data or switching devices causes session state mismatch between client and server.

### 5. Local Preview Security Fallback
- If Supabase environment variables are missing, `useAuth` falls back to `"local-preview"` mode ([src/components/chat/chat-shell.tsx:63](file:///d:/Projects/Maanak/Frontend/src/components/chat/chat-shell.tsx#L63)), granting UI access without valid authentication tokens.
# System Integration Analysis Report: NLP Module

This document provides a technical integration boundary analysis of the **NLP** module located in `NLP/`. It details execution entry points, hard data contracts, environmental dependencies, and integration blockers against external API servers and containers.

---

## 1. Execution Entry Points

### Execution Model
- **Type**: FastAPI HTTP Gateway Server & Standalone RAG/LLM Processing Engine.
- **Runtime Environment**: Python 3.11+ / FastAPI / Uvicorn / HTTPX / OpenRouter / ElevenLabs SDK.

### Module Entry Points & Primary Function Signatures

1. **Input Gateway Server (API)**:
   - **Filepath**: [NLP/Nlp/Input_Processing/api.py](file:///d:/Projects/Maanak/NLP/Nlp/Input_Processing/api.py)
   - **Command**: `uvicorn Nlp.Input_Processing.api:app --host 0.0.0.0 --port 8000` (or `python Nlp/Input_Processing/api.py`)
   - **Function Signature**: `app = FastAPI(title="Maanak Gateway (Input/Output Domain)")`

2. **Unified RAG Engine**:
   - **Filepath**: [NLP/Nlp/RAG_LLM_Processing/rag_engine.py](file:///d:/Projects/Maanak/NLP/Nlp/RAG_LLM_Processing/rag_engine.py)
   - **Function Signature**: `async def generate_response(self, query: str, history: list[dict], role: str = "citizen") -> AsyncGenerator[str, None]`

3. **Conversational Query Condenser**:
   - **Filepath**: [NLP/Nlp/RAG_LLM_Processing/query_condenser.py](file:///d:/Projects/Maanak/NLP/Nlp/RAG_LLM_Processing/query_condenser.py)
   - **Function Signature**: `def condense_query(query: str, chat_history: list[dict]) -> str`

4. **Guardrailed Response Generator**:
   - **Filepath**: [NLP/Nlp/RAG_LLM_Processing/generator.py](file:///d:/Projects/Maanak/NLP/Nlp/RAG_LLM_Processing/generator.py)
   - **Function Signature**: `async def generate_strict_response(condensed_query: str, retrieved_chunks: list[dict], role: str) -> AsyncGenerator[str, None]`

---

## 2. Hard Data Contracts (I/O)

### A. Inputs

1. **`POST /api/gateway/chat/stream`** ([api.py:34-38, 91-92](file:///d:/Projects/Maanak/NLP/Nlp/Input_Processing/api.py#L34-L38)):
   - **Body `FrontendRequest`**:
     ```json
     {
       "input_type": "text | audio",
       "data": "<string_query_or_raw_base64_audio>",
       "source_lang": "<iso_language_code_eg_en_hi_te>",
       "session_id": "<uuid_string>"
     }
     ```

2. **`POST /api/gateway/tts`** ([api.py:40-42, 134-135](file:///d:/Projects/Maanak/NLP/Nlp/Input_Processing/api.py#L40-L42)):
   - **Body `TTSRequest`**:
     ```json
     {
       "text": "<response_text_string>",
       "target_lang": "<iso_language_code>"
     }
     ```

3. **`RAGEngine.generate_response(...)`** ([rag_engine.py:54](file:///d:/Projects/Maanak/NLP/Nlp/RAG_LLM_Processing/rag_engine.py#L54)):
   - `query`: string
   - `history`: `list[dict]` (expects items with `{"role": str, "content": str}`)
   - `role`: string (`"citizen"`, `"manufacturer"`, `"auditor"`)

---

### B. Outputs

1. **`POST /api/gateway/chat/stream`**:
   - Yields Server-Sent Event (SSE) streams (`media_type="text/event-stream"`):
     - `event: token\ndata: {"text": "<token_string>"}\n\n`
     - `event: metadata\ndata: {"citations": [{"is_number": "IS 13252", "clause": "4.1"}]}\n\n`
     - `event: done\ndata: {}\n\n`

2. **`POST /api/gateway/tts`**:
   - Returns `JSONResponse`:
     ```json
     {
       "audio_base64": "<base64_encoded_audio_string>"
     }
     ```

---

## 3. Environmental Dependencies

### Environment Variables (.env)
- **`OPENROUTER_API_KEY`**: Bearer authentication key for OpenRouter API calls (`https://openrouter.ai/api/v1/chat/completions`).
- **`ELEVENLABS_API_KEY`**: Key for ElevenLabs Text-to-Speech API (`https://api.elevenlabs.io/v1/text-to-speech/...`).

### Network Bindings
- Default Port: `8000` (bound to `0.0.0.0`).

### External Web Services
- **OpenRouter API**: `https://openrouter.ai/api/v1/chat/completions` (OpenAI `gpt-4o-mini` model).
- **ElevenLabs TTS API**: `https://api.elevenlabs.io/v1/text-to-speech/EXAVITQu4vr4xnSDxMaL`.

---

## 4. Integration Blockers & Hardcoded IO

> [!WARNING]
> The following integration blockers and hardcoded shortcuts exist inside `NLP/`.

### 1. Mocked Bhashini ASR (Speech-to-Text) Shortcut (Critical Blocker)
- **Location**: [api.py:44-48](file:///d:/Projects/Maanak/NLP/Nlp/Input_Processing/api.py#L44-L48)
- **Issue**: `bhashini_asr(...)` contains hardcoded static strings instead of connecting to a real ASR engine:
  ```python
  if source_lang == 'te': return "నాకు లాప్టాప్ గురించి కావాలి"
  if source_lang == 'hi': return "मुझे लैपटॉप के बारे में चाहिए"
  return "I need information about laptops"
  ```
- **Impact**: Any audio input in Hindi or Telugu will ignore the actual recording and always return this hardcoded laptop string.

### 2. Hardcoded ElevenLabs Voice ID & Silent Error Catching
- **Location**: [api.py:79-89](file:///d:/Projects/Maanak/NLP/Nlp/Input_Processing/api.py#L79-L89)
- **Issue**: Voice ID is hardcoded in the request URL `EXAVITQu4vr4xnSDxMaL`. If `ELEVENLABS_API_KEY` is missing or ElevenLabs returns non-200, it catches the exception and returns an empty string `""` silently.

### 3. Dynamic Process Working Directory Mutation (`os.chdir`)
- **Location**: [rag_engine.py:61-69](file:///d:/Projects/Maanak/NLP/Nlp/RAG_LLM_Processing/rag_engine.py#L61-L69)
- **Issue**: To resolve relative vector paths, `generate_response` temporarily mutates the global working directory:
  ```python
  original_cwd = os.getcwd()
  os.chdir(rag_pipeline_path)
  # ...
  os.chdir(original_cwd)
  ```
- **Impact**: In a multi-threaded/async server handling concurrent requests, mutating `os.chdir()` globally causes race conditions for file IO in other routes.

### 4. Hardcoded Model Choice Across Modules
- **Location**: [query_condenser.py:34](file:///d:/Projects/Maanak/NLP/Nlp/RAG_LLM_Processing/query_condenser.py#L34), [generator.py:45](file:///d:/Projects/Maanak/NLP/Nlp/RAG_LLM_Processing/generator.py#L45), [api.py:62](file:///d:/Projects/Maanak/NLP/Nlp/Input_Processing/api.py#L62)
- **Issue**: Model name `"openai/gpt-4o-mini"` is hardcoded across multiple files rather than controlled via `Settings`.

### 5. Outdated Entrypoint (`NLP/main.py`)
- **Location**: [NLP/main.py](file:///d:/Projects/Maanak/NLP/main.py)
- **Issue**: `NLP/main.py` is a copy of root `main.py` mounting `app.api.v1.chat` instead of mounting `Nlp.Input_Processing.api:app`. Running `uvicorn main:app` inside `NLP/` launches the simple chat router rather than the Gateway API.
# System Integration Analysis Report: DataIngestion Module

This document provides a technical integration boundary analysis of the **DataIngestion** module located in `DataIngestion/`. It details execution entry points, hard data contracts, environmental dependencies, and integration blockers against external API servers and containers.

---

## 1. Execution Entry Points

### Execution Model
- **Type**: Offline Batch Data Ingestion Scripts & Asynchronous Retrieval Module.
- **Runtime Environment**: Python 3.11+ / PyMuPDF / HuggingFace Transformers / Pinecone SDK.

### Module Entry Points & Primary Function Signatures

1. **PDF Vision Parser**:
   - **Filepath**: [DataIngestion/rag_engine/ingestion/pdf_vision_parser.py](file:///d:/Projects/Maanak/DataIngestion/rag_engine/ingestion/pdf_vision_parser.py)
   - **Command**: `python DataIngestion/rag_engine/ingestion/pdf_vision_parser.py`
   - **Function Signature**: `parse_pdf_local(pdf_path: str)`

2. **Clause Chunker**:
   - **Filepath**: [DataIngestion/rag_engine/ingestion/clause_chunker.py](file:///d:/Projects/Maanak/DataIngestion/rag_engine/ingestion/clause_chunker.py)
   - **Command**: `python DataIngestion/rag_engine/ingestion/clause_chunker.py`
   - **Function Signature**: `process_markdown_files()`

3. **Hybrid Indexer (Sparse + Dense)**:
   - **Filepath**: [DataIngestion/rag_engine/ingestion/indexer.py](file:///d:/Projects/Maanak/DataIngestion/rag_engine/ingestion/indexer.py)
   - **Command**: `python DataIngestion/rag_engine/ingestion/indexer.py`
   - **Function Signature**: `run_indexer()`

4. **Hybrid RAG Retriever Service**:
   - **Filepath**: [DataIngestion/rag_engine/retrieval/retriever.py](file:///d:/Projects/Maanak/DataIngestion/rag_engine/retrieval/retriever.py)
   - **Function Signature**: `async def get_relevant_clauses(standalone_query: str, top_k: int = 3, alpha: float = 0.5) -> list[dict]`

---

## 2. Hard Data Contracts (I/O)

### A. Inputs

1. **`parse_pdf_local(pdf_path: str)`**:
   - `pdf_path`: Absolute or relative path to a valid `.pdf` document in `data/raw_pdfs/`.

2. **`process_markdown_files()`**:
   - Reads `.md` files from relative path `data/processed_chunks/`. Expects markdown files formatted with HTML page comments (`<!-- PAGE <number> -->`).

3. **`run_indexer()`**:
   - Reads `data/metadata/chunks_dataset.json`. Expects JSON array of chunk objects:
     ```json
     [
       {
         "doc_id": "is_16046_2018",
         "is_number": "IS 16046:2018",
         "clause_no": "5.2",
         "clause_title": "Cell Insulation",
         "page_number": 4,
         "chunk_text": "Clause text content..."
       }
     ]
     ```

4. **`get_relevant_clauses(...)`**:
   - `standalone_query` (str): Search string.
   - `top_k` (int, default=3): Number of top reranked chunks to return.
   - `alpha` (float, default=0.5): Hybrid search weight (`1.0` = Dense only, `0.0` = Sparse keyword only, `0.5` = Balanced).
   - Requires pickle model `data/metadata/sparse_encoder.pkl` to exist on disk.

---

### B. Outputs

1. **`parse_pdf_local`**: Writes converted Markdown files to `data/processed_chunks/{doc_id}.md`.
2. **`process_markdown_files`**: Generates and writes dataset JSON to `data/metadata/chunks_dataset.json`.
3. **`run_indexer`**: Saves fitted TF-IDF vectorizer to `data/metadata/sparse_encoder.pkl` and upserts 384-dimensional dense vectors + sparse TF-IDF vectors to Pinecone Index.
4. **`get_relevant_clauses`**: Returns ranked array of dictionary metadata objects containing relevance scores:
   ```json
   [
     {
       "chunk_text": "Clause content snippet...",
       "is_number": "IS 16046",
       "clause_no": "5.2",
       "clause_title": "Cell Insulation",
       "page_number": 4,
       "relevance_score": 3.4215
     }
   ]
   ```

---

## 3. Environmental Dependencies

### Environment Variables (.env)
- **`PINECONE_API_KEY`**: Secret API key for Pinecone vector database connection.
- **`PINECONE_INDEX_NAME`**: Name of the Pinecone vector index (defaults to `"bis-maanak-index"`).

### System Binary Requirements
- **Tesseract OCR**: System executable required in `$PATH` for `pymupdf4llm` image/flowchart OCR parsing ([pdf_vision_parser.py:24](file:///d:/Projects/Maanak/DataIngestion/rag_engine/ingestion/pdf_vision_parser.py#L24)).

### Machine Learning Models (HuggingFace Hub)
- **Dense Embedding Model**: `sentence-transformers/all-MiniLM-L6-v2` (384-dimensions).
- **Cross-Encoder Reranker**: `cross-encoder/ms-marco-MiniLM-L-6-v2`.

### External Infrastructure
- **Pinecone Vector Database**: Cloud vector storage engine for hybrid dense/sparse indexing.

### Hardcoded Relative File Paths
- `data/raw_pdfs/*.pdf`
- `data/processed_chunks/*.md`
- `data/metadata/chunks_dataset.json`
- `data/metadata/sparse_encoder.pkl`

---

## 4. Integration Blockers & Hardcoded IO

> [!WARNING]
> The following architectural flaws in `DataIngestion/` currently block integration with the FastAPI Web Backend (`app/`).

### 1. Relative Working Directory Dependency (Critical Blocker)
- **Issue**: All ingestion and retrieval scripts use hardcoded relative path joins like `os.path.join("data", "metadata", ...)` ([indexer.py:12](file:///d:/Projects/Maanak/DataIngestion/rag_engine/ingestion/indexer.py#L12), [retriever.py:34](file:///d:/Projects/Maanak/DataIngestion/rag_engine/retrieval/retriever.py#L34)).
- **Impact**: When the FastAPI backend (`main.py`) or Docker container runs from root directory (`d:\Projects\Maanak`), Python resolves `data/` at root (`d:\Projects\Maanak\data\`) instead of `DataIngestion/data/`, raising `FileNotFoundError`.

### 2. Disconnected RAG Engine
- **Issue**: `get_relevant_clauses` in [retriever.py](file:///d:/Projects/Maanak/DataIngestion/rag_engine/retrieval/retriever.py#L39) is an unmounted module function. The FastAPI backend ([app/services/rag.py](file:///d:/Projects/Maanak/app/services/rag.py)) currently returns simulated citations (`IS 16046`) instead of importing and invoking `get_relevant_clauses`.

### 3. Missing OCR Binary Error Handling
- **Issue**: If Tesseract OCR binaries are missing from the OS environment, `pymupdf4llm.to_markdown(..., use_ocr=True)` catches `Exception` and prints stdout text ([pdf_vision_parser.py:22-25](file:///d:/Projects/Maanak/DataIngestion/rag_engine/ingestion/pdf_vision_parser.py#L22-L25)) without raising an error code or alerting upstream pipelines.

### 4. Pinecone Key Missing Silent Suppression
- **Issue**: If `PINECONE_API_KEY` is omitted, `indexer.py:45-47` prints `"PINECONE_API_KEY not found in environment. Skipping dense indexing."` and exits with code `0`. Upstream scripts assume indexing succeeded when no vectors were written.

### 5. High Cold-Start Latency
- **Issue**: `retriever.py` lazily initializes `SentenceTransformer` and `CrossEncoder` model weights on the first user query call ([retriever.py:22-37](file:///d:/Projects/Maanak/DataIngestion/rag_engine/retrieval/retriever.py#L22-L37)). This creates an initial 3 to 8 second delay on the first API query request.
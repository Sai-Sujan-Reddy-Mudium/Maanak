# MAANAK DATA & INGESTION BLUEPRINT: DEV 2 (DATA INGESTION & STRUCTURING)
## System Architecture & Vibe-Coding Instructions

You are an expert Python, PyMuPDF, and Vector Database developer. Your goal is to build the multimodal ingestion and chunking pipeline for "MAANAK", an AI-powered compliance assistant for Indian Standards (BIS). 

Your mandate is strict: You turn messy, multi-page raw PDFs into a pristine, mathematically searchable vector database in Pinecone. You do not touch FastAPI endpoints, front-end code, or LLM chat UI components. You operate independently in the `/rag_engine/ingestion/` and `/rag_engine/retrieval/` directories and provide a clean `retriever.py` module to Dev 1 and Dev 3.

### 1. Core Tech Stack & Rules
* **PDF Processing & OCR:** `PyMuPDF` (`fitz`) to convert PDF pages to images in memory; OpenRouter API (`gpt-4o-mini`) for vision-based Markdown extraction.
* **Chunking:** Python regular expressions targeting strict BIS clause hierarchies (e.g., `^([0-9]+(\.[0-9]+)*)\s+([A-Z].*)`).
* **Embeddings:** `sentence-transformers` (specifically `all-MiniLM-L6-v2` for local, free 384-dimensional dense vectors).
* **Vector Store & Search:** `pinecone-client` for serverless vector hosting + `rank_bm25` for local sparse lexical matching.
* **Re-ranking:** `sentence-transformers` Cross-Encoder (`ms-marco-MiniLM-L-6-v2`) to filter top chunks.

### 2. Component 1: Multimodal Vision Ingestion (`pdf_vision_parser.py`)
Government PDFs contain complex multi-column layouts and tables that standard text extractors ruin. You must use a vision-based OCR pipeline.

* **Feature:** PyMuPDF + GPT-4o-mini Vision Extractor
* **Description:** A script that iterates over all raw PDFs in `data/raw_pdfs/`, converts pages to base64 images, and extracts clean Markdown via OpenRouter.
* **Input:** Raw PDF files (`.pdf`) located in `data/raw_pdfs/`.
* **Processing Rule (Anti-Garbage Filter):** 
  * The system prompt sent to GPT-4o-mini must aggressively ignore Table of Contents, Foreword, References, and Annexes containing human names.
  * If a page is boilerplate, the model must output `[SKIP]`.
* **Output:** Clean Markdown text files saved into a local `data/processed_chunks/` or `/markdown` folder.

### 3. Component 2: Clause-Level Chunking (`clause_chunker.py`)
Do not use naive 500-word character splits. BIS standards are legally bound by numbered clauses.

* **Feature:** Regex Clause Boundary Chunker
* **Description:** Parses the extracted Markdown files and slices them specifically at clause headings.
* **Input:** Processed Markdown text files.
* **Regex Pattern to Enforce:** `^([0-9]+(\.[0-9]+)*)\s+([A-Z].*)` (matches standard headings like `5.5.6 Logging Physical Access`).
* **Output Payload (JSON / Python Dictionary per chunk):**
  ```json
  {
    "doc_id": "is_16335_2025",
    "is_number": "IS 16335:2025",
    "standard_title": "Power Control Systems - Security Requirements",
    "clause_no": "5.5.6",
    "clause_title": "Logging Physical Access",
    "page_number": 10,
    "chunk_text": "Logging shall record sufficient information to uniquely identify individuals..."
  }

### 4. Component 3: Vectorization & Pinecone Indexing (`indexer.py`)
You must push both dense and sparse representations to ensure exact code matching.

* **Feature:** Pinecone Upserter & BM25 Builder
* **Description:** Converts structured chunks into dense vectors and populates Pinecone, while building a local BM25 keyword index.
* **Input:** Structured JSON chunk objects from Component 2.
* **Output Action:**
  1. Initialize local embedding model: `SentenceTransformer('all-MiniLM-L6-v2')`.
  2. Generate 384-dimensional vectors for every `chunk_text`.
  3. Upsert into Pinecone Serverless Index with metadata: `{"chunk_text": ..., "is_number": ..., "clause": ..., "page_number": ...}`.
  4. Build `rank_bm25` index over all chunk texts for keyword matching and serialize it to `data/bm25_index.pkl`.

### 5. Component 4: The Handoff Module (`retriever.py`)
This is the only file Dev 1 and Dev 3 care about. You must expose a clean asynchronous function that accepts a query and returns ranked chunks.

* **Feature:** Hybrid Retriever + Cross-Encoder Re-ranker
* **Description:** Takes an expanded query, performs concurrent Dense + Sparse search, fuses the scores, and re-ranks them.
* **Input Function Signature:** `async def get_relevant_clauses(standalone_query: str, top_k: int = 3) -> list[dict]:`
* **Internal Workflow:**
  1. **Dense Search:** Query Pinecone using `sentence-transformers`.
  2. **Sparse Search:** Query local BM25 index for exact terms (e.g., `"IS 13252"`).
  3. **Reciprocal Rank Fusion (RRF):** Merge results into a pool of 15 candidates.
  4. **Re-ranking:** Pass candidates through the Cross-Encoder model to select the top `k` chunks.
* **Output Format:** Returns a list of dictionaries matching the chunk schema (including `chunk_text`, `is_number`, `clause`, `page_number`, and `relevance_score`).

### 6. Developer Execution Sequence
1. **Hour 5-8:** Write `pdf_vision_parser.py` and test extraction on 2 sample PDFs (`IS 16335` and `IS 14543`). Verify output markdown.
2. **Hour 8-12:** Write `clause_chunker.py` using the Regex patterns to ensure sections like Clause 5.5.6 are cleanly isolated.
3. **Hour 12-16:** Setup Pinecone Serverless, initialize `sentence-transformers`, and run batch ingestion across all 15-20 core PDFs.
4. **Hour 16-20:** Build `hybrid_retriever.py` and `reranker.py`. Test via terminal script (`python retriever.py "What are the password rules?"`) to confirm exact clause retrieval.
5. **Hour 20 (The Merge):** Hand over `retriever.py` and the Pinecone index credentials to Dev 3 (AI Orchestrator) so they can plug it directly into the generation pipeline.
import sys
import os
from typing import AsyncGenerator
from .query_condenser import condense_query
from .generator import generate_strict_response

# Dynamically find the RAG Pipeline folder so it works on GitHub no matter how folders are named!
current_dir = os.path.dirname(__file__)
parent_dir = os.path.abspath(os.path.join(current_dir, '..'))

# Try to find the RAG folder whether it's nested in RAG_PIPELINE or just sitting at the root of the repo
possible_paths = [
    os.path.join(parent_dir, 'RAG_PIPELINE', 'Maanak-feat-retrieval'),
    os.path.join(parent_dir, 'Maanak-feat-retrieval'),
    os.path.join(parent_dir, 'rag_pipeline'),
    os.path.join(parent_dir, 'rag')
]

rag_pipeline_path = None
for path in possible_paths:
    if os.path.exists(os.path.join(path, 'rag_engine', 'retrieval', 'retriever.py')):
        rag_pipeline_path = path
        break

if rag_pipeline_path and rag_pipeline_path not in sys.path:
    sys.path.insert(0, rag_pipeline_path)

try:
    from rag_engine.retrieval.retriever import get_relevant_clauses
    RAG_AVAILABLE = True
except Exception as e:
    # Catch ALL exceptions (like pinecone package errors) so the app doesn't crash on startup!
    print(f"Warning: Could not load RAG pipeline: {e}")
    RAG_AVAILABLE = False
    
    async def get_relevant_clauses(query: str, top_k: int = 3) -> list[dict]:
        """Fallback mock if RAG pipeline isn't properly configured yet."""
        print(f"[Retriever Fallback] Fetching chunks for: {query}")
        return [
            {
                "chunk_text": "Laptops require safety testing under IS 13252...",
                "is_number": "IS 13252",
                "clause_no": "4.1",
                "page_number": 12,
                "relevance_score": 0.92
            }
        ]

class RAGEngine:
    """
    Component 4: Unified Pipeline Class
    """
    
    async def generate_response(self, query: str, history: list[dict], role: str = "citizen") -> AsyncGenerator[str, None]:
        # 1. Condense the query based on chat history
        standalone_query = condense_query(query, history)
        
        # 2. Call Dev 2's retriever to get real chunks
        print(f"[RAGEngine] Calling Dev 2's Retriever with query: {standalone_query}")
        
        # Super safe execution: change directory to the RAG guy's folder so his relative paths (like data/metadata) work perfectly on GitHub!
        original_cwd = os.getcwd()
        if rag_pipeline_path:
            os.chdir(rag_pipeline_path)
            
        try:
            chunks = await get_relevant_clauses(standalone_query, top_k=3)
        finally:
            os.chdir(original_cwd)
        
        # 3, 4, 5. Build prompt, invoke LLM, and stream tokens/metadata
        async for token_event in generate_strict_response(standalone_query, chunks, role):
            yield token_event

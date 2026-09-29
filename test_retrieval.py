import os
import sys
import asyncio
import json

# Ensure we can import from the DataIngestion module
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
from DataIngestion.rag_engine.retrieval.retriever import get_relevant_clauses, load_resources
import DataIngestion.rag_engine.retrieval.retriever as retriever_module

async def run_test():
    # 1. Load Environment Variables
    print("Loading environment variables...")
    load_dotenv()
    
    if not os.getenv("PINECONE_API_KEY"):
        print("ERROR: PINECONE_API_KEY is missing from .env file.")
        sys.exit(1)

    print("PINECONE_API_KEY found.")

    # 2. Initialize Models and Pinecone
    print("\nInitializing models, Pinecone, and sparse encoder...")
    try:
        # Simulate FastAPI Lifespan startup
        load_resources()
    except Exception as e:
        print(f"ERROR: Failed during resource initialization (models or Pinecone). Details: {e}")
        sys.exit(1)

    # Check if sparse encoder actually loaded (since load_resources swallows the error)
    if retriever_module.sparse_encoder is None:
        expected_path = os.path.join(os.path.dirname(retriever_module.__file__), "..", "..", "data", "metadata", "sparse_encoder.pkl")
        print(f"ERROR: Sparse encoder file missing or failed to load. Expected at: {os.path.abspath(expected_path)}")
        sys.exit(1)
        
    if retriever_module.pinecone_index is None:
        print("ERROR: Pinecone index failed to initialize. Check your API key and index name.")
        sys.exit(1)
        
    print("Resources loaded successfully.")

    # 3. Query Execution
    query = "How is resistance to cold conditions tested for current-carrying hoses?"
    top_k = 3
    print(f"\nExecuting query: '{query}' with top_k={top_k}")
    
    try:
        results = await get_relevant_clauses(standalone_query=query, top_k=top_k)
    except Exception as e:
        print(f"ERROR: Failed during execution of get_relevant_clauses. Details: {e}")
        sys.exit(1)

    # 4. Result Validation and Output
    if not results:
        print("WARNING: Query executed successfully but no vectors/chunks were returned (returned empty list).")
        sys.exit(0)
        
    print("\n--- RETRIEVAL RESULTS ---")
    formatted_results = []
    for i, res in enumerate(results, 1):
        formatted_results.append({
            "rank": i,
            "clause": res.get("clause"),
            "exact_pdf_name": res.get("exact_pdf_name"),
            "relevance_score": res.get("relevance_score"),
            "chunk_text": res.get("chunk_text")
        })

    # Print raw JSON output explicitly
    print(json.dumps(formatted_results, indent=4))
    
    print(f"\nSuccessfully retrieved {len(results)} chunks.")

if __name__ == "__main__":
    asyncio.run(run_test())

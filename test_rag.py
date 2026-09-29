import asyncio
import os
import sys
from dotenv import load_dotenv

# Ensure Python can resolve paths when running from the project root
sys.path.append(os.path.join(os.path.dirname(__file__), "DataIngestion"))
sys.path.append(os.path.join(os.path.dirname(__file__), "NLP"))

# Import the RAG components
try:
    from rag_engine.retrieval.retriever import load_resources
except ImportError:
    try:
        from DataIngestion.rag_engine.retrieval.retriever import load_resources
    except ImportError:
        print("Warning: Could not import load_resources from retriever.")
        def load_resources():
            pass

from Nlp.RAG_LLM_Processing.rag_engine import RAGEngine

async def test_scenario(engine: RAGEngine, scenario_name: str, query: str):
    print(f"\n{'='*60}")
    print(f"Running {scenario_name}")
    print(f"Query: '{query}'")
    print(f"{'='*60}")
    
    # Empty history for these tests
    history = []
    
    print("\n--- STREAM START ---\n")
    
    # We will accumulate the tokens to show the final text, 
    # but we will also print the SSE events as requested.
    async for event in engine.generate_response(query, history, role="citizen"):
        # The generator yields raw SSE strings like "event: token\ndata: {...}\n\n"
        event = event.strip()
        if not event:
            continue
            
        lines = event.split('\n')
        event_type = lines[0].replace("event: ", "").strip()
        
        if event_type == "token":
            # Just print the token as it streams for visual verification
            import json
            data_line = lines[1].replace("data: ", "").strip()
            try:
                data_json = json.loads(data_line)
                token = data_json.get("text", "")
                print(token, end="", flush=True)
            except json.JSONDecodeError:
                pass
                
        elif event_type == "metadata":
            print("\n\n[SSE Event] metadata")
            print(f"Payload: {lines[1]}")
            
        elif event_type == "done":
            print("\n[SSE Event] done")

    print("\n\n--- STREAM COMPLETE ---")


async def run_diagnostics(query: str):
    print(f"\n{'='*60}")
    print("--- DIAGNOSTIC RUN ---")
    print(f"Original Query: '{query}'")
    
    from Nlp.RAG_LLM_Processing.query_condenser import condense_query
    try:
        from rag_engine.retrieval.retriever import get_relevant_clauses
    except ImportError:
        from DataIngestion.rag_engine.retrieval.retriever import get_relevant_clauses
    
    # 1. Condense Query
    standalone_query = condense_query(query, [])
    print(f"1. Rewritten Query (sent to Pinecone): '{standalone_query}'")
    
    # 2. Get Raw Chunks (Disable Threshold, Max top_k)
    print("2. Raw Retrieved Chunks & Scores (Threshold Disabled):")
    # Setting min_score_threshold to a very low negative number disables the zero-floor filter
    raw_chunks = await get_relevant_clauses(standalone_query, top_k=15, min_score_threshold=-100.0)
    
    if not raw_chunks:
        print("   No chunks returned at all from Pinecone/Retriever.")
    else:
        for i, chunk in enumerate(raw_chunks, 1):
            score = chunk.get('relevance_score', 0.0)
            is_number = chunk.get('is_number', 'Unknown')
            clause = chunk.get('clause', 'Unknown')
            text = chunk.get('chunk_text', '').replace('\n', ' ')[:100]
            print(f"   [{i}] Score: {score:>7.4f} | {is_number} Clause {clause} | Preview: {text}...")
    
    print(f"{'='*60}\n")


async def main():
    # 1. Load environment variables
    load_dotenv(override=True)
    
    if not os.getenv("OPENROUTER_API_KEY"):
        print("WARNING: OPENROUTER_API_KEY is not set in .env!")
        
    # 2. Initialize Data Ingestion models
    print("Loading resources (retriever models)...")
    try:
        load_resources()
        print("Resources loaded successfully.")
    except Exception as e:
        print(f"Failed to load resources: {e}")
        
    # 3. Diagnostic Run for problematic query
    await run_diagnostics("How often should a cyber vulnerability assessment be performed?")
    
    # 4. Instantiate Engine
    engine = RAGEngine()
    
    # 5. Run Tests
    await test_scenario(engine, "Scenario A (Valid)", "Are motorized cleaning heads allowed in water suction cleaning appliances?")
    await test_scenario(engine, "Scenario B (Valid)", "How is resistance to cold conditions tested for current-carrying hoses?")
    await test_scenario(engine, "Scenario C (Valid)", "What are the permissible sizes of the hallmark for gold articles?")
    await test_scenario(engine, "Scenario D (Valid)", "How often should a cyber vulnerability assessment be performed?")
    await test_scenario(engine, "Scenario E (Nonsense)", "What is the recipe for chocolate cake?")


if __name__ == "__main__":
    asyncio.run(main())

import os
import pickle
import asyncio
from dotenv import load_dotenv
from pinecone import Pinecone
from sentence_transformers import SentenceTransformer, CrossEncoder

load_dotenv()

# Global models to avoid reloading on every query
DENSE_MODEL_NAME = 'all-MiniLM-L6-v2'
RERANKER_MODEL_NAME = 'cross-encoder/ms-marco-MiniLM-L-6-v2'

dense_model = None
reranker_model = None
pinecone_index = None
sparse_encoder = None

def load_resources():
    global dense_model, reranker_model, pinecone_index, sparse_encoder
    
    if dense_model is None:
        dense_model = SentenceTransformer(DENSE_MODEL_NAME)
        
    if reranker_model is None:
        reranker_model = CrossEncoder(RERANKER_MODEL_NAME)
        
    if pinecone_index is None:
        pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        index_name = os.getenv("PINECONE_INDEX_NAME", "bis-maanak-index")
        pinecone_index = pc.Index(index_name)
        
    if sparse_encoder is None:
        encoder_path = os.path.join("data", "metadata", "sparse_encoder.pkl")
        if os.path.exists(encoder_path):
            with open(encoder_path, "rb") as f:
                sparse_encoder = pickle.load(f)

async def get_relevant_clauses(standalone_query: str, top_k: int = 3, alpha: float = 0.5) -> list[dict]:
    """
    Query the vector database using hybrid search and rerank results.
    `alpha` balances sparse vs dense. 
      - alpha=1.0: Pure Dense (Semantic only)
      - alpha=0.0: Pure Sparse (Keyword only)
      - alpha=0.5: Balanced Hybrid
    """
    await asyncio.to_thread(load_resources)
    
    if sparse_encoder is None:
        print("Sparse encoder not found! Run indexer first.")
        return []

    # 1. Generate Query Vectors
    dense_vec = await asyncio.to_thread(dense_model.encode, standalone_query, convert_to_numpy=True)
    
    # Generate Sparse Vector
    sparse_matrix = sparse_encoder.transform([standalone_query])
    row = sparse_matrix[0]
    sparse_vec = {
        "indices": row.indices.tolist(),
        "values": row.data.tolist()
    }
    
    # 2. Hybrid Scaling
    # scale dense by alpha
    scaled_dense = [v * alpha for v in dense_vec.tolist()]
    # scale sparse by (1 - alpha)
    scaled_sparse = {
        "indices": sparse_vec["indices"],
        "values": [v * (1 - alpha) for v in sparse_vec["values"]]
    }
    
    # 3. Pinecone Native Hybrid Query
    # If the sparse vector is entirely empty (no recognized keywords), Pinecone will throw an error
    # if we pass an empty sparse_vector. We fallback to pure dense in this edge case.
    if len(scaled_sparse["indices"]) == 0:
        resp = await asyncio.to_thread(
            pinecone_index.query,
            vector=scaled_dense,
            top_k=15,
            include_metadata=True
        )
    else:
        resp = await asyncio.to_thread(
            pinecone_index.query,
            vector=scaled_dense,
            sparse_vector=scaled_sparse,
            top_k=15,
            include_metadata=True
        )
    
    candidate_metadata_list = [match.metadata for match in resp.matches]
    
    # 3. Re-ranking
    if not candidate_metadata_list:
        return []
        
    candidate_texts = [meta["chunk_text"] for meta in candidate_metadata_list]
    cross_inp = [[standalone_query, text] for text in candidate_texts]
    
    cross_scores = await asyncio.to_thread(reranker_model.predict, cross_inp)
    
    # Attach scores to metadata
    for i, meta in enumerate(candidate_metadata_list):
        meta["relevance_score"] = float(cross_scores[i])
        
    # Sort by relevance score
    candidate_metadata_list.sort(key=lambda x: x["relevance_score"], reverse=True)
    
    # Return top K
    return candidate_metadata_list[:top_k]

if __name__ == "__main__":
    async def test():
        query = "What is the process for identifying critical cyber assets?"
        print(f"Testing retriever with query: '{query}'")
        
        print("\n=== Pure Dense Search (alpha=1.0) ===")
        dense_results = await get_relevant_clauses(query, top_k=2, alpha=1.0)
        for i, res in enumerate(dense_results, 1):
            print(f"Result {i} (Score {res['relevance_score']:.4f}) -> Clause {res.get('clause_no')}: {res.get('clause_title')}")
            
        print("\n=== Pure Sparse Search (alpha=0.0) ===")
        sparse_results = await get_relevant_clauses(query, top_k=2, alpha=0.0)
        for i, res in enumerate(sparse_results, 1):
            print(f"Result {i} (Score {res['relevance_score']:.4f}) -> Clause {res.get('clause_no')}: {res.get('clause_title')}")
            
        print("\n=== Hybrid Search (alpha=0.5) ===")
        hybrid_results = await get_relevant_clauses(query, top_k=2, alpha=0.5)
        for i, res in enumerate(hybrid_results, 1):
            print(f"Result {i} (Score {res['relevance_score']:.4f}) -> Clause {res.get('clause_no')}: {res.get('clause_title')}")
            
    asyncio.run(test())

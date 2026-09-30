import os
import json
import pickle
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone
from sklearn.feature_extraction.text import TfidfVectorizer

load_dotenv()

def run_indexer():
    chunks_path = os.path.join("data", "metadata", "chunks_dataset.json")
    sparse_encoder_path = os.path.join("data", "metadata", "sparse_encoder.pkl")
    
    if not os.path.exists(chunks_path):
        print(f"File not found: {chunks_path}")
        return
        
    print(f"Loading chunks from {chunks_path}...")
    with open(chunks_path, "r", encoding="utf-8") as f:
        chunks = json.load(f)
        
    if not chunks:
        print("No chunks to index.")
        return

    # 1. Fit Sparse Encoder (TF-IDF)
    print("Fitting Sparse encoder on chunk texts...")
    vectorizer = TfidfVectorizer(stop_words='english')
    chunk_texts = [c["chunk_text"] for c in chunks]
    vectorizer.fit(chunk_texts)
    
    # Save the fitted vectorizer
    with open(sparse_encoder_path, "wb") as f:
        pickle.dump(vectorizer, f)
    print(f"Saved Sparse encoder to {sparse_encoder_path}")
    
    # Generate sparse matrices for all chunks
    sparse_matrices = vectorizer.transform(chunk_texts)

    # 2. Dense Indexing & Upsert (Pinecone)
    pinecone_api_key = os.getenv("PINECONE_API_KEY")
    index_name = os.getenv("PINECONE_INDEX_NAME", "bis-maanak-index")
    
    if not pinecone_api_key:
        print("PINECONE_API_KEY not found in environment. Skipping dense indexing.")
        return
        
    print("Initializing Pinecone and SentenceTransformer...")
    pc = Pinecone(api_key=pinecone_api_key)
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    try:
        index = pc.Index(index_name)
        print("Connected to Pinecone index:", index_name)
    except Exception as e:
        print(f"Could not connect to Pinecone index {index_name}. Error: {e}")
        return

    print("Generating embeddings and upserting in batches...")
    batch_size = 100
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i : i + batch_size]
        
        # Get sparse rows for this batch
        batch_sparse_matrix = sparse_matrices[i : i + batch_size]
        
        # Generate IDs
        ids = [f"{c['doc_id']}_{c['clause_no']}" for c in batch]
        
        # Generate dense vectors
        texts = [c["chunk_text"] for c in batch]
        dense_embeddings = model.encode(texts, convert_to_numpy=True).tolist()
        
        # Prepare metadata
        metadata = [
            {
                "chunk_text": c["chunk_text"],
                "is_number": c["is_number"],
                "clause_no": c["clause_no"],
                "clause_title": c["clause_title"],
                "page_number": c["page_number"]
            }
            for c in batch
        ]
        
        # Construct dictionaries for hybrid upsert
        vectors_to_upsert = []
        for row_idx, (id_, dense_vec, meta) in enumerate(zip(ids, dense_embeddings, metadata)):
            
            # Extract sparse indices and values for this specific row
            row = batch_sparse_matrix[row_idx]
            sparse_vec = {
                "indices": row.indices.tolist(),
                "values": row.data.tolist()
            }
            
            vectors_to_upsert.append({
                "id": id_,
                "values": dense_vec,
                "sparse_values": sparse_vec,
                "metadata": meta
            })
        
        # Upsert
        index.upsert(vectors=vectors_to_upsert)
        print(f"  Upserted batch {i} to {i + len(batch)}")
        
    print("Indexing completed successfully!")

if __name__ == "__main__":
    run_indexer()

import faiss
import numpy as np
import os
import config

# FAISS requires explicit float32 and specific shapes
EMBEDDING_DIM = 512

def get_or_create_index():
    """Load the existing index or create a new one if it doesn't exist."""
    faiss_path = config.FAISS_INDEX_PATH
    
    if os.path.exists(faiss_path):
        # Read existing index
        index = faiss.read_index(faiss_path)
    else:
        # Create new index: IndexFlatIP calculates inner product.
        # Since our vectors are L2-normalized, inner product == cosine similarity.
        base_index = faiss.IndexFlatIP(EMBEDDING_DIM)
        # Wrap it in an IndexIDMap to allow us to pass our own custom IDs
        index = faiss.IndexIDMap(base_index)
        
    return index

def save_index(index):
    """Save the index to disk."""
    faiss_path = config.FAISS_INDEX_PATH
    os.makedirs(os.path.dirname(os.path.abspath(faiss_path)), exist_ok=True)
    faiss.write_index(index, faiss_path)

def add_embedding(embedding: np.ndarray, faiss_id: int):
    """Add a single L2-normalized embedding with a specific ID to the index."""
    index = get_or_create_index()
    
    # Ensure embedding is a 2D float32 array
    embedding_2d = np.array([embedding], dtype=np.float32)
    id_array = np.array([faiss_id], dtype=np.int64)
    
    index.add_with_ids(embedding_2d, id_array)
    save_index(index)

def search_embedding(embedding: np.ndarray, threshold: float = None):
    """
    Search for the closest matching embedding.
    Returns (faiss_id, distance/similarity) or (None, None) if below threshold or empty.
    """
    index = get_or_create_index()
    
    if index.ntotal == 0:
        return None, None
        
    if threshold is None:
        threshold = config.FACE_SIMILARITY_THRESHOLD
        
    # Ensure embedding is a 2D float32 array
    embedding_2d = np.array([embedding], dtype=np.float32)
    
    # k=1 means we only want the single closest match
    distances, indices = index.search(embedding_2d, k=1)
    
    matched_distance = distances[0][0]
    matched_id = indices[0][0]
    
    # Since we use Inner Product on normalized vectors, higher distance = higher similarity
    if matched_distance >= threshold and matched_id != -1:
        return int(matched_id), float(matched_distance)
        
    return None, None

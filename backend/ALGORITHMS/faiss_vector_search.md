# FAISS (Facebook AI Similarity Search)

FAISS is a library developed by Meta for efficient similarity searching of dense vectors. It is designed to search through millions of vectors in milliseconds.

## How it works in our project
1. We use `IndexFlatIP` (Flat Index with Inner Product). Because our vectors are L2-normalized, the inner product calculation is mathematically equivalent to **Cosine Similarity**: **similarity = A · B = Σ(Aᵢ × Bᵢ)**
2. The index is wrapped in `IndexIDMap`, which allows us to assign our own custom integer IDs (called `faiss_id`) to each stored vector. This is essential for linking the vector back to the relational database.
3. When a new face embedding is queried, FAISS performs a brute-force comparison against all stored embeddings and returns the closest match along with the similarity score.
4. If the similarity score exceeds the threshold of **0.60**, the identity is considered a match, and the corresponding `faiss_id` is used to retrieve the person's name and email from SQLite.

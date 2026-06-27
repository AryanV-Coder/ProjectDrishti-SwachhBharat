# Database Architecture (FAISS & SQLite)

This document explains the dual-database architecture used to store and retrieve violator identities.

## Why Two Databases?
Facial recognition requires comparing mathematical vectors, which relational databases are too slow for. Therefore, the system splits the data:
1. **FAISS (Vector DB)**: Stores the high-dimensional mathematical embeddings of faces for ultra-fast similarity searches.
2. **SQLite (Relational DB)**: Stores the text metadata (Name, Email) linked to those vectors.

## FAISS Implementation (`faiss_db.py`)
- **Model**: Uses `faiss.IndexFlatIP` (Inner Product). Because our vectors are L2-normalized, calculating the inner product is mathematically identical to calculating **Cosine Similarity**.
- **Custom IDs**: Standard FAISS auto-generates IDs. We wrap the index in `faiss.IndexIDMap` to force FAISS to accept our own custom `faiss_id`. This allows us to link the vector to a SQLite record.

## SQLite Schema (`sqlite_db.py`)
The metadata is stored in `face_database.db` using two tables:
1. `persons`: Stores `person_id` (Auto-increment), `name`, and `email`.
2. `face_embeddings_id`: A bridging table that stores `faiss_id` (Primary Key) and maps it to a `person_id` (Foreign Key).

## Retrieval Query
When FAISS successfully matches a face and returns a `faiss_id`, the pipeline queries SQLite to get the email:
```sql
SELECT p.name, p.email 
FROM persons p
JOIN face_embeddings_id f ON p.person_id = f.person_id
WHERE f.faiss_id = ?
```

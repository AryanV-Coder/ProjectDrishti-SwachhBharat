import numpy as np
import cv2
from deepface import DeepFace
import os

from utils import faiss_db

def get_embedding(image_path: str) -> np.ndarray:
    """
    Extract a 512-dimensional facial embedding using DeepFace (Facenet512).
    L2-normalizes the embedding for use with FAISS inner product search.
    """
    try:
        # We use Facenet512 as it provides a 512D embedding which is very accurate
        # We use mtcnn backend as it is robust for face detection and alignment
        # enforce_detection=True ensures we only return an embedding if a face is actually found
        results = DeepFace.represent(
            img_path=image_path,
            model_name="Facenet512",
            detector_backend="mtcnn",
            enforce_detection=True
        )
        
        # DeepFace.represent can return multiple faces if multiple are found in the image.
        # We want the primary face (usually the largest).
        if not results:
            return None
            
        # Select the largest face by bounding box area (w * h)
        primary_face = max(results, key=lambda x: x['facial_area']['w'] * x['facial_area']['h'])
        embedding = np.array(primary_face['embedding'], dtype=np.float32)
        
        # L2-Normalize the embedding vector. 
        # This is critical because FAISS IndexFlatIP (Inner Product) on normalized vectors
        # is mathematically equivalent to Cosine Similarity.
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm
            
        return embedding
        
    except ValueError as e:
        # DeepFace throws ValueError if enforce_detection=True and no face is found
        print(f"[DeepFace] No face detected or error processing {image_path}: {e}")
        return None
    except Exception as e:
        print(f"[DeepFace] Unexpected error processing {image_path}: {e}")
        return None

def recognize_face(image_path: str):
    """
    Extract embedding from the image and search FAISS for a match.
    Returns (faiss_id, similarity) if a match > threshold is found, else (None, None).
    """
    embedding = get_embedding(image_path)
    
    if embedding is None:
        return None, None
        
    faiss_id, similarity = faiss_db.search_embedding(embedding)
    
    if faiss_id is not None:
        print(f"[Recognition] Match found: FAISS ID {faiss_id} with similarity {similarity:.3f}")
        return faiss_id, similarity
    else:
        print(f"[Recognition] No match found above threshold.")
        return None, None

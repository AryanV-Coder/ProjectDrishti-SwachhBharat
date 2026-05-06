# Data Ingestion (`self_data_upload.py`)

This document explains how the system is populated with known identities prior to runtime.

## Directory Structure
To register new individuals, their data must be organized in the `data_to_upload/` folder.
Each person gets their own subfolder.
```
data_to_upload/
    Person_Folder_Name/
        details.json     
        photo1.jpg
        photo2.jpg
```
The `details.json` must contain the email to which fines will be sent. The script extracts the person's real name from this JSON, falling back to the folder name if the JSON is missing or malformed.
```json
{
    "name": "Full Name",
    "email": "user@example.com"
}
```

## The Ingestion Process
Running `python self_data_upload.py` initiates the following sequence:

1. **SQLite Record Creation**: Reads the JSON metadata and creates a new entry in the `persons` table, generating a unique `person_id`.
2. **Embedding Extraction**: Iterates through all images in the folder and uses DeepFace to extract the 512D facial embedding. Images where no face is detected are safely skipped.
3. **FAISS Storage**: Reads the current size of the FAISS index to generate the next sequential `faiss_id`. The embedding is added to FAISS mapped to this exact ID.
4. **Relational Linking**: The `faiss_id` and the `person_id` are saved into the `face_embeddings_id` SQLite table, linking the vector to the person's identity.

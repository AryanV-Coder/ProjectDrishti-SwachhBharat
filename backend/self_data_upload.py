import os
import json
import glob
from utils import sqlite_db, faiss_db, deepface_recognition

def process_upload_folder(base_folder: str):
    """
    Process a folder containing subfolders of people.
    Expected structure:
    base_folder/
        Person_Name/
            details.json ({"email": "person@example.com"})
            img1.jpg
            img2.png
    """
    if not os.path.exists(base_folder):
        print(f"Folder '{base_folder}' does not exist.")
        return

    # Ensure DB tables exist
    sqlite_db.initialize_db()
    
    # Track the next faiss_id to use
    index = faiss_db.get_or_create_index()
    next_faiss_id = index.ntotal

    print(f"Starting data upload from '{base_folder}'...")

    for person_name in os.listdir(base_folder):
        person_dir = os.path.join(base_folder, person_name)
        if not os.path.isdir(person_dir):
            continue

        print(f"\nProcessing person: {person_name}")
        
        # Look for details.json
        details_path = os.path.join(person_dir, "details.json")
        
        # Defaults if JSON is missing or malformed
        person_name_from_json = person_name
        email = f"{person_name.lower().replace(' ', '.')}@example.com" 
        
        if os.path.exists(details_path):
            try:
                with open(details_path, 'r') as f:
                    details = json.load(f)
                    person_name_from_json = details.get("name", person_name)
                    email = details.get("email", email)
            except Exception as e:
                print(f"  Error reading details.json: {e}")

        # Add to SQLite
        person_id = sqlite_db.add_person(person_name_from_json, email)
        print(f"  Added to SQLite: ID={person_id}, Name={person_name_from_json}, Email={email}")

        # Process all images in the folder
        image_extensions = ('*.jpg', '*.jpeg', '*.png')
        image_paths = []
        for ext in image_extensions:
            image_paths.extend(glob.glob(os.path.join(person_dir, ext)))
            image_paths.extend(glob.glob(os.path.join(person_dir, ext.upper())))

        if not image_paths:
            print("  No images found. Skipping embeddings.")
            continue

        for img_path in image_paths:
            print(f"  Processing image: {os.path.basename(img_path)}")
            embedding = deepface_recognition.get_embedding(img_path)
            
            if embedding is not None:
                # Add to FAISS
                faiss_db.add_embedding(embedding, next_faiss_id)
                # Link FAISS ID to Person ID in SQLite
                sqlite_db.add_embedding_link(next_faiss_id, person_id)
                
                print(f"    -> Successfully mapped FAISS ID {next_faiss_id} to Person ID {person_id}")
                next_faiss_id += 1
            else:
                print("    -> Failed to extract embedding.")

    print("\nData upload complete.")

if __name__ == "__main__":
    # You can change this path or pass it as an argument
    UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_to_upload")
    
    if not os.path.exists(UPLOAD_DIR):
        print(f"Creating sample upload directory at {UPLOAD_DIR}")
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        print("Please add person folders inside 'data_to_upload' and run this script again.")
    else:
        process_upload_folder(UPLOAD_DIR)

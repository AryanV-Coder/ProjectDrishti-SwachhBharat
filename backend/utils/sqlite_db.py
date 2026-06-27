import sqlite3
import os
import config

def get_connection():
    """Create and return a database connection, creating the DB file if it doesn't exist."""
    db_path = config.SQLITE_DB_PATH
    os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
    conn = sqlite3.connect(db_path)
    return conn

def initialize_db():
    """Create the necessary tables according to the schema."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS persons (
            person_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS face_embeddings_id (
            faiss_id INTEGER PRIMARY KEY,
            person_id INTEGER NOT NULL,
            FOREIGN KEY (person_id) 
                REFERENCES persons (person_id) 
                ON DELETE CASCADE
                ON UPDATE CASCADE
        )
    ''')

    conn.commit()
    conn.close()

def add_person(name: str, email: str) -> int:
    """Insert a new person and return their auto-generated person_id."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO persons (name, email) VALUES (?, ?)", (name, email))
    person_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return person_id

def add_embedding_link(faiss_id: int, person_id: int):
    """Link a FAISS embedding ID to a person_id."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO face_embeddings_id (faiss_id, person_id) VALUES (?, ?)", (faiss_id, person_id))
    conn.commit()
    conn.close()

def get_person_by_faiss_id(faiss_id: int):
    """Retrieve person details (name, email) given a FAISS ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT p.name, p.email 
        FROM persons p
        JOIN face_embeddings_id f ON p.person_id = f.person_id
        WHERE f.faiss_id = ?
    ''', (faiss_id,))
    result = cursor.fetchone()
    conn.close()
    
    if result:
        return {"name": result[0], "email": result[1]}
    return None

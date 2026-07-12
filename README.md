# 🇮🇳 Project Drishti — SwachhBharat

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Status: Active](https://img.shields.io/badge/status-active-success.svg)](#)

> AI-Powered Littering Detection, Violator Identification & Automated Penalty System

**[🎥 See the Live Demo Here!](https://drive.google.com/file/d/1DsdMDOpNsNDCIIkZ-i0hOZVK5RwnV_Nu/view)**

## 📖 Project Overview

Project Drishti is an end-to-end AI surveillance pipeline that detects littering in real-time using computer vision, identifies the violator through facial recognition, and automatically dispatches an e-challan (fine notice) via email — all without human intervention.

---

## 🏗️ System Architecture

### End-to-End Pipeline

```mermaid
flowchart TB
    subgraph INPUT["📹 Input Sources"]
        CAM["Webcam / CCTV"]
        VID["Video File"]
        IMG["Static Image"]
    end

    subgraph DETECTION["🔍 Detection Layer"]
        YOLO["YOLOv8 Object Detection"]
        YOLO -->|Bounding Boxes| CLASSES["Class Separation"]
        CLASSES --> PERSONS["Humans"]
        CLASSES --> GARBAGE["Garbage"]
        CLASSES --> DUSTBINS["Dustbins"]
    end

    subgraph TRACKING["📍 Tracking Layer"]
        PERSONS --> PT["Person Tracker"]
        GARBAGE --> GT["Garbage Tracker"]
        DUSTBINS --> DT["Dustbin Tracker"]
        PT & GT & DT --> SA["Spatial Analyzer"]
    end

    subgraph STATEMACHINE["🧠 Littering Inference Engine"]
        SA --> SM["State Machine"]
        SM --> S1["UNTRACKED"]
        S1 -->|"Person near garbage"| S2["ATTACHED"]
        S2 -->|"Distance increasing"| S3["DETACHING"]
        S3 -->|"Garbage stationary"| S4["MONITORING"]
        S4 -->|"Person walked away"| S5["LITTERING_CONFIRMED 🚨"]
        S3 -->|"Person picks it back up"| S2
    end

    subgraph EVIDENCE["📸 Evidence Collection"]
        S5 --> FRAME["Save Violation Frame"]
        S5 --> FACE["Crop Violator Face via MediaPipe"]
    end

    subgraph RECOGNITION["🔐 Facial Recognition"]
        FACE --> DEEPFACE["DeepFace Facenet512"]
        DEEPFACE -->|"512D Embedding"| FAISS["FAISS Vector Search"]
        FAISS -->|"Matched faiss_id"| SQLITE["SQLite Lookup"]
        SQLITE -->|"Name + Email"| EMAIL["SMTP Email Dispatch"]
    end

    INPUT --> YOLO
    FRAME --> EMAIL
```

### Data Ingestion Pipeline

```mermaid
flowchart LR
    subgraph UPLOAD["data_to_upload"]
        FOLDER["Person Folder"] --> JSON["details.json"]
        FOLDER --> PHOTOS["Face Photos"]
    end

    subgraph PROCESSING["self_data_upload.py"]
        JSON -->|Parse| SQLINSERT["SQLite: Insert Person"]
        SQLINSERT -->|person_id| LINK["Link IDs"]
        PHOTOS -->|DeepFace| EMBED["Extract 512D Embedding"]
        EMBED -->|L2 Normalize| FAISSADD["FAISS: Add with custom ID"]
        FAISSADD -->|faiss_id| LINK
        LINK --> BRIDGE["SQLite: face_embeddings_id"]
    end
```

### Database Schema

```mermaid
erDiagram
    persons ||--o{ face_embeddings_id : has
    persons {
        int person_id PK
        text name
        text email
    }
    face_embeddings_id {
        int faiss_id PK
        int person_id FK
    }
    FAISS_INDEX {
        int faiss_id
        blob embedding
    }
    face_embeddings_id ||--|| FAISS_INDEX : maps_to
```

### State Machine Transitions

```mermaid
stateDiagram-v2
    [*] --> UNTRACKED
    UNTRACKED --> ATTACHED : Person near garbage
    ATTACHED --> DETACHING : Distance increasing
    DETACHING --> ATTACHED : Person picks it back up
    DETACHING --> MONITORING : Garbage stationary N frames
    MONITORING --> DETACHING : Garbage moves again
    MONITORING --> LITTERING_CONFIRMED : Person far away N frames
    LITTERING_CONFIRMED --> [*]
```

---

## ✨ Key Features

| Feature | Description |
|---|---|
| **Real-Time Detection** | YOLOv8 detects Humans, Garbage, and Dustbins simultaneously |
| **Temporal State Machine** | Tracks person-garbage relationship over time to infer littering behavior |
| **State Inheritance** | Handles YOLO detection gaps during drops by transferring state to new IDs |
| **Dustbin-Aware** | Ignores garbage disposed near dustbins (legitimate disposal) |
| **Face Cropping** | MediaPipe isolates the violator's face from the person bounding box |
| **Facial Recognition** | DeepFace (Facenet512) + FAISS for high-speed identity matching |
| **Automated E-Challan** | SMTP email with violation image and Rs. 500 fine notice |
| **Bulk Data Ingestion** | Admin script to register identities from folders of images + JSON |

---

## 💻 Tech Stack

| Layer | Technology |
|---|---|
| Object Detection | YOLOv8 (Ultralytics) |
| Object Tracking | Custom Centroid Tracker (SciPy) |
| Face Detection | MediaPipe |
| Face Recognition | DeepFace (Facenet512 + MTCNN) |
| Vector Database | FAISS (IndexFlatIP + IndexIDMap) |
| Relational Database | SQLite |
| Email System | Python smtplib (Gmail SMTP) |
| Configuration | python-dotenv |

---

## 📂 Project Structure

```
ProjectDrishti_SwachhBharat/
├── README.md
└── backend/
    ├── config.py                  # Centralized thresholds & settings
    ├── detector.py                # YOLO inference wrapper
    ├── tracker.py                 # Centroid-based object tracker
    ├── spatial_analyzer.py        # Distance & proximity calculations
    ├── littering_detector.py      # State machine engine
    ├── pipeline.py                # Orchestrator (Detection → Tracking → Inference → Recognition → Email)
    ├── main_webcam.py             # Entry point: Live webcam
    ├── main_video.py              # Entry point: Video file
    ├── main_photo.py              # Entry point: Static image
    ├── self_data_upload.py        # Bulk identity registration script
    ├── best.pt                    # Trained YOLO model weights
    ├── requirements.txt           # Python dependencies
    ├── .env                       # SMTP credentials (not committed)
    ├── utils/
    │   ├── sqlite_db.py           # SQLite operations
    │   ├── faiss_db.py            # FAISS operations
    │   ├── deepface_recognition.py # Embedding extraction & matching
    │   └── emailer.py             # SMTP email dispatch
    ├── CONTEXT/                   # Architecture documentation
    ├── violation/                 # Saved violation evidence (auto-generated)
    └── garbage_detected/          # Cropped garbage images (auto-generated)
```

---

## 🚀 Quick Start

### 1. Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure Email Credentials
Create a `.env` file in `backend/`:
```env
SMTP_EMAIL=your_email@gmail.com
SMTP_APP_PASSWORD=your_gmail_app_password
```

### 3. Register Identities
Place person folders inside `backend/data_to_upload/`:
```
data_to_upload/
    Aryan Varshney/
        details.json    → {"name": "Aryan Varshney", "email": "arv.coder@gmail.com"}
        photo1.jpg
```
Then run:
```bash
python self_data_upload.py
```

### 4. Run the System
```bash
# Live webcam
python main_webcam.py

# Video file
python main_video.py --source videos/test.mp4
```

---

## 🇮🇳 Contributing to a Cleaner India

This project supports the **Swachh Bharat (Clean India)** initiative by leveraging AI to enforce cleanliness standards and deter public littering through automated monitoring and penalties. We welcome contributions to make our surroundings cleaner and greener!
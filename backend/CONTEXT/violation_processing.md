# Violation Processing (Recognition & Emailing)

This document explains the runtime flow that executes when a littering event is confirmed.

## 1. Face Cropping
Before recognition, the system isolates the violator's face from the full video frame to improve accuracy.
- **Optimization**: Instead of searching the entire frame, it uses the YOLO bounding box of the person who dropped the garbage.
- **Detection**: MediaPipe Face Detection scans only that specific region, crops the face, and resizes it to 256x256.

## 2. Facial Recognition (`deepface_recognition.py`)
- **Model**: Uses DeepFace with the `Facenet512` model and `mtcnn` detector.
- **Execution**: Extracts a 512-dimensional embedding from the cropped face.
- **Safety**: `enforce_detection=True` ensures that if no face is visible (e.g., turned away), it fails gracefully rather than returning noise.
- **Matching**: The embedding is sent to FAISS. If the similarity score exceeds `FACE_SIMILARITY_THRESHOLD` (0.60), the identity is confirmed.

## 3. Automated Notification (`emailer.py`)
Once identified via SQLite:
- The system constructs a violation notice stating the rule broken and the Rs. 500 fine.
- The **full annotated violation frame** (not the face crop) is attached as photographic evidence.
- The email is dispatched via Gmail SMTP using credentials securely loaded from the `.env` file.

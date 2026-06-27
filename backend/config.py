"""
Configuration parameters for the Littering Detection System.
All tunable thresholds and settings are centralized here.
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ─── YOLO Model Settings ───────────────────────────────────────────────
YOLO_MODEL_PATH = "best.pt"          # Path to YOLO model weights (relative to backend/)
YOLO_CONFIDENCE = 0.50                # Minimum detection confidence threshold
YOLO_PERSON_CONFIDENCE = 0.80         # Higher threshold for person detection (reduce false positives)
YOLO_IOU_THRESHOLD = 0.45           # NMS IoU threshold for YOLO
YOLO_IMG_SIZE = 320                  # Input resolution for YOLO (lower = faster, 320/416/640)

# ─── File Paths & Credentials ─────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SQLITE_DB_PATH = os.path.join(BASE_DIR, "face_database.db")
FAISS_INDEX_PATH = os.path.join(BASE_DIR, "face_index.faiss")

SMTP_EMAIL = os.getenv("SMTP_EMAIL", "")
SMTP_APP_PASSWORD = os.getenv("SMTP_APP_PASSWORD", "")

FACE_SIMILARITY_THRESHOLD = 0.50    # Cosine similarity threshold for FAISS matching (lower = more matches)

# ─── Class Names (must match your YOLO model's training labels) ─────
CLASS_NAMES = {
    "person": "Human",      # YOLO label for people
    "garbage": "Garbage",   # YOLO label for garbage/litter
    "dustbin": "Dustbin",   # YOLO label for dustbins
}

# ─── Frame Sampling ────────────────────────────────────────────────────
FRAME_SAMPLE_RATE = 5               # Process every Nth frame (1 = every frame, higher = faster)

# ─── Tracker Settings ──────────────────────────────────────────────────
MAX_DISAPPEARED_FRAMES = 15         # Frames before a person is deregistered
MAX_TRACKING_DISTANCE = 200         # Max pixel distance for person centroid matching

# Garbage tracker needs higher tolerance — YOLO often loses detection
# during the drop action (motion blur, bounding box shape change)
GARBAGE_MAX_DISAPPEARED = 25        # Garbage can vanish for longer before deregistering
GARBAGE_MAX_TRACKING_DISTANCE = 250 # Larger matching radius for garbage (centroid shifts on drop)
GARBAGE_STATE_MEMORY_FRAMES = 20    # Remember recently-lost garbage states for this many frames

# ─── Spatial Analysis Thresholds ─────────────────────────────────────────
# Adaptive thresholds normalized to the tracked person's bounding box height.
# This makes the system camera-agnostic — a 720p webcam and a 4K CCTV camera
# will produce identical logical behaviour for the same real-world scene.
PROXIMITY_SCALE = 0.40        # Garbage within 40% of person height → "attached" (hand/waist level)
SEPARATION_SCALE = 0.55       # Garbage beyond 55% of person height → person has "walked away"

# Static pixel fallbacks — used only when no person bbox is available
PROXIMITY_THRESHOLD = 200     # px fallback
SEPARATION_THRESHOLD = 300    # px fallback

DUSTBIN_PROXIMITY = 100       # px — static; dustbin proximity has no person-size reference

# ─── Temporal Analysis Thresholds ───────────────────────────────────────
VELOCITY_THRESHOLD = 5.0            # Below this (px/frame) = garbage is stationary
STATIONARY_FRAMES = 4               # Garbage must be stationary for this many frames → MONITORING
PERSON_MOVING_AWAY_FRAMES = 2       # Person must be beyond separation threshold for N frames to confirm
MONITORING_TIMEOUT_FRAMES = 6       # Frames in MONITORING before confirming littering by timeout (~1s at 30fps/skip-5)
PERSON_HISTORY_FRAMES = 10          # Frames of person movement history to examine (sitting-person guard)
BUFFER_SIZE = 30                    # Temporal buffer length (history per object)

# ─── Display Settings ──────────────────────────────────────────────────
SHOW_DISPLAY = True                 # Show annotated video window
DISPLAY_WIDTH = 1280                # Resize display to this width (0 = no resize)
DISPLAY_HEIGHT = 720                # Resize display to this height (0 = no resize)

# ─── Logging ────────────────────────────────────────────────────────────
LOG_STATE_TRANSITIONS = True        # Print state transitions to console
LOG_DETECTIONS = True               # Print detection counts per frame

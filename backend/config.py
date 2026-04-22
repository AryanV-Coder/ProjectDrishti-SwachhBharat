"""
Configuration parameters for the Littering Detection System.
All tunable thresholds and settings are centralized here.
"""

# ─── YOLO Model Settings ───────────────────────────────────────────────
YOLO_MODEL_PATH = "best.pt"          # Path to YOLO model weights (relative to backend/)
YOLO_CONFIDENCE = 0.5                # Minimum detection confidence threshold
YOLO_IOU_THRESHOLD = 0.45           # NMS IoU threshold for YOLO
YOLO_IMG_SIZE = 320                  # Input resolution for YOLO (lower = faster, 320/416/640)

# ─── Class Names (must match your YOLO model's training labels) ─────
CLASS_NAMES = {
    "person": "Human",      # YOLO label for people
    "garbage": "Garbage",   # YOLO label for garbage/litter
    "dustbin": "Dustbin",   # YOLO label for dustbins
}

# ─── Frame Sampling ────────────────────────────────────────────────────
FRAME_SAMPLE_RATE = 5               # Process every Nth frame (1 = every frame, higher = faster)

# ─── Tracker Settings ──────────────────────────────────────────────────
MAX_DISAPPEARED_FRAMES = 15         # Frames before an object is deregistered
MAX_TRACKING_DISTANCE = 200         # Max pixel distance for centroid matching

# ─── Spatial Analysis Thresholds ────────────────────────────────────────
PROXIMITY_THRESHOLD = 150           # Max distance (px) to consider person-garbage "attached"
SEPARATION_THRESHOLD = 300          # Min distance (px) to confirm person has walked away
DUSTBIN_PROXIMITY = 100             # If garbage is within this distance of a dustbin, NOT littering

# ─── Temporal Analysis Thresholds ───────────────────────────────────────
VELOCITY_THRESHOLD = 5.0            # Below this (px/frame) = garbage is stationary
STATIONARY_FRAMES = 8               # Garbage must be stationary for this many frames
PERSON_MOVING_AWAY_FRAMES = 5       # Person must be moving away for this many frames
BUFFER_SIZE = 30                    # Temporal buffer length (history per object)

# ─── Display Settings ──────────────────────────────────────────────────
SHOW_DISPLAY = True                 # Show annotated video window
DISPLAY_WIDTH = 1280                # Resize display to this width (0 = no resize)
DISPLAY_HEIGHT = 720                # Resize display to this height (0 = no resize)

# ─── Logging ────────────────────────────────────────────────────────────
LOG_STATE_TRANSITIONS = True        # Print state transitions to console
LOG_DETECTIONS = True               # Print detection counts per frame

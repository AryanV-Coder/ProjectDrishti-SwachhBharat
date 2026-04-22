"""
Littering Detection Pipeline.
Orchestrates: Frame → Detection → Tracking → Spatial Analysis → Littering Logic.
"""

import cv2
import numpy as np
import os
import time as time_module
from typing import Dict, List

from detector import ObjectDetector
from tracker import CentroidTracker, TrackedObject
from littering_detector import LitteringDetector, LitteringEvent
import config

# Create output folder for garbage evidence
GARBAGE_OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "garbage_detected")
os.makedirs(GARBAGE_OUTPUT_DIR, exist_ok=True)


class LitteringPipeline:
    """
    Main pipeline that ties all modules together.
    
    Usage:
        pipeline = LitteringPipeline()
        events = pipeline.process_frame(frame)
        annotated = pipeline.draw_annotations(frame)
    """

    def __init__(self, model_path: str = None):
        # Initialize components
        self.detector = ObjectDetector(model_path=model_path)
        self.person_tracker = CentroidTracker()
        self.garbage_tracker = CentroidTracker(
            max_disappeared=config.GARBAGE_MAX_DISAPPEARED,
            max_distance=config.GARBAGE_MAX_TRACKING_DISTANCE,
        )
        self.dustbin_tracker = CentroidTracker()
        self.littering_detector = LitteringDetector()

        # Store latest tracking results for annotation
        self.tracked_persons: Dict[int, TrackedObject] = {}
        self.tracked_garbage: Dict[int, TrackedObject] = {}
        self.tracked_dustbins: Dict[int, TrackedObject] = {}
        self.latest_events: List[LitteringEvent] = []
        self.all_events: List[LitteringEvent] = []

        # Frame counter
        self.frame_count = 0

        print("[Pipeline] Initialized successfully")

    def process_frame(self, frame) -> List[LitteringEvent]:
        """
        Process a single frame through the full pipeline.
        
        Args:
            frame: BGR numpy array (OpenCV format)
            
        Returns:
            List of LitteringEvent objects detected this frame
        """
        self.frame_count += 1

        # 1. Run YOLO detection
        detections = self.detector.detect(frame)

        # 2. Separate detections by class
        person_dets = self.detector.filter_by_class(detections, config.CLASS_NAMES["person"])
        garbage_dets = self.detector.filter_by_class(detections, config.CLASS_NAMES["garbage"])
        dustbin_dets = self.detector.filter_by_class(detections, config.CLASS_NAMES["dustbin"])

        # Apply stricter confidence threshold for persons
        person_dets = [d for d in person_dets if d.confidence >= config.YOLO_PERSON_CONFIDENCE]

        # 3. Update trackers
        self.tracked_persons = self.person_tracker.update(person_dets)
        self.tracked_garbage = self.garbage_tracker.update(garbage_dets)
        self.tracked_dustbins = self.dustbin_tracker.update(dustbin_dets)

        # 4. Run littering detection logic
        self.latest_events = self.littering_detector.update(
            self.tracked_persons,
            self.tracked_garbage,
            self.tracked_dustbins,
        )

        self.all_events.extend(self.latest_events)

        # 5. Save cropped garbage images for confirmed events
        if self.latest_events:
            self._save_garbage_crops(frame, self.latest_events)

        return self.latest_events

    def _save_garbage_crops(self, frame, events: List[LitteringEvent]):
        """Save cropped garbage region from the frame for each confirmed event."""
        h, w = frame.shape[:2]
        padding = 20  # Extra pixels around the bounding box

        for event in events:
            x1, y1, x2, y2 = event.garbage_bbox

            # Add padding and clamp to frame bounds
            x1 = max(0, x1 - padding)
            y1 = max(0, y1 - padding)
            x2 = min(w, x2 + padding)
            y2 = min(h, y2 + padding)

            crop = frame[y1:y2, x1:x2]
            if crop.size == 0:
                continue

            timestamp = time_module.strftime("%Y%m%d_%H%M%S", time_module.localtime(event.timestamp))
            filename = f"garbage_person{event.person_id}_g{event.garbage_id}_{timestamp}.jpg"
            filepath = os.path.join(GARBAGE_OUTPUT_DIR, filename)

            cv2.imwrite(filepath, crop, [cv2.IMWRITE_JPEG_QUALITY, 95])
            print(f"[Pipeline] Garbage evidence saved: {filepath}")

    def draw_annotations(self, frame) -> np.ndarray:
        """
        Draw bounding boxes, IDs, and littering alerts on the frame.
        
        Args:
            frame: BGR numpy array
            
        Returns:
            Annotated frame
        """
        annotated = frame.copy()

        # ── Draw persons (green) ─────────────────────────────────
        for pid, person in self.tracked_persons.items():
            x1, y1, x2, y2 = person.bbox
            cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 255, 0), 2)
            label = f"Person #{pid}"
            cv2.putText(
                annotated, label, (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2,
            )

        # ── Draw dustbins (yellow) ────────────────────────────────
        for did, dustbin in self.tracked_dustbins.items():
            x1, y1, x2, y2 = dustbin.bbox
            cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 255, 255), 2)
            label = f"Dustbin #{did}"
            cv2.putText(
                annotated, label, (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2,
            )

        # ── Draw garbage (color based on state) ──────────────────
        garbage_states = self.littering_detector.get_active_states()
        for gid, garbage in self.tracked_garbage.items():
            x1, y1, x2, y2 = garbage.bbox
            state = garbage_states.get(gid, "UNTRACKED")

            # Color by state
            color = {
                "UNTRACKED": (200, 200, 200),       # gray
                "ATTACHED": (255, 165, 0),            # orange
                "DETACHING": (0, 165, 255),           # orange-blue
                "MONITORING": (0, 0, 255),            # red
                "LITTERING_CONFIRMED": (0, 0, 255),   # red
            }.get(state, (200, 200, 200))

            thickness = 3 if state == "LITTERING_CONFIRMED" else 2
            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, thickness)

            label = f"Garbage #{gid} [{state}]"
            cv2.putText(
                annotated, label, (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2,
            )

        # ── Draw littering alerts ────────────────────────────────
        if self.latest_events:
            for event in self.latest_events:
                # Big alert text at top
                alert_text = f"LITTERING DETECTED! Person #{event.person_id}"
                text_size = cv2.getTextSize(alert_text, cv2.FONT_HERSHEY_SIMPLEX, 1.0, 3)[0]
                text_x = (annotated.shape[1] - text_size[0]) // 2
                cv2.putText(
                    annotated, alert_text, (text_x, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 3,
                )

        # ── Draw stats bar ───────────────────────────────────────
        stats = (
            f"Frame: {self.frame_count} | "
            f"Persons: {len(self.tracked_persons)} | "
            f"Garbage: {len(self.tracked_garbage)} | "
            f"Dustbins: {len(self.tracked_dustbins)} | "
            f"Total Events: {len(self.all_events)}"
        )
        cv2.putText(
            annotated, stats, (10, annotated.shape[0] - 15),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1,
        )

        return annotated

    def reset(self):
        """Reset all trackers and detectors."""
        self.person_tracker.reset()
        self.garbage_tracker.reset()
        self.dustbin_tracker.reset()
        self.littering_detector.reset()
        self.tracked_persons.clear()
        self.tracked_garbage.clear()
        self.tracked_dustbins.clear()
        self.latest_events.clear()
        self.all_events.clear()
        self.frame_count = 0

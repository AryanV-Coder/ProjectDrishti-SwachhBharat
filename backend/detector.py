"""
YOLO Object Detector wrapper.
Loads the YOLO model and returns structured Detection objects per frame.
"""

from dataclasses import dataclass
from typing import List, Tuple
from ultralytics import YOLO
import config


@dataclass
class Detection:
    """A single detection from YOLO."""
    bbox: Tuple[int, int, int, int]   # (x1, y1, x2, y2)
    confidence: float
    class_name: str                    # "human", "garbage", or "dustbin"
    centroid: Tuple[int, int]          # (cx, cy)


class ObjectDetector:
    """Thin wrapper around YOLOv8 for person/garbage/dustbin detection."""

    def __init__(self, model_path: str = None, confidence: float = None):
        self.model_path = model_path or config.YOLO_MODEL_PATH
        self.confidence = confidence or config.YOLO_CONFIDENCE
        self.model = YOLO(self.model_path)

        # Build reverse lookup: YOLO class index → our label
        # e.g., {0: "human", 1: "garbage", 2: "dustbin"}
        self.class_map = self.model.names  # dict[int, str] from YOLO

        print(f"[Detector] Loaded model: {self.model_path}")
        print(f"[Detector] Classes: {self.class_map}")
        print(f"[Detector] Confidence threshold: {self.confidence}")

    def detect(self, frame) -> List[Detection]:
        """
        Run YOLO inference on a single frame.
        
        Args:
            frame: BGR numpy array (OpenCV format)
            
        Returns:
            List of Detection objects
        """
        results = self.model(
            frame,
            conf=self.confidence,
            iou=config.YOLO_IOU_THRESHOLD,
            imgsz=config.YOLO_IMG_SIZE,
            verbose=False,
        )

        detections = []

        for result in results:
            boxes = result.boxes
            if boxes is None:
                continue

            for box in boxes:
                # Extract bbox coordinates
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
                confidence = float(box.conf[0].cpu().numpy())
                class_id = int(box.cls[0].cpu().numpy())
                class_name = self.class_map.get(class_id, "unknown")

                # Compute centroid
                cx = (x1 + x2) // 2
                cy = (y1 + y2) // 2

                detections.append(Detection(
                    bbox=(x1, y1, x2, y2),
                    confidence=confidence,
                    class_name=class_name,
                    centroid=(cx, cy),
                ))

        if config.LOG_DETECTIONS:
            counts = {}
            for d in detections:
                counts[d.class_name] = counts.get(d.class_name, 0) + 1
            print(f"[Detector] Detections: {counts}")

        return detections

    def filter_by_class(self, detections: List[Detection], class_name: str) -> List[Detection]:
        """Filter detections to only include a specific class."""
        return [d for d in detections if d.class_name == class_name]

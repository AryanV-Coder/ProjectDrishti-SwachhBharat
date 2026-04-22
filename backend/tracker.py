"""
Simple Centroid-Based Object Tracker.
Assigns persistent IDs to detections across frames using nearest-centroid matching.
"""

from collections import OrderedDict
from typing import Dict, List, Tuple
from scipy.spatial import distance as dist
import numpy as np

from detector import Detection
import config


class TrackedObject:
    """Represents a tracked object with persistent ID."""

    def __init__(self, object_id: int, detection: Detection):
        self.object_id = object_id
        self.detection = detection
        self.centroid = detection.centroid
        self.bbox = detection.bbox
        self.class_name = detection.class_name
        self.confidence = detection.confidence

    def update(self, detection: Detection):
        """Update tracked object with new detection data."""
        self.detection = detection
        self.centroid = detection.centroid
        self.bbox = detection.bbox
        self.confidence = detection.confidence


class CentroidTracker:
    """
    Tracks objects across frames by matching centroids.
    
    Each new detection is matched to the closest existing tracked object.
    If no match is found within MAX_TRACKING_DISTANCE, a new ID is assigned.
    Objects disappearing for more than MAX_DISAPPEARED_FRAMES are deregistered.
    """

    def __init__(self, max_disappeared: int = None, max_distance: float = None):
        self.max_disappeared = max_disappeared or config.MAX_DISAPPEARED_FRAMES
        self.max_distance = max_distance or config.MAX_TRACKING_DISTANCE

        self.next_id = 0
        self.objects: OrderedDict[int, TrackedObject] = OrderedDict()
        self.disappeared: Dict[int, int] = {}

    def _register(self, detection: Detection) -> int:
        """Register a new object and return its ID."""
        object_id = self.next_id
        self.objects[object_id] = TrackedObject(object_id, detection)
        self.disappeared[object_id] = 0
        self.next_id += 1
        return object_id

    def _deregister(self, object_id: int):
        """Remove an object from tracking."""
        del self.objects[object_id]
        del self.disappeared[object_id]

    def update(self, detections: List[Detection]) -> Dict[int, TrackedObject]:
        """
        Update tracker with new detections.
        
        Args:
            detections: List of Detection objects (should be pre-filtered by class)
            
        Returns:
            Dict mapping object_id → TrackedObject
        """
        # If no detections, mark all existing as disappeared
        if len(detections) == 0:
            for object_id in list(self.disappeared.keys()):
                self.disappeared[object_id] += 1
                if self.disappeared[object_id] > self.max_disappeared:
                    self._deregister(object_id)
            return dict(self.objects)

        # If no existing objects, register all detections
        if len(self.objects) == 0:
            for det in detections:
                self._register(det)
            return dict(self.objects)

        # Match existing objects to new detections using centroid distance
        object_ids = list(self.objects.keys())
        object_centroids = np.array([self.objects[oid].centroid for oid in object_ids])
        detection_centroids = np.array([d.centroid for d in detections])

        # Compute pairwise distances
        D = dist.cdist(object_centroids, detection_centroids)

        # Find best matches (greedy: smallest distance first)
        rows = D.min(axis=1).argsort()
        cols = D.argmin(axis=1)[rows]

        used_rows = set()
        used_cols = set()

        for (row, col) in zip(rows, cols):
            if row in used_rows or col in used_cols:
                continue

            # Only match if within max distance
            if D[row, col] > self.max_distance:
                continue

            object_id = object_ids[row]
            self.objects[object_id].update(detections[col])
            self.disappeared[object_id] = 0

            used_rows.add(row)
            used_cols.add(col)

        # Handle unmatched existing objects (disappeared)
        unused_rows = set(range(len(object_ids))) - used_rows
        for row in unused_rows:
            object_id = object_ids[row]
            self.disappeared[object_id] += 1
            if self.disappeared[object_id] > self.max_disappeared:
                self._deregister(object_id)

        # Handle unmatched new detections (register new objects)
        unused_cols = set(range(len(detections))) - used_cols
        for col in unused_cols:
            self._register(detections[col])

        return dict(self.objects)

    def reset(self):
        """Clear all tracked objects."""
        self.objects.clear()
        self.disappeared.clear()
        self.next_id = 0

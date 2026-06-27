"""
Spatial Analysis Utilities.
Stateless math functions for distance, overlap, and proximity calculations.
"""

import math
from typing import Dict, Optional, Tuple

from tracker import TrackedObject


def euclidean_distance(p1: Tuple[int, int], p2: Tuple[int, int]) -> float:
    """Compute Euclidean distance between two points."""
    return math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)


def compute_iou(box1: Tuple[int, int, int, int], box2: Tuple[int, int, int, int]) -> float:
    """
    Compute Intersection over Union between two bounding boxes.
    Each box is (x1, y1, x2, y2).
    """
    x1 = max(box1[0], box2[0])
    y1 = max(box1[1], box2[1])
    x2 = min(box1[2], box2[2])
    y2 = min(box1[3], box2[3])

    intersection = max(0, x2 - x1) * max(0, y2 - y1)
    if intersection == 0:
        return 0.0

    area1 = (box1[2] - box1[0]) * (box1[3] - box1[1])
    area2 = (box2[2] - box2[0]) * (box2[3] - box2[1])
    union = area1 + area2 - intersection

    return intersection / union if union > 0 else 0.0


def is_inside(inner_box: Tuple[int, int, int, int], outer_box: Tuple[int, int, int, int]) -> bool:
    """Check if the centroid of inner_box lies within outer_box."""
    cx = (inner_box[0] + inner_box[2]) // 2
    cy = (inner_box[1] + inner_box[3]) // 2
    return (outer_box[0] <= cx <= outer_box[2]) and (outer_box[1] <= cy <= outer_box[3])


def find_nearest_person(
    garbage_centroid: Tuple[int, int],
    tracked_persons: Dict[int, TrackedObject],
) -> Tuple[Optional[int], float]:
    """
    Find the nearest person to a garbage object.
    
    Args:
        garbage_centroid: (cx, cy) of the garbage object
        tracked_persons: Dict of tracked person objects
        
    Returns:
        (person_id, distance) — person_id is None if no persons exist
    """
    if not tracked_persons:
        return None, float("inf")

    min_dist = float("inf")
    nearest_id = None

    for person_id, person in tracked_persons.items():
        d = euclidean_distance(garbage_centroid, person.centroid)
        if d < min_dist:
            min_dist = d
            nearest_id = person_id

    return nearest_id, min_dist


def is_near_dustbin(
    garbage_centroid: Tuple[int, int],
    tracked_dustbins: Dict[int, TrackedObject],
    threshold: float,
) -> bool:
    """
    Check if garbage is near any dustbin (i.e., likely NOT littering).
    
    Args:
        garbage_centroid: (cx, cy) of the garbage
        tracked_dustbins: Dict of tracked dustbin objects
        threshold: Max distance to consider "near" a dustbin
        
    Returns:
        True if garbage is near a dustbin
    """
    for dustbin in tracked_dustbins.values():
        if euclidean_distance(garbage_centroid, dustbin.centroid) < threshold:
            return True
    return False

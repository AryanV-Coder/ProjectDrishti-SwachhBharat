# YOLO & Object Tracking Architecture

This document explains exactly what information the system receives from YOLO and how that data is used to maintain object tracking IDs across frames.

## 1. What does YOLO return?

For every frame passed to YOLO, it performs a completely fresh, independent scan. **YOLO does not have any memory of previous frames.**

When YOLO detects objects in a frame, it returns a list of bounding boxes. For each box, it provides three pieces of information:

1. **Bounding Box Coordinates**: `[x1, y1, x2, y2]` (the pixel coordinates defining the rectangle around the object).
2. **Confidence Score**: A float from `0.0` to `1.0` (e.g., `0.85` means YOLO is 85% confident in its detection).
3. **Class ID**: An integer mapping to a label (e.g., `0 = Dustbin`, `1 = Garbage`, `2 = Human`).

*Crucially, YOLO does NOT return an Object ID. It doesn't know if the garbage in frame 2 is the same garbage from frame 1.*

---

## 2. How is the object tracked? (The Centroid Tracker)

Because YOLO doesn't provide persistent IDs, the system relies on a custom memory architecture called a **Centroid Tracking Algorithm** (implemented in `backend/tracker.py`) to connect the dots between frames.

Here is the step-by-step logic for how the tracker works:

### Step A: Calculate Centroids
For every bounding box YOLO finds in the current frame, the tracker calculates its **centroid** (the exact center coordinate `(x, y)` of the box).

### Step B: Compare to Memory (The previous frame)
The tracker maintains a dictionary of all objects it was tracking in the *previous* frame. It calculates the geometric distance (Euclidean distance) between all the *new* centroids from the current frame and all the *old* centroids from its memory.

### Step C: Match and Assign
The algorithm relies on the assumption that **objects do not teleport.** Therefore, if a new centroid is physically very close to an old centroid, they are assumed to be the same object.

- The tracker matches the new detection to the old detection with the shortest geometric distance between them.
- To prevent matching an object that moved too far (or a completely different object), a `MAX_TRACKING_DISTANCE` is enforced (e.g., 200 pixels). If the distance exceeds this threshold, the match is rejected.

---

## 3. How is the ID maintained?

The tracker uses three primary rules to assign and maintain IDs over time:

1. **Registering a New ID**: 
   If YOLO finds an object, and its centroid is *not* close to any existing object in the tracker's memory, the tracker assumes this is a brand new object. It assigns it the next available sequential integer ID (e.g., `Garbage #4`) and saves its current position.

2. **Updating an Existing ID**: 
   If a new detection successfully matches an old object in memory, the tracker updates that object's position with the new centroid, but **keeps the same ID** (`Garbage #4`). This mechanism allows the ID to persist as the object moves across the camera's field of view.

3. **Deregistering an ID (Disappearance)**: 
   If YOLO fails to detect an object in the current frame (due to occlusion, motion blur, or leaving the frame), the tracker doesn't delete it immediately. It increments a "disappeared" counter for that object.
   - If the object is missing for just a few frames, the tracker remembers its last known location.
   - If the object stays missing for more than `MAX_DISAPPEARED_FRAMES` (e.g., 15 frames for humans, 25 frames for garbage), the tracker assumes the object is gone permanently and deletes that ID from memory.

### Summary
YOLO acts as the "eyes" of the system (finding objects in a single isolated picture), while the Centroid Tracker acts as the "brain" (connecting those pictures together by assuming that objects located close to each other in consecutive frames are the same physical entity).

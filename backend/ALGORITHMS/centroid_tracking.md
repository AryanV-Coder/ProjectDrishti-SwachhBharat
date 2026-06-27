# Centroid Tracking Algorithm

YOLO provides detections per frame but has no memory of previous frames — it cannot tell if a person in frame 10 is the same person from frame 9. The Centroid Tracking Algorithm solves this by maintaining object identity across frames.

## How it works
1. For every bounding box detected by YOLO, the centroid (geometric center) is calculated as: **C = ((x₁ + x₂) / 2, (y₁ + y₂) / 2)**
2. The algorithm maintains a registry of all previously tracked objects with their last known centroids.
3. On each new frame, it computes the **Euclidean Distance** between every new centroid and every existing centroid using the formula: **d = √((x₂ − x₁)² + (y₂ − y₁)²)**
4. Using the **Hungarian Algorithm** (via SciPy's `linear_sum_assignment`), it finds the optimal one-to-one matching that minimizes total distance.
5. If a match distance exceeds a threshold (`MAX_TRACKING_DISTANCE`), the match is rejected and the detection is registered as a new object with a new ID.
6. If an existing object is not matched for several consecutive frames (`MAX_DISAPPEARED_FRAMES`), it is deregistered from memory.

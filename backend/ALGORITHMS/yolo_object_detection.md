# YOLOv8 (You Only Look Once)

YOLO is a single-stage, real-time object detection algorithm. Unlike traditional two-stage detectors (like R-CNN) which first propose regions and then classify them, YOLO treats detection as a single regression problem — it looks at the entire image **only once** in a single forward pass through its neural network and simultaneously predicts all bounding boxes and their class probabilities.

## How it works internally
1. The input image is divided into an S × S grid of cells.
2. Each grid cell is responsible for predicting a fixed number of bounding boxes.
3. For each bounding box, the network predicts 5 values: the x, y coordinates of the center, width, height, and a confidence score representing how likely the box contains an object.
4. Simultaneously, each cell predicts class probabilities (e.g., Human: 0.92, Garbage: 0.05, Dustbin: 0.03).
5. **Non-Maximum Suppression (NMS)** is applied to eliminate duplicate/overlapping boxes, keeping only the most confident prediction per object.

## Application in Project Drishti
In our project, we use a custom-trained YOLOv8 model (`best.pt`) fine-tuned to detect three classes: **Human**, **Garbage**, and **Dustbin**. The model operates at a reduced input resolution of 320×320 pixels to optimize for CPU inference speed, with a general confidence threshold of 0.50 and a stricter threshold of 0.80 for human detections to reduce false positives.

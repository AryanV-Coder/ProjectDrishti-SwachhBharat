"""
Photo Test — Run littering detection on a single image.

This mode does NOT perform temporal analysis (no state machine).
It only runs YOLO detection + spatial analysis to show what the system detects.

Usage:
    python main_photo.py --source path/to/image.jpg
    python main_photo.py --source image.jpg --model best.pt
    python main_photo.py --source image.jpg --output annotated.jpg
"""

import argparse
import cv2
import sys

from detector import ObjectDetector
from spatial_analyzer import euclidean_distance, find_nearest_person, is_near_dustbin
from tracker import TrackedObject
import config


def main():
    parser = argparse.ArgumentParser(description="Littering Detection — Photo Mode")
    parser.add_argument("--source", type=str, required=True, help="Path to input image")
    parser.add_argument("--model", type=str, default=None, help="Path to YOLO model weights")
    parser.add_argument("--output", type=str, default=None, help="Path to save annotated image")
    args = parser.parse_args()

    print("=" * 60)
    print("  LITTERING DETECTION SYSTEM — PHOTO MODE")
    print("=" * 60)
    detector = ObjectDetector(model_path=args.model)

    frame = cv2.imread(args.source)
    if frame is None:
        print(f"[ERROR] Cannot load image: {args.source}")
        sys.exit(1)

    height, width = frame.shape[:2]
    print(f"[Photo] Source: {args.source}")
    print(f"[Photo] Resolution: {width}x{height}")
    print("-" * 60)

    detections = detector.detect(frame)

    persons = detector.filter_by_class(detections, config.CLASS_NAMES["person"])
    garbage = detector.filter_by_class(detections, config.CLASS_NAMES["garbage"])
    dustbins = detector.filter_by_class(detections, config.CLASS_NAMES["dustbin"])

    print(f"\n[Results]")
    print(f"  Persons detected:  {len(persons)}")
    print(f"  Garbage detected:  {len(garbage)}")
    print(f"  Dustbins detected: {len(dustbins)}")

    person_objects = {i: TrackedObject(i, det) for i, det in enumerate(persons)}
    dustbin_objects = {i: TrackedObject(i, det) for i, det in enumerate(dustbins)}

    annotated = frame.copy()

    # Draw persons (green)
    for i, det in enumerate(persons):
        x1, y1, x2, y2 = det.bbox
        cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(annotated, f"Person #{i} ({det.confidence:.2f})", (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

    # Draw dustbins (yellow)
    for i, det in enumerate(dustbins):
        x1, y1, x2, y2 = det.bbox
        cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 255, 255), 2)
        cv2.putText(annotated, f"Dustbin #{i} ({det.confidence:.2f})", (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

    # Draw garbage with spatial risk analysis
    print(f"\n[Spatial Analysis]")
    for i, det in enumerate(garbage):
        x1, y1, x2, y2 = det.bbox
        near_dustbin = is_near_dustbin(det.centroid, dustbin_objects, config.DUSTBIN_PROXIMITY)
        nearest_pid, dist = find_nearest_person(det.centroid, person_objects)

        if near_dustbin:
            color = (0, 255, 255)
            risk = "LOW (near dustbin)"
        elif nearest_pid is not None and dist < config.PROXIMITY_THRESHOLD:
            color = (0, 165, 255)
            risk = f"MEDIUM (near person #{nearest_pid}, dist={dist:.0f}px)"
        elif nearest_pid is not None:
            color = (0, 0, 255)
            risk = f"HIGH (abandoned, nearest person #{nearest_pid} at {dist:.0f}px)"
        else:
            color = (0, 0, 255)
            risk = "HIGH (no persons detected)"

        cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
        cv2.putText(annotated, f"Garbage #{i} ({det.confidence:.2f})", (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

        if nearest_pid is not None:
            pc = person_objects[nearest_pid].centroid
            cv2.line(annotated, det.centroid, pc, color, 1, cv2.LINE_AA)
            mid = ((det.centroid[0] + pc[0]) // 2, (det.centroid[1] + pc[1]) // 2)
            cv2.putText(annotated, f"{dist:.0f}px", mid,
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)

        print(f"  Garbage #{i}: {risk}")

    summary = f"Persons: {len(persons)} | Garbage: {len(garbage)} | Dustbins: {len(dustbins)}"
    cv2.putText(annotated, summary, (10, height - 15),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

    if args.output:
        cv2.imwrite(args.output, annotated)
        print(f"\n[Photo] Annotated image saved: {args.output}")

    print(f"\n[Photo] Press any key to close the window")
    cv2.imshow("Littering Detection - Photo", annotated)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    print("\n" + "=" * 60)
    print("  NOTE: Photo mode shows detection + spatial analysis only.")
    print("  For temporal littering inference, use main_video.py or main_webcam.py.")
    print("=" * 60)


if __name__ == "__main__":
    main()

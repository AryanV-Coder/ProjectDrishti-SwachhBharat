"""
Webcam Test — Run littering detection on live webcam feed.

Usage:
    python main_webcam.py
    python main_webcam.py --camera 1          # Use camera index 1
    python main_webcam.py --model best.pt     # Specify model path
"""

import argparse
import cv2
import sys

from pipeline import LitteringPipeline
import config


def main():
    parser = argparse.ArgumentParser(description="Littering Detection — Webcam Mode")
    parser.add_argument("--camera", type=int, default=0, help="Camera index (default: 0)")
    parser.add_argument("--model", type=str, default=None, help="Path to YOLO model weights")
    parser.add_argument("--sample-rate", type=int, default=None, help="Process every Nth frame")
    args = parser.parse_args()

    # Override config if args provided
    sample_rate = args.sample_rate or config.FRAME_SAMPLE_RATE

    # Initialize pipeline
    print("=" * 60)
    print("  LITTERING DETECTION SYSTEM — WEBCAM MODE")
    print("=" * 60)
    pipeline = LitteringPipeline(model_path=args.model)

    # Open webcam
    cap = cv2.VideoCapture(args.camera)
    if not cap.isOpened():
        print(f"[ERROR] Cannot open camera {args.camera}")
        sys.exit(1)

    print(f"[Webcam] Camera {args.camera} opened successfully")
    print(f"[Webcam] Frame sampling rate: every {sample_rate} frames")
    print(f"[Webcam] Press 'q' to quit, 'r' to reset trackers")
    print("-" * 60)

    frame_count = 0
    last_annotated = None  # Store last annotated frame to prevent blinking

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("[Webcam] Failed to read frame")
                break

            frame_count += 1

            # Frame sampling — only process every Nth frame
            if frame_count % sample_rate != 0:
                # Show the LAST annotated frame (not raw) to prevent blinking
                if config.SHOW_DISPLAY and last_annotated is not None:
                    cv2.imshow("Littering Detection - Webcam", last_annotated)
                    if cv2.waitKey(1) & 0xFF == ord("q"):
                        break
                continue

            # Process frame through pipeline
            events = pipeline.process_frame(frame)

            # Log detection counts
            print(
                f"[Frame {pipeline.frame_count}] "
                f"Persons: {len(pipeline.tracked_persons)} | "
                f"Garbage: {len(pipeline.tracked_garbage)} | "
                f"Dustbins: {len(pipeline.tracked_dustbins)}",
                end="\r",
            )

            # Draw annotations
            annotated = pipeline.draw_annotations(frame)
            last_annotated = annotated  # Cache for non-processed frames

            # Display
            if config.SHOW_DISPLAY:
                # Resize if configured
                if config.DISPLAY_WIDTH > 0 and config.DISPLAY_HEIGHT > 0:
                    annotated = cv2.resize(annotated, (config.DISPLAY_WIDTH, config.DISPLAY_HEIGHT))

                cv2.imshow("Littering Detection - Webcam", annotated)

                key = cv2.waitKey(1) & 0xFF
                if key == ord("q"):
                    break
                elif key == ord("r"):
                    pipeline.reset()
                    print("[Webcam] Trackers reset")

    except KeyboardInterrupt:
        print("\n[Webcam] Interrupted by user")

    finally:
        cap.release()
        cv2.destroyAllWindows()

        # Print summary
        print("\n" + "=" * 60)
        print("  SESSION SUMMARY")
        print("=" * 60)
        print(f"  Frames processed: {pipeline.frame_count}")
        print(f"  Total littering events: {len(pipeline.all_events)}")
        for event in pipeline.all_events:
            print(f"    → {event}")
        print("=" * 60)


if __name__ == "__main__":
    main()

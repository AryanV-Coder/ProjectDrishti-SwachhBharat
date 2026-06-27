"""
Video File Test — Run littering detection on a video file.

Usage:
    python main_video.py --source path/to/video.mp4
    python main_video.py --source video.mp4 --model best.pt
    python main_video.py --source video.mp4 --output output.avi
"""

import argparse
import cv2
import sys
import time

from pipeline import LitteringPipeline
import config


def main():
    parser = argparse.ArgumentParser(description="Littering Detection — Video Mode")
    parser.add_argument("--source", type=str, required=True, help="Path to input video file")
    parser.add_argument("--model", type=str, default=None, help="Path to YOLO model weights")
    parser.add_argument("--output", type=str, default=None, help="Path to save annotated output video")
    parser.add_argument("--sample-rate", type=int, default=None, help="Process every Nth frame")
    parser.add_argument("--no-display", action="store_true", help="Disable video display window")
    args = parser.parse_args()

    sample_rate = args.sample_rate or config.FRAME_SAMPLE_RATE
    show_display = not args.no_display and config.SHOW_DISPLAY

    print("=" * 60)
    print("  LITTERING DETECTION SYSTEM — VIDEO MODE")
    print("=" * 60)
    pipeline = LitteringPipeline(model_path=args.model)

    cap = cv2.VideoCapture(args.source)
    if not cap.isOpened():
        print(f"[ERROR] Cannot open video: {args.source}")
        sys.exit(1)

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    print(f"[Video] Source: {args.source}")
    print(f"[Video] Resolution: {width}x{height} @ {fps:.1f} FPS")
    print(f"[Video] Total frames: {total_frames}")
    print(f"[Video] Frame sampling: every {sample_rate} frames")

    writer = None
    if args.output:
        fourcc = cv2.VideoWriter_fourcc(*"XVID")
        writer = cv2.VideoWriter(args.output, fourcc, fps / sample_rate, (width, height))
        print(f"[Video] Output: {args.output}")

    print("[Video] Press 'q' to quit, 'p' to pause/resume")
    print("-" * 60)

    frame_count = 0
    start_time = time.time()
    paused = False

    try:
        while True:
            if paused:
                key = cv2.waitKey(100) & 0xFF
                if key == ord("p"):
                    paused = False
                elif key == ord("q"):
                    break
                continue

            ret, frame = cap.read()
            if not ret:
                print("[Video] End of video reached")
                break

            frame_count += 1
            if frame_count % sample_rate != 0:
                continue

            events = pipeline.process_frame(frame)
            annotated = pipeline.draw_annotations(frame)

            # Progress bar
            if total_frames > 0:
                progress = frame_count / total_frames
                bw = int(annotated.shape[1] * 0.6)
                bx = int(annotated.shape[1] * 0.2)
                cv2.rectangle(annotated, (bx, 10), (bx + bw, 18), (50, 50, 50), -1)
                cv2.rectangle(annotated, (bx, 10), (bx + int(bw * progress), 18), (0, 200, 0), -1)
                cv2.putText(annotated, f"{progress*100:.0f}%", (bx + bw + 10, 18),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)

            if writer:
                writer.write(annotated)

            if show_display:
                display = annotated
                if config.DISPLAY_WIDTH > 0 and config.DISPLAY_HEIGHT > 0:
                    # Resize preserving aspect ratio (fit within display bounds)
                    ah, aw = annotated.shape[:2]
                    scale = min(config.DISPLAY_WIDTH / aw, config.DISPLAY_HEIGHT / ah)
                    if scale < 1.0:  # Only downscale, never upscale
                        new_w = int(aw * scale)
                        new_h = int(ah * scale)
                        display = cv2.resize(annotated, (new_w, new_h))
                cv2.imshow("Littering Detection - Video", display)
                key = cv2.waitKey(1) & 0xFF
                if key == ord("q"):
                    break
                elif key == ord("p"):
                    paused = True

    except KeyboardInterrupt:
        print("\n[Video] Interrupted by user")

    finally:
        elapsed = time.time() - start_time
        cap.release()
        if writer:
            writer.release()
        cv2.destroyAllWindows()

        print("\n" + "=" * 60)
        print("  SESSION SUMMARY")
        print("=" * 60)
        print(f"  Video: {args.source}")
        print(f"  Frames processed: {pipeline.frame_count}")
        print(f"  Processing time: {elapsed:.1f}s")
        if elapsed > 0:
            print(f"  Avg FPS: {pipeline.frame_count / elapsed:.1f}")
        print(f"  Total littering events: {len(pipeline.all_events)}")
        for event in pipeline.all_events:
            print(f"    -> {event}")
        if args.output:
            print(f"  Output saved: {args.output}")
        print("=" * 60)


if __name__ == "__main__":
    main()

# MediaPipe Face Detection

MediaPipe is Google's lightweight, on-device face detection framework. It is used in the pipeline to precisely locate and crop the violator's face from the video frame after littering is confirmed.

## How it works
1. The system does **not** scan the entire frame for faces (which would be slow and return irrelevant faces).
2. Instead, it uses the violator's YOLO bounding box to extract only the **person region** from the frame.
3. MediaPipe's `FaceDetection` model (with `model_selection=1` for full-range detection) scans this smaller region and returns **relative bounding box coordinates** of the face.
4. These relative coordinates are converted to absolute pixel values, padded by 25%, and the face is cropped and resized to 256×256 pixels for standardized input to the recognition model.

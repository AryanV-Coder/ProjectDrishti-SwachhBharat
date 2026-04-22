import cv2 
import os
import time 
import mediapipe as mp  

# creating a directory to store captured faces
os.makedirs('CapturedFaces',exist_ok=True) 
  
#start cam
cap = cv2.VideoCapture(0) 

print("Press 'v' to simulate violation")
print("Press 'q' to quit")
print("Test different conditions: low light, side face, tilted face, distance change, multiple people etc.")

violation_detected = False

# Initialize MediaPipe face detection and set parameters for better performance in real-life conditions 
# model_selection = 1 for full range of face sizes, min_detection_confidence = 0.6 for better accuracy

mp_face = mp.solutions.face_detection  
face_detector = mp_face.FaceDetection(model_selection=1, min_detection_confidence=0.6)

while True:
    ret, frame = cap.read()  # frame dimensions: (height, width, channels)
    
    # If camera fails to capture frame
    if not ret: 
        print("Camera Access Error") 
        break

    display = frame.copy()
    
    key = cv2.waitKey(1) & 0xff
    
    if key == ord('v') or key == ord('V'):
        violation_detected = True
        print("Violation Detected ... Capturing Face")
        print("Now try different real-life cases while testing detection")
        
    if violation_detected:
        # Convert BGR to RGB because MediaPipe works on RGB
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # MediaPipe detection (works better for side faces and low light)
        results = face_detector.process(rgb)
        
        if results.detections:
            detection = results.detections[0]  # Take first detected face
            bbox = detection.location_data.relative_bounding_box
            
            h, w, _ = frame.shape
            
            x = int(bbox.xmin * w)
            y = int(bbox.ymin * h)
            box_w = int(bbox.width * w)
            box_h = int(bbox.height * h)
            
            padding = int(0.2 * box_w)  # Padding for better crop
            
            x1 = max(0, x - padding)
            y1 = max(0, y - padding)
            x2 = min(w, x + box_w + padding)
            y2 = min(h, y + box_h + padding)
            
            #resize to 256 x 256
            face_crop = cv2.resize(frame[y1:y2, x1:x2] ,(256,256))
            filename = f"CapturedFaces/face_{int(time.time())}.jpg"
            
            # Save the cropped face image with high quality (95% JPEG quality)            
            cv2.imwrite(filename, face_crop, [cv2.IMWRITE_JPEG_QUALITY, 95]) 
            
            print("Colored face saved:", filename)
            
            # Draw rectangle on display with green color, thickness = 2 border
            cv2.rectangle(display, (x1, y1), (x2, y2), (0, 255, 0), 2)
            
            violation_detected = False  # stop after successful capture
            
        else:
            print("No face detected. Adjust lighting/angle/distance and try again.")

    cv2.imshow("Violation Detected", display)      
      
    if key == ord('q'):
        break
    
cap.release()
cv2.destroyAllWindows()
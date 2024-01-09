import cv2
from deepface import DeepFace
import time

# OpenCV function to access the webcam
def capture_frames(interval, total_duration):
    cap = cv2.VideoCapture(0)  # 0 refers to the default webcam, change it if needed

    frames = []
    start_time = time.time()
    while True:
        ret, frame = cap.read()  # Capture frame-by-frame
        cv2.imshow('Webcam', frame)  # Display the captured frame
        if time.time() - start_time >= total_duration:
            break

        if ret:
            frames.append(frame)

        if cv2.waitKey(interval * 1000) & 0xFF == ord('q'):  # Press 'q' to stop capturing
            break

    cap.release()  # Release the camera
    cv2.destroyAllWindows()  # Close the OpenCV window
    return frames

# Function to detect emotions from a list of captured frames
def detect_emotions(frames):
    emotions = []
    for idx, frame in enumerate(frames):
        cv2.imwrite('temp_img.jpg', frame)  # Save each frame temporarily
        try:
            result = DeepFace.analyze('temp_img.jpg', actions=['emotion'])
        except Exception as e:
            print("Ignoring exception from deepface analyzer: ", e)
            emotions.append(None)
            continue
        print(f"frame {idx} result: ", result)
        emotions.append(result[0]["dominant_emotion"])   #list(result[0]["emotion"].keys())[0]
    
    return emotions

# Capture frames every x seconds
capture_interval = 2  # Capture a frame every 5 seconds
total_duration = 10  # Capture frames for a total of 30 seconds

captured_frames = capture_frames(capture_interval, total_duration)
captured_emotions = detect_emotions(captured_frames)

print("Emotions detected from captured frames:")
for idx, emotion in enumerate(captured_emotions):
    print(f"Frame {idx + 1}: {emotion}")
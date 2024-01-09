from deepface import DeepFace

# Path to the image you want to analyze
image_path = 'temp_img.jpg'

# Perform face recognition
#detected_faces = DeepFace.detectFace(image_path, detector_backend='mtcnn')
detected_faces = DeepFace.extract_faces(image_path)

# Perform emotion analysis on each detected face
for face in detected_faces:
    result = DeepFace.analyze(img_path=image_path, actions=['emotion'], enforce_detection=False, region=face)
    print("Emotions detected for this face:", result["emotion"])
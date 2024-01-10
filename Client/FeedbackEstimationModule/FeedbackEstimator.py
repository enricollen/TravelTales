import os
from pydub import AudioSegment
from dotenv import load_dotenv
from AudioSentimentClassificationModule.AudioSentimentClassifier import AudioSentimentClassifier
from SpeakerRecognitionModule.SpeakerRecognizerStreaming import SpeakerRecognizerStreaming
from NewsPlayingModule.news import News

env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(env_path)

RECORDED_SPEECH_PATH = os.getenv("RECORDED_SPEECH_PATH")
AUDIO_INPUT_DEVICE_INDEX = int(os.getenv("AUDIO_INPUT_DEVICE_INDEX"))

USE_VIDEO = True if os.getenv("USE_VIDEO").lower() in ["true", "yes", "1"] else False

if USE_VIDEO:
    from deepface import DeepFace
    DEEPFACE_DATABASE_PATH = os.getenv("DEEPFACE_DATABASE_PATH")


class FeedbackEstimator(object):

    passengers_onboard = None
    audioSentimentClassifier = None
    speakerRecognizer = None

    def __init__(self, passenger_list):
        self.passengers_onboard = passenger_list
        self.speakerRecognizer = SpeakerRecognizerStreaming()
        self.audioSentimentClassifier = AudioSentimentClassifier()
        self.audioSentimentClassifier.load_model()

    def update_passengers_list(self, passenger_list):
        """
        this method has to be called after that the list of passengers is modified
        """
        self.passengers_onboard = passenger_list

    def compute_feedback(self, current_news_obj: News, feedback_window=None):
        """
        Computes the users' engagement level for a given news by creating a dictionary to be returned to the server
        that will accomplish the task to adjust the embeddings w.r.t. the gathered feedback.
        This method performs the following actions:
        - call the start_listening() method to listen to the vocal speeches from passengers on board
        - call the estimate_sentiment(merged_speech_paths) to extract the sentiment linked to a passenger speech
        - creates the resulting dictionary of the whole feedbacks to be returned to the server
        - call send_to_server(feedbacks_dict) to send the dictionary to the server

        current_news_obj: the object associated with the news to be evaluated through feedback gathering
        """
        feedbacks_dict = {"url-identifier": current_news_obj.get_news_link(), "users-feeback": []}

        if USE_VIDEO:
            # a. starts the camera recording and redirect the camera frames to deepface model
            self.start_video_recording(feedback_window=feedback_window)
            
        merged_speech_paths = self.start_listening(feedback_window)

        if USE_VIDEO:
            visual_emotions_recognised = self.stop_video_recording()

            num_visual_labels = max([len(l) for l in visual_emotions_recognised.values()])


        for audio_path in merged_speech_paths:
            # 1. first predict audio sentiment
            predicted_sentiment = self.audioSentimentClassifier.predict(audio_path)

            # 2. estimate user engagement based on sentiment, speech rate, and audio duration
            engagement_score = self.audioSentimentClassifier.estimate_user_engagement(predicted_sentiment, audio_path)

            # 3. create feedback dictionary for the current user
            username = self.get_username_from_audio_path(audio_path)
            
            # 4. get audio duration
            audio_duration = self.get_audio_duration(audio_path)

            # 5. create feedback dictionary for the current user
            user_feedback = {
                "username": username,
                "predicted_sentiment": predicted_sentiment,
                "engagement_score": engagement_score,
                "audio_duration": audio_duration
            }

            if USE_VIDEO is True:
                if username in visual_emotions_recognised.keys():
                    users_emotions = list(visual_emotions_recognised[username]) + ( ["NA"] * max(0, num_visual_labels - len(visual_emotions_recognised[username])) )
                    visual_emotion = max(set(users_emotions), key=users_emotions.count)
                    user_feedback["visual_emotion"] = visual_emotion
                    engagement_score_video = self.audioSentimentClassifier.estimate_user_engagement_video_only(visual_emotion, audio_path)
                    user_feedback["engagement_score_video"] = engagement_score_video
                    user_feedback["engagement_score_mixed"] = self.audioSentimentClassifier.estimate_user_engagement_ensemble(predicted_sentiment, visual_emotion, audio_path)

            feedbacks_dict["users-feeback"].append(user_feedback)

        #self.send_feedback_to_server(feedbacks_dict)
        #if USE_VIDEO:
        #    print(f"returning feedback_dict which is: ", feedbacks_dict)
        return feedbacks_dict
    
    def get_audio_duration(self, audio_path):
        """
        Get the duration of the audio file in seconds.

        audio_path: path to the audio file
        """
        audio = AudioSegment.from_wav(audio_path)
        duration_in_seconds = len(audio) / 1000.0  # ms to s
        return duration_in_seconds

    
    def get_username_from_audio_path(self, audio_path):
        """
            Method to extract the username from the audio path
            Example: "Client\speaker_profiles\enrico_speech.pv" -> "enrico"
        """
        file_name = os.path.basename(audio_path)
        username = file_name.split("_")[0]
        return username


    def start_listening(self, feedback_window=None):
        """
            Starts the recording of the passengers' voices invoking listen() method of SpeakerRecognizerStreaming.
            The method listen() is blocking; it starts the recording and waits for the user to stop speaking.
            While listening, it saves slices of passengers' speeches (at least 4 seconds long)
            inside Client\\SpeakerRecognition\\resources\\audio_output

            Returns the paths of the merged speechs for each passenger
        """

        def merge_audio_slices():
            merged_paths = []  #list to store the paths of the final merged WAV files
            for username in self.passengers_onboard:
                audio_slices = []
                i = 1
                while True:
                    audio_path = os.path.join(os.path.dirname(__file__), RECORDED_SPEECH_PATH, f"{username}_speech_{i}.wav")
                    if os.path.exists(audio_path):
                        audio_slices.append(AudioSegment.from_wav(audio_path))
                        i += 1
                    else:
                        break

                #concatenate audio slices for the same passenger
                if audio_slices:
                    concatenated_audio = sum(audio_slices)

                    output_dir = os.path.join(os.path.dirname(__file__), RECORDED_SPEECH_PATH)
                    os.makedirs(output_dir, exist_ok=True)

                    concatenated_path = os.path.join(output_dir, f"{username}_speech.wav")
                    concatenated_audio.export(concatenated_path, format="wav")
                    merged_paths.append(concatenated_path)

            #print("Done merging audio slices.")
            return merged_paths

        print("Listening...")
        if feedback_window:
            feedback_window.print("Listening...")

        try:
            test_input_profile_paths = [f"{username}.pv" for username in self.passengers_onboard]
            self.speakerRecognizer.listen(
                audio_device_index=AUDIO_INPUT_DEVICE_INDEX,
                output_audio_path=None,
                input_profile_paths=test_input_profile_paths,
                min_speech_duration=4,
                feedback_window=feedback_window
            )
        except Exception as e:
            print("Something went wrong while listening: ", e)
            if feedback_window:
                feedback_window.print("Something went wrong while listening")

        #at this point, we have all the slices of all the passengers inside the audio_output folder,
        #and we can proceed to stitch them together (in case there are more than 1 .wav from the same person)
        try:
            merged_paths = merge_audio_slices()
        except Exception as e:
            print("Something went wrong while merging audio slices: ", e)
            return

        return merged_paths
    
    video_processing_thread = None
    continue_video_recording = False
    gathered_frames_infos = None
    # should be a dictionary where for each user (whose username is the key) stores the list of emotions recognized at each frame

    def start_video_recording(self, timeout = 600, images_frequency = float(os.getenv("IMAGE_ANALYSIS_FREQUENCY")), feedback_window=None):
        """
        this method should:
        1. launch a new thread dedicated to images gathering
        2. collect an image every 'images_frequency' seconds
        3. get the results (and possibly the labelled image) from DeepFace applied to the given frame
        4. show the gathered image (possibly with the labels) in the pySimpleGUI given window
        """
        import time, cv2, threading, base64

        def convert_frame_to_bytes(frame, target_width=400, target_height=300):
            # Convert the OpenCV frame to bytes
            # Get the original image dimensions
            height, width = frame.shape[:2]

            # Calculate the aspect ratio of the original image
            aspect_ratio = width / height

            # Determine the target width and height while maintaining the aspect ratio
            if target_width / aspect_ratio <= target_height:
                resized_width = target_width
                resized_height = int(resized_width / aspect_ratio)
            else:
                resized_height = target_height
                resized_width = int(resized_height * aspect_ratio)

            # Resize the image while maintaining the aspect ratio
            resized_frame = cv2.resize(frame, (resized_width, resized_height), interpolation=cv2.INTER_AREA)
            _, buffer = cv2.imencode('.png', resized_frame)
            frame_bytes = base64.b64encode(buffer)
            return frame_bytes

        self.continue_video_recording = True
        self.gathered_frames_infos = {}

        if feedback_window is None:
            print("[!] the method start_video_recording received a None type feedback_window [!]")
        #else:
        #    print(f"[+] feedback_window type: {type(feedback_window)}", feedback_window)

        def capture_frames_thread(feedback_window):
            #global last_frame, new_frame_available
            
            cap = cv2.VideoCapture(0)
            
            while self.continue_video_recording is True:
                iteration_begin_time = time.time()
                ret, frame = cap.read()
                if ret:
                    frame = frame.copy()
                    cv2.imwrite('temp_img.jpg', frame)  # Save each frame temporarily
                    default_username = self.passengers_onboard[0]
                    detected_faces = DeepFace.extract_faces('temp_img.jpg', enforce_detection=False)
                    for result in detected_faces:
                        ret = DeepFace.find(result['face'], DEEPFACE_DATABASE_PATH, enforce_detection=False)
                        if len(ret) > 0 and len(ret[0]) > 0:
                            try:
                                default_username = recognised_username = (ret[0].iloc[0]['identity']).replace(DEEPFACE_DATABASE_PATH, "").split("/")[0].replace("\\", "").replace(".jpg", "")
                                #print("deepface find username string: ", recognised_username)
                            except Exception as e:
                                print(e)
                                print(ret)
                                print("len(ret)", len(ret), "len(ret[0]): ", len(ret[0]))
                            
                        else:
                            #print("Using as username the default value: ", default_username)
                            recognised_username = default_username
                        
                        if recognised_username not in self.passengers_onboard:
                            print(f"[!] The recognised user: {recognised_username} is not in the list of the current passengers [!]")
                        username = recognised_username
                        x, y, w, h = result['facial_area'].values()
                        
                        cv2.imwrite('temp-img-cropped.jpg', frame[y:y + w, x:x + h])

                        analyzed = DeepFace.analyze('temp-img-cropped.jpg', actions=['emotion'], enforce_detection=False)
                        print(f"Received results from DeepFace.analyze method: ", analyzed)
                        analyzed = analyzed[0]
                        if username not in self.gathered_frames_infos.keys():
                            self.gathered_frames_infos[username] = []
                        self.gathered_frames_infos[username].append(analyzed['dominant_emotion'])
                    
                        frame = cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)  # Draw bounding box
                        label = f"Emotion: {analyzed['dominant_emotion']}"  # Create label text
                        frame = cv2.putText(frame, label, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)  # Display label
                        frame = cv2.putText(frame, f'User: {username}', (x, y + h + 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)  # Display label
                    # here we can add labels to the image that is in the variable frame
                    if len(detected_faces) > 0:
                        buffered_image = convert_frame_to_bytes(frame)
                        feedback_window.show_image(buffered_image)
                else:
                    print("ret, frame = cap.read() returned empty ret, calling the method again")
                    #continue
                
                elapsed_time_during_iteration = time.time() - iteration_begin_time
                
                time.sleep(max(0.2, images_frequency - elapsed_time_during_iteration))  # Adjust the delay as needed
            print("Video gathering thread is terminating...")
            cap.release()  # Release the camera
            print("Video gathering released the camera")
            exit()

        self.video_processing_thread = threading.Thread(target=capture_frames_thread, args=[feedback_window], daemon=True)
        self.video_processing_thread.start()
        print("Started video processing thread")

    def stop_video_recording(self):
        print("Setting continue video recording to false")
        self.continue_video_recording = False
        import threading
        if self.video_processing_thread is not None and isinstance(self.video_processing_thread, threading.Thread):
            self.video_processing_thread.join(3)
            print(f"video_processing_thread has terminated correctly? {'no' if self.video_processing_thread.is_alive() else 'yes'}")
            self.video_processing_thread = None

        return self.gathered_frames_infos
    
    def stop_gathering(self):
        print("[+] FeedbackEstimator: received a call to method stop_gathering [+]")
        self.speakerRecognizer.stop()

    def send_feedback_to_server(self, feedbacks_dict):
        #print(feedbacks_dict)
        print("Feedbacks sent back to the server.")
        pass
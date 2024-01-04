import os
from pydub import AudioSegment
from dotenv import load_dotenv
from AudioSentimentClassificationModule.AudioSentimentClassifier import AudioSentimentClassifier
from SpeakerRecognitionModule.SpeakerRecognizerStreaming import SpeakerRecognizerStreaming
from NewsPlayingModule.news import News

load_dotenv()

RECORDED_SPEECH_PATH = os.getenv("RECORDED_SPEECH_PATH")

class FeedbackEstimator(object):

    passengers_onboard = None
    audioSentimentClassifier = None
    speakerRecognizer = None

    def __init__(self, passenger_list):
        self.passengers_onboard = passenger_list
        self.speakerRecognizer = SpeakerRecognizerStreaming()
        self.audioSentimentClassifier = AudioSentimentClassifier()
        self.audioSentimentClassifier.load_model()


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
        merged_speech_paths = self.start_listening(feedback_window)

        for audio_path in merged_speech_paths:
            # 1. first predict audio sentiment
            predicted_sentiment = self.audioSentimentClassifier.predict(audio_path)

            # 2. estimate user engagement based on sentiment, speech rate, and audio duration
            engagement_score = self.audioSentimentClassifier.estimate_user_engagement(predicted_sentiment, audio_path)

            # 3. create feedback dictionary for the current user
            username = self.get_username_from_audio_path(audio_path)
            user_feedback = {"username": username, "predicted_sentiment": predicted_sentiment, "engagement_score": engagement_score}

            feedbacks_dict["users-feeback"].append(user_feedback)

        self.send_feedback_to_server(feedbacks_dict)

        return feedbacks_dict

    
    def get_username_from_audio_path(self, audio_path):
        """
            Method to extract the username from the audio path
            Example: "Client\speaker_profiles\enrico_speech.pv" -> "enrico"
        """
        file_name = os.path.basename(audio_path)
        username = file_name.split("_")[0]
        return username

    def estimate_user_engagement(self, audio_paths):
        """
        Method to estimate the user engagement within the audio files.
        The engagement score is estimated from the sentiment, speech rate, and audio duration.
        audio_paths: paths to the merged audio files for each passenger
        """    
        
        for audio_path in audio_paths:
            #1. first predict audio sentiment
            predicted_sentiment = self.audioSentimentClassifier.predict(audio_path)

            #2. estimate user engagement based on sentiment, speech rate, and audio duration
            engagement_score = self.audioSentimentClassifier.estimate_user_engagement(predicted_sentiment, audio_path)

            #3. create feedback dictionary for the current user
            username = self.get_username_from_audio_path(audio_path)
            feedback_dict = {"username": username, "sentiment_score": predicted_sentiment, "engagement_score": engagement_score}

            return feedback_dict


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
        try:
            test_input_profile_paths = [f"{username}.pv" for username in self.passengers_onboard]
            self.speakerRecognizer.listen(
                audio_device_index=0,
                output_audio_path=None,
                input_profile_paths=test_input_profile_paths,
                min_speech_duration=4,
                feedback_window=feedback_window
            )
        except Exception as e:
            print("Something went wrong while listening: ", e)

        #at this point, we have all the slices of all the passengers inside the audio_output folder,
        #and we can proceed to stitch them together (in case there are more than 1 .wav from the same person)
        try:
            merged_paths = merge_audio_slices()
        except Exception as e:
            print("Something went wrong while merging audio slices: ", e)
            return

        return merged_paths

    def send_feedback_to_server(self, feedbacks_dict):
        endpoint="http://localhost:5000/feedback"
        #print(feedbacks_dict)
        print("Feedbacks sent back to the server.")
        pass
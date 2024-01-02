import os
import librosa
import numpy as np
import tensorflow as tf
from dotenv import load_dotenv

load_dotenv()

MODEL_PATH = os.getenv("TFLITE_MODEL_PATH")

class AudioSentimentClassifier:

    def __init__(self):
        self.model_path = os.path.join(os.path.dirname(__file__), MODEL_PATH)

    def load_model(self):
      """
      Method to load the model.
      """
      self.interpreter = tf.lite.Interpreter(model_path=self.model_path)
      self.interpreter.allocate_tensors()


    def predict(self, audio_file):
      """
      Method to process the files and create audio features.
      audio_file: path to the audio file to be classified
      """
      data, sampling_rate = librosa.load(audio_file)
      mfccs = np.mean(librosa.feature.mfcc(y=data, sr=sampling_rate, n_mfcc=40).T, axis=0)
      x = np.expand_dims(mfccs, axis=0)
      x = np.expand_dims(x, axis=2) 

      # get input and output tensors
      input_tensor_index = self.interpreter.get_input_details()[0]['index']
      output = self.interpreter.tensor(self.interpreter.get_output_details()[0]['index'])

      # run inference
      self.interpreter.set_tensor(input_tensor_index, x)
      self.interpreter.invoke()

      # get the output
      predictions = output()[0]
      predicted_class = np.argmax(predictions)
      predicted_class = self.convertclasstoemotion(predicted_class)

      return predicted_class
    

    def estimate_user_engagement(self, sentiment, audio_file):
      """
        Method to estimate the user engagement within the audio file. 
        The engagement score is estimated from the speech rate, audio duration and the sentiment.
        sentiment: the predicted sentiment of the audio file
        audio_file: path to the audio file to be classified
      """
      data, sampling_rate = librosa.load(audio_file)

      # 1. speech rate as the ratio of non-silent frames over total frames
      non_silent_frames = len(librosa.effects.split(data))
      total_frames = len(data) / sampling_rate
      speech_rate = non_silent_frames / total_frames

      # 2. audio duration
      audio_duration = total_frames / sampling_rate

      # 3. mapping sentiment to engagement score
      sentiment_engagement_mapping = {
          'neutral': 2,
          'calm': 5,
          'happy': 9,
          'sad': 8,
          'angry': 4,
          'fearful': 3,
          'disgust': 5,
          'surprised': 9
      }

      engagement_score = sentiment_engagement_mapping.get(sentiment, 5)

      # now adjust engagement score based on speech rate and audio duration
      if speech_rate > 0.5:
          engagement_score += 1
      else:
          engagement_score -= 1

      # adjust based on audio duration
      if audio_duration < 10:
          engagement_score -= 1
      elif audio_duration > 30:
          engagement_score += 1

      engagement_score = max(1, min(10, engagement_score))

      return engagement_score




    @staticmethod
    def convertclasstoemotion(pred):
        """
        Method to convert the predictions (int) into readable strings.
        """

        label_conversion = {'0': 'neutral',
                            '1': 'calm',
                            '2': 'happy',
                            '3': 'sad',
                            '4': 'angry',
                            '5': 'fearful',
                            '6': 'disgust',
                            '7': 'surprised'}

        for key, value in label_conversion.items():
            if int(key) == pred:
                label = value
        return label
    

"""
if __name__ == '__main__':

    audio_classifier = AudioSentimentClassifier()
    audio_classifier.load_model()

    audio_file_path = 'Client/AudioSentimentClassification/audio/disgust.wav'

    predicted_sentiment = audio_classifier.predict(audio_file_path)
    print("Predicted Sentiment:", predicted_sentiment)
"""
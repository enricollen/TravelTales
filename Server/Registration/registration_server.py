import struct
import wave
from flask import Flask, request, jsonify
import os
from flask_cors import CORS
import pandas as pd
import pveagle
from dotenv import load_dotenv
from pydub import AudioSegment

load_dotenv()
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

SCRIPT_DIRECTORY = os.path.dirname(os.path.abspath(__file__))
API_KEY = os.getenv("API_KEY")
SPEAKER_PROFILE_OUTPUT_PATH = os.getenv("SPEAKER_PROFILE_OUTPUT_PATH")
CLIENT_AUDIO_UPLOAD_PATH = os.getenv("CLIENT_AUDIO_UPLOAD_PATH")
USERS_TSV_FILENAME=os.getenv("USERS_TSV_FILENAME")
USERS_TSV_PATH = os.path.join(SCRIPT_DIRECTORY, USERS_TSV_FILENAME)
FEEDBACK_TO_DESCRIPTIVE_MSG = {
    pveagle.EagleProfilerEnrollFeedback.AUDIO_OK: 'Good audio',
    pveagle.EagleProfilerEnrollFeedback.AUDIO_TOO_SHORT: 'Insufficient audio length',
    pveagle.EagleProfilerEnrollFeedback.UNKNOWN_SPEAKER: 'Different speaker in audio',
    pveagle.EagleProfilerEnrollFeedback.NO_VOICE_FOUND: 'No voice found in audio',
    pveagle.EagleProfilerEnrollFeedback.QUALITY_ISSUE: 'Low audio quality due to bad microphone or environment'
}


def read_file(file_name, sample_rate):
    try:
        with wave.open(file_name, mode="rb") as wav_file:
            channels = wav_file.getnchannels()
            sample_width = wav_file.getsampwidth()
            num_frames = wav_file.getnframes()

            if wav_file.getframerate() != sample_rate:
                raise ValueError(
                "Audio file should have a sample rate of %d. got %d" % (sample_rate, wav_file.getframerate()))
            if sample_width != 2:
                raise ValueError("Audio file should be 16-bit. got %d" % sample_width)
            if channels == 2:
                print("Eagle processes single-channel audio but stereo file is provided. Processing left channel only.")

            samples = wav_file.readframes(num_frames)

    except Exception as e:
        print("Failed to perform wave.open: ", e)
        raise

    frames = struct.unpack('h' * num_frames * channels, samples)

    return frames[::channels]

def webm_opus_to_wav(webm_file_path, wav_file_path):
    """
    convert webm to wav format and force audio to be 16-bit mono and 16KHz
    """
    audio = AudioSegment.from_file(webm_file_path, format="webm")
    audio = audio.set_frame_rate(16000)
    audio = audio.set_sample_width(2)
    audio.export(wav_file_path, format="wav")

@app.route('/register', methods=['POST'])
def upload():
    try:
        username = request.form.get('username')
        politics = float(request.form.get('politics'))
        photography = float(request.form.get('photography'))
        soccer = float(request.form.get('soccer'))

        # save the audio file
        audio_file = request.files['audio']
        user_audio_webm_path = os.path.join(CLIENT_AUDIO_UPLOAD_PATH, username+'.webm')       
        audio_file.save(user_audio_webm_path)
        user_audio_wav_path = os.path.join(CLIENT_AUDIO_UPLOAD_PATH, username+'.wav')
        webm_opus_to_wav(user_audio_webm_path, user_audio_wav_path)

        try:
            eagle_profiler = pveagle.create_profiler(
                access_key=API_KEY,
                model_path=None,  
                library_path=None  
            )
        except pveagle.EagleError as e:
            print("Failed to initialize EagleProfiler: ", e)
            return jsonify({'success': False, 'error': 'It was not possible to register your profile due to an error. Please try again later'})

        print('Eagle version: %s' % eagle_profiler.version)

        try:
            enroll_percentage = 0.0

            audio = read_file(user_audio_wav_path, eagle_profiler.sample_rate)
            enroll_percentage, feedback = eagle_profiler.enroll(audio)
            print('Enrolled audio file %s [Enrollment percentage: %.2f%% - Enrollment feedback: %s]'
                    % (user_audio_wav_path, enroll_percentage, FEEDBACK_TO_DESCRIPTIVE_MSG[feedback]))

            if enroll_percentage < 100.0:
                print('Failed to create speaker profile. Insufficient enrollment percentage: %.2f%%. '
                      'Please add more audio speech for enrollment.' % enroll_percentage)
                return jsonify({'success': False, 'error': 'Audio not sufficient, please speak more to enroll'})

            # export the speaker profile
            speaker_profile = eagle_profiler.export()
            if SPEAKER_PROFILE_OUTPUT_PATH is not None:
                with open(os.path.join(SPEAKER_PROFILE_OUTPUT_PATH, username+'.pv'), 'wb') as f:
                    f.write(speaker_profile.to_bytes())
                print('Speaker profile is saved to %s' % SPEAKER_PROFILE_OUTPUT_PATH)

            # check if csv already exists
            if os.path.exists(USERS_TSV_PATH):
                df = pd.read_csv(USERS_TSV_PATH, sep='\t')
                new_user = {'username': username, 'interests': [politics, photography, soccer]}
                if username in df['username'].values:
                    print("Username already exists, aborting registration.")
                    return jsonify({'success': False, 'error': 'Username already exists, please choose another one'})
                df = pd.concat([df, pd.DataFrame([new_user])], ignore_index=True)
            else:
                df = pd.DataFrame({'username': [username], 'interests': [[politics, photography, soccer]]})

            df.to_csv(USERS_TSV_PATH, index=False, sep='\t')

            return jsonify({'success': True, 'message': 'Registered Successfully!'})

        except pveagle.EagleActivationLimitError:
            print('AccessKey has reached its processing limit')
            return jsonify({'success': False, 'error': 'AccessKey has reached its processing limit'})
        except pveagle.EagleError as e:
            print('Failed to perform enrollment: ', e)
            return jsonify({'success': False, 'error': str(e)})
        finally:
            eagle_profiler.delete()

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


if __name__ == '__main__':
    os.makedirs(CLIENT_AUDIO_UPLOAD_PATH, exist_ok=True)
    os.makedirs(SPEAKER_PROFILE_OUTPUT_PATH, exist_ok=True)

    #threaded=True to allow multiple connections
    app.run(debug=True, host='0.0.0.0', threaded=True)

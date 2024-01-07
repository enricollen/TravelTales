import struct
import wave
from flask import Flask, request, jsonify, render_template, Response, send_from_directory
import os
from flask_cors import CORS
import pandas as pd
import pveagle
from dotenv import load_dotenv
from pydub import AudioSegment

from retrievalSystem import RetrievalSystem

from ast import literal_eval

load_dotenv()
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

SCRIPT_DIRECTORY = os.path.dirname(os.path.abspath(__file__))
API_KEY = os.getenv("API_KEY")
SPEAKER_PROFILE_OUTPUT_PATH = os.getenv("SPEAKER_PROFILE_OUTPUT_PATH")
CLIENT_AUDIO_UPLOAD_PATH = os.getenv("CLIENT_AUDIO_UPLOAD_PATH")
USERS_TSV_FILENAME=os.getenv("USERS_TSV_FILENAME")
USERS_TSV_PATH = os.path.join(SCRIPT_DIRECTORY, USERS_TSV_FILENAME)

COLL_CSV_FILENAME=os.getenv("COLL_CSV_FILENAME")
COLL_CSV_PATH = os.path.join(SCRIPT_DIRECTORY, COLL_CSV_FILENAME)

CATEGORIES = os.getenv("CATEGORIES").split(',')

FEEDBACK_TO_DESCRIPTIVE_MSG = {
    pveagle.EagleProfilerEnrollFeedback.AUDIO_OK: 'Good audio',
    pveagle.EagleProfilerEnrollFeedback.AUDIO_TOO_SHORT: 'Insufficient audio length',
    pveagle.EagleProfilerEnrollFeedback.UNKNOWN_SPEAKER: 'Different speaker in audio',
    pveagle.EagleProfilerEnrollFeedback.NO_VOICE_FOUND: 'No voice found in audio',
    pveagle.EagleProfilerEnrollFeedback.QUALITY_ISSUE: 'Low audio quality due to bad microphone or environment'
}


def get_users_df():

    def f(x):
        x = str(x)
        if "," not in x:
            x = x.replace(" ", ", ")
        try:
            return literal_eval(str(x))
        except Exception as e:
            print(e)
            print("given x:" , x)
            return []
        
    conv = {'interests': lambda x: f(x)}

    if os.path.exists(USERS_TSV_PATH):
        return pd.read_csv(USERS_TSV_PATH, sep='\t', converters=conv)
    return None

coll_df = None

def load_collection_df():
    global coll_df
    if coll_df is not None:
        return coll_df
    def f(x):
        x = str(x)
        if "," not in x:
            x = x.replace(" ", ", ")
        try:
            return literal_eval(str(x))
        except Exception as e:
            print(e)
            print("given x:" , x)
            return []
    conv = {'Embedding': lambda x: f(x)}
    coll_df = pd.read_csv(COLL_CSV_PATH, converters=conv, index_col=0)
    print(f"Loaded dataframe of {len(coll_df)} rows")
    return coll_df


import numpy as np

def normalize_embedding(list):
    vector = np.array(list)
    normalized_vector = vector / np.linalg.norm(vector)
    return normalized_vector.tolist()


def read_file(file_name, sample_rate):
    """
        Read audio file and make sure it is 16-bit mono and 16KHz, thus handling the audio formats supported by wave module.
        file_name: the path to the audio file
        sample_rate: the sample rate of the audio file
    """
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
        webm_file_path: the path to the webm file
        wav_file_path: the path to the wav file
    """
    audio = AudioSegment.from_file(webm_file_path, format="webm")
    audio = audio.set_frame_rate(16000)
    audio = audio.set_sample_width(2)
    audio.export(wav_file_path, format="wav")

@app.route('/', methods=['GET']) 
def render_html():
    return render_template("registration.html")

@app.route('/register', methods=['POST'])
def register():
    """
        Register a new user to the system
    """
    try:
        username = request.form.get('username')
        
        embeddings = []

        for category in CATEGORIES:
            value_from_form = request.form.get(category)

            # Check if the value is not None before converting to float
            if value_from_form is not None:
                embeddings.append(float(value_from_form))
            else:
                # Handle the case where the value is None (e.g., provide a default value or raise an error)
                return jsonify({'success': False, 'error': f'Missing value for category {category}'})


        embeddings = normalize_embedding(embeddings)

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
            
            # check if csv already exists
            if os.path.exists(USERS_TSV_PATH):
                df = pd.read_csv(USERS_TSV_PATH, sep='\t')
                new_user = {'username': username, 'interests': embeddings}
                if username in df['username'].values:
                    print("Username already exists, aborting registration.")
                    return jsonify({'success': False, 'error': 'Username already exists, please choose another one'})
                df = pd.concat([df, pd.DataFrame([new_user])], ignore_index=True)
            else:
                df = pd.DataFrame({'username': [username], 'interests': [embeddings]})

            df.to_csv(USERS_TSV_PATH, index=False, sep='\t')

            # start voice enrolling phase 
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

            return jsonify({'success': True, 'message': 'Registered Successfully!'})

        except pveagle.EagleActivationLimitError:
            print('AccessKey has reached its processing limit')
            return jsonify({'success': False, 'error': 'AccessKey has reached its processing limit'})
        except pveagle.EagleError as e:
            print('Failed to perform enrollment: ', e)
            return jsonify({'success': False, 'error': str(e)})
        finally:
            eagle_profiler.delete()
            # Delete the temporary webm & wav file after processing
            os.remove(user_audio_wav_path)
            os.remove(user_audio_webm_path)

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route("/users", methods=["GET"])
def users_list():
    """
    returns the list of registered users
    """
    df = get_users_df()
    return Response(df.to_json(orient="records"), mimetype='application/json')

@app.route('/speaker_profiles/<path:path>')
def send_profile(path):
    """
    speaker profiles filename are in the form 'username.pv'
    """
    return send_from_directory('speaker_profiles', path)

@app.route('/audio-news/<path:path>')
def get_audio_news(path):
    """
    audio news are wav file whose file name is indicated in their corresponding collection.csv row
    """
    return send_from_directory('generated_audio', path)


@app.route('/feedback', methods=['POST'])
def users_feedback(feedbacks_dict):
    """
        Client sends the users' feedback w.r.t. the proposed news in a dictionary       

        feedbacks_dict: the users feedbacks in the following format:
        {   proposed_news_id: : {
            'passenger_id1': 'engagement_lvl1',
            'passenger_id2': 'engagement_lvl2',
            ...
            }
        }
    """
    pass

@app.route('/news_suggestion', methods=['GET'])
def news_suggestion():
    """
        ?users GET paramter must contain the list of users separated by a ';' semicolon
        Client asks for a news to propose, given the passengers on board

        passengers_usernames: the list of passengers on board

        returns a json formatted list of suggested news
    """
    if "users" not in request.args:
        return jsonify({'success': False, 'error': '\'users\' parameter was not given'})
    passengers_usernames = request.args["users"].split(";")
    print("received passengers names: ", passengers_usernames)
    users_df = get_users_df()
    passengers_embeddings = users_df[users_df['username'].isin(passengers_usernames)]['interests'].to_list()
    coll = load_collection_df()
    ret_json = RetrievalSystem.retrieve(coll, passengers_embeddings, 10)
    return Response(ret_json, mimetype='application/json')


if __name__ == '__main__':
    os.makedirs(CLIENT_AUDIO_UPLOAD_PATH, exist_ok=True)
    os.makedirs(SPEAKER_PROFILE_OUTPUT_PATH, exist_ok=True)

    #threaded=True to allow multiple connections
    app.run(debug=True, host='0.0.0.0', threaded=True)

from flask import Flask, render_template, request
import argparse
import contextlib
import os
import struct
import time
import wave
import pveagle
from pvrecorder import PvRecorder
from enrollment_animation import EnrollmentAnimation
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

PV_RECORDER_FRAME_LENGTH = int(os.getenv("PV_RECORDER_FRAME_LENGTH"))
API_KEY = os.getenv("API_KEY")

FEEDBACK_TO_DESCRIPTIVE_MSG = {
    pveagle.EagleProfilerEnrollFeedback.AUDIO_OK: 'Good audio',
    pveagle.EagleProfilerEnrollFeedback.AUDIO_TOO_SHORT: 'Insufficient audio length',
    pveagle.EagleProfilerEnrollFeedback.UNKNOWN_SPEAKER: 'Different speaker in audio',
    pveagle.EagleProfilerEnrollFeedback.NO_VOICE_FOUND: 'No voice found in audio',
    pveagle.EagleProfilerEnrollFeedback.QUALITY_ISSUE: 'Low audio quality due to bad microphone or environment'
}

@app.route('/')
def index():
    return render_template('index.html')

def enroll_operation():
    try:
        eagle_profiler = pveagle.create_profiler(access_key=API_KEY)

        print('Eagle version: %s' % eagle_profiler.version)
        recorder = PvRecorder(frame_length=PV_RECORDER_FRAME_LENGTH, device_index=0)
        print("Recording audio from '%s'" % recorder.selected_device)
        num_enroll_frames = eagle_profiler.min_enroll_samples // PV_RECORDER_FRAME_LENGTH
        sample_rate = eagle_profiler.sample_rate
        enrollment_animation = EnrollmentAnimation()
        print('Please keep speaking until the enrollment percentage reaches 100%')
        try:
            with contextlib.ExitStack() as file_stack:
                #if "output.wav":
                    #enroll_audio_file = file_stack.enter_context(wave.open("output.wav", 'wb'))
                    #enroll_audio_file.setnchannels(1)
                    #enroll_audio_file.setsampwidth(2)
                    #enroll_audio_file.setframerate(sample_rate)

                enroll_percentage = 0.0
                enrollment_animation.start()
                while enroll_percentage < 100.0:
                    enroll_pcm = list()
                    recorder.start()
                    for _ in range(num_enroll_frames):
                        input_frame = recorder.read()
                        #enroll_audio_file.writeframes(struct.pack('%dh' % len(input_frame), *input_frame))
                        enroll_pcm.extend(input_frame)
                    recorder.stop()

                    enroll_percentage, feedback = eagle_profiler.enroll(enroll_pcm)
                    enrollment_animation.percentage = enroll_percentage
                    enrollment_animation.feedback = ' - %s'  % FEEDBACK_TO_DESCRIPTIVE_MSG[feedback]

            speaker_profile = eagle_profiler.export()
            enrollment_animation.stop()
            with open("output.pv", 'wb') as f:
                f.write(speaker_profile.to_bytes())
            print('\nSpeaker profile is saved')

            # send form data for displaying in the result page
            username = request.form.get('username')
            selected_categories = ', '.join(request.form.getlist('categories'))
            soccer_interest = request.form.get('soccerInterest')
            politics_interest = request.form.get('politicsInterest')
            photography_interest = request.form.get('photographyInterest')

            # pass the data to the template
            return render_template('result.html', result_message="Enrollment successful!",
                                   username=username, selected_categories=selected_categories,
                                   soccer_interest=soccer_interest, politics_interest=politics_interest,
                                   photography_interest=photography_interest)

        except KeyboardInterrupt:
            print('\nStopping enrollment. No speaker profile is saved.')
            enrollment_animation.stop()
        except pveagle.EagleActivationLimitError:
            print('AccessKey has reached its processing limit')
        except pveagle.EagleError as e:
            print('Failed to enroll speaker: %s' % e)
        finally:
            recorder.stop()
            recorder.delete()
            eagle_profiler.delete()

    except pveagle.EagleError as e:
        return render_template('result.html', result_message=f"Enrollment failed: {str(e)}")

@app.route('/enroll', methods=['POST'])
def enroll():
    return enroll_operation()

if __name__ == '__main__':
    app.run(debug=True)

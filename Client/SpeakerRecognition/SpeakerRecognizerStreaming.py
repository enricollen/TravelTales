import contextlib
import os
import struct
import time
import wave
from dotenv import load_dotenv
from pvrecorder import PvRecorder
from enrollment_animation import EnrollmentAnimation
import pveagle

load_dotenv()

PV_RECORDER_FRAME_LENGTH = int(os.getenv("PV_RECORDER_FRAME_LENGTH"))
SILENCE_THRESHOLD = int(os.getenv("SILENCE_THRESHOLD"))
MIN_SPEECH_DURATION = int(os.getenv("MIN_SPEECH_DURATION"))
FEEDBACK_TO_DESCRIPTIVE_MSG = {
    pveagle.EagleProfilerEnrollFeedback.AUDIO_OK: 'Good audio',
    pveagle.EagleProfilerEnrollFeedback.AUDIO_TOO_SHORT: 'Insufficient audio length',
    pveagle.EagleProfilerEnrollFeedback.UNKNOWN_SPEAKER: 'Different speaker in audio',
    pveagle.EagleProfilerEnrollFeedback.NO_VOICE_FOUND: 'No voice found in audio',
    pveagle.EagleProfilerEnrollFeedback.QUALITY_ISSUE: 'Low audio quality due to bad microphone or environment'
}


class SpeakerRecognizerStreaming:
    def __init__(self):
        self.access_key = os.getenv("API_KEY")

    def read_file(self, file_name, sample_rate):
        """
            Read audio file and make sure it is 16-bit mono and 16KHz, thus handling the audio formats supported by wave module.
            file_name: the path to the audio file
            sample_rate: the sample rate of the audio file
        """
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

        frames = struct.unpack('h' * num_frames * channels, samples)

        return frames[::channels]

    def print_result(self, scores, labels):
        result = '\rscores -> '
        result += ', '.join('`%s`: %.2f' % (label, score) for label, score in zip(labels, scores))
        print(result, end='', flush=True)


    def enroll(self, model_path, library_path, audio_device_index, output_audio_path, output_profile_path):
        try:
            eagle_profiler = pveagle.create_profiler(
                access_key=self.access_key,
                model_path=model_path,
                library_path=library_path)
        except pveagle.EagleError as e:
            print("Failed to initialize Eagle: %s" % e)
            raise

        print('Eagle version: %s' % eagle_profiler.version)
        recorder = PvRecorder(frame_length=PV_RECORDER_FRAME_LENGTH, device_index=audio_device_index)
        print("Recording audio from '%s'" % recorder.selected_device)
        num_enroll_frames = eagle_profiler.min_enroll_samples // PV_RECORDER_FRAME_LENGTH
        sample_rate = eagle_profiler.sample_rate
        enrollment_animation = EnrollmentAnimation()
        print('Please keep speaking until the enrollment percentage reaches 100%')
        try:
            with contextlib.ExitStack() as file_stack:
                if output_audio_path is not None:
                    enroll_audio_file = file_stack.enter_context(wave.open(output_audio_path, 'wb'))
                    enroll_audio_file.setnchannels(1)
                    enroll_audio_file.setsampwidth(2)
                    enroll_audio_file.setframerate(sample_rate)

                enroll_percentage = 0.0
                enrollment_animation.start()
                while enroll_percentage < 100.0:
                    enroll_pcm = list()
                    recorder.start()
                    for _ in range(num_enroll_frames):
                        input_frame = recorder.read()
                        if output_audio_path is not None:
                            enroll_audio_file.writeframes(struct.pack('%dh' % len(input_frame), *input_frame))
                        enroll_pcm.extend(input_frame)
                    recorder.stop()

                    enroll_percentage, feedback = eagle_profiler.enroll(enroll_pcm)
                    enrollment_animation.percentage = enroll_percentage
                    enrollment_animation.feedback = ' - %s' % FEEDBACK_TO_DESCRIPTIVE_MSG[feedback]

            speaker_profile = eagle_profiler.export()
            enrollment_animation.stop()
            with open(output_profile_path, 'wb') as f:
                f.write(speaker_profile.to_bytes())
            print('\nSpeaker profile is saved to %s' % output_profile_path)

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

    def test(self, model_path, library_path, audio_device_index, output_audio_path,
             input_profile_paths, min_speech_duration=15):
        profiles = list()
        speaker_labels = list()
        for profile_path in input_profile_paths:
            speaker_labels.append(os.path.splitext(os.path.basename(profile_path))[0])
            with open(profile_path, 'rb') as f:
                profile = pveagle.EagleProfile.from_bytes(f.read())
            profiles.append(profile)

        try:
            eagle = pveagle.create_recognizer(
                access_key=self.access_key,
                model_path=model_path,
                library_path=library_path,
                speaker_profiles=profiles)

            recorder = PvRecorder(device_index=audio_device_index, frame_length=eagle.frame_length)
            recorder.start()

            with contextlib.ExitStack() as file_stack:
                if output_audio_path is not None:
                    test_audio_file = file_stack.enter_context(wave.open(output_audio_path, 'wb'))
                    test_audio_file.setnchannels(1)
                    test_audio_file.setsampwidth(2)
                    test_audio_file.setframerate(eagle.sample_rate)

                print('Listening for audio... (press Ctrl+C to stop)')
                start_times = {label: None for label in speaker_labels}
                enrollment_animation = EnrollmentAnimation()

                silence_duration = 0.0
                recording_active = {label: False for label in speaker_labels}
                start_times = {label: None for label in speaker_labels}
                speech_buffer = {label: [] for label in speaker_labels}

                try:
                    while True:
                        pcm = recorder.read()
                        if output_audio_path is not None:
                            for label, active in recording_active.items():
                                if active:
                                    test_audio_file.writeframes(struct.pack('%dh' % len(pcm), *pcm))

                        scores = eagle.process(pcm)
                        self.print_result(scores, speaker_labels)

                        no_speech_detected = all(confidence <= 0.0 for confidence in scores)

                        if no_speech_detected:
                            silence_duration += eagle.frame_length / eagle.sample_rate
                        else:
                            silence_duration = 0.0

                        if silence_duration > SILENCE_THRESHOLD:
                            print(f'\nNo speech detected for {silence_duration:.2f} seconds. Stopping...')
                            break

                        for label, confidence in zip(speaker_labels, scores):
                            if confidence > 0.0:
                                if not recording_active[label]:
                                    recording_active[label] = True
                                    start_times[label] = time.time()
                                    # start of speech, initialize audio buffer
                                    speech_buffer[label] = []
                                else:
                                    # append audio to buffer during speech
                                    speech_buffer[label].extend(pcm)
                            elif recording_active[label]:
                                # check for end of speech
                                end_time = time.time()
                                duration = end_time - start_times[label]
                                if duration > min_speech_duration:
                                    # here I save the audio buffer associated with the speech
                                    output_folder = os.getenv("SPEECH_OUTPUT_FOLDER")
                                    if not os.path.exists(output_folder):
                                        os.makedirs(output_folder)
                                    export_path = f"{output_folder}/{label}_speech_{int(start_times[label])}.wav"
                                    with wave.open(export_path, 'wb') as export_file:
                                        export_file.setnchannels(1)
                                        export_file.setsampwidth(2)
                                        export_file.setframerate(eagle.sample_rate)
                                        export_file.writeframes(
                                            struct.pack('%dh' % len(speech_buffer[label]), *speech_buffer[label]))
                                    print(f"\nSpeaker '{label}' talked with confidence > 0.0 for {duration:.2f} seconds\n"
                                          f"Audio saved to: {export_path}\n")
                                recording_active[label] = False

                except KeyboardInterrupt:
                    print('\nStopping...')
                except pveagle.EagleActivationLimitError:
                    print('\nAccessKey has reached its processing limit')
                finally:
                    recorder.stop()
                    recorder.delete()

        finally:
            if eagle is not None:
                eagle.delete()

    def show_audio_devices(self):
        for index, name in enumerate(PvRecorder.get_available_devices()):
            print('Device #%d: %s' % (index, name))


if __name__ == '__main__':
    speaker_recognizer = SpeakerRecognizerStreaming()

    #enrollment
    """enroll_model_path = None
    enroll_library_path = None
    enroll_audio_device_index = 0
    enroll_output_audio_path = None #"Server/speaker_profiles/enrico.pv"
    enroll_output_profile_path = "marianna.pv"
    speaker_recognizer.enroll(
        model_path=enroll_model_path,
        library_path=enroll_library_path,
        audio_device_index=enroll_audio_device_index,
        output_audio_path=enroll_output_audio_path,
        output_profile_path=enroll_output_profile_path)"""

    #testing
    test_model_path = None
    test_library_path = None
    test_audio_device_index = 0
    test_output_audio_path = None
    test_input_profile_paths = ["Server/speaker_profiles/enrico.pv", "Server/speaker_profiles/marianna.pv"]
    test_min_speech_duration = MIN_SPEECH_DURATION
    speaker_recognizer.test(
        model_path=test_model_path,
        library_path=test_library_path,
        audio_device_index=test_audio_device_index,
        output_audio_path=test_output_audio_path,
        input_profile_paths=test_input_profile_paths,
        min_speech_duration=test_min_speech_duration)

    #show available audio devices
    #speaker_recognizer.show_audio_devices()

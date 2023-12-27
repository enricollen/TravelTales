import contextlib
import csv
import os
import struct
import wave
import pveagle
from dotenv import load_dotenv

load_dotenv()

FEEDBACK_TO_DESCRIPTIVE_MSG = {
    pveagle.EagleProfilerEnrollFeedback.AUDIO_OK: 'Good audio',
    pveagle.EagleProfilerEnrollFeedback.AUDIO_TOO_SHORT: 'Insufficient audio length',
    pveagle.EagleProfilerEnrollFeedback.UNKNOWN_SPEAKER: 'Different speaker in audio',
    pveagle.EagleProfilerEnrollFeedback.NO_VOICE_FOUND: 'No voice found in audio',
    pveagle.EagleProfilerEnrollFeedback.QUALITY_ISSUE: 'Low audio quality due to bad microphone or environment'
}

class SpeakerRecognizer:
    def __init__(self):
        self.eagle_profiler = None
        self.eagle = None
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

    def print_result(self, time, scores, labels):
        result = 'time: %4.2f sec | scores -> ' % time
        result += ', '.join('`%s`: %.2f' % (label, score) for label, score in zip(labels, scores))
        print(result)

    def enroll(self, enroll_audio_paths, output_profile_path):
            """
                Enroll a speaker profile.
                enroll_audio_paths: a list of paths to audio files for enrollment
                output_profile_path: the path to save the speaker profile
            """
            try:
                self.eagle_profiler = pveagle.create_profiler(
                    access_key=self.access_key,
                    model_path=None,  # specify model_path or let the library use the default.
                    library_path=None  # specify library_path or let the library use the default.
                )
            except pveagle.EagleError as e:
                print("Failed to initialize EagleProfiler: ", e)
                raise

            print('Eagle version: %s' % self.eagle_profiler.version)

            try:
                enroll_percentage = 0.0
                for audio_path in enroll_audio_paths:
                    if not audio_path.lower().endswith('.wav'):
                        raise ValueError('Given argument --enroll_audio_paths must have WAV file extension')

                    audio = self.read_file(audio_path, self.eagle_profiler.sample_rate)
                    enroll_percentage, feedback = self.eagle_profiler.enroll(audio)
                    print('Enrolled audio file %s [Enrollment percentage: %.2f%% - Enrollment feedback: %s]'
                        % (audio_path, enroll_percentage, FEEDBACK_TO_DESCRIPTIVE_MSG[feedback]))

                if enroll_percentage < 100.0:
                    print('Failed to create a speaker profile. Insufficient enrollment percentage: %.2f%%. '
                        'Please add more audio files for enrollment.' % enroll_percentage)
                else:
                    speaker_profile = self.eagle_profiler.export()
                    if output_profile_path is not None:
                        with open(output_profile_path, 'wb') as f:
                            f.write(speaker_profile.to_bytes())
                        print('Speaker profile is saved to %s' % output_profile_path)
            except pveagle.EagleActivationLimitError:
                print('AccessKey has reached its processing limit')
            except pveagle.EagleError as e:
                print('Failed to perform enrollment: ', e)
            finally:
                self.eagle_profiler.delete()

    def test(self, input_profile_paths, test_audio_path, csv_output_path):
            """
                Test a speaker profile.
                input_profile_paths: a list of paths to speaker profiles for testing
                test_audio_path: the path to the audio file for testing
                csv_output_path: the path to save the test result as a CSV file (optional)
            """
            speaker_profiles = []
            speaker_labels = []
            for input_profile_path in input_profile_paths:
                speaker_labels.append(os.path.splitext(os.path.basename(input_profile_path))[0])
                with open(input_profile_path, 'rb') as f:
                    speaker_profiles.append(pveagle.EagleProfile.from_bytes(f.read()))

            try:
                self.eagle = pveagle.create_recognizer(
                    access_key=self.access_key,
                    model_path=None,  # specify model_path or let the library use the default.
                    library_path=None,  # specify library_path or let the library use the default.
                    speaker_profiles=speaker_profiles
                )
            except pveagle.EagleActivationLimitError:
                print('AccessKey has reached its processing limit.')
            except pveagle.EagleError as e:
                print("Failed to initialize Eagle: ", e)
                raise

            print('Eagle version: %s' % self.eagle.version)

            csv_file = None
            result_writer = None
            with contextlib.ExitStack() as file_stack:
                if csv_output_path:
                    csv_file = file_stack.enter_context(open(csv_output_path, mode='w'))
                    result_writer = csv.writer(csv_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                    result_writer.writerow(['time', *['Speaker_%d' % i for i in range(len(speaker_profiles))]])

                try:
                    audio = self.read_file(test_audio_path, self.eagle.sample_rate)
                    num_frames = len(audio) // self.eagle.frame_length
                    frame_to_second = self.eagle.frame_length / self.eagle.sample_rate
                    for i in range(num_frames):
                        frame = audio[i * self.eagle.frame_length:(i + 1) * self.eagle.frame_length]
                        scores = self.eagle.process(frame)
                        time = i * frame_to_second
                        if result_writer is not None:
                            result_writer.writerow([time, *scores])
                        else:
                            self.print_result(time, scores, speaker_labels)

                    if result_writer is not None:
                        print('Test result is saved to %s' % csv_output_path)

                except pveagle.EagleActivationLimitError:
                    print('AccessKey has reached its processing limit.')
                except pveagle.EagleError as e:
                    print("Failed to process audio: ", e)
                    raise
                finally:
                    self.eagle.delete()


"""
if __name__ == '__main__':
    speaker_recognizer = SpeakerRecognizer()

    # usage for enrollment
    enroll_audio_paths = ["enroll.wav"]
    output_profile_path = "output_profile.pv"
    speaker_recognizer.enroll(enroll_audio_paths, output_profile_path)

    # usage for testing
    input_profile_paths = ["enrico.pv"]
    test_audio_path = "test.wav"
    csv_output_path = "output.csv"
    speaker_recognizer.test(input_profile_paths, test_audio_path, csv_output_path)
"""
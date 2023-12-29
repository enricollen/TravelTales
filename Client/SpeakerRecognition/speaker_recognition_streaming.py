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

PV_RECORDER_FRAME_LENGTH = int(os.getenv("PV_RECORDER_FRAME_LENGTH"))
SILENCE_THRESHOLD = int(os.getenv("SILENCE_THRESHOLD"))
FEEDBACK_TO_DESCRIPTIVE_MSG = {
    pveagle.EagleProfilerEnrollFeedback.AUDIO_OK: 'Good audio',
    pveagle.EagleProfilerEnrollFeedback.AUDIO_TOO_SHORT: 'Insufficient audio length',
    pveagle.EagleProfilerEnrollFeedback.UNKNOWN_SPEAKER: 'Different speaker in audio',
    pveagle.EagleProfilerEnrollFeedback.NO_VOICE_FOUND: 'No voice found in audio',
    pveagle.EagleProfilerEnrollFeedback.QUALITY_ISSUE: 'Low audio quality due to bad microphone or environment'
}


def print_result(scores, labels):
    result = '\rscores -> '
    result += ', '.join('`%s`: %.2f' % (label, score) for label, score in zip(labels, scores))
    print(result, end='', flush=True)


def enroll_operation(args):
    try:
            eagle_profiler = pveagle.create_profiler(
                access_key=args.access_key,
                model_path=args.model_path,
                library_path=args.library_path)
    except pveagle.EagleError as e:
        print("Failed to initialize Eagle: %s" % e)
        raise

    print('Eagle version: %s' % eagle_profiler.version)
    recorder = PvRecorder(frame_length=PV_RECORDER_FRAME_LENGTH, device_index=args.audio_device_index)
    print("Recording audio from '%s'" % recorder.selected_device)
    num_enroll_frames = eagle_profiler.min_enroll_samples // PV_RECORDER_FRAME_LENGTH
    sample_rate = eagle_profiler.sample_rate
    enrollment_animation = EnrollmentAnimation()
    print('Please keep speaking until the enrollment percentage reaches 100%')
    try:
        with contextlib.ExitStack() as file_stack:
            if args.output_audio_path is not None:
                enroll_audio_file = file_stack.enter_context(wave.open(args.output_audio_path, 'wb'))
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
                    if args.output_audio_path is not None:
                        enroll_audio_file.writeframes(struct.pack('%dh' % len(input_frame), *input_frame))
                    enroll_pcm.extend(input_frame)
                recorder.stop()

                enroll_percentage, feedback = eagle_profiler.enroll(enroll_pcm)
                enrollment_animation.percentage = enroll_percentage
                enrollment_animation.feedback = ' - %s' % FEEDBACK_TO_DESCRIPTIVE_MSG[feedback]

        speaker_profile = eagle_profiler.export()
        enrollment_animation.stop()
        with open(args.output_profile_path, 'wb') as f:
            f.write(speaker_profile.to_bytes())
        print('\nSpeaker profile is saved to %s' % args.output_profile_path)

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

def test_operation(args):
    profiles = list()
    speaker_labels = list()
    for profile_path in args.input_profile_paths:
        speaker_labels.append(os.path.splitext(os.path.basename(profile_path))[0])
        with open(profile_path, 'rb') as f:
            profile = pveagle.EagleProfile.from_bytes(f.read())
        profiles.append(profile)

    eagle = pveagle.create_recognizer(
        access_key=args.access_key,
        model_path=args.model_path,
        library_path=args.library_path,
        speaker_profiles=profiles)

    recorder = PvRecorder(device_index=args.audio_device_index, frame_length=eagle.frame_length)
    recorder.start()

    with contextlib.ExitStack() as file_stack:
        if args.output_audio_path is not None:
            test_audio_file = file_stack.enter_context(wave.open(args.output_audio_path, 'wb'))
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
                if args.output_audio_path is not None:
                    for label, active in recording_active.items():
                        if active:
                            test_audio_file.writeframes(struct.pack('%dh' % len(pcm), *pcm))

                scores = eagle.process(pcm)
                print_result(scores, speaker_labels)

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
                            #start of speech, initialize audio buffer
                            speech_buffer[label] = []
                        else:
                            #append audio to buffer during speech
                            speech_buffer[label].extend(pcm)
                    elif recording_active[label]:
                        #check for end of speech
                        end_time = time.time()
                        duration = end_time - start_times[label]
                        if duration > args.min_speech_duration:
                            #here i save the audio buffer associated with the speech
                            output_folder = os.getenv("SPEECH_OUTPUT_FOLDER")
                            if not os.path.exists(output_folder):
                                os.makedirs(output_folder)
                            export_path = f"{output_folder}/{label}_speech_{int(start_times[label])}.wav"
                            with wave.open(export_path, 'wb') as export_file:
                                export_file.setnchannels(1)
                                export_file.setsampwidth(2)
                                export_file.setframerate(eagle.sample_rate)
                                export_file.writeframes(struct.pack('%dh' % len(speech_buffer[label]), *speech_buffer[label]))
                            print(f"\nSpeaker '{label}' talked with confidence > 0.0 for {duration:.2f} seconds\n"
                                    f"Audio saved to: {export_path}\n")
                        recording_active[label] = False

        except KeyboardInterrupt:
            print('\nStopping...')
        except pveagle.EagleActivationLimitError:
            print('\nAccessKey has reached its processing limit')
        finally:
            if eagle is not None:
                eagle.delete()
            recorder.stop()
            recorder.delete()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--show_audio_devices',
        action='store_true',
        help='List available audio input devices and exit')

    common_parser = argparse.ArgumentParser(add_help=False)
    common_parser.add_argument(
        '--access_key',
        required=True,
        help='AccessKey obtained from Picovoice Console (https://console.picovoice.ai/)')
    common_parser.add_argument(
        '--library_path',
        help='Absolute path to dynamic library. Default: using the library provided by `pveagle`')
    common_parser.add_argument(
        '--model_path',
        help='Absolute path to Eagle model. Default: using the model provided by `pveagle`')
    common_parser.add_argument('--audio_device_index', type=int, default=-1, help='Index of input audio device')
    common_parser.add_argument(
        '--output_audio_path',
        help='If provided, all recorded audio data will be saved to the given .wav file')

    subparsers = parser.add_subparsers(dest='command')

    enroll = subparsers.add_parser('enroll', help='Enroll a new speaker profile', parents=[common_parser])
    enroll.add_argument(
        '--output_profile_path',
        required=True,
        help='Absolute path to output file for the created profile')

    test = subparsers.add_parser(
        'test',
        help='Evaluate Eagle''s performance using the provided speaker profiles.',
        parents=[common_parser])
    test.add_argument(
        '--input_profile_paths',
        required=True,
        nargs='+',
        help='Absolute path(s) to speaker profile(s)')
    test.add_argument(
        '--min_speech_duration',
        type=float,
        default=os.getenv("MIN_SPEECH_DURATION"),
        help='Minimum duration (in seconds) for speech segments to be saved. Default: 4.0')

    args = parser.parse_args()

    if args.show_audio_devices:
        for index, name in enumerate(PvRecorder.get_available_devices()):
            print('Device #%d: %s' % (index, name))
        return

    if args.command == 'enroll':
        enroll_operation(args)

    elif args.command == 'test':
        test_operation(args)

    else:
        print('Please specify a mode: enroll or test')
        return


if __name__ == '__main__':
    main()
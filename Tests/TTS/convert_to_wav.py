from pydub import AudioSegment

def _to_wav(file_path, wav_file_path, format="m4a"):
    """
        convert webm to wav format and force audio to be 16-bit mono and 16KHz
        webm_file_path: the path to the webm file
        wav_file_path: the path to the wav file
    """
    audio = AudioSegment.from_file(file_path, format=format)
    audio = audio.set_frame_rate(16000)
    audio = audio.set_sample_width(2)
    audio.export(wav_file_path, format="ogg")



if __name__ == "__main__":
    _to_wav("./voices/berlusconi-siete-ancora-oggi.mp3", "./voices/berlusconi.wav", "mp3")
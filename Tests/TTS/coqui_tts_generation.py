import torch
from TTS.api import TTS

# Get device
device = "cuda" if torch.cuda.is_available() else "cpu"

# List available 🐸TTS models
print(TTS().list_models())

# Init TTS
TTS_bark = "tts_models/multilingual/multi-dataset/bark"
TTS_xtts_v2 = "tts_models/multilingual/multi-dataset/xtts_v2"
tts = TTS(TTS_xtts_v2).to(device)

# Run TTS
# ❗ Since this model is multi-lingual voice cloning model, we must set the target speaker_wav and language
# Text to speech list of amplitude values as output
#wav = tts.tts(text="Hello world!", speaker_wav="my/cloning/audio.wav", language="en")
# Text to speech to a file

input_txt="""
Roofs were torn off houses, trees blew down and walls collapsed. Police declared a major incident in Tameside at about 23:45 GMT on Wednesday. Around a hundred homes have been damaged and people are being asked to avoid the area. Storm Gerrit has brought flooding and disrupted travel in Scotland.
"""

alt_input = """
Hello everybody [uh], my name is Marcellino. I am going to introduce you a simple tool of the [he] artificial intelligence [ah].
"""

r_input = """
Ragazzi parliamoci chiaramente, il mio scopo ultimo nella vita è diventare il capo dei boy scout di rignano sull'arno, non mi rompete i coglioni, sto solo cercando di raggiungerlo.
"""

tts.tts_to_file(text=input_txt, speaker_wav="voices/renzi.wav", speed=1.4, language="en", file_path="generated_tts/xtts_v2/renzi.wav")

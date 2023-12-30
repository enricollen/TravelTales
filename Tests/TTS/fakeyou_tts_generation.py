import fakeyou

# modello di gerry scotti
MODEL_TOKEN = "TM:5ggf3m5w2mhq"

obj = fakeyou.FakeYou()
obj.create_account("pippoJ", "password", "pippo@mail.it")

wav_file = obj.say("Salve a tutti ragazzi sono il mitico gerry scotti", MODEL_TOKEN)

voices = obj.list_voices()

#voices.json
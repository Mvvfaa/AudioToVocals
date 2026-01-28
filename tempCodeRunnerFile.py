import torchaudio

torchaudio.set_audio_backend("soundfile")

print("Loading audio...")
waveform, sr = torchaudio.load("Amen.wav")
print(waveform.shape, sr)
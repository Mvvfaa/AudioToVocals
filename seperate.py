# seperate.py
# works with Open-Unmix to separate audio into stems and save them as individual files

import torch
import torchaudio
from openunmix import predict
from pathlib import Path

# ---------- CONFIG ----------
INPUT_AUDIO = "AL.wav"     # your song
OUTPUT_DIR = "outputs"
SAMPLE_RATE = 44100
# ----------------------------

print("Loading audio...")

audio, sr = torchaudio.load(INPUT_AUDIO)

# convert mono → stereo if needed
if audio.shape[0] == 1:
    audio = audio.repeat(2, 1)

print("Running Open-Unmix...")

estimates = predict.separate(
    audio,
    rate=sr
)

Path(OUTPUT_DIR).mkdir(exist_ok=True)

print("Saving outputs...")

# remove batch dimension (1, C, T) → (C, T)
vocals = estimates["vocals"].squeeze(0)
drums = estimates["drums"].squeeze(0)
bass = estimates["bass"].squeeze(0)
other = estimates["other"].squeeze(0)

# create accompaniment manually
accompaniment = drums + bass + other

torchaudio.save(f"{OUTPUT_DIR}/vocals.wav", vocals, SAMPLE_RATE)
torchaudio.save(f"{OUTPUT_DIR}/drums.wav", drums, SAMPLE_RATE)
torchaudio.save(f"{OUTPUT_DIR}/bass.wav", bass, SAMPLE_RATE)
torchaudio.save(f"{OUTPUT_DIR}/other.wav", other, SAMPLE_RATE)
torchaudio.save(f"{OUTPUT_DIR}/accompaniment.wav", accompaniment, SAMPLE_RATE)

print("Done! ^_^")

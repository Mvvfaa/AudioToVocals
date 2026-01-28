import torch
import torchaudio
import soundfile as sf
from pathlib import Path

from demucs.pretrained import get_model
from demucs.apply import apply_model

# ---------------- CONFIG ----------------
INPUT_FILE = "AL.wav"
OUTPUT_DIR = "outputs_demucs"
MODEL_NAME = "htdemucs"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# CLI-like quality settings
SHIFTS = 4          # time-shift augmentation (CLI uses this)
SPLIT = True
OVERLAP = 0.25
# ----------------------------------------

print("Loading audio...")
wav, sr = torchaudio.load(INPUT_FILE)

# Stereo required
if wav.shape[0] == 1:
    wav = wav.repeat(2, 1)

wav = wav.unsqueeze(0).to(DEVICE)

print("Loading Demucs model...")
model = get_model(MODEL_NAME)
model.to(DEVICE)
model.eval()

print("Running Demucs (high quality)...")
with torch.no_grad():
    sources = apply_model(
        model,
        wav,
        device=DEVICE,
        shifts=SHIFTS,
        split=SPLIT,
        overlap=OVERLAP,
        progress=True
    )

Path(OUTPUT_DIR).mkdir(exist_ok=True)

print("Saving stems...")
for i, name in enumerate(model.sources):
    stem = sources[0, i].cpu().numpy().T
    sf.write(f"{OUTPUT_DIR}/{name}.wav", stem, sr)
    print(f"Saved: {name}.wav")

print("Done! ^_^")
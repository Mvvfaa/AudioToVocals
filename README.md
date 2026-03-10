# Vocal Extraction Web App (MDX Pipeline)

A Streamlit app for high-quality vocal extraction using a two-step MDX/UVR pipeline:
1. MDX Main separates vocals from the full mix.
2. Inst HQ refines vocals to reduce residual instrument artifacts.

This setup is tuned for vocal clarity across studio tracks, heavy instrumentals, and noisy/live recordings.

CPU-only processing is supported, but high-quality presets can take 15-30 minutes per song.

---

## Features

- Upload MP3, WAV, or FLAC audio files.
- Two-stage separation pipeline for cleaner vocals.
- Presets for different song types:
- `Normal (fast)`: ~6-10 minutes
- `Heavy Instrumental`: ~15-20 minutes
- `Noisy / Live`: ~20-30 minutes
- Live progress feedback in the Streamlit UI.
- Download final vocals as MP3.
- Safer temporary file handling across runs.

---

## Pipeline Overview

```text
Input Song
  -> MDX Main (Vocals + Instrumental)
  -> Inst HQ Model (Vocals Refinement)
  -> Final Clean Vocals
```

Why this works:
- MDX Main removes most of the music structure.
- Inst HQ cleans remaining instrument bleed and artifacts.

---

## Requirements

- Windows (tested)
- Python 3.10 (`runtime.txt`)
- CPU (GPU optional)
- FFmpeg available in PATH (`packages.txt`)

---

## Installation

### 1. Create and activate a virtual environment

```bash
python -m venv .venv
.venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

Models are automatically downloaded by `audio-separator` when first used.

---

## Run the App

```bash
streamlit run Home.py
```

Then open `http://localhost:8501`.

---

## Presets Explained

| Preset | Use Case | Time (CPU) |
| --- | --- | --- |
| Normal | Studio / clean songs | ~6-10 min |
| Heavy Instrumental | Dense beats, loud instrumentals | ~20-30 min |
| Noisy / Live | Live vocals, background noise | ~20-30 min |

Tip: start with `Normal` and only switch to heavy presets when needed.

---

## Project Structure

```text
AudioToVocals/
|- Home.py
|- pages/
|  |- 1_MDX.py
|- examples/
|- requirements.txt
|- packages.txt
|- runtime.txt
`- README.md
```

---

## Known Limitations

- CPU processing can be slow for long audio files.
- Streamlit cannot fully mirror terminal-style progress bars.
- Very long songs may take significant time with heavy presets.

---

## Built With

- [Streamlit](https://streamlit.io/)
- [audio-separator](https://github.com/Anjok07/ultimatevocalremovergui)
- MDX / UVR models
- FFmpeg

---

## License

This project is intended for educational and personal use.
Model licenses belong to their respective authors.

---

## Acknowledgements

- UVR / MDX community
- audio-separator contributors
- Open-source audio ML ecosystem

# 🎤 Vocal Extraction Web App (MDX Pipeline)

A Streamlit-based web app for **high-quality vocal extraction** using the  
**MDX Main → Inst HQ (UVR) two-step pipeline**.

This app is optimized for **vocal clarity** and works well for:
- Studio tracks
- Heavy instrumental songs
- Noisy or live recordings

> ⚠️ CPU-only processing is supported, but high-quality presets can take **15–30 minutes** per song.

---

## ✨ Features

- 🎧 Upload **MP3 / WAV / FLAC** files
- 🧪 Two-stage separation pipeline:
  1. **MDX Main** – Extract vocals from full mix
  2. **Inst HQ** – Clean and refine vocals
- 🎚 Presets for different song types:
  - **Normal (fast)** – ~6–10 minutes
  - **Heavy Instrumental** – ~20–30 minutes
  - **Noisy / Live** – ~20–30 minutes
- 📊 Live progress feedback
- ⬇ Download final vocals as **MP3**
- 🧠 Safe file handling (no crashes if filenames change)

---

## 🧬 Pipeline Overview

```

Input Song
↓
MDX Main (Vocals + Instrumental)
↓
Inst HQ Model (Vocals Only)
↓
Final Clean Vocals

````

Why this works:
- **MDX Main** removes most of the music structure
- **Inst HQ** cleans residual instruments and artifacts

---

## 🖥 Requirements

- Windows (tested)
- Python **3.10**
- CPU (GPU optional but not required)
- FFmpeg installed and available in PATH

---

## 📦 Installation

### 1️⃣ Create & activate virtual environment
```bash
python -m venv mdx_venv
mdx_venv\Scripts\activate
````

### 2️⃣ Install dependencies

```bash
pip install streamlit audio-separator onnxruntime soundfile pydub
```

> Models are automatically downloaded by `audio-separator`.

---

## ▶️ Running the App

```bash
streamlit run MDX_app.py
```

Then open:

```
http://localhost:8501
```

---

## 🎛 Presets Explained

| Preset             | Use Case                        | Time (CPU) |
| ------------------ | ------------------------------- | ---------- |
| Normal             | Studio / clean songs            | ~6–10 min  |
| Heavy Instrumental | Dense beats, loud instrumentals | ~20–30 min |
| Noisy / Live       | Live vocals, background noise   | ~20–30 min |

💡 **Tip:** Use **Normal** if you’re in a hurry.

---

## 📁 Project Structure

```
AudioSep/
├─ MDX_app.py
├─ temp/
│   ├─ step1_<id>/
│   └─ step2_<id>/
├─ mdx_venv/
└─ README.md
```

Temporary files are generated per session and reused safely.

---

## ⚠️ Known Limitations

* CPU processing is slow for large files
* Streamlit UI cannot perfectly mirror terminal progress bars
* Very long songs may take significant time on heavy presets

---

## 🛠 Built With

* [Streamlit](https://streamlit.io/)
* [audio-separator](https://github.com/Anjok07/ultimatevocalremovergui)
* MDX / UVR models
* FFmpeg

---

## 📜 License

This project is for **educational and personal use**.
Model licenses belong to their respective authors.

---

## 🙌 Acknowledgements

* UVR / MDX community
* audio-separator contributors
* Open-source audio ML ecosystem

```

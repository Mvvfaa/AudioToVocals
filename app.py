import streamlit as st
import subprocess
import sys
from pathlib import Path
import shutil

st.set_page_config(page_title="Demucs Audio Separator", layout="centered")

st.title("🎧 AI Music Source Separation")
st.write("Powered by **Demucs (htdemucs)** — near-studio quality")

# Upload audio
uploaded_file = st.file_uploader(
    "Upload an audio file",
    type=["wav", "mp3", "flac"]
)

if uploaded_file:
    temp_dir = Path("temp")
    output_dir = Path("Halal_Demucs_Outputs")

    temp_dir.mkdir(exist_ok=True)
    output_dir.mkdir(exist_ok=True)

    audio_path = temp_dir / uploaded_file.name

    # Save uploaded file
    with open(audio_path, "wb") as f:
        f.write(uploaded_file.read())

    st.audio(str(audio_path))

    if st.button("🚀 Separate Audio"):
        with st.spinner("Running Demucs… this may take a minute ⏳"):
            try:
                cmd = [
                    sys.executable,
                    "-m", "demucs",
                    "-n", "htdemucs",
                    "-o", str(output_dir),
                    str(audio_path)
                ]

                subprocess.run(cmd, check=True)

                st.success("Separation complete 🎉")

                track_name = audio_path.stem
                stems_path = output_dir / "htdemucs" / track_name

                st.subheader("🎼 Download stems")

                for stem in stems_path.glob("*.wav"):
                    with open(stem, "rb") as f:
                        st.download_button(
                            label=f"⬇️ {stem.name}",
                            data=f,
                            file_name=stem.name,
                            mime="audio/wav"
                        )

            except subprocess.CalledProcessError as e:
                st.error("Demucs failed. Check logs.")
                st.text(str(e))

        # Cleanup temp file
        shutil.rmtree(temp_dir, ignore_errors=True)

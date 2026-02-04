import streamlit as st
import subprocess
import uuid
import os
from pathlib import Path

# ---------------- CONFIG ----------------
st.set_page_config(
    page_title="Vocal Separator",
    layout="wide"
)

TEMP_DIR = Path("temp")
TEMP_DIR.mkdir(exist_ok=True)

# ---------------- HELPERS ----------------
def run_with_logs(cmd, log_box):
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )

    logs = ""
    for line in process.stdout:
        logs += line
        log_box.text_area(
            "Processing log",
            logs,
            height=300
        )

    process.wait()
    if process.returncode != 0:
        raise RuntimeError("Processing failed")
    
def find_stem(folder, keyword):
    files = list(folder.glob(f"*{keyword}*"))
    if not files:
        return None
    return files[0]


# ---------------- HEADER ----------------
st.title("🎤 AI Vocal Separator")
st.caption("MDX-Net pipeline · High-quality vocal extraction")

# ---------------- ABOUT + EXAMPLE ----------------
left, right = st.columns([1.4, 1])

with left:
    st.subheader("About our service")
    st.write(
        """
        This tool separates **vocals and music** from any song using
        state-of-the-art **MDX-Net AI models**.
        
        • No account required  
        • MP3 / WAV supported  
        • Studio-quality results  
        """
    )

with right:
    st.subheader("Listen to an example")

    st.audio("examples/original.mp3", format="audio/mp3")
    st.audio("examples/vocals.mp3", format="audio/mp3")
    st.caption("Original song (top) vs Extracted vocals (bottom)")

# ---------------- UPLOAD ----------------
st.divider()
st.subheader("Upload your song")

uploaded = st.file_uploader(
    "MP3 or WAV file",
    type=["mp3", "wav"]
)

# ---------------- PRESETS ----------------
st.divider()
st.subheader("Choose a preset")

preset = st.radio(
    "",
    ["Normal", "Heavy instrumental", "Noisy / live"],
    horizontal=True
)

if preset == "Normal":
    st.success("✅ Best balance — Recommended")
    ETA = "≈ 6 minutes"
    MAIN = {"seg": 512, "overlap": 0.5}
    HQ = {"seg": 256, "overlap": 0.25}

elif preset == "Heavy instrumental":
    st.warning("⏳ Slower — Strong music removal")
    ETA = "≈ 26 minutes"
    MAIN = {"seg": 768, "overlap": 0.75}
    HQ = {"seg": 256, "overlap": 0.4}

else:
    st.error("🐢 Very Slow — Best for noisy recordings")
    ETA = "≈ 26 minutes"
    MAIN = {"seg": 1024, "overlap": 0.9}
    HQ = {"seg": 512, "overlap": 0.5}

st.caption(f"Estimated processing time: **{ETA}** (depends on CPU & song length)")

# ---------------- PROCESS ----------------
st.divider()

if uploaded and st.button("🎧 Extract Vocals"):
    job_id = uuid.uuid4().hex[:8]

    input_path = TEMP_DIR / f"{job_id}_{uploaded.name}"
    step1_dir = TEMP_DIR / f"step1_{job_id}"
    step2_dir = TEMP_DIR / f"step2_{job_id}"

    with open(input_path, "wb") as f:
        f.write(uploaded.read())

    # ---------- STEP 1 ----------
    st.subheader("Step 1 — Extracting vocals")
    log1 = st.empty()

    cmd_step1 = [
        "audio-separator",
        "-m", "UVR_MDXNET_Main.onnx",
        "--mdx_segment_size", str(MAIN["seg"]),
        "--mdx_overlap", str(MAIN["overlap"]),
        "--output_format", "MP3",
        "--output_dir", str(step1_dir),
        str(input_path)
    ]

    with st.spinner("Running MDX Main…"):
        run_with_logs(cmd_step1, log1)

    st.success("Step 1 complete")

    vocals_path = find_stem(step1_dir, "Vocals")
    if vocals_path is None:
        st.error("Vocals file not found.")
        st.stop()


    # ---------- STEP 2 ----------
    st.subheader("Step 2 — Cleaning vocals")
    log2 = st.empty()

    cmd_step2 = [
        "audio-separator",
        "-m", "UVR-MDX-NET-Inst_HQ_5.onnx",
        "--single_stem", "Vocals",
        "--mdx_segment_size", str(HQ["seg"]),
        "--mdx_overlap", str(HQ["overlap"]),
        "--output_format", "MP3",
        "--output_dir", str(step2_dir),
        str(vocals_path)
    ]

    with st.spinner("Refining vocals…"):
        run_with_logs(cmd_step2, log2)

    st.success("🎉 Final vocals ready!")

    # ---------- OUTPUT ----------
    st.subheader("Your extracted vocals")
    final_vocals = find_stem(step2_dir, "Vocals")
    if final_vocals is None:
        st.error("Final vocals file not found.")
        st.stop()

    st.audio(final_vocals.read_bytes(), format="audio/mp3")
    st.download_button(
        "⬇ Download vocals",
        final_vocals.read_bytes(),
        file_name="vocals.mp3"
    )

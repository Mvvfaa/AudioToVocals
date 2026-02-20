import streamlit as st
import subprocess
import uuid
import os
import shutil
from collections import deque
from pathlib import Path

# ---------------- CONFIG ----------------
st.set_page_config(
    page_title="Vocal Separator",
    layout="wide"
)

TEMP_DIR = Path("temp")
TEMP_DIR.mkdir(exist_ok=True)

# Streamlit Cloud timeout: 2 hours
PROCESS_TIMEOUT = 7200

# Max audio file size: 150MB to prevent crashes
MAX_FILE_SIZE = 150 * 1024 * 1024  # 150MB

# Store only critical info in session (not full logs to save memory)
if 'processing_status' not in st.session_state:
    st.session_state.processing_status = {}

# ---------------- HELPERS ----------------
def check_file_size(uploaded_file):
    """Validate audio file size to prevent memory issues"""
    if uploaded_file.size > MAX_FILE_SIZE:
        size_mb = uploaded_file.size / (1024 * 1024)
        max_mb = MAX_FILE_SIZE / (1024 * 1024)
        raise ValueError(f"File too large: {size_mb:.1f}MB. Maximum: {max_mb:.0f}MB")

def run_with_logs(cmd, status_container, job_id):
    """Run subprocess with minimal memory usage and keep a short log tail"""
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )

        line_count = 0
        log_tail = deque(maxlen=200)
        
        # Read stdout line by line WITHOUT storing in memory
        for line in iter(process.stdout.readline, ''):
            if not line:
                break
            line_count += 1
            log_tail.append(line.rstrip())
            
            # Update status container every 50 lines
            if line_count % 50 == 0:
                status_container.write(f"⏳ Processing... ({line_count} lines)")
        
        # Wait for process to finish
        process.stdout.close()
        returncode = process.wait(timeout=PROCESS_TIMEOUT)
        
        # Show completion info (even if 0 lines, step may have succeeded)
        if returncode == 0:
            if line_count > 0:
                status_container.success(f"✅ Complete! ({line_count} lines processed)")
            else:
                status_container.success("✅ Complete!")
        else:
            tail_text = "\n".join(log_tail) if log_tail else "No logs captured"
            raise RuntimeError(
                f"Processing failed with exit code {returncode}\n\nLast log lines:\n{tail_text}"
            )
        
        return line_count
            
    except subprocess.TimeoutExpired:
        process.kill()
        status_container.error("⏱️ Processing timed out")
        raise RuntimeError(f"Processing timed out after {PROCESS_TIMEOUT} seconds")
    except Exception as e:
        status_container.error(f"❌ Error: {str(e)}")
        raise RuntimeError(f"Error during processing: {str(e)}")
    
def find_stem(folder, keyword, extensions=None):
    if not folder.exists():
        return None
    if extensions is None:
        extensions = {".mp3", ".wav", ".flac", ".m4a", ".ogg"}
    keyword_lower = keyword.lower()
    candidates = []
    for file_path in folder.iterdir():
        if file_path.is_file() and file_path.suffix.lower() in extensions:
            if keyword_lower in file_path.name.lower():
                candidates.append(file_path)
    if candidates:
        return max(candidates, key=lambda p: p.stat().st_mtime)
    # Fallback: return newest audio file if keyword match failed
    audio_files = [
        p for p in folder.iterdir()
        if p.is_file() and p.suffix.lower() in extensions
    ]
    if not audio_files:
        return None
    return max(audio_files, key=lambda p: p.stat().st_mtime)


# ---------------- HEADER ----------------
st.title("🎤 AI Vocal Separator")
st.caption("MDX-Net pipeline · High-quality vocal extraction")

# ---------------- SIDEBAR ----------------
with st.sidebar:
    st.header("⚙️ Utilities")
    if st.button("🗑️ Clear all temp files"):
        shutil.rmtree(TEMP_DIR, ignore_errors=True)
        TEMP_DIR.mkdir(exist_ok=True)
        st.success("✅ All temp files cleared!")

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
    "MP3 or WAV file (Max 150MB)",
    type=["mp3", "wav"]
)

# Validate file size immediately
if uploaded:
    try:
        check_file_size(uploaded)
        st.success(f"✅ File size OK ({uploaded.size / (1024*1024):.1f}MB)")
    except ValueError as e:
        st.error(f"❌ {e}")
        uploaded = None

# ---------------- PRESETS ----------------
st.divider()
st.subheader("Choose a preset")

preset = st.radio(
    "Preset",
    ["Normal", "Heavy instrumental", "Noisy / live"],
    horizontal=True,
    label_visibility="collapsed"
)

if preset == "Normal":
    st.success("✅ Best balance — Recommended")
    ETA = "≈ 6 minutes"
    MAIN = {"seg": 512, "overlap": 0.5}
    HQ = {"seg": 256, "overlap": 0.25}

elif preset == "Heavy instrumental":
    st.warning("⏳ Slower — Strong music removal")
    ETA = "≈ 16 minutes"
    MAIN = {"seg": 640, "overlap": 0.6}
    HQ = {"seg": 256, "overlap": 0.3}

else:
    st.error("🐢 Very Slow — Best for noisy recordings")
    ETA = "≈ 26 minutes"
    MAIN = {"seg": 768, "overlap": 0.7}
    HQ = {"seg": 256, "overlap": 0.35}

st.caption(f"Estimated processing time: **{ETA}** (depends on CPU & song length)")

# ---------------- PROCESS ----------------
st.divider()

if uploaded and st.button("🎧 Extract Vocals"):
    try:
        job_id = uuid.uuid4().hex[:8]

        input_path = TEMP_DIR / f"{job_id}_{uploaded.name}"
        step1_dir = TEMP_DIR / f"step1_{job_id}"
        step2_dir = TEMP_DIR / f"step2_{job_id}"

        with open(input_path, "wb") as f:
            f.write(uploaded.read())

        # ---------- STEP 1 ----------
        st.subheader("Step 1 — Extracting vocals")
        
        with st.status("Running MDX Main…", expanded=False) as status1:
            cmd_step1 = [
                "audio-separator",
                "-m", "UVR_MDXNET_Main.onnx",
                "--mdx_segment_size", str(MAIN["seg"]),
                "--mdx_overlap", str(MAIN["overlap"]),
                "--output_format", "MP3",
                "--output_dir", str(step1_dir),
                str(input_path)
            ]

            run_with_logs(cmd_step1, status1, job_id)

        vocals_path = find_stem(step1_dir, "Vocals")
        if vocals_path is None:
            st.error("❌ Vocals file not found after Step 1. Please try again with a different audio file.")
            st.stop()

        # ---------- STEP 2 ----------
        st.subheader("Step 2 — Cleaning vocals")
        
        with st.status("Refining vocals…", expanded=False) as status2:
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

            run_with_logs(cmd_step2, status2, job_id)

        # ---------- OUTPUT ----------
        st.subheader("Your extracted vocals")
        final_vocals = find_stem(step2_dir, "Vocals")
        if final_vocals is None:
            st.error("❌ Final vocals file not found. Processing may have been interrupted.")
            # Debug: show what files ARE in the output directory
            if step2_dir.exists():
                files_found = list(step2_dir.iterdir())
                if files_found:
                    st.warning(f"Debug: Found {len(files_found)} file(s) in output folder:")
                    for f in files_found:
                        st.code(f.name)
                else:
                    st.warning("Debug: Output folder exists but is empty")
            else:
                st.warning("Debug: Output folder does not exist")
            st.stop()

        st.audio(final_vocals.read_bytes(), format="audio/mp3")
        st.download_button(
            "⬇ Download vocals",
            final_vocals.read_bytes(),
            file_name="vocals.mp3"
        )
        
        # Auto-cleanup temp files to save disk space
        st.divider()
        st.info("🧹 Cleaning up temporary files...")
        shutil.rmtree(step1_dir, ignore_errors=True)
        shutil.rmtree(step2_dir, ignore_errors=True)
        if input_path.exists():
            input_path.unlink(missing_ok=True)
        st.success("✅ Temp files cleaned up!")

    except RuntimeError as e:
        st.error(f"❌ Processing error: {e}")
    except Exception as e:
        st.error(f"❌ Unexpected error: {str(e)}")
        st.info("Please reload the page and try again.")
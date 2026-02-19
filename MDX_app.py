import streamlit as st
import subprocess
import uuid
import os
import shutil
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

# Store logs in session state to avoid widget re-renders
if 'current_logs' not in st.session_state:
    st.session_state.current_logs = {}

# ---------------- HELPERS ----------------
def run_with_logs(cmd, status_container, job_id):
    """Run subprocess and stream logs to status container without triggering reruns"""
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )

        logs = ""
        line_count = 0
        
        # Read stdout line by line
        while True:
            line = process.stdout.readline()
            if not line:
                break
            logs += line
            line_count += 1
            
            # Update status container every 10 lines (shows progress without reruns)
            if line_count % 10 == 0:
                status_container.write(f"📝 Processed {line_count} log lines...")
        
        # Wait for process to finish
        returncode = process.wait(timeout=PROCESS_TIMEOUT)
        
        # Get any remaining stderr
        stderr = process.stderr.read() if process.stderr else ""
        if stderr:
            logs += f"\n[STDERR]\n{stderr}"
        
        # Store in session state
        st.session_state.current_logs[job_id] = logs
        
        # Final status
        if returncode == 0:
            status_container.success(f"✅ Completed! ({line_count} log lines)")
        else:
            status_container.error(f"❌ Failed with exit code {returncode}")
            raise RuntimeError(f"Processing failed with exit code {returncode}\n\nLogs:\n{logs}")
        
        return logs
            
    except subprocess.TimeoutExpired:
        process.kill()
        status_container.error("⏱️ Processing timed out")
        raise RuntimeError(f"Processing timed out after {PROCESS_TIMEOUT} seconds")
    except Exception as e:
        status_container.error(f"❌ Error: {str(e)}")
        raise RuntimeError(f"Error during processing: {str(e)}")
    
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
    try:
        job_id = uuid.uuid4().hex[:8]

        input_path = TEMP_DIR / f"{job_id}_{uploaded.name}"
        step1_dir = TEMP_DIR / f"step1_{job_id}"
        step2_dir = TEMP_DIR / f"step2_{job_id}"

        with open(input_path, "wb") as f:
            f.write(uploaded.read())

        # ---------- STEP 1 ----------
        st.subheader("Step 1 — Extracting vocals")
        
        with st.status("Running MDX Main…", expanded=True) as status1:
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
        
        with st.status("Refining vocals…", expanded=True) as status2:
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
            st.stop()

        st.audio(final_vocals.read_bytes(), format="audio/mp3")
        st.download_button(
            "⬇ Download vocals",
            final_vocals.read_bytes(),
            file_name="vocals.mp3"
        )
        
        # Cleanup temp files after successful download (user can trigger manually)
        if st.button("🗑️ Clean up temp files"):
            try:
                if input_path.exists():
                    input_path.unlink()
                if step1_dir.exists():
                    shutil.rmtree(step1_dir)
                if step2_dir.exists():
                    shutil.rmtree(step2_dir)
                st.success("Temp files cleaned up!")
            except Exception as e:
                st.warning(f"Could not clean up all temp files: {e}")

    except RuntimeError as e:
        st.error(f"❌ Processing error: {e}")
    except Exception as e:
        st.error(f"❌ Unexpected error: {str(e)}")
        st.info("Please reload the page and try again.")
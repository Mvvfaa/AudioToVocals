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

# Store processing state in session
if "step1_vocals" not in st.session_state:
    st.session_state.step1_vocals = None
if "step1_dirs" not in st.session_state:
    st.session_state.step1_dirs = {}
if "show_step1_download" not in st.session_state:
    st.session_state.show_step1_download = False
if "proceed_step2" not in st.session_state:
    st.session_state.proceed_step2 = False
if "step2_done" not in st.session_state:
    st.session_state.step2_done = False
if "final_vocals" not in st.session_state:
    st.session_state.final_vocals = None
if "enable_step2" not in st.session_state:
    st.session_state.enable_step2 = False

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
            encoding="utf-8",
            errors="replace",
            bufsize=1,
            universal_newlines=True
        )

        line_count = 0
        log_tail = deque(maxlen=200)

        # Initial status message only (avoid frequent UI mutations on Streamlit Cloud)
        try:
            status_container.write("⏳ Processing...")
        except Exception:
            pass
        
        if process.stdout is None:
            raise RuntimeError("Failed to capture process output")

        # Read stdout line by line WITHOUT storing in memory
        for line in iter(process.stdout.readline, ''):
            if not line:
                break
            line_count += 1
            log_tail.append(line.rstrip())
            
            # Do not update UI repeatedly here; it can crash/restart app on Cloud
            pass
        
        # Wait for process to finish
        process.stdout.close()
        returncode = process.wait(timeout=PROCESS_TIMEOUT)
        
        # Show completion info (even if 0 lines, step may have succeeded)
        if returncode == 0:
            if line_count > 0:
                try:
                    status_container.write(f"✅ Complete! ({line_count} lines processed)")
                except Exception:
                    pass
            else:
                try:
                    status_container.write("✅ Complete!")
                except Exception:
                    pass
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
    st.session_state.enable_step2 = st.toggle(
        "Enable Step 2 refinement (high memory)",
        value=st.session_state.enable_step2,
        help="Turn on only if your environment can handle heavier processing."
    )
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
    HQ = {"seg": 128, "overlap": 0.1}

elif preset == "Heavy instrumental":
    st.warning("⏳ Slower — Strong music removal")
    ETA = "≈ 16 minutes"
    MAIN = {"seg": 640, "overlap": 0.6}
    HQ = {"seg": 128, "overlap": 0.1}

else:
    st.error("🐢 Very Slow — Best for noisy recordings")
    ETA = "≈ 26 minutes"
    MAIN = {"seg": 768, "overlap": 0.7}
    HQ = {"seg": 128, "overlap": 0.1}

st.caption(f"Estimated processing time: **{ETA}** (depends on CPU & song length)")

# ---------------- PROCESS ----------------
st.divider()

if uploaded and st.button("🎧 Extract Vocals"):
    try:
        st.session_state.proceed_step2 = False
        st.session_state.step2_done = False
        st.session_state.final_vocals = None

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

        # Save Step 1 results to session state for potential Step 2
        st.session_state.step1_vocals = str(vocals_path)
        st.session_state.step1_dirs = {"step1": str(step1_dir), "step2": str(step2_dir)}
        st.success("✅ Step 1 complete! Use the controls above to download or continue to Step 2.")
        st.rerun()

    except RuntimeError as e:
        st.error(f"❌ Processing error: {e}")
    except Exception as e:
        st.error(f"❌ Unexpected error: {str(e)}")
        st.info("Please reload the page and try again.")

# Show Step 1 actions below processing section
if st.session_state.step1_vocals:
    st.subheader("Step 1 — Ready to Download")
    st.info("You can download Step 1 vocals now, or continue to Step 2 refinement.")

    step1_path = Path(st.session_state.step1_vocals)
    if not step1_path.exists():
        st.warning("Step 1 vocals file is missing. Please run Step 1 again.")
    else:
        with open(step1_path, "rb") as step1_file:
            st.download_button(
                "⬇️ Download Step 1 Vocals",
                data=step1_file,
                file_name=step1_path.name,
                mime="audio/mpeg",
                key="download_step1_primary"
            )

    if st.button("▶️ Continue to Step 2 Refinement", key="continue_step2_primary"):
        if st.session_state.enable_step2:
            st.session_state.proceed_step2 = True
        else:
            st.warning("Step 2 is disabled in Cloud-safe mode. Enable it from the sidebar to proceed.")
            st.session_state.final_vocals = str(step1_path)
            st.session_state.step2_done = True

# Run Step 2 directly from the Continue button flow (without re-running Step 1)
if st.session_state.proceed_step2 and st.session_state.step1_vocals and not st.session_state.step2_done:
    try:
        step1_path = Path(st.session_state.step1_vocals)
        step2_dir = Path(st.session_state.step1_dirs.get("step2", TEMP_DIR / f"step2_{uuid.uuid4().hex[:8]}"))
        step2_dir.mkdir(parents=True, exist_ok=True)

        if not step1_path.exists():
            st.error("❌ Step 1 vocals file is missing. Please run Step 1 again.")
            st.session_state.proceed_step2 = False
            st.stop()

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
                str(step1_path)
            ]

            try:
                run_with_logs(cmd_step2, status2, "step2")
            except RuntimeError:
                st.warning("⚠️ Step 2 refinement failed, using Step 1 vocals instead.")

        final_vocals = find_stem(step2_dir, "Vocals")
        if final_vocals is None:
            final_vocals = step1_path

        st.session_state.final_vocals = str(final_vocals)
        st.session_state.step2_done = True
        st.session_state.proceed_step2 = False

    except RuntimeError as e:
        st.error(f"❌ Processing error: {e}")
        st.session_state.proceed_step2 = False
    except Exception as e:
        st.error(f"❌ Unexpected error: {str(e)}")
        st.session_state.proceed_step2 = False

# Render final output if available
if st.session_state.final_vocals:
    final_path = Path(st.session_state.final_vocals)
    if final_path.exists():
        st.subheader("Your extracted vocals")
        st.audio(str(final_path), format="audio/mp3")
        with open(final_path, "rb") as final_file:
            st.download_button(
                "⬇ Download vocals",
                data=final_file,
                file_name=final_path.name,
                mime="audio/mpeg"
            )
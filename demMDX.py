import subprocess

def run(cmd):
    subprocess.run(cmd, shell=True, check=True)

# 1. Demucs
run(
    "demucs -n htdemucs --two-stems vocals -o demucs_out AL.wav"
)

# 2. MDX cleanup
run(
    "audio-separator "
    "-m UVR_MDXNET_Main.onnx "
    "--single_stem Vocals "
    "--mdx_segment_size 256 "
    "--mdx_overlap 0.35 "
    "--mdx_enable_denoise "
    "--output_format WAV "
    "--output_dir final_vocals "
    "demucs_out/htdemucs/AL/vocals.wav"
)

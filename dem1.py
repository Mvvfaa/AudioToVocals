# import subprocess

# subprocess.run([
#     "demucs",
#     "-n", "htdemucs",
#     "AL.wav"
# ], check=True)

# print("Done! CLI-quality separation completed.")

import subprocess
import sys
from pathlib import Path

input_file = "AL.wav"
output_dir = Path("outputs")

output_dir.mkdir(exist_ok=True)

cmd = [
    sys.executable,
    "-m", "demucs",
    "-n", "htdemucs",
    "-o", str(output_dir),
    input_file
]

print("Running Demucs...")
subprocess.run(cmd, check=True)
print("Done! ^_^")

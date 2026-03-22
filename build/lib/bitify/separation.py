import os
import subprocess
import logging
import tempfile

from .utils import get_venv_bin


def separate_audio(input_file):
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Input file not found: {input_file}")

    working_dir = tempfile.mkdtemp(prefix="8bitify_demucs_")

    # Prefer the venv-managed demucs; fall back to PATH for edge cases
    demucs_bin = get_venv_bin("demucs")
    if not os.path.exists(demucs_bin):
        import shutil
        demucs_bin = shutil.which("demucs")
        if not demucs_bin:
            raise RuntimeError(
                "demucs not found. Run '8bitify' once to trigger the setup, "
                "or check ~/.8bitify/venv."
            )

    cmd = [demucs_bin, input_file, "-o", working_dir]
    logging.info(f"Running separation command: {' '.join(cmd)}")
    subprocess.check_call(cmd)

    stems = {}
    for root, _, files in os.walk(working_dir):
        for f in files:
            for stem_type in ["vocals", "drums", "bass", "other"]:
                if f.startswith(stem_type) and f.endswith(".wav"):
                    stems[stem_type] = os.path.join(root, f)

    for expected in ["vocals", "drums", "bass", "other"]:
        if expected not in stems:
            raise RuntimeError(f"Separation failed: missing stem {expected}.wav")
        fs = os.path.getsize(stems[expected])
        if fs < 10240:
            raise RuntimeError(
                f"Separation failed: {expected} stem is too small ({fs} bytes)"
            )

    return stems

import os
import tempfile
import click
import numpy as np
from pydub import AudioSegment
from .processor import process_stem
from .mixer import mix_stems

def generate_test_tone(duration_ms=1000, hz=440):
    sample_rate = 44100
    t = np.linspace(0, duration_ms/1000, int(sample_rate * (duration_ms/1000)), False)
    tone = np.sin(hz * t * 2 * np.pi)
    
    audio = np.int16(tone * 32767)
    seg = AudioSegment(
        audio.tobytes(),
        frame_rate=sample_rate,
        sample_width=2,
        channels=1
    )
    return seg

def run_pipeline_check():
    click.echo("Running Self-Health Check on Bitify Engine...")
    
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            stems = {}
            for stem_type in ["vocals", "drums", "bass", "other"]:
                path = os.path.join(tmpdir, f"{stem_type}.wav")
                generate_test_tone().export(path, format="wav")
                stems[stem_type] = path
                
            processed = {}
            for stem_type, path in stems.items():
                processed[stem_type] = process_stem(path, stem_type)
                
            output_path = os.path.join(tmpdir, "output.mp3")
            mix_stems(processed, output_path)
            
            if os.path.exists(output_path):
                click.echo("✅ Pipeline check passed successfully.")
                return True
            else:
                click.echo("❌ Pipeline check failed: Output not generated.")
                return False
    except Exception as e:
        from .utils import print_agent_error_report
        print_agent_error_report(e, "Self-Health Check")
        return False

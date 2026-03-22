import os
import shutil
import click
from .separation import separate_audio
from .processor import process_stem
from .mixer import mix_stems
from .utils import check_and_install_demucs, print_agent_error_report

def run_hq_pipeline(input_path, output_path=None):
    if output_path is None:
        base, ext = os.path.splitext(input_path)
        output_path = f"{base}_hq_8bit.mp3"

    try:
        click.echo("[1/4] 🎵 Initializing High-Quality Pipeline...")
        if not check_and_install_demucs():
            return None

        click.echo("[2/4] ✂️  Separating audio stems with AI (this may take a minute)...")
        stems_dict = separate_audio(input_path)
        
        click.echo("\n[3/4] 🎛️  Applying 8-bit DSP to individual instruments...")
        processed = {}
        for stem_type, path in stems_dict.items():
            click.echo(f"      -> Processing {stem_type.upper()} stem...")
            processed[stem_type] = process_stem(path, stem_type)
            click.echo(f"         Done with {stem_type}.")
            
        click.echo("\n[4/4] 🎚️  Mixing final chiptune track...")
        from pydub import AudioSegment as _AS
        _src_duration_ms = len(_AS.from_file(input_path))
        result = mix_stems(processed, output_path, source_duration_ms=_src_duration_ms)
        
        # Cleanup
        try:
            temp_root = os.path.dirname(os.path.dirname(os.path.dirname(stems_dict["drums"])))
            if "8bitify_demucs_" in temp_root:
                shutil.rmtree(temp_root, ignore_errors=True)
        except Exception as e:
            pass # ignore cleanup errors
            
        return result
    except Exception as e:
        print_agent_error_report(e, "High-Quality Pipeline")
        return None

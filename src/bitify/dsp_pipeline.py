"""
Simple DSP-only Pipeline
========================
Fast, deterministic, no AI. Just pure audio transformation.
"""

import os
import click
from .dsp_processor import process_audio_dsp
from .utils import print_agent_error_report


def run_dsp_pipeline(input_path, output_path=None):
    """Run the simple DSP pipeline without AI separation."""
    if output_path is None:
        base, ext = os.path.splitext(input_path)
        output_path = f"{base}_8bit.mp3"

    try:
        click.echo("[1/1] 🎛️  Applying DSP effects...")
        result = process_audio_dsp(input_path, output_path)
        click.echo("      Done!")
        return result

    except Exception as e:
        print_agent_error_report(e, "DSP Pipeline")
        return None

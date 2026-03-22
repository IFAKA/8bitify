"""
Simple Honest Pipeline
======================
Detect what's actually there, synthesize only high-confidence pitches.
"""

import os
import click
from .synth_processor import process_with_honest_synthesis
from .utils import print_agent_error_report


def run_simple_pipeline(input_path, output_path=None):
    """Run honest synthesis pipeline."""
    if output_path is None:
        base, ext = os.path.splitext(input_path)
        output_path = f"{base}_8bit.mp3"

    try:
        click.echo("[1/1] 🎛️  Detecting & synthesizing...")
        result = process_with_honest_synthesis(input_path, output_path)
        click.echo("      Done!")
        return result

    except Exception as e:
        print_agent_error_report(e, "Synthesis Pipeline")
        return None

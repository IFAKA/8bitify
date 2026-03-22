import os
import sys

# Python 3.13+ compatibility shim for pydub
try:
    import audioop
except ImportError:
    try:
        import audioop_lts
        sys.modules['audioop'] = audioop_lts
        sys.modules['pyaudioop'] = audioop_lts
    except ImportError:
        pass

import click
from iterfzf import iterfzf
from .converter import convert_to_8bit

IGNORE_DIRS = {
    '.git', 'node_modules', 'venv', '__pycache__', '.idea', '.vscode', 'dist', 'build', 'target', '.gemini'
}

AUDIO_EXTENSIONS = {'.mp3', '.wav', '.flac', '.ogg', '.m4a'}

def find_audio_files(root_dir='.'):
    for root, dirs, files in os.walk(root_dir):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext in AUDIO_EXTENSIONS:
                yield os.path.relpath(os.path.join(root, file), root_dir)

@click.command()
@click.argument('input_file', required=False, type=click.Path(exists=True))
@click.option('--output', '-o', help='Output file path.')
@click.option('--check-pipeline', is_flag=True, help='Run a self-health check on the pipeline.')
def main(input_file, output, check_pipeline):
    """
    Converts an audio file to an authentic 8-bit chiptune.

    Run without arguments to pick a file with the fuzzy finder.
    """
    if check_pipeline:
        from .health import run_pipeline_check
        run_pipeline_check()
        return

    file_to_convert = input_file

    if not file_to_convert:
        click.echo("Scanning for audio files...")
        files = list(find_audio_files())

        if not files:
            click.echo("No audio files found in current directory.")
            return

        try:
            selection = iterfzf(files, prompt="Select a track > ")
        except Exception as e:
            click.echo(f"Error launching selection menu: {e}")
            return

        if not selection:
            click.echo("No file selected.")
            return

        file_to_convert = selection

    click.echo(f"Processing: {file_to_convert}")

    try:
        out = convert_to_8bit(file_to_convert, output)

        if out:
            click.echo(f"Success! Saved to: {out}")
            from .validator import validate, print_report
            click.echo("\n📊 Measuring chiptune authenticity...")
            out_report = validate(out)
            print_report(out_report)
        else:
            click.echo("Conversion failed.")

    except Exception as e:
        from .utils import print_agent_error_report
        print_agent_error_report(e, "Main CLI")
        if "ffmpeg" in str(e).lower() or "ffprobe" in str(e).lower():
            click.echo("\nTip: Ensure 'ffmpeg' is installed and in your PATH.")
            click.echo("MacOS: brew install ffmpeg")
            click.echo("Ubuntu: sudo apt install ffmpeg")

if __name__ == '__main__':
    main()

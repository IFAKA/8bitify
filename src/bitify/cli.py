import os
import sys

# Python 3.13 compatibility shim for pydub
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
    """
    Generator that yields audio files in the current directory and subdirectories,
    skipping ignored directories.
    """
    for root, dirs, files in os.walk(root_dir):
        # Modify dirs in-place to skip ignored directories
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext in AUDIO_EXTENSIONS:
                # Yield relative path for better UX in list
                yield os.path.relpath(os.path.join(root, file), root_dir)

@click.command()
@click.argument('input_file', required=False, type=click.Path(exists=True))
@click.option('--output', '-o', help='Output file path.')
def main(input_file, output):
    """
    Converts audio files to an 8-bit chiptune style.
    
    If INPUT_FILE is provided, converts that file.
    If not provided, opens a fuzzy finder to select a file from the current directory.
    """
    
    # Check for ffmpeg (basic check)
    # pydub usually warns, but we can do a quick shutil check if we want.
    # We'll rely on pydub's error handling for now but wrap the call.

    file_to_convert = input_file

    if not file_to_convert:
        # Fuzzy finder mode
        click.echo("Scanning for audio files...")
        files = list(find_audio_files())
        
        if not files:
            click.echo("No audio files found in current directory.")
            return

        try:
            # simple iterfzf call
            selection = iterfzf(files, prompt="Select a track > ")
        except Exception as e:
            # Fallback or error if fzf binary is missing/fails
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
        else:
            click.echo("Conversion failed.")
    except Exception as e:
        click.echo(f"An error occurred: {e}")
        # Check if it might be ffmpeg related
        if "ffmpeg" in str(e).lower() or "ffprobe" in str(e).lower():
            click.echo("\nTip: Ensure 'ffmpeg' is installed and in your PATH.")
            click.echo("MacOS: brew install ffmpeg")
            click.echo("Ubuntu: sudo apt install ffmpeg")

if __name__ == '__main__':
    main()

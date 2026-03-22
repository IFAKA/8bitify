# 8bitify

A simple CLI tool to convert MP3 files into 8-bit chiptune-style audio.

## Features
- **One-Command Conversion:** `8bitify song.mp3`
- **Interactive Mode:** Run `8bitify` without arguments to select a file using a fuzzy finder.
- **Batch Processing:** (Coming soon, currently single file)
- **Automatic filtering:** Ignores non-audio files and system directories.

## Installation

### Prerequisites
- Python 3.8+
- `ffmpeg` (Required for audio processing)
  - macOS: `brew install ffmpeg`
  - Ubuntu: `sudo apt install ffmpeg`
  - Windows: Download from ffmpeg.org and add to PATH.

### Install

```bash
pip install .
```

(Or simpler if you publish to PyPI later: `pip install 8bitify`)

## Usage

**Convert a specific file:**
```bash
8bitify my_song.mp3
```

**Interactive Selection:**
```bash
8bitify
```
(Opens a fuzzy finder list of all audio files in the current directory)

## Uninstallation

```bash
pip uninstall 8bitify
```

## How it works
It uses `pydub` and `numpy` to:
1. Downsample audio to 8000Hz (Gameboy-style sample rate).
2. Convert to Mono.
3. Apply bit-depth reduction (quantization) to simulate 8-bit dynamic range.

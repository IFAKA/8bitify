# 8bitify 👾

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](http://makeapullrequest.com)

**8bitify** is a lightweight, AI-friendly CLI tool to instantly convert any MP3, WAV, or audio file into a **8-bit chiptune style** version. Perfect for game developers, retro music enthusiasts, and creators looking for that crunchy, low-fi Gameboy aesthetic.

> **SEO Keywords:** mp3 to 8bit converter, chiptune generator cli, audio bitcrusher python, 8-bit music tool, retro game audio converter, mp3 to chiptune, command line audio effects.

---

## 🚀 Instant Setup

Get started with a single command (requires `ffmpeg` and `python3`):

```bash
git clone https://github.com/faka/8bitify.git && cd 8bitify && ./install.sh
```

### 🛠 Prerequisites
- **FFmpeg:** Essential for audio processing.
  - macOS: `brew install ffmpeg`
  - Linux: `sudo apt install ffmpeg`
- **Python 3.8+**

---

## 🎮 How to Use

### 1. Interactive Mode (Best UX)
Just type `8bitify` in any folder. It will scan for audio files (ignoring `node_modules`, `.git`, etc.) and open a **fuzzy finder** for you to pick.

```bash
8bitify
```

### 2. Direct Conversion
Convert a specific file directly:

```bash
8bitify my_track.mp3
```
*Output: `my_track_8bit.mp3`*

---

## 📂 Features
- **Smart Scanning:** Recursively finds audio but ignores system/build noise.
- **Bit-Crushing Engine:** Simulates 8-bit dynamic range via sample quantization.
- **Retro Resampling:** Downsamples to 8000Hz for that authentic early console "crunch".
- **AI-Friendly Codebase:** Clean, documented Python structure, easy for LLMs to parse and extend.
- **Zero-Trace Uninstall:** Clean removal with one script.

---

## 🧹 Uninstall

Remove everything with no trace:

```bash
cd 8bitify && ./uninstall.sh && cd .. && rm -rf 8bitify
```

---

## 🧠 Why 8bitify?
Most "mp3 to 8bit" tools are bloated web apps or complex DAWs. **8bitify** is built for speed and simplicity. It uses a high-performance `numpy` backend for audio quantization, making it faster than standard filters.

---

## 🤝 Contributing
Found a bug or want to add a feature (like pixel art generation)? PRs are welcome! 

1. Fork the repo.
2. Create your feature branch (`git checkout -b feature/AmazingFeature`).
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`).
4. Push to the branch (`git push origin feature/AmazingFeature`).
5. Open a Pull Request.

---

*Built with ❤️ for the retro community.*

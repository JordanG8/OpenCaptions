# OpenCaptions - AI Hebrew Captions for Premiere Pro

<p align="center">
  <a href="https://github.com/JordanG8/OpenCaptions/releases/latest/download/OpenCaptions-Setup-1.0.0.exe">
    <img src="https://img.shields.io/badge/Download_for_Windows-0078D4?style=for-the-badge&logo=windows&logoColor=white" alt="Download for Windows" height="60">
  </a>
</p>

<p align="center">
  <em>One-click installer. Python and FFmpeg included — nothing else to install.</em>
</p>

---

**OpenCaptions** generates accurate, time-synced Hebrew subtitles directly on your Premiere Pro timeline using AI. Everything runs **100% offline** — no data leaves your computer.

## Features
- **Hebrew AI transcription** with word-level timestamps
- **RTL punctuation fix** — corrects `?!.` jumping to the wrong side
- **One-click timeline placement** — imports and places SRT automatically
- **GPU accelerated** — NVIDIA (CUDA), AMD (DirectML), and Intel GPUs supported
- **Track selection** — choose which audio track to transcribe
- **100% local & private** — no cloud APIs, no subscriptions
- **Self-contained** — Python and FFmpeg are bundled, no manual setup

## What the installer does

The Windows installer automatically:
1. Copies the extension (with bundled Python + FFmpeg) to your Adobe CEP extensions folder
2. Sets the required registry keys (PlayerDebugMode)
3. Installs the correct AI packages for your GPU (requires internet on first install)
4. Downloads the AI model (~1-2 GB, one-time)

After install, restart Premiere Pro and go to **Window > Extensions > OpenCaptions**.

## GPU Support

| GPU | Backend | Speed |
|-----|---------|-------|
| NVIDIA (GTX/RTX) | faster-whisper + CUDA | Fastest |
| AMD (Radeon) | openai-whisper + DirectML | Fast |
| Intel (Arc) | openai-whisper + DirectML | Fast |
| CPU fallback | faster-whisper int8 | Slower |

The extension auto-detects your GPU and uses the best available backend.

## Prerequisites

- **Adobe Premiere Pro 2020+**
- **Internet connection** (first install only — for AI packages and model download)

That's it. Python and FFmpeg are bundled in the installer.

## Manual Install (advanced)

If you prefer not to use the installer:

```bash
# 1. Copy extension to CEP folder
xcopy /E /I com.opencaptions.hebrewcaptions "%AppData%\Adobe\CEP\extensions\com.opencaptions.hebrewcaptions"

# 2. Enable debug mode (run as admin)
com.opencaptions.hebrewcaptions\enable-debug-mode.bat

# 3. Install dependencies (requires Python 3.10+ and FFmpeg on PATH)
cd com.opencaptions.hebrewcaptions/python
python install_deps.py
python download_model.py

# 4. Restart Premiere Pro > Window > Extensions > OpenCaptions
```

## Building the installer

Requires [Inno Setup](https://jrsoftware.org/isinfo.php) (free) and Python 3.10+.

```bash
# Downloads bundled Python + FFmpeg, then compiles the installer
python installer/build_installer.py
# Output: installer/Output/OpenCaptions-Setup-1.0.0.exe
```

## License

MIT License — see [LICENSE](LICENSE)

---

<p align="center"><sub>Made by Jordan Goren & Claude</sub></p>

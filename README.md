# Free KAPS - AI Hebrew Captions for Premiere Pro

<p align="center">
  <a href="https://github.com/JordanG8/OpenCaptions/releases/latest/download/FreeKAPS-Setup-1.0.0.exe">
    <img src="https://img.shields.io/badge/Download_for_Windows-0078D4?style=for-the-badge&logo=windows&logoColor=white" alt="Download for Windows" height="60">
  </a>
</p>

<p align="center">
  <em>One-click installer. No terminal needed.</em><br>
  <sub>Requires Python 3.10+ and FFmpeg on PATH</sub>
</p>

---

**Free KAPS** generates accurate, time-synced Hebrew subtitles directly on your Premiere Pro timeline using AI. Everything runs **100% offline** — no data leaves your computer.

## Features
- **Hebrew AI transcription** with word-level timestamps
- **RTL punctuation fix** — corrects `?!.` jumping to the wrong side
- **One-click timeline placement** — imports and places SRT automatically
- **GPU accelerated** — NVIDIA (CUDA), AMD (DirectML), and Intel GPUs supported
- **Track selection** — choose which audio track to transcribe
- **100% local & private** — no cloud APIs, no subscriptions

## What the installer does

The Windows installer automatically:
1. Copies the extension to your Adobe CEP extensions folder
2. Sets the required registry keys (PlayerDebugMode)
3. Installs the correct Python packages for your GPU
4. Downloads the AI model (~1-2 GB, one-time)

After install, restart Premiere Pro and go to **Window > Extensions > Free KAPS**.

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
- **Python 3.10+** — [Download](https://www.python.org/downloads/) (check "Add to PATH" during install)
- **FFmpeg** — [Download](https://ffmpeg.org/download.html) (add to system PATH)

## Manual Install (advanced)

If you prefer not to use the installer:

```bash
# 1. Copy extension to CEP folder
xcopy /E /I com.freekaps.hebrewcaptions "%AppData%\Adobe\CEP\extensions\com.freekaps.hebrewcaptions"

# 2. Enable debug mode (run as admin)
com.freekaps.hebrewcaptions\enable-debug-mode.bat

# 3. Install dependencies
cd com.freekaps.hebrewcaptions/python
python install_deps.py
python download_model.py

# 4. Restart Premiere Pro → Window > Extensions > Free KAPS
```

## Building the installer

Requires [Inno Setup](https://jrsoftware.org/isinfo.php) (free).

```bash
# Open installer/freekaps-installer.iss in Inno Setup Compiler
# Click Build > Compile (Ctrl+F9)
# Output: installer/Output/FreeKAPS-Setup-1.0.0.exe
```

Or from command line:
```bash
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer/freekaps-installer.iss
```

## License

MIT License — see [LICENSE](LICENSE)

---

<p align="center"><sub>Made by Jordan Goren & Claude</sub></p>

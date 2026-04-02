# OpenCaptions - AI Hebrew Captions for Premiere Pro

<p align="center">
  <a href="https://github.com/JordanG8/OpenCaptions/releases/latest/download/OpenCaptions-Setup-1.2.0.exe">
    <img src="https://img.shields.io/badge/Download_for_Windows-0078D4?style=for-the-badge&logo=windows&logoColor=white" alt="Download for Windows" height="60">
  </a>
</p>

<p align="center">
  <em>One-click installer. Python, FFmpeg, and AI model included — fully offline, nothing else to install.</em>
</p>

> **Important:** Right-click the installer and select **"Run as Administrator"**. This is required because the installer sets Adobe registry keys to enable the extension. Windows Defender may also show a SmartScreen warning since the installer is not code-signed — click **"More info" → "Run anyway"** to proceed. The installer is open-source and safe.

---

**OpenCaptions** generates accurate, time-synced Hebrew subtitles directly on your Premiere Pro timeline using AI. Everything runs **100% offline** — no data leaves your computer.

## Features
- **Hebrew AI transcription** powered by [ivrit-ai](https://huggingface.co/ivrit-ai) (state-of-the-art Hebrew model, trained on 5,050 hours of Hebrew speech)
- **RTL punctuation fix** — corrects `?!.` jumping to the wrong side
- **One-click timeline placement** — imports and places SRT automatically
- **GPU accelerated** — NVIDIA (CUDA), AMD (DirectML), and Intel GPUs supported
- **Track selection** — choose which audio track to transcribe
- **100% local & private** — no cloud APIs, no subscriptions
- **Self-contained** — Python and FFmpeg are bundled, no manual setup

## What the installer does

The Windows installer automatically:
1. Copies the extension (with bundled Python, FFmpeg, and AI model) to your Adobe CEP extensions folder
2. Sets the required registry keys (PlayerDebugMode) — **this is why admin is needed**
3. Installs the correct GPU packages for your hardware (requires internet on first install)

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
- **Internet connection** (first install only — for GPU-specific packages)

That's it. Python, FFmpeg, and the AI model are bundled in the installer.

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
# Downloads bundled Python + FFmpeg + AI model, then compiles the installer
python installer/build_installer.py
# Output: installer/Output/OpenCaptions-Setup-1.2.0.exe
```

## License

MIT License — see [LICENSE](LICENSE)

---

<p align="center"><sub>Made by Jordan Goren & Claude</sub></p>

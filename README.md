# Free KAPS - כתוביות חכמות בעברית

**Free KAPS** is an AI-powered Hebrew captioning extension for Adobe Premiere Pro. It generates accurate, time-synced Hebrew subtitles directly on your timeline.

Everything runs **100% offline** on your local machine. No data leaves your computer.

## Key Features
- **Hebrew AI transcription** with word-level timestamps
- **RTL punctuation fix** — corrects `?!.` jumping to the wrong side
- **One-click timeline placement** — imports and places SRT automatically
- **GPU accelerated** — NVIDIA (CUDA), AMD (DirectML), and Intel GPUs supported
- **100% local & private** — no cloud APIs, no subscriptions

---

## Quick Start

### 1. Enable debug mode (one-time)
**Windows:** Right-click `enable-debug-mode.bat` → Run as Administrator

**Mac:**
```bash
defaults write com.adobe.CSXS.11 PlayerDebugMode 1
defaults write com.adobe.CSXS.12 PlayerDebugMode 1
```

### 2. Copy to extensions folder
Place the `com.freekaps.hebrewcaptions` folder into:
- **Windows:** `%AppData%\Adobe\CEP\extensions\`
- **Mac:** `~/Library/Application Support/Adobe/CEP/extensions/`

### 3. Install dependencies
Requires **Python 3.10+** and **FFmpeg** on your PATH.

```bash
cd com.freekaps.hebrewcaptions/python
python install_deps.py   # auto-detects GPU, installs correct packages
python download_model.py  # downloads AI model (~1-2 GB, one-time)
```

Or use the all-in-one setup (creates a virtual environment):
```bash
python setup_env.py
```

### 4. Use it
1. Restart Premiere Pro
2. **Window > Extensions > Free KAPS**
3. Select audio track, click **"צור כתוביות (AI)"**

---

## GPU Support

| GPU | Backend | Speed |
|-----|---------|-------|
| NVIDIA (GTX/RTX) | faster-whisper + CUDA | Fastest |
| AMD (Radeon) | openai-whisper + DirectML | Fast |
| Intel (Arc) | openai-whisper + DirectML | Fast |
| CPU fallback | faster-whisper int8 | Slower |

The extension auto-detects your GPU and uses the best available backend.

---

## Requirements
- Adobe Premiere Pro 2020 or newer
- Python 3.10+
- FFmpeg (on system PATH)

---

## License
MIT License - see [LICENSE](LICENSE)

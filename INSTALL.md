# OpenCaptions — Installation Guide

## Folder Structure

```
com.opencaptions.hebrewcaptions/
├── .debug                  <- CEP debug config (port 7737)
├── enable-debug-mode.bat   <- Windows helper script
├── CSXS/
│   └── manifest.xml        <- Extension manifest
├── client/
│   ├── index.html          <- Panel UI
│   ├── main.js             <- Node.js bridge (spawns Python)
│   └── CSInterface.js      <- Adobe CSInterface library
├── host/
│   └── host.jsx            <- ExtendScript (Premiere automation)
└── python/
    ├── transcriber.py      <- AI transcription engine (multi-GPU)
    ├── install_deps.py     <- Auto GPU detection & package installer
    ├── download_model.py   <- Pre-downloads AI models
    ├── setup_env.py        <- All-in-one venv setup
    └── requirements.txt
```

---

## Step 1: Enable Unsigned CEP Extensions (Debug Mode)

Adobe requires this for unsigned extensions. You only need to do this once.

### Windows

**Option A (easy):** Right-click `enable-debug-mode.bat` and select **Run as Administrator**.

**Option B (manual):** Open Command Prompt as Administrator:
```cmd
reg add "HKCU\SOFTWARE\Adobe\CSXS.11" /v PlayerDebugMode /t REG_SZ /d 1 /f
reg add "HKCU\SOFTWARE\Adobe\CSXS.12" /v PlayerDebugMode /t REG_SZ /d 1 /f
```

### Mac

Open Terminal:
```bash
defaults write com.adobe.CSXS.11 PlayerDebugMode 1
defaults write com.adobe.CSXS.12 PlayerDebugMode 1
```

---

## Step 2: Place the Extension Folder

Copy the **entire** `com.opencaptions.hebrewcaptions` folder to:

### Windows
```
C:\Users\<YOUR_USERNAME>\AppData\Roaming\Adobe\CEP\extensions\
```
If the `CEP\extensions\` folder doesn't exist, create it.

### Mac
```
~/Library/Application Support/Adobe/CEP/extensions/
```

---

## Step 3: Install Python Dependencies

### 3a. Install Python 3.10+

Download from https://www.python.org/downloads/ if you don't have it.
Make sure `python` is on your PATH.

### 3b. Install packages (auto GPU detection)

```bash
cd com.opencaptions.hebrewcaptions/python
python install_deps.py
```

This auto-detects your GPU (NVIDIA, AMD, or Intel) and installs the correct packages:
- **NVIDIA:** `faster-whisper` + CUDA libraries
- **AMD/Intel:** `openai-whisper` + `torch-directml`
- **No GPU:** `faster-whisper` CPU mode

You can also force a specific backend:
```bash
python install_deps.py nvidia   # force NVIDIA packages
python install_deps.py amd      # force DirectML packages
python install_deps.py cpu      # force CPU-only
```

### 3c. FFmpeg

`faster-whisper` needs FFmpeg to decode audio files.

**Windows:**
```bash
winget install Gyan.FFmpeg
# or: choco install ffmpeg
```

**Mac:**
```bash
brew install ffmpeg
```

Make sure `ffmpeg` is on your system PATH.

---

## Step 4: Download the AI Model (One-Time)

```bash
cd com.opencaptions.hebrewcaptions/python
python download_model.py
```

This downloads the Whisper medium model (~1-2 GB) and caches it locally.
After this, everything runs 100% offline.

---

## Alternative: All-in-One Setup

Instead of steps 3b-4, you can run the all-in-one script which creates a
virtual environment, installs everything, and downloads the model:

```bash
cd com.opencaptions.hebrewcaptions/python
python setup_env.py
```

---

## Step 5: Launch Premiere Pro

1. Open (or restart) **Adobe Premiere Pro**
2. Go to **Window > Extensions > OpenCaptions**
3. The panel should appear with a "Generate Captions" button
4. Open a sequence, select your audio track, click the button

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Panel doesn't appear in Extensions menu | Check the registry key (Step 1) and restart Premiere |
| "No active sequence" | Open a sequence in the timeline before clicking |
| Python not found | Make sure `python` is on your system PATH |
| Model download fails | Check internet connection; run `download_model.py` again |
| CUDA DLL error (NVIDIA) | Run `python install_deps.py nvidia` to reinstall CUDA packages |
| Slow transcription | Run `python install_deps.py` to check GPU setup |
| SRT not importing | Check that the file was created in your temp folder |

---

## How It Works

1. **Click "Generate Captions"** in the panel
2. ExtendScript exports the active sequence audio as a `.wav` file
3. Node.js spawns the Python transcriber
4. The AI model transcribes Hebrew speech and generates `.srt` with word-level timestamps
5. ExtendScript imports the `.srt` into the project and places it on the timeline

The transcriber auto-detects your GPU and uses the fastest available backend (CUDA > DirectML > CPU).

"""
download_model.py — Pre-download Whisper models so they're cached locally.

Usage:
    python download_model.py

Downloads:
  - ivrit-ai/whisper-large-v3-turbo-ct2 (Hebrew-optimized, for NVIDIA CUDA + CPU backends)
  - openai-whisper medium model (for DirectML backend, if packages installed)
"""

import os
import sys
import shutil
import time

sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)


def set_title(title):
    if sys.platform == "win32":
        os.system(f"title {title}")


def disk_stats():
    try:
        usage = shutil.disk_usage(os.path.expanduser("~"))
        free_gb = usage.free / (1024 ** 3)
        return f"{free_gb:.1f} GB free"
    except Exception:
        return "unknown"


set_title("OpenCaptions — Downloading AI model")
print()
print("  " + "="*56)
print("    OpenCaptions — Model Downloader")
print("  " + "="*56)
print(f"  Disk: {disk_stats()}")

success = False

# 1. faster-whisper ivrit-ai model (always available)
try:
    from faster_whisper import WhisperModel
    print("\n  Downloading ivrit-ai/whisper-large-v3-turbo-ct2 model...")
    print("  This is a Hebrew-optimized model (~1.6 GB, first run only)...\n")
    start = time.time()
    model = WhisperModel("ivrit-ai/whisper-large-v3-turbo-ct2", device="cpu", compute_type="int8")
    del model
    elapsed = time.time() - start
    print(f"\n  ivrit-ai model cached in {elapsed:.0f}s — Disk: {disk_stats()}")
    success = True
except Exception as e:
    print(f"  ivrit-ai model download failed: {e}")

# 2. openai-whisper model (only if installed — for DirectML backend)
try:
    import whisper
    print("\n  Downloading openai-whisper 'medium' model...")
    print("  This may take several minutes on first run...\n")
    start = time.time()
    model = whisper.load_model("medium", device="cpu")
    del model
    elapsed = time.time() - start
    print(f"\n  openai-whisper model cached in {elapsed:.0f}s — Disk: {disk_stats()}")
    success = True
except ImportError:
    print("\n  openai-whisper not installed — skipping DirectML model download.")
except Exception as e:
    print(f"  openai-whisper model download failed: {e}")

print()
print("  " + "="*56)
if not success:
    print("  ERROR: No AI models were downloaded!")
    sys.exit(1)

print(f"  Done! Disk: {disk_stats()}")
print("  You can now use the OpenCaptions plugin in Premiere Pro.")
print("  " + "="*56)
print()

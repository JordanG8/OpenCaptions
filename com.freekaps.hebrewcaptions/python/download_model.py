"""
download_model.py — Pre-download Whisper models so they're cached locally.

Usage:
    python download_model.py

Downloads both:
  - faster-whisper medium model (for NVIDIA CUDA + CPU backends)
  - openai-whisper medium model (for DirectML backend, if packages installed)
"""

print("Free KAPS — Model Downloader")
print("=" * 50)

# 1. faster-whisper model (always available)
try:
    from faster_whisper import WhisperModel
    print("\nDownloading faster-whisper 'medium' model...")
    print("This may take several minutes on first run...\n")
    model = WhisperModel("medium", device="cpu", compute_type="int8")
    del model
    print("faster-whisper model cached successfully!")
except Exception as e:
    print(f"faster-whisper model download skipped: {e}")

# 2. openai-whisper model (only if installed — for DirectML backend)
try:
    import whisper
    print("\nDownloading openai-whisper 'medium' model...")
    print("This may take several minutes on first run...\n")
    model = whisper.load_model("medium", device="cpu")
    del model
    print("openai-whisper model cached successfully!")
except ImportError:
    print("\nopenai-whisper not installed — skipping DirectML model download.")
    print("(Run 'python install_deps.py' if you have an AMD/Intel GPU)")
except Exception as e:
    print(f"openai-whisper model download skipped: {e}")

print("\n" + "=" * 50)
print("Done! You can now use the Free KAPS plugin in Premiere Pro.")

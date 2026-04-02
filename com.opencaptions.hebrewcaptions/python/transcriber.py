"""
transcriber.py — Multi-backend GPU-accelerated Hebrew transcription.

Backends (tried in priority order):
  1. NVIDIA CUDA  — faster-whisper + CTranslate2 (fastest)
  2. DirectML     — openai-whisper + torch-directml (AMD / Intel / any DX12 GPU)
  3. CPU          — faster-whisper int8 (last resort)

Usage:  python transcriber.py <input.wav> <output.srt> [max_words] [do_rtl_fix]

Progress protocol (parsed by main.js):
  @@DURATION:<seconds>      — total audio length
  @@BACKEND:<name>          — which backend is active
  @@MODEL_LOADING           — model is loading into memory
  @@MODEL_READY             — model loaded, transcription starting
  @@SEG:<end_sec>|<text>    — a segment was transcribed (for live preview + progress)
  @@WRITING_SRT             — writing SRT file
  @@DONE                    — all finished
"""

import sys
import os
import time
import re
import subprocess
import json

# Ensure UTF-8 output
sys.stdout.reconfigure(encoding='utf-8')


# ── Model Resolution ─────────────────────────────────────────

def _resolve_model(hf_model_id):
    """Return local bundled model path if it exists, otherwise the HuggingFace model ID."""
    # Check for model bundled by the installer (vendor/models/<model-name>/)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    ext_dir = os.path.dirname(script_dir)
    local_path = os.path.join(ext_dir, "vendor", "models", hf_model_id.replace("/", "--"))
    if os.path.isdir(local_path) and os.path.exists(os.path.join(local_path, "model.bin")):
        print(f"Using bundled model: {local_path}", flush=True)
        return local_path
    return hf_model_id


# ── GPU Detection ─────────────────────────────────────────────

def detect_gpu_vendor():
    """Detect primary GPU vendor via Windows WMI. Returns 'nvidia', 'amd', 'intel', or 'unknown'."""
    if sys.platform != "win32":
        return "unknown"
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "Get-CimInstance Win32_VideoController | Select-Object Name | ConvertTo-Json"],
            capture_output=True, text=True, timeout=10
        )
        gpus = json.loads(result.stdout)
        if not isinstance(gpus, list):
            gpus = [gpus]

        # Prefer discrete GPUs: check NVIDIA first, then AMD, then Intel
        for gpu in gpus:
            name = gpu.get("Name", "").upper()
            if "NVIDIA" in name:
                return "nvidia"
        for gpu in gpus:
            name = gpu.get("Name", "").upper()
            if "AMD" in name or "RADEON" in name:
                return "amd"
        for gpu in gpus:
            name = gpu.get("Name", "").upper()
            if "INTEL" in name:
                return "intel"
        return "unknown"
    except Exception:
        return "unknown"


# ── NVIDIA CUDA DLL Setup ────────────────────────────────────

def setup_cuda_paths():
    """Robustly locate and register CUDA DLL directories on Windows."""
    if sys.platform != "win32":
        return

    dll_dirs = set()

    # 1. pip-installed nvidia namespace packages (nvidia-cublas-cu12, nvidia-cudnn-cu12, etc.)
    try:
        import importlib.util
        for pkg in ["nvidia.cublas", "nvidia.cudnn", "nvidia.cuda_runtime",
                     "nvidia.cufft", "nvidia.curand", "nvidia.cusolver", "nvidia.cusparse"]:
            spec = importlib.util.find_spec(pkg)
            if spec and spec.submodule_search_locations:
                for loc in spec.submodule_search_locations:
                    for leaf in ("bin", "lib"):
                        d = os.path.join(loc, leaf)
                        if os.path.isdir(d):
                            dll_dirs.add(d)
    except Exception:
        pass

    # 2. Scan site-packages/nvidia/* for bin/lib folders
    try:
        import site
        search = list(site.getsitepackages())
        usp = site.getusersitepackages()
        if isinstance(usp, str):
            search.append(usp)
        for sp in search:
            nvidia_dir = os.path.join(sp, "nvidia")
            if os.path.isdir(nvidia_dir):
                for subdir in os.listdir(nvidia_dir):
                    for leaf in ("bin", "lib"):
                        d = os.path.join(nvidia_dir, subdir, leaf)
                        if os.path.isdir(d):
                            dll_dirs.add(d)
    except Exception:
        pass

    # 3. CUDA Toolkit system installation
    cuda_path = os.environ.get("CUDA_PATH", "")
    if cuda_path:
        d = os.path.join(cuda_path, "bin")
        if os.path.isdir(d):
            dll_dirs.add(d)

    # 4. Common CUDA Toolkit install location
    prog = os.environ.get("ProgramFiles", r"C:\Program Files")
    cuda_base = os.path.join(prog, "NVIDIA GPU Computing Toolkit", "CUDA")
    if os.path.isdir(cuda_base):
        for ver in sorted(os.listdir(cuda_base), reverse=True):
            d = os.path.join(cuda_base, ver, "bin")
            if os.path.isdir(d):
                dll_dirs.add(d)
                break  # latest version only

    # 5. cuDNN standalone install
    cudnn_path = os.environ.get("CUDNN_PATH", "")
    if cudnn_path:
        d = os.path.join(cudnn_path, "bin")
        if os.path.isdir(d):
            dll_dirs.add(d)

    # Register all directories
    for d in dll_dirs:
        if d not in os.environ.get("PATH", ""):
            os.environ["PATH"] = d + os.pathsep + os.environ["PATH"]
        if hasattr(os, "add_dll_directory"):
            try:
                os.add_dll_directory(d)
            except OSError:
                pass


# ── Backend: faster-whisper + CUDA (NVIDIA) ───────────────────

def transcribe_cuda(input_file, language, beam_size):
    """Transcribe with faster-whisper on NVIDIA CUDA GPU."""
    setup_cuda_paths()
    from faster_whisper import WhisperModel

    print("@@BACKEND:faster-whisper CUDA", flush=True)
    print("@@MODEL_LOADING", flush=True)
    model_id = _resolve_model("ivrit-ai/whisper-large-v3-turbo-ct2")
    model = WhisperModel(model_id, device="cuda", compute_type="float16")
    print("@@MODEL_READY", flush=True)

    segments, info = model.transcribe(
        input_file, language=language, beam_size=beam_size, word_timestamps=True
    )
    duration = info.duration
    print(f"@@DURATION:{duration:.2f}", flush=True)

    words = []
    for segment in segments:
        words.extend(segment.words)
        text = " ".join(w.word.strip() for w in segment.words)
        print(f"@@SEG:{segment.end:.2f}|{text}", flush=True)
    return words


# ── Backend: openai-whisper + DirectML (AMD / Intel / any DX12) ──

def transcribe_directml(input_file, language, beam_size):
    """Transcribe with openai-whisper on DirectML GPU (works for AMD, Intel, NVIDIA)."""
    import torch
    import torch_directml
    import whisper

    print("@@BACKEND:openai-whisper DirectML", flush=True)
    print("@@MODEL_LOADING", flush=True)
    dml_device = torch_directml.device()

    # Load model on CPU first, then move to DirectML
    model = whisper.load_model("medium", device="cpu")
    model = model.to(dml_device)
    print("@@MODEL_READY", flush=True)

    # Get audio duration
    import whisper.audio
    audio = whisper.audio.load_audio(input_file)
    duration = len(audio) / whisper.audio.SAMPLE_RATE
    print(f"@@DURATION:{duration:.2f}", flush=True)

    # Transcribe — word_timestamps gives per-word timing
    result = model.transcribe(
        input_file,
        language=language,
        beam_size=beam_size,
        word_timestamps=True,
        fp16=False,  # DirectML works best with float32
    )

    # Convert to word objects matching our SRT writer interface
    words = []
    for seg in result.get("segments", []):
        seg_words = []
        for w in seg.get("words", []):
            seg_words.append(_WordObj(w["word"], w["start"], w["end"]))
        words.extend(seg_words)
        text = " ".join(w.word.strip() for w in seg_words)
        if text:
            print(f"@@SEG:{seg.get('end', 0):.2f}|{text}", flush=True)
    return words


# ── Backend: faster-whisper CPU (last resort) ─────────────────

def transcribe_cpu(input_file, language, beam_size):
    """Transcribe with faster-whisper on CPU (no GPU acceleration)."""
    from faster_whisper import WhisperModel

    print("@@BACKEND:faster-whisper CPU", flush=True)
    print("@@MODEL_LOADING", flush=True)
    model_id = _resolve_model("ivrit-ai/whisper-large-v3-turbo-ct2")
    model = WhisperModel(model_id, device="cpu", compute_type="int8")
    print("@@MODEL_READY", flush=True)

    segments, info = model.transcribe(
        input_file, language=language, beam_size=beam_size, word_timestamps=True
    )
    duration = info.duration
    print(f"@@DURATION:{duration:.2f}", flush=True)

    words = []
    for segment in segments:
        words.extend(segment.words)
        text = " ".join(w.word.strip() for w in segment.words)
        print(f"@@SEG:{segment.end:.2f}|{text}", flush=True)
    return words


# ── Shared helpers ────────────────────────────────────────────

class _WordObj:
    """Lightweight word container for the DirectML backend."""
    __slots__ = ("word", "start", "end")
    def __init__(self, word, start, end):
        self.word = word
        self.start = start
        self.end = end


def fix_hebrew_rtl(text):
    """Move trailing punctuation to the front for RTL SRT display."""
    if not text:
        return text
    if not re.search(r'[\u0590-\u05FF]', text):
        return text
    m = re.search(r'([.?!,]+)$', text)
    if m:
        punc = m.group(1)
        return punc + text[:-len(punc)]
    return text


def format_timestamp(seconds):
    td = time.gmtime(seconds)
    ms = int((seconds % 1) * 1000)
    return f"{time.strftime('%H:%M:%S', td)},{ms:03d}"


def write_srt(words, output_file, max_words, do_rtl_fix):
    """Write words to SRT file, grouped by max_words per subtitle."""
    print("@@WRITING_SRT", flush=True)
    with open(output_file, "w", encoding="utf-8-sig") as f:
        counter = 1
        for i in range(0, len(words), max_words):
            chunk = words[i:i + max_words]
            start = chunk[0].start
            end = chunk[-1].end

            phrase = " ".join(w.word.strip() for w in chunk)
            if do_rtl_fix:
                phrase = fix_hebrew_rtl(phrase)

            f.write(f"{counter}\n")
            f.write(f"{format_timestamp(start)} --> {format_timestamp(end)}\n")
            f.write(f"{phrase}\n\n")
            counter += 1


# ── Main ──────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 3:
        print("Usage: transcriber.py <input.wav> <output.srt> [max_words] [do_rtl_fix]")
        return

    input_file  = sys.argv[1]
    output_file = sys.argv[2]
    max_words   = int(sys.argv[3]) if len(sys.argv) > 3 else 7
    do_rtl_fix  = sys.argv[4].lower() == "true" if len(sys.argv) > 4 else False

    # Detect GPU vendor
    vendor = detect_gpu_vendor()
    print(f"GPU: {vendor}")

    # Build backend priority list based on detected GPU
    if vendor == "nvidia":
        backends = [
            ("CUDA",     transcribe_cuda),
            ("DirectML", transcribe_directml),
            ("CPU",      transcribe_cpu),
        ]
    elif vendor in ("amd", "intel"):
        backends = [
            ("DirectML", transcribe_directml),
            ("CPU",      transcribe_cpu),
        ]
    else:
        backends = [
            ("DirectML", transcribe_directml),
            ("CUDA",     transcribe_cuda),
            ("CPU",      transcribe_cpu),
        ]

    # Try each backend until one succeeds
    words = None
    first_attempt = True
    for name, fn in backends:
        try:
            words = fn(input_file, "he", 5)
            break
        except Exception as e:
            print(f"{name} backend failed: {e}")
            if first_attempt and name != "CPU":
                # Signal to UI that we're falling back so it can warn the user
                print(f"@@BACKEND_FALLBACK:{e}", flush=True)
            first_attempt = False
            continue

    if not words:
        print("ERROR: All transcription backends failed!")
        sys.exit(1)

    write_srt(words, output_file, max_words, do_rtl_fix)
    print("@@DONE", flush=True)
    # Force exit to prevent GPU library teardown crash
    os._exit(0)


if __name__ == "__main__":
    main()

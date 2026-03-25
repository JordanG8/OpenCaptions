"""
install_deps.py — Auto-detect GPU vendor and install the correct packages.

Usage:
    python install_deps.py          # auto-detect GPU
    python install_deps.py nvidia   # force NVIDIA packages
    python install_deps.py amd      # force AMD/DirectML packages
    python install_deps.py cpu      # force CPU-only packages
"""

import subprocess
import sys
import json
import os
import shutil
import time

# Ensure unbuffered output
sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)


def set_title(title):
    """Set console window title on Windows."""
    if sys.platform == "win32":
        os.system(f"title {title}")


def disk_stats():
    """Return free disk space string for the drive where packages are installed."""
    try:
        site_pkg = os.path.dirname(os.path.abspath(__file__))
        usage = shutil.disk_usage(site_pkg)
        free_gb = usage.free / (1024 ** 3)
        total_gb = usage.total / (1024 ** 3)
        used_pct = (usage.used / usage.total) * 100
        return f"{free_gb:.1f} GB free / {total_gb:.1f} GB total ({used_pct:.0f}% used)"
    except Exception:
        return "unknown"


def dir_size_mb(path):
    """Get directory size in MB."""
    total = 0
    try:
        for dirpath, dirnames, filenames in os.walk(path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                try:
                    total += os.path.getsize(fp)
                except OSError:
                    pass
    except Exception:
        pass
    return total / (1024 * 1024)


def detect_gpu():
    """Detect GPU vendor via Windows WMI."""
    if sys.platform != "win32":
        print("Non-Windows platform — defaulting to CPU packages.")
        return "cpu"
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "Get-CimInstance Win32_VideoController | Select-Object Name | ConvertTo-Json"],
            capture_output=True, text=True, timeout=10
        )
        gpus = json.loads(result.stdout)
        if not isinstance(gpus, list):
            gpus = [gpus]

        found = []
        for gpu in gpus:
            name = gpu.get("Name", "")
            found.append(name)
            upper = name.upper()
            if "NVIDIA" in upper:
                return "nvidia"
            if "AMD" in upper or "RADEON" in upper:
                return "amd"
            if "INTEL" in upper:
                return "intel"

        print(f"Could not identify GPU vendor from: {found}")
        return "cpu"
    except Exception as e:
        print(f"GPU detection failed: {e}")
        return "cpu"


def pip_install(packages, desc, step, total_steps):
    """Run pip install for a list of packages with progress stats."""
    set_title(f"OpenCaptions — Installing {desc} [{step}/{total_steps}]")

    print(f"\n{'='*60}")
    print(f"  [{step}/{total_steps}] Installing {desc}...")
    print(f"  Disk: {disk_stats()}")
    print(f"{'='*60}\n")

    cmd = [sys.executable, "-m", "pip", "install", "--upgrade",
           "--progress-bar", "on"] + packages
    start = time.time()
    result = subprocess.run(cmd)
    elapsed = time.time() - start

    if result.returncode != 0:
        print(f"\n  WARNING: Some packages in '{desc}' may have failed.")
        return False

    print(f"\n  Done in {elapsed:.0f}s — Disk: {disk_stats()}")
    return True


def install_nvidia():
    """Install packages for NVIDIA CUDA GPU."""
    print("\n  Detected: NVIDIA GPU")
    print("  Installing faster-whisper with CUDA support...\n")

    s1 = pip_install(["faster-whisper>=1.0.0"], "faster-whisper", 1, 2)
    s2 = pip_install([
        "nvidia-cublas-cu12",
        "nvidia-cudnn-cu12",
        "nvidia-cuda-runtime-cu12",
    ], "NVIDIA CUDA libraries", 2, 2)

    if s1 and s2:
        print("\n" + "="*60)
        print("  NVIDIA setup complete!")
        print("="*60)
        return True
    return False


def install_directml():
    """Install packages for AMD/Intel DirectML GPU."""
    print("\n  Detected: AMD / Intel GPU")
    print("  Installing openai-whisper with DirectML GPU support...\n")

    s1 = pip_install(["torch>=2.1.0", "torchaudio>=2.1.0"], "PyTorch", 1, 4)
    s2 = pip_install(["torch-directml>=0.2.5"], "DirectML backend", 2, 4)
    s3 = pip_install(["openai-whisper>=20231117"], "OpenAI Whisper", 3, 4)
    s4 = pip_install(["faster-whisper>=1.0.0"], "faster-whisper (CPU fallback)", 4, 4)

    if s1 and s2 and s3 and s4:
        print("\n" + "="*60)
        print("  DirectML setup complete!")
        print("="*60)
        return True
    return False


def install_cpu():
    """Install CPU-only packages (minimal)."""
    print("\n  Installing CPU-only packages...")
    s1 = pip_install(["faster-whisper>=1.0.0"], "faster-whisper (CPU)", 1, 1)

    if s1:
        print("\n" + "="*60)
        print("  CPU-only setup complete.")
        print("="*60)
        return True
    return False


def main():
    set_title("OpenCaptions — Installing AI packages")

    print()
    print("  " + "="*56)
    print("    OpenCaptions — AI Package Installer")
    print("  " + "="*56)
    print(f"  Python: {sys.executable}")
    print(f"  Disk:   {disk_stats()}")

    if len(sys.argv) > 1:
        vendor = sys.argv[1].lower()
    else:
        vendor = detect_gpu()

    success = True
    if vendor == "nvidia":
        success = install_nvidia()
    elif vendor in ("amd", "intel"):
        success = install_directml()
    else:
        success = install_cpu()

    print(f"\n  Final disk: {disk_stats()}")
    if success is False:
        print("\n  ERROR: Dependency installation failed!")
        sys.exit(1)
    
    print("  Done! You can now use the OpenCaptions plugin in Premiere Pro.")
    print()


if __name__ == "__main__":
    main()

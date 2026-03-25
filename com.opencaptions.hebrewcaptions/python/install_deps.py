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


def pip_install(packages, desc):
    """Run pip install for a list of packages."""
    print(f"\n{'='*50}")
    print(f"Installing {desc}...")
    print(f"{'='*50}")
    cmd = [sys.executable, "-m", "pip", "install", "--upgrade"] + packages
    print(f"  > {' '.join(cmd)}\n")
    result = subprocess.run(cmd)
    if result.returncode != 0:
        print(f"WARNING: Some packages in '{desc}' may have failed to install.")
        return False
    return True


def install_nvidia():
    """Install packages for NVIDIA CUDA GPU."""
    print("\nDetected: NVIDIA GPU")
    print("Installing faster-whisper with CUDA support...\n")

    # Core transcription engine
    pip_install(["faster-whisper>=1.0.0"], "faster-whisper")

    # CUDA runtime libraries (DLLs for cublas, cudnn, etc.)
    pip_install([
        "nvidia-cublas-cu12",
        "nvidia-cudnn-cu12",
        "nvidia-cuda-runtime-cu12",
    ], "NVIDIA CUDA libraries")

    print("\n" + "="*50)
    print("NVIDIA setup complete!")
    print("If you still get CUDA errors, install the NVIDIA CUDA Toolkit:")
    print("  https://developer.nvidia.com/cuda-downloads")
    print("="*50)


def install_directml():
    """Install packages for AMD/Intel DirectML GPU."""
    print("\nDetected: AMD / Intel GPU")
    print("Installing openai-whisper with DirectML GPU support...\n")

    # PyTorch + DirectML (order matters: torch first, then directml)
    pip_install(["torch>=2.1.0", "torchaudio>=2.1.0"], "PyTorch")
    pip_install(["torch-directml>=0.2.5"], "DirectML backend")

    # OpenAI Whisper (uses the already-installed torch)
    pip_install(["openai-whisper>=20231117"], "OpenAI Whisper")

    # Also install faster-whisper for CPU fallback
    pip_install(["faster-whisper>=1.0.0"], "faster-whisper (CPU fallback)")

    print("\n" + "="*50)
    print("DirectML setup complete!")
    print("Supported: AMD Radeon, Intel Arc, and any DirectX 12 GPU.")
    print("="*50)


def install_cpu():
    """Install CPU-only packages (minimal)."""
    print("\nInstalling CPU-only packages...")
    pip_install(["faster-whisper>=1.0.0"], "faster-whisper (CPU)")

    print("\n" + "="*50)
    print("CPU-only setup complete.")
    print("="*50)


def main():
    print("OpenCaptions — GPU Dependency Installer")
    print("="*50)

    # Allow manual override via command-line argument
    if len(sys.argv) > 1:
        vendor = sys.argv[1].lower()
    else:
        vendor = detect_gpu()

    if vendor == "nvidia":
        install_nvidia()
    elif vendor in ("amd", "intel"):
        install_directml()
    else:
        install_cpu()

    print("\nDone! You can now use the OpenCaptions plugin in Premiere Pro.")


if __name__ == "__main__":
    main()

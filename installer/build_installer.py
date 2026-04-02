"""
build_installer.py — Downloads bundled Python + FFmpeg, then compiles the installer.

This makes the installer fully self-contained: users don't need Python or FFmpeg on PATH.

Downloads:
  - Python 3.11.9 embeddable (Windows x64) + pip
  - FFmpeg static build (Windows x64)

Usage:
    python installer/build_installer.py              # download deps + compile
    python installer/build_installer.py --deps-only  # download deps only
    python installer/build_installer.py --compile-only  # compile only
"""

import os
import sys
import glob
import shutil
import zipfile
import subprocess
import urllib.request

# ── Configuration ────────────────────────────────────────────

PYTHON_VERSION = "3.11.9"
PYTHON_URL = f"https://www.python.org/ftp/python/{PYTHON_VERSION}/python-{PYTHON_VERSION}-embed-amd64.zip"
GETPIP_URL = "https://bootstrap.pypa.io/get-pip.py"
FFMPEG_URL = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
WHISPER_MODEL_ID = "ivrit-ai/whisper-large-v3-turbo-ct2"

# ── Paths ────────────────────────────────────────────────────

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
EXTENSION_DIR = os.path.join(PROJECT_ROOT, "com.opencaptions.hebrewcaptions")
VENDOR_DIR = os.path.join(EXTENSION_DIR, "vendor")
PYTHON_DIR = os.path.join(VENDOR_DIR, "python")
FFMPEG_DIR = os.path.join(VENDOR_DIR, "ffmpeg")
MODELS_DIR = os.path.join(VENDOR_DIR, "models")
DOWNLOAD_CACHE = os.path.join(SCRIPT_DIR, "_cache")


def log(msg):
    print(f"[BUILD] {msg}")


def download(url, dest):
    """Download a file with progress indication."""
    filename = os.path.basename(dest)
    if os.path.exists(dest):
        log(f"  Cached: {filename}")
        return
    log(f"  Downloading {filename}...")
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    urllib.request.urlretrieve(url, dest)
    log(f"  Done: {filename} ({os.path.getsize(dest) / 1024 / 1024:.1f} MB)")


def setup_python():
    """Download and set up Python embeddable with pip."""
    if os.path.exists(os.path.join(PYTHON_DIR, "python.exe")):
        log("Python already set up, skipping.")
        return

    log("Setting up Python embeddable...")

    # Download Python embeddable zip
    python_zip = os.path.join(DOWNLOAD_CACHE, f"python-{PYTHON_VERSION}-embed-amd64.zip")
    download(PYTHON_URL, python_zip)

    # Extract
    os.makedirs(PYTHON_DIR, exist_ok=True)
    log("  Extracting Python...")
    with zipfile.ZipFile(python_zip, "r") as zf:
        zf.extractall(PYTHON_DIR)

    # Patch ._pth file to enable site-packages (required for pip)
    pth_files = glob.glob(os.path.join(PYTHON_DIR, "python*._pth"))
    for pth in pth_files:
        log(f"  Patching {os.path.basename(pth)} to enable site-packages...")
        with open(pth, "r") as f:
            content = f.read()
        content = content.replace("#import site", "import site")
        with open(pth, "w") as f:
            f.write(content)

    # Download and run get-pip.py
    getpip_path = os.path.join(DOWNLOAD_CACHE, "get-pip.py")
    download(GETPIP_URL, getpip_path)

    python_exe = os.path.join(PYTHON_DIR, "python.exe")
    log("  Installing pip...")
    subprocess.check_call(
        [python_exe, getpip_path, "--no-warn-script-location"],
        cwd=PYTHON_DIR,
    )

    # Verify pip works
    result = subprocess.run(
        [python_exe, "-m", "pip", "--version"],
        capture_output=True, text=True,
    )
    if result.returncode == 0:
        log(f"  pip installed: {result.stdout.strip()}")
    else:
        log("  WARNING: pip verification failed!")
        print(result.stderr)

    log("Python setup complete.")


def setup_ffmpeg():
    """Download and extract FFmpeg static build."""
    ffmpeg_exe = os.path.join(FFMPEG_DIR, "ffmpeg.exe")
    if os.path.exists(ffmpeg_exe):
        log("FFmpeg already set up, skipping.")
        return

    log("Setting up FFmpeg...")

    # Download FFmpeg zip
    ffmpeg_zip = os.path.join(DOWNLOAD_CACHE, "ffmpeg-latest-win64.zip")
    download(FFMPEG_URL, ffmpeg_zip)

    # Extract only the binaries we need (ffmpeg.exe, ffprobe.exe)
    os.makedirs(FFMPEG_DIR, exist_ok=True)
    log("  Extracting FFmpeg binaries...")
    with zipfile.ZipFile(ffmpeg_zip, "r") as zf:
        for member in zf.namelist():
            basename = os.path.basename(member)
            if basename in ("ffmpeg.exe", "ffprobe.exe"):
                log(f"    Extracting {basename}...")
                with zf.open(member) as src, open(os.path.join(FFMPEG_DIR, basename), "wb") as dst:
                    dst.write(src.read())

    if os.path.exists(ffmpeg_exe):
        log(f"FFmpeg setup complete ({os.path.getsize(ffmpeg_exe) / 1024 / 1024:.1f} MB).")
    else:
        log("WARNING: ffmpeg.exe not found after extraction!")


def setup_model():
    """Download the ivrit-ai Whisper model for bundling."""
    model_dir_name = WHISPER_MODEL_ID.replace("/", "--")
    dest = os.path.join(MODELS_DIR, model_dir_name)
    if os.path.exists(os.path.join(dest, "model.bin")):
        log("Whisper model already downloaded, skipping.")
        return

    log(f"Downloading {WHISPER_MODEL_ID} for bundling...")
    os.makedirs(dest, exist_ok=True)
    try:
        from huggingface_hub import snapshot_download
        snapshot_download(
            repo_id=WHISPER_MODEL_ID,
            local_dir=dest,
            local_dir_use_symlinks=False,
        )
        model_bin = os.path.join(dest, "model.bin")
        if os.path.exists(model_bin):
            size_mb = os.path.getsize(model_bin) / 1024 / 1024
            log(f"Model downloaded: {size_mb:.0f} MB")
        else:
            log("WARNING: model.bin not found after download!")
    except ImportError:
        log("huggingface_hub not installed. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "huggingface_hub"])
        from huggingface_hub import snapshot_download
        snapshot_download(
            repo_id=WHISPER_MODEL_ID,
            local_dir=dest,
            local_dir_use_symlinks=False,
        )
        log("Model downloaded.")

    log("Model setup complete.")


def compile_installer():
    """Find ISCC.exe and compile the installer."""
    iss_file = os.path.join(SCRIPT_DIR, "opencaptions-installer.iss")
    if not os.path.exists(iss_file):
        log("ERROR: opencaptions-installer.iss not found!")
        return False

    # Search for ISCC.exe in common locations
    search_paths = [
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "Inno Setup 6", "ISCC.exe"),
        os.path.join(os.environ.get("ProgramFiles(x86)", ""), "Inno Setup 6", "ISCC.exe"),
        os.path.join(os.environ.get("ProgramFiles", ""), "Inno Setup 6", "ISCC.exe"),
    ]

    iscc = None
    for p in search_paths:
        if os.path.exists(p):
            iscc = p
            break

    if not iscc:
        log("WARNING: ISCC.exe not found. Install Inno Setup 6 to compile the installer.")
        log("  Download: https://jrsoftware.org/isinfo.php")
        log(f"  Then run: ISCC.exe \"{iss_file}\"")
        return False

    log(f"Compiling installer with: {iscc}")
    result = subprocess.run([iscc, iss_file])
    if result.returncode == 0:
        output_dir = os.path.join(SCRIPT_DIR, "Output")
        exes = glob.glob(os.path.join(output_dir, "*.exe"))
        if exes:
            size_mb = os.path.getsize(exes[0]) / 1024 / 1024
            log(f"Installer built: {exes[0]} ({size_mb:.1f} MB)")
        return True
    else:
        log("ERROR: Installer compilation failed!")
        return False


def clean():
    """Remove vendor directory (for a clean rebuild)."""
    if os.path.exists(VENDOR_DIR):
        log(f"Removing {VENDOR_DIR}...")
        shutil.rmtree(VENDOR_DIR)
    log("Clean complete.")


def main():
    log("OpenCaptions Installer Builder")
    log("=" * 50)

    args = sys.argv[1:]

    if "--clean" in args:
        clean()
        return

    if "--compile-only" not in args:
        setup_python()
        setup_ffmpeg()
        setup_model()

    if "--deps-only" not in args:
        compile_installer()

    log("Done!")


if __name__ == "__main__":
    main()

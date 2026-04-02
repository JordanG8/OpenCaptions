"""
setup_env.py — One-click setup for OpenCaptions.

Creates a virtual environment, auto-detects your GPU, installs the
correct packages, and pre-downloads the AI model.

Usage:
    cd python
    python setup_env.py
"""

import os
import sys
import subprocess
import venv
import platform


def log(msg):
    print(f"--- [OPENCAPTIONS SETUP] {msg}")


def main():
    root_dir = os.path.dirname(os.path.abspath(__file__))
    venv_dir = os.path.join(root_dir, "venv")

    # 1. Create Virtual Environment
    if not os.path.exists(venv_dir):
        log("Creating virtual environment...")
        venv.create(venv_dir, with_pip=True)
    else:
        log("Virtual environment already exists.")

    # 2. Identify Python/Pip path inside venv
    if platform.system() == "Windows":
        pip_exe = os.path.join(venv_dir, "Scripts", "pip.exe")
        py_exe = os.path.join(venv_dir, "Scripts", "python.exe")
    else:
        pip_exe = os.path.join(venv_dir, "bin", "pip")
        py_exe = os.path.join(venv_dir, "bin", "python")

    # 3. Upgrade Pip and install setuptools
    log("Upgrading pip and installing setuptools...")
    subprocess.check_call([py_exe, "-m", "pip", "install", "--upgrade", "pip", "setuptools<70"])

    # 4. Auto-detect GPU and install correct packages
    install_script = os.path.join(root_dir, "install_deps.py")
    if os.path.exists(install_script):
        log("Auto-detecting GPU and installing dependencies...")
        subprocess.check_call([py_exe, install_script])
    else:
        # Fallback: install base requirements
        log("install_deps.py not found, installing base requirements...")
        subprocess.check_call([pip_exe, "install", "faster-whisper>=1.0.0"])

    # 5. Pre-download the model
    log("Pre-downloading AI model...")
    download_script = os.path.join(root_dir, "download_model.py")
    if os.path.exists(download_script):
        subprocess.check_call([py_exe, download_script])
    else:
        log("Warning: download_model.py not found.")

    log("SUCCESS: OpenCaptions environment is ready!")
    print(f"\nYour Python path is: {py_exe}\n")


if __name__ == "__main__":
    main()

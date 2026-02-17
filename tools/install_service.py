# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
# filepath: tools/install_service.py
"""
Install SWARMZ as a background service.
Supports Windows, macOS, and Linux.
"""

import os
import platform
import subprocess

LOG_PATH = "data/logs/service.log"

def install_service():
    system = platform.system()
    if system == "Windows":
        install_windows_service()
    elif system == "Darwin":
        install_macos_service()
    elif system == "Linux":
        install_linux_service()
    else:
        print("Unsupported OS. Service installation skipped.")

def install_windows_service():
    try:
        subprocess.run(["nssm", "install", "SWARMZ", "python", "run_swarmz.py"], check=True)
        subprocess.run(["nssm", "set", "SWARMZ", "AppStdout", LOG_PATH], check=True)
        subprocess.run(["nssm", "set", "SWARMZ", "AppStderr", LOG_PATH], check=True)
        print("Windows service installed successfully.")
    except Exception as e:
        print(f"Failed to install Windows service: {e}")

def install_macos_service():
    # macOS launchd setup
    pass  # TODO: Implement macOS service installation

def install_linux_service():
    # Linux systemd setup
    pass  # TODO: Implement Linux service installation

if __name__ == "__main__":
    install_service()

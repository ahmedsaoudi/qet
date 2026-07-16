# qet/utils.py - Utility Functions

import os
import tempfile
import shutil
from pathlib import Path


def is_command_available(cmd: str) -> bool:
    """Checks if a command is available in the system's PATH."""
    return shutil.which(cmd) is not None


def atomic_write(filepath: Path, content: str):
    """
    Writes content to a file atomically to prevent corruption.
    """
    filepath.parent.mkdir(parents=True, exist_ok=True)

    fd, tmp_path_str = tempfile.mkstemp(dir=filepath.parent)
    tmp_path = Path(tmp_path_str)

    try:
        with os.fdopen(fd, "w") as tmp_file:
            tmp_file.write(content)
        os.rename(tmp_path, filepath)
    except Exception as e:
        if tmp_path.exists():
            tmp_path.unlink()
        raise IOError(f"Atomic write to {filepath} failed: {e}")


def check_package_exists(manager: str, package_name: str) -> bool:
    """Checks if a package exists in a given system package manager."""
    import subprocess

    cmd = None
    if manager == "apt":
        cmd = ["apt-cache", "show", package_name]
    elif manager == "dnf":
        cmd = ["dnf", "info", package_name]
    elif manager == "pacman":
        cmd = ["pacman", "-Si", package_name]
    elif manager == "snap":
        cmd = ["snap", "info", package_name]
    elif manager == "flatpak":
        cmd = ["flatpak", "search", package_name]
    elif manager == "brew":
        cmd = ["brew", "info", package_name]
    elif manager == "pip":
        cmd = ["python3", "-m", "pip", "index", "versions", package_name]
    elif manager == "cargo":
        cmd = ["cargo", "search", package_name, "--limit", "1"]

    if not cmd:
        return False

    try:
        if not is_command_available(cmd[0]):
            return False
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if res.returncode == 0:
            if manager == "flatpak" and "No matches found" in res.stdout:
                return False
            if manager == "cargo" and not res.stdout.strip():
                return False
            return True
        return False
    except Exception:
        return False


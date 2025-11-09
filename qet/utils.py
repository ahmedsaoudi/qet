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
        with os.fdopen(fd, 'w') as tmp_file:
            tmp_file.write(content)
        os.rename(tmp_path, filepath)
    except Exception as e:
        if tmp_path.exists():
            tmp_path.unlink()
        raise IOError(f"Atomic write to {filepath} failed: {e}")
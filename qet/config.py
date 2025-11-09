# qet/config.py - Configuration and State Management

import os
import toml
from pathlib import Path
from typing import Dict, List, Any

# Define paths according to the specification
CONFIG_DIR = Path.home() / ".config" / "qet"
DATA_DIR = Path.home() / ".local" / "share" / "qet"
SYSTEM_DIR = Path("/usr/share/qet")

# File paths
CONF_FILE = CONFIG_DIR / "conf.toml"
MANIFEST_FILE = DATA_DIR / "manifest.toml"
DEFINITIONS_FILE = DATA_DIR / "definitions.toml"
METHODS_FILE = SYSTEM_DIR / "methods.toml"
QETFILE_PATH = Path.cwd() / "Qetfile"

# --- Default Content for Initial Setup ---

DEFAULT_CONF = {
    "priority": [
        "npm", "uvx", "pip", "cargo", "apt", "dnf", "pacman", "zypper", 
        "brew", "snap", "flatpak", "appimage", "script"
    ],
    "exclude": [],
    "defaults": {
        "download_tool": "curl",
        "appimage_dir": "~/.local/bin"
    }
}

MANAGER_PROVIDERS = {
    "npm": "@nodejs/node",
    "pip": "@python/pip",
    "uvx": "@python/uv",
    "cargo": "@rust/cargo",
    "brew": "@homebrew/brew",
    "flatpak": "@flatpak/flatpak",
    "snap": "@snapcraft/snapd",
}

DEFAULT_METHODS = {
    "apt": {"add_plumbing": "sudo apt-get install -y {package_name}", "remove_plumbing": "sudo apt-get purge -y {package_name}"},
    "dnf": {"add_plumbing": "sudo dnf install -y -q {package_name}", "remove_plumbing": "sudo dnf remove -y -q {package_name}"},
    "pacman": {"add_plumbing": "sudo pacman -S --noconfirm --needed {package_name}", "remove_plumbing": "sudo pacman -Rns --noconfirm {package_name}"},
    "zypper": {"add_plumbing": "sudo zypper --non-interactive install {package_name}", "remove_plumbing": "sudo zypper --non-interactive remove {package_name}"},
    "snap": {"add_plumbing": "sudo snap install {package_name}", "remove_plumbing": "sudo snap remove {package_name}"},
    "flatpak": {"add_plumbing": "flatpak install --user --assumeyes flathub {package_name}", "remove_plumbing": "flatpak uninstall --user --assumeyes {package_name}"},
    "brew": {"add_plumbing": "brew install {package_name}", "remove_plumbing": "brew uninstall {package_name}"},
    "npm": {"add_plumbing": "npm install -g {package_name}", "remove_plumbing": "npm uninstall -g {package_name}"},
    "pip": {"add_plumbing": "python3 -m pip install --upgrade {package_name}", "remove_plumbing": "python3 -m pip uninstall -y {package_name}"},
    "uvx": {"add_plumbing": "uvx --from-scope system pip install {package_name}", "remove_plumbing": "uvx --from-scope system pip uninstall -y {package_name}"},
    "cargo": {"add_plumbing": "cargo install {package_name}", "remove_plumbing": "cargo uninstall {package_name}"},
    "script": {"add_raw": "{download_command}"},
    "appimage": {"add_plumbing": "{download_command} && chmod +x {destination_path}", "remove_plumbing": "rm -f {destination_path}"}
}


def _load_toml_file(path: Path, default_content: Dict = None) -> Dict:
    """Loads a TOML file, creating it from defaults if it doesn't exist."""
    try:
        if not path.exists():
            if default_content is not None:
                path.parent.mkdir(parents=True, exist_ok=True)
                with open(path, "w") as f: toml.dump(default_content, f)
                return default_content
            return {}
        with open(path, "r") as f: return toml.load(f)
    except Exception as e:
        raise IOError(f"Failed to load or create {path}: {e}")

def get_conf() -> Dict[str, Any]: return _load_toml_file(CONF_FILE, DEFAULT_CONF)
def get_manifest() -> Dict[str, List[Dict]]: return _load_toml_file(MANIFEST_FILE, {"packages": []})
def save_manifest(data: Dict[str, List[Dict]]): from . import utils; utils.atomic_write(MANIFEST_FILE, toml.dumps(data))
def get_definitions() -> Dict: return _load_toml_file(DEFINITIONS_FILE)
def get_methods() -> Dict: return DEFAULT_METHODS
def get_manager_providers() -> dict: return MANAGER_PROVIDERS
def get_qetfile() -> Dict:
    if not QETFILE_PATH.exists(): raise FileNotFoundError("Qetfile not found in the current directory.")
    return _load_toml_file(QETFILE_PATH)
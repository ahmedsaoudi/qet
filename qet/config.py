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
INSTALL_LOGS_FILE = DATA_DIR / "install-logs.toml"
DEFINITIONS_FILE = DATA_DIR / "definitions.toml"
METHODS_FILE = SYSTEM_DIR / "methods.toml"
QETFILE_PATH = CONFIG_DIR / "Qetfile"

# --- Default Content for Initial Setup ---

DEFAULT_CONF = {
    "priority": ["appimage", "flatpak", "apt", "dnf", "pacman", "pip", "uvx", "cargo", "brew", "deb", "rpm", "script", "snap"],
    "exclude": ["snap"],
    "defaults": {
        "appimage_dir": "~/.local/bin",
        "require_confirmation_for": ["script"],
        "auto_search": True,
        "auto_fallback": False
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
    "apt":      {"add_plumbing": "sudo apt-get install -y {package_name}",                     "upgrade_plumbing": "sudo apt-get install --only-upgrade -y {package_name}",  "remove_plumbing": "sudo apt-get purge -y {package_name}"},
    "dnf":      {"add_plumbing": "sudo dnf install -y -q {package_name}",                      "upgrade_plumbing": "sudo dnf upgrade -y -q {package_name}",                    "remove_plumbing": "sudo dnf remove -y -q {package_name}"},
    "pacman":   {"add_plumbing": "sudo pacman -S --noconfirm --needed {package_name}",          "upgrade_plumbing": "sudo pacman -S --noconfirm {package_name}",                  "remove_plumbing": "sudo pacman -Rns --noconfirm {package_name}"},
    "zypper":   {"add_plumbing": "sudo zypper --non-interactive install {package_name}",        "upgrade_plumbing": "sudo zypper --non-interactive update {package_name}",         "remove_plumbing": "sudo zypper --non-interactive remove {package_name}"},
    "snap":     {"add_plumbing": "sudo snap install {package_name}",                            "upgrade_plumbing": "sudo snap refresh {package_name}",                           "remove_plumbing": "sudo snap remove {package_name}"},
    "flatpak":  {"add_plumbing": "flatpak install --user --assumeyes flathub {package_name}",  "upgrade_plumbing": "flatpak update --user --assumeyes {package_name}",            "remove_plumbing": "flatpak uninstall --user --assumeyes {package_name}"},
    "brew":     {"add_plumbing": "brew install {package_name}",                                 "upgrade_plumbing": "brew upgrade {package_name}",                                "remove_plumbing": "brew uninstall {package_name}"},
    "npm":      {"add_plumbing": "npm install -g {package_name}",                               "upgrade_plumbing": "npm install -g {package_name}",                              "remove_plumbing": "npm uninstall -g {package_name}"},
    "pip":      {"add_plumbing": "python3 -m pip install --upgrade {package_name}",             "upgrade_plumbing": "python3 -m pip install --upgrade {package_name}",            "remove_plumbing": "python3 -m pip uninstall -y {package_name}"},
    "uvx":      {"add_plumbing": "uvx --from-scope system pip install {package_name}",          "upgrade_plumbing": "uvx --from-scope system pip install --upgrade {package_name}","remove_plumbing": "uvx --from-scope system pip uninstall -y {package_name}"},
    "cargo":    {"add_plumbing": "cargo install {package_name}",                                "upgrade_plumbing": "cargo install {package_name}",                               "remove_plumbing": "cargo uninstall {package_name}"},
    "deb":      {"add_plumbing": "{download_command} && sudo apt-get install -y {destination_path}",  "upgrade_plumbing": "{download_command} && sudo apt-get install -y {destination_path}",  "remove_plumbing": "sudo apt-get purge -y {package_name}"},
    "rpm":      {"add_plumbing": "{download_command} && sudo dnf install -y {destination_path}",       "upgrade_plumbing": "{download_command} && sudo dnf install -y {destination_path}",       "remove_plumbing": "sudo dnf remove -y {package_name}"},
    "script":   {"add_raw": "{download_command}",                                               "upgrade_raw": "{download_command}"},
    "appimage": {"add_plumbing": "{download_command} && chmod +x {destination_path}",           "upgrade_plumbing": "{download_command} && chmod +x {destination_path}",          "remove_plumbing": "rm -f {destination_path}"}
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
def get_install_logs() -> Dict[str, List[Dict]]: return _load_toml_file(INSTALL_LOGS_FILE, {"packages": []})
def save_install_logs(data: Dict[str, List[Dict]]): from . import utils; utils.atomic_write(INSTALL_LOGS_FILE, toml.dumps(data))
def get_definitions() -> Dict:
    default_defs_path = Path(__file__).parent.parent / "example_definitions.toml"
    default_content = {}
    if default_defs_path.exists():
        with open(default_defs_path, "r") as f:
            default_content = toml.load(f)
    return _load_toml_file(DEFINITIONS_FILE, default_content)
def get_methods() -> Dict: return DEFAULT_METHODS
def get_manager_providers() -> dict: return MANAGER_PROVIDERS
def get_qetfile() -> Dict:
    return _load_toml_file(QETFILE_PATH, {"packages": []})
def save_qetfile(data: Dict):
    from . import utils; utils.atomic_write(QETFILE_PATH, toml.dumps(data))
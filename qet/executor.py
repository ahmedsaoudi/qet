# qet/executor.py - Command Execution Engine

import subprocess
import sys
import shlex
from typing import Dict
from .exceptions import MethodNotAvailableError, ConfigError, ExecutionError

def _build_download_command(conf: Dict, safe_context: Dict) -> str:
    """Constructs a download command string based on user configuration."""
    tool = conf.get("defaults", {}).get("download_tool", "curl")
    source_url = safe_context.get("source_url", "")
    destination = safe_context.get("destination_path", "")

    if tool == "wget":
        if destination: return f"wget -q {source_url} -O {destination}"
        else: return f"wget -qO- {source_url} | sudo bash"
    else: # Default to curl
        if destination: return f"curl -fsSL {source_url} -o {destination}"
        else: return f"curl -fsSL {source_url} | sudo bash"

def execute(method_name: str, action: str, conf: Dict, method_definitions: Dict, context: Dict) -> bool:
    """Executes a command based on the "Plumbing First" strategy."""
    method = method_definitions.get(method_name, {})
    cmd_template = method.get(f"{action}_plumbing") or method.get(f"{action}_raw")

    if not cmd_template:
        raise MethodNotAvailableError(f"No command defined for action '{action}' with method '{method_name}'.")

    # Sanitize inputs to prevent shell injection
    safe_context = {k: shlex.quote(str(v)) if v is not None else "" for k, v in context.items()}

    if method_name in ["appimage", "script", "deb", "rpm"]:
        if "source_url" in context:
            safe_context["download_command"] = _build_download_command(conf, safe_context)
        else:
            raise ConfigError(f"source_url is missing for method '{method_name}'.")

    command = cmd_template.format(**safe_context)
    
    try:
        process = subprocess.run(
            command, shell=True, check=True, capture_output=True, text=True
        )
        return process.stdout
    except subprocess.CalledProcessError as e:
        raise ExecutionError(
            f"Command failed with exit code {e.returncode}.",
            command=command,
            returncode=e.returncode,
            stdout=e.stdout,
            stderr=e.stderr
        )
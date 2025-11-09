# qet/executor.py - Command Execution Engine

import subprocess
import sys
from typing import Dict

def _build_download_command(conf: Dict, context: Dict) -> str:
    """Constructs a download command string based on user configuration."""
    tool = conf.get("defaults", {}).get("download_tool", "curl")
    source_url = context.get("source_url")
    destination = context.get("destination_path")

    if tool == "wget":
        if destination: return f"wget -q '{source_url}' -O '{destination}'"
        else: return f"wget -qO- '{source_url}' | sudo bash"
    else: # Default to curl
        if destination: return f"curl -fsSL '{source_url}' -o '{destination}'"
        else: return f"curl -fsSL '{source_url}' | sudo bash"

def execute(method_name: str, action: str, conf: Dict, method_definitions: Dict, context: Dict) -> bool:
    """Executes a command based on the "Plumbing First" strategy."""
    method = method_definitions.get(method_name, {})
    cmd_template = method.get(f"{action}_plumbing") or method.get(f"{action}_raw")

    if not cmd_template:
        print(f"--- ERROR: No command defined for action '{action}' with method '{method_name}'.", file=sys.stderr)
        return False

    if method_name in ["appimage", "script"]:
        if "source_url" in context:
            context["download_command"] = _build_download_command(conf, context)
        else:
            print(f"--- ERROR: source_url is missing for method '{method_name}'.", file=sys.stderr)
            return False

    command = cmd_template.format(**context)
    print(f"--- Running command: `{command}`")
    try:
        process = subprocess.run(
            command, shell=True, check=True, capture_output=True, text=True
        )
        if process.stdout: print(process.stdout)
        if process.stderr: print(process.stderr, file=sys.stderr)
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n--- ERROR: Command failed with exit code {e.returncode}.", file=sys.stderr)
        if e.stdout: print(e.stdout, file=sys.stderr)
        if e.stderr: print(e.stderr, file=sys.stderr)
        return False```

---

### **`qet/cli.py`**

```python
# qet/cli.py - Command-Line Interface Definition

import argparse
from . import commands

def run():
    """Sets up the argument parser and executes the appropriate command."""
    parser = argparse.ArgumentParser(prog="qet", description="A command-line meta package manager for Linux.")
    subparsers = parser.add_subparsers(dest="command", required=True, help="Available commands")

    # `qet add`
    p_add = subparsers.add_parser("add", help="Installs a new package.")
    p_add.add_argument("qet_name", help="The canonical qet name for the package (e.g., '@scope/name').")
    p_add.add_argument("--using", dest="method", help="Manually specify an installation method.")
    p_add.set_defaults(func=lambda args: commands.add_command(args))

    # `qet remove`
    p_remove = subparsers.add_parser("remove", help="Removes a package previously installed by qet.")
    p_remove.add_argument("qet_name", help="The canonical qet name of the package to remove.")
    p_remove.set_defaults(func=lambda args: commands.remove_command(args))

    # `qet upgrade`
    p_upgrade = subparsers.add_parser("upgrade", help="Upgrades one or all packages.")
    group = p_upgrade.add_mutually_exclusive_group(required=True)
    group.add_argument("qet_name", nargs="?", help="The canonical qet name of the package to upgrade.")
    group.add_argument("--all", action="store_true", help="Upgrade all packages managed by qet.")
    p_upgrade.set_defaults(func=commands.upgrade)
    
    # `qet update`
    p_update = subparsers.add_parser("update", help="Updates the local package definitions database.")
    p_update.set_defaults(func=commands.update)

    # `qet sync`
    p_sync = subparsers.add_parser("sync", help="Synchronizes the system with a Qetfile.")
    p_sync.set_defaults(func=commands.sync)

    # `qet snapshot`
    p_snapshot = subparsers.add_parser("snapshot", help="Creates a Qetfile from the current system state.")
    p_snapshot.set_defaults(func=commands.snapshot)

    args = parser.parse_args()
    args.func(args)
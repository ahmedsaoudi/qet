# qet/commands.py - Implementation of Core Logic

import datetime
import toml
from pathlib import Path
from typing import Dict, List, Any
from . import config, executor, utils
from .exceptions import (
    QetError,
    PackageNotFoundError,
    MethodNotAvailableError,
    ExecutionError,
    AllMethodsFailedError,
)


def resolve_method_candidates(qet_name: str, method_override: str = None) -> List[str]:
    """Returns all viable methods for a package in priority order."""
    conf = config.get_conf()
    definitions = config.get_definitions()
    package_def = definitions.get(qet_name)
    if not package_def:
        raise PackageNotFoundError(
            f"Package '{qet_name}' not found in definitions database."
        )

    if method_override:
        if method_override not in package_def:
            raise MethodNotAvailableError(
                f"Method '{method_override}' is not available for '{qet_name}'."
            )
        return [method_override]  # --using pins to exactly one method, no fallback

    candidates = [
        m for m in conf.get("priority", [])
        if m not in conf.get("exclude", []) and m in package_def
    ]

    if not candidates:
        raise MethodNotAvailableError(
            f"Could not find a suitable installation method for '{qet_name}'."
        )

    return candidates


def resolve_method(qet_name: str, method_override: str = None) -> str:
    """Resolves the first viable method for a package. Used for pre-flight checks."""
    return resolve_method_candidates(qet_name, method_override)[0]


def add_package(
    qet_name: str, method_override: str = None, status_callback=None, confirm_callback=None
) -> Dict[str, Any]:
    """Handles the logic for adding a package. Returns the manifest entry on success."""

    def status(msg):
        if status_callback:
            status_callback(msg)

    def needs_confirm(method_name: str) -> bool:
        # User requested confirmation for all installations
        return True

    def confirmed(method_name: str, context: Dict[str, Any]) -> bool:
        """Returns True if we may proceed. Calls confirm_callback if needed."""
        if not needs_confirm(method_name):
            return True
        if confirm_callback is None:
            return True  # Non-interactive mode: allow
        return confirm_callback(method_name, context)

    status(f"Resolving package '{qet_name}'...")
    conf = config.get_conf()
    methods = config.get_methods()
    definitions = config.get_definitions()

    current_state = {p["qet_name"]: p for p in list_installed()}
    if qet_name in current_state:
        raise QetError(f"Package '{qet_name}' is already installed.")

    package_def = definitions.get(qet_name)
    candidates = resolve_method_candidates(qet_name, method_override)

    last_error = None
    for method_to_use in candidates:
        method_info = package_def[method_to_use]
        context = {**method_info}
        manifest_entry = {"qet_name": qet_name, "method": method_to_use, **method_info}

        if method_to_use in ["appimage", "deb", "rpm"]:
            if method_to_use == "appimage":
                dest_dir = Path(
                    conf["defaults"].get("appimage_dir", "~/.local/bin")
                ).expanduser()
                filename = qet_name.split("/")[-1] + ".AppImage"
                destination_path = dest_dir / filename
                manifest_entry["appimage_path"] = str(destination_path)
            else:
                dest_dir = Path("/tmp/qet_downloads")
                filename = qet_name.split("/")[-1] + f".{method_to_use}"
                destination_path = dest_dir / filename

            dest_dir.mkdir(parents=True, exist_ok=True)
            context["destination_path"] = str(destination_path)

        status(f"Trying '{method_to_use}'...")

        if not confirmed(method_to_use, context):
            status(f"Skipping '{method_to_use}' (confirmation declined)...")
            continue

        try:
            executor.execute(method_to_use, "add", conf, methods, context)
        except ExecutionError as e:
            _log_event(
                "install", qet_name, "failed",
                method=method_to_use,
                details=e.stderr.strip() if e.stderr else str(e),
                command=e.command
            )
            last_error = e
            if len(candidates) > 1:
                status(f"'{method_to_use}' failed (exit {e.returncode}), trying next method...")
            continue  # try next candidate

        # Success
        status("Logging installation...")
        manifest_entry["install_date"] = datetime.datetime.now(
            datetime.timezone.utc
        ).isoformat()
        _log_event(
            "install", qet_name, "success",
            method=method_to_use,
            details=context.get("destination_path") or context.get("package_name"),
        )

        status("Syncing Qetfile...")
        qetfile_data = config.get_qetfile()
        if not any(
            p["qet_name"] == qet_name for p in qetfile_data.get("packages", [])
        ):
            qetfile_data.setdefault("packages", []).append(
                {"qet_name": qet_name, "method": method_to_use}
            )
            config.save_qetfile(qetfile_data)

        return manifest_entry

    # All candidates exhausted — collect per-method details and raise structured error
    failures = []
    logs = config.get_install_logs().get("events", [])
    for candidate in candidates:
        for ev in reversed(logs):
            if ev.get("qet_name") == qet_name and ev.get("method") == candidate and ev.get("action") == "install" and ev.get("status") == "failed":
                failures.append((candidate, ev.get("details", "Unknown error")))
                break
        else:
            failures.append((candidate, "Skipped (confirmation declined)"))
    raise AllMethodsFailedError(qet_name, failures)


def remove_package(qet_name: str, status_callback=None) -> None:
    """Handles the logic for removing a package."""

    def status(msg):
        if status_callback:
            status_callback(msg)

    status(f"Resolving installed package '{qet_name}'...")
    conf = config.get_conf()
    methods = config.get_methods()

    current_state = {p["qet_name"]: p for p in list_installed()}
    package_to_remove = current_state.get(qet_name)

    if not package_to_remove:
        raise QetError(
            f"Package '{qet_name}' is not logged as installed by qet."
        )

    method = package_to_remove["method"]
    context = {
        "package_name": package_to_remove.get("details"),
        "destination_path": package_to_remove.get("details"),
    }

    status(f"Executing uninstallation using '{method}'...")
    try:
        executor.execute(method, "remove", conf, methods, context)
    except ExecutionError as e:
        _log_event("remove", qet_name, "failed", method=method, details=str(e))
        raise

    status("Logging uninstallation...")
    _log_event(
        "remove",
        qet_name,
        "success",
        method=method,
        details=context.get("destination_path") or context.get("package_name"),
    )

    status("Syncing Qetfile...")
    qetfile_data = config.get_qetfile()
    qetfile_data["packages"] = [
        p for p in qetfile_data.get("packages", []) if p["qet_name"] != qet_name
    ]
    config.save_qetfile(qetfile_data)


def upgrade_package(qet_name: str = None, status_callback=None) -> List[str]:
    """Upgrades one or all installed packages. Returns list of upgraded package names."""

    def status(msg):
        if status_callback:
            status_callback(msg)

    conf = config.get_conf()
    methods = config.get_methods()
    installed = list_installed()

    if not installed:
        raise QetError("No packages are currently installed via qet.")

    targets = []
    if qet_name:
        pkg = next((p for p in installed if p["qet_name"] == qet_name), None)
        if not pkg:
            raise QetError(
                f"Package '{qet_name}' is not logged as installed by qet."
            )
        targets = [pkg]
    else:
        targets = installed

    upgraded = []
    failed = []

    for pkg in targets:
        name = pkg["qet_name"]
        method = pkg["method"]

        status(f"Upgrading '{name}' via {method}...")

        # Reconstruct context from definitions
        context = {}
        definitions = config.get_definitions()
        pkg_def = definitions.get(name, {})
        method_def = pkg_def.get(method, {})
        context.update(method_def)

        original_dest = None
        tmp_dest = None

        if method in ["appimage", "deb", "rpm"]:
            original_dest = pkg.get("details") or ""
            # Download to a .tmp path — never touch the live file until we're sure
            tmp_dest = original_dest + ".tmp"
            context["destination_path"] = tmp_dest

        try:
            executor.execute(method, "upgrade", conf, methods, context)

            # Atomically replace the old file with the newly downloaded one
            if original_dest and tmp_dest:
                import os

                os.replace(tmp_dest, original_dest)

            _log_event("upgrade", name, "success", method=method)
            upgraded.append(name)
        except Exception as e:
            # Clean up the partial/temp file if it exists
            if tmp_dest:
                import os

                try:
                    os.unlink(tmp_dest)
                except OSError:
                    pass

            _log_event("upgrade", name, "failed", method=method, details=str(e))
            failed.append(name)

    if failed:
        raise QetError(
            f"Upgrade completed with errors. Failed: {', '.join(failed)}"
        )

    return upgraded


def get_snapshot_data() -> str:
    """Returns a Qetfile TOML string representing the current state."""
    installed = list_installed()
    if not installed:
        return "# No packages managed by qet.\n"

    qetfile_data = {"packages": []}
    for pkg in sorted(installed, key=lambda p: p["qet_name"]):
        qetfile_data["packages"].append(
            {"qet_name": pkg["qet_name"], "method": pkg["method"]}
        )

    header = "# This file was generated by `qet snapshot`.\n\n"
    return header + toml.dumps(qetfile_data)


def write_snapshot(path: Path = None) -> Path:
    """Writes a Qetfile snapshot to *path* (defaults to the configured qetfile_path).

    Returns the resolved path where the file was written.
    """
    target = Path(path).expanduser() if path else config.get_qetfile_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    utils.atomic_write(target, get_snapshot_data())
    return target


def sync_from_qetfile(
    qetfile_path: Path = None,
    status_callback=None,
    confirm_callback=None,
) -> Dict[str, Any]:
    """Reads a Qetfile and installs any packages not already present.

    Returns a dict with three keys:
      - "installed": list of qet_names that were successfully installed.
      - "skipped":   list of qet_names that were already installed.
      - "failed":    list of (qet_name, error_message) tuples.
    """

    def status(msg):
        if status_callback:
            status_callback(msg)

    if qetfile_path is None:
        qetfile_path = config.get_qetfile_path()

    qetfile_path = Path(qetfile_path)
    if not qetfile_path.exists():
        raise QetError(f"No Qetfile found at '{qetfile_path.resolve()}'.")

    status(f"Reading {qetfile_path}...")
    try:
        qetfile_data = toml.load(qetfile_path)
    except Exception as e:
        raise QetError(f"Failed to parse Qetfile: {e}")

    packages = qetfile_data.get("packages", [])
    if not packages:
        raise QetError(
            "Qetfile contains no [[packages]] entries."
        )

    status("Comparing against currently installed packages...")
    current_names = {p["qet_name"] for p in list_installed()}

    result: Dict[str, Any] = {"installed": [], "skipped": [], "failed": []}

    for i, entry in enumerate(packages, 1):
        qet_name = entry.get("qet_name", "").strip()
        method_override = entry.get("method") or None

        if not qet_name:
            continue

        if qet_name in current_names:
            result["skipped"].append(qet_name)
            continue

        status(f"[{i}/{len(packages)}] Installing '{qet_name}'...")
        try:
            add_package(
                qet_name,
                method_override,
                status_callback=status_callback,
                confirm_callback=confirm_callback,
            )
            result["installed"].append(qet_name)
            current_names.add(qet_name)
        except AllMethodsFailedError as e:
            result["failed"].append(
                (qet_name, f"All methods failed: {', '.join(m for m, _ in e.failures)}")
            )
        except QetError as e:
            result["failed"].append((qet_name, str(e)))

    return result


def info_package(qet_name: str) -> Dict[str, Any]:
    """Returns information about a package from the definitions database."""
    definitions = config.get_definitions()
    package_def = definitions.get(qet_name)
    if not package_def:
        raise PackageNotFoundError(
            f"Package '{qet_name}' not found in definitions database."
        )

    return package_def


def search_packages(query: str) -> List[str]:
    """Searches the definitions database for packages matching the query."""
    definitions = config.get_definitions()
    query_lower = query.lower()

    matches = []
    for qet_name in definitions.keys():
        if query_lower in qet_name.lower():
            matches.append(qet_name)

    return sorted(matches)


def _log_event(
    action: str,
    qet_name: str,
    event_status: str,
    method: str = None,
    details: str = None,
    command: str = None,
):
    """Appends an event to the global install-logs.toml file."""
    install_logs = config.get_install_logs()
    event = {
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "action": action,
        "qet_name": qet_name,
        "status": event_status,
    }
    if method:
        event["method"] = method
    if details:
        event["details"] = details
    if command:
        event["command"] = command

    install_logs.setdefault("events", []).append(event)
    config.save_install_logs(install_logs)


def list_installed() -> List[Dict[str, Any]]:
    """Calculates the current state by replaying the event log."""
    install_logs = config.get_install_logs()
    state = {}
    for event in install_logs.get("events", []):
        if event["status"] != "success":
            continue

        name = event["qet_name"]
        if event["action"] == "install":
            state[name] = event
        elif event["action"] == "remove" and name in state:
            del state[name]

    # Convert dict to list
    return [v for k, v in state.items()]


def get_history(
    since_date: str = None, package_name: str = None
) -> List[Dict[str, Any]]:
    """Returns a filtered list of historical events."""
    events = config.get_install_logs().get("events", [])

    if package_name:
        events = [e for e in events if e.get("qet_name") == package_name]

    if since_date:
        # Simple string comparison works for ISO dates (e.g. '2026-07-16')
        events = [e for e in events if e.get("timestamp", "") >= since_date]

    return events


def search_system_managers(package_name: str) -> List[str]:
    """Searches available system managers to see if they have the package."""
    conf = config.get_conf()
    available = []
    for manager in conf.get("priority", []):
        if manager in conf.get("exclude", []):
            continue
        if utils.check_package_exists(manager, package_name):
            available.append(manager)
    return available


def define_package(qet_name: str, method: str, value: str) -> None:
    """Manually adds or updates a package definition in the database."""
    definitions = config.get_definitions()
    entry = definitions.setdefault(qet_name, {})
    if method in ["appimage", "script", "deb", "rpm"]:
        entry[method] = {"source_url": value}
    else:
        entry[method] = {"package_name": value}

    import toml

    utils.atomic_write(config.DEFINITIONS_FILE, toml.dumps(definitions))


def add_to_definitions(qet_name: str, method: str, package_name: str) -> None:
    """Legacy helper for auto-fallback to add a definition."""
    define_package(qet_name, method, package_name)


def method_enable(method_name: str) -> None:
    """Moves a method from exclude to priority in the config."""
    conf = config.get_conf()
    if method_name in conf.get("exclude", []):
        conf["exclude"].remove(method_name)
    if method_name not in conf.get("priority", []):
        conf.setdefault("priority", []).append(method_name)
    import toml

    utils.atomic_write(config.CONF_FILE, toml.dumps(conf))


def method_disable(method_name: str) -> None:
    """Moves a method from priority to exclude in the config."""
    conf = config.get_conf()
    if method_name in conf.get("priority", []):
        conf["priority"].remove(method_name)
    if method_name not in conf.get("exclude", []):
        conf.setdefault("exclude", []).append(method_name)
    import toml

    utils.atomic_write(config.CONF_FILE, toml.dumps(conf))


def init_environment(status_callback=None) -> None:
    """Analyses the current environment and sets up the conf.toml."""

    def status(msg):
        if status_callback:
            status_callback(msg)

    status("Detecting system package managers...")
    all_known_managers = [
        "apt",
        "dnf",
        "pacman",
        "zypper",
        "brew",
        "snap",
        "flatpak",
        "pip",
        "uvx",
        "cargo",
    ]
    installed_managers = [
        m for m in all_known_managers if utils.is_command_available(m)
    ]

    # 1. Identify Default System Manager (Must be first)
    system_primary_candidates = ["apt", "dnf", "pacman", "zypper"]
    default_manager = next(
        (
            cand
            for cand in system_primary_candidates
            if cand in installed_managers
        ),
        None,
    )

    # 2. Sandbox managers ordering (Ubuntu-esque preference)
    has_snap = "snap" in installed_managers
    has_flatpak = "flatpak" in installed_managers
    sandbox_managers = []

    if default_manager == "apt":
        # Ubuntu-esque: snap before flatpak
        if has_snap:
            sandbox_managers.append("snap")
        if has_flatpak:
            sandbox_managers.append("flatpak")
    else:
        # Others: flatpak before snap
        if has_flatpak:
            sandbox_managers.append("flatpak")
        if has_snap:
            sandbox_managers.append("snap")

    # 3. Other non-default managers (only if installed)
    other_managers = [
        m for m in ["brew", "uvx", "pip", "cargo"] if m in installed_managers
    ]

    # 4. Abstract methods (only if their underlying dependencies exist)
    abstract_methods = ["appimage", "script"]
    if default_manager == "apt":
        abstract_methods.append("deb")
    if default_manager == "dnf":
        abstract_methods.append("rpm")

    # Assemble Priority (No duplicates, default manager ALWAYS first)
    priority = []
    if default_manager:
        priority.append(default_manager)
    priority.extend(sandbox_managers)
    priority.extend(other_managers)
    priority.extend(abstract_methods)

    # Assemble Exclude (Everything known that is NOT in priority)
    exclude = [m for m in all_known_managers if m not in priority]

    conf = config.get_conf()
    conf["priority"] = priority
    conf["exclude"] = exclude
    # Ensure the defaults section exists and qetfile_path is stamped in,
    # but preserve any value the user has already set.
    conf.setdefault("defaults", {})
    conf["defaults"].setdefault("qetfile_path", str(config.QETFILE_PATH))

    status("Writing optimized config to ~/.config/qet/conf.toml...")
    import toml

    utils.atomic_write(config.CONF_FILE, toml.dumps(conf))


# qet/commands.py - Implementation of CLI Commands

import sys
import datetime
import toml
from pathlib import Path
from . import config, executor, utils

def add_package(qet_name: str, method_override: str = None) -> bool:
    """Handles the logic for adding a package. Returns True on success, False on failure."""
    conf = config.get_conf()
    methods = config.get_methods()
    definitions = config.get_definitions()
    manifest = config.get_manifest()

    if any(p['qet_name'] == qet_name for p in manifest.get('packages', [])):
        print(f"Package '{qet_name}' is already installed.")
        return True

    package_def = definitions.get(qet_name)
    if not package_def:
        print(f"Error: Package '{qet_name}' not found in definitions database.", file=sys.stderr)
        return False

    method_to_use = None
    if method_override:
        if method_override not in package_def:
            print(f"Error: Method '{method_override}' is not available for '{qet_name}'.", file=sys.stderr)
            return False
        method_to_use = method_override
    else:
        for method_name in conf.get('priority', []):
            if method_name in conf.get('exclude', []): continue
            if method_name in package_def:
                method_to_use = method_name
                break
    
    if not method_to_use:
        print(f"Error: Could not find a suitable installation method for '{qet_name}'.", file=sys.stderr)
        return False
    
    print(f"Using method: '{method_to_use}'")
    method_info = package_def[method_to_use]
    context = {**method_info}
    manifest_entry = {"qet_name": qet_name, "method": method_to_use, **method_info}

    if method_to_use == "appimage":
        appimage_dir = Path(conf["defaults"]["appimage_dir"]).expanduser()
        appimage_dir.mkdir(parents=True, exist_ok=True)
        filename = qet_name.split('/')[-1] + ".AppImage"
        destination_path = appimage_dir / filename
        context["destination_path"] = str(destination_path)
        manifest_entry["appimage_path"] = str(destination_path)

    success = executor.execute(method_to_use, "add", conf, methods, context)

    if success:
        manifest_entry["install_date"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        manifest.setdefault("packages", []).append(manifest_entry)
        config.save_manifest(manifest)
        print(f"Successfully installed '{qet_name}'.")
    else:
        print(f"Failed to install '{qet_name}'.", file=sys.stderr)
    return success

def remove_package(qet_name: str) -> bool:
    """Handles the logic for removing a package. Returns True on success, False on failure."""
    conf = config.get_conf()
    methods = config.get_methods()
    manifest = config.get_manifest()
    
    package_to_remove = next((p for p in manifest.get('packages', []) if p['qet_name'] == qet_name), None)
            
    if not package_to_remove:
        print(f"Package '{qet_name}' is not managed by qet. Nothing to do.")
        return True

    method = package_to_remove['method']
    context = { "package_name": package_to_remove.get("package_name"), "destination_path": package_to_remove.get("appimage_path") }
    success = executor.execute(method, "remove", conf, methods, context)

    if success:
        manifest['packages'] = [p for p in manifest['packages'] if p['qet_name'] != qet_name]
        config.save_manifest(manifest)
        print(f"Successfully removed '{qet_name}'.")
    else:
        print(f"Failed to remove '{qet_name}'.", file=sys.stderr)
    return success

# --- User-facing command wrappers ---
def add_command(args):
    print(f"Attempting to add package: {args.qet_name}")
    if not add_package(args.qet_name, args.method): sys.exit(1)

def remove_command(args):
    print(f"Attempting to remove package: {args.qet_name}")
    if not remove_package(args.qet_name): sys.exit(1)

def sync(args):
    """Handles the `qet sync` command with pre-flight checks and reporting."""
    print("--- Starting sync with Qetfile ---")
    
    print("--- [1/4] Performing pre-flight checks...")
    all_methods = set(config.get_methods().keys())
    available_managers = {name for name in all_methods if utils.is_command_available(name)}
    if utils.is_command_available('node'): available_managers.add('npm')
    if utils.is_command_available('python3'): available_managers.add('pip')
    print(f"Available managers: {', '.join(sorted(list(available_managers)))}")

    print("--- [2/4] Analyzing desired state...")
    try: qetfile = config.get_qetfile()
    except FileNotFoundError as e: print(f"Error: {e}", file=sys.stderr); sys.exit(1)
        
    manifest = config.get_manifest()
    desired = {p['qet_name']: p for p in qetfile.get('packages', [])}
    installed = {p['qet_name']: p for p in manifest.get('packages', [])}

    to_add = [pkg for name, pkg in desired.items() if name not in installed]
    to_remove = [name for name in installed if name not in desired]
            
    print(f"Analysis: {len(to_add)} package(s) to add, {len(to_remove)} to remove.")
    if not to_add and not to_remove:
        print("System is already in sync."); return

    print("--- [3/4] Executing changes...")
    results = {"success": [], "skipped": [], "failed": [], "removed": [], "removed_failed": []}
    
    for pkg_info in to_add:
        pkg_name = pkg_info['qet_name']
        method = pkg_info['method']
        
        print(f"\n-> Processing '{pkg_name}' with method '{method}'...")
        
        if method not in available_managers and method not in ['script', 'appimage']:
            print(f"SKIPPED: Required manager '{method}' is not installed.")
            results["skipped"].append((pkg_name, f"missing manager: {method}"))
            continue

        if add_package(pkg_name, method): results["success"].append(pkg_name)
        else: results["failed"].append(pkg_name)

    for name in to_remove:
        print(f"\n-> Removing '{name}'...")
        if remove_package(name): results["removed"].append(name)
        else: results["removed_failed"].append(name)

    print("\n--- [4/4] Sync session summary ---")
    manager_providers = config.get_manager_providers()
    if results["success"]: print(f"\n✅ Successfully installed ({len(results['success'])}): {', '.join(results['success'])}")
    if results["removed"]: print(f"\n🗑️ Successfully removed ({len(results['removed'])}): {', '.join(results['removed'])}")
    if results["skipped"]:
        print(f"\n⚠️ Skipped packages ({len(results['skipped'])}):")
        for pkg, reason in results["skipped"]:
            print(f"  - {pkg} (Reason: {reason})")
            manager = reason.split(": ")[-1]
            if manager in manager_providers:
                print(f"    💡 To fix, try: qet add {manager_providers[manager]}")
    if results["failed"] or results["removed_failed"]:
        failed = results['failed'] + results['removed_failed']
        print(f"\n❌ Failed operations ({len(failed)}): {', '.join(failed)}")
    print("\n--- Sync completed. ---")

def snapshot(args):
    """Handles the `qet snapshot` command."""
    manifest = config.get_manifest()
    if not manifest.get('packages'):
        print("# No packages managed by qet.", file=sys.stderr); return
    
    qetfile_data = {"packages": []}
    for pkg in sorted(manifest['packages'], key=lambda p: p['qet_name']):
        qetfile_data["packages"].append({"qet_name": pkg['qet_name'], "method": pkg['method']})
        
    header = "# This file was generated by `qet snapshot`.\n\n"
    print(header + toml.dumps(qetfile_data))

def upgrade(args): print("The 'upgrade' command is not yet implemented.")
def update(args): print("The 'update' command is not yet implemented.")
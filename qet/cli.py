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


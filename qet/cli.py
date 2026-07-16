# qet/cli.py - Command-Line Interface Definition

import argparse
import sys
import json
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Confirm
from . import commands
from .exceptions import QetError, ExecutionError, AllMethodsFailedError

console = Console()


def run():
    """Sets up the argument parser and executes the appropriate command."""
    parser = argparse.ArgumentParser(
        prog="qet", description="A command-line meta package manager for Linux."
    )
    subparsers = parser.add_subparsers(
        dest="command", required=True, help="Available commands"
    )

    # `qet add`
    p_add = subparsers.add_parser("add", help="Installs a package.")
    p_add.add_argument("qet_name", help="The canonical qet name of the package.")
    p_add.add_argument(
        "--using", dest="method", help="Force a specific installation method."
    )
    p_add.add_argument("-y", "--yes", action="store_true", help="Skip confirmation prompts.")

    # `qet init`
    p_init = subparsers.add_parser("init", help="Analyses the environment and sets optimal defaults.")

    # `qet method`
    p_method = subparsers.add_parser("method", help="Manage installation methods (enable/disable).")
    p_method.add_argument("action", choices=["enable", "disable"], help="Action to perform.")
    p_method.add_argument("name", help="The name of the method (e.g. cargo, snap).")

    # `qet define`
    p_define = subparsers.add_parser("define", help="Manually add a package definition to the database.")
    p_define.add_argument("qet_name", help="The canonical qet name (e.g. @utils/tool).")
    p_define.add_argument("method", help="The installation method (e.g. apt, appimage).")
    p_define.add_argument("value", help="The package name or source URL.")

    # `qet remove`
    p_remove = subparsers.add_parser(
        "remove", help="Removes a package previously installed by qet."
    )
    p_remove.add_argument(
        "qet_name", help="The canonical qet name of the package to remove."
    )


    # `qet update`
    p_update = subparsers.add_parser(
        "update", help="Updates the local package definitions database."
    )

    # `qet sync`
    p_sync = subparsers.add_parser(
        "sync", help="Synchronizes the system with a Qetfile."
    )

    # `qet snapshot`
    p_snapshot = subparsers.add_parser("snapshot", help="Creates a Qetfile from the current system state.")

    # `qet info`
    p_info = subparsers.add_parser("info", help="Displays information about a package.")
    p_info.add_argument("qet_name", help="The canonical qet name of the package.")

    # `qet search`
    p_search = subparsers.add_parser("search", help="Searches for packages in the definitions database.")
    p_search.add_argument("query", help="The term to search for.")

    # `qet list`
    p_list = subparsers.add_parser("list", help="Lists all currently installed packages and their details.")
    p_list.add_argument("--json", action="store_true", help="Output in machine-readable JSON format.")

    # `qet upgrade`
    p_upgrade = subparsers.add_parser("upgrade", help="Upgrades one or all installed packages to their latest version.")
    p_upgrade.add_argument("qet_name", nargs="?", default=None, help="Package to upgrade. If omitted, upgrades all.")

    # `qet audit`
    p_audit = subparsers.add_parser("audit", help="Explore the history of package installations and removals.")
    p_audit.add_argument("qet_name", nargs="?", help="Filter history by a specific package name.")
    p_audit.add_argument("--since", help="Filter history since a specific date (YYYY-MM-DD).")
    p_audit.add_argument("--json", action="store_true", help="Output in machine-readable JSON format.")

    args = parser.parse_args()

    try:
        if args.command == "add":
            conf = commands.config.get_conf()
            try:
                method_to_use = commands.resolve_method(args.qet_name, args.method)
            except commands.PackageNotFoundError:
                if not conf.get("defaults", {}).get("auto_search", True):
                    raise
                    
                with console.status(f"[bold cyan]Searching for '{args.qet_name}' across system managers...[/bold cyan]", spinner="dots"):
                    available_managers = commands.search_system_managers(args.qet_name)
                    
                if not available_managers:
                    console.print(f"[bold red]Error:[/bold red] '{args.qet_name}' not found in qet definitions or any system manager.")
                    sys.exit(1)
                    
                if conf.get("defaults", {}).get("auto_fallback", False) or args.yes:
                    method_to_use = available_managers[0]
                    console.print(f"[bold cyan]Auto-fallback selected '{method_to_use}' for '{args.qet_name}'.[/bold cyan]")
                    commands.add_to_definitions(args.qet_name, method_to_use, args.qet_name)
                else:
                    console.print(f"\n[bold yellow]Package '{args.qet_name}' is not in qet definitions, but was found in:[/bold yellow] {', '.join(available_managers)}")
                    if Confirm.ask(f"Would you like to install it using [cyan]{available_managers[0]}[/cyan] and remember this choice?"):
                        method_to_use = available_managers[0]
                        commands.add_to_definitions(args.qet_name, method_to_use, args.qet_name)
                    else:
                        console.print("[yellow]Installation cancelled.[/yellow]")
                        sys.exit(0)

            # Do NOT pin args.method here — let add_package iterate all candidates.
            # Pass a confirm_callback so security prompts fire per-candidate inside
            # the fallback loop, not just for the first resolved method.
            skip_confirm = args.yes

            with console.status(f"[bold cyan]Initializing...[/bold cyan]", spinner="dots") as status:
                def update_status(msg):
                    status.update(f"[bold cyan]{msg}[/bold cyan]")

                def do_confirm(method_name):
                    if skip_confirm:
                        return True
                    status.stop()
                    console.print(f"\n[bold yellow]Security Warning:[/bold yellow] '{args.qet_name}' will be installed using [bold red]'{method_name}'[/bold red] which executes an external script.")
                    result = Confirm.ask("Do you want to proceed?")
                    if result:
                        status.start()
                    return result

                entry = commands.add_package(
                    args.qet_name,
                    args.method,  # None unless user passed --using
                    status_callback=update_status,
                    confirm_callback=do_confirm,
                )
            console.print(f"[bold green]Successfully installed[/bold green] [bold]{args.qet_name}[/bold] using [cyan]{entry['method']}[/cyan].")


            
        elif args.command == "remove":
            with console.status(f"[bold red]Initializing...[/bold red]", spinner="dots") as status:
                def update_status(msg):
                    status.update(f"[bold red]{msg}[/bold red]")
                
                commands.remove_package(args.qet_name, status_callback=update_status)
            console.print(f"[bold green]Successfully removed[/bold green] [bold]{args.qet_name}[/bold].")
            
        elif args.command == "info":
            info = commands.info_package(args.qet_name)
            console.print(f"[bold]Package:[/bold] [cyan]{args.qet_name}[/cyan]")
            console.print("[bold]Available installation methods:[/bold]")
            for method, details in info.items():
                if isinstance(details, dict):
                    detail_str = ", ".join(f"{k}='{v}'" for k, v in details.items())
                    console.print(f"  - [yellow]{method}[/yellow]: {detail_str}")

        elif args.command == "search":
            results = commands.search_packages(args.query)
            if results:
                console.print(f"Found [bold green]{len(results)}[/bold green] package(s) matching '[cyan]{args.query}[/cyan]':")
                for res in results:
                    console.print(f"  - [bold]{res}[/bold]")
            else:
                console.print(f"[yellow]No packages found matching '{args.query}'.[/yellow]")
                
        elif args.command == "list":
            packages = commands.list_installed()
            if args.json:
                print(json.dumps(packages, indent=2))
                return
                
            if not packages:
                console.print("[yellow]No packages are currently installed via qet.[/yellow]")
            else:
                table = Table(title="Currently Installed Packages")
                table.add_column("Package Name", style="cyan", no_wrap=True)
                table.add_column("Method", style="magenta")
                table.add_column("Install Date", style="green")
                table.add_column("Details", style="yellow")
                
                for p in packages:
                    name = p.get("qet_name", "Unknown")
                    method = p.get("method", "Unknown")
                    
                    date_str = p.get("timestamp", "Unknown")
                    if "T" in date_str:
                        date_str = date_str.replace("T", " ")[:16]
                    
                    details = p.get("details", "")
                    table.add_row(name, method, date_str, details)
                    
                console.print(table)
                
        elif args.command == "audit":
            events = commands.get_history(since_date=args.since, package_name=args.qet_name)
            if args.json:
                print(json.dumps(events, indent=2))
                return
                
            if not events:
                console.print("[yellow]No historical events found matching your criteria.[/yellow]")
            else:
                table = Table(title="System Audit Log")
                table.add_column("Timestamp", style="green")
                table.add_column("Action", style="bold")
                table.add_column("Status", style="bold")
                table.add_column("Package", style="cyan")
                table.add_column("Method", style="magenta")
                table.add_column("Details", style="yellow")
                
                for e in events:
                    date_str = e.get("timestamp", "Unknown").replace("T", " ")[:16]
                    action = e.get("action", "")
                    
                    action_fmt = f"[blue]{action}[/blue]" if action == "install" else f"[red]{action}[/red]"
                    status = e.get("status", "")
                    status_fmt = f"[green]{status}[/green]" if status == "success" else f"[bold red]{status}[/bold red]"
                    
                    table.add_row(
                        date_str, 
                        action_fmt, 
                        status_fmt, 
                        e.get("qet_name", ""), 
                        e.get("method", ""), 
                        e.get("details", "")
                    )
                console.print(table)
                
        elif args.command == "init":
            with console.status("[bold cyan]Initializing qet environment...[/bold cyan]", spinner="dots") as status:
                def update_status(msg):
                    status.update(f"[bold cyan]{msg}[/bold cyan]")
                commands.init_environment(status_callback=update_status)
            console.print("[bold green]Successfully initialized qet for your environment![/bold green]")
            
        elif args.command == "method":
            if args.action == "enable":
                commands.method_enable(args.name)
                console.print(f"[bold green]Method '{args.name}' enabled and added to priority list.[/bold green]")
            elif args.action == "disable":
                commands.method_disable(args.name)
                console.print(f"[bold green]Method '{args.name}' disabled and excluded.[/bold green]")

        elif args.command == "define":
            commands.define_package(args.qet_name, args.method, args.value)
            console.print(f"[bold green]Successfully added definition for '{args.qet_name}' using '{args.method}'.[/bold green]")
            
        elif args.command == "upgrade":
            target = getattr(args, 'qet_name', None)
            label = f"'{target}'" if target else "all packages"
            
            with console.status(f"[bold cyan]Upgrading {label}...[/bold cyan]", spinner="dots") as status:
                def update_status(msg):
                    status.update(f"[bold cyan]{msg}[/bold cyan]")
                upgraded = commands.upgrade_package(target, status_callback=update_status)
            
            if len(upgraded) == 1:
                console.print(f"[bold green]Successfully upgraded {upgraded[0]}.[/bold green]")
            else:
                console.print(f"[bold green]Successfully upgraded {len(upgraded)} package(s):[/bold green]")
                for name in upgraded:
                    console.print(f"  - {name}")

        elif args.command == "snapshot":
            console.print(commands.get_snapshot_data())
            
        elif args.command == "sync":
            console.print("[yellow]The 'sync' command is being restructured and is temporarily disabled.[/yellow]")

            
    except AllMethodsFailedError as e:
        console.print(f"\n[bold red]All installation methods failed for '{e.qet_name}':[/bold red]\n")
        table = Table(show_header=True, header_style="bold")
        table.add_column("Method", style="magenta", no_wrap=True)
        table.add_column("Reason", style="yellow")
        for method, detail in e.failures:
            # Extract the most useful line from the error (last non-empty line of stderr)
            reason = detail.strip().splitlines()[-1].strip() if detail else "Unknown error"
            table.add_row(method, reason)
        console.print(table)
        sys.exit(1)
    except ExecutionError as e:
        console.print(f"\n[bold red]Execution Error:[/bold red] {e}")
        if e.stderr:
            console.print(Panel(e.stderr.strip(), title="Command Output", border_style="red"))
        sys.exit(1)
    except QetError as e:
        console.print(f"\n[bold red]Error:[/bold red] {e}")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[bold red]An unexpected error occurred:[/bold red] {e}")
        sys.exit(2)

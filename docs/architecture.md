# Architecture

This document describes the internal structure of `qet`: the purpose of each module, how they interact, and the flow of data for key operations.

---

## Source Map

```
qet/
├── __init__.py        # Package marker (minimal)
├── cli.py             # Argument parsing and user-facing output (Rich)
├── commands.py        # Core business logic
├── config.py          # Configuration and state management (file I/O)
├── executor.py        # Command execution engine (shell dispatch)
├── exceptions.py      # Exception hierarchy
└── utils.py           # Utility helpers (atomic writes, command detection)
```

---

## Module Responsibilities

### [`cli.py`](../qet/cli.py)

**Entry point.** The `run()` function is registered as the `qet` console script in `pyproject.toml`.

Responsibilities:
- Defines all `argparse` subparsers (one per command).
- Calls the appropriate `commands.*` function.
- Formats and prints results using [`Rich`](https://github.com/Textualize/rich) tables, panels, and status spinners.
- Catches all `QetError` subclasses and renders them as user-friendly error messages.
- Passes `status_callback` and `confirm_callback` closures into commands so the business logic never imports Rich directly.

**Does NOT** contain any business logic or file I/O.

> File: [`qet/cli.py`](../qet/cli.py) · Entry point: [`run()`](../qet/cli.py#L16-L303)

---

### [`commands.py`](../qet/commands.py)

**Core logic layer.** All meaningful decisions happen here.

| Function | Description |
|---|---|
| [`add_package()`](../qet/commands.py#L52-L155) | Installs a package; handles fallback loop, confirmation, logging, Qetfile sync |
| [`remove_package()`](../qet/commands.py#L158-L205) | Removes a package by replaying the log to find the install method |
| [`upgrade_package()`](../qet/commands.py#L208-L287) | Upgrades one or all packages; atomic download for file-based methods |
| [`list_installed()`](../qet/commands.py#L355-L370) | Derives current state by replaying the event log |
| [`get_history()`](../qet/commands.py#L373-L386) | Returns filtered install/remove history |
| [`info_package()`](../qet/commands.py#L306-L315) | Returns the definitions entry for a package |
| [`search_packages()`](../qet/commands.py#L318-L328) | Substring search over definitions keys |
| [`search_system_managers()`](../qet/commands.py#L389-L398) | Queries native managers for an unknown package |
| [`resolve_method_candidates()`](../qet/commands.py#L17-L44) | Returns all viable methods in priority order |
| [`resolve_method()`](../qet/commands.py#L47-L49) | Returns just the first viable method |
| [`define_package()`](../qet/commands.py#L401-L412) | Adds/updates a definition in the local DB |
| [`method_enable()` / `method_disable()`](../qet/commands.py#L420-L441) | Edits `conf.toml` priority/exclude lists |
| [`init_environment()`](../qet/commands.py#L444-L528) | Detects available managers and writes optimised `conf.toml` |
| [`get_snapshot_data()`](../qet/commands.py#L290-L303) | Serialises the current state as a Qetfile TOML string |
| [`_log_event()`](../qet/commands.py#L331-L352) | Internal helper to append an event to `install-logs.toml` |

**Does NOT** format output or import Rich. Communicates progress via optional callback functions.

---

### [`config.py`](../qet/config.py)

**File I/O and default values.** All file paths, default content, and TOML loading are centralised here.

| Symbol | Description |
|---|---|
| `CONFIG_DIR` | `~/.config/qet` |
| `DATA_DIR` | `~/.local/share/qet` |
| `SYSTEM_DIR` | `/usr/share/qet` |
| `CONF_FILE` | `~/.config/qet/conf.toml` |
| `INSTALL_LOGS_FILE` | `~/.local/share/qet/install-logs.toml` |
| `DEFINITIONS_FILE` | `~/.local/share/qet/definitions.toml` |
| `METHODS_FILE` | `/usr/share/qet/methods.toml` |
| `QETFILE_PATH` | `~/.config/qet/Qetfile` |
| `DEFAULT_CONF` | Default configuration dictionary |
| `DEFAULT_METHODS` | Shell command templates for all supported methods |
| `MANAGER_PROVIDERS` | Maps manager names to their qet package (e.g. `npm` → `@nodejs/node`) |
| `get_conf()` | Loads or creates `conf.toml` |
| `get_install_logs()` | Loads or creates `install-logs.toml` |
| `get_definitions()` | Loads or creates `definitions.toml` (seeded from `example_definitions.toml`) |
| `get_methods()` | Returns `DEFAULT_METHODS` (future: reads from `methods.toml`) |
| `get_qetfile()` | Loads or creates the global `Qetfile` |
| `save_install_logs()` | Atomically writes the install log |
| `save_qetfile()` | Atomically writes the global Qetfile |

---

### [`executor.py`](../qet/executor.py)

**Shell dispatch engine.** Translates a method name + action + context into a shell command and executes it.

| Function | Description |
|---|---|
| [`execute()`](../qet/executor.py#L22-L53) | Builds and runs a command; raises `ExecutionError` on non-zero exit |
| [`_build_download_command()`](../qet/executor.py#L9-L20) | Constructs a `curl` or `wget` invocation from config |

**Security:** All context values are passed through `shlex.quote()` before being interpolated into the command template to prevent shell injection.

**"Plumbing First" strategy:** For each method + action, executor first tries `<action>_plumbing` (a complete shell command), then falls back to `<action>_raw` (a raw command string). This allows future extensibility.

---

### [`exceptions.py`](../qet/exceptions.py)

**Exception hierarchy.** All exceptions inherit from `QetError`.

```
QetError
├── ConfigError              # Bad/missing config files
├── PackageNotFoundError     # qet_name not in definitions database
├── MethodNotAvailableError  # Method not in definition or no candidates found
├── ExecutionError           # Shell command returned non-zero exit code
│   └── .command, .returncode, .stdout, .stderr
└── AllMethodsFailedError    # Every candidate method was tried and failed
    └── .qet_name, .failures (list of (method, detail) tuples)
```

> File: [`qet/exceptions.py`](../qet/exceptions.py)

---

### [`utils.py`](../qet/utils.py)

**Utility helpers.** Small, pure functions with no qet-specific business logic.

| Function | Description |
|---|---|
| [`is_command_available(cmd)`](../qet/utils.py#L9-L11) | Returns `True` if `cmd` is found in `PATH` via `shutil.which` |
| [`atomic_write(filepath, content)`](../qet/utils.py#L14-L30) | Writes to a temp file, then `os.rename`s it — prevents partial writes |
| [`check_package_exists(manager, package_name)`](../qet/utils.py#L33-L70) | Queries a native manager to check if a package exists |

---

## Data Flow: `qet add @utils/htop`

```
User
  │
  └─▶ cli.run()                        [cli.py]
        │
        ├─▶ commands.resolve_method()   [commands.py]
        │     │
        │     ├─▶ config.get_conf()     [config.py]  → reads conf.toml
        │     └─▶ config.get_definitions() [config.py] → reads definitions.toml
        │
        └─▶ commands.add_package()      [commands.py]
              │
              ├─▶ config.get_methods()  [config.py]  → returns DEFAULT_METHODS
              ├─▶ [fallback loop over candidates]
              │     │
              │     └─▶ executor.execute("apt", "add", conf, methods, context)
              │               │                                [executor.py]
              │               ├─▶ shlex.quote() all context values
              │               ├─▶ cmd = "sudo apt-get install -y htop"
              │               └─▶ subprocess.run(cmd, shell=True, check=True)
              │
              ├─▶ commands._log_event("install", ..., "success")  [commands.py]
              │     └─▶ config.save_install_logs()  [config.py]  → atomic write
              │
              └─▶ config.save_qetfile()             [config.py]  → atomic write
```

---

## State Model

qet uses an **event-sourced** model for tracking installed packages:

- All install and remove operations append an event to `install-logs.toml`. These events include the exact shell `command` executed and the raw `stderr` (stored in `details`) on failure, ensuring `qet audit` is highly actionable.
- `list_installed()` **replays** the full event log to compute the current state:
  - `install` (success) → adds the package.
  - `remove` (success) → removes the package.
  - Failed events are ignored.

This design makes the log corruption-resistant and auditable.

---

## Dependencies

| Library | Version | Purpose |
|---|---|---|
| `toml` | ≥ 0.10.2 | Reading and writing TOML files |
| `rich` | ≥ 13.0.0 | Terminal formatting — tables, spinners, colours |

Both are declared in [`pyproject.toml`](../pyproject.toml).

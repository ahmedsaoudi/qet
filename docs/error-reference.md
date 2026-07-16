# Error Reference

All exceptions in qet inherit from `QetError`.

> **Source:** [`qet/exceptions.py`](../qet/exceptions.py)

---

## Exception Hierarchy

```
QetError
├── ConfigError
├── PackageNotFoundError
├── MethodNotAvailableError
├── ExecutionError
└── AllMethodsFailedError
```

---

## `QetError`

**Base class** for all qet-specific errors. Any exception you don't recognise below will be printed as a generic `Error:` message.

```python
class QetError(Exception):
    pass
```

---

## `ConfigError`

Raised when a configuration or methods file cannot be loaded or parsed.

| Trigger | Example |
|---|---|
| Malformed TOML in `conf.toml` or `definitions.toml` | Syntax error in the file |
| `source_url` missing for an `appimage` / `script` / `deb` / `rpm` package | Definition is incomplete |

**Resolution:** Check the file indicated in the error message for TOML syntax errors or missing required fields.

> **Source:** [`qet/executor.py` L37](../qet/executor.py#L37), raised as `ConfigError` when `source_url` is absent.

---

## `PackageNotFoundError`

Raised when a requested qet name is not present in the definitions database.

| Trigger | Example |
|---|---|
| `qet add @foo/bar` where `@foo/bar` is not in `definitions.toml` | New/unknown package |
| `qet info @foo/bar` for a non-existent package | Same |

**Resolution:**
- Run `qet search <term>` to find the correct qet name.
- Add a definition manually: `qet define @foo/bar apt bar`.
- If `auto_search = true` (default) and you're using `qet add`, qet will automatically trigger an interactive "Did you mean?" prompt displaying close matches and native repository packages before failing completely.

> **Source:** [`qet/commands.py` L23](../qet/commands.py#L23), [`qet/commands.py` L311](../qet/commands.py#L311)

---

## `MethodNotAvailableError`

Raised when no viable installation method can be found for a package.

**Two distinct causes:**

### 1. `--using` flag with an unavailable method

```bash
qet add @utils/htop --using cargo
# Error: Method 'cargo' is not available for '@utils/htop'.
```

The method you forced does not exist in the package's definition. Run `qet info <qet_name>` to see what methods are defined.

### 2. No candidates after filtering

```bash
qet add @microsoft/vscode
# Error: Could not find a suitable installation method for '@microsoft/vscode'.
```

The package is defined but none of its methods appear in your `priority` list (or all are in `exclude`).

**Resolution:**
- Run `qet info <qet_name>` to see available methods.
- Run `qet method enable <method>` to add the needed method to your priority list.
- Or add the method manually to `conf.toml`.

> **Source:** [`qet/commands.py` L29–L42](../qet/commands.py#L29-L42)

---

## `ExecutionError`

Raised when a shell command exits with a non-zero return code.

**Attributes:**

| Attribute | Type | Description |
|---|---|---|
| `command` | `str` | The exact shell command that was run |
| `returncode` | `int` | The process exit code |
| `stdout` | `str` | Standard output from the command |
| `stderr` | `str` | Standard error from the command |

**CLI output:** The error message and `stderr` are printed in a red panel.

```
Execution Error: Command failed with exit code 1.
╭─ Command Output ─────────────────────────────────────────────╮
│ E: Unable to locate package htop                             │
╰──────────────────────────────────────────────────────────────╯
```

**Common causes:**

| Cause | Fix |
|---|---|
| Package name wrong in definition | Correct the definition via `qet define` |
| System manager not installed | Install the manager or run `qet init` |
| Insufficient permissions | Ensure `sudo` is available and configured |
| Network error during download | Check connectivity; verify the `source_url` is valid |

> **Source:** [`qet/executor.py` L46–L53](../qet/executor.py#L46-L53)

---

## `AllMethodsFailedError`

Raised when **every candidate method** for a package was attempted and all failed.

**Attributes:**

| Attribute | Type | Description |
|---|---|---|
| `qet_name` | `str` | The qet name of the package |
| `failures` | `list[tuple[str, str]]` | List of `(method_name, error_detail)` pairs |

**CLI output:** A table listing each failed method and the last line of its stderr:

```
All installation methods failed for '@microsoft/vscode':

┌──────────┬──────────────────────────────────────────────────┐
│ Method   │ Reason                                           │
├──────────┼──────────────────────────────────────────────────┤
│ apt      │ E: Unable to locate package code                 │
│ flatpak  │ error: No remote refs found similar to 'flathub' │
└──────────┴──────────────────────────────────────────────────┘
```

**Resolution:** Fix the underlying issue for at least one of the listed methods. Common fixes:
- Add the package's apt repository before trying `apt`.
- Add the Flathub remote before trying `flatpak`: `flatpak remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo`.
- Use `--using <method>` to force a specific method that you know is correctly set up.

> **Source:** [`qet/commands.py` L145–L155](../qet/commands.py#L145-L155), rendered in [`qet/cli.py` L282–L292](../qet/cli.py#L282-L292)

---

## Common Native Errors

Because `qet` wraps native package managers, you may occasionally see errors originating directly from the underlying tool. `qet` logs the exact executed `command` and raw `stderr` in `install-logs.toml` to help you debug these.

### Snap in Docker/Containers

```
error: cannot communicate with server: Post "http://localhost/v2/snaps/...": dial unix /run/snapd.socket: connect: no such file or directory
```

**Cause:** The Snap daemon (`snapd`) relies heavily on `systemd` and kernel features like squashfs/AppArmor. Standard Docker containers do not run `systemd` and are isolated from these kernel features, meaning `snap` packages fundamentally cannot be installed in this environment.

**Resolution:** When running `qet` inside a container (like a devcontainer or Dockerfile), rely on `apt`, `deb`, `script`, or `appimage` methods. `qet`'s fallback loop will usually handle this automatically, but if you force `--using snap`, it will fail.

---

## Unexpected Errors

Any exception not in the `QetError` hierarchy is caught as a last resort and printed with exit code `2`:

```
An unexpected error occurred: <message>
```

If you encounter this, please open a bug report with the full traceback (run with `python -m qet ...` to see it).

---

## Exit Codes

| Code | Meaning |
|---|---|
| `0` | Success |
| `1` | Known qet error (`QetError` subclass or `AllMethodsFailedError`) |
| `2` | Unexpected / unhandled exception |

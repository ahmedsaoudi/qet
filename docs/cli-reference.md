# CLI Reference

All commands follow the form:

```
qet <command> [arguments] [flags]
```

---

## `qet add`

Installs a package using the best available method.

```
qet add <qet_name> [--using <method>] [-y]
```

| Argument / Flag | Description |
|---|---|
| `qet_name` | Required. The canonical qet name (e.g. `@utils/htop`). |
| `--using <method>` | Force a specific installation method. No automatic fallback. |
| `-y`, `--yes` | Skip all confirmation prompts (including security warnings). |

### Resolution logic

1. Looks up `qet_name` in `~/.local/share/qet/definitions.toml`.
2. Filters candidates to those present in `priority` and not in `exclude` (from `conf.toml`).
3. Tries each candidate in priority order, falling back to the next on failure.
4. If the package is **not** an exact match in the definitions database, `qet` triggers an interactive fallback prompt ("Did you mean?"). It lists closely matching canonical definitions and native system packages, neatly filtered by your `priority` list.
5. If exactly *one* valid option is found in the fallback search, `qet` auto-selects it and proceeds silently.
6. On success, logs the exact command and raw `stderr` (if any errors occurred) to `install-logs.toml` and appends the entry to the global `Qetfile`.

### Examples

```bash
# Auto-select the best method
qet add @utils/ripgrep

# Force Flatpak specifically
qet add @microsoft/vscode --using flatpak

# Skip security prompts (useful in scripts)
qet add @ai/lm-studio -y

# Install an imprecise name (triggers the interactive "Did you mean?" prompt)
qet add code
```

### Interactive Fallback

If you forget a scope or type a native package name (e.g. `qet add code`), `qet` will search both its internal definitions and native system managers (like `apt` or `dnf`). It presents a unified, sorted list of options that respect your `conf.toml` `priority` and `exclude` rules, ensuring you never accidentally pollute your `Qetfile` with unscoped names when canonical ones exist.

### Security prompt

Methods `script` (and any others listed in `require_confirmation_for`) show a confirmation before running. Pass `-y` or `--yes` to suppress this.

> **Source:** [`qet/cli.py` L94–L147](../qet/cli.py#L94-L147) · [`qet/commands.py` — `add_package()`](../qet/commands.py#L52-L155)

---

## `qet remove`

Removes a package that was previously installed by qet.

```
qet remove <qet_name>
```

| Argument | Description |
|---|---|
| `qet_name` | Required. The canonical qet name of the package to remove. |

`remove` replays the install log to find the exact method that was used and passes the correct arguments to the native uninstaller. The event is logged and the entry is removed from the global `Qetfile`.

### Examples

```bash
qet remove @utils/htop
qet remove @microsoft/vscode
```

> **Source:** [`qet/cli.py` L151–L157](../qet/cli.py#L151-L157) · [`qet/commands.py` — `remove_package()`](../qet/commands.py#L158-L205)

---

## `qet upgrade`

Upgrades one or all qet-managed packages to their latest version.

```
qet upgrade [qet_name]
```

| Argument | Description |
|---|---|
| `qet_name` | Optional. If omitted, all installed packages are upgraded. |

For `appimage`, `deb`, and `rpm` methods, the new file is downloaded to a `.tmp` path and atomically moved into place only on success, preventing corruption.

### Examples

```bash
# Upgrade a single package
qet upgrade @utils/ripgrep

# Upgrade everything
qet upgrade
```

> **Source:** [`qet/cli.py` L259–L273](../qet/cli.py#L259-L273) · [`qet/commands.py` — `upgrade_package()`](../qet/commands.py#L208-L287)

---

## `qet list`

Lists all currently installed packages.

```
qet list [--json]
```

| Flag | Description |
|---|---|
| `--json` | Output as machine-readable JSON instead of a formatted table. |

The current state is computed by replaying the event log — installs add entries, successful removes delete them.

### Examples

```bash
# Human-readable table
qet list

# JSON for scripting
qet list --json | jq '.[].qet_name'
```

### Sample output

```
           Currently Installed Packages
┌─────────────────────┬──────────┬──────────────────┬──────────────┐
│ Package Name        │ Method   │ Install Date     │ Details      │
├─────────────────────┼──────────┼──────────────────┼──────────────┤
│ @utils/htop         │ apt      │ 2026-07-15 10:23 │ htop         │
│ @microsoft/vscode   │ flatpak  │ 2026-07-15 11:05 │ com.visual…  │
└─────────────────────┴──────────┴──────────────────┴──────────────┘
```

> **Source:** [`qet/cli.py` L177–L203](../qet/cli.py#L177-L203) · [`qet/commands.py` — `list_installed()`](../qet/commands.py#L355-L370)

---

## `qet search`

Searches the local definitions database for matching package names.

```
qet search <query>
```

| Argument | Description |
|---|---|
| `query` | A substring to search for in package names (case-insensitive). |

### Examples

```bash
qet search vscode
# Found 1 package(s) matching 'vscode':
#   - @microsoft/vscode

qet search ai
# Found 2 package(s) matching 'ai':
#   - @ai/lm-studio
#   - @ai/unsloth
```

> **Source:** [`qet/cli.py` L168–L175](../qet/cli.py#L168-L175) · [`qet/commands.py` — `search_packages()`](../qet/commands.py#L318-L328)

---

## `qet info`

Displays all available installation methods for a package.

```
qet info <qet_name>
```

### Examples

```bash
qet info @utils/ripgrep
# Package: @utils/ripgrep
# Available installation methods:
#   - apt:    package_name='ripgrep'
#   - dnf:    package_name='ripgrep'
#   - pacman: package_name='ripgrep'
#   - cargo:  package_name='ripgrep'
#   - brew:   package_name='ripgrep'
```

> **Source:** [`qet/cli.py` L159–L166](../qet/cli.py#L159-L166) · [`qet/commands.py` — `info_package()`](../qet/commands.py#L306-L315)

---

## `qet audit`

Displays the full history of install/remove events.

```
qet audit [qet_name] [--since YYYY-MM-DD] [--json]
```

| Argument / Flag | Description |
|---|---|
| `qet_name` | Optional. Filter events to a specific package. |
| `--since YYYY-MM-DD` | Optional. Only show events on or after this date. |
| `--json` | Output as machine-readable JSON. |

### Examples

```bash
# Full history
qet audit

# History for a single package
qet audit @microsoft/vscode

# Only recent events
qet audit --since 2026-07-01

# Combined filters
qet audit @utils/htop --since 2026-01-01 --json
```

### Sample output

```
                         System Audit Log
┌─────────────────┬─────────┬─────────┬─────────────────────┬──────────┬──────────┐
│ Timestamp       │ Action  │ Status  │ Package             │ Method   │ Details  │
├─────────────────┼─────────┼─────────┼─────────────────────┼──────────┼──────────┤
│ 2026-07-15 10:23│ install │ success │ @utils/htop         │ apt      │ htop     │
│ 2026-07-15 11:05│ install │ success │ @microsoft/vscode   │ flatpak  │ com.vi…  │
└─────────────────┴─────────┴─────────┴─────────────────────┴──────────┴──────────┘
```

> **Source:** [`qet/cli.py` L205–L238](../qet/cli.py#L205-L238) · [`qet/commands.py` — `get_history()`](../qet/commands.py#L373-L386)

---

## `qet init`

Analyses the current system and writes an optimised `conf.toml`.

```
qet init
```

No arguments. Run this once after installation, or again after adding a new package manager to your system.

> **Source:** [`qet/cli.py` L240–L245](../qet/cli.py#L240-L245) · [`qet/commands.py` — `init_environment()`](../qet/commands.py#L444-L528)

---

## `qet method`

Enables or disables an installation method globally.

```
qet method enable <name>
qet method disable <name>
```

| Argument | Description |
|---|---|
| `enable` / `disable` | The action to perform. |
| `name` | The method name (e.g. `snap`, `cargo`, `pip`). |

- **`enable`**: Removes the method from `exclude` and appends it to `priority`.
- **`disable`**: Removes the method from `priority` and adds it to `exclude`.

### Examples

```bash
# Stop qet from ever using snap
qet method disable snap

# Allow cargo-based installations
qet method enable cargo
```

> **Source:** [`qet/cli.py` L247–L253](../qet/cli.py#L247-L253) · [`qet/commands.py` — `method_enable()` / `method_disable()`](../qet/commands.py#L420-L441)

---

## `qet define`

Manually adds or updates a package definition in the local database.

```
qet define <qet_name> <method> <value>
```

| Argument | Description |
|---|---|
| `qet_name` | The canonical qet name (e.g. `@utils/mytool`). |
| `method` | The installation method (`apt`, `appimage`, `script`, etc.). |
| `value` | For URL-based methods (`appimage`, `script`, `deb`, `rpm`): a download URL. For all others: the package name. |

### Examples

```bash
# Add an apt definition for a custom tool
qet define @myorg/mytool apt my-tool-package

# Add an AppImage definition
qet define @video/obs appimage https://github.com/obsproject/obs-studio/releases/download/30.2.3/OBS-Studio-30.2.3-x86_64.AppImage

# Add a pip definition
qet define @python/black pip black
```

> **Source:** [`qet/cli.py` L255–L257](../qet/cli.py#L255-L257) · [`qet/commands.py` — `define_package()`](../qet/commands.py#L401-L412)

---

## `qet snapshot`

Exports the current qet state as a Qetfile TOML string (printed to stdout).

```
qet snapshot [> Qetfile]
```

### Examples

```bash
# Print to terminal
qet snapshot

# Save to a Qetfile in the current directory
qet snapshot > Qetfile

# Save to home directory
qet snapshot > ~/dotfiles/Qetfile
```

> **Source:** [`qet/cli.py` L275–L276](../qet/cli.py#L275-L276) · [`qet/commands.py` — `get_snapshot_data()`](../qet/commands.py#L290-L303)

---

## `qet sync`

Applies a Qetfile to the system by installing any listed packages that are not already installed. Already-installed packages are skipped cleanly.

```
qet sync [--file PATH] [-y]
```

| Flag | Description |
|---|---|
| `--file PATH` | Path to the Qetfile to read. Defaults to `~/.config/qet/Qetfile`. |
| `-y`, `--yes` | Skip confirmation prompts (including script-execution security warnings). |

### Behaviour

1. Reads and parses the Qetfile at `--file` (or `~/.config/qet/Qetfile`).
2. Compares every `[[packages]]` entry against the current install log.
3. For each missing package, runs the same installation logic as `qet add`, including method priority, fallback, and security confirmation.
4. Prints a structured summary: installed ✓, skipped ─, failed ✗.
5. Exits with code `1` if any packages failed to install.

### Examples

```bash
# Apply ./Qetfile in the current directory
qet sync

# Apply a Qetfile at a custom path
qet sync --file ~/dotfiles/Qetfile

# Non-interactive (e.g. CI, bootstrap scripts)
qet sync -y
qet sync --file ~/dotfiles/Qetfile -y
```

### Sample output

```
Installed 2 package(s):
  ✓ @utils/ripgrep
  ✓ @python/uv

Skipped 1 already-installed package(s):
  ─ @utils/htop
```

> **Source:** [`qet/cli.py` — sync handler](../qet/cli.py) · [`qet/commands.py` — `sync_from_qetfile()`](../qet/commands.py)

---

## `qet update`

*(Defined but not yet implemented.)*

Will update the local package definitions database from a remote source.

```bash
qet update
```

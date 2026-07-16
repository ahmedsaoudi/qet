# Configuration Reference

qet's configuration lives in `~/.config/qet/conf.toml`. It is created automatically with sensible defaults on first run (or after `qet init`).

> **Source:** [`qet/config.py`](../qet/config.py)

---

## File Location

```
~/.config/qet/conf.toml
```

---

## Full Example

```toml
priority = ["apt", "flatpak", "snap", "pip", "cargo", "appimage", "script", "deb"]
exclude  = ["dnf", "pacman", "zypper", "brew", "uvx", "npm", "rpm"]

[defaults]
appimage_dir              = "~/.local/bin"
download_tool             = "curl"
require_confirmation_for  = ["script"]
auto_search               = true
auto_fallback             = false
```

---

## Top-Level Keys

### `priority`

An **ordered list** of installation methods that qet will consider and try, in the order listed.

- When installing a package, qet picks the **first method** in `priority` that is both available in the package's definition and not in `exclude`.
- If that method fails, qet tries the **next matching candidate**, and so on.
- If `--using` is passed on the command line, `priority` is ignored for that invocation.

```toml
priority = ["apt", "flatpak", "pip", "cargo", "appimage", "script", "deb"]
```

**Known method names:** `apt`, `dnf`, `pacman`, `zypper`, `snap`, `flatpak`, `brew`, `npm`, `pip`, `uvx`, `cargo`, `deb`, `rpm`, `script`, `appimage`

### `exclude`

A list of methods that qet will **never use**, regardless of what is in `priority`.

```toml
exclude = ["snap", "npm"]
```

> Tip: Use `qet method disable snap` instead of editing this file by hand.

---

## `[defaults]` Section

### `appimage_dir`

Directory where AppImage files are saved.

```toml
appimage_dir = "~/.local/bin"
```

Tilde expansion is applied. The directory is created automatically if it does not exist.

### `qetfile_path`

Path to the Qetfile that `qet add`, `qet remove`, and `qet sync` use.

```toml
qetfile_path = "~/.config/qet/Qetfile"
```

Tilde expansion is applied. Change this to keep your Qetfile somewhere else — for example in a dotfiles repo:

```toml
qetfile_path = "~/dotfiles/Qetfile"
```

> **Note:** This key is written automatically the first time you run `qet init`, so you will always find it in `conf.toml` with a sensible default you can then edit freely.

### `download_tool`

The HTTP download tool used for `appimage`, `deb`, `rpm`, and `script` methods.

```toml
download_tool = "curl"   # or "wget"
```

| Tool | Command template (with destination) | Command template (piped to bash) |
|---|---|---|
| `curl` (default) | `curl -fsSL <url> -o <dest>` | `curl -fsSL <url> \| sudo bash` |
| `wget` | `wget -q <url> -O <dest>` | `wget -qO- <url> \| sudo bash` |

> **Source:** [`qet/executor.py` — `_build_download_command()`](../qet/executor.py#L9-L20)

### `require_confirmation_for`

A list of methods that must ask for explicit confirmation before executing. This is a safety net for methods that run arbitrary code from the internet.

```toml
require_confirmation_for = ["script"]
```

The default is `["script"]`. You can add `"appimage"` or other methods if you want extra confirmation. Pass `-y` / `--yes` to `qet add` to bypass these prompts in non-interactive environments.

### `auto_search`

If `true` (default), when a package is not found in the definitions database, qet automatically queries all available system managers to see if they know the package.

```toml
auto_search = true
```

### `auto_fallback`

If `true`, and `auto_search` finds the package in a system manager, qet installs it automatically without prompting. Defaults to `false` (qet will ask first).

```toml
auto_fallback = false
```

---

## Method Priority — How `qet init` Decides

`qet init` scans your system and builds `priority` using the following logic:

1. **System manager first** — the first of `apt`, `dnf`, `pacman`, `zypper` found is always placed at index 0.
2. **Sandbox managers** — on Debian/Ubuntu (`apt`-based) systems, `snap` comes before `flatpak`; on all others, `flatpak` comes first.
3. **Language managers** — `brew`, `uvx`, `pip`, `cargo` are added if detected.
4. **Abstract methods** — `appimage` and `script` are always included; `deb` is added on `apt` systems, `rpm` on `dnf` systems.
5. **Exclude** — everything known that did not make it into `priority`.

> **Source:** [`qet/commands.py` — `init_environment()`](../qet/commands.py#L444-L528)

---

## Editing Methods via CLI

Rather than hand-editing `conf.toml`, use the `qet method` command:

```bash
# Disable a method globally
qet method disable snap

# Re-enable it
qet method enable snap
```

Changes are written atomically to avoid corruption.

> **Source:** [`qet/commands.py` — `method_enable()` / `method_disable()`](../qet/commands.py#L420-L441)

---

## Default Configuration

If `conf.toml` does not exist, qet creates it with the following defaults:

```python
DEFAULT_CONF = {
    "priority": [
        "appimage", "flatpak", "apt", "dnf", "pacman",
        "pip", "uvx", "cargo", "brew", "deb", "rpm", "script", "snap",
    ],
    "exclude": ["snap"],
    "defaults": {
        "appimage_dir": "~/.local/bin",
        "require_confirmation_for": ["script"],
        "auto_search": True,
        "auto_fallback": False,
    },
}
```

> **Source:** [`qet/config.py` — `DEFAULT_CONF`](../qet/config.py#L22-L45)

---

## Other Configuration Files

### `~/.local/share/qet/install-logs.toml`

An **append-only** event log. qet replays this file to determine which packages are currently installed. Never edit this by hand.

Structure:
```toml
[[events]]
timestamp = "2026-07-15T10:23:00+00:00"
action    = "install"
qet_name  = "@utils/htop"
status    = "success"
method    = "apt"
details   = "htop"
```

### `~/.config/qet/Qetfile`

The **global Qetfile** — automatically kept in sync by `qet add` and `qet remove`. See the [Qetfile guide](./qetfile.md).

### `~/.local/share/qet/definitions.toml`

The **local definitions database** — maps qet names to installation methods. See the [Package Definitions guide](./package-definitions.md).

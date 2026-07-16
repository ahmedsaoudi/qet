# Getting Started with qet

## Prerequisites

- **Linux** (any modern distribution)
- **Python ≥ 3.8**
- At least one native package manager already installed (`apt`, `dnf`, `pacman`, etc.)

---

## Installation

### From source (recommended during early development)

```bash
# Clone the repository
git clone https://github.com/your-org/qet.git
cd qet

# Install into your active Python environment
pip install -e .
```

### Using `uv` (fastest)

```bash
git clone https://github.com/your-org/qet.git
cd qet
uv pip install -e .
```

After either method, the `qet` binary is available in your shell:

```bash
qet --help
```

---

## Docker (Sandbox)

A `Dockerfile` is provided for safe, isolated testing without touching your real system.

```bash
# Build the image
docker build -t qet-sandbox .

# Open an interactive shell inside the sandbox
docker run -it --rm qet-sandbox

# Inside the container:
qet init
qet add @utils/htop
```

The container runs as a non-root user (`qetuser`) with passwordless `sudo`, matching a typical Linux desktop environment.

> **Source:** [`Dockerfile`](../Dockerfile) — `python:3.11-slim-bookworm` base, includes `curl`, `wget`, `git`, `uv`.

---

## First-Time Setup

Run `qet init` immediately after installing to let qet analyse your environment and configure the optimal priority list:

```bash
qet init
```

What `init` does:
1. Detects which package managers are available on your system (`apt`, `dnf`, `pacman`, `snap`, `flatpak`, `brew`, `pip`, `uvx`, `cargo`).
2. Picks the primary system manager (the first of `apt`, `dnf`, `pacman`, `zypper` that is available).
3. Orders sandbox managers (`snap`/`flatpak`) by distro conventions — Ubuntu-based systems prefer `snap` first; all others prefer `flatpak`.
4. Appends any additional detected managers (`brew`, `uvx`, `pip`, `cargo`).
5. Writes the result to `~/.config/qet/conf.toml`.

Example output on an Ubuntu machine:

```
priority = ["apt", "snap", "flatpak", "pip", "cargo", "appimage", "script", "deb"]
exclude  = ["dnf", "pacman", "zypper", "brew", "uvx", "rpm"]
```

> **Source:** [`qet/commands.py` — `init_environment()`](../qet/commands.py#L444-L528)

---

## Quick-Start Walkthrough

### 1 — Search for a package

```bash
qet search vscode
# Found 1 package(s) matching 'vscode':
#   - @microsoft/vscode
```

### 2 — See what methods are available

```bash
qet info @microsoft/vscode
# Package: @microsoft/vscode
# Available installation methods:
#   - apt:     package_name='code'
#   - dnf:     package_name='code'
#   - snap:    package_name='code'
#   - flatpak: package_name='com.visualstudio.code'
```

### 3 — Install it

```bash
qet add @microsoft/vscode
# qet automatically picks the best method from your priority list
```

Or force a specific method:

```bash
qet add @microsoft/vscode --using flatpak
```

### 4 — List installed packages

```bash
qet list
```

### 5 — Upgrade everything

```bash
qet upgrade
```

### 6 — Remove a package

```bash
qet remove @microsoft/vscode
```

### 7 — Export your setup

```bash
qet snapshot > Qetfile
```

---

## File Locations

| File | Path | Purpose |
|---|---|---|
| Configuration | `~/.config/qet/conf.toml` | Priority list, exclusions, defaults |
| Install log | `~/.local/share/qet/install-logs.toml` | Append-only event history |
| Definitions DB | `~/.local/share/qet/definitions.toml` | Package name → method mappings |
| Global Qetfile | `~/.config/qet/Qetfile` | Auto-synced desired-state manifest |
| Methods config | `/usr/share/qet/methods.toml` | Shell command templates per manager |

> **Source:** [`qet/config.py` — path constants](../qet/config.py#L9-L18)

# Package Definitions

The **definitions database** is a TOML file that maps canonical qet names to the installation methods available for each package.

- **User-local path:** `~/.local/share/qet/definitions.toml`
- **Example / seed file:** [`example_definitions.toml`](../example_definitions.toml)

> **Source:** [`qet/config.py` — `get_definitions()`](../qet/config.py#L165-L173)

---

## Package Name Format

Every package has a **canonical qet name** in the form:

```
@<scope>/<package>
```

| Part | Description | Example |
|---|---|---|
| `@scope` | Groups related packages by vendor, language, or category | `@microsoft`, `@python`, `@utils` |
| `/package` | The tool or library name | `vscode`, `uv`, `htop` |

Scopes are free-form; use whatever makes sense for your organisation.

---

## Definition File Format

Each entry is a TOML table keyed by the qet name. Inside, each key is a method name, and its value is a table with the method-specific fields.

```toml
["@scope/package"]
<method> = { <field> = "<value>" }
```

### `package_name` field

Used by all registry-based managers (`apt`, `dnf`, `pacman`, `zypper`, `snap`, `flatpak`, `brew`, `npm`, `pip`, `uvx`, `cargo`).

```toml
["@utils/ripgrep"]
apt    = { package_name = "ripgrep" }
dnf    = { package_name = "ripgrep" }
pacman = { package_name = "ripgrep" }
cargo  = { package_name = "ripgrep" }
brew   = { package_name = "ripgrep" }
```

### `source_url` field

Used by URL-based methods (`appimage`, `script`, `deb`, `rpm`). qet downloads the file and handles it appropriately.

```toml
["@ai/lm-studio"]
appimage = { source_url = "https://releases.lmstudio.ai/linux/latest/LM_Studio.AppImage" }

["@python/uv"]
script = { source_url = "https://astral.sh/uv/install.sh" }

["@ai/unsloth"]
pip    = { package_name = "unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git" }
script = { source_url = "https://raw.githubusercontent.com/unslothai/unsloth/main/install.sh" }
```

---

## Supported Methods and Their Fields

| Method | Field | Description |
|---|---|---|
| `apt` | `package_name` | Debian/Ubuntu package name |
| `dnf` | `package_name` | Fedora/RHEL package name |
| `pacman` | `package_name` | Arch Linux package name |
| `zypper` | `package_name` | openSUSE package name |
| `snap` | `package_name` | Snap store name |
| `flatpak` | `package_name` | Flatpak application ID (e.g. `com.visualstudio.code`) |
| `brew` | `package_name` | Homebrew formula/cask name |
| `npm` | `package_name` | npm package name (installed globally) |
| `pip` | `package_name` | PyPI package name (supports extras and VCS URLs) |
| `uvx` | `package_name` | Package name for `uvx` / uv tool |
| `cargo` | `package_name` | Crates.io package name |
| `appimage` | `source_url` | Direct download URL for the `.AppImage` file |
| `deb` | `source_url` | Direct download URL for the `.deb` file |
| `rpm` | `source_url` | Direct download URL for the `.rpm` file |
| `script` | `source_url` | URL of a shell script to download and execute |

---

## Adding Definitions

### Via CLI (recommended)

```bash
# Registry-based method (package_name)
qet define @myorg/mytool apt my-package-name

# URL-based method (source_url)
qet define @video/obs appimage https://example.com/obs.AppImage
```

The `define` command automatically infers whether to use `package_name` or `source_url` based on the method type.

> **Source:** [`qet/commands.py` — `define_package()`](../qet/commands.py#L401-L412)

### Manually editing the file

Open `~/.local/share/qet/definitions.toml` in any text editor and add TOML entries. Ensure the file remains valid TOML before saving.

### Seeding from the example file

The bundled [`example_definitions.toml`](../example_definitions.toml) is automatically used to seed your local database if `definitions.toml` does not exist yet. You can also copy it manually:

```bash
cp example_definitions.toml ~/.local/share/qet/definitions.toml
```

---

## Full Example from the Seed File

```toml
# @microsoft/vscode — available via four methods
["@microsoft/vscode"]
apt     = { package_name = "code" }
dnf     = { package_name = "code" }
snap    = { package_name = "code" }
flatpak = { package_name = "com.visualstudio.code" }

# @web/nodejs — system managers + NVM script
["@web/nodejs"]
apt    = { package_name = "nodejs" }
dnf    = { package_name = "nodejs" }
pacman = { package_name = "nodejs" }
snap   = { package_name = "node" }
script = { source_url = "https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh" }

# @ai/lm-studio — AppImage only
["@ai/lm-studio"]
appimage = { source_url = "https://releases.lmstudio.ai/linux/latest/LM_Studio.AppImage" }
flatpak  = { package_name = "ai.lmstudio.LMStudio" }

# @python/uv — script or pip or brew
["@python/uv"]
script = { source_url = "https://astral.sh/uv/install.sh" }
pip    = { package_name = "uv" }
brew   = { package_name = "uv" }
```

---

## How qet Uses the Definitions at Runtime

When you run `qet add @utils/ripgrep`:

1. [`config.get_definitions()`](../qet/config.py#L165-L173) loads `~/.local/share/qet/definitions.toml`.
2. [`commands.resolve_method_candidates()`](../qet/commands.py#L17-L44) intersects the package's available methods with the `priority` list (excluding anything in `exclude`).
3. The resulting ordered list of candidates is passed to `add_package()`, which tries them in order.

```
definitions["@utils/ripgrep"] = {apt, dnf, pacman, cargo, brew}
priority (from conf.toml)      = [apt, flatpak, pip, cargo]
exclude                        = [snap]

→ candidates = [apt, cargo]   (intersection, in priority order)
→ qet tries apt first; if it fails, tries cargo.
```

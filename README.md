# qet - A Meta Package Manager

`qet` is a command-line tool for Linux that acts as a meta package manager. It provides a unified interface to manage packages from different sources, such as system package managers (apt, dnf, pacman), language-specific managers (pip, npm), and other distribution formats (AppImage, Snap, Flatpak).

## How It Works

`qet` works by maintaining a central manifest of packages you've installed. It reads a database of package definitions that map a single `qet` package name to multiple installation methods across different package managers.

When you ask `qet` to install a package, it:
1.  Looks up the package in its definitions database.
2.  Checks which package managers are available on your system.
3.  Selects the best available method based on a configurable priority list.
4.  Executes the appropriate command to install the package using the native manager.

This allows you to manage your applications and tools with a consistent set of commands (`qet add`, `qet remove`), regardless of how they are installed.

## What qet Is Not

-   **`qet` is not a package manager.** It does not have its own package repository, build system, or distribution infrastructure. It is a meta-manager that sits on top of other package managers.
-   **`qet` does not replace your system's package manager.** You will still need `apt`, `dnf`, `pacman`, or others to be installed and working. `qet` simply provides a unified interface to them.
-   **`qet` does not resolve dependencies across different managers.** If you install a package with `npm`, `qet` will not use `apt` to install its system-level dependencies.

## Installation

To install `qet`, you can clone this repository and run the installation script:

```bash
git clone https://github.com/your-username/qet.git
cd qet
sudo ./install.sh
```

## Usage Examples

### Adding a Package

You can add a package using its canonical `qet` name. `qet` will automatically determine the best installation method.

```bash
# Install the 'htop' utility
qet add @utils/htop
```

This might translate to one of the following commands, depending on your system and configuration:

-   On Debian/Ubuntu: `sudo apt-get install -y htop`
-   On Fedora/CentOS: `sudo dnf install -y htop`
-   On Arch Linux: `sudo pacman -S --noconfirm htop`

### Removing a Package

To remove a package, use the `remove` command with the same `qet` name.

```bash
qet remove @utils/htop
```

### Specifying an Installation Method

If a package is available from multiple sources, you can manually specify which one to use with the `--using` flag.

```bash
# Install Visual Studio Code as a Snap package
qet add @editors/vscode --using snap
```

### Syncing with a Qetfile

You can define a list of desired packages in a `Qetfile` and use the `sync` command to install all of them. This is useful for bootstrapping a new system.

Create a file named `Qetfile` with the following content:

```toml
# Qetfile

[[packages]]
qet_name = "@utils/htop"
method = "apt"

[[packages]]
qet_name = "@editors/vscode"
method = "snap"

[[packages]]
qet_name = "@dev/nodejs"
method = "npm"
```

Then, run the `sync` command in the same directory:

```bash
qet sync
```

`qet` will analyze the `Qetfile` and install any missing packages.

### Creating a Snapshot

You can generate a `Qetfile` from the packages you've already installed with `qet`. This is useful for saving your current setup.

```bash
qet snapshot > Qetfile
```

This will create a `Qetfile` in the current directory containing all your `qet`-managed packages.

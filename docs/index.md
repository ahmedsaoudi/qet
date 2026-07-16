# qet Documentation

> **⚠ Early Development Warning:** `qet` is in an early stage of development. Use it with caution, preferably in virtual machines or non-essential systems.

`qet` is a meta package manager for Linux that provides a single, unified interface to install, remove, upgrade, and track software from any package manager — `apt`, `dnf`, `pacman`, `snap`, `flatpak`, `pip`, `cargo`, and more.

---

## Documentation Map

| Document | Description |
|---|---|
| [Getting Started](./getting-started.md) | Installation, first-time setup, and a quick-start walkthrough |
| [CLI Reference](./cli-reference.md) | Complete reference for every `qet` command and its flags |
| [Configuration](./configuration.md) | `conf.toml`, priority lists, exclusions, and default settings |
| [Package Definitions](./package-definitions.md) | How to write and manage the `definitions.toml` database |
| [Qetfile](./qetfile.md) | Declarative environment files for reproducible setups |
| [Architecture](./architecture.md) | Source-code map, module responsibilities, and data flow |
| [Error Reference](./error-reference.md) | All exceptions, what triggers them, and how to fix them |

---

## At a Glance

```
qet add @utils/htop          # install htop via the best available method
qet remove @utils/htop       # remove it
qet upgrade                  # upgrade all qet-managed packages
qet list                     # see everything qet manages
qet audit                    # full install/remove history
qet snapshot > Qetfile       # export current state as a Qetfile
qet sync                     # apply a Qetfile to the system
```

---

## Key Concepts

| Concept | Meaning |
|---|---|
| **qet name** | A scoped identifier like `@scope/package` (e.g. `@microsoft/vscode`) |
| **method** | The underlying manager used to install (`apt`, `flatpak`, `pip`, …) |
| **definitions** | A TOML database mapping qet names → available methods |
| **priority list** | Ordered list of methods qet tries, in preference order |
| **Qetfile** | A TOML manifest declaring the desired package state of a system |
| **install log** | An append-only event log used to calculate the current state |

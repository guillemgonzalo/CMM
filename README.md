# CMM - Cyberpunk Mod Manager for macOS

Small mod installer for the **native macOS build** of Cyberpunk 2077 (GOG or Steam).
Think "Mod Organizer 2, but tiny": it installs Nexus-style zips, remembers exactly which files
each mod put in the game, and removes only those files later.

Nexus zips use the Windows layout (`archive/pc/mod`). The macOS game reads `archive/Mac/mod`,
so CMM rewrites that path while installing. Windows-only files (`.dll`, `.exe`, `bin/`) are
skipped and reported, because a macOS build cannot load them.

## Requirements

macOS, [uv](https://docs.astral.sh/uv/) (`brew install uv`) and the native macOS build of Cyberpunk 2077.

## Run it

```sh
git clone https://github.com/guillemgonzalo/CMM && cd CMM
uv run cmm            # opens the menu
```

Optional: install it as a global command, then run `cmm` from anywhere.

```sh
uv tool install .     # update later with: uv tool install --reinstall .
```

## Menu

Drop mod archives (`.zip`, `.7z`, `.rar`) in the `mods/` folder, run `cmm` and pick:

```
1) Install  2) Reorder  3) Uninstall  4) Run  5) Exit
```

- **Install** lists what is in `mods/`; installed archives move to `mods/installed/`.
- **Reorder** changes load order (last wins) by renumbering archives with `NNN_` prefixes.
- **Uninstall** removes only that mod's files and moves its archive back to `mods/`.
- **Run** starts the game (refuses if it is already running). Set `CMM_LAUNCHER` to a script to launch
  it your own way (e.g. with a mod loader); otherwise the plain game app is opened.

Install, reorder and uninstall are refused while the game is running.

## Commands

```sh
cmm install "Some Mod-1234-1-0.zip"      # install (.zip, .7z or .rar)
cmm install "Some Mod.zip" --skip r6/scripts   # leave out files under a prefix
cmm list                                  # installed mods, in load order
cmm uninstall "Some Mod"                  # remove only that mod's files
cmm --game "/path/to/Cyberpunk 2077" list # other game folder
```

(Use `uv run cmm ...` if you did not install it globally.)

Settings: `$CMM_GAME` game folder (default `/Applications/Cyberpunk 2077`), `$CMM_HOME` folder that
holds `mods/` (default `~/CMM`), `$CMM_LAUNCHER` launch script. State is stored in
`<game>/.cmm/manifest.json`.

If a file already exists (from another mod or untracked) nothing is installed and the
conflicts are listed; pass `--force` to overwrite.

## Design

```
menu.py       interactive menu;  library.py  the mods/ drop folder
cli.py        composition root: wires classes, maps errors to exit codes
installer.py  use cases (install / uninstall / list / reorder), depends only on abstractions
mapping.py    PathMapper protocol + MacPathMapper (strategy)
archive.py    ModArchive protocol + ZipModArchive + TarModArchive (7z/rar via macOS bsdtar), open_archive()
store.py      ManifestStore protocol + JsonManifestStore
model.py      dataclasses;  errors.py  domain errors
```

## Development

```sh
uv sync
uv run pytest
```

## Not done yet

FOMOD installers, a GUI. RAR support depends on what libarchive in macOS reads (RAR5 and most RAR4 work; very new variants may not). Load order was tested and did not
matter for the cases found so far.

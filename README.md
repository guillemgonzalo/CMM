# CMM - Cyberpunk Mod Manager for macOS

Small mod installer for the **native macOS build** of Cyberpunk 2077 (GOG or Steam).
Think "Mod Organizer 2, but tiny": it installs Nexus-style zips, remembers exactly which files
each mod put in the game, and removes only those files later.

Nexus zips use the Windows layout (`archive/pc/mod`). The macOS game reads `archive/Mac/mod`,
so CMM rewrites that path while installing. Windows-only files (`.dll`, `.exe`, `bin/`) are
skipped and reported, because a macOS build cannot load them.

## Usage

```sh
uv run cmm install "Some Mod-1234-1-0.zip"      # install (.zip, .7z or .rar)
uv run cmm list                                  # installed mods
uv run cmm uninstall "Some Mod"                  # remove only that mod's files
uv run cmm --game "/path/to/Cyberpunk 2077" list # other game folder
```

The game folder defaults to `$CMM_GAME` or `/Applications/Cyberpunk 2077`.
State is stored in `<game>/.cmm/manifest.json`.

If a file already exists (from another mod or untracked) nothing is installed and the
conflicts are listed; pass `--force` to overwrite.

## Design

```
cli.py        composition root: wires classes, maps errors to exit codes
installer.py  use cases (install / uninstall / list), depends only on abstractions
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

Load-order control, FOMOD installers, a GUI. RAR support depends on what libarchive in macOS reads (RAR5 and most RAR4 work; very new variants may not). Load order was tested and did not
matter for the cases found so far.

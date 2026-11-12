"""Composition root: wires concrete classes together and translates errors to exit codes."""

import argparse
import os
import sys
from pathlib import Path

from .archive import open_archive
from .errors import CmmError, ConflictError
from .installer import ModInstaller
from .library import Library
from .mapping import MacPathMapper
from .menu import run_menu
from .store import JsonManifestStore

DEFAULT_GAME = "/Applications/Cyberpunk 2077"


def build_installer(game: Path) -> ModInstaller:
    return ModInstaller(game, MacPathMapper(), JsonManifestStore(game / ".cmm" / "manifest.json"))


def parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="cmm", description="Cyberpunk Mod Manager for macOS")
    ap.add_argument(
        "--game",
        type=Path,
        default=Path(os.environ.get("CMM_GAME", DEFAULT_GAME)),
        help="game folder (default: $CMM_GAME or %(default)s)",
    )
    sub = ap.add_subparsers(dest="cmd")
    i = sub.add_parser("install", help="install a mod (.zip, .7z or .rar)")
    i.add_argument("zip", type=Path)
    i.add_argument("--name")
    i.add_argument("--force", action="store_true", help="overwrite files that already exist")
    i.add_argument(
        "--skip",
        action="append",
        default=[],
        metavar="PREFIX",
        help="skip files under PREFIX (e.g. r6/scripts)",
    )
    u = sub.add_parser("uninstall", help="remove a mod and only its files")
    u.add_argument("name")
    sub.add_parser("list", help="show installed mods")
    return ap


def library(args: argparse.Namespace) -> Library:
    return Library(Path(os.environ.get("CMM_HOME", Path.home() / "CMM")))


def run(args: argparse.Namespace) -> None:
    installer = build_installer(args.game)
    if args.cmd is None:
        run_menu(installer, library(args), args.game)
    elif args.cmd == "install":
        report = installer.install(open_archive(args.zip), args.name, args.force, tuple(args.skip))
        library(args).mark_installed(args.zip.resolve())
        print(f"installed {report.mod.name}: {len(report.mod.files)} files")
        for s in report.skipped:
            print(f"  skipped (Windows-only or not a game file): {s}")
    elif args.cmd == "uninstall":
        mod = installer.uninstall(args.name)
        library(args).restore(mod.source)
        print(f"removed {mod.name}")
    else:
        for m in installer.installed():
            print(f"{m.name}\t{len(m.files)} files\t{m.source}")


def main(argv: list[str] | None = None) -> None:
    try:
        run(parser().parse_args(argv))
    except ConflictError as e:
        for path, owner in e.conflicts.items():
            print(f"conflict: {path} ({owner})", file=sys.stderr)
        sys.exit(f"nothing installed: {e}")
    except CmmError as e:
        sys.exit(f"error: {e}")

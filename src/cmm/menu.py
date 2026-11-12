"""Interactive text menu. Thin: every action delegates to the installer, library or launcher."""

import os
import subprocess
from pathlib import Path

from .archive import open_archive
from .errors import CmmError, ConflictError
from .installer import ModInstaller
from .library import Library


def game_running() -> bool:
    return subprocess.run(["pgrep", "-x", "Cyberpunk2077"], capture_output=True, check=False).returncode == 0


def launch(game: Path) -> None:
    if game_running():
        print("game already running")
        return
    script = os.environ.get("CMM_LAUNCHER")
    cmd = [script] if script else ["open", str(game / "Cyberpunk2077.app")]
    subprocess.Popen(cmd, start_new_session=True)
    print("launching: " + " ".join(cmd))


def pick(title: str, items: list[str]) -> int | None:
    if not items:
        print("  (nothing)")
        return None
    for n, item in enumerate(items, 1):
        print(f"  {n}) {item}")
    raw = input(f"{title} [number, enter = cancel]: ").strip()
    return int(raw) - 1 if raw.isdigit() and 0 < int(raw) <= len(items) else None


def show(installer: ModInstaller) -> None:
    print("\nLoad order (last wins):")
    for n, m in enumerate(installer.installed(), 1):
        print(f"  {n:>2}. {m.name}")


def action(choice: str, installer: ModInstaller, lib: Library, game: Path) -> None:
    mods = installer.installed()
    if choice == "1":
        files = lib.pending()
        i = pick(f"Install (drop archives in {lib.drop})", [f.name for f in files])
        if i is not None:
            report = installer.install(open_archive(files[i]))
            lib.mark_installed(files[i])
            print(f"installed {report.mod.name}: {len(report.mod.files)} files")
    elif choice == "2":
        i = pick("Move which mod", [m.name for m in mods])
        d = input("up / down [u/d]: ").strip().lower()
        if i is not None and d in ("u", "d"):
            installer.move(mods[i].name, -1 if d == "u" else 1)
    elif choice == "3":
        i = pick("Uninstall", [m.name for m in mods])
        if i is not None:
            installer.uninstall(mods[i].name)
            lib.restore(mods[i].source)
            print(f"removed {mods[i].name}")
    elif choice == "4":
        launch(game)


def run_menu(installer: ModInstaller, lib: Library, game: Path) -> None:
    while True:
        show(installer)
        print("\n1) Install  2) Reorder  3) Uninstall  4) Run  5) Exit")
        choice = input("> ").strip()
        if choice == "5":
            return
        try:
            if choice in ("1", "2", "3") and game_running():
                print("close the game first")
                continue
            action(choice, installer, lib, game)
        except ConflictError as e:
            print(f"conflicts, nothing installed: {e.conflicts}")
        except CmmError as e:
            print(f"error: {e}")

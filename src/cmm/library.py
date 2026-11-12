"""CMM's own mods folder: drop archives in `mods/`, installed ones are filed under `mods/installed/`."""

import shutil
from pathlib import Path

SUFFIXES = {".zip", ".7z", ".rar"}
HINT = "DROP MODS HERE.txt"


class Library:
    def __init__(self, root: Path):
        self.drop, self.done = root / "mods", root / "mods" / "installed"
        self.done.mkdir(parents=True, exist_ok=True)
        (self.drop / HINT).write_text(
            "Drop mod archives (.zip, .7z, .rar) here, then run `cmm` and pick Install.\n"
        )

    def pending(self) -> list[Path]:
        return sorted(p for p in self.drop.iterdir() if p.suffix.lower() in SUFFIXES)

    def mark_installed(self, path: Path) -> None:
        if path.resolve().parent == self.drop.resolve():
            shutil.move(path, self.done / path.name)

    def restore(self, source: str) -> None:
        if (self.done / source).exists():
            shutil.move(self.done / source, self.drop / source)

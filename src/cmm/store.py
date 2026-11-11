"""Persistence of what is installed. Swappable behind `ManifestStore` (dependency inversion)."""
import json
from pathlib import Path
from typing import Protocol

from .model import InstalledMod


class ManifestStore(Protocol):
    def load(self) -> dict[str, InstalledMod]: ...
    def save(self, mods: dict[str, InstalledMod]) -> None: ...


class JsonManifestStore:
    def __init__(self, path: Path):
        self._path = path

    def load(self) -> dict[str, InstalledMod]:
        if not self._path.exists():
            return {}
        raw = json.loads(self._path.read_text())
        return {n: InstalledMod(n, tuple(d["files"]), d["source"], d["installed_at"]) for n, d in raw.items()}

    def save(self, mods: dict[str, InstalledMod]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        raw = {n: {"files": list(m.files), "source": m.source, "installed_at": m.installed_at}
               for n, m in sorted(mods.items())}
        self._path.write_text(json.dumps(raw, indent=1))

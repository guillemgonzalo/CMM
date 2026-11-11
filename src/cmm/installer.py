"""Use cases: install / uninstall / list. Depends only on abstractions, never on zip or JSON."""
import re
import time
from pathlib import Path

from .archive import ModArchive
from .errors import AlreadyInstalled, ConflictError, NotAGameFolder, NotInstalled
from .mapping import PathMapper
from .model import InstalledMod, InstallReport
from .store import ManifestStore

# Base folders the game expects; never removed even when a mod's removal leaves them empty.
KEEP = frozenset({"archive", "archive/Mac", "archive/Mac/mod", "r6", "r6/scripts", "r6/tweaks",
                  "r6/config", "red4ext", "red4ext/plugins", "engine"})


def default_name(source: str) -> str:
    """'Cool Outfit-123-1-0-99.zip' -> 'Cool Outfit'."""
    stem = Path(source).stem
    return re.sub(r"[-_ ]?\d{3,}.*$", "", stem).strip() or stem


class ModInstaller:
    def __init__(self, game: Path, mapper: PathMapper, store: ManifestStore):
        if not (game / "archive").is_dir():
            raise NotAGameFolder(f"no archive/ folder in {game}")
        self._game, self._mapper, self._store = game, mapper, store

    def installed(self) -> list[InstalledMod]:
        return sorted(self._store.load().values(), key=lambda m: m.name)

    def install(self, archive: ModArchive, name: str | None = None, force: bool = False) -> InstallReport:
        mods = self._store.load()
        name = name or default_name(archive.source)
        if name in mods:
            raise AlreadyInstalled(f"'{name}' is already installed; uninstall it first")
        plan, skipped = self._plan(archive)
        if not force:
            self._check_conflicts(plan.values(), mods)
        for member, rel in plan.items():
            dst = self._game / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes(archive.read(member))
        mod = InstalledMod(name, tuple(plan.values()), archive.source, int(time.time()))
        mods[name] = mod
        self._store.save(mods)
        return InstallReport(mod, skipped)

    def uninstall(self, name: str) -> InstalledMod:
        mods = self._store.load()
        if name not in mods:
            raise NotInstalled(f"not installed: {name}")
        mod = mods.pop(name)
        for rel in mod.files:
            path = self._game / rel
            path.unlink(missing_ok=True)
            self._prune_empty_parents(path)
        self._store.save(mods)
        return mod

    def _plan(self, archive: ModArchive) -> tuple[dict[str, str], list[str]]:
        plan: dict[str, str] = {}
        skipped: list[str] = []
        for member in archive.members():
            rel = self._mapper.map(member)
            if rel is None:
                skipped.append(member)
            else:
                plan[member] = rel
        return plan, skipped

    def _check_conflicts(self, targets, mods: dict[str, InstalledMod]) -> None:
        owners = {f: m.name for m in mods.values() for f in m.files}
        conflicts = {t: owners.get(t, "untracked file") for t in targets if (self._game / t).exists()}
        if conflicts:
            raise ConflictError(conflicts)

    def _prune_empty_parents(self, path: Path) -> None:
        d = path.parent
        while d != self._game and d.relative_to(self._game).as_posix() not in KEEP:
            if not d.is_dir() or any(d.iterdir()):
                return
            d.rmdir()
            d = d.parent

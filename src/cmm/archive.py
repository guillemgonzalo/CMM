"""Reading mod archives. `ModArchive` lets the installer ignore the container format."""

import subprocess
import tempfile
import zipfile
from pathlib import Path
from typing import Protocol

from .errors import CmmError, UnsupportedFormat


class ModArchive(Protocol):
    @property
    def source(self) -> str: ...
    def members(self) -> list[str]: ...
    def read(self, member: str) -> bytes: ...


class ZipModArchive:
    def __init__(self, path: Path):
        self._zip = zipfile.ZipFile(path)
        self._source = path.name

    @property
    def source(self) -> str:
        return self._source

    def members(self) -> list[str]:
        return [i.filename for i in self._zip.infolist() if not i.is_dir()]

    def read(self, member: str) -> bytes:
        return self._zip.read(member)


class TarModArchive:
    """7z / rar (and anything else libarchive reads) through macOS's built-in `bsdtar`.

    Extracts once into a temp folder (bsdtar already refuses `..` and absolute paths), then
    serves files from there. Symlinks are ignored so an archive cannot point outside it.
    """

    def __init__(self, path: Path):
        self._source = path.name
        self._tmp = tempfile.TemporaryDirectory(prefix="cmm-")
        self._root = Path(self._tmp.name)
        done = subprocess.run(
            ["tar", "-xf", str(path), "-C", str(self._tmp.name)], check=False, capture_output=True, text=True
        )
        if done.returncode != 0:
            raise CmmError(f"cannot read {path.name}: {done.stderr.strip() or 'tar failed'}")

    @property
    def source(self) -> str:
        return self._source

    def members(self) -> list[str]:
        return sorted(
            p.relative_to(self._root).as_posix()
            for p in self._root.rglob("*")
            if p.is_file() and not p.is_symlink()
        )

    def read(self, member: str) -> bytes:
        return (self._root / member).read_bytes()


def open_archive(path: Path) -> ModArchive:
    """Pick the reader by file extension."""
    suffix = path.suffix.lower()
    if suffix == ".zip":
        return ZipModArchive(path)
    if suffix in (".7z", ".rar"):
        return TarModArchive(path)
    raise UnsupportedFormat(f"unsupported archive type {suffix or path.name!r} (use .zip, .7z or .rar)")

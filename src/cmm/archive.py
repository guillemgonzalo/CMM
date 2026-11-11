"""Reading mod archives. `ModArchive` lets the installer ignore the container format."""
import zipfile
from pathlib import Path
from typing import Protocol


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

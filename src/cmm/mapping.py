"""Single responsibility: decide where a zip member goes inside the game folder.

`PathMapper` is the abstraction (Strategy); the installer never knows about macOS specifics,
so supporting another layout means adding a class, not editing the installer (open/closed).
"""

from typing import Protocol

from .errors import UnsafeArchive


class PathMapper(Protocol):
    def map(self, member: str) -> str | None:
        """Return the game-relative destination, or None to skip the member."""


class MacPathMapper:
    """Nexus zips are Windows layouts; the macOS build reads archive/Mac instead of archive/pc."""

    windows_only = (".dll", ".exe", ".asi")

    def map(self, member: str) -> str | None:
        parts = member.replace("\\", "/").split("/")
        if member.startswith("/") or ".." in parts or "" in parts[:-1]:
            raise UnsafeArchive(f"unsafe path in archive: {member!r}")
        if len(parts) < 2 or parts[0] == "bin" or member.lower().endswith(self.windows_only):
            return None  # root-level notes, or Windows-only binaries no macOS build can load
        if parts[:2] == ["archive", "pc"]:
            parts[1] = "Mac"
        return "/".join(parts)

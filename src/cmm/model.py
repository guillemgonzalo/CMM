"""Plain data types shared by all layers."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class InstalledMod:
    name: str
    files: tuple[str, ...]
    source: str
    installed_at: int


@dataclass
class InstallReport:
    mod: InstalledMod
    skipped: list[str] = field(default_factory=list)

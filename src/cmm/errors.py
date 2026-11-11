"""Domain errors. The CLI is the only place that turns them into exit codes."""


class CmmError(Exception):
    """Base class for every expected failure."""


class NotAGameFolder(CmmError):
    pass


class UnsafeArchive(CmmError):
    pass


class AlreadyInstalled(CmmError):
    pass


class NotInstalled(CmmError):
    pass


class ConflictError(CmmError):
    def __init__(self, conflicts: dict[str, str]):
        self.conflicts = conflicts
        super().__init__(f"{len(conflicts)} conflicting file(s); use --force to overwrite")

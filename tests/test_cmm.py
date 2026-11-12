import shutil
import subprocess
import zipfile

import pytest

from cmm.archive import ZipModArchive, open_archive
from cmm.cli import build_installer
from cmm.errors import (
    AlreadyInstalled,
    CmmError,
    ConflictError,
    NotAGameFolder,
    UnsafeArchive,
    UnsupportedFormat,
)
from cmm.installer import default_name
from cmm.mapping import MacPathMapper


@pytest.fixture
def game(tmp_path):
    (tmp_path / "game" / "archive" / "Mac" / "mod").mkdir(parents=True)
    return tmp_path / "game"


@pytest.fixture
def mod_zip(tmp_path):
    p = tmp_path / "Cool Outfit-123-1-0-99.zip"
    with zipfile.ZipFile(p, "w") as z:
        z.writestr("archive/pc/mod/a.archive", "x")
        z.writestr("r6/tweaks/a.yaml", "y")
        z.writestr("bin/x64/plugins/p.dll", "d")
        z.writestr("Items Codes.txt", "t")
    return p


def test_install_and_uninstall_roundtrip(game, mod_zip):
    inst = build_installer(game)
    report = inst.install(ZipModArchive(mod_zip))
    assert report.mod.name == "Cool Outfit"
    assert (game / "archive/Mac/mod/a.archive").read_text() == "x"
    assert (game / "r6/tweaks/a.yaml").exists()
    assert not (game / "bin").exists()
    assert sorted(report.skipped) == ["Items Codes.txt", "bin/x64/plugins/p.dll"]
    inst.uninstall("Cool Outfit")
    assert not (game / "archive/Mac/mod/a.archive").exists()
    assert (game / "archive/Mac/mod").is_dir()  # base folders are kept
    assert inst.installed() == []


def test_conflict_needs_force_and_reinstall_is_rejected(game, mod_zip):
    inst = build_installer(game)
    inst.install(ZipModArchive(mod_zip))
    with pytest.raises(AlreadyInstalled):
        inst.install(ZipModArchive(mod_zip))
    with pytest.raises(ConflictError) as e:
        inst.install(ZipModArchive(mod_zip), name="other")
    assert e.value.conflicts["archive/Mac/mod/a.archive"] == "Cool Outfit"
    inst.install(ZipModArchive(mod_zip), name="other", force=True)


def test_zip_slip_rejected():
    with pytest.raises(UnsafeArchive):
        MacPathMapper().map("../evil")


def test_not_a_game_folder(tmp_path):
    with pytest.raises(NotAGameFolder):
        build_installer(tmp_path)


def test_default_name():
    assert (
        default_name("Casual Day Outfit - Archive XL-24351-1-1-1778009202.zip")
        == "Casual Day Outfit - Archive XL"
    )


def _tree(tmp_path):
    src = tmp_path / "src"
    (src / "archive/pc/mod").mkdir(parents=True)
    (src / "archive/pc/mod/a.archive").write_text("x")
    (src / "r6/tweaks").mkdir(parents=True)
    (src / "r6/tweaks/a.yaml").write_text("y")
    return src


def _install_and_check(game, path):
    inst = build_installer(game)
    inst.install(open_archive(path), name="m")
    assert (game / "archive/Mac/mod/a.archive").read_text() == "x"
    assert (game / "r6/tweaks/a.yaml").read_text() == "y"
    inst.uninstall("m")
    assert not (game / "archive/Mac/mod/a.archive").exists()


def test_7z(game, tmp_path):
    src = _tree(tmp_path)
    out = tmp_path / "m.7z"
    subprocess.run(["tar", "--format", "7zip", "-cf", str(out), "-C", str(src), "archive", "r6"], check=True)
    _install_and_check(game, out)


@pytest.mark.skipif(shutil.which("rar") is None, reason="rar not installed")
def test_rar(game, tmp_path):
    src = _tree(tmp_path)
    out = tmp_path / "m.rar"
    subprocess.run(["rar", "a", "-r", "-ep1", "-idq", str(out), "archive", "r6"], cwd=src, check=True)
    _install_and_check(game, out)


def test_unsupported_and_corrupt(tmp_path):
    with pytest.raises(UnsupportedFormat):
        open_archive(tmp_path / "m.tar.gz")
    bad = tmp_path / "bad.7z"
    bad.write_bytes(b"not an archive")
    with pytest.raises(CmmError):
        open_archive(bad)


def test_move_renumbers_archives_and_uninstall_stays_clean(game, tmp_path):
    inst = build_installer(game)
    for n in ("A", "B"):
        p = tmp_path / f"{n}.zip"
        with zipfile.ZipFile(p, "w") as z:
            z.writestr(f"archive/pc/mod/{n}.archive", n)
        inst.install(ZipModArchive(p))
    inst.move("B", -1)
    assert [m.name for m in inst.installed()] == ["B", "A"]
    assert sorted(f.name for f in (game / "archive/Mac/mod").iterdir()) == ["000_B.archive", "001_A.archive"]
    inst.uninstall("B")
    assert [f.name for f in (game / "archive/Mac/mod").iterdir()] == ["001_A.archive"]

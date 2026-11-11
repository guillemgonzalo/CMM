import zipfile
from pathlib import Path

import pytest

from cmm.archive import ZipModArchive
from cmm.cli import build_installer
from cmm.errors import AlreadyInstalled, ConflictError, NotAGameFolder, UnsafeArchive
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
    assert default_name("Casual Day Outfit - Archive XL-24351-1-1-1778009202.zip") == "Casual Day Outfit - Archive XL"

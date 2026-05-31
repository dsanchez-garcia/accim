"""Tests for accim.data.morphing.morph_epws.

The actual climate morphing is done by an external Java tool
(FutureWeatherGenerator), so subprocess.run is mocked. This exercises everything
else: per-EPW folder creation, the scenario renaming/moving, cleanup, and the
fixed NameError that happened when the morphing produced no scenario EPWs.
"""

import os
import re
import subprocess

import pytest

from accim.data.morphing import morph_epws


def _make_epw(path, name="Madrid.epw"):
    (path / name).write_text("FAKE EPW")


def test_morph_epws_no_scenarios_no_nameerror(tmp_path, monkeypatch):
    # Mock the Java call so it produces NO scenario EPWs.
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: None)
    _make_epw(tmp_path)
    monkeypatch.chdir(tmp_path)

    # Must NOT raise NameError (parent_folder_path was previously undefined here).
    morph_epws(fwg_path="fake.jar", delete_morphing_files=True, verbose=False)

    # The original EPW is moved back to the working directory and the per-EPW
    # working folder is removed.
    assert (tmp_path / "Madrid.epw").exists()
    assert not (tmp_path / "Madrid").exists()


def test_morph_epws_renames_and_moves_scenarios(tmp_path, monkeypatch):
    # Mock the Java call to create a fake morphed scenario EPW in the output folder.
    def fake_run(cmd, *a, **k):
        m = re.search(r'"([^"]+)/"', cmd if isinstance(cmd, str) else cmd[0])
        if m:
            folder = m.group(1)
            with open(os.path.join(folder, "raw_ssp126_2050.epw"), "w") as f:
                f.write("MORPHED")
        return None

    monkeypatch.setattr(subprocess, "run", fake_run)
    _make_epw(tmp_path)
    monkeypatch.chdir(tmp_path)

    morph_epws(fwg_path="fake.jar", delete_morphing_files=True, verbose=False)

    # The scenario EPW is renamed to '<folder>_<scenario>.epw' and moved to cwd,
    # the original EPW is moved back, and the working folder is deleted.
    assert (tmp_path / "Madrid_ssp126_2050.epw").exists()
    assert (tmp_path / "Madrid.epw").exists()
    assert not (tmp_path / "Madrid").exists()


def test_morph_epws_explicit_filelist(tmp_path, monkeypatch):
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: None)
    _make_epw(tmp_path, "Sevilla.epw")
    _make_epw(tmp_path, "Other.epw")
    monkeypatch.chdir(tmp_path)

    # Only the explicitly listed EPW is processed; the other is untouched.
    morph_epws(fwg_path="fake.jar", epw_filepaths=["Sevilla.epw"], delete_morphing_files=True)

    assert (tmp_path / "Sevilla.epw").exists()
    assert (tmp_path / "Other.epw").exists()
    assert not (tmp_path / "Sevilla").exists()
